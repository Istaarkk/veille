import calendar
import re
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from html import unescape

import feedparser
import requests
from bs4 import BeautifulSoup

from config import FENETRE_HEURES, MAX_PAR_SOURCE, REGIONS, SOURCES
from glossaire import trouver_termes


@dataclass
class Article:
    id: str
    titre: str
    resume: str
    lien: str
    source: str
    type_source: str
    timestamp: int
    regions: list[str] = field(default_factory=list)
    termes_definis: dict[str, str] = field(default_factory=dict)
    image: str = ""


def nettoyer_html(texte: str) -> str:
    if not texte:
        return ""
    propre = unescape(BeautifulSoup(texte, "html.parser").get_text(separator=" ", strip=True))
    return re.sub(r"\s+", " ", propre).strip()


# Mot-clé en mot entier, avec les terminaisons courantes (russe → russes, palestin → palestinienne).
# Sans ces bornes, « eu » trouvait l'Europe dans « peu » et « inde » l'Asie dans « indépendance ».
_LETTRE = "a-z0-9àâäéèêëïîôöùûüÿçœæ"
_MOTIFS_REGIONS = {
    region: re.compile("|".join(
        rf"(?<![{_LETTRE}]){re.escape(m.strip())}(?:s|e|es|ne|nes|ien|ienne|iens|iennes)?(?![{_LETTRE}])" for m in mots))
    for region, mots in REGIONS.items()
}


def detecter_regions(texte: str) -> list[str]:
    t = texte.lower()
    return [region for region, motif in _MOTIFS_REGIONS.items() if motif.search(t)]


def extraire_image(e: dict) -> str:
    """URL https de l'illustration d'une entrée RSS, ou chaîne vide."""
    candidats = [m.get("url") for m in e.get("media_content", []) + e.get("media_thumbnail", [])]
    candidats += [l.get("href") for l in e.get("links", []) + e.get("enclosures", [])
                  if (l.get("type") or "").startswith("image")]
    html = e.get("summary", "") + "".join(c.get("value", "") for c in e.get("content", []))
    candidats += re.findall(r'<img[^>]+src="([^"]+)"', html)
    for url in candidats:
        if not url:
            continue
        url = unescape(url.strip())
        if url.startswith("http://"):
            url = "https://" + url[7:]  # la page est en https : une image http serait bloquée
        if url.startswith("https://"):
            # La BBC sert des vignettes de 240 px : on demande la taille au-dessus pour les grandes tuiles.
            return url.replace("/ace/standard/240/", "/ace/standard/480/")
    return ""


def _cle_dedup(titre: str) -> str:
    return re.sub(r"[^a-z0-9àâäéèêëïîôùûüÿçœæ]", "", titre.lower())[:80]


def _recuperer(source: dict) -> tuple[dict, list]:
    try:
        resp = requests.get(source["url"], timeout=20, headers={"User-Agent": "Mozilla/5.0 (VeilleBot; usage personnel)"})
        resp.raise_for_status()
        return source, feedparser.parse(resp.content).entries
    except Exception as e:
        print(f"  ! {source['nom']} : {e}")
        return source, []


def scraper_sources() -> list[Article]:
    limite = time.time() - FENETRE_HEURES * 3600
    with ThreadPoolExecutor(max_workers=10) as pool:
        resultats = list(pool.map(_recuperer, SOURCES))

    articles: list[Article] = []
    vus: set[str] = set()
    for source, entrees in resultats:
        retenus = 0
        for e in entrees:
            if retenus >= MAX_PAR_SOURCE:
                break
            date = e.get("published_parsed") or e.get("updated_parsed")
            ts = calendar.timegm(date) if date else int(time.time())
            if ts < limite:
                continue
            titre = nettoyer_html(e.get("title", ""))
            cle = _cle_dedup(titre)
            if not titre or cle in vus:
                continue
            vus.add(cle)
            resume = nettoyer_html(e.get("summary", e.get("description", "")))
            if len(resume) > 320:
                resume = resume[:320].rsplit(" ", 1)[0] + "…"
            texte = f"{titre} {resume}"
            articles.append(Article(
                id=f"a{len(articles)}",
                titre=titre,
                resume=resume,
                lien=e.get("link", ""),
                source=source["nom"],
                type_source=source["type"],
                timestamp=ts,
                regions=detecter_regions(texte),
                termes_definis=trouver_termes(texte),
                image=extraire_image(e),
            ))
            retenus += 1
        print(f"  {source['nom']} : {retenus}")

    articles.sort(key=lambda a: a.timestamp, reverse=True)
    return articles
