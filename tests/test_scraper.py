import calendar
import time

import pytest

import scraper
from scraper import _cle_dedup, detecter_regions, nettoyer_html, scraper_sources


def _entree(titre, age_h=1.0, resume="Résumé.", lien="https://exemple.fr/x", date=True):
    e = {"title": titre, "summary": resume, "link": lien}
    if date:
        e["published_parsed"] = time.gmtime(time.time() - age_h * 3600)
    return e


@pytest.fixture
def flux(monkeypatch):
    """Remplace le réseau : flux({nom_source: [entrées]}) configure ce que chaque source renvoie."""
    def configurer(par_source: dict, max_par_source=15, fenetre=36):
        sources = [{"nom": n, "url": f"https://{i}.test/rss", "type": "analyse" if n.startswith("TT") else "presse"}
                   for i, n in enumerate(par_source)]
        monkeypatch.setattr(scraper, "SOURCES", sources)
        monkeypatch.setattr(scraper, "MAX_PAR_SOURCE", max_par_source)
        monkeypatch.setattr(scraper, "FENETRE_HEURES", fenetre)
        monkeypatch.setattr(scraper, "_recuperer", lambda s: (s, par_source[s["nom"]]))
    return configurer


# --- nettoyer_html ---

@pytest.mark.parametrize("brut, attendu", [
    ("<p>Bonjour <b>le monde</b></p>", "Bonjour le monde"),
    ("A&amp;B &eacute;t&eacute;", "A&B été"),
    ("  trop   d'espaces\n\net sauts ", "trop d'espaces et sauts"),
    ("<script>alert(1)</script>texte", "texte"),
    ("", ""),
    (None, ""),
])
def test_nettoyer_html(brut, attendu):
    assert nettoyer_html(brut) == attendu


# --- detecter_regions ---

@pytest.mark.parametrize("texte, attendues", [
    ("Macron reçoit Zelensky à l'Élysée", {"France", "Russie / Ukraine"}),
    ("China and Taiwan tensions rise", {"Asie-Pacifique"}),
    ("Israeli strike on Gaza", {"Moyen-Orient"}),
    ("Le Sahel face au djihadisme", {"Afrique"}),
    ("Trump signe un décret", {"Amériques"}),
    ("Recette de la tarte aux pommes", set()),
])
def test_detecter_regions(texte, attendues):
    assert set(detecter_regions(texte)) == attendues


def test_detecter_regions_insensible_a_la_casse():
    assert detecter_regions("UKRAINE") == detecter_regions("ukraine") == ["Russie / Ukraine"]


def test_detecter_regions_uk_en_mot_entier():
    assert "Europe" in detecter_regions("The UK votes")
    assert "Europe" not in detecter_regions("Le bouquet de fleurs")


# --- déduplication ---

def test_cle_dedup_ignore_casse_et_ponctuation():
    assert _cle_dedup("Gaza : la trêve vacille !") == _cle_dedup("gaza la treve vacille".replace("treve", "trêve"))


def test_cle_dedup_tronquee():
    assert len(_cle_dedup("a" * 300)) == 80


# --- scraper_sources ---

def test_articles_tries_du_plus_recent_au_plus_ancien(flux):
    flux({"A": [_entree("Vieux", age_h=10), _entree("Récent", age_h=1)], "B": [_entree("Milieu", age_h=5)]})
    assert [a.titre for a in scraper_sources()] == ["Récent", "Milieu", "Vieux"]


def test_articles_hors_fenetre_exclus(flux):
    flux({"A": [_entree("Dedans", age_h=35), _entree("Dehors", age_h=37)]}, fenetre=36)
    assert [a.titre for a in scraper_sources()] == ["Dedans"]


def test_doublons_entre_sources_elimines(flux):
    flux({"A": [_entree("Même titre")], "B": [_entree("même TITRE !")]})
    arts = scraper_sources()
    assert len(arts) == 1 and arts[0].source == "A"


def test_max_par_source(flux):
    flux({"A": [_entree(f"Titre {i}") for i in range(10)]}, max_par_source=3)
    assert len(scraper_sources()) == 3


def test_max_par_source_ne_compte_pas_les_articles_ecartes(flux):
    flux({"A": [_entree("Périmé", age_h=99), _entree("", age_h=1), _entree("Bon 1"), _entree("Bon 2")]}, max_par_source=2)
    assert {a.titre for a in scraper_sources()} == {"Bon 1", "Bon 2"}


def test_identifiants_uniques(flux):
    flux({"A": [_entree(f"A{i}") for i in range(5)], "B": [_entree(f"B{i}") for i in range(5)]})
    ids = [a.id for a in scraper_sources()]
    assert len(set(ids)) == 10


def test_resume_long_tronque_sur_un_mot(flux):
    flux({"A": [_entree("Long", resume="mot " * 200)]})
    resume = scraper_sources()[0].resume
    assert len(resume) <= 321 and resume.endswith("…") and not resume.endswith(" …")


def test_html_nettoye_dans_titre_et_resume(flux):
    flux({"A": [_entree("<i>Titre</i> &amp; co", resume="<p>Un <a href='x'>lien</a></p>")]})
    a = scraper_sources()[0]
    assert a.titre == "Titre & co" and a.resume == "Un lien"


def test_entree_sans_date_datee_de_maintenant(flux):
    flux({"A": [_entree("Sans date", date=False)]})
    assert abs(scraper_sources()[0].timestamp - time.time()) < 5


def test_date_updated_utilisee_a_defaut(flux):
    quand = time.gmtime(time.time() - 7200)
    flux({"A": [{"title": "Atom", "summary": "", "link": "https://x.test", "updated_parsed": quand}]})
    assert scraper_sources()[0].timestamp == calendar.timegm(quand)


def test_type_regions_et_glossaire_renseignes(flux):
    flux({"TT": [_entree("Le 49.3 et l'Ukraine")]})
    a = scraper_sources()[0]
    assert a.type_source == "analyse" and "Russie / Ukraine" in a.regions and "49.3" in a.termes_definis


def test_source_vide_n_empeche_pas_les_autres(flux):
    flux({"A": [], "B": [_entree("Seul")]})
    assert [a.source for a in scraper_sources()] == ["B"]


def test_aucune_source_ne_repond(flux):
    flux({"A": [], "B": []})
    assert scraper_sources() == []


def test_recuperer_avale_les_erreurs_reseau(monkeypatch):
    def boum(*a, **k):
        raise scraper.requests.ConnectionError("hors ligne")
    monkeypatch.setattr(scraper.requests, "get", boum)
    source = {"nom": "A", "url": "https://x.test", "type": "presse"}
    assert scraper._recuperer(source) == (source, [])


def test_recuperer_parse_un_flux_rss(monkeypatch):
    rss = b"""<?xml version="1.0"?><rss version="2.0"><channel><title>T</title>
      <item><title>Un titre</title><link>https://x.test/1</link><description>Desc</description>
      <pubDate>Thu, 12 Nov 2026 08:00:00 GMT</pubDate></item></channel></rss>"""

    class Rep:
        content = rss
        def raise_for_status(self): pass

    monkeypatch.setattr(scraper.requests, "get", lambda *a, **k: Rep())
    _, entrees = scraper._recuperer({"nom": "A", "url": "https://x.test", "type": "presse"})
    assert entrees[0]["title"] == "Un titre" and entrees[0]["published_parsed"].tm_year == 2026
