# app.py — CibleNet : interface Streamlit (Recherche & Scoring · Pipeline · Handoff · Tableau de bord · Paramètres)
import os
import tempfile

import pandas as pd
import streamlit as st

import config
import database as db
import llm
import lss
import notifier
import ui
import webhook
from scoring import SECTEURS, VILLES, TRANCHES, LABELS, score_prospect, offre_recommandee

st.set_page_config(page_title=config.APP_NOM, page_icon="🎯", layout="wide")

# Streamlit Cloud : les secrets (GROQ_API_KEY, GROQ_API_KEY_2, DISCORD_WEBHOOK_URL) sont exposés comme variables d'environnement
try:
    for _k, _v in st.secrets.items():
        if isinstance(_v, str):
            os.environ.setdefault(_k, _v)
except Exception:
    pass  # pas de fichier secrets en local : on utilise .env / les variables système

db.init_db()
ui.injecter_css()

# ---------- barre latérale ----------
with st.sidebar:
    st.title(f"🎯 {config.APP_NOM}")
    st.caption(f"{config.APP_SLOGAN} — profil actif : **{config.profil()['entreprise']}**")
    st.markdown(f"**LLM :** {llm.mode()}")
    actifs = notifier.canaux_actifs()
    st.markdown("**Canaux de notification :** " + (" ".join(f"{notifier.CANAUX[c]['icone']} {notifier.CANAUX[c]['label']}" for c in actifs) if actifs else "⚠️ aucun configuré (notification interne)"))
    st.divider()
    if st.button("🔄 Réinitialiser la démo", use_container_width=True):
        db.init_db(reset=True)
        st.session_state.clear()
        st.rerun()
    if lss.disponible() and st.button("📂 Charger les données LSS 2026", use_container_width=True, help="Jeu officiel des organisateurs : 150 prospects, 250 interactions"):
        con = db.connexion(); r = lss.importer(con); con.close()
        db.scorer_tous()
        st.session_state.clear()
        st.success(f"{r['prospects']} prospects et {r['interactions']} interactions chargés ({r['doublons_ignores']} doublons ignorés)")
    fichier = st.file_uploader("📥 Importer des entreprises (CSV)", type=["csv"], help="Colonnes : nom;secteur;localisation;effectif;signal_croissance")
    if fichier is not None:
        chemin = os.path.join(tempfile.gettempdir(), fichier.name)
        with open(chemin, "wb") as f:
            f.write(fichier.getbuffer())
        n = db.importer_csv(chemin)
        st.success(f"{n} entreprise(s) importée(s)")
    chemin_backup = os.path.join(tempfile.gettempdir(), "backup_ciblenet.csv")
    db.exporter_csv(chemin_backup)
    with open(chemin_backup, "rb") as f:
        st.download_button("💾 Backup CSV (Google Sheets / Excel)", f, "backup_ciblenet.csv", "text/csv", use_container_width=True)


def badge(statut: str) -> str:
    return {"Nouveau": "⚪", "Scoré": "🔵", "Contacté": "🟣", "Relancé": "🟠", "Converti": "🟢",
            "Non intéressé": "🔴", "À relancer plus tard": "🟤"}.get(statut, "") + " " + statut


def fiche(e: dict):
    """Détail d'une entreprise : score et 4 raisons, offre recommandée, historique."""
    score, reasons, status = score_prospect(e)
    c1, c2 = st.columns([1, 2])
    with c1:
        st.markdown(f"<div style='font-size:13px;color:#64748b'>SCORE ICP</div><div style='font-size:40px;font-weight:800;line-height:1'>{score}<span style='font-size:18px;color:#94a3b8'>/100</span></div>", unsafe_allow_html=True)
        st.markdown(LABELS[status])
        st.markdown(f"<div class='offre'>🎯 {offre_recommandee(e)}</div>", unsafe_allow_html=True)
        st.markdown(f"<div style='margin-top:8px'>Statut : <b>{badge(e['statut'])}</b></div>", unsafe_allow_html=True)
    with c2:
        st.markdown("**Détail du score — chaque point est expliqué**")
        st.markdown("".join(ui.raison(r) for r in reasons), unsafe_allow_html=True)
    hist = db.actions(e["id"])
    if hist:
        with st.expander(f"Historique ({len(hist)} action(s))"):
            for a in hist:
                st.markdown(f"**{a['date'][:16].replace('T', ' ')}** — {a['type']}" + (f" : {a['detail'][:120]}…" if a["detail"] and len(a["detail"]) > 120 else f" : {a['detail']}" if a["detail"] else ""))


