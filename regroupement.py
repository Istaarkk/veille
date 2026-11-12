"""« À la une » sans IA : regroupe les articles qui traitent du même événement et classe les sujets
selon le nombre de rédactions qui les couvrent."""

import math
import re
import time
import unicodedata
from collections import Counter

from scraper import Article

# Sources francophones : on préfère leur titre et leur résumé pour présenter un sujet.
SOURCES_FR = {"Le Monde", "Le Monde Politique", "Le Monde Éco", "RFI", "France 24", "Courrier international",
              "Opex360", "Le Grand Continent", "IRIS", "The Conversation"}

MOTS_VIDES = set("""
a au aux avec ce ces cet cette dans de des du elle elles en entre est et etre eux il ils je la le les leur leurs lui
ma mais me meme mes moi mon ne nos notre nous on ou par pas pour qu que qui sa se ses son sont sur ta te tes toi ton
tu un une vos votre vous y ete etait sera fait faire plus moins tres tout tous toute toutes apres avant depuis sans
sous selon comme alors aussi ainsi encore deja quand dont lors chez vers contre face pendant fois jour jours jeudi
mercredi mardi lundi vendredi samedi dimanche hier demain annee ans an deux trois premier premiere nouveau nouvelle
nouveaux nouvelles grand grande grands selon via entre afin cela ceci celle celui ceux leurs quelle quel quels
the a an and or of to in on at for with by from as is are was were be been has have had it its this that these those
not no but if than then there their they them he she his her we our you your who what which when where how why will
would could should can may might after before over under into about amid against new says said say also more most
just than out up down off one two three first last year years day week monday tuesday wednesday thursday friday
saturday sunday live latest update news report reports video watch
""".split())

