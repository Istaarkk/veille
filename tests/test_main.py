import json
import sys
import time

import pytest

import main


@pytest.fixture
def lancer(monkeypatch, tmp_path, articles, brief):
    """Exécute main() hors ligne. Renvoie (dossier de sortie, nombre d'appels à l'IA)."""
    def _lancer(*args, arts=articles, genere=brief, existant=None):
        appels = []
        monkeypatch.setattr(main, "scraper_sources", lambda: arts)
        monkeypatch.setattr(main, "generer_brief", lambda a: appels.append(a) or genere)
        monkeypatch.setattr(main, "BRIEF_MAX_AGE_HEURES", 5)
        monkeypatch.setattr(sys, "argv", ["main.py", "-o", str(tmp_path), *args])
        if existant is not None:
            (tmp_path / "brief.json").write_text(json.dumps(existant), encoding="utf-8")
        main.main()
        return tmp_path, len(appels)
    return _lancer


def _publie(sortie):
    return json.loads((sortie / "brief.json").read_text(encoding="utf-8"))


def test_premiere_execution_genere_et_publie_le_brief(lancer, brief):
    sortie, appels = lancer()
    assert appels == 1
    assert _publie(sortie) == brief
    assert "Frappes massives sur Kiev" in (sortie / "index.html").read_text(encoding="utf-8")


def test_brief_recent_reutilise_sans_appeler_l_ia(lancer, brief):
    ancien = dict(brief, accroche="Ancienne accroche", genere=int(time.time()) - 2 * 3600)
    sortie, appels = lancer(existant=ancien)
    assert appels == 0
    assert _publie(sortie) == ancien
    assert "Ancienne accroche" in (sortie / "index.html").read_text(encoding="utf-8")


def test_brief_perime_regenere(lancer, brief):
    ancien = dict(brief, accroche="Ancienne accroche", genere=int(time.time()) - 6 * 3600)
    sortie, appels = lancer(existant=ancien)
    assert appels == 1 and _publie(sortie) == brief


def test_forcer_brief_ignore_le_brief_recent(lancer, brief):
    ancien = dict(brief, accroche="Ancienne accroche", genere=int(time.time()) - 60)
    sortie, appels = lancer("--forcer-brief", existant=ancien)
    assert appels == 1 and _publie(sortie)["accroche"] == brief["accroche"]


def test_ia_en_panne_on_garde_le_brief_perime(lancer, brief):
    ancien = dict(brief, accroche="Ancienne accroche", genere=int(time.time()) - 20 * 3600)
    sortie, appels = lancer(genere=None, existant=ancien)
    assert appels == 1
    assert _publie(sortie) == ancien  # date d'origine conservée : la prochaine exécution réessaiera
    assert "Ancienne accroche" in (sortie / "index.html").read_text(encoding="utf-8")


def test_ia_en_panne_sans_brief_existant(lancer):
    sortie, _ = lancer(genere=None)
    assert not (sortie / "brief.json").exists()
    assert "Pas de brief" in (sortie / "index.html").read_text(encoding="utf-8")


def test_brief_existant_corrompu_regenere(lancer, brief, tmp_path):
    (tmp_path / "brief.json").write_text("<html>404 Not Found</html>")
    sortie, appels = lancer()
    assert appels == 1 and _publie(sortie) == brief


def test_sans_ia_n_appelle_jamais_l_ia(lancer):
    sortie, appels = lancer("--sans-ia")
    assert appels == 0 and not (sortie / "brief.json").exists()
    assert (sortie / "index.html").exists()


def test_sans_ia_reutilise_un_brief_existant(lancer, brief):
    ancien = dict(brief, genere=int(time.time()) - 20 * 3600)
    sortie, appels = lancer("--sans-ia", existant=ancien)
    assert appels == 0 and "Frappes massives sur Kiev" in (sortie / "index.html").read_text(encoding="utf-8")


def test_aucun_article_code_de_sortie_1(lancer, tmp_path):
    with pytest.raises(SystemExit) as e:
        lancer(arts=[])
    assert e.value.code == 1
    assert not (tmp_path / "index.html").exists()
