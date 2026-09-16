# Yas Prospect Copilot

Copilote commercial pour **Yas Business** (Yas Togo / Mixx by Yas) : identifier, qualifier, prospecter, relancer et convertir
les meilleures PME togolaises — dans un seul outil simple, gratuit et explicable.

Réalisé pour le Projet 1 « Identifier les bons prospects » — ACAN Campus, Lomé IA Summer School 2026.
Conforme au *Cahier des charges final — Projet Yas Prospect Copilot* (Streamlit + SQLite + Groq + webhook Discord + backup).

## Lancer

```bash
pip install -r requirements.txt
streamlit run app.py
```

ou double-clic sur `start.bat` (Windows, charge automatiquement le fichier `.env`).

Variables optionnelles (copier `.env.example` en `.env`) :

| Variable | Rôle | Sans elle |
|---|---|---|
| `GROQ_API_KEY`, `GROQ_API_KEY_2` | Génération des messages par Llama 3.3 (bascule automatique entre les 2 clés) | Templates locaux, la démo fonctionne |
| `DISCORD_WEBHOOK_URL` | Handoff réel sur Discord | Notification interne affichée dans l'appli |

## Structure

```
yas-prospect-copilot/
├── app.py              # Interface Streamlit : Recherche & Scoring · Pipeline · Handoff · Tableau de bord
├── scoring.py          # Moteur de scoring ICP Yas Business (Python pur) — `python scoring.py` vérifie le dataset
├── llm.py              # Appel Groq (2 clés, repli template)
├── database.py         # SQLite : entreprises, actions, statuts, relance J+3, export CSV
├── webhook.py          # Handoff Discord
├── data/entreprises.csv   # Dataset de démonstration : 12 PME togolaises (noms fictifs)
├── demo/demo_script.md    # Script de démo 5 min + réponses aux questions du jury
├── requirements.txt
└── README.md
```

## Scoring (100 points, chaque point expliqué)

| Critère | Max | Barème |
|---|---|---|
| Secteur | 30 | Banque, Assurance : 30 · Logistique, Éducation, Informatique, Santé : 25 · Commerce, Industrie : 15 · autres : 5 |
| Effectif | 25 | 50-250 : 25 · 10-49 : 20 · 251-500 : 15 · sinon : 5 |
| Localisation | 20 | Lomé : 20 · Kara : 15 · autres : 5 |
| Signal de croissance | 25 | présent : 25 · absent : 0 |

Seuils : **≥ 75** haute priorité (contact immédiat) · **≥ 60** priorité moyenne (template + variables) · **< 60** disqualifié (nurture).

## Pipeline

`Nouveau → Scoré → Contacté → Relancé → Converti`, avec sorties `Non intéressé` (archivé) et `À relancer plus tard` (nurture).
Règle de relance : statut *Contacté* sans réponse depuis 3 jours → relance due (bouton « Simuler J+3 » pour la démo).
Toutes les actions (messages, changements de statut, handoff) sont historisées dans la table `actions`.

## Différences assumées avec le cahier des charges

- Les **scores attendus** du dataset ont été recalculés avec `scoring.py` (8 valeurs du cahier étaient incohérentes avec le code).
- Les **seuils** sont unifiés à 75 / 60 (le cahier mélangeait 50 et 60).
- Le secteur **Santé** est ajouté (une clinique était classée en Éducation).
- Les entreprises portent des **noms fictifs** : pas de faits inventés sur des sociétés réelles.
- Le **backup Google Sheets** est remplacé par un export CSV téléchargeable (importable dans Google Sheets en un clic) :
  même service pour le jury, sans compte de service Google à configurer.
- Ajout d'un **historique des actions** et d'une **date de contact** réelle pour que la relance J+3 soit une règle et non une simulation.
