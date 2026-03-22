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
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&display=swap');

*, *::before, *::after { box-sizing: border-box; }

html, body, .stApp {
    background: #FAFAFA !important;
    font-family: 'DM Sans', sans-serif !important;
    color: #1C1C1E !important;
    -webkit-font-smoothing: antialiased;
}

/* Hide Streamlit chrome */
section[data-testid="stSidebar"],
header[data-testid="stHeader"],
[data-testid="stToolbar"],
#MainMenu, footer { display: none !important; }

.block-container {
    padding: 0 0 80px 0 !important;
    max-width: 480px !important;
    margin: 0 auto !important;
}

/* ---- HERO ---- */
.hero {
    background: #1C1C1E;
    padding: 52px 24px 32px 24px;
    margin-bottom: 0;
}
.hero-eyebrow {
    font-size: 11px;
    font-weight: 500;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #8E8E93;
    margin-bottom: 8px;
}
.hero h1 {
    font-size: 28px;
    font-weight: 700;
    color: #FFFFFF;
    margin: 0 0 6px 0;
    line-height: 1.2;
    letter-spacing: -0.03em;
}
.hero-sub {
    font-size: 14px;
    color: #8E8E93;
    margin: 0;
    font-weight: 400;
}

/* ---- SECTION LABEL ---- */
.section-label {
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #8E8E93;
    margin: 0 0 8px 0;
    padding: 0 24px;
}

/* ---- FIELD GROUPS ---- */
.field-group {
    background: white;
    border-radius: 16px;
    border: 1px solid #E5E5EA;
    margin: 0 16px 12px 16px;
    overflow: hidden;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}

/* ---- Override Streamlit widgets ---- */

/* Selectbox */
div[data-testid="stSelectbox"] > label {
    font-size: 11px !important;
    font-weight: 600 !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    color: #8E8E93 !important;
    margin-bottom: 4px !important;
}
div[data-testid="stSelectbox"] > div > div {
    background: white !important;
    border: 1.5px solid #E5E5EA !important;
    border-radius: 12px !important;
    font-size: 15px !important;
    font-weight: 500 !important;
    color: #1C1C1E !important;
    padding: 4px 8px !important;
    transition: border-color .2s, box-shadow .2s !important;
    box-shadow: none !important;
}
div[data-testid="stSelectbox"] > div > div:focus-within {
    border-color: #1C1C1E !important;
    box-shadow: 0 0 0 3px rgba(28,28,30,0.08) !important;
}

/* Radio - pill style */
div[data-testid="stRadio"] > label {
    font-size: 11px !important;
    font-weight: 600 !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    color: #8E8E93 !important;
    margin-bottom: 8px !important;
}
div[data-testid="stRadio"] > div {
    gap: 8px !important;
    flex-wrap: wrap !important;
}
div[data-testid="stRadio"] > div > label {
    background: #F2F2F7 !important;
    border: 1.5px solid transparent !important;
    border-radius: 999px !important;
    padding: 8px 20px !important;
    font-size: 14px !important;
    font-weight: 500 !important;
    color: #3A3A3C !important;
    cursor: pointer !important;
    transition: all .15s ease !important;
    text-transform: none !important;
    letter-spacing: 0 !important;
}
div[data-testid="stRadio"] > div > label:has(input:checked) {
    background: #1C1C1E !important;
    border-color: #1C1C1E !important;
    color: white !important;
    box-shadow: 0 2px 8px rgba(28,28,30,0.25) !important;
}

/* Slider */
div[data-testid="stSlider"] > label {
    font-size: 11px !important;
    font-weight: 600 !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    color: #8E8E93 !important;
}
div[data-testid="stSlider"] [role="slider"] {
    background: #1C1C1E !important;
    border: 3px solid white !important;
    box-shadow: 0 2px 6px rgba(0,0,0,0.2) !important;
    width: 22px !important;
    height: 22px !important;
}
div[data-testid="stSlider"] [data-baseweb="slider"] [data-testid="stSliderTrackFill"] {
    background: #1C1C1E !important;
}

