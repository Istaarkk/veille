import json
import re

import pytest
from bs4 import BeautifulSoup

from scraper import Article
from site_builder import _lien_sur, construire_site


@pytest.fixture
def page(tmp_path, articles, une):
    def construire(arts=articles, b=une):
        return BeautifulSoup(construire_site(arts, b, tmp_path).read_text(encoding="utf-8"), "html.parser")
    return construire


# --- fichiers produits ---

def test_fichiers_generes(tmp_path, articles, une):
    chemin = construire_site(articles, une, tmp_path / "neuf" / "dossier")
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


# --- à la une ---

def test_une_affichee(page, une):
    p = page()
    assert p.select_one('.tab[data-vue="une"]').text == "À la une"
    sujets = p.select("details.sujet")
    assert len(sujets) == 1
    s = sujets[0]
    assert s.select_one("summary h2").text == "Frappes massives sur Kiev"
    assert s.select_one("summary .tldr").text == "La Russie a tiré 400 drones dans la nuit."
    assert s.select_one("summary .tag").text == "Russie / Ukraine"
    assert s.select_one(".couverture").text == "2 sources"
    assert [a.select_one("b").text for a in s.select(".detail .sources a")] == ["Le Monde", "BBC World"]
    assert [a.select_one("b").text for a in p.select(".signaux .sources a")] == ["IRIS"]


def test_sujets_replies_par_defaut_et_tldr_visible_sans_deplier(page):
    s = page().select_one("details.sujet")
    assert not s.has_attr("open")
    assert s.select_one("summary .tldr") and not s.select_one("summary .sources")


def test_sujets_numerotes_dans_l_ordre(page, une):
    une["sujets"] = [dict(une["sujets"][0], titre=f"Sujet {i}") for i in range(1, 4)]
    p = page(b=une)
    assert [r.text for r in p.select(".rang")] == ["1", "2", "3"]
    assert [h.text for h in p.select(".sujet h2")] == ["Sujet 1", "Sujet 2", "Sujet 3"]


def test_sources_du_sujet_cliquables(page):
    liens = page().select(".sujet .sources a")
    assert [a["href"] for a in liens] == ["https://exemple.fr/a0", "https://example.org/a1"]
    assert all(a["target"] == "_blank" and "noopener" in a["rel"] for a in liens)


def test_sujet_porte_son_horodatage(page, une):
    assert page().select_one("details.sujet")["data-ts"] == str(une["sujets"][0]["ts"])


def test_tldr_du_sujet_raccourci(page, une):
    une["sujets"][0]["en_bref"] = "Première phrase. " + "Détail sans fin " * 30 + "."
    assert page(b=une).select_one(".sujet .tldr").text == "Première phrase."


def test_sujet_sans_resume(page, une):
    une["sujets"][0]["en_bref"] = ""
    assert not page(b=une).select_one(".sujet .tldr")


def test_sans_analyses(page, une):
    une["analyses"] = []
    assert not page(b=une).select_one(".signaux")


def test_sans_une(page):
    p = page(b=None)
    assert not p.select("details.sujet")
    assert "Aucun sujet" in p.select_one("#une .vide").text
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
    carte = page(arts=articles).select_one(".art")
    assert not carte.select_one(".tldr") and not carte.select_one(".plus")


# --- cartes ---

def test_tuile_d_article(page):
    c = page().select("#fil .art.tuile")[2]
    assert c.select_one(".ini").text == "I" and "--h:" in c.select_one(".ini")["style"]
    assert c.select_one("h3").text == "Le 49.3 en débat"
    assert c.select_one(".tldr").text == "Analyse du recours au 49.3."
    assert [t.text for t in c.select(".tags span")] == ["France"]
    assert c.select_one(".lire")["href"] == "https://exemple.fr/a2"


# --- mosaïque ---

def test_fil_en_mosaique_avec_une_grande_tuile_sur_cinq(page, articles):
    arts = [Article(id=f"a{i}", titre=f"T{i}", resume="R", lien=f"https://x.test/{i}", source="S",
                    type_source="presse", timestamp=1_800_000_000 - i) for i in range(11)]
    p = page(arts=arts)
    assert p.select_one("#fil .mosaique")
    assert [i for i, a in enumerate(p.select("#fil .art")) if "large" in a["class"]] == [0, 5, 10]


@pytest.mark.parametrize("n, larges", [
    (1, [0]), (2, [0, 1]), (3, [0]), (4, [0, 3]), (5, [0, 3, 4]), (8, [0, 3, 6, 7]),
])
def test_une_en_mosaique_sans_trou_en_fin_de_grille(page, une, n, larges):
    une["sujets"] = [dict(une["sujets"][0], titre=f"S{i}") for i in range(n)]
    tuiles = page(b=une).select("#une .mosaique .sujet")
    assert [i for i, t in enumerate(tuiles) if "large" in t["class"]] == larges


