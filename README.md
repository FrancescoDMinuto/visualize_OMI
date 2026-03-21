# 🏙️ Mercato Immobiliare OMI

Dashboard per analizzare l'andamento storico dei prezzi immobiliari italiani,
basata sui dati ufficiali **OMI** dell'Agenzia delle Entrate via [3eurotools.it](https://3eurotools.it/api-quotazioni-immobiliari-omi).

## Deploy su Streamlit Cloud (gratis)

1. Crea un repo GitHub e carica: `app.py`, `requirements.txt`, `.gitignore`
2. Vai su **[share.streamlit.io](https://share.streamlit.io)** → accedi con GitHub
3. "New app" → seleziona il repo → `app.py` come file principale
4. Deploy → link pubblico in 1-2 minuti

## Come funziona la cache

| Anno | Comportamento |
|------|---------------|
| Storici consolidati | `ttl=None` — permanente in memoria, mai ri-scaricati |
| Anno corrente / non consolidato | `ttl=300s` — aggiornati ogni 5 minuti |

## Uso locale

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Trovare le zone OMI

https://www1.agenziaentrate.gov.it/servizi/geopoi_omi/index.php