/* Multiselect */
div[data-testid="stMultiSelect"] > label {
    font-size: 11px !important;
    font-weight: 600 !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    color: #8E8E93 !important;
    margin-bottom: 4px !important;
}
div[data-testid="stMultiSelect"] > div > div {
    background: white !important;
    border: 1.5px solid #E5E5EA !important;
    border-radius: 12px !important;
    min-height: 52px !important;
    padding: 4px 8px !important;
    transition: border-color .2s !important;
}
div[data-testid="stMultiSelect"] > div > div:focus-within {
    border-color: #1C1C1E !important;
    box-shadow: 0 0 0 3px rgba(28,28,30,0.08) !important;
}
.stMultiSelect [data-baseweb="tag"] {
    background: #F2F2F7 !important;
    border: none !important;
    color: #1C1C1E !important;
    border-radius: 8px !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    padding: 4px 10px !important;
}
.stMultiSelect [data-baseweb="tag"] span { color: #1C1C1E !important; }

/* Button - Idealista style */
div[data-testid="stButton"] > button {
    background: #FF4500 !important;
    color: white !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 700 !important;
    font-size: 16px !important;
    border: none !important;
    border-radius: 14px !important;
    padding: 16px 24px !important;
    width: 100% !important;
    letter-spacing: -0.01em !important;
    box-shadow: 0 4px 16px rgba(255,69,0,0.3) !important;
    transition: all .2s ease !important;
    margin: 4px 0 !important;
}
div[data-testid="stButton"] > button:hover {
    background: #E63E00 !important;
    box-shadow: 0 6px 24px rgba(255,69,0,0.4) !important;
    transform: translateY(-1px) !important;
}
div[data-testid="stButton"] > button:active {
    transform: translateY(0) !important;
}
div[data-testid="stButton"] > button:disabled {
    background: #E5E5EA !important;
    color: #AEAEB2 !important;
    box-shadow: none !important;
    transform: none !important;
}

/* Metric cards */
[data-testid="metric-container"] {
    background: white !important;
    border: 1px solid #E5E5EA !important;
    border-radius: 16px !important;
    padding: 16px !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.05) !important;
}
[data-testid="metric-container"] [data-testid="stMetricLabel"] {
    font-size: 11px !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.08em !important;
    color: #8E8E93 !important;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    font-size: 22px !important;
    font-weight: 700 !important;
    color: #1C1C1E !important;
    letter-spacing: -0.02em !important;
}
[data-testid="stMetricDelta"] svg { display: none !important; }
[data-testid="stMetricDelta"] > div {
    font-size: 12px !important;
    font-weight: 500 !important;
}

/* Divider */
hr { border: none !important; border-top: 1px solid #F2F2F7 !important; margin: 16px 0 !important; }

/* Expander */
details {
    border: 1px solid #E5E5EA !important;
    border-radius: 16px !important;
    overflow: hidden !important;
    background: white !important;
    margin: 12px 16px !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04) !important;
}
summary {
    padding: 16px !important;
    font-weight: 600 !important;
    font-size: 14px !important;
    color: #1C1C1E !important;
    background: white !important;
    cursor: pointer !important;
}

/* Badge fascia */
.fascia-badge {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 5px 12px;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 600;
    margin: 3px 4px 3px 0;
    letter-spacing: 0.01em;
}

/* Caption / link */
.stCaption, .stCaption a {
    font-size: 12px !important;
    color: #8E8E93 !important;
}

/* Inner padding for all widget areas */
.stSelectbox, .stMultiSelect, .stRadio, .stSlider, .stButton {
    padding: 0 16px !important;
    margin-bottom: 16px !important;
}

/* Section headers */
h4 {
    font-size: 20px !important;
    font-weight: 700 !important;
    letter-spacing: -0.02em !important;
    color: #1C1C1E !important;
    padding: 0 16px !important;
    margin: 24px 0 16px 0 !important;
}

.stCaption { padding: 0 16px !important; }

