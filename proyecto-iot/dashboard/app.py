import streamlit as st
import pandas as pd
import firebase_admin
from firebase_admin import credentials, firestore
import time
import pytz

BOGOTA = pytz.timezone("America/Bogota")

def get_lecturas():
    docs = db.collection("lecturas")\
             .order_by("fecha", direction=firestore.Query.DESCENDING)\
             .limit(100)\
             .stream()
    rows = []
    for doc in docs:
        d = doc.to_dict()
        fecha_utc = d.get("fecha")
        # Convertir UTC → hora Colombia
        if fecha_utc:
            fecha_local = fecha_utc.astimezone(BOGOTA)
        else:
            fecha_local = None
        rows.append({
            "sensor":    d.get("sensor"),
            "estado":    d.get("estado"),
            "deteccion": d.get("deteccion"),
            "fecha":     fecha_local,
        })
    return pd.DataFrame(rows)

st.set_page_config(
    page_title="Dashboard Sensor IR",
    page_icon="📡",
    layout="wide"
)

st.markdown("""
    <style>
        .estado-presencia {
            background-color: #1a3a2a;
            color: #3fb950;
            padding: 20px;
            border-radius: 12px;
            font-size: 2rem;
            font-weight: bold;
            text-align: center;
            border: 2px solid #3fb950;
        }
        .estado-libre {
            background-color: #1a1f2e;
            color: #58a6ff;
            padding: 20px;
            border-radius: 12px;
            font-size: 2rem;
            font-weight: bold;
            text-align: center;
            border: 2px solid #58a6ff;
        }
    </style>
""", unsafe_allow_html=True)

# ── Firebase init (solo una vez) ──────────────────────
if not firebase_admin._apps:
    cred = credentials.Certificate(dict(st.secrets["firebase"]))
    firebase_admin.initialize_app(cred)

db = firestore.client()

st.title("📡 Dashboard Sensor Infrarrojo")
st.caption("Arquitectura de Software · Tiempo Real · Auto-refresh cada 2s")

def get_lecturas():
    docs = db.collection("lecturas")\
             .order_by("fecha", direction=firestore.Query.DESCENDING)\
             .limit(100)\
             .stream()
    rows = []
    for doc in docs:
        d = doc.to_dict()
        rows.append({
            "sensor":   d.get("sensor"),
            "estado":   d.get("estado"),
            "deteccion": d.get("deteccion"),
            "fecha":    d.get("fecha"),
        })
    return pd.DataFrame(rows)

placeholder = st.empty()

while True:
    df = get_lecturas()

    with placeholder.container():
        col1, col2 = st.columns([1, 2])

        with col1:
            st.subheader("Estado Actual")
            if not df.empty:
                ultimo = df.iloc[0]
                if ultimo["deteccion"]:
                    st.markdown('<div class="estado-presencia">🔴 PRESENCIA</div>',
                                unsafe_allow_html=True)
                else:
                    st.markdown('<div class="estado-libre">🟢 LIBRE</div>',
                                unsafe_allow_html=True)
                st.caption(f"Última lectura: {ultimo['fecha']}")
            else:
                st.warning("Sin datos aún...")

        with col2:
            st.subheader("Estadísticas")
            total     = len(df)
            presencias = len(df[df["deteccion"] == True])
            libres    = len(df[df["deteccion"] == False])
            c1, c2, c3 = st.columns(3)
            c1.metric("Total lecturas", total)
            c2.metric("Presencias",     presencias)
            c3.metric("Libre",          libres)

        st.divider()
        st.subheader("📋 Historial de lecturas")
        if not df.empty:
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("Sin registros aún")

    time.sleep(2)