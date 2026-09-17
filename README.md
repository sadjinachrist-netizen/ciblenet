# CibleNet

Copilote commercial pour PME : **identifier, qualifier, prospecter, relancer et convertir** les meilleurs prospects B2B,
dans un seul outil simple, gratuit et explicable. L'entreprise utilisatrice configure son profil (nom, offres, secteurs et zones
prioritaires) ; le scoring, les messages générés et le handoff s'y adaptent.

Réalisé pour le Projet 1 « Identifier les bons prospects » — ACAN Campus, Lomé IA Summer School 2026.

## Lancer

```bash
pip install -r requirements.txt
streamlit run app.py
```

ou double-clic sur `start.bat` (Windows, charge automatiquement le fichier `.env`).

Variables optionnelles (copier `.env.example` en `.env`, ou les mettre dans les *Secrets* Streamlit Cloud) :

| Variable | Rôle | Sans elle |
|---|---|---|
| `GROQ_API_KEY`, `GROQ_API_KEY_2` | Génération des messages par Llama 3.3 (bascule automatique entre les 2 clés) | Templates locaux, la démo fonctionne |
| `DISCORD_WEBHOOK_URL` | Handoff réel sur Discord | Notification interne affichée dans l'appli |

## Structure

```
ciblenet/
├── app.py              # Interface Streamlit : Recherche & Scoring · Pipeline · Handoff · Tableau de bord · Paramètres
├── config.py           # Nom de la plateforme + profil de l'entreprise (offres, grille de scoring), stocké en base
├── scoring.py          # Moteur de scoring ICP (Python pur) — `python scoring.py` vérifie le dataset
├── llm.py              # Appel Groq (2 clés, repli template), prompts paramétrés par le profil
├── database.py         # SQLite : entreprises, actions, statuts, relance J+3, export CSV
├── webhook.py          # Handoff Discord
├── lss.py              # Import du jeu de données officiel LSS 2026
├── ui.py               # Habillage (CSS, en-tête, indicateurs, cartes)
├── data/entreprises.csv   # Dataset de démonstration : 12 PME togolaises (noms fictifs)
├── data/lss/              # Jeu officiel LSS 2026 — 01_Prospection
├── demo/demo_script.md    # Script de démo 5 min + réponses aux questions du jury
├── requirements.txt
└── README.md
```

## Profil de l'entreprise (onglet Paramètres)

Par défaut, CibleNet est configuré pour **l'entreprise témoin du jeu de données LSS 2026** : une PME de solutions informatiques
(offres : CRM, Développement web, Application mobile, Automatisation, Data/BI, Marketing digital). Toute PME peut saisir son nom,
ses offres, ses secteurs prioritaires (30 / 25 / 15 points) et ses zones (20 / 15 points) ; les prospects sont rescorés aussitôt.

## Données officielles LSS 2026

Le bouton **« Charger les données LSS 2026 »** (barre latérale) remplace le dataset de démo par le jeu fourni par les organisateurs
(`data/lss/`, fichier `01_Prospection` : 150 prospects après dédoublonnage, 250 interactions). Mapping : Finance → Banque,
Technologie → Informatique, Distribution → Commerce, Services → Conseil ; Agoè-Nyivé → Lomé, Kpalimé / Atakpamé → Autres ;
En discussion → Contacté, À relancer → Relancé, Refusé → Non intéressé. Le « besoin potentiel » du fichier est utilisé comme
signal d'intention. Les interactions alimentent l'historique.

## Scoring (100 points, chaque point expliqué)

| Critère | Max | Barème (profil par défaut) |
|---|---|---|
| Secteur | 30 | Banque, Assurance : 30 · Logistique, Éducation, Informatique, Santé : 25 · Commerce, Industrie : 15 · autres : 5 |
| Effectif | 25 | 50-250 : 25 · 10-49 : 20 · 251-500 : 15 · sinon : 5 |
| Zone | 20 | Lomé : 20 · Kara : 15 · autres : 5 |
| Signal de croissance | 25 | présent : 25 · absent : 0 |

Seuils : **≥ 75** haute priorité (contact immédiat) · **≥ 60** priorité moyenne (template + variables) · **< 60** disqualifié (nurture).

## Pipeline

`Nouveau → Scoré → Contacté → Relancé → Converti`, avec sorties `Non intéressé` (archivé) et `À relancer plus tard` (nurture).
Règle de relance : statut *Contacté* sans réponse depuis 3 jours → relance due (bouton « Simuler J+3 » pour la démo).
Toutes les actions (messages, changements de statut, handoff) sont historisées dans la table `actions`.