ui.entete()
_c = db.compteurs()
_rows = db.lister()
_clos = _c["Converti"] + _c["Non intéressé"]
ui.kpis([
    (sum(_c.values()), "Prospects identifiés", "#3b82f6"),
    (sum(1 for r in _rows if (r["score"] or 0) >= 75), "Haute priorité (≥ 75)", "#f59e0b"),
    (sum(1 for r in _rows if db.relance_due(r)), "Relances dues", "#8b5cf6"),
    (_c["Converti"], "Convertis", "#16a34a"),
    (f"{round(100 * _c['Converti'] / _clos) if _clos else 0} %", "Taux de conversion", ui.ROUGE),
])
st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

tab1, tab2, tab3, tab4, tab5 = st.tabs(["🔎 Recherche & Scoring", "🗂️ Pipeline", "🤝 Handoff", "📊 Tableau de bord", "⚙️ Paramètres"])

# =====================================================================
# Onglet 1 — Recherche & Scoring
# =====================================================================
with tab1:
    st.subheader(f"Identifier les entreprises correspondant au profil client idéal de {config.profil()['entreprise']}")
    f1, f2, f3, f4 = st.columns([2, 2, 2, 1])
    secteur = f1.selectbox("Secteur d'activité", ["Tous"] + SECTEURS)
    ville = f2.selectbox("Localisation", ["Toutes"] + VILLES)
    tranche = f3.selectbox("Taille (salariés)", ["Toutes"] + TRANCHES)
    f4.markdown("<br>", unsafe_allow_html=True)
    if f4.button("Rechercher", type="primary", use_container_width=True):
        st.session_state["filtres"] = (secteur, ville, tranche)

    if st.button("✨ Scorer toutes les entreprises"):
        n = db.scorer_tous()
        st.success(f"{n} entreprises scorées — chaque score est accompagné de ses 4 raisons.")

    secteur, ville, tranche = st.session_state.get("filtres", ("Tous", "Toutes", "Toutes"))
    rows = db.lister(secteur, ville, tranche)
    if not rows:
        st.warning("Aucune entreprise trouvée — élargir les critères.")
    else:
        df = pd.DataFrame(rows)[["id", "nom", "secteur", "localisation", "effectif", "signal_croissance", "score", "statut"]]
        df["score"] = df["score"].fillna(-1).astype(int).replace(-1, None)
        st.dataframe(df.drop(columns=["id"]), use_container_width=True, hide_index=True)
        choix = st.selectbox("Voir le détail du score de :", rows, format_func=lambda r: f"{r['nom']} — {r['score'] if r['score'] is not None else '?'}/100")
        if choix:
            fiche(choix)

