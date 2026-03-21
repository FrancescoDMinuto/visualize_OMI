import streamlit as st
import requests
import plotly.graph_objects as go
import pandas as pd
import time
from datetime import date
from pathlib import Path

st.set_page_config(
    page_title="Prezzi Immobili Italia",
    page_icon="home",
    layout="centered",
    initial_sidebar_state="collapsed",
)

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, .stApp {
    background: #f7f8fa !important;
    font-family: 'Inter', sans-serif !important;
    color: #1a1a2e !important;
}
section[data-testid="stSidebar"],
header[data-testid="stHeader"],
#MainMenu, footer, [data-testid="stToolbar"] { display: none !important; }

.block-container {
    padding: 0 !important;
    max-width: 100% !important;
}

/* Hero bar */
.hero {
    background: linear-gradient(135deg, #e8350a 0%, #c8290a 100%);
    padding: 20px 20px 16px 20px;
    margin-bottom: 0;
}
.hero h1 {
    color: white; font-size: 1.4rem; font-weight: 700;
    margin: 0 0 2px 0; letter-spacing: -0.02em;
}
.hero p {
    color: rgba(255,255,255,0.8); font-size: 0.8rem; margin: 0;
}

/* Search panel */
.search-panel {
    background: white;
    border-bottom: 1px solid #e8eaed;
    padding: 16px 16px 12px 16px;
    position: sticky; top: 0; z-index: 100;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}

/* Stila i widget Streamlit nativi per sembrare Airbnb/immobiliare */
div[data-testid="stSelectbox"] > div > div {
    background: white !important;
    border: 1.5px solid #dddddd !important;
    border-radius: 12px !important;
    padding: 2px 4px !important;
    font-size: 0.95rem !important;
    box-shadow: none !important;
    transition: border-color .2s;
}
div[data-testid="stSelectbox"] > div > div:focus-within {
    border-color: #e8350a !important;
    box-shadow: 0 0 0 2px rgba(232,53,10,0.15) !important;
}

div[data-testid="stRadio"] > div {
    gap: 8px !important;
}
div[data-testid="stRadio"] label {
    background: #f0f0f0;
    border: 1.5px solid #ddd;
    border-radius: 999px !important;
    padding: 6px 16px !important;
    font-size: 0.85rem !important;
    font-weight: 500 !important;
    cursor: pointer;
    transition: all .15s;
}
div[data-testid="stRadio"] label:has(input:checked) {
    background: #1a1a2e !important;
    border-color: #1a1a2e !important;
    color: white !important;
}

/* Slider */
div[data-testid="stSlider"] {
    padding: 0 4px;
}
div[data-testid="stSlider"] [data-baseweb="slider"] [role="slider"] {
    background: #e8350a !important;
    border-color: #e8350a !important;
}
div[data-testid="stSlider"] [data-baseweb="slider"] [data-testid="stTickBar"] {
    background: #e8350a !important;
}

/* Multiselect */
div[data-testid="stMultiSelect"] > div > div {
    background: white !important;
    border: 1.5px solid #dddddd !important;
    border-radius: 12px !important;
    min-height: 48px !important;
}
div[data-testid="stMultiSelect"] > div > div:focus-within {
    border-color: #e8350a !important;
    box-shadow: 0 0 0 2px rgba(232,53,10,0.15) !important;
}
.stMultiSelect [data-baseweb="tag"] {
    background: #fff0ed !important;
    border: 1px solid #f5a896 !important;
    color: #c8290a !important;
    border-radius: 8px !important;
    font-weight: 500 !important;
}

/* Bottone cerca - stile Airbnb */
div[data-testid="stButton"] > button {
    background: linear-gradient(135deg, #e8350a, #c8290a) !important;
    color: white !important;
    font-weight: 700 !important;
    font-size: 1rem !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 14px !important;
    width: 100% !important;
    letter-spacing: 0.01em !important;
    box-shadow: 0 4px 14px rgba(232,53,10,0.35) !important;
    transition: all .2s !important;
}
div[data-testid="stButton"] > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px rgba(232,53,10,0.45) !important;
}

/* Labels */
.stSelectbox label, .stMultiSelect label,
.stSlider label, .stRadio label {
    font-size: 0.78rem !important;
    font-weight: 600 !important;
    color: #717171 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.06em !important;
}

/* Sezione risultati */
.results-area {
    background: white;
    border-radius: 16px;
    margin: 12px 0;
    padding: 16px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.08);
}

