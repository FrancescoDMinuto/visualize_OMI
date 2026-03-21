import streamlit as st
import requests
import plotly.graph_objects as go
import pandas as pd
import time
from datetime import date
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Prezzi Immobili Italia",
    page_icon="🏠",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
  html, body, .stApp { background-color: #0f1923 !important; color: #e8eaf0; }
  section[data-testid="stSidebar"], button[kind="header"],
  header[data-testid="stHeader"], #MainMenu, footer { display: none !important; }
  .block-container { padding: 1rem 1rem 4rem 1rem !important; max-width: 720px !important; }
  .card {
    background: #1a2535; border: 1px solid #2a3a50;
    border-radius: 16px; padding: 1.2rem; margin-bottom: 1rem;
  }
  .card-title {
    font-size: 0.75rem; font-weight: 700; color: #c8a84b;
    text-transform: uppercase; letter-spacing: 0.09em; margin: 0 0 0.9rem 0;
  }
  .stMultiSelect [data-baseweb="tag"] {
    background-color: #1e3a5f !important; border: 1px solid #3a6090 !important;
    color: #a8c8f0 !important; border-radius: 6px !important;
  }
  div[data-testid="stButton"] > button {
    width: 100%; background: #c8a84b; color: #0f1923;
    font-weight: 800; font-size: 1rem; border: none;
    border-radius: 12px; padding: 0.75rem; letter-spacing: 0.03em;
  }
  div[data-testid="stButton"] > button:hover { background: #dfc06a; }
  [data-testid="metric-container"] {
    background: #1a2535; border: 1px solid #2a3a50;
    border-radius: 12px; padding: 0.8rem 1rem;
  }
  [data-testid="metric-container"] label { color: #8a9ab0 !important; font-size: 0.75rem !important; }
  .results-label {
    font-size: 0.75rem; color: #6a7a8a; text-transform: uppercase;
    letter-spacing: 0.08em; margin: 1.2rem 0 0.4rem 0;
  }
  @media (max-width: 600px) {
    .block-container { padding: 0.5rem 0.5rem 3rem 0.5rem !important; }
  }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# COSTANTI
# ─────────────────────────────────────────────
BASE_URL  = "https://3eurotools.it/api-quotazioni-immobiliari-omi/ricerca"
ANNO_CORR = date.today().year

ZONE_CANDIDATE = [
    "A1","A2","A3","A4","A5",
    "B1","B2","B3","B4","B5","B6","B7","B8","B9",
    "B10","B11","B12","B13","B14","B15","B16","B17","B18","B19","B20",
    "B21","B22","B23","B24","B25","B26","B27","B28","B29","B30","B31","B32",
    "C1","C2","C3","C4","C5","C6","C7","C8","C9","C10",
    "D1","D2","D3","D4","E1","R1",
]

TIPI_IMMOBILE = {
    "🏠 Abitazioni civili":      "abitazioni_civili",
    "🏚 Abitazioni economiche":  "abitazioni_di_tipo_economico",
    "🏛 Abitazioni signorili":   "abitazioni_signorili",
    "🏡 Ville e villini":        "ville_e_villini",
    "🏪 Negozi":                 "negozi",
    "🏢 Uffici":                 "uffici",
    "🅿️ Box/Garage":            "box",
    "🚗 Posti auto coperti":     "posti_auto_coperti",
    "📦 Magazzini":              "magazzini",
    "🏭 Capannoni industriali":  "capannoni_industriali",
}

FASCIA_LABEL = {
    "A": "Centrale/Pregio", "B": "Semicentrale", "C": "Periferica",
    "D": "Suburbana",       "E": "Extraurbana",  "R": "Rurale",
}
FASCIA_COLOR = {
    "A": "#f0a500", "B": "#4a9eff", "C": "#50c878",
    "D": "#c87850", "E": "#a87fcc", "R": "#78c8c8",
}


# ─────────────────────────────────────────────
# UTILS
# ─────────────────────────────────────────────
def hex_to_rgba(h: str, alpha: float = 0.15) -> str:
    h = h.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"

def colore_zona(zona: str) -> str:
    return FASCIA_COLOR.get(zona[0] if zona else "B", "#4a9eff")


# ─────────────────────────────────────────────
# CARICA PARQUET LOCALI
# ─────────────────────────────────────────────
BASE_DIR = Path(__file__).parent

@st.cache_data(show_spinner=False)
def carica_dati():
    zone_df  = pd.read_parquet(BASE_DIR / "zone.parquet")
    comuni_df = pd.read_parquet(BASE_DIR / "comuni.parquet")
    # lookup zone: {(codice, zona): zona_descr}
    zone_lookup = {
        (r.codice, r.zona): r.zona_descr
        for r in zone_df.itertuples()
    }
    # dict comuni: {nome_title: codice}
    comuni_dict = dict(zip(comuni_df["nome"], comuni_df["codice"]))
    return zone_lookup, comuni_dict

ZONE_LOOKUP, COMUNI = carica_dati()
NOMI_COMUNI = sorted(COMUNI.keys())


# ─────────────────────────────────────────────
# NOME ZONA LEGGIBILE
# ─────────────────────────────────────────────
def nome_zona(codice_comune: str, zona: str) -> str:
    descr = ZONE_LOOKUP.get((codice_comune, zona), "")
    if descr:
        return f"{zona}  ·  {descr.title()}"
    fascia = FASCIA_LABEL.get(zona[0], "") if zona else ""
    return f"{zona}  ·  {fascia}" if fascia else zona


# ─────────────────────────────────────────────
# API + CACHE
# ─────────────────────────────────────────────
def anno_definitivo(a: int) -> bool:
    if a < ANNO_CORR - 1: return True
    if a == ANNO_CORR - 1 and date.today().month >= 7: return True
    return False

def _chiama_api(codice, anno, tipo, op, zona):
    try:
        p = {"codice_comune": codice, "anno": anno,
             "tipo_immobile": tipo, "operazione": op, "metri_quadri": 100}
        if zona:
            p["zona_omi"] = zona
        r = requests.get(BASE_URL, params=p, timeout=10)
        if r.status_code == 200:
            d = r.json()
            return d if d else None
    except Exception:
        pass
    return None

@st.cache_data(ttl=None, show_spinner=False)
def _fetch_def(codice, anno, tipo, op, zona):
    return _chiama_api(codice, anno, tipo, op, zona)

@st.cache_data(ttl=300, show_spinner=False)
def _fetch_rec(codice, anno, tipo, op, zona):
    return _chiama_api(codice, anno, tipo, op, zona)

def fetch_q(codice, anno, tipo, op, zona=None):
    return _fetch_def(codice, anno, tipo, op, zona) \
           if anno_definitivo(anno) else _fetch_rec(codice, anno, tipo, op, zona)

def extract_prezzi(data, tipo_api, op):
    if not data or tipo_api not in data:
        return None
    d = data[tipo_api]
    k = "acquisto" if op == "acquisto" else "affitto"
    m = d.get(f"prezzo_{k}_medio")
    if not m:
        return None
    return {
        "min":   d.get(f"prezzo_{k}_min"),
        "max":   d.get(f"prezzo_{k}_max"),
        "medio": m,
        "stato": d.get("stato_di_conservazione_mediano_della_zona", "—"),
    }

@st.cache_data(ttl=3600, show_spinner=False)
def scopri_zone(codice: str, tipo_api: str, op: str) -> list:
    """
    Usa prima il parquet per sapere quali zone esistono per questo comune,
    poi verifica con l'API quali hanno effettivamente dati per la tipologia scelta.
    """
    # Zone note dal parquet per questo comune
    zone_note = [
        r.zona for r in
        pd.read_parquet(BASE_DIR / "zone.parquet").query(f"codice == '{codice}'").itertuples()
    ]
    # Unisci con le candidate standard (per comuni non nel parquet)
    candidate = sorted(set(zone_note + ZONE_CANDIDATE),
                       key=lambda z: (z[0], int(z[1:]) if z[1:].isdigit() else 0))

    anno_t = ANNO_CORR - 1 if date.today().month >= 3 else ANNO_CORR - 2
    trovate = []

    def testa(z):
        d = _chiama_api(codice, anno_t, tipo_api, op, z)
        return z if extract_prezzi(d, tipo_api, op) else None

    with ThreadPoolExecutor(max_workers=10) as ex:
        for fut in as_completed({ex.submit(testa, z): z for z in candidate}):
            v = fut.result()
            if v:
                trovate.append(v)

    trovate.sort(key=lambda z: (z[0], int(z[1:]) if z[1:].isdigit() else 0))
    return trovate

def fetch_serie(label, codice, anni, tipo_api, op, zona):
    rows = []
    prog = st.progress(0, text=f"Caricamento {label}…")
    for i, anno in enumerate(anni):
        da_cache = anno_definitivo(anno)
        d = fetch_q(codice, anno, tipo_api, op, zona)
        if not da_cache:
            time.sleep(0.35)
        p = extract_prezzi(d, tipo_api, op)
        if p:
            rows.append({"anno": anno, "label": label,
                         "medio": p["medio"], "min": p["min"],
                         "max": p["max"], "stato": p["stato"]})
        prog.progress((i + 1) / len(anni), text=f"{label} · {anno}")
    prog.empty()
    return pd.DataFrame(rows)


# ─────────────────────────────────────────────
# UI — HEADER
# ─────────────────────────────────────────────
st.markdown("## 🏠 Prezzi Immobili Italia")
st.markdown(
    "<p style='color:#6a7a8a;font-size:0.85rem;margin-top:-0.5rem'>"
    "Dati ufficiali Agenzia delle Entrate · OMI</p>",
    unsafe_allow_html=True)


# ─────────────────────────────────────────────
# CARD RICERCA
# ─────────────────────────────────────────────
st.markdown('<div class="card"><p class="card-title">🔍 Ricerca</p>', unsafe_allow_html=True)

comune_sel = st.selectbox(
    "Comune", NOMI_COMUNI,
    index=NOMI_COMUNI.index("Roma") if "Roma" in NOMI_COMUNI else 0,
    placeholder="Scrivi il nome del comune…",
    label_visibility="collapsed",
)
codice_comune = COMUNI[comune_sel]

c1, c2 = st.columns([3, 2])
with c1:
    tipo_label = st.selectbox("Tipologia", list(TIPI_IMMOBILE.keys()))
    tipo_api   = TIPI_IMMOBILE[tipo_label]
with c2:
    operazione = st.radio("Operazione", ["acquisto", "affitto"], horizontal=True)

anni_range = st.slider("Periodo", 2004, 2025, (2012, 2024))
anni_sel   = list(range(anni_range[0], anni_range[1] + 1))

st.markdown('</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────
# CARD ZONE
# ─────────────────────────────────────────────
st.markdown('<div class="card"><p class="card-title">📍 Zone OMI</p>', unsafe_allow_html=True)

with st.spinner(f"Cerco le zone di {comune_sel}…"):
    zone_disp = scopri_zone(codice_comune, tipo_api, operazione)

zone_sel = []
if not zone_disp:
    st.warning("Nessuna zona trovata per questa tipologia.")
else:
    fasce = sorted(set(z[0] for z in zone_disp))
    badges = " ".join(
        f'<span style="background:{FASCIA_COLOR.get(f,"#888")};color:#0f1923;'
        f'padding:3px 10px;border-radius:999px;font-size:0.72rem;font-weight:700">'
        f'{FASCIA_LABEL.get(f, f)}</span>'
        for f in fasce
    )
    st.markdown(badges + "<br><br>", unsafe_allow_html=True)

    opzioni = {nome_zona(codice_comune, z): z for z in zone_disp}

    # Default: prima zona di ogni fascia (max 4)
    default, viste = [], set()
    for z in zone_disp:
        if z[0] not in viste:
            default.append(nome_zona(codice_comune, z))
            viste.add(z[0])
        if len(default) >= 4:
            break

    sel_labels = st.multiselect(
        f"{len(zone_disp)} zone — seleziona quelle da confrontare (max 6)",
        options=list(opzioni.keys()),
        default=default,
        max_selections=6,
        label_visibility="collapsed",
    )
    zone_sel = [opzioni[l] for l in sel_labels]

st.caption(
    "[Visualizza zone su mappa →]"
    "(https://www1.agenziaentrate.gov.it/servizi/geopoi_omi/index.php)")
st.markdown('</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────
# BOTTONE
# ─────────────────────────────────────────────
avvia = st.button(
    f"📊  Analizza  {comune_sel}",
    disabled=(len(zone_sel) == 0),
    use_container_width=True,
)


# ─────────────────────────────────────────────
# ESECUZIONE
# ─────────────────────────────────────────────
if avvia:
    tutti_df = []
    for zona in zone_sel:
        label = nome_zona(codice_comune, zona)
        df = fetch_serie(label, codice_comune, anni_sel, tipo_api, operazione, zona)
        if not df.empty:
            tutti_df.append(df)

    if not tutti_df:
        st.error("Nessun dato trovato. Prova un periodo o zone diverse.")
        st.stop()

    st.session_state.update({
        "df_all":     pd.concat(tutti_df, ignore_index=True),
        "operazione": operazione,
        "anni_range": anni_range,
        "comune_sel": comune_sel,
    })


# ─────────────────────────────────────────────
# RISULTATI
# ─────────────────────────────────────────────
if "df_all" in st.session_state:
    df_all = st.session_state["df_all"]
    op     = st.session_state["operazione"]
    c_nome = st.session_state["comune_sel"]
    unita  = "€/mq" if op == "acquisto" else "€/mq/mese"
    labels = df_all["label"].unique().tolist()
    c_map  = {l: colore_zona(l.split("·")[0].strip()) for l in labels}

    st.markdown(
        f'<p class="results-label">📍 {c_nome} · '
        f'{"Acquisto" if op=="acquisto" else "Affitto"} · '
        f'{st.session_state["anni_range"][0]}–{st.session_state["anni_range"][1]}</p>',
        unsafe_allow_html=True)

    # ── Metriche ──
    cols = st.columns(min(len(labels), 3))
    for i, label in enumerate(labels):
        dfl = df_all[df_all["label"] == label].sort_values("anno")
        if dfl.empty:
            continue
        ult, pri = dfl.iloc[-1], dfl.iloc[0]
        var = ((ult["medio"] - pri["medio"]) / pri["medio"] * 100) if pri["medio"] else 0
        with cols[i % min(len(labels), 3)]:
            st.metric(
                label=label,
                value=f"{ult['medio']:,.0f} {unita}",
                delta=f"{var:+.1f}% dal {int(pri['anno'])}",
            )

    st.divider()

    # ── Grafico andamento ──
    fig = go.Figure()
    for label in labels:
        dfl = df_all[df_all["label"] == label].sort_values("anno")
        col = c_map[label]

        if dfl["min"].notna().any():
            fig.add_trace(go.Scatter(
                x=pd.concat([dfl["anno"], dfl["anno"][::-1]]),
                y=pd.concat([dfl["max"], dfl["min"][::-1]]),
                fill="toself",
                fillcolor=hex_to_rgba(col, 0.15),
                line=dict(color="rgba(0,0,0,0)"),
                showlegend=False, hoverinfo="skip",
            ))
        fig.add_trace(go.Scatter(
            x=dfl["anno"], y=dfl["medio"],
            mode="lines+markers", name=label,
            line=dict(color=col, width=2.5),
            marker=dict(size=6, color=col),
            hovertemplate=f"<b>{label}</b><br>%{{x}}: %{{y:,.0f}} {unita}<extra></extra>",
        ))

    fig.update_layout(
        title=dict(text="Andamento prezzi medi", font=dict(size=15, color="#e8eaf0")),
        xaxis=dict(tickmode="linear", dtick=2, gridcolor="#1e2d3d", color="#6a7a8a"),
        yaxis=dict(gridcolor="#1e2d3d", color="#6a7a8a", tickformat=",.0f"),
        plot_bgcolor="#0f1923", paper_bgcolor="#0f1923",
        font=dict(color="#c8d0dc", size=11),
        legend=dict(bgcolor="rgba(0,0,0,0)", orientation="h",
                    yanchor="bottom", y=1.02, xanchor="left", x=0),
        hovermode="x unified", height=340,
        margin=dict(l=0, r=0, t=40, b=0),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # ── Grafico YoY ──
    fig2 = go.Figure()
    for label in labels:
        dfl = df_all[df_all["label"] == label].sort_values("anno").copy()
        dfl["var"] = dfl["medio"].pct_change() * 100
        fig2.add_trace(go.Bar(
            x=dfl["anno"], y=dfl["var"], name=label,
            marker_color=c_map[label],
            hovertemplate=f"<b>{label}</b> %{{x}}: %{{y:+.1f}}%<extra></extra>",
        ))
    fig2.update_layout(
        title=dict(text="Variazione % anno su anno", font=dict(size=15, color="#e8eaf0")),
        barmode="group",
        xaxis=dict(tickmode="linear", dtick=2, gridcolor="#1e2d3d", color="#6a7a8a"),
        yaxis=dict(gridcolor="#1e2d3d", color="#6a7a8a", ticksuffix="%"),
        plot_bgcolor="#0f1923", paper_bgcolor="#0f1923",
        font=dict(color="#c8d0dc", size=11),
        legend=dict(bgcolor="rgba(0,0,0,0)", orientation="h",
                    yanchor="bottom", y=1.02, xanchor="left", x=0),
        height=280, margin=dict(l=0, r=0, t=40, b=0),
    )
    st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

    # ── Tabella ──
    with st.expander("📋 Dati completi"):
        df_show = df_all[["anno","label","min","medio","max","stato"]].copy()
        df_show.columns = ["Anno","Zona",f"Min {unita}",f"Medio {unita}",f"Max {unita}","Stato zona"]
        st.dataframe(df_show.sort_values(["Zona","Anno"]),
                     use_container_width=True, hide_index=True)
        st.download_button("⬇️ Scarica CSV",
                           df_show.to_csv(index=False).encode("utf-8"),
                           "quotazioni_omi.csv", "text/csv",
                           use_container_width=True)

    st.markdown(
        "<p style='text-align:center;color:#3a4a5a;font-size:0.75rem;margin-top:2rem'>"
        "Fonte: Agenzia delle Entrate · OMI · 100 mq commerciali</p>",
        unsafe_allow_html=True)