# =====================================================================
# Onglet 2 — Pipeline
# =====================================================================
with tab2:
    st.subheader("Pipeline commercial")
    colonnes = st.columns(len(db.STATUTS))
    for col, statut in zip(colonnes, db.STATUTS):
        items = db.lister(statut=statut)
        col.markdown(ui.tete_colonne(statut, len(items)) + "".join(ui.carte_pipeline(e, db.relance_due(e)) for e in items), unsafe_allow_html=True)

    st.divider()
    rows = db.lister()
    e = st.selectbox("Entreprise à travailler", rows, format_func=lambda r: f"{r['nom']} — {badge(r['statut'])}", key="pipe_sel")
    if e:
        e = db.obtenir(e["id"])
        fiche(e)
        if db.relance_due(e):
            st.warning(f"🔔 Relance due : contacté le {e['date_contact']}, aucune réponse depuis {db.DELAI_RELANCE_JOURS} jours.")

        b1, b2, b3, b4, b5, b6 = st.columns(6)
        if b1.button("✉️ Générer message", use_container_width=True):
            with st.spinner("Rédaction en cours…"):
                msg, src = llm.generer_message(e)
            db.enregistrer_message(e["id"], msg)
            st.session_state["dernier_message"] = (e["id"], msg, src)
        if b2.button("📤 Marquer contacté", use_container_width=True):
            db.changer_statut(e["id"], "Contacté", "Premier email envoyé")
            st.rerun()
        if b3.button("⏩ Simuler J+3", use_container_width=True, help="Démo : recule la date de contact de 3 jours"):
            db.simuler_j3(e["id"])
            st.rerun()
        if b4.button("🔁 Relancer", use_container_width=True, disabled=not db.relance_due(e)):
            with st.spinner("Rédaction de la relance…"):
                msg, src = llm.generer_message(e, relance=True)
            db.enregistrer_message(e["id"], msg, "Relance J+3")
            db.changer_statut(e["id"], "Relancé", "Relance envoyée")
            st.session_state["dernier_message"] = (e["id"], msg, src)
            st.rerun()
        if b5.button("✅ Converti", use_container_width=True, type="primary"):
            db.changer_statut(e["id"], "Converti", "Décision commercial")
            st.rerun()
        with b6.popover("Classer…", use_container_width=True):
            if st.button("🔴 Non intéressé (archiver)"):
                db.changer_statut(e["id"], "Non intéressé"); st.rerun()
            if st.button("🟤 À relancer plus tard (nurture)"):
                db.changer_statut(e["id"], "À relancer plus tard"); st.rerun()

        dm = st.session_state.get("dernier_message")
        if dm and dm[0] == e["id"]:
            st.markdown(f"**Message généré** *(source : {'Groq Llama 3.3' if dm[2] == 'groq' else 'template local'})*")
            st.text_area("", dm[1], height=220, label_visibility="collapsed")
            if notifier.configure("gmail"):
                dest = e.get("email") or os.environ.get("GMAIL_RECIPIENT", "")
                if st.button(f"📧 Envoyer ce message par email à {dest}", key=f"mail_{e['id']}"):
                    ok, detail = notifier.envoyer_gmail(f"{config.profil()['entreprise']} — proposition pour {e['nom']}", dm[1], dest)
                    db.journaliser(e["id"], "Email envoyé (Gmail)" if ok else "Échec email", detail)
                    (st.success if ok else st.error)(detail)
                    if ok and e["statut"] in ("Nouveau", "Scoré"):
                        db.changer_statut(e["id"], "Contacté", "Email envoyé via Gmail"); st.rerun()
        elif e.get("message_genere"):
            st.markdown("**Dernier message généré**")
            st.text_area("", e["message_genere"], height=200, label_visibility="collapsed")

# =====================================================================
# Onglet 3 — Handoff
# =====================================================================
with tab3:
    st.subheader(f"Transmettre les prospects convertis au responsable commercial de {config.profil()['entreprise']}")
    convertis = db.lister(statut="Converti")
    if not convertis:
        st.info("Aucun prospect converti pour l'instant. Convertissez-en un depuis l'onglet Pipeline.")
    for e in convertis:
        with st.container(border=True):
            st.markdown(f"**{e['nom']}** — {e['secteur']} · {e['effectif']} salariés · {e['localisation']} · score **{e['score']}/100**")
            texte = webhook.message_handoff(e)
            sujet = f"Prospect converti : {e['nom']}"
            cols = st.columns(5)
            boutons = [("discord", "🟣 Discord"), ("gmail", "📧 Gmail"), ("whatsapp", "💬 WhatsApp"), ("sms", "📱 SMS")]
            for col, (canal, label) in zip(cols, boutons):
                if col.button(label, key=f"{canal}_{e['id']}", use_container_width=True, disabled=not notifier.configure(canal),
                              help=None if notifier.configure(canal) else "Canal non configuré (voir .env / Secrets)"):
                    ok, detail = notifier.envoyer(canal, sujet, texte)
                    db.journaliser(e["id"], f"Handoff {notifier.CANAUX[canal]['label']}" + ("" if ok else " (échec)"), detail)
                    (st.success if ok else st.error)(detail)
            if cols[4].button("📣 Tous les canaux", key=f"tous_{e['id']}", type="primary", use_container_width=True):
                res = notifier.envoyer_tous(sujet, texte)
                if not res:
                    db.journaliser(e["id"], "Handoff interne", texte)
                    st.warning("Aucun canal configuré — notification interne affichée ci-dessous.")
                for canal, (ok, detail) in res.items():
                    db.journaliser(e["id"], f"Handoff {notifier.CANAUX[canal]['label']}" + ("" if ok else " (échec)"), detail)
                    (st.success if ok else st.error)(f"{notifier.CANAUX[canal]['icone']} {detail}")
            with st.expander("Voir la fiche de transmission"):
                st.code(texte)

