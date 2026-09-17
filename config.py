# config.py — Identité de la plateforme et profil de l'entreprise utilisatrice (PME), stocké en base
import json
import sqlite3

APP_NOM = "CibleNet"
APP_SLOGAN = "Identifier · Qualifier · Prospecter · Relancer · Convertir — le copilote commercial des PME"

# Profil par défaut : l'entreprise témoin du jeu de données LSS 2026 (PME de solutions informatiques)
PROFIL_DEFAUT = {
    "entreprise": "Entreprise A",
    "activite": "PME de solutions informatiques pour les entreprises togolaises",
    "offres": ["CRM", "Développement web", "Application mobile", "Automatisation", "Data/BI", "Marketing digital"],
    "secteurs_30": ["Banque", "Assurance"],
    "secteurs_25": ["Logistique", "Éducation", "Informatique", "Santé"],
    "secteurs_15": ["Commerce", "Industrie"],
    "villes_20": ["Lomé"],
    "villes_15": ["Kara"],
    "signature": "L'équipe commerciale",
}


def _table(con: sqlite3.Connection) -> None:
    con.execute("CREATE TABLE IF NOT EXISTS parametres (cle TEXT PRIMARY KEY, valeur TEXT NOT NULL)")


def charger(con: sqlite3.Connection) -> dict:
    """Profil actif : valeurs par défaut complétées par ce qui est enregistré en base."""
    _table(con)
    row = con.execute("SELECT valeur FROM parametres WHERE cle = 'profil'").fetchone()
    profil = dict(PROFIL_DEFAUT)
    if row:
        profil.update(json.loads(row[0]))
    return profil


def enregistrer(con: sqlite3.Connection, profil: dict) -> None:
    _table(con)
    con.execute("INSERT OR REPLACE INTO parametres (cle, valeur) VALUES ('profil', ?)", (json.dumps(profil, ensure_ascii=False),))
    con.commit()


_cache: dict | None = None


def profil() -> dict:
    """Accès rapide au profil courant (cache en mémoire, invalidé par rafraichir())."""
    global _cache
    if _cache is None:
        import database
        con = database.connexion()
        _cache = charger(con)
        con.close()
    return _cache


def rafraichir() -> None:
    global _cache
    _cache = None