def test_image_de_l_article(page, articles):
    articles[0].image = "https://img.test/a.jpg"
    c = page(arts=articles).select("#fil .art")
    img = c[0].select_one("img.visuel")
    assert img["src"] == "https://img.test/a.jpg" and img["loading"] == "lazy" and img["alt"] == ""
    assert not c[1].select_one("img") and c[1].select_one(".visuel.vide")


def test_image_du_sujet(page, une):
    une["sujets"][0]["image"] = "https://img.test/s.jpg"
    assert page(b=une).select_one(".sujet img.visuel")["src"] == "https://img.test/s.jpg"
    une["sujets"][0]["image"] = ""
    assert page(b=une).select_one(".sujet .visuel.vide")


def test_image_dangereuse_neutralisee(page, articles):
    articles[0].image = "javascript:alert(1)"
    assert page(arts=articles).select_one(".art img")["src"] == "#"


def test_resume_court_pas_de_doublon_dans_le_detail(page):
    c = page().select_one("#fil .art")
    assert c.select_one(".tldr") and not c.select_one(".complet")


def test_resume_long_tldr_court_et_texte_complet_dans_le_detail(page, articles):
    articles[0].resume = "Première phrase courte. " + "Suite très détaillée " * 20 + "."
    c = page(arts=articles).select_one(".art")
    assert c.select_one(".tldr").text == "Première phrase courte."
    assert c.select_one(".plus .complet").text == articles[0].resume


def test_teinte_stable_par_source():
    from site_builder import _teinte
    assert _teinte("Le Monde") == _teinte("Le Monde")
    assert 0 <= _teinte("BBC World") < 360


@pytest.mark.parametrize("texte, attendu", [
    ("", ""),
    (None, ""),
    ("Court.", "Court."),
    ("Une phrase. " * 5, "Une phrase. " * 5),  # sous la limite : inchangé (aux espaces près)
])
def test_tldr_textes_courts(texte, attendu):
    from site_builder import _tldr
    assert _tldr(texte) == (attendu or "").strip()


def test_tldr_garde_des_phrases_entieres():
    from site_builder import _tldr
    texte = "Kiev a été frappée cette nuit. " + "Le bilan provisoire fait état de dizaines de blessés dans plusieurs quartiers. " * 4
    court = _tldr(texte, max_car=120)
    assert court == "Kiev a été frappée cette nuit. Le bilan provisoire fait état de dizaines de blessés dans plusieurs quartiers."
    assert len(court) <= 120


def test_tldr_ne_coupe_pas_sur_une_abreviation_ou_un_chiffre():
    from site_builder import _tldr
    texte = "Le PIB a progressé de 1.5 % selon l'Insee, un rythme inattendu. " + "x " * 150
    assert _tldr(texte).startswith("Le PIB a progressé de 1.5 % selon")


def test_tldr_premiere_phrase_trop_longue_coupee_sur_un_mot():
    from site_builder import _tldr
    court = _tldr("mot " * 100, max_car=50)
    assert court.endswith("…") and len(court) <= 51 and not court[:-1].endswith(" ")


# --- sécurité ---

def test_contenu_des_flux_echappe(page, articles, une):
    articles[0].titre = '<img src=x onerror=alert(1)>'
    articles[0].resume = '"><script>alert(2)</script>'
    une["sujets"][0]["titre"] = "<script>alert(3)</script>"
    une["sujets"][0]["en_bref"] = "<b>gras</b>"
    p = page(arts=articles, b=une)
    assert not p.select("img") and not p.select(".tldr b") and len(p.select("script")) == 1
    assert p.select_one(".sujet .tldr").text == "<b>gras</b>"
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


def test_lien_dangereux_neutralise_dans_la_page(page, articles, une):
    articles[0].lien = "javascript:alert(1)"
    une["sujets"][0]["sources"][0]["lien"] = "javascript:alert(1)"
    une["analyses"][0]["lien"] = "javascript:alert(1)"
    p = page(arts=articles, b=une)
    assert "javascript:" not in str(p.select("a"))


# --- horodatages et script ---

def test_horodatage_de_generation(page):
    import time
    assert abs(int(page().body["data-genere"]) - time.time()) < 5


def test_date_de_l_edition(page):
    edition = page().select_one(".edition").text
    assert re.search(r"(lundi|mardi|mercredi|jeudi|vendredi|samedi|dimanche) \d{1,2} \w+ · 1 sujets", edition)


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
