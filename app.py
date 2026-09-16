# app.py — Yas Prospect Copilot : interface Streamlit (Recherche & Scoring · Pipeline · Handoff · Tableau de bord)
import os
import tempfile

import pandas as pd
import streamlit as st

import database as db
import llm
import webhook
from scoring import SECTEURS, VILLES, TRANCHES, LABELS, score_prospect, offre_recommandee

st.set_page_config(page_title="Yas Prospect Copilot", page_icon="🎯", layout="wide")

# Streamlit Cloud : les secrets (GROQ_API_KEY, GROQ_API_KEY_2, DISCORD_WEBHOOK_URL) sont exposés comme variables d'environnement
try:
    for _k, _v in st.secrets.items():
        if isinstance(_v, str):
            os.environ.setdefault(_k, _v)
except Exception:
    pass  # pas de fichier secrets en local : on utilise .env / les variables système

db.init_db()

# ---------- barre latérale ----------
with st.sidebar:
    st.title("🎯 Yas Prospect Copilot")
    st.caption("Identifier · Qualifier · Prospecter · Relancer · Convertir — pour Yas Business")
    st.markdown(f"**LLM :** {llm.mode()}")
    st.markdown(f"**Handoff Discord :** {'✅ configuré' if webhook.configure() else '⚠️ non configuré (notification interne)'}")
    st.divider()
    if st.button("🔄 Réinitialiser la démo", use_container_width=True):
        db.init_db(reset=True)
        st.session_state.clear()
        st.rerun()
    fichier = st.file_uploader("📥 Importer des entreprises (CSV)", type=["csv"], help="Colonnes : nom;secteur;localisation;effectif;signal_croissance")
    if fichier is not None:
        chemin = os.path.join(tempfile.gettempdir(), fichier.name)
        with open(chemin, "wb") as f:
            f.write(fichier.getbuffer())
        n = db.importer_csv(chemin)
        st.success(f"{n} entreprise(s) importée(s)")
    chemin_backup = os.path.join(tempfile.gettempdir(), "backup_yas_prospects.csv")
    db.exporter_csv(chemin_backup)
    with open(chemin_backup, "rb") as f:
        st.download_button("💾 Backup CSV (Google Sheets / Excel)", f, "backup_yas_prospects.csv", "text/csv", use_container_width=True)


def badge(statut: str) -> str:
    return {"Nouveau": "⚪", "Scoré": "🔵", "Contacté": "🟣", "Relancé": "🟠", "Converti": "🟢",
            "Non intéressé": "🔴", "À relancer plus tard": "🟤"}.get(statut, "") + " " + statut


def fiche(e: dict):
    """Détail d'une entreprise : score et 4 raisons, offre recommandée, historique."""
    score, reasons, status = score_prospect(e)
    c1, c2 = st.columns([1, 2])
    with c1:
        st.metric("Score ICP", f"{score}/100")
        st.markdown(LABELS[status])
        st.markdown(f"**Offre recommandée :** {offre_recommandee(e)}")
        st.markdown(f"**Statut :** {badge(e['statut'])}")
    with c2:
        st.markdown("**Détail du score (chaque point est expliqué)**")
        for r in reasons:
            st.markdown(f"- `{r.split(' ', 1)[0]}` {r.split(' ', 1)[1]}")
    hist = db.actions(e["id"])
    if hist:
        with st.expander(f"Historique ({len(hist)} action(s))"):
            for a in hist:
                st.markdown(f"**{a['date'][:16].replace('T', ' ')}** — {a['type']}" + (f" : {a['detail'][:120]}…" if a["detail"] and len(a["detail"]) > 120 else f" : {a['detail']}" if a["detail"] else ""))


tab1, tab2, tab3, tab4 = st.tabs(["🔎 Recherche & Scoring", "🗂️ Pipeline", "🤝 Handoff", "📊 Tableau de bord"])

# =====================================================================
# Onglet 1 — Recherche & Scoring
# =====================================================================
with tab1:
    st.subheader("Identifier des PME togolaises correspondant à l'ICP Yas Business")
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
        col.markdown(f"**{badge(statut)}** ({len(items)})")
        for e in items:
            due = db.relance_due(e)
            col.markdown(f"{'🔔 ' if due else ''}{e['nom']}  \n<small>{e['score'] if e['score'] is not None else '?'}/100 · {e['secteur']}</small>", unsafe_allow_html=True)

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
        elif e.get("message_genere"):
            st.markdown("**Dernier message généré**")
            st.text_area("", e["message_genere"], height=200, label_visibility="collapsed")

# =====================================================================
# Onglet 3 — Handoff
# =====================================================================
with tab3:
    st.subheader("Transmettre les prospects convertis au responsable commercial")
    convertis = db.lister(statut="Converti")
    if not convertis:
        st.info("Aucun prospect converti pour l'instant. Convertissez-en un depuis l'onglet Pipeline.")
    for e in convertis:
        with st.container(border=True):
            c1, c2 = st.columns([3, 1])
            c1.markdown(f"**{e['nom']}** — {e['secteur']} · {e['effectif']} salariés · {e['localisation']} · score **{e['score']}/100**")
            if c2.button("🤝 Transmettre", key=f"h{e['id']}", type="primary", use_container_width=True):
                ok, texte = webhook.envoyer_handoff(e)
                db.enregistrer_message(e["id"], texte, "Handoff " + ("Discord" if ok else "interne"))
                if ok:
                    st.success("Notification envoyée sur Discord ✅")
                else:
                    st.warning("Webhook non configuré ou injoignable — notification interne affichée ci-dessous.")
                st.code(texte)

# =====================================================================
# Onglet 4 — Tableau de bord
# =====================================================================
with tab4:
    st.subheader("Impact")
    c = db.compteurs()
    total = sum(c.values())
    clos = c["Converti"] + c["Non intéressé"]
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Prospects", total)
    m2.metric("Convertis", c["Converti"])
    m3.metric("Taux de conversion", f"{round(100 * c['Converti'] / clos) if clos else 0} %")
    m4.metric("Temps de prospection", "15 min", "-3 h 45 vs manuel", delta_color="inverse")
    st.bar_chart(pd.DataFrame({"statut": list(c.keys()), "prospects": list(c.values())}).set_index("statut"))
    st.markdown(f"""
**Comment on calcule 4 h → 15 min** : pour {total} entreprises, la recherche manuelle (annuaire, site web, LinkedIn) prend environ
20 min par entreprise, soit **{total * 20 // 60} h {total * 20 % 60:02d}**. Avec le copilote : scoring instantané, 1 min par message généré
et validé, soit **≈ {total} min**.
""")
