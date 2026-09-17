# database.py — Gestion SQLite (zéro configuration)
import csv
import os
import sqlite3
from datetime import date, datetime, timedelta

from scoring import score_prospect

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ciblenet.db")
CSV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "entreprises.csv")

STATUTS = ["Nouveau", "Scoré", "Contacté", "Relancé", "Converti", "Non intéressé", "À relancer plus tard"]
DELAI_RELANCE_JOURS = 3

SCHEMA = """
CREATE TABLE IF NOT EXISTS entreprises (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nom TEXT NOT NULL UNIQUE,
    secteur TEXT,
    localisation TEXT,
    effectif INTEGER,
    signal_croissance TEXT,
    site_web INTEGER DEFAULT 0,
    paiement_en_ligne INTEGER DEFAULT 0,
    score INTEGER,
    score_reasons TEXT,
    statut TEXT DEFAULT 'Nouveau',
    date_contact DATE,
    message_genere TEXT
);
CREATE TABLE IF NOT EXISTS actions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entreprise_id INTEGER NOT NULL,
    type TEXT NOT NULL,
    detail TEXT,
    date TEXT NOT NULL
);
"""


def connexion() -> sqlite3.Connection:
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


def init_db(reset: bool = False) -> int:
    """Crée les tables et charge le dataset CSV si la base est vide. Retourne le nombre d'entreprises."""
    con = connexion()
    con.executescript(SCHEMA)
    if "email" not in [r[1] for r in con.execute("PRAGMA table_info(entreprises)")]:
        con.execute("ALTER TABLE entreprises ADD COLUMN email TEXT")   # ajout après coup : migration douce
    if reset:
        # on vide les données (le profil de l'entreprise, table parametres, est conservé)
        con.execute("DELETE FROM actions")
        con.execute("DELETE FROM entreprises")
        con.commit()
    n = con.execute("SELECT COUNT(*) FROM entreprises").fetchone()[0]
    if n == 0:
        n = importer_csv(CSV_PATH, con)
    con.close()
    return n


def importer_csv(chemin, con=None) -> int:
    """Importe un CSV (séparateur ; ou ,). Les doublons de nom sont ignorés."""
    fermer = con is None
    con = con or connexion()
    with open(chemin, encoding="utf-8-sig") as f:
        texte = f.read()
    sep = ";" if texte.count(";") >= texte.count(",") else ","
    n = 0
    for row in csv.DictReader(texte.splitlines(), delimiter=sep):
        row = {k.strip().lower(): (v or "").strip() for k, v in row.items() if k}
        if not row.get("nom"):
            continue
        try:
            con.execute(
                "INSERT INTO entreprises (nom, secteur, localisation, effectif, signal_croissance, site_web, paiement_en_ligne, email) VALUES (?,?,?,?,?,?,?,?)",
                (row["nom"], row.get("secteur"), row.get("localisation") or row.get("ville"), int(row.get("effectif") or 0),
                 row.get("signal_croissance") or "", int(row.get("site_web") in ("1", "oui", "true")), int(row.get("paiement_en_ligne") in ("1", "oui", "true")),
                 row.get("email") or row.get("email_contact") or None),
            )
            n += 1
        except sqlite3.IntegrityError:
            pass  # doublon
    con.commit()
    if fermer:
        con.close()
    return n


def lister(secteur=None, ville=None, tranche=None, statut=None) -> list[dict]:
    q, params = "SELECT * FROM entreprises WHERE 1=1", []
    if secteur and secteur != "Tous":
        q += " AND secteur = ?"; params.append(secteur)
    if ville and ville != "Toutes":
        q += " AND localisation = ?"; params.append(ville)
    if tranche and tranche != "Toutes":
        lo, hi = {"1-9": (0, 9), "10-49": (10, 49), "50-250": (50, 250), "250+": (251, 10**9)}[tranche]
        q += " AND effectif BETWEEN ? AND ?"; params += [lo, hi]
    if statut:
        q += " AND statut = ?"; params.append(statut)
    q += " ORDER BY COALESCE(score, -1) DESC, nom"
    con = connexion()
    rows = [dict(r) for r in con.execute(q, params).fetchall()]
    con.close()
    return rows


