# lss.py — Import du jeu de données officiel « LSS 2026 — 01_Prospection » (153 prospects, 250 interactions)
# On mappe secteurs, villes et statuts sur le vocabulaire de la grille de scoring.
import csv
import os
import sqlite3

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "lss")

# secteur LSS -> secteur de la grille de scoring
SECTEURS = {"Finance": "Banque", "Technologie": "Informatique", "Distribution": "Commerce", "Services": "Conseil",
            "Immobilier": "Autres", "Logistique": "Logistique", "Commerce": "Commerce", "Agroalimentaire": "Agroalimentaire",
            "Santé": "Santé", "Industrie": "Industrie", "Éducation": "Éducation"}
# ville LSS -> zone (Agoè-Nyivé fait partie du Grand Lomé)
VILLES = {"Lomé": "Lomé", "Agoè-Nyivé": "Lomé", "Kara": "Kara", "Tsévié": "Tsevié", "Kpalimé": "Autres", "Atakpamé": "Autres"}
# statut LSS -> statut du pipeline
STATUTS = {"Nouveau": "Nouveau", "Contacté": "Contacté", "En discussion": "Contacté", "À relancer": "Relancé",
           "Converti": "Converti", "Refusé": "Non intéressé"}


def _lire(nom):
    with open(os.path.join(DATA_DIR, nom), encoding="utf-8-sig", newline="") as f:
        return [{k.strip(): (v or "").strip() for k, v in r.items()} for r in csv.DictReader(f)]


def disponible() -> bool:
    return os.path.exists(os.path.join(DATA_DIR, "01_Prospection_prospects.csv"))


def importer(con: sqlite3.Connection) -> dict:
    """Remplace le contenu de la base par le jeu LSS 2026. Retourne les compteurs."""
    con.execute("DELETE FROM actions")
    con.execute("DELETE FROM entreprises")
    ids, doublons = {}, 0
    for r in _lire("01_Prospection_prospects.csv"):
        if r["prospect_id"] in ids:
            doublons += 1          # 3 identifiants dupliqués dans le fichier source
            continue
        # un besoin exprimé est traité comme signal d'intention (le fichier n'a pas de signal de croissance)
        signal = f"Besoin exprimé : {r['besoin_potentiel']}" if r["besoin_potentiel"] else ""
        statut = STATUTS.get(r["statut"], "Nouveau")
        cur = con.execute(
            "INSERT INTO entreprises (nom, secteur, localisation, effectif, signal_croissance, site_web, paiement_en_ligne, statut, date_contact, email) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (r["entreprise"], SECTEURS.get(r["secteur"], "Autres"), VILLES.get(r["ville"], "Autres"), int(r["taille_effectif"] or 0),
             signal, int(bool(r["email"])), 0, statut, r["date_dernier_contact"] or None, r["email"] or None))
        ids[r["prospect_id"]] = cur.lastrowid
    n_act = 0
    for r in _lire("01_Prospection_interactions.csv"):
        eid = ids.get(r["prospect_id"])
        if not eid:
            continue
        detail = f"{r['canal']} — {r['resultat']}" + (f" — {r['commentaire']}" if r["commentaire"] else "")
        con.execute("INSERT INTO actions (entreprise_id, type, detail, date) VALUES (?,?,?,?)", (eid, r["action"], detail, r["date"]))
        n_act += 1
    con.commit()
    return {"prospects": len(ids), "doublons_ignores": doublons, "interactions": n_act}