# Rapprochement FR/EN des noms qui reviennent le plus dans l'actualité internationale.
ALIAS = {
    "kiev": "kyiv", "moscou": "moscow", "russie": "russia", "russe": "russia", "russian": "russia",
    "ukrainien": "ukraine", "ukrainienne": "ukraine", "ukrainian": "ukraine", "poutine": "putin",
    "zelensky": "zelensky", "zelenskyy": "zelensky", "zelenski": "zelensky",
    "israel": "israel", "israelien": "israel", "israelienne": "israel", "israeli": "israel",
    "palestinien": "palestine", "palestinienne": "palestine", "palestinian": "palestine",
    "liban": "lebanon", "libanais": "lebanon", "lebanese": "lebanon", "syrie": "syria", "syrien": "syria", "syrian": "syria",
    "irak": "iraq", "iranien": "iran", "iranian": "iran", "yemen": "yemen", "turquie": "turkey", "turc": "turkey",
    "chine": "china", "chinois": "china", "chinoise": "china", "chinese": "china", "pekin": "beijing",
    "taiwanais": "taiwan", "japon": "japan", "japonais": "japan", "japanese": "japan", "coree": "korea", "korean": "korea",
    "inde": "india", "indien": "india", "indian": "india",
    "etats": "usa", "unis": "usa", "americain": "usa", "americaine": "usa", "american": "usa", "us": "usa",
    "washington": "usa", "maison": "", "blanche": "whitehouse",
    "allemagne": "germany", "allemand": "germany", "german": "germany", "royaume": "uk", "britannique": "uk",
    "british": "uk", "britain": "uk", "londres": "london", "bruxelles": "brussels", "europeen": "europe",
    "europeenne": "europe", "european": "europe", "ue": "eu", "otan": "nato", "pologne": "poland", "polish": "poland",
    "soudan": "sudan", "soudanais": "sudan", "ethiopie": "ethiopia", "nigeria": "nigeria", "algerie": "algeria",
    "maroc": "morocco", "tunisie": "tunisia", "libye": "libya", "tchad": "chad", "somalie": "somalia",
    "espagne": "spain", "espagnol": "spain", "spanish": "spain", "barcelone": "barcelona", "italie": "italy",
    "italien": "italy", "italian": "italy", "grece": "greece", "grec": "greece", "greek": "greece",
    "hongrie": "hungary", "roumanie": "romania", "suede": "sweden", "norvege": "norway", "danemark": "denmark",
    "finlande": "finland", "pays": "", "bas": "", "netherlands": "netherlands", "belgique": "belgium",
    "suisse": "switzerland", "autriche": "austria", "irlande": "ireland", "ecosse": "scotland",
    "indonesie": "indonesia", "indonesien": "indonesia", "indonesian": "indonesia", "philippin": "philippines",
    "birmanie": "myanmar", "thailande": "thailand", "australie": "australia", "coree": "korea",
    "afrique": "africa", "africain": "africa", "african": "africa", "egypte": "egypt", "egyptien": "egypt",
    "arabie": "saudi", "saoudite": "saudi", "emirats": "emirates", "jordanie": "jordan", "cisjordanie": "westbank",
    "afghanistan": "afghanistan", "argentine": "argentina", "chili": "chile", "perou": "peru", "canada": "canada",
    "bresil": "brazil", "vice": "vice", "president": "president", "presidente": "president",
    "presidentielle": "election", "demission": "resign", "demissionne": "resign", "resigns": "resign",
    "resigned": "resign", "heurts": "clash", "clashes": "clash", "manifestants": "protester",
    "manifestation": "protest", "protesters": "protester", "protests": "protest", "generale": "general",
    "accord": "deal", "agreement": "deal", "sanctions": "sanction", "emissaires": "envoy", "envoys": "envoy",
    "envoyes": "envoy", "ecoutes": "wiretap", "gouvernement": "government", "premier": "",
    "ministre": "minister", "ministres": "minister", "mexique": "mexico", "colombie": "colombia", "venezuelien": "venezuela",
    "francais": "france", "francaise": "france", "french": "france", "paris": "france",
    "cessez": "ceasefire", "treve": "ceasefire", "elections": "election", "electoral": "election",
    "frappes": "strike", "frappe": "strike", "strikes": "strike", "attaque": "attack", "attacks": "attack",
    "drones": "drone", "missiles": "missile", "sommet": "summit", "talks": "negotiation", "negociations": "negotiation",
    "droits": "tariff", "douane": "tariff", "tariffs": "tariff",
}

SEUIL = 0.24        # similarité minimale pour rattacher un article à un sujet
MAX_SUJETS = 8
MIN_SOURCES = 2     # un sujet « à la une » doit être couvert par au moins deux rédactions


