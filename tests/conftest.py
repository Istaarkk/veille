import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scraper import Article  # noqa: E402


@pytest.fixture
def articles() -> list[Article]:
    t = int(time.time())
    return [
        Article(id="a0", titre="Frappes sur Kiev", resume="La Russie a frappé l'Ukraine.", lien="https://exemple.fr/a0",
                source="Le Monde", type_source="presse", timestamp=t - 600, regions=["Russie / Ukraine"]),
        Article(id="a1", titre="Russia strikes Kyiv", resume="Overnight attack.", lien="https://example.org/a1",
                source="BBC World", type_source="presse", timestamp=t - 1200, regions=["Russie / Ukraine"]),
        Article(id="a2", titre="Le 49.3 en débat", resume="Analyse du recours au 49.3.", lien="https://exemple.fr/a2",
                source="IRIS", type_source="analyse", timestamp=t - 7200, regions=["France"],
                termes_definis={"49.3": "Article de la Constitution."}),
    ]


@pytest.fixture
def brief(articles) -> dict:
    return {
        "genere": int(time.time()) - 3600,
        "accroche": "Moscou intensifie ses frappes.",
        "sujets": [{
            "titre": "Frappes massives sur Kiev",
            "region": "Russie / Ukraine",
            "en_bref": "La Russie a tiré 400 drones dans la nuit.",
            "points": ["400 drones tirés.", "Coupures dans huit régions."],
            "a_surveiller": "Réunion de Ramstein jeudi.",
            "sources": [{"source": a.source, "titre": a.titre, "lien": a.lien} for a in articles[:2]],
            "ts": articles[0].timestamp,
        }],
        "signaux_faibles": ["Le Kazakhstan rejoint les accords d'Abraham."],
    }
