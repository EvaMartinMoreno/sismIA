# =========================
# 📦 Librerías
# =========================
import streamlit as st
import pandas as pd
import os
import subprocess
import locale
import sys
import unicodedata
from datetime import datetime, timedelta
from pathlib import Path
from src.scaraping.scraper_athletiks import scrappear_eventos

# =========================
# 📁 Rutas
# =========================
CRUDO_PATH = Path("data/clean/eventos_crudos_unificados.csv")
ACTUALIZAR_SCRIPT = Path("src/pipeline_app.py")
RESULTADOS_PATH = Path("stats/datasets/Girona_prediccion_beneficio_eventos_futuros.csv")
REAL_PATH = Path("data/clean/dataset_modelo.csv")

# =========================
# 🚀 Configuración general
# =========================
st.set_page_config(page_title="SismIA - Gestión de Eventos", layout="wide")

try:
    locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
except:
    try:
        locale.setlocale(locale.LC_TIME, 'es_ES')
    except:
        pass

fecha_actual = datetime.today().strftime('%A, %d de %B de %Y').capitalize()
fecha_limpia = unicodedata.normalize('NFKD', fecha_actual).encode('ASCII', 'ignore').decode('utf-8')
st.markdown(
    f"""
    <h1 style='text-align: center; color: #4B0082;'>💡 Bienvenida, Eva :)</h1>
    <h4 style='text-align: center; color: gray;'>Hoy es {fecha_limpia}</h4>
    """,
    unsafe_allow_html=True
)

# =========================
# 🔝 Menú superior
# =========================
st.markdown(
    """
    <style>
        .menu-container {
            display: flex;
            gap: 2rem;
            justify-content: center;
            margin-bottom: 2rem;
        }
        .menu-button {
            padding: 0.5rem 1rem;
            background-color: #E6E6FA;
            border-radius: 10px;
            text-align: center;
            cursor: pointer;
            font-weight: bold;
            color: #4B0082;
            text-decoration: none;
        }
    </style>
    <div class="menu-container">
        <a href="#actualizacion" class="menu-button">🔄 Actualizar datos</a>
        <a href="#costes" class="menu-button">💸 Costes por evento</a>
        <a href="#proximos-eventos" class="menu-button">📅 Próximos eventos</a>
    </div>
    """,
    unsafe_allow_html=True
)

# =========================
# 🔄 Actualización de datos
# =========================
st.markdown("<h2 id='actualizacion'>🔄 Actualización de datos</h2>", unsafe_allow_html=True)

if st.button("🔁"):
    with st.spinner("Ejecutando actualización..."):
       #result = subprocess.run([sys.executable, ACTUALIZAR_SCRIPT], capture_output=True, text=True)
       result = scrappear_eventos(
        usuario=USUARIO_GIRONA,
        password=PASSWORD_GIRONA,
        comunidad="GIRONA",
        estado_scraping=estado,
        status="dev"
        )
       st.write("funciono!")
        if result.returncode == 0:
            st.success("Datos actualizados correctamente.")
        else:
            st.error("Error al ejecutar el pipeline.")

        st.markdown("### Log de ejecución")
        st.code(result.stdout + "\n" + result.stderr, language="bash")

# =========================
# 💸 Costes unitarios
# =========================
st.markdown("---")
st.subheader("📋 Introducción manual de costes unitarios")

if CRUDO_PATH.exists():
    df_eventos = pd.read_csv(CRUDO_PATH)

    # Inicializa columnas si no existen
    if "COSTE_UNITARIO" not in df_eventos.columns:
        df_eventos["COSTE_UNITARIO"] = np.nan
    if "COSTE_UNITARIO_VALIDADO" not in df_eventos.columns:
        df_eventos["COSTE_UNITARIO_VALIDADO"] = False

    # Agrupar y buscar los eventos que aún no han sido validados
    df_costes = df_eventos.groupby(["NOMBRE_EVENTO"], as_index=False).agg({
        "COSTE_UNITARIO": "first",
        "COSTE_UNITARIO_VALIDADO": "first"
    })

    pendientes = df_costes[df_costes["COSTE_UNITARIO_VALIDADO"] == False].copy()

    if pendientes.empty:
        st.success("🎉 Todos los eventos tienen un coste unitario asignado y validado.")
    else:
        with st.form("form_costes"):
            nuevas_filas = []
            st.write("Introduce el coste unitario por evento y marca como validado:")
            for i, row in pendientes.iterrows():
                col1, col2, col3 = st.columns([3, 2, 2])
                col1.text(row["NOMBRE_EVENTO"])
                coste_input = col2.number_input(
                    "Coste €", 
                    key=f"coste_{i}", 
                    min_value=0.0, 
                    value=0.0 if pd.isna(row["COSTE_UNITARIO"]) else float(row["COSTE_UNITARIO"]), 
                    format="%.2f"
                )
                validado = col3.checkbox("✅ Validar", key=f"validado_{i}")
                nuevas_filas.append((row["NOMBRE_EVENTO"], coste_input, validado))

            if st.form_submit_button("📏 Guardar costes"):
                cambios = 0
                for nombre_evento, nuevo_coste, validado in nuevas_filas:
                    mask = (df_eventos["NOMBRE_EVENTO"] == nombre_evento)
                    df_eventos.loc[mask, "COSTE_UNITARIO"] = nuevo_coste
                    df_eventos.loc[mask, "COSTE_UNITARIO_VALIDADO"] = validado
                    cambios += 1
                if cambios > 0:
                    df_eventos.to_csv(CRUDO_PATH, index=False)
                    st.success("Costes actualizados y validados.")
                    st.rerun()
                else:
                    st.info("No se realizaron cambios.")
