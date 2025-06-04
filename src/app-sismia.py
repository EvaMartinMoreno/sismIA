import streamlit as st
import pandas as pd
import os
import subprocess
import locale
import unicodedata
import joblib
from datetime import datetime
from pathlib import Path

# =========================
# 📁 Rutas
# =========================
CRUDO_PATH = os.path.join("data", "clean", "eventos_crudos_unificados.csv")
ACTUALIZAR_SCRIPT = os.path.join("src", "pipeline_app.py")
SIMULACION_BENEFICIO_PATH = os.path.join("stats", "datasets", "Girona_prediccion_beneficio_eventos_futuros.csv")

# =========================
# 🚀 Configuración general
# =========================
st.set_page_config(page_title="SismIA - Gestión de Eventos", layout="wide")

# =========================
# 🤔 CABECERA
# =========================
try:
    locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
except:
    try:
        locale.setlocale(locale.LC_TIME, 'es_ES')
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
# 📜 Introducción de costes
# =========================
st.markdown("---")
st.subheader("📋 Introduce coste unitario por evento")

if os.path.exists(CRUDO_PATH):
    df_eventos = pd.read_csv(CRUDO_PATH)
else:
    st.error("❌ No se encontró el archivo de datos crudos.")
    st.stop()

if "COSTE_UNITARIO" not in df_eventos.columns:
    df_eventos["COSTE_UNITARIO"] = 0.0
else:
    df_eventos["COSTE_UNITARIO"] = pd.to_numeric(df_eventos["COSTE_UNITARIO"], errors="coerce").fillna(0.0)

df_costes_full = df_eventos.groupby("NOMBRE_EVENTO", as_index=False)["COSTE_UNITARIO"].mean()

eventos_pendientes = df_costes_full[
    df_costes_full["COSTE_UNITARIO"].isna()].sort_values("NOMBRE_EVENTO")

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
                nuevo_coste = st.number_input("", key=f"coste_{i}", min_value=0.0, format="%.2f")
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
# 🧩 Simulador de eventos y recomendador
# =========================
st.markdown("<h2 style='text-align: center;'>¿Qué te apetece hacer hoy?</h2>", unsafe_allow_html=True)

col1, col2 = st.columns(2)

# === 📅 Cargar datos y modelos
if not os.path.exists(SIMULACION_BENEFICIO_PATH):
    st.error(f"❌ No se encontró el archivo: {SIMULACION_BENEFICIO_PATH}")
    st.stop()

modelo_asist = joblib.load("src/models/modelo_lineal_unificado_girona.pkl")
modelo_benef = joblib.load("src/models/modelo_beneficio_girona.pkl")
df_sim = pd.read_csv(SIMULACION_BENEFICIO_PATH, parse_dates=["FECHA_EVENTO"])
df_real = pd.read_csv("data/clean/dataset_modelo.csv", parse_dates=["FECHA_EVENTO"])
df_real = df_real[df_real["TIPO_EVENTO"] == "pago"]

# === 🛠️ Filtrar eventos futuros
hoy = pd.Timestamp.now().normalize()
df_futuro = df_sim[df_sim["FECHA_EVENTO"] > hoy].copy()
df_real_futuro = df_real[df_real["FECHA_EVENTO"] >= hoy]

# === 🤖 Aplicar predicciones
if not df_futuro.empty:
    def safe_predict():
        df_feat = df_futuro.copy()

        X_asist = pd.get_dummies(
            df_feat[["MES", "DIA_SEMANA_NUM", "DIA_MES", "SEMANA_MES", "TEMPORADA",
                     "COSTE_UNITARIO", "PRECIO_MEDIO", "COLABORACION", "TIPO_ACTIVIDAD"]],
            columns=["TEMPORADA", "TIPO_ACTIVIDAD"],
            drop_first=True
        ).reindex(columns=modelo_asist.feature_names_in_, fill_value=0)
        df_futuro["ASISTENCIA_PREVISTA"] = modelo_asist.predict(X_asist)

        X_benef = pd.get_dummies(
            df_feat[["MES", "DIA_SEMANA_NUM", "DIA_MES", "SEMANA_MES", "TEMPORADA",
                     "COSTE_UNITARIO", "PRECIO_MEDIO", "COLABORACION", "TIPO_ACTIVIDAD"]],
            columns=["TEMPORADA", "TIPO_ACTIVIDAD"],
            drop_first=True
        ).reindex(columns=modelo_benef.feature_names_in_, fill_value=0)
        df_futuro["BENEFICIO_PREDICHO"] = modelo_benef.predict(X_benef)

    if "ASISTENCIA_PREVISTA" not in df_futuro.columns or "BENEFICIO_PREDICHO" not in df_futuro.columns:
        safe_predict()

# === 📢 Mostrar mejor evento simulado
with col2:
    if df_futuro.empty:
        st.warning("No hay eventos futuros simulados aún.")
    else:
        mejor_evento = df_futuro.loc[df_futuro["BENEFICIO_PREDICHO"].idxmax()]
        fecha_sugerida = mejor_evento["FECHA_EVENTO"].strftime("%d/%m/%Y")
        comunidad = mejor_evento["COMUNIDAD"]
        asistencia = round(mejor_evento["ASISTENCIA_PREVISTA"])
        beneficio = round(mejor_evento["BENEFICIO_PREDICHO"], 2)

        st.subheader("📢 Te recomiendo que el próximo evento sea:")
        st.markdown(f"🗓️ Fecha sugerida: **{fecha_sugerida}**")
        st.markdown(f"📍 Comunidad: **{comunidad}**")
        st.markdown(f"👥 Asistencia esperada: **{asistencia}** personas")
        st.markdown(f"💰 Beneficio estimado: **{beneficio:.2f} €**")

# === 📢 Mostrar próximo evento real
with col1:
    if df_real_futuro.empty:
        st.warning("No hay eventos reales programados próximamente.")
    else:
        proximo_evento = df_real_futuro.sort_values("FECHA_EVENTO").iloc[0]
        fecha_real = proximo_evento["FECHA_EVENTO"].strftime("%d/%m/%Y")
        comunidad_real = proximo_evento["COMUNIDAD"]
        asistencia_real = int(proximo_evento["NUM_ASISTENCIAS"])
        beneficio_real = round(proximo_evento["BENEFICIO_ESTIMADO"], 2)

        st.subheader("📢 Próximo evento a la vista")
        st.markdown(f"🗓️ Fecha: **{fecha_real}**")
        st.markdown(f"📍 Comunidad: **{comunidad_real}**")
        st.markdown(f"👥 Inscritas: **{asistencia_real}** personas")
        st.markdown(f"💰 Beneficio actual: **{beneficio_real} €**")
