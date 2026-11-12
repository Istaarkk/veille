#!/usr/bin/env python3
"""Veille — site de veille géopolitique multi-sources avec brief IA."""

import argparse
import json
import sys
from pathlib import Path

from analyse import charger_brief, generer_brief
from config import BRIEF_MAX_AGE_HEURES
from scraper import scraper_sources
from site_builder import construire_site


def main() -> None:
    parser = argparse.ArgumentParser(description="Génère le site de veille")
    parser.add_argument("--sortie", "-o", default="public", help="Dossier de sortie (défaut : public)")
    parser.add_argument("--sans-ia", action="store_true", help="Ne pas générer le brief IA")
    parser.add_argument("--forcer-brief", action="store_true", help="Régénérer le brief même s'il est récent")
    args = parser.parse_args()
    sortie = Path(args.sortie)
    fichier_brief = sortie / "brief.json"

    print("Récupération des flux…")
    articles = scraper_sources()
    if not articles:
        print("Aucun article récupéré.")
        sys.exit(1)
    print(f"{len(articles)} articles retenus.")

    # Le fil est rafraîchi à chaque exécution ; le brief (coûteux) n'est régénéré que s'il a vieilli.
    brief = None if args.forcer_brief else charger_brief(fichier_brief, BRIEF_MAX_AGE_HEURES)
    if brief:
        print("Brief récent réutilisé.")
    elif not args.sans_ia:
        brief = generer_brief(articles)
        if brief:
            print(f"Brief : {len(brief['sujets'])} sujets.")
    if not brief:
        # Mieux vaut un brief daté (affiché comme tel) que pas de brief du tout.
        brief = charger_brief(fichier_brief)

    chemin = construire_site(articles, brief, sortie)
    if brief:
        fichier_brief.write_text(json.dumps(brief, ensure_ascii=False), encoding="utf-8")
    print(f"Site généré : {chemin.resolve()}")


if __name__ == "__main__":
    main()
