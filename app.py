import streamlit as st
import requests
import plotly.graph_objects as go
import pandas as pd
import time
from datetime import date
from pathlib import Path

st.set_page_config(
    page_title="Prezzi Immobili Italia",
    page_icon="🏠",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
  
  html, body, .stApp { 
      background-color: #F7F7F9 !important; 
      color: #222222 !important; 
      font-family: 'Inter', -apple-system, sans-serif !important;
  }
  
  section[data-testid="stSidebar"], button[kind="header"],
  header[data-testid="stHeader"], #MainMenu, footer { display: none !important; }
  
  .block-container { 
      padding: 2rem 1rem 4rem 1rem !important; 
      max-width: 760px !important; 
  }
  
  .card {
    background: #FFFFFF; 
    border: 1px solid #EBEBEB;
    border-radius: 16px; 
    padding: 1.5rem; 
    margin-bottom: 1.5rem;
    box-shadow: 0 6px 16px rgba(0, 0, 0, 0.04);
  }
  
  .card-title {
    font-size: 0.85rem; 
    font-weight: 700; 
    color: #717171;
    text-transform: uppercase; 
    letter-spacing: 0.05em; 
    margin: 0 0 1rem 0;
  }
  
  .stMultiSelect [data-baseweb="tag"] {
    background-color: #F7F7F9 !important; 
    border: 1px solid #DDDDDD !important;
    color: #222222 !important; 
    border-radius: 8px !important;
    font-weight: 500;
  }
  
  div[data-testid="stButton"] > button {
    width: 100%; 
    background: #FF385C; 
    color: #FFFFFF;
    font-weight: 600; 
    font-size: 1rem; 
    border: none;
    border-radius: 12px; 
    padding: 0.75rem; 
    transition: transform 0.1s ease, background 0.2s ease;
  }
  
  div[data-testid="stButton"] > button:hover { 
      background: #D90B3E; 
      color: #FFFFFF;
  }
  
  div[data-testid="stButton"] > button:active {
      transform: scale(0.98);
  }
  
  [data-testid="metric-container"] {
    background: #FFFFFF; 
    border: 1px solid #EBEBEB;
    border-radius: 16px; 
    padding: 1.2rem;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03);
  }
  
  [data-testid="metric-container"] label { 
      color: #717171 !important; 
      font-size: 0.85rem !important; 
      font-weight: 500 !important;
  }
  
  [data-testid="metric-container"] div[data-testid="stMetricValue"] {
      color: #222222 !important;
      font-weight: 700 !important;
  }
  
  .results-label {
    font-size: 1.25rem; 
    font-weight: 700;
    color: #222222; 
    margin: 1.5rem 0 1rem 0;
  }
  
  p, div, span, label {
      color: #222222;
  }
  
  .stSelectbox label, .stRadio label, .stSlider label, .stNumberInput label {
      font-weight: 600 !important;
      color: #222222 !important;
  }
  
  @media (max-width: 600px) {
    .block-container { padding: 1rem 0.5rem 3rem 0.5rem !important; }
    .card { padding: 1rem; }
  }