def _sans_accents(texte: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", texte) if unicodedata.category(c) != "Mn")


def mots(texte: str) -> list[str]:
    sortie = []
    for m in re.findall(r"[a-z0-9]+", _sans_accents(texte.lower())):
        m = ALIAS.get(m, m)
        if len(m) < 3 or m in MOTS_VIDES or m.isdigit():
            continue
        if len(m) > 4 and m.endswith("s"):
            m = m[:-1]
        sortie.append(m)
    return sortie


def _vecteur(a: Article, idf: dict[str, float]) -> dict[str, float]:
    poids = Counter()
    for m in mots(a.titre):
        poids[m] += 2.0
    for m in mots(a.resume[:240]):
        poids[m] += 1.0
    v = {m: p * idf.get(m, 0.0) for m, p in poids.items()}
    norme = math.sqrt(sum(x * x for x in v.values())) or 1.0
    return {m: x / norme for m, x in v.items()}


def _cosinus(u: dict[str, float], v: dict[str, float]) -> float:
    if len(u) > len(v):
        u, v = v, u
    return sum(x * v.get(m, 0.0) for m, x in u.items())


def _normaliser(v: dict[str, float]) -> dict[str, float]:
    norme = math.sqrt(sum(x * x for x in v.values())) or 1.0
    return {m: x / norme for m, x in v.items()}


def regrouper(articles: list[Article], seuil: float = SEUIL) -> list[list[Article]]:
    """Regroupement glouton : chaque article rejoint le sujet dont il est le plus proche, ou en ouvre un nouveau.
    Dans chaque groupe, les articles sont triés du plus central au plus périphérique."""
    if not articles:
        return []
    df = Counter()
    for a in articles:
        df.update(set(mots(a.titre) + mots(a.resume[:240])))
    n = len(articles)
    # Un mot vu une seule fois ne peut rien rapprocher ; sur un gros lot, un mot présent dans plus de 30 %
    # des articles ne distingue rien. Le +1 garde un poids aux mots communs quand le lot est petit.
    idf = {m: math.log(1 + n / c) for m, c in df.items() if c > 1 and (n < 20 or c < n * 0.3)}

    groupes: list[dict] = []
    for a in sorted(articles, key=lambda x: x.timestamp, reverse=True):
        v = _vecteur(a, idf)
        meilleur, score = None, seuil
        for g in groupes if v else []:
            s = _cosinus(v, g["centre"])
            if s >= score:
                meilleur, score = g, s
        if meilleur is None:
            meilleur = {"membres": [], "somme": Counter()}
            groupes.append(meilleur)
        meilleur["membres"].append((a, v))
        meilleur["somme"].update(v)
        meilleur["centre"] = _normaliser(meilleur["somme"])
    return [[a for a, v in sorted(g["membres"], key=lambda m: _cosinus(m[1], g["centre"]), reverse=True)]
            for g in groupes]


_DIRECT = re.compile(r"\b(en direct|live)\b", re.IGNORECASE)


def _representant(groupe: list[Article]) -> Article:
    """L'article le plus central, de préférence francophone, avec un résumé, et pas un direct (titres à rallonge)."""
    filtres = (
        lambda a: a.source in SOURCES_FR and a.resume and not _DIRECT.search(a.titre),
        lambda a: a.resume and not _DIRECT.search(a.titre),
        lambda a: a.source in SOURCES_FR and a.resume,
        lambda a: a.resume,
    )
    for filtre in filtres:
        for a in groupe:
            if filtre(a):
                return a
    return groupe[0]


def a_la_une(articles: list[Article], max_sujets: int = MAX_SUJETS) -> dict | None:
    """Construit « À la une » : les sujets couverts par le plus de rédactions, avec un TL;DR et leurs sources."""
    sujets = []
    for groupe in regrouper(articles):
        nb_sources = len({a.source for a in groupe})
        if nb_sources < MIN_SOURCES:
            continue
        rep = _representant(groupe)
        regions = Counter(r for a in groupe for r in a.regions)
        ts = max(a.timestamp for a in groupe)
        # Les sources d'un même média (Le Monde, Le Monde Éco…) ne comptent qu'une fois par rédaction.
        redactions = len({a.source.split()[0] if a.source.startswith("Le Monde") else a.source for a in groupe})
        vus, sources = set(), []
        for a in [rep] + [x for x in groupe if x is not rep]:
            if a.source not in vus:
                vus.add(a.source)
                sources.append({"source": a.source, "titre": a.titre, "lien": a.lien})
        sujets.append({  # le score sert au tri puis est retiré
            "titre": rep.titre,
            "region": regions.most_common(1)[0][0] if regions else "Monde",
            "en_bref": rep.resume,
            "sources": sources,
            "ts": ts,
            "_score": (redactions, len(groupe), ts),
        })
    if not sujets:
        return None
    sujets.sort(key=lambda s: s.pop("_score"), reverse=True)
    analyses = [a for a in articles if a.type_source == "analyse"][:5]
    return {
        "genere": int(time.time()),
        "sujets": sujets[:max_sujets],
        "analyses": [{"source": a.source, "titre": a.titre, "lien": a.lien} for a in analyses],
    }
