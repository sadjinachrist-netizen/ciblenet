# Script de démo — Yas Prospect Copilot (5 minutes)

## Avant de monter sur scène (checklist)
- [ ] `start.bat` lancé, l'appli s'ouvre sur http://localhost:8501 sans erreur
- [ ] Barre latérale : **LLM : Groq (Llama 3.3)** et **Handoff Discord : configuré** (sinon la démo marche quand même en mode template / notification interne — le dire)
- [ ] Bouton **Réinitialiser la démo** cliqué → 12 entreprises, aucune scorée
- [ ] Discord ouvert sur un second écran, sur le salon du webhook
- [ ] Vidéo de secours accessible en un clic
- [ ] Recherche testée une fois : Logistique + Lomé + 10-49 → Togo Logistique SA

## Ouverture (30 s)
« Un commercial Yas Business perd 4 heures par jour à chercher des prospects à la main, dans des fichiers dispersés,
sans savoir lesquels valent vraiment un appel. Voici notre copilote : construit en 4 jours, zéro budget,
et chaque décision de l'IA est expliquée par une raison métier. »

## Étape 1 — Identifier (1 min) — onglet Recherche & Scoring
1. Secteur **Logistique**, localisation **Lomé**, taille **10-49** → **Rechercher**.
2. Le tableau affiche Togo Logistique SA (score vide).
3. Cliquer **✨ Scorer toutes les entreprises** : « 12 entreprises scorées instantanément ».
4. Remettre les filtres sur **Tous / Toutes / Toutes** → Rechercher : le tableau est trié par score.

## Étape 2 — Qualifier (1 min 30)
1. Dans « Voir le détail du score de », choisir **Togo Logistique SA — 90/100**.
2. Lire les 4 raisons :
   - +25 Secteur prioritaire (Logistique)
   - +20 Taille correcte (45 salariés)
   - +20 Lomé, couverture Fibre optimale
   - +25 Signal d'expansion : Recrutement informatique
3. « Chaque point est explicable. Un commercial peut contester ou ajuster. »
4. Choisir **Boulangerie de la Paix — 15/100** : « Disqualifié : secteur hors cible, 8 salariés, Tsevié, aucun signal. Le scoring discrimine vraiment. »
5. Montrer l'**offre recommandée** (Flotte mobile pour Togo Logistique).

## Étape 3 — Prospecter (1 min) — onglet Pipeline
1. Sélectionner **Togo Logistique SA** → **✉️ Générer message** (< 2 s).
2. Lire l'email à voix haute : il cite « Recrutement informatique » et l'offre Flotte mobile, < 100 mots, propose un rendez-vous.
3. **📤 Marquer contacté** : la carte passe dans la colonne Contacté avec la date du jour.

## Étape 4 — Relancer & Convertir (1 min)
1. **⏩ Simuler J+3** : la cloche 🔔 apparaît, « relance due : aucune réponse depuis 3 jours ».
2. **🔁 Relancer** : relance courte, ton différent, la carte passe en Relancé.
3. **✅ Converti**.
4. Onglet **Handoff** → **🤝 Transmettre** : la notification apparaît **en direct sur Discord**
   (« Transmis au responsable commercial Yas Business », secteur, effectif, score, message).
   Si Discord ne répond pas : la même notification s'affiche dans l'appli.

## Clôture (30 s) — onglet Tableau de bord
« 12 prospects : 4 heures de recherche manuelle, 15 minutes avec le copilote. Le backup CSV est téléchargeable
à tout moment, et pour passer à 1 000 entreprises : PostgreSQL, file d'attente pour le webhook, et génération
temps réel réservée aux scores > 75. Merci. »

## Réponses prêtes aux questions du jury
- **D'où viennent les entreprises ?** Dataset de démonstration (noms fictifs). En production : import du fichier CFE / CCI,
  ou recherche OpenStreetMap par secteur et ville.
- **Pourquoi Discord ?** C'est un webhook : le même code alimente Slack, Teams ou un email.
- **Et si Groq tombe ?** Deux clés avec bascule automatique, puis templates locaux : la démo ne bloque jamais.
- **Le signal de croissance, vous le trouvez comment ?** Saisi par le business developer ou détecté sur le site / LinkedIn ;
  c'est le critère le plus fort du score, donc il doit être vérifié par un humain.