</style>
""", unsafe_allow_html=True)

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
    "A": "#FF385C", 
    "B": "#00A699", 
    "C": "#FFB400", 
    "D": "#FC642D", 
    "E": "#484848", 
    "R": "#767676", 
}

def hex_to_rgba(h, alpha=0.15):
    h = h.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return "rgba({},{},{},{})".format(r, g, b, alpha)

def colore_zona(zona):
    return FASCIA_COLOR.get(zona[0] if zona else "B", "#00A699")

@st.cache_data(show_spinner=False)
def carica_dati():
    try:
        zone_df   = pd.read_parquet(BASE_DIR / "zone.parquet")
        comuni_df = pd.read_parquet(BASE_DIR / "comuni.parquet")
        zone_lookup = {
            (r.codice, r.zona): r.zona_descr
            for r in zone_df.itertuples()
        }
        comuni_dict = dict(zip(comuni_df["nome"], comuni_df["codice"]))
        return zone_lookup, comuni_dict
    except FileNotFoundError:
        return {}, {"Roma": "H501", "Milano": "F205", "Novara": "F952"}

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
    try:
        df = pd.read_parquet(BASE_DIR / "zone.parquet")
        zone = df.loc[df["codice"] == codice, "zona"].unique().tolist()
        zone.sort(key=lambda z: (z[0], int(z[1:]) if z[1:].isdigit() else 0))
        return zone
    except FileNotFoundError:
        return ["B1", "C2", "D3"]

def anno_definitivo(a):
    if a < ANNO_CORR - 1:
        return True
    if a == ANNO_CORR - 1 and date.today().month >= 7:
        return True
    return False

def _chiama_api(codice, anno, tipo, op, zona):
    try:
        p = {
            "codice_comune": codice, "anno": anno,
            "tipo_immobile": tipo, "operazione": op, 
            "metri_quadri": 1, 
        }
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
    if anno_definitivo(anno):
        return _fetch_def(codice, anno, tipo, op, zona)
    return _fetch_rec(codice, anno, tipo, op, zona)

def extract_prezzi(data, tipo_api, op):
    if not data or tipo_api not in data:
        return None
    d = data[tipo_api]
    k = "acquisto" if op == "acquisto" else "affitto"
    m = d.get("prezzo_{}_medio".format(k))
    if not m:
        return None
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
        if not da_cache:
            time.sleep(0.35)
        p = extract_prezzi(d, tipo_api, op)
        if p:
            rows.append({
                "anno": anno, "label": label,
                "medio": p["medio"], "min": p["min"],
                "max": p["max"], "stato": p["stato"],
            })
        prog.progress((i + 1) / len(anni), text="{} - {}".format(label, anno))
    prog.empty()
    return pd.DataFrame(rows)

def accorcia_legenda(testo):
    troncato = testo.split(',')[0]
    if len(troncato) > 20:
        return troncato[:20].strip() + "..."
    return troncato

# --- UI ---

st.markdown("<h2 style='font-weight: 700; color: #222222; margin-bottom: 0.2rem;'>Prezzi Immobili Italia</h2>", unsafe_allow_html=True)
st.markdown(
    "<p style='color:#717171;font-size:0.95rem;margin-top:0;margin-bottom:2rem;font-weight:500;'>"
    "Dati ufficiali Agenzia delle Entrate - OMI</p>",
    unsafe_allow_html=True,
)

st.markdown('<div class="card"><p class="card-title">Cerca una città</p>', unsafe_allow_html=True)

comune_sel = st.selectbox(
    "Comune", NOMI_COMUNI,
    index=NOMI_COMUNI.index("Novara") if "Novara" in NOMI_COMUNI else 0,
    label_visibility="collapsed",
)
codice_comune = COMUNI.get(comune_sel, "H501")

c1, c2, c3 = st.columns([4, 2, 3])
with c1:
    tipo_label = st.selectbox("Tipologia", list(TIPI_IMMOBILE.keys()))
    tipo_api   = TIPI_IMMOBILE[tipo_label]
with c2:
    mq_sel = st.number_input("Superficie (mq)", min_value=10, max_value=1500, value=100, step=5)
with c3:
    operazione = st.radio("Operazione", ["acquisto", "affitto"], horizontal=True)

anni_range = st.slider("Periodo", 2004, 2025, (2012, 2024))
anni_sel   = list(range(anni_range[0], anni_range[1] + 1))

st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="card"><p class="card-title">Zone OMI</p>', unsafe_allow_html=True)

zone_disp = zone_del_comune(codice_comune)
zone_sel = []

if not zone_disp:
    st.warning("Nessuna zona trovata per questo comune.")
else:
    fasce = sorted(set(z[0] for z in zone_disp))
    badges = " ".join(
        '<span style="background:{};color:#FFFFFF;'.format(FASCIA_COLOR.get(f, "#888")) +
        'padding:4px 12px;border-radius:999px;font-size:0.75rem;font-weight:600;display:inline-block;margin-bottom:8px;">' +
        '{}</span>'.format(FASCIA_LABEL.get(f, f))
        for f in fasce
    )
    st.markdown(badges + "<br><br>", unsafe_allow_html=True)

    opzioni = {nome_zona(codice_comune, z): z for z in zone_disp}

    default, viste = [], set()
    for z in zone_disp:
        if z[0] not in viste:
            default.append(nome_zona(codice_comune, z))
            viste.add(z[0])
        if len(default) >= 4:
            break

    sel_labels = st.multiselect(
        "{} zone disponibili - seleziona quelle da confrontare (max 6)".format(len(zone_disp)),
        options=list(opzioni.keys()),
        default=default,
        max_selections=6,
        label_visibility="collapsed",
    )
    zone_sel = [opzioni[l] for l in sel_labels]

st.markdown(
    "<a href='https://www1.agenziaentrate.gov.it/servizi/geopoi_omi/index.php' target='_blank' "
    "style='font-size:0.8rem;color:#717171;text-decoration:underline;'>Visualizza zone su mappa ufficiale</a>", 
    unsafe_allow_html=True
)
st.markdown('</div>', unsafe_allow_html=True)

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
        "df_all":     pd.concat(tutti_df, ignore_index=True),
        "operazione": operazione,
        "anni_range": anni_range,
        "comune_sel": comune_sel,
        "mq_sel":     mq_sel,
    })

if "df_all" in st.session_state:
    df_all  = st.session_state["df_all"]
    op      = st.session_state["operazione"]
    c_nome  = st.session_state["comune_sel"]
    mq_val  = st.session_state.get("mq_sel", 100)
    unita   = "€/mq" if op == "acquisto" else "€/mq/mese"
    labels  = df_all["label"].unique().tolist()
    c_map   = {l: colore_zona(l.split("-")[0].strip()) for l in labels}

    st.markdown(
        '<p class="results-label">{} &middot; {} &middot; {}-{}</p>'.format(
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
        if dfl.empty:
            continue
        ult, pri = dfl.iloc[-1], dfl.iloc[0]
        var = ((ult["medio"] - pri["medio"]) / pri["medio"] * 100) if pri["medio"] else 0
        
        prezzo_mq = ult["medio"]
        pmq_fmt = "{:,.0f}".format(prezzo_mq).replace(",", ".")
        
        with cols[i % min(len(labels), 3)]:
            st.metric(
                label=label,
                value=f"{pmq_fmt} {unita}",
                delta=f"{var:+.1f}% dal {int(pri['anno'])}",
                delta_color="off"
            )

    st.markdown("<br>", unsafe_allow_html=True)

    fig = go.Figure()
    for label in labels:
        dfl = df_all[df_all["label"] == label].sort_values("anno")
        col = c_map[label]
        nome_legenda = accorcia_legenda(label)
        
        prezzi_medio_tot = dfl["medio"] * mq_val
        prezzi_max_tot = dfl["max"] * mq_val
        prezzi_min_tot = dfl["min"] * mq_val

        if dfl["min"].notna().any():
            fig.add_trace(go.Scatter(
                x=pd.concat([dfl["anno"], dfl["anno"][::-1]]),
                y=pd.concat([prezzi_max_tot, prezzi_min_tot[::-1]]),
                fill="toself",
                fillcolor=hex_to_rgba(col, 0.1),
                line=dict(color="rgba(0,0,0,0)"),
                showlegend=False,
                hoverinfo="skip",
            ))
        fig.add_trace(go.Scatter(
            x=dfl["anno"], y=prezzi_medio_tot,
            mode="lines+markers", name=nome_legenda,
            line=dict(color=col, width=3),
            marker=dict(size=8, color=col, line=dict(color="#FFFFFF", width=1.5)),
            hovertemplate="<b>{}</b><br>%{{x}}: € %{{y:,.0f}}<extra></extra>".format(nome_legenda),
        ))

    fig.update_layout(
        title=dict(text=f"Andamento storico prezzo totale ({mq_val} mq)", font=dict(size=16, color="#222222", weight="bold")),
        xaxis=dict(tickmode="linear", dtick=2, gridcolor="#F0F0F0", color="#717171"),
        yaxis=dict(gridcolor="#F0F0F0", color="#717171", tickformat=",.0f"),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color="#717171", size=13),
        legend=dict(bgcolor="rgba(255,255,255,0.8)", orientation="h",
                    yanchor="bottom", y=1.05, xanchor="left", x=0),
        hovermode="x unified", height=380,
        margin=dict(l=0, r=0, t=60, b=0),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    fig2 = go.Figure()
    for label in labels:
        dfl = df_all[df_all["label"] == label].sort_values("anno").copy()
        dfl["var"] = dfl["medio"].pct_change() * 100
        nome_legenda = accorcia_legenda(label)
        
        fig2.add_trace(go.Bar(
            x=dfl["anno"], y=dfl["var"], name=nome_legenda,
            marker_color=c_map[label],
            marker_line=dict(color="#FFFFFF", width=1),
            hovertemplate="<b>{}</b> %{{x}}: %{{y:+.1f}}%<extra></extra>".format(nome_legenda),
        ))
    fig2.update_layout(
        title=dict(text="Variazione percentuale anno su anno", font=dict(size=16, color="#222222", weight="bold")),
        barmode="group",
        xaxis=dict(tickmode="linear", dtick=2, gridcolor="#F0F0F0", color="#717171"),
        yaxis=dict(gridcolor="#F0F0F0", color="#717171", ticksuffix="%"),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color="#717171", size=13),
        legend=dict(bgcolor="rgba(255,255,255,0.8)", orientation="h",
                    yanchor="bottom", y=1.05, xanchor="left", x=0),
        height=320, margin=dict(l=0, r=0, t=60, b=0),
    )
    st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("Mostra dati completi (Valori al mq)"):
        df_show = df_all[["anno", "label", "min", "medio", "max", "stato"]].copy()
        df_show.columns = ["Anno", "Zona", "Min", "Medio", "Max", "Stato zona"]
        st.dataframe(df_show.sort_values(["Zona", "Anno"]),
                     use_container_width=True, hide_index=True)
        st.download_button(
            "Scarica CSV",
            df_show.to_csv(index=False).encode("utf-8"),
            "quotazioni_omi.csv", "text/csv",
            use_container_width=True,
        )

    st.markdown(
        f"<p style='text-align:center;color:#717171;font-size:0.8rem;margin-top:2.5rem;font-weight:500;'>"
        f"Fonte: Agenzia delle Entrate - OMI &middot; Grafici calcolati su {mq_val} mq</p>",
        unsafe_allow_html=True,
    )
