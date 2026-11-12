import json
import time
from types import SimpleNamespace

import anthropic
import pytest

import analyse
from analyse import Brief, Sujet, _formater, _resoudre, charger_brief, generer_brief


def _sujet(ids, titre="Titre"):
    return Sujet(titre=titre, region="Europe", en_bref="Bref.", points=["p1", "p2"], a_surveiller="Suite.", article_ids=ids)


def _brief(*sujets):
    return Brief(accroche="Accroche.", sujets=list(sujets), signaux_faibles=["s1"])


@pytest.fixture
def api(monkeypatch):
    """Remplace le client Anthropic : api(reponse=…) ou api(erreur=…). Renvoie les appels reçus."""
    appels = []

    def configurer(reponse=None, erreur=None):
        def parse(**kwargs):
            appels.append(kwargs)
            if erreur:
                raise erreur
            return reponse
        client = SimpleNamespace(beta=SimpleNamespace(messages=SimpleNamespace(parse=parse)))
        monkeypatch.setattr(analyse, "ANTHROPIC_API_KEY", "sk-test")
        monkeypatch.setattr(analyse.anthropic, "Anthropic", lambda **k: client)
        return appels
    return configurer


# --- _formater ---

def test_formater_une_ligne_par_article(articles):
    lignes = _formater(articles).split("\n")
    assert len(lignes) == 3
    assert lignes[0] == "[a0] (Le Monde) Frappes sur Kiev — La Russie a frappé l'Ukraine."


# --- _resoudre ---

def test_resoudre_remplace_les_ids_par_les_sources(articles):
    r = _resoudre(_brief(_sujet(["a0", "a1"])), articles)
    assert r["sujets"][0]["sources"] == [
        {"source": "Le Monde", "titre": "Frappes sur Kiev", "lien": "https://exemple.fr/a0"},
        {"source": "BBC World", "titre": "Russia strikes Kyiv", "lien": "https://example.org/a1"},
    ]


def test_resoudre_ignore_les_ids_inventes(articles):
    r = _resoudre(_brief(_sujet(["a0", "a999", "bidon"])), articles)
    assert [s["titre"] for s in r["sujets"][0]["sources"]] == ["Frappes sur Kiev"]


def test_resoudre_deduplique_les_ids(articles):
    r = _resoudre(_brief(_sujet(["a1", "a0", "a1"])), articles)
    assert [s["source"] for s in r["sujets"][0]["sources"]] == ["BBC World", "Le Monde"]


def test_resoudre_ts_du_sujet_est_celui_de_la_source_la_plus_recente(articles):
    r = _resoudre(_brief(_sujet(["a2", "a0"])), articles)
    assert r["sujets"][0]["ts"] == articles[0].timestamp


def test_resoudre_sujet_sans_source_valide(articles):
    s = _resoudre(_brief(_sujet(["a999"])), articles)["sujets"][0]
    assert s["sources"] == [] and s["ts"] == 0


def test_resoudre_conserve_ordre_et_contenu(articles):
    r = _resoudre(_brief(_sujet(["a0"], "Premier"), _sujet(["a1"], "Second")), articles)
    assert [s["titre"] for s in r["sujets"]] == ["Premier", "Second"]
    assert r["accroche"] == "Accroche." and r["signaux_faibles"] == ["s1"]
    assert abs(r["genere"] - time.time()) < 5
    assert set(r["sujets"][0]) == {"titre", "region", "en_bref", "points", "a_surveiller", "sources", "ts"}


def test_resoudre_serialisable_en_json(articles):
    r = _resoudre(_brief(_sujet(["a0"])), articles)
    assert json.loads(json.dumps(r)) == r


# --- generer_brief ---

def test_generer_sans_cle_api(monkeypatch, articles):
    monkeypatch.setattr(analyse, "ANTHROPIC_API_KEY", "")
    monkeypatch.setattr(analyse.anthropic, "Anthropic", lambda **k: pytest.fail("l'API ne doit pas être appelée"))
    assert generer_brief(articles) is None


def test_generer_succes(api, articles):
    appels = api(reponse=SimpleNamespace(stop_reason="end_turn", parsed_output=_brief(_sujet(["a0", "a999"]))))
    r = generer_brief(articles)
    assert r["sujets"][0]["sources"][0]["source"] == "Le Monde" and len(r["sujets"][0]["sources"]) == 1
    assert len(appels) == 1
    assert appels[0]["output_format"] is Brief
    assert "[a2] (IRIS)" in appels[0]["messages"][0]["content"]


def test_generer_refus_du_modele(api, articles):
    api(reponse=SimpleNamespace(stop_reason="refusal", parsed_output=None))
    assert generer_brief(articles) is None


def _erreur(classe, **attributs):
    """Fabrique une erreur du SDK sans dépendre de sa bibliothèque HTTP interne."""
    e = classe.__new__(classe)
    e.__dict__.update(attributs)
    return e


@pytest.mark.parametrize("code", [401, 429, 500, 529])
def test_generer_erreur_http(api, articles, code):
    api(erreur=_erreur(anthropic.APIStatusError, status_code=code, message="refusé"))
    assert generer_brief(articles) is None


def test_generer_erreur_reseau(api, articles):
    api(erreur=_erreur(anthropic.APIConnectionError, message="hors ligne"))
    assert generer_brief(articles) is None


# --- charger_brief ---

def test_charger_brief_valide(tmp_path, brief):
    f = tmp_path / "brief.json"
    f.write_text(json.dumps(brief), encoding="utf-8")
    assert charger_brief(f) == brief
    assert charger_brief(f, age_max_heures=5) == brief


def test_charger_brief_trop_vieux(tmp_path, brief):
    brief["genere"] = int(time.time()) - 6 * 3600
    f = tmp_path / "brief.json"
    f.write_text(json.dumps(brief), encoding="utf-8")
    assert charger_brief(f, age_max_heures=5) is None
    assert charger_brief(f) == brief  # sans limite d'âge, il reste utilisable en secours


def test_charger_brief_absent(tmp_path):
    assert charger_brief(tmp_path / "absent.json") is None


@pytest.mark.parametrize("contenu", [
    "", "pas du json", "<html>404</html>", "[]", "null", "42",
    '{"sujets": []}',                          # pas de date
    '{"genere": 1}',                           # pas de sujets
    '{"genere": "hier", "sujets": []}',        # date mal typée
    '{"genere": 1, "sujets": "aucun"}',        # sujets mal typés
])
def test_charger_brief_corrompu(tmp_path, contenu):
    f = tmp_path / "brief.json"
    f.write_text(contenu, encoding="utf-8")
    assert charger_brief(f) is None
