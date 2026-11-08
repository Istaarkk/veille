#!/usr/bin/env python3
"""Veille Actu — Digest quotidien des actualités Le Monde."""

import argparse
import locale
import sys
from pathlib import Path

import requests

from config import RESEND_API_KEY, EMAIL_TO
from scraper import scraper_flux
from email_builder import construire_email


def envoyer_email(html: str, destinataire: str) -> None:
    resp = requests.post(
        "https://api.resend.com/emails",
        headers={"Authorization": f"Bearer {RESEND_API_KEY}"},
        json={
            "from": "Veille Actu <onboarding@resend.dev>",
            "to": [destinataire],
            "subject": "Veille Actu — Votre digest du jour",
            "html": html,
        },
        timeout=30,
    )
    resp.raise_for_status()


def main() -> None:
    parser = argparse.ArgumentParser(description="Veille Actu — Digest quotidien")
    parser.add_argument(
        "--preview",
        action="store_true",
        help="Génère le HTML dans un fichier au lieu d'envoyer l'email",
    )
    parser.add_argument(
        "--output", "-o",
        default="preview.html",
        help="Fichier de sortie en mode preview (défaut: preview.html)",
    )
    args = parser.parse_args()

    try:
        locale.setlocale(locale.LC_TIME, "fr_FR.UTF-8")
    except locale.Error:
        pass

    print("Récupération des flux RSS…")
    sections = scraper_flux()

    if not sections:
        print("Aucun article récupéré. Vérifiez votre connexion.")
        sys.exit(1)

    total = sum(len(arts) for arts in sections.values())
    print(f"{total} articles récupérés dans {len(sections)} catégories.")

    print("Construction de l'email…")
    html = construire_email(sections)

    if args.preview:
        chemin = Path(args.output)
        chemin.write_text(html, encoding="utf-8")
        print(f"Preview sauvegardée : {chemin.resolve()}")
    else:
        if not all([RESEND_API_KEY, EMAIL_TO]):
            print("Erreur : configurez RESEND_API_KEY et EMAIL_TO dans .env")
            sys.exit(1)
        print(f"Envoi à {EMAIL_TO}…")
        envoyer_email(html, EMAIL_TO)
        print("Email envoyé.")


if __name__ == "__main__":
    main()
