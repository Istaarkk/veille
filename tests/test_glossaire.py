import pytest

from glossaire import TERMES, trouver_termes


@pytest.mark.parametrize("texte, terme", [
    ("Le gouvernement dégaine le 49.3", "49.3"),
    ("MOTION DE CENSURE déposée", "motion de censure"),
    ("La COP s'ouvre à Belém", "cop"),
    ("Saisine du Conseil constitutionnel.", "conseil constitutionnel"),
])
def test_terme_detecte(texte, terme):
    assert terme in trouver_termes(texte)


@pytest.mark.parametrize("texte, terme", [
    ("Un hélicoptère s'est écrasé", "cop"),
    ("Les copains d'abord", "cop"),
    ("Des gestes simples", "ges"),
])
def test_pas_de_faux_positif_dans_un_mot(texte, terme):
    assert terme not in trouver_termes(texte)


def test_texte_vide():
    assert trouver_termes("") == {}


def test_definition_renvoyee():
    assert trouver_termes("le giec alerte")["giec"] == TERMES["giec"]


def test_glossaire_bien_forme():
    for terme, definition in TERMES.items():
        assert terme == terme.lower().strip(), f"clé non normalisée : {terme!r}"
        assert definition.strip(), f"définition vide : {terme!r}"
