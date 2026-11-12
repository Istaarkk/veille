import os

from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
MODELE = os.getenv("VEILLE_MODELE", "claude-opus-5-5")

FENETRE_HEURES = int(os.getenv("FENETRE_HEURES", "36"))
MAX_PAR_SOURCE = int(os.getenv("MAX_PAR_SOURCE", "15"))

# type : "presse" (actu chaude) ou "analyse" (think tanks, revues)
SOURCES = [
    {"nom": "Le Monde", "url": "https://www.lemonde.fr/international/rss_full.xml", "type": "presse"},
    {"nom": "Le Monde Politique", "url": "https://www.lemonde.fr/politique/rss_full.xml", "type": "presse"},
    {"nom": "Le Monde Éco", "url": "https://www.lemonde.fr/economie/rss_full.xml", "type": "presse"},
    {"nom": "RFI", "url": "https://www.rfi.fr/fr/rss", "type": "presse"},
    {"nom": "France 24", "url": "https://www.france24.com/fr/rss", "type": "presse"},
    {"nom": "Courrier international", "url": "https://www.courrierinternational.com/feed/all/rss.xml", "type": "presse"},
    {"nom": "BBC World", "url": "https://feeds.bbci.co.uk/news/world/rss.xml", "type": "presse"},
    {"nom": "The Guardian", "url": "https://www.theguardian.com/world/rss", "type": "presse"},
    {"nom": "Al Jazeera", "url": "https://www.aljazeera.com/xml/rss/all.xml", "type": "presse"},
    {"nom": "DW", "url": "https://rss.dw.com/rdf/rss-en-world", "type": "presse"},
    {"nom": "Politico Europe", "url": "https://www.politico.eu/feed/", "type": "presse"},
    {"nom": "Africanews", "url": "https://www.africanews.com/feed/rss", "type": "presse"},
    {"nom": "Opex360", "url": "https://www.opex360.com/feed/", "type": "presse"},
    {"nom": "Le Grand Continent", "url": "https://legrandcontinent.eu/fr/feed/", "type": "analyse"},
    {"nom": "IRIS", "url": "https://www.iris-france.org/feed/", "type": "analyse"},
    {"nom": "Crisis Group", "url": "https://www.crisisgroup.org/rss.xml", "type": "analyse"},
    {"nom": "Foreign Policy", "url": "https://foreignpolicy.com/feed/", "type": "analyse"},
    {"nom": "War on the Rocks", "url": "https://warontherocks.com/feed/", "type": "analyse"},
    {"nom": "The Diplomat", "url": "https://thediplomat.com/feed/", "type": "analyse"},
    {"nom": "The Conversation", "url": "https://theconversation.com/fr/articles.atom", "type": "analyse"},
]

# Mots-clés (minuscules, FR + EN) pour l'étiquetage régional des articles.
REGIONS = {
    "France": ["france", "français", "macron", "élysée", "assemblée nationale", "matignon", "sénat", "paris"],
    "Europe": ["europe", "européen", "bruxelles", "allemagne", "germany", "italie", "italy", "espagne", "spain",
               "pologne", "poland", "royaume-uni", "britain", " uk ", "otan", "nato", "eu ", "ue "],
    "Russie / Ukraine": ["russie", "russia", "russe", "russian", "ukraine", "kyiv", "kiev", "kremlin", "poutine",
                         "putin", "zelensky", "moscou", "moscow"],
    "Moyen-Orient": ["israël", "israel", "gaza", "iran", "liban", "lebanon", "syrie", "syria", "irak", "iraq",
                     "arabie", "saudi", "yémen", "yemen", "hamas", "hezbollah", "palestin", "turquie", "turkey",
                     "qatar", "émirats", "emirates", "cisjordanie", "west bank"],
    "Afrique": ["afrique", "africa", "sahel", "mali", "niger", "burkina", "soudan", "sudan", "congo", "rdc",
                "éthiopie", "ethiopia", "nigeria", "sénégal", "senegal", "algérie", "algeria", "maroc", "morocco",
                "tunisie", "libye", "libya", "kenya", "somalie", "somalia", "tchad", "chad"],
    "Asie-Pacifique": ["chine", "china", "chinois", "chinese", "pékin", "beijing", "taïwan", "taiwan", "japon",
                       "japan", "corée", "korea", "inde", "india", "pakistan", "afghanistan", "indonésie",
                       "philippines", "vietnam", "birmanie", "myanmar", "australie", "australia", "xi jinping"],
    "Amériques": ["états-unis", "united states", "washington", "trump", "américain", "american", "maison-blanche",
                  "white house", "canada", "mexique", "mexico", "brésil", "brazil", "argentine", "argentina",
                  "venezuela", "colombie", "colombia", "cuba", "chili", "chile"],
}
