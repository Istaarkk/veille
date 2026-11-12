import sys

import pytest

import main


@pytest.fixture
def lancer(monkeypatch, tmp_path):
    def _lancer(arts):
        monkeypatch.setattr(main, "scraper_sources", lambda: arts)
        monkeypatch.setattr(sys, "argv", ["main.py", "-o", str(tmp_path)])
        main.main()
        return (tmp_path / "index.html").read_text(encoding="utf-8")
    return _lancer


def test_genere_le_site_avec_la_une(lancer, articles):
    html = lancer(articles)
    assert "Frappes sur Kiev" in html and 'id="une"' in html


def test_sans_sujet_commun_le_fil_reste_disponible(lancer, articles):
    html = lancer(articles[2:])
    assert "Aucun sujet couvert par plusieurs rédactions" in html
    assert "Le 49.3 en débat" in html


def test_aucun_article_code_de_sortie_1(lancer, tmp_path):
    with pytest.raises(SystemExit) as e:
        lancer([])
    assert e.value.code == 1
    assert not (tmp_path / "index.html").exists()


def test_aucune_dependance_a_une_api_payante():
    import pathlib
    racine = pathlib.Path(main.__file__).parent
    code = " ".join(p.read_text(encoding="utf-8") for p in racine.glob("*.py"))
    assert "anthropic" not in code.lower() and "openai" not in code.lower()
    assert "anthropic" not in (racine / "requirements.txt").read_text().lower()
