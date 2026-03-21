import streamlit as st
import requests
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import time
from datetime import date

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Mercato Immobiliare OMI",
    page_icon="🏙️",
    layout="wide",
)

st.markdown("""
<style>
    .stApp { background-color: #0e1117; }
    h1 { font-family: Georgia, serif; }
    .stMultiSelect [data-baseweb="tag"] { background-color: #c8a84b !important; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# DATI DI RIFERIMENTO
# ─────────────────────────────────────────────
COMUNI = {
    "Milano": "F205",
    "Roma": "H501",
    "Napoli": "F839",
    "Torino": "L219",
    "Firenze": "D612",
    "Bologna": "A944",
    "Venezia": "L736",
    "Palermo": "G273",
    "Genova": "D969",
    "Bari": "A662",
    "Catania": "C351",
    "Verona": "L781",
    "Padova": "G224",
    "Trieste": "L424",
    "Brescia": "B157",
    "Bergamo": "A794",
    "Modena": "F257",
    "Parma": "G337",
    "Perugia": "G478",
    "Reggio Calabria": "H224",
}

TIPI_IMMOBILE = {
    "Abitazioni civili (A/2)": "abitazioni_civili",
    "Abitazioni economiche (A/3-4-5)": "abitazioni_di_tipo_economico",
    "Abitazioni signorili (A/1)": "abitazioni_signorili",
    "Ville e villini (A/7-8)": "ville_e_villini",
    "Negozi (C/1)": "negozi",
    "Uffici (A/10)": "uffici",
    "Box/Garage (C/6)": "box",
    "Posti auto coperti": "posti_auto_coperti",
    "Magazzini (C/2)": "magazzini",
    "Capannoni industriali (D/7)": "capannoni_industriali",
}

ANNI_DISPONIBILI = list(range(2004, 2026))
ANNO_CORRENTE = date.today().year
BASE_URL = "https://3eurotools.it/api-quotazioni-immobiliari-omi/ricerca"


# ─────────────────────────────────────────────
# CACHE INTELLIGENTE
#
# Su Streamlit Cloud il filesystem è effimero (si resetta ad ogni riavvio),
# quindi non usiamo file su disco ma st.cache_data:
#
#   - anni DEFINITIVI (storici consolidati) → ttl=None (permanente finché
#     il server è in piedi, sopravvive a tutte le sessioni utente)
#
#   - anni RECENTI non consolidati (anno corrente e ultimo se prima di luglio)
#     → ttl=300 (5 min), così si aggiornano quando escono nuovi dati OMI
#
# Un anno è "definitivo" se:
#   - è almeno 2 anni fa, OPPURE
#   - è l'anno scorso e siamo dopo luglio (il S2 OMI è già pubblicato)
# ─────────────────────────────────────────────

def anno_e_definitivo(anno: int) -> bool:
    if anno < ANNO_CORRENTE - 1:
        return True
    if anno == ANNO_CORRENTE - 1 and date.today().month >= 7:
        return True
    return False


def _chiama_api(codice_comune, anno, tipo_immobile, operazione, zona_omi):
    params = {
        "codice_comune": codice_comune,
        "anno": anno,
        "tipo_immobile": tipo_immobile,
        "operazione": operazione,
        "metri_quadri": 100,
    }
    if zona_omi:
        params["zona_omi"] = zona_omi
    try:
        r = requests.get(BASE_URL, params=params, timeout=10)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None


@st.cache_data(ttl=None, show_spinner=False)
def _fetch_definitivo(codice_comune, anno, tipo_immobile, operazione, zona_omi):
    """Cache PERMANENTE: ttl=None = non scade mai finché il server è attivo."""
    return _chiama_api(codice_comune, anno, tipo_immobile, operazione, zona_omi)


@st.cache_data(ttl=300, show_spinner=False)
def _fetch_recente(codice_comune, anno, tipo_immobile, operazione, zona_omi):
    """Cache da 5 minuti per anni non ancora consolidati."""
    return _chiama_api(codice_comune, anno, tipo_immobile, operazione, zona_omi)


def fetch_quotazione(codice_comune, anno, tipo_immobile, operazione, zona_omi=None):
    if anno_e_definitivo(anno):
        return _fetch_definitivo(codice_comune, anno, tipo_immobile, operazione, zona_omi)
    else:
        return _fetch_recente(codice_comune, anno, tipo_immobile, operazione, zona_omi)


def extract_prezzi(data, tipo_immobile_api, operazione):
    if not data or tipo_immobile_api not in data:
        return None
    d = data[tipo_immobile_api]
    if operazione == "acquisto":
        return {
            "min": d.get("prezzo_acquisto_min"),
            "max": d.get("prezzo_acquisto_max"),
            "medio": d.get("prezzo_acquisto_medio"),
            "stato": d.get("stato_di_conservazione_mediano_della_zona", "—"),
        }
    else:
        return {
            "min": d.get("prezzo_affitto_min"),
            "max": d.get("prezzo_affitto_max"),
            "medio": d.get("prezzo_affitto_medio"),
            "stato": d.get("stato_di_conservazione_mediano_della_zona", "—"),
        }


def fetch_serie_storica(label, codice_comune, anni, tipo_immobile_api, operazione, zona_omi=None):
    rows = []
    cache_hits, api_calls = 0, 0
    progress = st.progress(0, text=f"Caricamento {label}…")

    for i, anno in enumerate(anni):
        da_cache = anno_e_definitivo(anno)
        data = fetch_quotazione(codice_comune, anno, tipo_immobile_api, operazione, zona_omi)

        if da_cache:
            cache_hits += 1
        else:
            api_calls += 1
            time.sleep(0.35)  # throttle solo per chiamate reali all'API

        prezzi = extract_prezzi(data, tipo_immobile_api, operazione)
        if prezzi and prezzi["medio"]:
            rows.append({
                "anno": anno,
                "label": label,
                "medio": prezzi["medio"],
                "min": prezzi["min"],
                "max": prezzi["max"],
                "stato": prezzi["stato"],
                "fonte": "💾 cache" if da_cache else "🌐 API",
            })

        stato_txt = "💾 cache" if da_cache else f"🌐 API {anno}"
        progress.progress((i + 1) / len(anni), text=f"{label} — {stato_txt}")

    progress.empty()
    df = pd.DataFrame(rows)
    if not df.empty:
        msg = f"**{label}**: {cache_hits} anni da cache permanente"
        if api_calls:
            msg += f" · {api_calls} anni scaricati dall'API (non ancora consolidati)"
        st.caption(msg)
    return df


# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.title("⚙️ Configurazione")
    st.divider()

    modalita = st.radio(
        "Cosa vuoi confrontare?",
        ["Zone dello stesso comune", "Più comuni a confronto"],
    )
    st.divider()

    if modalita == "Zone dello stesso comune":
        comune_sel = st.selectbox("Comune", list(COMUNI.keys()))
        codice_comune = COMUNI[comune_sel]

        st.markdown("**Zone OMI** *(lascia vuoto per l'intero comune)*")
        st.caption("[Trova la tua zona OMI →](https://www1.agenziaentrate.gov.it/servizi/geopoi_omi/index.php)")
        zone_input = st.text_input("Zone separate da virgola", placeholder="es: B1, B3, C1")
        zone_list = [z.strip().upper() for z in zone_input.split(",") if z.strip()] or [None]
        serie_params = [
            (comune_sel, codice_comune, z,
             f"{comune_sel} – {z}" if z else f"{comune_sel} (intero comune)")
            for z in zone_list
        ]
    else:
        comuni_sel = st.multiselect(
            "Scegli i comuni (max 6)", list(COMUNI.keys()),
            default=["Milano", "Roma"], max_selections=6,
        )
        zona_c = st.text_input("Zona OMI per tutti (opzionale)", placeholder="es: B1")
        zona_c = zona_c.strip().upper() or None
        serie_params = [
            (c, COMUNI[c], zona_c, f"{c}{' – ' + zona_c if zona_c else ''}")
            for c in comuni_sel
        ]

    st.divider()
    tipo_label = st.selectbox("Tipologia immobile", list(TIPI_IMMOBILE.keys()))
    tipo_api = TIPI_IMMOBILE[tipo_label]
    operazione = st.radio("Operazione", ["acquisto", "affitto"], horizontal=True)
    anni_range = st.slider("Periodo", min_value=2004, max_value=2025, value=(2010, 2024))
    anni_sel = list(range(anni_range[0], anni_range[1] + 1))

    avvia = st.button("🔍 Analizza andamento", type="primary", use_container_width=True)

    st.divider()
    anni_def = sum(1 for a in anni_sel if anno_e_definitivo(a))
    anni_fresh = len(anni_sel) - anni_def
    st.markdown("**💾 Cache in memoria**")
    st.caption(
        f"Periodo selezionato: **{anni_def}** anni in cache permanente"
        + (f", **{anni_fresh}** aggiornati dall'API." if anni_fresh else ".")
        + "\n\nLa cache permanente sopravvive a tutte le sessioni utente "
        "finché il server Streamlit è attivo."
    )
    st.divider()
    st.caption(
        "Dati: **Agenzia Entrate – OMI** "
        "via [3eurotools.it](https://3eurotools.it/api-quotazioni-immobiliari-omi)\n\n"
        "Prezzi riferiti a 100 mq commerciali."
    )


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
st.title("🏙️ Mercato Immobiliare Italia")
st.markdown(
    f"**{tipo_label}** · {'Acquisto' if operazione == 'acquisto' else 'Affitto/mese'} · "
    f"{anni_range[0]}–{anni_range[1]} · 100 mq commerciali"
)
st.divider()

if avvia:
    if not serie_params:
        st.warning("Seleziona almeno un comune o una zona.")
        st.stop()

    tutti_df = []
    for (nome_comune, codice, zona, label) in serie_params:
        df = fetch_serie_storica(label, codice, anni_sel, tipo_api, operazione, zona)
        if not df.empty:
            tutti_df.append(df)

    if not tutti_df:
        st.error("Nessun dato trovato. Prova con anni o zone diverse.")
        st.stop()

    st.session_state["df_all"] = pd.concat(tutti_df, ignore_index=True)
    st.session_state["operazione"] = operazione
    st.session_state["anni_range"] = anni_range

if "df_all" in st.session_state:
    df_all = st.session_state["df_all"]
    op = st.session_state["operazione"]
    unita = "€" if op == "acquisto" else "€/mese"
    labels = df_all["label"].unique().tolist()
    colori = px.colors.qualitative.Set2[: len(labels)]
    colore_map = dict(zip(labels, colori))

    # ── Grafico andamento ──
    fig = go.Figure()
    for label in labels:
        dfl = df_all[df_all["label"] == label].sort_values("anno")
        col = colore_map[label]
        if dfl["min"].notna().any():
            fc = col.replace("rgb", "rgba").replace(")", ",0.12)") if col.startswith("rgb") else col + "20"
            fig.add_trace(go.Scatter(
                x=pd.concat([dfl["anno"], dfl["anno"][::-1]]),
                y=pd.concat([dfl["max"], dfl["min"][::-1]]),
                fill="toself", fillcolor=fc,
                line=dict(color="rgba(0,0,0,0)"),
                showlegend=False, hoverinfo="skip",
            ))
        fig.add_trace(go.Scatter(
            x=dfl["anno"], y=dfl["medio"],
            mode="lines+markers", name=label,
            line=dict(color=col, width=2.5), marker=dict(size=7),
            hovertemplate=f"<b>{label}</b><br>Anno: %{{x}}<br>Medio: %{{y:,.0f}} {unita}<extra></extra>",
        ))

    fig.update_layout(
        title=dict(text=f"Andamento prezzi – {unita} (100 mq)", font=dict(size=18)),
        xaxis=dict(title="Anno", tickmode="linear", dtick=1, gridcolor="#2a2d3a"),
        yaxis=dict(title=f"Prezzo ({unita})", gridcolor="#2a2d3a", tickformat=",.0f"),
        plot_bgcolor="#0e1117", paper_bgcolor="#0e1117",
        font=dict(color="#cdd1e0"),
        legend=dict(bgcolor="#1a1d27", bordercolor="#2a2d3a", borderwidth=1),
        hovermode="x unified", height=480,
    )
    st.plotly_chart(fig, use_container_width=True)

    # ── Metriche ──
    st.subheader("📊 Riepilogo")
    cols = st.columns(len(labels))
    for col_ui, label in zip(cols, labels):
        dfl = df_all[df_all["label"] == label].sort_values("anno")
        if dfl.empty:
            continue
        ultimo, primo = dfl.iloc[-1], dfl.iloc[0]
        var = ((ultimo["medio"] - primo["medio"]) / primo["medio"] * 100) if primo["medio"] else 0
        with col_ui:
            st.metric(label=label, value=f"{ultimo['medio']:,.0f} {unita}",
                      delta=f"{var:+.1f}% dal {int(primo['anno'])}")
            st.caption(f"Anno: {int(ultimo['anno'])} · Stato zona: *{ultimo['stato']}*")

    # ── Variazione % YoY ──
    st.subheader("📈 Variazione % anno su anno")
    fig2 = go.Figure()
    for label in labels:
        dfl = df_all[df_all["label"] == label].sort_values("anno").copy()
        dfl["var_pct"] = dfl["medio"].pct_change() * 100
        fig2.add_trace(go.Bar(
            x=dfl["anno"], y=dfl["var_pct"], name=label,
            marker_color=colore_map[label],
            hovertemplate=f"<b>{label}</b><br>%{{x}}: %{{y:+.1f}}%<extra></extra>",
        ))
    fig2.update_layout(
        barmode="group",
        xaxis=dict(title="Anno", tickmode="linear", dtick=1, gridcolor="#2a2d3a"),
        yaxis=dict(title="Variazione %", gridcolor="#2a2d3a", ticksuffix="%"),
        plot_bgcolor="#0e1117", paper_bgcolor="#0e1117",
        font=dict(color="#cdd1e0"),
        legend=dict(bgcolor="#1a1d27", bordercolor="#2a2d3a", borderwidth=1),
        height=360,
    )
    st.plotly_chart(fig2, use_container_width=True)

    # ── Tabella ──
    with st.expander("📋 Dati grezzi"):
        df_show = df_all[["anno", "label", "min", "medio", "max", "stato", "fonte"]].copy()
        df_show.columns = ["Anno", "Serie", f"Min ({unita})", f"Medio ({unita})", f"Max ({unita})", "Stato zona", "Fonte"]
        st.dataframe(df_show.sort_values(["Serie", "Anno"]), use_container_width=True, hide_index=True)
        st.download_button("⬇️ Scarica CSV",
                           df_show.to_csv(index=False).encode("utf-8"),
                           "quotazioni_omi.csv", "text/csv")

else:
    st.info(
        "👈 **Configura la ricerca** nella barra laterale e premi **Analizza andamento**.\n\n"
        "**Puoi confrontare:**\n"
        "- Diverse **zone OMI** dello stesso comune (es: B1, B3, C1 di Milano)\n"
        "- Più **comuni** tra loro (es: Milano vs Roma vs Napoli)\n\n"
        "[Mappa zone OMI →](https://www1.agenziaentrate.gov.it/servizi/geopoi_omi/index.php)"
    )