/* Download button */
div[data-testid="stDownloadButton"] > button {
    background: #F2F2F7 !important;
    color: #1C1C1E !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    font-size: 14px !important;
    box-shadow: none !important;
}

/* Progress bar */
div[data-testid="stProgressBar"] > div {
    background: #FF4500 !important;
    border-radius: 999px !important;
}

@media (max-width: 480px) {
    .block-container { max-width: 100% !important; }
    .hero { padding: 48px 20px 28px 20px; }
    .hero h1 { font-size: 24px; }
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
    "Box / Garage":           "box",
    "Posti auto coperti":     "posti_auto_coperti",
    "Magazzini":              "magazzini",
    "Capannoni industriali":  "capannoni_industriali",
}

FASCIA_LABEL = {
    "A": "Centrale",   "B": "Semicentrale", "C": "Periferica",
    "D": "Suburbana",  "E": "Extraurbana",  "R": "Rurale",
}
FASCIA_COLOR_BG = {
    "A": "#FFF3E0", "B": "#E3F2FD", "C": "#E8F5E9",
    "D": "#FBE9E7", "E": "#F3E5F5", "R": "#E0F7FA",
}
FASCIA_COLOR_TEXT = {
    "A": "#E65100", "B": "#1565C0", "C": "#2E7D32",
    "D": "#BF360C", "E": "#6A1B9A", "R": "#006064",
}
LINE_COLORS = ["#FF4500", "#0070C0", "#00875A", "#9B59B6", "#E67E22", "#16A085"]


def hex_to_rgba(h, alpha=0.1):
    h = h.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return "rgba({},{},{},{})".format(r, g, b, alpha)


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
    return _fetch_def(codice, anno, tipo, op, zona) if anno_definitivo(anno) \
           else _fetch_rec(codice, anno, tipo, op, zona)


