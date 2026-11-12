import time

import pytest

from regroupement import MIN_SOURCES, a_la_une, mots, regrouper
from scraper import Article

T = int(time.time())


def art(i, titre, source, resume="", age=0, regions=(), type_source="presse"):
    return Article(id=f"a{i}", titre=titre, resume=resume, lien=f"https://x.test/{i}", source=source,
                   type_source=type_source, timestamp=T - age, regions=list(regions))


@pytest.fixture
def actu():
    """Trois événements couverts par plusieurs médias (dont en anglais) et du bruit isolé."""
    return [
        art(0, "Des émissaires américains à Moscou pour parler de l'Ukraine avec Poutine", "Le Monde",
            "Les envoyés de Washington rencontrent Vladimir Poutine au Kremlin. La rencontre doit durer deux jours.",
            regions=["Russie / Ukraine", "Amériques"]),
        art(1, "US envoys arrive in Moscow for Ukraine talks with Putin", "BBC World",
            "The envoys will meet Putin at the Kremlin.", age=60, regions=["Russie / Ukraine"]),
        art(2, "US envoys in Moscow: Putin to discuss Ukraine peace plan", "The Guardian",
            "Envoys arrive in Moscow for talks.", age=120, regions=["Russie / Ukraine"]),
        art(3, "Indonésie : le vice-président démissionne après un scandale d'écoutes", "RFI",
            "Le vice-président indonésien a présenté sa démission.", age=30, regions=["Asie-Pacifique"]),
        art(4, "Indonesia vice president resigns amid wiretap scandal", "Al Jazeera",
            "Indonesia's vice president resigned on Thursday.", age=90, regions=["Asie-Pacifique"]),
        art(5, "Indonesia's vice-president resigns", "BBC World", "", age=200, regions=["Asie-Pacifique"]),
        art(6, "Grève générale en Espagne : heurts à Barcelone", "France 24",
            "Des milliers de manifestants à Barcelone.", age=10, regions=["Europe"]),
        art(7, "Spain general strike: clashes erupt in Barcelona", "Africanews",
            "Clashes in Barcelona during Spain's general strike.", age=15, regions=["Europe"]),
        art(8, "Recette : la tarte aux pommes de grand-mère", "Le Monde Éco", "Un dessert simple.", age=5),
        art(9, "Football : le PSG s'impose face à Lyon", "France 24", "Victoire parisienne.", age=7),
        art(10, "Why NATO needs a new doctrine", "War on the Rocks", "An essay.", age=3000, type_source="analyse"),
    ]


def _groupe_de(groupes, i):
    return next({a.id for a in g} for g in groupes if any(a.id == f"a{i}" for a in g))


# --- mots ---

def test_mots_normalise_accents_casse_et_mots_vides():
    assert mots("Les ÉMISSAIRES à Moscou") == ["envoy", "moscow"]


def test_mots_rapproche_francais_et_anglais():
    assert set(mots("Poutine reçoit à Moscou")) & set(mots("Putin in Moscow")) == {"putin", "moscow"}


def test_mots_ignore_les_nombres_et_mots_courts():
    assert mots("Le G7 a 50 ans en 2025") == []


# --- regrouper ---

def test_chaque_article_dans_un_seul_groupe(actu):
    groupes = regrouper(actu)
    ids = [a.id for g in groupes for a in g]
    assert sorted(ids) == sorted(a.id for a in actu)


def test_meme_evenement_regroupe_malgre_la_langue(actu):
    groupes = regrouper(actu)
    assert {"a0", "a1", "a2"} <= _groupe_de(groupes, 1)
    assert {"a3", "a4", "a5"} <= _groupe_de(groupes, 4)
    assert {"a6", "a7"} <= _groupe_de(groupes, 6)


def test_evenements_differents_separes(actu):
    groupes = regrouper(actu)
    assert _groupe_de(groupes, 1).isdisjoint(_groupe_de(groupes, 4))
    assert _groupe_de(groupes, 4).isdisjoint(_groupe_de(groupes, 6))
    assert _groupe_de(groupes, 8) == {"a8"}


def test_liste_vide():
    assert regrouper([]) == []


def test_articles_sans_mot_utile_restent_isoles():
    groupes = regrouper([art(0, "Le", "A"), art(1, "Le", "B")])
    assert len(groupes) == 2


# --- a_la_une ---

