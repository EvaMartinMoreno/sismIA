import streamlit as st
import pandas as pd
import os
import subprocess
import locale
import unicodedata
from datetime import datetime


# =========================
# 📁 Rutas de entrada/salida
# =========================
COSTES_PATH = os.path.join("data", "clean", "costes_eventos.csv")
OUTPUT_EVENTOS = os.path.join("data", "clean", "datos_eventos.csv")
OUTPUT_PERSONA = os.path.join("data", "clean", "datos_persona.csv")
ACTUALIZAR_SCRIPT = os.path.join("src", "actualizar_datos.py")

# =========================
# 🚀 Configuración general
# =========================
st.set_page_config(page_title="SismIA - Gestión de Eventos", layout="wide")

# =========================
# 🔍 Carga de eventos y costes
# =========================
if os.path.exists(OUTPUT_EVENTOS):
    df_eventos = pd.read_csv(OUTPUT_EVENTOS)
    eventos_unicos = pd.DataFrame({"EVENTO": df_eventos["EVENTO"].unique()})
else:
    eventos_unicos = pd.DataFrame(columns=["EVENTO"])

if os.path.exists(COSTES_PATH):
    df_costes = pd.read_csv(COSTES_PATH)
else:
    df_costes = pd.DataFrame(columns=["EVENTO", "COSTE_ESTIMADO"])

# Unificamos y detectamos eventos sin coste
df_costes_full = eventos_unicos.merge(df_costes, on="EVENTO", how="left")
faltan_costes = df_costes_full["COSTE_ESTIMADO"].isna().sum()

# =========================
# 🧠 CABECERA
# =========================

# 📅 Configuración de idioma y fecha
try:
    locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')  # Linux/Mac
except:
    try:
        locale.setlocale(locale.LC_TIME, 'es_ES')  # Windows
    except:
        pass

fecha_actual = datetime.today().strftime('%A, %d de %B de %Y').capitalize()

# 🔤 Limpieza de tildes y texto final
fecha_limpia = unicodedata.normalize('NFKD', fecha_actual).encode('ASCII', 'ignore').decode('utf-8')
texto_fecha = f"Hoy es {fecha_limpia}"

# =========================
# 🎨 Cabecera visual con logo centrado, título y fecha
# =========================
# Cabecera visual con logo centrado, título y fecha
col1, col2, col3 = st.columns([1,2,1])
with col2:
    st.image("src/assets/logo_sismia.png", width=120)

# Título y fecha centrados
st.markdown(
    f"""
    <h1 style='text-align: center; color: #4B0082;'>💡 Bienvenida, Eva :)</h1>
    <h4 style='text-align: center; color: gray;'>{texto_fecha}</h4>
    """,
    unsafe_allow_html=True
)

# =========================
# 🔄 Actualización de datos
# =========================
if st.button("🔄 Actualizar datos automáticamente"):
    with st.spinner("Ejecutando actualización..."):
        result = subprocess.run(["python", ACTUALIZAR_SCRIPT], capture_output=True, text=True)
        if result.returncode == 0:
            st.success("✅ Datos actualizados correctamente.")
        else:
            st.error("❌ Error en la ejecución del script.")
            st.text(result.stderr)

# =========================
# 🔮 Simulador de eventos
# =========================
st.markdown("<h2 style='text-align: center;'>¿Qué te apetece hacer hoy?</h2>", unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    st.subheader("⏳ Próximo evento:") #falta añadir el countdown de fecha
    st.markdown("🎯 Evento: **--**") #titulo evento
    st.markdown("📆 Fecha: **--/--/----**")
    st.markdown("⏳ Faltan: **-- días**")
    st.markdown("👥 Inscritas: **--**")
    st.markdown("💸 Beneficio actual: **-- €**")
    st.markdown("💰 Llevamos: **-- € de beneficio**")
with col2:

    st.subheader("📢 Te recomiendo que el próximo evento sea:")
    st.markdown("🗓️ Fecha sugerida: **--/--/----**")
    st.markdown("📍 Comunidad: **--**")
    st.markdown("👥 Asistencia esperada: **--**")
    st.markdown("💰 Beneficio estimado: **-- €**")
