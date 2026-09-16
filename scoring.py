# scoring.py — Moteur de scoring ICP Yas Business
# Python pur, aucune dépendance. Chaque point attribué est explicable.

SECTEURS = ["Banque", "Assurance", "Logistique", "Éducation", "Informatique", "Santé",
            "Commerce", "Industrie", "Agroalimentaire", "Conseil", "Autres"]
VILLES = ["Lomé", "Kara", "Tsevié", "Autres"]
TRANCHES = ["1-9", "10-49", "50-250", "250+"]

SEUIL_HAUTE = 75
SEUIL_MOYENNE = 60


def tranche(effectif: int) -> str:
    if effectif < 10:
        return "1-9"
    if effectif < 50:
        return "10-49"
    if effectif <= 250:
        return "50-250"
    return "250+"


def score_prospect(company: dict):
    """
    Calcule le score ICP d'une entreprise.
    Retourne (score, reasons, status) — reasons est une liste de chaînes "+N raison".
    """
    score, reasons = 0, []
    sector = company.get("secteur", "") or ""
    employees = int(company.get("effectif", 0) or 0)
    city = company.get("localisation", "") or ""
    signal = (company.get("signal_croissance", "") or "").strip()

    # Critère 1 - Secteur (30 pts max)
    if sector in ("Banque", "Assurance"):
        pts, why = 30, f"Secteur prioritaire haute valeur ({sector})"
    elif sector in ("Logistique", "Éducation", "Informatique", "Santé"):
        pts, why = 25, f"Secteur prioritaire ({sector})"
    elif sector in ("Commerce", "Industrie"):
        pts, why = 15, f"Secteur secondaire ({sector})"
    else:
        pts, why = 5, f"Secteur hors cible ({sector or 'inconnu'})"
    score += pts
    reasons.append(f"+{pts} {why}")

    # Critère 2 - Effectif (25 pts max)
    if 50 <= employees <= 250:
        pts, why = 25, f"Taille idéale ({employees} salariés)"
    elif 10 <= employees < 50:
        pts, why = 20, f"Taille correcte ({employees} salariés)"
    elif 250 < employees <= 500:
        pts, why = 15, f"Grande entreprise, cycle long ({employees} salariés)"
    else:
        pts, why = 5, f"Taille hors cible ({employees} salariés)"
    score += pts
    reasons.append(f"+{pts} {why}")

    # Critère 3 - Localisation (20 pts max)
    if city == "Lomé":
        pts, why = 20, "Lomé, couverture Fibre optimale"
    elif city == "Kara":
        pts, why = 15, "Kara, couverture Fibre partielle"
    else:
        pts, why = 5, f"Hors zone prioritaire ({city or 'inconnue'})"
    score += pts
    reasons.append(f"+{pts} {why}")

    # Critère 4 - Signal de croissance (25 pts max)
    if signal and signal.lower() != "aucun":
        score += 25
        reasons.append(f"+25 Signal d'expansion : {signal}")
    else:
        reasons.append("+0 Aucun signal de croissance détecté")

    if score >= SEUIL_HAUTE:
        status = "QUALIFIE_HAUTE_PRIORITE"
    elif score >= SEUIL_MOYENNE:
        status = "QUALIFIE_PRIORITE_MOYENNE"
    else:
        status = "DISQUALIFIE"
    return score, reasons, status


LABELS = {
    "QUALIFIE_HAUTE_PRIORITE": "🔥 Qualifié — haute priorité (contact immédiat)",
    "QUALIFIE_PRIORITE_MOYENNE": "🟡 Qualifié — priorité moyenne (template + variables)",
    "DISQUALIFIE": "⚪ Disqualifié (mise en nurture)",
}


def offre_recommandee(company: dict) -> str:
    """Choisit l'offre Yas Business à mettre en avant selon le profil."""
    sector = company.get("secteur", "")
    employees = int(company.get("effectif", 0) or 0)
    if sector in ("Banque", "Assurance", "Commerce"):
        return "Mixx Business (encaissement marchand, virements groupés)"
    if sector == "Logistique" or employees >= 50:
        return "Flotte mobile (forfaits SIM groupés pour vos équipes)"
    if sector in ("Informatique", "Éducation", "Santé"):
        return "Fibre Pro (internet très haut débit dédié)"
    return "Fibre Pro + API SMS"


if __name__ == "__main__":
    import csv, sys
    ok = True
    with open("data/entreprises.csv", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f, delimiter=";"):
            s, r, st = score_prospect(row)
            attendu = int(row.get("score_attendu") or -1)
            flag = "OK " if s == attendu else "!! "
            ok &= s == attendu
            print(f"{flag}{row['nom']:<32} {s:>3}/100  attendu {attendu:>3}  {st}")
    sys.exit(0 if ok else 1)