def test_sujets_classes_par_nombre_de_redactions(actu):
    une = a_la_une(actu)
    assert [len(s["sources"]) for s in une["sujets"]] == [3, 3, 2]
    assert "Espagne" in une["sujets"][2]["titre"] or "Spain" in une["sujets"][2]["titre"]


def test_bruit_isole_exclu(actu):
    titres = " ".join(s["titre"] for s in a_la_une(actu)["sujets"])
    assert "tarte" not in titres and "PSG" not in titres


def test_titre_et_resume_francophones_preferes(actu):
    ukraine = next(s for s in a_la_une(actu)["sujets"] if "Moscou" in s["titre"] or "Moscow" in s["titre"])
    assert ukraine["titre"].startswith("Des émissaires américains")
    assert ukraine["en_bref"].startswith("Les envoyés de Washington")
    assert ukraine["sources"][0]["source"] == "Le Monde"


def test_region_majoritaire_et_horodatage(actu):
    ukraine = next(s for s in a_la_une(actu)["sujets"] if "Ukraine" in s["titre"])
    assert ukraine["region"] == "Russie / Ukraine"
    assert ukraine["ts"] == T


def test_une_source_par_media_dans_un_sujet():
    une = a_la_une([art(0, "Sommet de l'OTAN à Vilnius", "Le Monde"), art(1, "Sommet OTAN Vilnius : le bilan", "Le Monde"),
                    art(2, "NATO summit in Vilnius", "DW")])
    assert [s["source"] for s in une["sujets"][0]["sources"]] == ["Le Monde", "DW"]


def test_un_seul_media_ne_suffit_pas():
    assert MIN_SOURCES == 2
    assert a_la_une([art(0, "Sommet OTAN Vilnius", "Le Monde"), art(1, "Sommet OTAN Vilnius bilan", "Le Monde")]) is None


def test_rubriques_d_un_meme_media_comptent_une_fois_au_classement():
    une = a_la_une([
        art(0, "Budget : vote du Sénat", "Le Monde"), art(1, "Budget : le Sénat vote", "Le Monde Politique"),
        art(2, "Budget : le Sénat a voté", "Le Monde Éco"),
        art(3, "Sommet OTAN Vilnius", "RFI"), art(4, "NATO summit Vilnius", "DW"), art(5, "Sommet OTAN : Vilnius", "France 24"),
    ])
    assert "OTAN" in une["sujets"][0]["titre"]


def test_nombre_de_sujets_plafonne(actu):
    assert len(a_la_une(actu, max_sujets=2)["sujets"]) == 2


def test_analyses_recentes(actu):
    assert a_la_une(actu)["analyses"] == [{"source": "War on the Rocks", "titre": "Why NATO needs a new doctrine",
                                          "lien": "https://x.test/10"}]


def test_aucun_article():
    assert a_la_une([]) is None


def test_un_direct_n_est_pas_choisi_comme_titre():
    une = a_la_une([
        art(0, "EN DIRECT, sommet de l'OTAN à Vilnius : toutes les informations", "Le Monde", "Suivez le sommet."),
        art(1, "Sommet de l'OTAN à Vilnius : l'Ukraine attendue", "RFI", "Les alliés se retrouvent à Vilnius."),
        art(2, "NATO summit in Vilnius - live", "The Guardian", "Live coverage."),
    ])
    assert une["sujets"][0]["titre"].startswith("Sommet de l'OTAN à Vilnius : l'Ukraine")
    assert [s["source"] for s in une["sujets"][0]["sources"]][0] == "RFI"


def test_un_direct_reste_choisi_s_il_n_y_a_que_ca():
    une = a_la_une([art(0, "EN DIRECT : sommet OTAN Vilnius", "Le Monde", "Suivez."),
                    art(1, "NATO summit Vilnius live", "DW", "Live.")])
    assert une["sujets"][0]["titre"] == "EN DIRECT : sommet OTAN Vilnius"


def test_image_du_sujet_prise_sur_le_premier_article_illustre():
    a, b = art(0, "Sommet OTAN Vilnius", "Le Monde", "Résumé."), art(1, "NATO summit Vilnius", "DW", "Summary.")
    b.image = "https://img.test/dw.jpg"
    assert a_la_une([a, b])["sujets"][0]["image"] == "https://img.test/dw.jpg"
    b.image = ""
    assert a_la_une([a, b])["sujets"][0]["image"] == ""
