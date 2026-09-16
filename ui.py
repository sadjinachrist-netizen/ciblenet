# ui.py — Habillage visuel de Yas Prospect Copilot (CSS + composants HTML réutilisables)
import streamlit as st

ROUGE = "#e30613"      # rouge Yas
NUIT = "#0f172a"
COULEURS_STATUT = {
    "Nouveau": "#94a3b8", "Scoré": "#3b82f6", "Contacté": "#8b5cf6", "Relancé": "#f59e0b",
    "Converti": "#16a34a", "Non intéressé": "#dc2626", "À relancer plus tard": "#a16207",
}

CSS = f"""
<style>
/* ---- base ---- */
#MainMenu, footer {{ visibility: hidden; }}
.block-container {{ padding-top: 1.2rem; padding-bottom: 2rem; max-width: 1280px; }}
h2, h3 {{ letter-spacing: -.01em; }}
section[data-testid="stSidebar"] {{ background: {NUIT}; }}
section[data-testid="stSidebar"] * {{ color: #e2e8f0; }}
section[data-testid="stSidebar"] .stButton button, section[data-testid="stSidebar"] .stDownloadButton button {{
  background: #1e293b; color: #fff; border: 1px solid #334155; border-radius: 10px; }}
section[data-testid="stSidebar"] .stButton button:hover {{ border-color: {ROUGE}; color: #fff; }}
.stTabs [data-baseweb="tab-list"] {{ gap: 6px; }}
.stTabs [data-baseweb="tab"] {{ padding: 10px 18px; border-radius: 10px 10px 0 0; font-weight: 600; }}
.stTabs [aria-selected="true"] {{ background: #fff1f2; color: {ROUGE}; }}
.stButton button[kind="primary"] {{ background: {ROUGE}; border-color: {ROUGE}; border-radius: 10px; font-weight: 600; }}
.stButton button {{ border-radius: 10px; }}
[data-testid="stMetric"] {{ background: #fff; border: 1px solid #e5e7eb; border-radius: 14px; padding: 14px 18px; }}

/* ---- en-tête ---- */
.yas-hero {{ background: linear-gradient(120deg, {NUIT} 0%, #7f1d1d 60%, {ROUGE} 100%); color: #fff; border-radius: 18px;
  padding: 26px 30px; margin-bottom: 18px; box-shadow: 0 10px 30px rgba(15,23,42,.18); }}
.yas-hero h1 {{ color: #fff; margin: 0 0 4px; font-size: 30px; }}
.yas-hero p {{ margin: 0 0 12px; color: #fecaca; font-size: 15px; }}
.yas-chip {{ display: inline-block; background: rgba(255,255,255,.14); border: 1px solid rgba(255,255,255,.3); border-radius: 999px;
  padding: 4px 12px; margin: 2px 6px 2px 0; font-size: 12.5px; font-weight: 600; }}

/* ---- KPI ---- */
.kpi {{ background: #fff; border: 1px solid #e5e7eb; border-radius: 16px; padding: 16px 18px; text-align: center;
  box-shadow: 0 1px 3px rgba(15,23,42,.06); border-top: 4px solid var(--c, {ROUGE}); }}
.kpi .v {{ font-size: 30px; font-weight: 800; color: {NUIT}; line-height: 1.1; }}
.kpi .l {{ font-size: 11.5px; letter-spacing: .06em; text-transform: uppercase; color: #64748b; margin-top: 4px; }}

/* ---- pipeline ---- */
.col-head {{ font-weight: 700; font-size: 13px; padding: 6px 10px; border-radius: 8px; color: #fff; margin-bottom: 8px; display: flex; justify-content: space-between; }}
.kcard {{ background: #fff; border: 1px solid #e5e7eb; border-left: 4px solid var(--c, #94a3b8); border-radius: 10px; padding: 8px 10px; margin-bottom: 8px;
  box-shadow: 0 1px 2px rgba(15,23,42,.05); }}
.kcard .n {{ font-weight: 600; font-size: 13px; color: {NUIT}; }}
.kcard .m {{ font-size: 11.5px; color: #64748b; display: flex; justify-content: space-between; margin-top: 4px; }}

/* ---- score ---- */
.score {{ display: inline-block; min-width: 46px; text-align: center; padding: 2px 8px; border-radius: 8px; font-weight: 800; font-size: 13px; }}
.score-h {{ background: #dcfce7; color: #166534; }} .score-m {{ background: #fef9c3; color: #854d0e; }} .score-b {{ background: #fee2e2; color: #991b1b; }}
.raison {{ background: #f8fafc; border: 1px solid #e5e7eb; border-radius: 10px; padding: 8px 12px; margin-bottom: 6px; font-size: 14px; }}
.raison b {{ color: {ROUGE}; margin-right: 8px; font-family: ui-monospace, monospace; }}
.offre {{ background: #fff1f2; border: 1px solid #fecdd3; color: #9f1239; border-radius: 10px; padding: 8px 12px; font-size: 13.5px; font-weight: 600; }}
</style>
"""


def injecter_css():
    st.markdown(CSS, unsafe_allow_html=True)


def entete():
    st.markdown(f"""
<div class="yas-hero">
  <h1>🎯 Yas Prospect Copilot</h1>
  <p>Identifier · Qualifier · Prospecter · Relancer · Convertir — le copilote commercial de Yas Business</p>
  <span class="yas-chip">📶 Fibre Pro</span><span class="yas-chip">📱 Flotte mobile</span>
  <span class="yas-chip">💳 Mixx Business</span><span class="yas-chip">✉️ API SMS</span>
</div>""", unsafe_allow_html=True)


def kpis(items):
    """items : liste de (valeur, libellé, couleur)"""
    cols = st.columns(len(items))
    for col, (v, l, c) in zip(cols, items):
        col.markdown(f'<div class="kpi" style="--c:{c}"><div class="v">{v}</div><div class="l">{l}</div></div>', unsafe_allow_html=True)


def score_badge(score) -> str:
    if score is None:
        return '<span class="score score-b" style="background:#f1f5f9;color:#64748b">—</span>'
    cls = "score-h" if score >= 75 else "score-m" if score >= 60 else "score-b"
    return f'<span class="score {cls}">{score}</span>'


def raison(r: str) -> str:
    pts, texte = r.split(" ", 1)
    return f'<div class="raison"><b>{pts}</b>{texte}</div>'


def carte_pipeline(e: dict, due: bool) -> str:
    c = COULEURS_STATUT.get(e["statut"], "#94a3b8")
    return (f'<div class="kcard" style="--c:{c}"><div class="n">{"🔔 " if due else ""}{e["nom"]}</div>'
            f'<div class="m"><span>{e["secteur"]} · {e["localisation"]}</span>{score_badge(e["score"])}</div></div>')


def tete_colonne(statut: str, n: int) -> str:
    return f'<div class="col-head" style="background:{COULEURS_STATUT.get(statut, "#94a3b8")}"><span>{statut}</span><span>{n}</span></div>'
