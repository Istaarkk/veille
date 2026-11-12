import json
import re

import pytest
from bs4 import BeautifulSoup

from scraper import Article
from site_builder import _lien_sur, construire_site


@pytest.fixture
def page(tmp_path, articles, brief):
    def construire(arts=articles, b=brief):
        return BeautifulSoup(construire_site(arts, b, tmp_path).read_text(encoding="utf-8"), "html.parser")
    return construire


# --- fichiers produits ---

def test_fichiers_generes(tmp_path, articles, brief):
    chemin = construire_site(articles, brief, tmp_path / "neuf" / "dossier")
    assert chemin.name == "index.html" and chemin.exists()
    assert (chemin.parent / "icon.svg").read_text().startswith("<svg")
    manifest = json.loads((chemin.parent / "manifest.webmanifest").read_text())
    assert manifest["display"] == "standalone" and manifest["icons"][0]["src"] == "icon.svg"


def test_page_autonome_sans_ressource_externe(page):
    p = page()
    assert not p.select("script[src]")
    assert all(not l["href"].startswith("http") for l in p.select("link[href]"))


def test_meta_mobile(page):
    p = page()
    assert "width=device-width" in p.select_one('meta[name="viewport"]')["content"]
    assert p.html["lang"] == "fr"


# --- brief ---

def test_brief_affiche(page, brief):
    p = page()
    assert p.select_one(".accroche").text == brief["accroche"]
    sujets = p.select("details.sujet")
    assert len(sujets) == 1
    s = sujets[0]
    assert s.select_one("summary h2").text == "Frappes massives sur Kiev"
    assert s.select_one("summary .bref").text == "La Russie a tiré 400 drones dans la nuit."
    assert s.select_one("summary .kicker").text.startswith("Russie / Ukraine")
    assert [li.text for li in s.select(".points li")] == brief["sujets"][0]["points"]
    assert "Réunion de Ramstein" in s.select_one(".surveiller").text
    assert [li.text for li in p.select(".signaux li")] == brief["signaux_faibles"]


def test_sujets_replies_par_defaut_et_resume_visible_sans_deplier(page):
    s = page().select_one("details.sujet")
    assert not s.has_attr("open")
    assert s.select_one("summary .bref") and not s.select_one("summary .points")


def test_sujets_numerotes_dans_l_ordre(page, brief):
    brief["sujets"] = [dict(brief["sujets"][0], titre=f"Sujet {i}") for i in range(1, 4)]
    p = page(b=brief)
    assert [r.text for r in p.select(".rang")] == ["1", "2", "3"]
    assert [h.text for h in p.select(".sujet h2")] == ["Sujet 1", "Sujet 2", "Sujet 3"]


def test_sources_du_sujet_cliquables(page):
    liens = page().select(".sujet .sources a")
    assert [a["href"] for a in liens] == ["https://exemple.fr/a0", "https://example.org/a1"]
    assert all(a["target"] == "_blank" and "noopener" in a["rel"] for a in liens)


def test_sujet_porte_son_horodatage(page, brief):
    assert page().select_one("details.sujet")["data-ts"] == str(brief["sujets"][0]["ts"])


def test_sujet_sans_source_ni_a_surveiller(page, brief):
    brief["sujets"][0].update(sources=[], a_surveiller="")
    s = page(b=brief).select_one("details.sujet")
    assert not s.select_one(".sources") and not s.select_one(".surveiller")


def test_sans_signaux_faibles(page, brief):
    brief["signaux_faibles"] = []
    assert not page(b=brief).select_one(".signaux")


def test_sans_brief(page):
    p = page(b=None)
    assert not p.select("details.sujet")
    assert "Pas de brief" in p.select_one("#brief .vide").text
    assert len(p.select(".art")) == 3


# --- fil ---

def test_fil_liste_tous_les_articles_dans_l_ordre(page, articles):
    arts = page().select("#fil .art")
    assert [a.select_one("h3").text for a in arts] == [a.titre for a in articles]
    assert [a.select_one(".src").text for a in arts] == ["Le Monde", "BBC World", "IRIS"]