def obtenir(eid: int) -> dict | None:
    con = connexion()
    r = con.execute("SELECT * FROM entreprises WHERE id = ?", (eid,)).fetchone()
    con.close()
    return dict(r) if r else None


def scorer_tous() -> int:
    """Calcule le score de toutes les entreprises et passe les 'Nouveau' en 'Scoré'."""
    con = connexion()
    n = 0
    for r in con.execute("SELECT * FROM entreprises").fetchall():
        s, reasons, _ = score_prospect(dict(r))
        con.execute("UPDATE entreprises SET score = ?, score_reasons = ?, statut = CASE WHEN statut = 'Nouveau' THEN 'Scoré' ELSE statut END WHERE id = ?",
                    (s, "\n".join(reasons), r["id"]))
        n += 1
    con.commit()
    con.close()
    return n


def changer_statut(eid: int, statut: str, detail: str = "") -> None:
    con = connexion()
    if statut == "Contacté":
        con.execute("UPDATE entreprises SET statut = ?, date_contact = ? WHERE id = ?", (statut, date.today().isoformat(), eid))
    else:
        con.execute("UPDATE entreprises SET statut = ? WHERE id = ?", (statut, eid))
    con.execute("INSERT INTO actions (entreprise_id, type, detail, date) VALUES (?,?,?,?)",
                (eid, f"Statut → {statut}", detail, datetime.now().isoformat(timespec="minutes")))
    con.commit()
    con.close()


def enregistrer_message(eid: int, message: str, type_action: str = "Message généré") -> None:
    con = connexion()
    con.execute("UPDATE entreprises SET message_genere = ? WHERE id = ?", (message, eid))
    con.execute("INSERT INTO actions (entreprise_id, type, detail, date) VALUES (?,?,?,?)",
                (eid, type_action, message, datetime.now().isoformat(timespec="minutes")))
    con.commit()
    con.close()


def simuler_j3(eid: int) -> None:
    """Pour la démo : recule la date de contact de 3 jours afin que la relance devienne due."""
    con = connexion()
    con.execute("UPDATE entreprises SET date_contact = ? WHERE id = ?",
                ((date.today() - timedelta(days=DELAI_RELANCE_JOURS)).isoformat(), eid))
    con.commit()
    con.close()


def relance_due(e: dict) -> bool:
    """Règle : statut Contacté et aucune réponse depuis 3 jours."""
    if e.get("statut") != "Contacté" or not e.get("date_contact"):
        return False
    return (date.today() - date.fromisoformat(e["date_contact"])).days >= DELAI_RELANCE_JOURS


def actions(eid: int) -> list[dict]:
    con = connexion()
    rows = [dict(r) for r in con.execute("SELECT * FROM actions WHERE entreprise_id = ? ORDER BY date DESC", (eid,)).fetchall()]
    con.close()
    return rows


def compteurs() -> dict:
    con = connexion()
    d = {s: 0 for s in STATUTS}
    for st, n in con.execute("SELECT statut, COUNT(*) FROM entreprises GROUP BY statut"):
        d[st] = n
    con.close()
    return d


def exporter_csv(chemin: str) -> str:
    """Backup : même contenu que la table, consultable dans Excel / Google Sheets."""
    rows = lister()
    with open(chemin, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else ["id"], delimiter=";")
        w.writeheader()
        w.writerows(rows)
    return chemin


def journaliser(eid: int, type_action: str, detail: str) -> None:
    """Trace une action (envoi Gmail, WhatsApp, SMS, Discord…) dans l'historique du prospect."""
    con = connexion()
    con.execute("INSERT INTO actions (entreprise_id, type, detail, date) VALUES (?,?,?,?)",
                (eid, type_action, detail, datetime.now().isoformat(timespec="minutes")))
    con.commit()
    con.close()