else:
    st.error(" No se encontró el archivo de eventos.")

# =========================
# 📊 Próximos eventos
# =========================
st.markdown("---")
st.markdown("<h2 id='proximos-eventos'>📅 Próximos eventos</h2>", unsafe_allow_html=True)

col1, col2 = st.columns(2)

# === 📍 Evento real
with col1:
    st.subheader("📢 Próximo evento")
    if REAL_PATH.exists():
        df_real = pd.read_csv(REAL_PATH, parse_dates=["FECHA_EVENTO"])
        df_real = df_real[
            (df_real["TIPO_EVENTO"] == "pago") & (df_real["FECHA_EVENTO"] >= pd.Timestamp.now())
        ]
        if not df_real.empty:
            proximo_real = df_real.sort_values("FECHA_EVENTO").iloc[0]
            fecha_real = proximo_real["FECHA_EVENTO"].strftime("%d/%m/%Y")
            comunidad_real = proximo_real["COMUNIDAD"]

            asistencia_real = (
                int(proximo_real["NUM_ASISTENCIAS"])
                if "NUM_ASISTENCIAS" in proximo_real and pd.notna(proximo_real["NUM_ASISTENCIAS"])
                else "N/A"
            )

            beneficio_real = (
                round(proximo_real["BENEFICIO_ESTIMADO"], 2)
                if "BENEFICIO_ESTIMADO" in proximo_real and pd.notna(proximo_real["BENEFICIO_ESTIMADO"])
                else "N/A"
            )

            st.markdown(f"🗓️ Fecha: **{fecha_real}**")
            st.markdown(f"📍 Comunidad: **{comunidad_real}**")
            st.markdown(f"👥 Inscritas: **{asistencia_real}** personas")
            st.markdown(f"💰 Beneficio actual: **{beneficio_real} €**")
        else:
            st.info("No hay eventos reales programados.")
    else:
        st.warning("Falta el archivo de datos reales.")

# === 📍 Evento simulado
with col2:
    st.subheader("📢 Simulación del próximo evento")
    if RESULTADOS_PATH.exists():
        df_sim = pd.read_csv(RESULTADOS_PATH, parse_dates=["FECHA_EVENTO"])
        df_sim = df_sim[df_sim["FECHA_EVENTO"] > pd.Timestamp.now()]
        if not df_sim.empty:
            proximo_sim = df_sim.sort_values("FECHA_EVENTO").iloc[0]
            fecha_sim = proximo_sim["FECHA_EVENTO"].strftime("%d/%m/%Y")
            comunidad_sim = proximo_sim["COMUNIDAD"]

            asistencia_sim = (
                int(proximo_sim["ASISTENCIA_PREVISTA"])
                if "ASISTENCIA_PREVISTA" in proximo_sim and pd.notna(proximo_sim["ASISTENCIA_PREVISTA"])
                else "N/A"
            )

            beneficio_sim = (
                round(proximo_sim["BENEFICIO_PREDICHO"], 2)
                if "BENEFICIO_PREDICHO" in proximo_sim and pd.notna(proximo_sim["BENEFICIO_PREDICHO"])
                else "N/A"
            )

            st.markdown(f"🗓️ Te recomiendo la fecha: **{fecha_sim}**")
            st.markdown(f"📍 Comunidad: **{comunidad_sim}**")
            st.markdown(f"👥 Asistencia esperada: **{asistencia_sim}** personas")
            st.markdown(f"💰 Beneficio estimado: **{beneficio_sim} €**")
        else:
            st.info("No hay eventos futuros simulados.")
    else:
        st.warning("Falta el archivo de simulación.")
