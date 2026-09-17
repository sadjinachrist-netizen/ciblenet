# notifier.py — Canaux de notification : Gmail (SMTP), WhatsApp et SMS (Twilio), Discord (webhook.py)
# Une seule fonction publique : envoyer(canal, sujet, texte, destinataire=None) -> (ok, detail).
# Chaque canal est optionnel : sans identifiants dans l'environnement, il est simplement « non configuré ».
import os
import smtplib
from email.message import EmailMessage

import httpx

import webhook

CANAUX = {
    "discord":  {"label": "Discord",  "icone": "🟣"},
    "gmail":    {"label": "Gmail",    "icone": "📧"},
    "whatsapp": {"label": "WhatsApp", "icone": "💬"},
    "sms":      {"label": "SMS",      "icone": "📱"},
}


def _env(*noms: str) -> list[str]:
    return [os.environ.get(n, "").strip() for n in noms]


def configure(canal: str) -> bool:
    if canal == "discord":
        return webhook.configure()
    if canal == "gmail":
        return all(_env("GMAIL_SENDER", "GMAIL_APP_PASSWORD"))
    if canal == "whatsapp":
        return all(_env("TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "TWILIO_WHATSAPP_FROM", "TWILIO_WHATSAPP_TO"))
    if canal == "sms":
        return all(_env("TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "TWILIO_SMS_FROM", "TWILIO_SMS_TO"))
    return False


def canaux_actifs() -> list[str]:
    return [c for c in CANAUX if configure(c)]


# ---------------------------------------------------------------- Gmail (SMTP + App Password)
def envoyer_gmail(sujet: str, texte: str, destinataire: str | None = None) -> tuple[bool, str]:
    expediteur, mdp, defaut = _env("GMAIL_SENDER", "GMAIL_APP_PASSWORD", "GMAIL_RECIPIENT")
    dest = destinataire or defaut
    if not (expediteur and mdp and dest):
        return False, "Gmail non configuré (GMAIL_SENDER, GMAIL_APP_PASSWORD, GMAIL_RECIPIENT)"
    msg = EmailMessage()
    msg["From"], msg["To"], msg["Subject"] = expediteur, dest, sujet
    msg.set_content(texte)
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=20) as s:
            s.login(expediteur, mdp.replace(" ", ""))   # l'App Password est affiché avec des espaces
            s.send_message(msg)
        return True, f"Email envoyé à {dest}"
    except (smtplib.SMTPException, OSError) as exc:
        return False, f"Échec Gmail : {exc}"


# ---------------------------------------------------------------- Twilio (WhatsApp / SMS) en HTTP direct
def _twilio(de: str, vers: str, texte: str) -> tuple[bool, str]:
    sid, token = _env("TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN")
    if not (sid and token and de and vers):
        return False, "Twilio non configuré"
    try:
        r = httpx.post(f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json",
                       auth=(sid, token), data={"From": de, "To": vers, "Body": texte[:1500]}, timeout=20)
        if r.status_code >= 400:
            return False, f"Twilio {r.status_code} : {r.json().get('message', r.text[:120])}"
        return True, f"Message envoyé à {vers} (SID {r.json().get('sid', '?')[:8]}…)"
    except httpx.HTTPError as exc:
        return False, f"Échec Twilio : {exc}"


def envoyer_whatsapp(texte: str, destinataire: str | None = None) -> tuple[bool, str]:
    de, defaut = _env("TWILIO_WHATSAPP_FROM", "TWILIO_WHATSAPP_TO")
    vers = destinataire or defaut
    if vers and not vers.startswith("whatsapp:"):
        vers = "whatsapp:" + vers
    return _twilio(de, vers, texte)


def envoyer_sms(texte: str, destinataire: str | None = None) -> tuple[bool, str]:
    de, defaut = _env("TWILIO_SMS_FROM", "TWILIO_SMS_TO")
    return _twilio(de, destinataire or defaut, texte[:600])   # un SMS long est segmenté et facturé par segment


# ---------------------------------------------------------------- point d'entrée unique
def envoyer(canal: str, sujet: str, texte: str, destinataire: str | None = None) -> tuple[bool, str]:
    if canal == "discord":
        ok, _ = webhook.envoyer_handoff_texte(texte)
        return ok, ("Notification Discord envoyée" if ok else "Discord non configuré ou injoignable")
    if canal == "gmail":
        return envoyer_gmail(sujet, texte, destinataire)
    if canal == "whatsapp":
        return envoyer_whatsapp(f"{sujet}\n\n{texte}", destinataire)
    if canal == "sms":
        return envoyer_sms(f"{sujet} — {texte}", destinataire)
    return False, f"Canal inconnu : {canal}"


def envoyer_tous(sujet: str, texte: str) -> dict[str, tuple[bool, str]]:
    """Diffusion sur tous les canaux configurés. Retourne {canal: (ok, detail)}."""
    return {c: envoyer(c, sujet, texte) for c in canaux_actifs()}
