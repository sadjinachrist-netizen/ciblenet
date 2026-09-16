# llm.py — Génération de messages via Groq (llama-3.3-70b-versatile), avec bascule de clé et repli local
import os

import httpx

from scoring import offre_recommandee

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "llama-3.3-70b-versatile"


def cles() -> list[str]:
    """2 clés API configurées avec bascule automatique (GROQ_API_KEY, GROQ_API_KEY_2)."""
    return [k for k in (os.environ.get("GROQ_API_KEY"), os.environ.get("GROQ_API_KEY_2")) if k]


def mode() -> str:
    return "Groq (Llama 3.3)" if cles() else "mode démo (templates)"


PROMPT_CONTACT = """Tu es commercial chez Yas Togo, division Yas Business.
Rédige un email de prospection court en français à destination de :
Entreprise : {nom}
Secteur : {secteur}
Ville : {localisation}
Effectif : {effectif} salariés
Signal de croissance : {signal_croissance}
Raisons du score ICP : {score_reasons}
Offre à mettre en avant : {offre}
Présente l'offre Yas Business (Fibre Pro, Flotte mobile, Mixx Business, API SMS) en insistant sur l'offre à mettre en avant.
Personnalise en citant UNE raison du score.
Maximum 100 mots. Ton professionnel et direct.
Termine par une proposition de rendez-vous."""

PROMPT_RELANCE = """Tu es commercial chez Yas Togo, division Yas Business.
Rédige une relance très courte (60 mots maximum) en français pour {nom} ({secteur}, {localisation}),
qui n'a pas répondu à ton premier email envoyé il y a 3 jours.
Ton différent du premier message : plus léger, une seule question, pas de liste d'offres.
Rappelle en une phrase l'offre {offre}. Termine par une proposition de créneau."""


def _appeler_groq(prompt: str) -> str:
    derniere_erreur = None
    for cle in cles():
        try:
            r = httpx.post(GROQ_URL, timeout=20, headers={"Authorization": f"Bearer {cle}"},
                           json={"model": MODEL, "temperature": 0.6, "max_tokens": 300,
                                 "messages": [{"role": "user", "content": prompt}]})
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"].strip()
        except (httpx.HTTPError, KeyError) as exc:
            derniere_erreur = exc   # bascule sur la clé suivante
    raise RuntimeError(f"Groq indisponible : {derniere_erreur}")


def _template_contact(e: dict, offre: str) -> str:
    raison = (e.get("score_reasons") or "").split("\n")[0].lstrip("+0123456789 ")
    return (f"Bonjour,\n\nJe suis commercial chez Yas Business. J'ai remarqué que {e['nom']} "
            f"({raison.lower()}) est en pleine dynamique, et je pense que notre offre {offre} "
            f"peut accompagner votre croissance à {e.get('localisation', 'Lomé')}.\n\n"
            f"Yas Business propose aussi la Fibre Pro, la Flotte mobile et l'API SMS, adaptées aux PME togolaises.\n\n"
            f"Auriez-vous 20 minutes cette semaine pour un échange ?\n\nCordialement,\nL'équipe Yas Business")


def _template_relance(e: dict, offre: str) -> str:
    return (f"Bonjour,\n\nPetit message pour faire suite à mon email de la semaine : est-ce que le sujet "
            f"{offre.split(' (')[0]} est d'actualité chez {e['nom']} ?\n\n"
            f"Je peux passer vous voir mardi ou jeudi matin, à votre convenance.\n\nBien à vous,\nL'équipe Yas Business")


def generer_message(e: dict, relance: bool = False) -> tuple[str, str]:
    """Retourne (message, source) — source = 'groq' ou 'template'."""
    offre = offre_recommandee(e)
    if cles():
        try:
            prompt = (PROMPT_RELANCE if relance else PROMPT_CONTACT).format(offre=offre, **{
                k: e.get(k, "") for k in ("nom", "secteur", "localisation", "effectif", "signal_croissance", "score_reasons")})
            return _appeler_groq(prompt), "groq"
        except RuntimeError:
            pass  # repli sur le template, la démo ne bloque jamais
    return (_template_relance(e, offre) if relance else _template_contact(e, offre)), "template"
