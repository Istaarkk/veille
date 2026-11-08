import re
from dataclasses import dataclass, field
from html import unescape

import feedparser
import requests
from bs4 import BeautifulSoup

from config import RSS_FEEDS, MAX_ARTICLES
from glossaire import trouver_termes


@dataclass
class Article:
    titre: str
    resume: str
    lien: str
    categorie: str
    date: str
    mots_cles: list[str] = field(default_factory=list)
    termes_definis: dict[str, str] = field(default_factory=dict)


def nettoyer_html(texte: str) -> str:
    if not texte:
        return ""
    soup = BeautifulSoup(texte, "html.parser")
    propre = unescape(soup.get_text(separator=" ", strip=True))
    return re.sub(r"\s+", " ", propre).strip()


def extraire_mots_cles(titre: str, resume: str) -> list[str]:
    texte = f"{titre} {resume}".lower()
    mots_vides = {
        "le", "la", "les", "un", "une", "des", "de", "du", "au", "aux",
        "et", "ou", "en", "dans", "sur", "par", "pour", "avec", "sans",
        "est", "sont", "a", "ont", "qui", "que", "ce", "cette", "ces",
        "il", "elle", "ils", "elles", "on", "nous", "vous", "se", "sa",
        "son", "ses", "leur", "leurs", "ne", "pas", "plus", "très",
        "être", "avoir", "faire", "dit", "peut", "doit", "après",
        "avant", "entre", "aussi", "comme", "tout", "tous", "mais",
        "car", "donc", "bien", "même", "autre", "autres", "où",
        "depuis", "lors", "chez", "été", "fait", "selon", "dont",
        "contre", "encore", "sous", "quel", "quelle", "quels", "quelles",
        "cette", "ceux", "celle", "celles", "quand", "comment",
        "pourquoi", "alors", "déjà", "toujours", "jamais", "rien",
        "chaque", "quelques", "plusieurs", "certain", "certains",
        "certaine", "certaines", "premier", "première", "nouveau",
        "nouvelle", "nouveaux", "nouvelles", "grand", "grande",
        "petit", "petite", "année", "années", "jour", "jours",
        "fois", "monde", "pays", "temps", "part", "deux", "trois",
        "france", "français", "française", "état", "états",
        "notamment", "ainsi", "cependant", "lors", "sera", "seront",
        "était", "étaient", "peut", "être", "avoir",
    }
    mots = re.findall(r"[a-zàâäéèêëïîôùûüÿçœæ]{4,}", texte)
    compteur: dict[str, int] = {}
    for mot in mots:
        if mot not in mots_vides:
            compteur[mot] = compteur.get(mot, 0) + 1

    triés = sorted(compteur.items(), key=lambda x: x[1], reverse=True)
    return [mot for mot, _ in triés[:5]]


def scraper_flux() -> dict[str, list[Article]]:
    resultats: dict[str, list[Article]] = {}
    tous_titres_vus: set[str] = set()

    for categorie, url in RSS_FEEDS.items():
        try:
            resp = requests.get(url, timeout=15, headers={
                "User-Agent": "VeilleNews/1.0 (digest personnel)"
            })
            resp.raise_for_status()
            flux = feedparser.parse(resp.text)
        except Exception:
            continue

        articles = []

        for entree in flux.entries[:MAX_ARTICLES * 2]:
            if len(articles) >= MAX_ARTICLES:
                break
            titre = nettoyer_html(entree.get("title", ""))
            if not titre or titre in tous_titres_vus:
                continue
            tous_titres_vus.add(titre)

            resume = nettoyer_html(
                entree.get("summary", entree.get("description", ""))
            )
            lien = entree.get("link", "")
            date = entree.get("published", "")

            texte_complet = f"{titre} {resume}"
            mots_cles = extraire_mots_cles(titre, resume)
            termes = trouver_termes(texte_complet)

            articles.append(Article(
                titre=titre,
                resume=resume[:200] + "…" if len(resume) > 200 else resume,
                lien=lien,
                categorie=categorie,
                date=date,
                mots_cles=mots_cles,
                termes_definis=termes,
            ))

        if articles:
            resultats[categorie] = articles

    return resultats