def test_attributs_de_filtrage(page, articles):
    arts = page().select("#fil .art")
    assert arts[0]["data-regions"] == "Russie / Ukraine" and arts[0]["data-type"] == "presse"
    assert arts[2]["data-type"] == "analyse" and arts[2].select_one(".analyse")
    assert not arts[0].select_one(".analyse")
    assert [a["data-ts"] for a in arts] == [str(a.timestamp) for a in articles]


def test_article_multi_regions(page, articles):
    articles[0].regions = ["France", "Europe"]
    assert page(arts=articles).select_one(".art")["data-regions"] == "France|Europe"


def test_chips_de_region_correspondent_a_la_config(page):
    from config import REGIONS
    chips = [c["data-val"] for c in page().select('.filtres[data-groupe="region"] .chip')]
    assert chips == [""] + list(REGIONS)


def test_definitions_du_glossaire(page):
    arts = page().select("#fil .art")
    assert "49.3" in arts[2].select_one(".def").text
    assert not arts[0].select_one(".def")


def test_article_sans_resume(page, articles):
    articles[0].resume = ""
    assert not page(arts=articles).select_one(".art").select_one("p")


# --- sécurité ---

def test_contenu_des_flux_echappe(page, articles, brief):
    articles[0].titre = '<img src=x onerror=alert(1)>'
    articles[0].resume = '"><script>alert(2)</script>'
    brief["sujets"][0]["titre"] = "<script>alert(3)</script>"
    brief["accroche"] = "<b>gras</b>"
    p = page(arts=articles, b=brief)
    assert not p.select("img") and len(p.select("script")) == 1
    assert p.select_one(".accroche").text == "<b>gras</b>"
    assert p.select_one(".art h3").text == "<img src=x onerror=alert(1)>"


@pytest.mark.parametrize("url, attendu", [
    ("https://exemple.fr/a", "https://exemple.fr/a"),
    ("http://exemple.fr/a", "http://exemple.fr/a"),
    ("javascript:alert(1)", "#"),
    ("data:text/html,<script>", "#"),
    ("//exemple.fr", "#"),
    ("", "#"),
])
def test_lien_sur(url, attendu):
    assert _lien_sur(url) == attendu


def test_lien_dangereux_neutralise_dans_la_page(page, articles, brief):
    articles[0].lien = "javascript:alert(1)"
    brief["sujets"][0]["sources"][0]["lien"] = "javascript:alert(1)"
    p = page(arts=articles, b=brief)
    assert "javascript:" not in str(p.select("a"))


# --- horodatages et script ---

def test_horodatage_de_generation(page):
    import time
    assert abs(int(page().body["data-genere"]) - time.time()) < 5


def test_date_et_heure_du_brief(page, brief):
    from datetime import datetime
    from zoneinfo import ZoneInfo
    edition = page().select_one(".edition").text
    attendu = datetime.fromtimestamp(brief["genere"], ZoneInfo("Europe/Paris")).strftime("%H:%M")
    assert f"brief de {attendu}" in edition
    assert re.search(r"(lundi|mardi|mercredi|jeudi|vendredi|samedi|dimanche) \d{1,2} \w+", edition)


def test_script_reference_des_elements_existants(page):
    """Chaque sélecteur simple utilisé par le script doit exister dans la page (garde-fou contre un renommage)."""
    p = page()
    script = p.select_one("script").string
    for sel in set(re.findall(r"\$\$?\('([.#][\w-]+)'", script)):
        assert p.select(sel), f"sélecteur absent du HTML : {sel}"
    assert "[\\u0300-\\u036f]" in script  # l'échappement de la regex d'accents a survécu au gabarit


def test_beaucoup_d_articles(page):
    arts = [Article(id=f"a{i}", titre=f"Titre {i}", resume="R", lien=f"https://x.test/{i}", source="S",
                    type_source="presse", timestamp=1_800_000_000 - i) for i in range(400)]
    assert len(page(arts=arts).select(".art")) == 400
