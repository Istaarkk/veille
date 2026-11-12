import json
import time
from pathlib import Path

import anthropic
from pydantic import BaseModel, Field

from config import ANTHROPIC_API_KEY, MODELE
from scraper import Article


class Sujet(BaseModel):
    titre: str = Field(description="Titre factuel de 9 mots maximum, sans ponctuation finale")
    region: str
    en_bref: str = Field(description="UNE phrase de 25 mots maximum : le fait essentiel, lisible seul sans le titre")
    points: list[str] = Field(description="2 à 4 puces de 20 mots maximum : faits, chiffres, acteurs, divergences entre médias")
    a_surveiller: str = Field(description="Une phrase : la prochaine échéance ou le risque à suivre")
    article_ids: list[str] = Field(description="Identifiants des articles sources (ex. a12)")


class Brief(BaseModel):
    accroche: str = Field(description="1 à 2 phrases, 40 mots maximum : le fil rouge de la journée géopolitique")
    sujets: list[Sujet]
    signaux_faibles: list[str] = Field(description="2 à 4 faits peu couverts mais potentiellement significatifs, une phrase courte chacun")


SYSTEME = """Tu es analyste en veille géopolitique pour un lecteur français qui consulte son brief sur téléphone, souvent en moins de deux minutes.
On te fournit des articles récents (presse internationale et think tanks), chacun avec un identifiant.
Produis un brief en français, conçu pour être balayé du regard :
- 6 à 9 sujets, classés par importance géopolitique décroissante (pas par volume de couverture).
- Le lecteur ne lira souvent que le titre et « en_bref » : ils doivent suffire à savoir ce qui s'est passé. Commence par le fait, pas par le contexte.
- Style télégraphique et dense : pas de formules d'introduction, pas de redite entre titre, en_bref et points.
- Regroupe les articles qui traitent du même événement et recoupe les sources ; signale dans les points les divergences de traitement entre médias quand elles sont notables.
- Reste factuel et sobre, sans spéculation ; distingue faits établis et affirmations d'une partie.
- Ne cite que des identifiants d'articles présents dans la liste.
- region : une valeur parmi France, Europe, Russie / Ukraine, Moyen-Orient, Afrique, Asie-Pacifique, Amériques, Monde."""


def _formater(articles: list[Article]) -> str:
    return "\n".join(f"[{a.id}] ({a.source}) {a.titre} — {a.resume}" for a in articles)


def _resoudre(brief: Brief, articles: list[Article]) -> dict:
    """Remplace les identifiants d'articles par les sources elles-mêmes : le brief devient autonome et réutilisable."""
    par_id = {a.id: a for a in articles}
    sujets = []
    for s in brief.sujets:
        sources = [par_id[i] for i in dict.fromkeys(s.article_ids) if i in par_id]
        sujets.append({
            "titre": s.titre,
            "region": s.region,
            "en_bref": s.en_bref,
            "points": s.points,
            "a_surveiller": s.a_surveiller,
            "sources": [{"source": a.source, "titre": a.titre, "lien": a.lien} for a in sources],
            "ts": max((a.timestamp for a in sources), default=0),
        })
    return {
        "genere": int(time.time()),
        "accroche": brief.accroche,
        "sujets": sujets,
        "signaux_faibles": brief.signaux_faibles,
    }


def generer_brief(articles: list[Article]) -> dict | None:
    if not ANTHROPIC_API_KEY:
        print("ANTHROPIC_API_KEY absente : brief IA ignoré.")
        return None

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    try:
        response = client.beta.messages.parse(
            model=MODELE,
            max_tokens=16000,
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            output_config={"effort": "medium"},
            system=SYSTEME,
            messages=[{"role": "user", "content": _formater(articles)}],
            output_format=Brief,
        )
    except anthropic.APIStatusError as e:
        print(f"Erreur API Claude ({e.status_code}) : {e.message}")
        return None
    except anthropic.APIConnectionError:
        print("Erreur réseau vers l'API Claude.")
        return None

    if response.stop_reason == "refusal":
        print("Brief refusé par le modèle.")
        return None
    return _resoudre(response.parsed_output, articles)


def charger_brief(chemin: Path, age_max_heures: float | None = None) -> dict | None:
    """Relit un brief déjà généré ; None s'il est absent, illisible ou plus vieux que age_max_heures."""
    try:
        brief = json.loads(chemin.read_text(encoding="utf-8"))
        if not isinstance(brief["sujets"], list) or not isinstance(brief["genere"], int):
            return None
    except (OSError, ValueError, KeyError, TypeError):
        return None
    if age_max_heures is not None and time.time() - brief["genere"] > age_max_heures * 3600:
        return None
    return brief