/* Metric cards */
[data-testid="metric-container"] {
    background: white !important;
    border: 1px solid #ebebeb !important;
    border-radius: 14px !important;
    padding: 14px 16px !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06) !important;
}
[data-testid="metric-container"] [data-testid="stMetricLabel"] {
    font-size: 0.72rem !important; color: #717171 !important;
    font-weight: 600 !important; text-transform: uppercase !important;
    letter-spacing: 0.04em !important;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    font-size: 1.25rem !important; font-weight: 700 !important; color: #1a1a2e !important;
}
[data-testid="metric-container"] [data-testid="stMetricDelta"] {
    font-size: 0.8rem !important; font-weight: 500 !important;
}

/* Divider */
hr { border-color: #f0f0f0 !important; }

/* Expander */
details {
    border: 1px solid #ebebeb !important;
    border-radius: 12px !important;
    overflow: hidden !important;
    margin-top: 12px !important;
}
summary {
    padding: 12px 16px !important;
    font-weight: 600 !important;
    font-size: 0.9rem !important;
    color: #1a1a2e !important;
    background: #fafafa !important;
}

/* Badge fascia */
.badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 999px;
    font-size: 0.72rem;
    font-weight: 700;
    margin: 2px 3px 2px 0;
}

/* Sezione zone */
.zone-header {
    font-size: 0.78rem; font-weight: 600; color: #717171;
    text-transform: uppercase; letter-spacing: 0.06em;
    margin: 16px 0 8px 0;
}

