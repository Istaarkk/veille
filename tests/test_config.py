import importlib

import config


def _recharger(monkeypatch, **env):
    for k, v in env.items():
        monkeypatch.setenv(k, v)
    monkeypatch.setattr("dotenv.load_dotenv", lambda *a, **k: None)
    return importlib.reload(config)


def test_variables_vides_retombent_sur_les_defauts(monkeypatch):
    c = _recharger(monkeypatch, VEILLE_MODELE="", BRIEF_MAX_AGE_HEURES="")
    assert c.MODELE == "claude-opus-5-5" and c.BRIEF_MAX_AGE_HEURES == 5


def test_variables_renseignees(monkeypatch):
    c = _recharger(monkeypatch, VEILLE_MODELE="claude-sonnet-5-5", BRIEF_MAX_AGE_HEURES="8")
    assert c.MODELE == "claude-sonnet-5-5" and c.BRIEF_MAX_AGE_HEURES == 8


def teardown_module():
    importlib.reload(config)