# =====================================================================
# Onglet 4 — Tableau de bord
# =====================================================================
with tab4:
    st.subheader("Impact")
    c = db.compteurs()
    total = sum(c.values())
    clos = c["Converti"] + c["Non intéressé"]
    m1, m2 = st.columns(2)
    m1.metric("Temps de prospection manuel", f"{total * 20 // 60} h {total * 20 % 60:02d}", "20 min par entreprise")
    m2.metric("Avec le copilote", f"{total} min", f"-{round(100 - 100 * total / (total * 20))} % de temps", delta_color="normal")
    st.bar_chart(pd.DataFrame({"statut": list(c.keys()), "prospects": list(c.values())}).set_index("statut"))
    st.markdown(f"""
**Comment on calcule 4 h → 15 min** : pour {total} entreprises, la recherche manuelle (annuaire, site web, LinkedIn) prend environ
20 min par entreprise, soit **{total * 20 // 60} h {total * 20 % 60:02d}**. Avec le copilote : scoring instantané, 1 min par message généré
et validé, soit **≈ {total} min**.
""")

# =====================================================================
# Onglet 5 — Paramètres : profil de l'entreprise (nom, offres, secteurs et zones prioritaires)
# =====================================================================
with tab5:
    st.subheader("Profil de l'entreprise utilisatrice")
    st.caption("Le scoring, les messages générés et le handoff s'adaptent à ces paramètres. Par défaut : l'entreprise témoin du jeu de données LSS 2026.")
    prof = dict(config.profil())
    c1, c2 = st.columns(2)
    prof["entreprise"] = c1.text_input("Nom de l'entreprise", prof["entreprise"])
    prof["signature"] = c2.text_input("Signature des messages", prof["signature"])
    prof["activite"] = st.text_input("Activité (une phrase, utilisée dans les prompts)", prof["activite"])
    liste = lambda txt: [x.strip() for x in txt.split(",") if x.strip()]
    prof["offres"] = liste(st.text_input("Offres (séparées par des virgules)", ", ".join(prof["offres"])))
    st.markdown("**Grille de scoring — secteurs**")
    s1, s2, s3 = st.columns(3)
    prof["secteurs_30"] = liste(s1.text_input("Haute valeur (30 pts)", ", ".join(prof["secteurs_30"])))
    prof["secteurs_25"] = liste(s2.text_input("Prioritaires (25 pts)", ", ".join(prof["secteurs_25"])))
    prof["secteurs_15"] = liste(s3.text_input("Secondaires (15 pts) — les autres : 5 pts", ", ".join(prof["secteurs_15"])))
    st.markdown("**Grille de scoring — zones**")
    z1, z2 = st.columns(2)
    prof["villes_20"] = liste(z1.text_input("Zones prioritaires (20 pts)", ", ".join(prof["villes_20"])))
    prof["villes_15"] = liste(z2.text_input("Zones secondaires (15 pts) — les autres : 5 pts", ", ".join(prof["villes_15"])))
    b1, b2 = st.columns([1, 3])
    if b1.button("💾 Enregistrer et rescorer", type="primary", use_container_width=True):
        con = db.connexion(); config.enregistrer(con, prof); con.close()
        config.rafraichir()
        db.scorer_tous()
        st.success("Profil enregistré — tous les prospects ont été rescorés.")
        st.rerun()
    if b2.button("↩ Revenir au profil par défaut (entreprise témoin LSS 2026)"):
        con = db.connexion(); config.enregistrer(con, config.PROFIL_DEFAUT); con.close()
        config.rafraichir()
        db.scorer_tous()
        st.rerun()