/* Caption */
.stCaption { color: #717171 !important; font-size: 0.78rem !important; }

@media (max-width: 640px) {
    .hero { padding: 14px; }
    .hero h1 { font-size: 1.2rem; }
    [data-testid="metric-container"] {
        padding: 10px 12px !important;
    }
    [data-testid="metric-container"] [data-testid="stMetricValue"] {
        font-size: 1.05rem !important;
    }
}
</style>
"""

st.markdown(CSS, unsafe_allow_html=True)

BASE_URL  = "https://3eurotools.it/api-quotazioni-immobiliari-omi/ricerca"
ANNO_CORR = date.today().year
BASE_DIR  = Path(__file__).parent

TIPI_IMMOBILE = {
    "Abitazioni civili":      "abitazioni_civili",
    "Abitazioni economiche":  "abitazioni_di_tipo_economico",
    "Abitazioni signorili":   "abitazioni_signorili",
    "Ville e villini":        "ville_e_villini",
    "Negozi":                 "negozi",
    "Uffici":                 "uffici",
    "Box/Garage":             "box",
    "Posti auto coperti":     "posti_auto_coperti",
    "Magazzini":              "magazzini",
    "Capannoni industriali":  "capannoni_industriali",
}

FASCIA_LABEL = {
    "A": "Centrale/Pregio", "B": "Semicentrale", "C": "Periferica",
    "D": "Suburbana",       "E": "Extraurbana",  "R": "Rurale",
}
FASCIA_COLOR = {
    "A": "#e8350a", "B": "#0070f3", "C": "#00a550",
    "D": "#7b4f3a", "E": "#8b5cf6", "R": "#0891b2",
}
LINE_COLOR = {
    "A": "#e8350a", "B": "#0070f3", "C": "#00a550",
    "D": "#c87850", "E": "#8b5cf6", "R": "#0891b2",
}


def hex_to_rgba(h, alpha=0.12):
    h = h.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return "rgba({},{},{},{})".format(r, g, b, alpha)


def colore_zona(zona):
    return LINE_COLOR.get(zona[0] if zona else "B", "#0070f3")


@st.cache_data(show_spinner=False)
def carica_dati():
    zone_df   = pd.read_parquet(BASE_DIR / "zone.parquet")
    comuni_df = pd.read_parquet(BASE_DIR / "comuni.parquet")
    zone_lookup = {(r.codice, r.zona): r.zona_descr for r in zone_df.itertuples()}
    comuni_dict = dict(zip(comuni_df["nome"], comuni_df["codice"]))
    return zone_lookup, comuni_dict


ZONE_LOOKUP, COMUNI = carica_dati()
NOMI_COMUNI = sorted(COMUNI.keys())


def nome_zona(codice_comune, zona):
    descr = ZONE_LOOKUP.get((codice_comune, zona), "")
    if descr:
        return "{} - {}".format(zona, descr.title())
    fascia = FASCIA_LABEL.get(zona[0], "") if zona else ""
    return "{} - {}".format(zona, fascia) if fascia else zona


@st.cache_data(show_spinner=False)
def zone_del_comune(codice):
    df = pd.read_parquet(BASE_DIR / "zone.parquet")
    zone = df.loc[df["codice"] == codice, "zona"].unique().tolist()
    zone.sort(key=lambda z: (z[0], int(z[1:]) if z[1:].isdigit() else 0))
    return zone


def anno_definitivo(a):
    if a < ANNO_CORR - 1: return True
    if a == ANNO_CORR - 1 and date.today().month >= 7: return True
    return False


def _chiama_api(codice, anno, tipo, op, zona):
    try:
        p = {"codice_comune": codice, "anno": anno,
             "tipo_immobile": tipo, "operazione": op, "metri_quadri": 100}
        if zona: p["zona_omi"] = zona
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
    return _fetch_def(codice, anno, tipo, op, zona) if anno_definitivo(anno)            else _fetch_rec(codice, anno, tipo, op, zona)


def extract_prezzi(data, tipo_api, op):
    if not data or tipo_api not in data: return None
    d = data[tipo_api]
    k = "acquisto" if op == "acquisto" else "affitto"
    m = d.get("prezzo_{}_medio".format(k))
    if not m: return None
    return {
        "min": d.get("prezzo_{}_min".format(k)),
        "max": d.get("prezzo_{}_max".format(k)),
        "medio": m,
        "stato": d.get("stato_di_conservazione_mediano_della_zona", "-"),
    }


def fetch_serie(label, codice, anni, tipo_api, op, zona):
    rows = []
    prog = st.progress(0, text="Caricamento {}...".format(label))
    for i, anno in enumerate(anni):
        da_cache = anno_definitivo(anno)
        d = fetch_q(codice, anno, tipo_api, op, zona)
        if not da_cache: time.sleep(0.35)
        p = extract_prezzi(d, tipo_api, op)
        if p:
            rows.append({"anno": anno, "label": label,
                         "medio": p["medio"], "min": p["min"],
                         "max": p["max"], "stato": p["stato"]})
        prog.progress((i + 1) / len(anni), text="{} - {}".format(label, anno))
    prog.empty()
    return pd.DataFrame(rows)


# -- UI --

st.markdown(
    "<div class=hero>"
    "<h1>Prezzi Immobili Italia</h1>"
    "<p>Quotazioni ufficiali Agenzia delle Entrate &middot; OMI</p>"
    "</div>",
    unsafe_allow_html=True,
)

with st.container():
    st.markdown("#### Cerca")

    comune_sel = st.selectbox(
        "Comune", NOMI_COMUNI,
        index=NOMI_COMUNI.index("Roma") if "Roma" in NOMI_COMUNI else 0,
    )
    codice_comune = COMUNI[comune_sel]

    c1, c2 = st.columns([3, 2])
    with c1:
        tipo_label = st.selectbox("Tipologia", list(TIPI_IMMOBILE.keys()))
        tipo_api   = TIPI_IMMOBILE[tipo_label]
    with c2:
        operazione = st.radio("Operazione", ["acquisto", "affitto"], horizontal=True)

    anni_range = st.slider("Periodo di analisi", 2004, 2025, (2012, 2024))
    anni_sel   = list(range(anni_range[0], anni_range[1] + 1))

st.divider()

with st.container():
    st.markdown("#### Zone OMI disponibili")

    zone_disp = zone_del_comune(codice_comune)
    zone_sel = []

    if not zone_disp:
        st.warning("Nessuna zona trovata per questo comune.")
    else:
        fasce = sorted(set(z[0] for z in zone_disp))
        badge_html = "".join(
            "<span class=badge style=background:{};color:white>{} &ndash; {}</span>".format(
                FASCIA_COLOR.get(f, "#888"),
                f, FASCIA_LABEL.get(f, f)
            )
            for f in fasce
        )
        st.markdown(badge_html, unsafe_allow_html=True)

        opzioni = {nome_zona(codice_comune, z): z for z in zone_disp}
        default, viste = [], set()
        for z in zone_disp:
            if z[0] not in viste:
                default.append(nome_zona(codice_comune, z))
                viste.add(z[0])
            if len(default) >= 4:
                break

        sel_labels = st.multiselect(
            "{} zone - seleziona fino a 6 da confrontare".format(len(zone_disp)),
            options=list(opzioni.keys()),
            default=default,
            max_selections=6,
        )
        zone_sel = [opzioni[l] for l in sel_labels]

    st.caption("[Visualizza zone su mappa](https://www1.agenziaentrate.gov.it/servizi/geopoi_omi/index.php)")

st.divider()

avvia = st.button(
    "Analizza {}".format(comune_sel),
    disabled=(len(zone_sel) == 0),
    use_container_width=True,
)

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
        "df_all": pd.concat(tutti_df, ignore_index=True),
        "operazione": operazione,
        "anni_range": anni_range,
        "comune_sel": comune_sel,
    })

if "df_all" in st.session_state:
    df_all  = st.session_state["df_all"]
    op      = st.session_state["operazione"]
    c_nome  = st.session_state["comune_sel"]
    unita   = "euro/mq" if op == "acquisto" else "euro/mq/mese"
    labels  = df_all["label"].unique().tolist()
    c_map   = {l: colore_zona(l.split("-")[0].strip()) for l in labels}

    st.markdown(
        "<p style=font-size:0.75rem;color:#717171;text-transform:uppercase;"
        "letter-spacing:0.06em;margin-bottom:12px>{} &middot; {} &middot; {}-{}</p>".format(
            c_nome,
            "Acquisto" if op == "acquisto" else "Affitto",
            st.session_state["anni_range"][0],
            st.session_state["anni_range"][1],
        ),
        unsafe_allow_html=True,
    )

    cols = st.columns(min(len(labels), 3))
    for i, label in enumerate(labels):
        dfl = df_all[df_all["label"] == label].sort_values("anno")
        if dfl.empty: continue
        ult, pri = dfl.iloc[-1], dfl.iloc[0]
        var = ((ult["medio"] - pri["medio"]) / pri["medio"] * 100) if pri["medio"] else 0
        with cols[i % min(len(labels), 3)]:
            st.metric(
                label=label,
                value="{:,.0f} {}".format(ult["medio"], unita),
                delta="{:+.1f}% dal {}".format(var, int(pri["anno"])),
            )

    st.divider()

    fig = go.Figure()
    for label in labels:
        dfl = df_all[df_all["label"] == label].sort_values("anno")
        col = c_map[label]
        if dfl["min"].notna().any():
            fig.add_trace(go.Scatter(
                x=pd.concat([dfl["anno"], dfl["anno"][::-1]]),
                y=pd.concat([dfl["max"], dfl["min"][::-1]]),
                fill="toself", fillcolor=hex_to_rgba(col, 0.1),
                line=dict(color="rgba(0,0,0,0)"),
                showlegend=False, hoverinfo="skip",
            ))
        fig.add_trace(go.Scatter(
            x=dfl["anno"], y=dfl["medio"],
            mode="lines+markers", name=label,
            line=dict(color=col, width=2.5),
            marker=dict(size=6, color=col),
            hovertemplate="<b>{}</b><br>%{{x}}: %{{y:,.0f}} {}<extra></extra>".format(label, unita),
        ))
    fig.update_layout(
        title=dict(text="Andamento prezzi medi", font=dict(size=14, color="#1a1a2e")),
        xaxis=dict(tickmode="linear", dtick=2, gridcolor="#f0f0f0", color="#717171"),
        yaxis=dict(gridcolor="#f0f0f0", color="#717171", tickformat=",.0f"),
        plot_bgcolor="white", paper_bgcolor="white",
        font=dict(color="#1a1a2e", size=11, family="Inter"),
        legend=dict(bgcolor="rgba(0,0,0,0)", orientation="h",
                    yanchor="bottom", y=1.02, xanchor="left", x=0),
        hovermode="x unified", height=340,
        margin=dict(l=0, r=0, t=40, b=0),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    fig2 = go.Figure()
    for label in labels:
        dfl = df_all[df_all["label"] == label].sort_values("anno").copy()
        dfl["var"] = dfl["medio"].pct_change() * 100
        fig2.add_trace(go.Bar(
            x=dfl["anno"], y=dfl["var"], name=label,
            marker_color=c_map[label],
            hovertemplate="<b>{}</b> %{{x}}: %{{y:+.1f}}%<extra></extra>".format(label),
        ))
    fig2.update_layout(
        title=dict(text="Variazione % anno su anno", font=dict(size=14, color="#1a1a2e")),
        barmode="group",
        xaxis=dict(tickmode="linear", dtick=2, gridcolor="#f0f0f0", color="#717171"),
        yaxis=dict(gridcolor="#f0f0f0", color="#717171", ticksuffix="%"),
        plot_bgcolor="white", paper_bgcolor="white",
        font=dict(color="#1a1a2e", size=11, family="Inter"),
        legend=dict(bgcolor="rgba(0,0,0,0)", orientation="h",
                    yanchor="bottom", y=1.02, xanchor="left", x=0),
        height=280, margin=dict(l=0, r=0, t=40, b=0),
    )
    st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

    with st.expander("Dati completi"):
        df_show = df_all[["anno", "label", "min", "medio", "max", "stato"]].copy()
        df_show.columns = ["Anno", "Zona", "Min", "Medio", "Max", "Stato"]
        st.dataframe(df_show.sort_values(["Zona", "Anno"]),
                     use_container_width=True, hide_index=True)
        st.download_button(
            "Scarica CSV",
            df_show.to_csv(index=False).encode("utf-8"),
            "quotazioni_omi.csv", "text/csv",
            use_container_width=True,
        )

    st.markdown(
        "<p style=text-align:center;color:#717171;font-size:0.72rem;margin-top:16px>"
        "Fonte: Agenzia delle Entrate &middot; OMI &middot; 100 mq commerciali</p>",
        unsafe_allow_html=True,
    )
