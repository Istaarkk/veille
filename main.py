#!/usr/bin/env python3
"""Veille — site de veille géopolitique multi-sources avec brief IA."""

import argparse
import sys
from pathlib import Path

from analyse import generer_brief
from scraper import scraper_sources
from site_builder import construire_site


def main() -> None:
    parser = argparse.ArgumentParser(description="Génère le site de veille")
    parser.add_argument("--sortie", "-o", default="public", help="Dossier de sortie (défaut : public)")
    parser.add_argument("--sans-ia", action="store_true", help="Ne pas générer le brief IA")
    args = parser.parse_args()

    print("Récupération des flux…")
    articles = scraper_sources()
    if not articles:
        print("Aucun article récupéré.")
        sys.exit(1)
    print(f"{len(articles)} articles retenus.")

    brief = None if args.sans_ia else generer_brief(articles)
    if brief:
        print(f"Brief : {len(brief.sujets)} sujets.")

    chemin = construire_site(articles, brief, Path(args.sortie))
    print(f"Site généré : {chemin.resolve()}")


if __name__ == "__main__":
    main()
