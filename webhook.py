# webhook.py — Handoff réel : notification Discord (ou tout webhook compatible : Slack, Teams via Power Automate…)
import os

import httpx

import config


def configure() -> bool:
    return bool(os.environ.get("DISCORD_WEBHOOK_URL"))


def message_handoff(e: dict) -> str:
    return (f"✅ **Prospect converti : {e['nom']}**\n"
            f"Transmis au responsable commercial de {config.profil()['entreprise']}\n"
            f"Secteur : {e.get('secteur')} | Effectif : {e.get('effectif')} | Ville : {e.get('localisation')}\n"
            f"Score ICP : {e.get('score')}/100\n"
            f"Message généré : {(e.get('message_genere') or '—')[:900]}")


def envoyer_handoff(e: dict) -> tuple[bool, str]:
    """Retourne (envoyé, texte). Sans webhook configuré ou en cas d'échec, le texte sert de notification interne."""
    texte = message_handoff(e)
    url = os.environ.get("DISCORD_WEBHOOK_URL")
    if not url:
        return False, texte
    try:
        r = httpx.post(url, json={"content": texte}, timeout=10)
        r.raise_for_status()
        return True, texte
    except httpx.HTTPError:
        return False, texte


def envoyer_handoff_texte(texte: str) -> tuple[bool, str]:
    """Envoie un texte déjà composé (utilisé par notifier.py)."""
    url = os.environ.get("DISCORD_WEBHOOK_URL")
    if not url:
        return False, texte
    try:
        r = httpx.post(url, json={"content": texte[:1900]}, timeout=10)
        r.raise_for_status()
        return True, texte
    except httpx.HTTPError:
        return False, texte
