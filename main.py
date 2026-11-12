#!/usr/bin/env python3
"""Veille — site de veille géopolitique multi-sources, sans IA ni service payant."""

import argparse
import sys
from pathlib import Path

from regroupement import a_la_une
from scraper import scraper_sources
from site_builder import construire_site


def main() -> None:
    parser = argparse.ArgumentParser(description="Génère le site de veille")
    parser.add_argument("--sortie", "-o", default="public", help="Dossier de sortie (défaut : public)")
    args = parser.parse_args()

    print("Récupération des flux…")
    articles = scraper_sources()
    if not articles:
        print("Aucun article récupéré.")
        sys.exit(1)
    print(f"{len(articles)} articles retenus.")

    une = a_la_une(articles)
    print(f"À la une : {len(une['sujets']) if une else 0} sujets.")

    chemin = construire_site(articles, une, Path(args.sortie))
    print(f"Site généré : {chemin.resolve()}")


if __name__ == "__main__":
    main()
