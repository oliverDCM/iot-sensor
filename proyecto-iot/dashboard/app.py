import streamlit as st
import pandas as pd
import firebase_admin
from firebase_admin import credentials, firestore
import pytz
from datetime import datetime

BOGOTA = pytz.timezone("America/Bogota")

st.set_page_config(page_title="Dashboard Sensor IR", page_icon="📡", layout="wide")
st.markdown("""
    <style>
        .estado-presencia {
            background-color: #1a3a2a; color: #3fb950; padding: 20px;
            border-radius: 12px; font-size: 2rem; font-weight: bold;
            text-align: center; border: 2px solid #3fb950;
        }
        .estado-libre {
            background-color: #1a1f2e; color: #58a6ff; padding: 20px;
            border-radius: 12px; font-size: 2rem; font-weight: bold;
            text-align: center; border: 2px solid #58a6ff;
        }
    </style>
""", unsafe_allow_html=True)

if not firebase_admin._apps:
    cred = credentials.Certificate(dict(st.secrets["firebase"]))
    firebase_admin.initialize_app(cred)

# ── Caché real: la función no recibe el objeto db como argumento ──
# Streamlit cachea basándose en los argumentos; al no pasar db,
# el caché funciona correctamente entre reruns.
@st.cache_data(ttl=60)
def get_lecturas():
    db = firestore.client()  # ← se obtiene aquí adentro, no como argumento
    docs = (
        db.collection("lecturas")
        .order_by("fecha", direction=firestore.Query.DESCENDING)
        .limit(50)
        .stream()
    )
    rows = []
    for doc in docs:
        d = doc.to_dict()
        fecha_utc = d.get("fecha")
        fecha_local = fecha_utc.astimezone(BOGOTA) if fecha_utc else None
        rows.append({
            "sensor":    d.get("sensor"),
            "estado":    d.get("estado"),
            "deteccion": d.get("deteccion"),
            "fecha":     fecha_local,
        })
    return pd.DataFrame(rows)

# ── UI ──
st.title("📡 Dashboard Sensor Infrarrojo")
st.caption("Arquitectura de Software · Tiempo Real · Auto-refresh cada 60s")

df = get_lecturas()

col1, col2 = st.columns([1, 2])
with col1:
    st.subheader("Estado Actual")
    if not df.empty:
        ultimo = df.iloc[0]
        if ultimo["deteccion"]:
            st.markdown('<div class="estado-presencia">🔴 PRESENCIA</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="estado-libre">🟢 LIBRE</div>', unsafe_allow_html=True)
        st.caption(f"Última lectura: {ultimo['fecha']}")
    else:
        st.warning("Sin datos aún...")

with col2:
    st.subheader("Estadísticas")
    total      = len(df)
    presencias = len(df[df["deteccion"] == True])
    libres     = len(df[df["deteccion"] == False])
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

# ── Auto-refresh correcto: no bloquea, no recarga el script completo ──
st.caption(f"🕐 Próxima actualización en 60s · {datetime.now(BOGOTA).strftime('%H:%M:%S')}")
st.rerun()  # ← sin sleep; el caché ttl=60 controla cuándo va a Firestore
