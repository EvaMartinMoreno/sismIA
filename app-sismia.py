# =========================
# 📦 Librerías
# =========================
import importlib
import sys
import src.pipeline_app as pipe
import streamlit as st
import pandas as pd
import os
import subprocess
import locale
import unicodedata
from datetime import datetime, timedelta
from pathlib import Path
from src.scraping.scraper_athletiks import scrappear_eventos
from dotenv import load_dotenv
load_dotenv()

# =========================
# 📁 Rutas
# =========================
ACTUALIZAR_SCRIPT = Path("src/pipeline_app.py")
RESULTADOS_PATH = Path ("data/predicciones/simulaciones_futuras.csv")
REAL_PATH = Path("data/raw/dataset_modelo.csv")
USUARIO_GIRONA = os.getenv("USUARIO_GIRONA")
PASSWORD_GIRONA = os.getenv("PASSWORD_GIRONA")
USUARIO_ELCHE = os.getenv("USUARIO_ELCHE")
PASSWORD_ELCHE = os.getenv("PASSWORD_ELCHE")

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
    """,
    unsafe_allow_html=True
)

# =========================
# 🔄 Actualización de datos
# =========================
if st.button("🔁 Actualizar datos"):
    try:
        with st.spinner("Actualizando datos…"):
            importlib.reload(pipe)   
            pipe.main()            

        st.success("Datos actualizados✅")
    except Exception as e:
        st.error("⚠️ El pipeline falló.")
        st.exception(e)

# =========================
# ✍️ Edición completa del evento
# =========================
if REAL_PATH.exists():
    df_eventos = pd.read_csv(REAL_PATH)

    # Inicializar columnas si faltan
    for col in ["COSTE_UNITARIO", "COSTE_UNITARIO_VALIDADO", "COLABORACION", "TIPO_ACTIVIDAD", "INSTAGRAM_SHORTCODE"]:
        if col not in df_eventos.columns:
            if col == "COSTE_UNITARIO":
                df_eventos[col] = np.nan
            elif col == "COSTE_UNITARIO_VALIDADO":
                df_eventos[col] = False
            elif col == "COLABORACION":
                df_eventos[col] = 0
            elif col == "TIPO_ACTIVIDAD":
                df_eventos[col] = "otro"

    # Agrupar eventos únicos
    df_formulario = df_eventos.groupby("NOMBRE_EVENTO", as_index=False).agg({
        "COSTE_UNITARIO": "first",
        "COSTE_UNITARIO_VALIDADO": "first",
        "COLABORACION": "first",
        "TIPO_ACTIVIDAD": "first",
    })

    pendientes = df_formulario[df_formulario["COSTE_UNITARIO_VALIDADO"] == False].copy()

    if pendientes.empty:
        st.success("🎉 Todos los eventos están validados.")
    else:
        with st.form("form_edicion_eventos"):
            nuevas_filas = []
            st.write("Introduce los datos y valida cada evento:")
            for i, row in pendientes.iterrows():
                st.markdown(f"#### 📌 {row['NOMBRE_EVENTO']}")
                col1, col2, col3 = st.columns([2, 2, 2])
                col4, col5 = st.columns([3, 1])

                coste = col1.number_input(
                    "Coste unitario (€)", 
                    key=f"coste_{i}", 
                    value=0.0 if pd.isna(row["COSTE_UNITARIO"]) else float(row["COSTE_UNITARIO"]),
                    min_value=0.0,
                    format="%.2f"
                )

                colaboracion = col2.checkbox("¿Colaboración?", value=bool(row["COLABORACION"]), key=f"colab_{i}")

                tipo_default = row["TIPO_ACTIVIDAD"] if row["TIPO_ACTIVIDAD"] in ["ludico", "only run", "desayuno", "deportivo", "charla"] else "ludico"
                tipo = col3.selectbox(
                    "Tipo de actividad", 
                    options=["ludico", "only run", "desayuno", "deportivo", "charla"], 
                    index=["ludico", "only run", "desayuno", "deportivo", "charla"].index(tipo_default),
                    key=f"tipo_{i}"
                )

                validar = col5.checkbox("✅ Validar", key=f"validar_{i}")

                nuevas_filas.append((row["NOMBRE_EVENTO"], coste, colaboracion, tipo, validar))
                st.markdown("---")

            if st.form_submit_button("💾 Guardar cambios"):
                cambios = 0
                for nombre, coste, colab, tipo, validado in nuevas_filas:
                    mask = df_eventos["NOMBRE_EVENTO"] == nombre
                    df_eventos.loc[mask, "COSTE_UNITARIO"] = coste
                    df_eventos.loc[mask, "COLABORACION"] = int(colab)
                    df_eventos.loc[mask, "TIPO_ACTIVIDAD"] = tipo
                    df_eventos.loc[mask, "COSTE_UNITARIO_VALIDADO"] = validado
                    cambios += 1

                if cambios > 0:
                    df_eventos.to_csv(REAL_PATH, index=False)
                    df_eventos.to_csv("data/clean/dataset_modelo.csv", index=False)
                    st.success(" Cambios guardados correctamente.")
                    st.rerun()
                else:
                    st.info("No se realizaron cambios.")
else:
    st.error("No se encuentra el archivo de eventos.")

# =========================
# 📊 Próximos eventos
# =========================
st.markdown("---")
st.markdown("<h2 id='proximos-eventos'>📅 Próximos eventos</h2>", unsafe_allow_html=True)

col1, col2 = st.columns(2)

# === 📍 Evento real
with col1:
    if REAL_PATH.exists():
        df_real = pd.read_csv(REAL_PATH, parse_dates=["FECHA_EVENTO"])

        # Filtra solo eventos de tipo pago
        df_real = df_real[df_real["TIPO_EVENTO"] == "pago"]

        # Divide en futuros y pasados
        df_futuros = df_real[df_real["FECHA_EVENTO"] >= pd.Timestamp.now()]
        df_pasados = df_real[df_real["FECHA_EVENTO"] < pd.Timestamp.now()]

        if not df_futuros.empty:
            evento = df_futuros.sort_values("FECHA_EVENTO").iloc[0]
            st.subheader("📢 Próximo evento")
        elif not df_pasados.empty:
            evento = df_pasados.sort_values("FECHA_EVENTO", ascending=False).iloc[0]
            st.subheader("📢 Último evento realizado")
        else:
            evento = None
            st.info("No hay eventos reales registrados.")

        if evento is not None:
            fecha_real = evento["FECHA_EVENTO"].strftime("%d/%m/%Y")
            comunidad_real = evento["COMUNIDAD"]

            asistencia_real = (
                int(evento["NUM_ASISTENCIAS"])
                if "NUM_ASISTENCIAS" in evento and pd.notna(evento["NUM_ASISTENCIAS"])
                else "N/A"
            )

            beneficio_real = (
                round(evento["BENEFICIO_ESTIMADO"], 2)
                if "BENEFICIO_ESTIMADO" in evento and pd.notna(evento["BENEFICIO_ESTIMADO"])
                else "N/A"
            )

            st.markdown(f"🗓️ Fecha: **{fecha_real}**")
            st.markdown(f"📍 Comunidad: **{comunidad_real}**")
            st.markdown(f"👥 Inscritas: **{asistencia_real}** personas")
            st.markdown(f"💰 Beneficio: **{beneficio_real} €**")
            # Mostrar imagen de Instagram si existe SHORTCODE
            if "INSTAGRAM_SHORTCODE" in evento and pd.notna(evento["INSTAGRAM_SHORTCODE"]):
                shortcode = evento["INSTAGRAM_SHORTCODE"]
                insta_url = f"https://www.instagram.com/p/{shortcode}/media/?size=l"
                st.image(insta_url, caption="📸 Imagen del evento en Instagram", use_column_width=True)
                st.markdown(f"[Ver post en Instagram](https://www.instagram.com/p/{shortcode}/)")

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
            tipo_actividad_sim = proximo_sim["TIPO_ACTIVIDAD"]

            asistencia_sim = (
                int(proximo_sim["ASISTENCIAS_PREDICHAS"])
                if "ASISTENCIAS_PREDICHAS" in proximo_sim and pd.notna(proximo_sim["ASISTENCIAS_PREDICHAS"])
                else "N/A"
            )

            beneficio_sim = (
            round(proximo_sim["BENEFICIO_ESTIMADO"], 2)
                if "BENEFICIO_ESTIMADO" in proximo_sim and pd.notna(proximo_sim["BENEFICIO_ESTIMADO"])
                else "N/A"
                )


            st.markdown(f"🗓️ Te recomiendo la fecha: **{fecha_sim}**")
            st.markdown(f"📍 Comunidad: **GIRONA**")
            st.markdown(f"👥 Asistencia esperada: **{asistencia_sim}** personas")
            st.markdown(f"💰 Beneficio estimado: **{beneficio_sim} €**")
            st.markdown(f"Tipo de actividad: **{proximo_sim['TIPO_ACTIVIDAD']}**")
        else:
            st.info("No hay eventos futuros simulados.")
    else:
        st.warning("Falta el archivo de simulación.")
