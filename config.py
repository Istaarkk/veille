import os
from dotenv import load_dotenv

load_dotenv()

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
EMAIL_TO = os.getenv("EMAIL_TO", "")

MAX_ARTICLES = int(os.getenv("MAX_ARTICLES", "5"))

RSS_FEEDS = {
    "À la une": "https://www.lemonde.fr/rss/une.xml",
    "International": "https://www.lemonde.fr/international/rss_full.xml",
    "Politique": "https://www.lemonde.fr/politique/rss_full.xml",
    "Économie": "https://www.lemonde.fr/economie/rss_full.xml",
    "Planète": "https://www.lemonde.fr/planete/rss_full.xml",
    "Sciences": "https://www.lemonde.fr/sciences/rss_full.xml",
    "Tech": "https://www.lemonde.fr/pixels/rss_full.xml",
}
