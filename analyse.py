import anthropic
from pydantic import BaseModel, Field

from config import ANTHROPIC_API_KEY, MODELE
from scraper import Article


class Sujet(BaseModel):
    titre: str = Field(description="Titre court et factuel du sujet")
    region: str
    synthese: str = Field(description="3 à 5 phrases : ce qui s'est passé, en recoupant les sources")
    enjeux: str = Field(description="1 à 2 phrases : pourquoi c'est important, ce qu'il faut surveiller")
    article_ids: list[str] = Field(description="Identifiants des articles sources (ex. a12)")


class Brief(BaseModel):
    vue_ensemble: str = Field(description="3 à 4 phrases résumant la journée géopolitique")
    sujets: list[Sujet]
    signaux_faibles: list[str] = Field(description="2 à 5 faits peu couverts mais potentiellement significatifs")


SYSTEME = """Tu es analyste en veille géopolitique pour un lecteur français qui consulte son brief sur téléphone.
On te fournit des articles récents (presse internationale et think tanks), chacun avec un identifiant.
Produis un brief en français :
- 6 à 10 sujets majeurs, classés par importance géopolitique (pas par volume de couverture).
- Regroupe les articles qui traitent du même événement et recoupe les sources ; signale les divergences de traitement entre médias quand elles sont notables.
- Reste factuel et sobre, sans spéculation ; distingue faits établis et affirmations d'une partie.
- Ne cite que des identifiants d'articles présents dans la liste.
- region : une valeur parmi France, Europe, Russie / Ukraine, Moyen-Orient, Afrique, Asie-Pacifique, Amériques, Monde."""


def _formater(articles: list[Article]) -> str:
    return "\n".join(f"[{a.id}] ({a.source}) {a.titre} — {a.resume}" for a in articles)


def generer_brief(articles: list[Article]) -> Brief | None:
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
    brief = response.parsed_output
    ids_valides = {a.id for a in articles}
    for sujet in brief.sujets:
        sujet.article_ids = [i for i in sujet.article_ids if i in ids_valides]
    return brief
