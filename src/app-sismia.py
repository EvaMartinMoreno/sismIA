import streamlit as st
import pandas as pd
import os
import subprocess
import locale
import unicodedata
from datetime import datetime

# =========================
# 📁 Rutas
# =========================
CRUDO_PATH = os.path.join("data", "clean", "eventos_crudos_unificados.csv")
OUTPUT_EVENTOS = os.path.join("data", "clean", "datos_eventos.csv")
OUTPUT_PERSONA = os.path.join("data", "clean", "datos_persona.csv")
ACTUALIZAR_SCRIPT = os.path.join("src", "pipeline_app.py")

# =========================
# 🚀 Configuración general
# =========================
st.set_page_config(page_title="SismIA - Gestión de Eventos", layout="wide")

# =========================
# 🧐 CABECERA
# =========================

try:
    locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')  # Linux/Mac
except:
    try:
        locale.setlocale(locale.LC_TIME, 'es_ES')  # Windows
    except:
        pass

fecha_actual = datetime.today().strftime('%A, %d de %B de %Y').capitalize()
fecha_limpia = unicodedata.normalize('NFKD', fecha_actual).encode('ASCII', 'ignore').decode('utf-8')
texto_fecha = f"Hoy es {fecha_limpia}"

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.image("src/assets/logo_sismia.png", width=120)

st.markdown(
    f"""
    <h1 style='text-align: center; color: #4B0082;'>💡 Bienvenida, Eva :)</h1>
    <h4 style='text-align: center; color: gray;'>{texto_fecha}</h4>
    """,
    unsafe_allow_html=True
)

# =========================
# 🔄 Botón de actualización
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
# 🧾 Introducción de costes
# =========================
st.markdown("---")
st.subheader("📋 Introducir coste unitario por evento (solo eventos sin coste o con coste 0)")

# Cargar datos crudos
if os.path.exists(CRUDO_PATH):
    df_eventos = pd.read_csv(CRUDO_PATH)
else:
    st.error("❌ No se encontró el archivo de datos crudos.")
    st.stop()

# Asegurar columna
if "COSTE_UNITARIO" not in df_eventos.columns:
    df_eventos["COSTE_UNITARIO"] = 0.0
else:
    df_eventos["COSTE_UNITARIO"] = pd.to_numeric(df_eventos["COSTE_UNITARIO"], errors="coerce").fillna(0.0)

df_costes_full = df_eventos.groupby("NOMBRE_EVENTO", as_index=False)["COSTE_UNITARIO"].mean()

eventos_pendientes = df_costes_full[
    (df_costes_full["COSTE_UNITARIO"].isna()) | (df_costes_full["COSTE_UNITARIO"] == 0)
].sort_values("NOMBRE_EVENTO")

if eventos_pendientes.empty:
    st.success("🎉 Todos los eventos tienen un coste por persona asignado.")
else:
    with st.form("formulario_costes_tabla"):
        nuevas_filas = []
        st.write("Introduce el coste unitario por evento:")

        for i, row in eventos_pendientes.iterrows():
            col1, col2 = st.columns([3, 2])
            with col1:
                st.text(row["NOMBRE_EVENTO"])
            with col2:
                nuevo_coste = st.number_input(
                    "", key=f"coste_{i}", min_value=0.0, format="%.2f"
                )
                nuevas_filas.append((row["NOMBRE_EVENTO"], nuevo_coste))

        submitted = st.form_submit_button("📏 Guardar todos los costes")

        if submitted:
            cambios = 0
            for nombre_evento, nuevo_coste in nuevas_filas:
                mask = (df_eventos["NOMBRE_EVENTO"] == nombre_evento) & (df_eventos["COSTE_UNITARIO"] != nuevo_coste)
                if mask.any():
                    df_eventos.loc[mask, "COSTE_UNITARIO"] = nuevo_coste
                    cambios += 1

            if cambios > 0:
                df_eventos.to_csv(CRUDO_PATH, index=False)
                st.success("✅ Costes unitarios actualizados correctamente.")
                st.rerun()
            else:
                st.info("ℹ️ No se realizaron cambios.")

# =========================
# 🧩 Simulador de eventos (placeholder)
# =========================
st.markdown("<h2 style='text-align: center;'>¿Qué te apetece hacer hoy?</h2>", unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    st.subheader("⏳ Próximo evento:")
    st.markdown("🌟 Evento: **--**")
    st.markdown("🗓️ Fecha: **--/--/----**")
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