def extract_prezzi(data, tipo_api, op):
    if not data or tipo_api not in data: return None
    d = data[tipo_api]
    k = "acquisto" if op == "acquisto" else "affitto"
    m = d.get("prezzo_{}_medio".format(k))
    if not m: return None
    return {
        "min":   d.get("prezzo_{}_min".format(k)),
        "max":   d.get("prezzo_{}_max".format(k)),
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


# ---------- HERO ----------
st.markdown(
    "<div class=hero>"
    "<div class=hero-eyebrow>Dati ufficiali Agenzia delle Entrate</div>"
    "<h1>Prezzi Immobili<br>Italia</h1>"
    "<p class=hero-sub>Quotazioni OMI &middot; Aggiornate ogni semestre</p>"
    "</div>",
    unsafe_allow_html=True,
)

# ---------- SEARCH ----------
st.markdown("#### Cerca")

comune_sel = st.selectbox(
    "Comune",
    NOMI_COMUNI,
    index=NOMI_COMUNI.index("Roma") if "Roma" in NOMI_COMUNI else 0,
)
codice_comune = COMUNI[comune_sel]

tipo_label = st.selectbox("Tipologia immobile", list(TIPI_IMMOBILE.keys()))
tipo_api   = TIPI_IMMOBILE[tipo_label]

operazione = st.radio("Operazione", ["Acquisto", "Affitto"], horizontal=True)
op_key = operazione.lower()

anni_range = st.slider("Periodo di analisi", 2004, 2025, (2012, 2024))
anni_sel   = list(range(anni_range[0], anni_range[1] + 1))

# ---------- ZONE ----------
st.markdown("#### Zone disponibili")

zone_disp = zone_del_comune(codice_comune)
zone_sel  = []

if not zone_disp:
    st.warning("Nessuna zona trovata per questo comune.")
else:
    fasce = sorted(set(z[0] for z in zone_disp))
    badges = "".join(
        "<span class=fascia-badge style=\"background:{};color:{}\">{} {}</span>".format(
            FASCIA_COLOR_BG.get(f, "#F2F2F7"),
            FASCIA_COLOR_TEXT.get(f, "#3A3A3C"),
            f,
            FASCIA_LABEL.get(f, f),
        )
        for f in fasce
    )
    st.markdown(
        "<div style=\"padding:0 16px 8px 16px\">{}</div>".format(badges),
        unsafe_allow_html=True,
    )

    opzioni = {nome_zona(codice_comune, z): z for z in zone_disp}

    default, viste = [], set()
    for z in zone_disp:
        if z[0] not in viste:
            default.append(nome_zona(codice_comune, z))
            viste.add(z[0])
        if len(default) >= 3:
            break

    sel_labels = st.multiselect(
        "{} zone - seleziona fino a 6".format(len(zone_disp)),
        options=list(opzioni.keys()),
        default=default,
        max_selections=6,
    )
    zone_sel = [opzioni[l] for l in sel_labels]

st.caption("[Mappa zone OMI](https://www1.agenziaentrate.gov.it/servizi/geopoi_omi/index.php)")

# ---------- CTA ----------
avvia = st.button(
    "Analizza {}".format(comune_sel),
    disabled=(len(zone_sel) == 0),
    use_container_width=True,
)

# ---------- RUN ----------
if avvia:
    tutti_df = []
    for zona in zone_sel:
        label = nome_zona(codice_comune, zona)
        df = fetch_serie(label, codice_comune, anni_sel, tipo_api, op_key, zona)
        if not df.empty:
            tutti_df.append(df)
    if not tutti_df:
        st.error("Nessun dato trovato. Prova zone o periodo diversi.")
        st.stop()
    st.session_state.update({
        "df_all":     pd.concat(tutti_df, ignore_index=True),
        "operazione": op_key,
        "anni_range": anni_range,
        "comune_sel": comune_sel,
    })

# ---------- RESULTS ----------
if "df_all" in st.session_state:
    df_all  = st.session_state["df_all"]
    op      = st.session_state["operazione"]
    c_nome  = st.session_state["comune_sel"]
    unita   = "euro/mq" if op == "acquisto" else "euro/mq/mese"
    labels  = df_all["label"].unique().tolist()
    palette = LINE_COLORS[:len(labels)]
    c_map   = dict(zip(labels, palette))

    # Header risultati
    ar = st.session_state["anni_range"]
    st.markdown(
        "<div style=\"padding:8px 16px;\">"
        "<span style=\"font-size:12px;font-weight:600;color:#8E8E93;"
        "text-transform:uppercase;letter-spacing:0.08em\">"
        "{} &middot; {} &middot; {}-{}"
        "</span></div>".format(
            c_nome, "Acquisto" if op == "acquisto" else "Affitto", ar[0], ar[1]
        ),
        unsafe_allow_html=True,
    )

    # Metriche
    cols = st.columns(min(len(labels), 2))
    for i, label in enumerate(labels):
        dfl = df_all[df_all["label"] == label].sort_values("anno")
        if dfl.empty: continue
        ult, pri = dfl.iloc[-1], dfl.iloc[0]
        var = ((ult["medio"] - pri["medio"]) / pri["medio"] * 100) if pri["medio"] else 0
        with cols[i % min(len(labels), 2)]:
            st.metric(
                label=label,
                value="{:,.0f}".format(ult["medio"]),
                delta="{:+.1f}% dal {}".format(var, int(pri["anno"])),
            )
            st.caption(unita + " &middot; " + str(int(ult["anno"])))

    st.divider()

    # Grafico andamento - stile pulito
    fig = go.Figure()
    for idx, label in enumerate(labels):
        dfl = df_all[df_all["label"] == label].sort_values("anno")
        col = c_map[label]
        if dfl["min"].notna().any():
            fig.add_trace(go.Scatter(
                x=pd.concat([dfl["anno"], dfl["anno"][::-1]]),
                y=pd.concat([dfl["max"], dfl["min"][::-1]]),
                fill="toself",
                fillcolor=hex_to_rgba(col, 0.08),
                line=dict(color="rgba(0,0,0,0)"),
                showlegend=False, hoverinfo="skip",
            ))
        fig.add_trace(go.Scatter(
            x=dfl["anno"], y=dfl["medio"],
            mode="lines+markers", name=label,
            line=dict(color=col, width=2, shape="spline", smoothing=0.8),
            marker=dict(size=5, color=col, line=dict(color="white", width=1.5)),
            hovertemplate="<b>%{x}</b><br>{}: %{{y:,.0f}} {}<extra></extra>".format(label, unita),
        ))

    fig.update_layout(
        title=dict(
            text="Andamento prezzi",
            font=dict(size=15, color="#1C1C1E", family="DM Sans"),
            x=0, xanchor="left",
        ),
        xaxis=dict(
            tickmode="linear", dtick=2,
            gridcolor="#F2F2F7", linecolor="#E5E5EA",
            color="#8E8E93", tickfont=dict(size=11),
            showgrid=True,
        ),
        yaxis=dict(
            gridcolor="#F2F2F7", linecolor="#E5E5EA",
            color="#8E8E93", tickformat=",.0f",
            tickfont=dict(size=11),
        ),
        plot_bgcolor="white", paper_bgcolor="white",
        font=dict(family="DM Sans", color="#1C1C1E", size=12),
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            orientation="h", yanchor="bottom", y=1.01,
            xanchor="left", x=0,
            font=dict(size=11),
        ),
        hovermode="x unified",
        height=300,
        margin=dict(l=0, r=0, t=44, b=0),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # Grafico variazione YoY
    fig2 = go.Figure()
    for label in labels:
        dfl = df_all[df_all["label"] == label].sort_values("anno").copy()
        dfl["var"] = dfl["medio"].pct_change() * 100
        col = c_map[label]
        fig2.add_trace(go.Bar(
            x=dfl["anno"], y=dfl["var"], name=label,
            marker=dict(
                color=[hex_to_rgba(col, 0.9) if v >= 0 else hex_to_rgba("#FF3B30", 0.8)
                       for v in dfl["var"].fillna(0)],
                line=dict(width=0),
            ),
            hovertemplate="<b>%{x}</b>: %{y:+.1f}%<extra>{}</extra>".format(label),
        ))

    fig2.add_hline(y=0, line_color="#E5E5EA", line_width=1)
    fig2.update_layout(
        title=dict(
            text="Variazione % annua",
            font=dict(size=15, color="#1C1C1E", family="DM Sans"),
            x=0, xanchor="left",
        ),
        barmode="group",
        xaxis=dict(
            tickmode="linear", dtick=2,
            gridcolor="#F2F2F7", linecolor="#E5E5EA",
            color="#8E8E93", tickfont=dict(size=11),
        ),
        yaxis=dict(
            gridcolor="#F2F2F7", color="#8E8E93",
            ticksuffix="%", tickfont=dict(size=11),
            zeroline=False,
        ),
        plot_bgcolor="white", paper_bgcolor="white",
        font=dict(family="DM Sans", color="#1C1C1E", size=12),
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            orientation="h", yanchor="bottom", y=1.01,
            xanchor="left", x=0, font=dict(size=11),
        ),
        bargap=0.3, bargroupgap=0.05,
        height=240,
        margin=dict(l=0, r=0, t=44, b=0),
    )
    st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

    # Tabella dati
    with st.expander("Dati completi"):
        df_show = df_all[["anno", "label", "min", "medio", "max", "stato"]].copy()
        df_show.columns = ["Anno", "Zona", "Minimo", "Medio", "Massimo", "Stato"]
        st.dataframe(
            df_show.sort_values(["Zona", "Anno"]),
            use_container_width=True, hide_index=True,
        )
        st.download_button(
            "Scarica CSV",
            df_show.to_csv(index=False).encode("utf-8"),
            "quotazioni_omi.csv", "text/csv",
            use_container_width=True,
        )

    st.markdown(
        "<div style=\"padding:24px 16px 8px 16px;text-align:center;\">"
        "<span style=\"font-size:11px;color:#C7C7CC\">"
        "Fonte: Agenzia delle Entrate &middot; OMI &middot; 100 mq commerciali"
        "</span></div>",
        unsafe_allow_html=True,
    )
