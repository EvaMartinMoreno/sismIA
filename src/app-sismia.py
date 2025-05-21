import streamlit as st
from datetime import datetime
from limpieza_eventos import cargar_y_procesar_eventos
from instadata import cargar_métricas_instagram
from limpieza_calendario import mostrar_calendario
import os
import locale
import pandas as pd

# === Tema personalizado ===
def aplicar_tema_personalizado():
    config_dir = os.path.join(os.path.expanduser("~"), ".streamlit")
    os.makedirs(config_dir, exist_ok=True)

    config_path = os.path.join(config_dir, "config.toml")
    tema = """
[theme]
base = "light"
primaryColor = "#a26ec6"
backgroundColor = "#fbffe0"
secondaryBackgroundColor = "#ffffff"
textColor = "#4b286d"
font = "sans serif"
""".strip()

    if not os.path.exists(config_path):
        with open(config_path, "w", encoding="utf-8") as f:
            f.write(tema)
        print("✅ Tema personalizado aplicado automáticamente.")
    else:
        print("ℹ️ Tema ya existente. No se ha sobrescrito.")

# Ejecutar al arrancar la app
aplicar_tema_personalizado()

# === Configuración de página ===
st.set_page_config(page_title="SismIA Dashboard", layout="wide")

# === Cargar CSS personalizado ===
style_path = os.path.join(os.path.dirname(__file__), "style.css")
with open(style_path) as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# === Cabecera ===
locale.setlocale(locale.LC_TIME, "es_ES.UTF-8")

st.markdown("""
    <div style='text-align: center;'>
        <img src='assets/logo_sismia.png' width='180' />
    </div>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

st.markdown(f"""
    <div style='text-align: center; margin-top: 10px;'>
        <h2 style='color: #a26ec6;'>¡Bienvenida, Eva!</h2>
        <p style='font-size: 18px; color: #4b286d;'>Hoy es {datetime.now().strftime('%A, %#d de %B de %Y')}</p>
    </div>
""", unsafe_allow_html=True)

# === Cargar datos ===
ruta_csv_eventos = os.path.join(os.path.dirname(__file__), "..", "data", "clean", "events_athletiks_limpio.csv")
ruta_csv_carreras = os.path.join(os.path.dirname(__file__), "..", "data", "processed", "carreras_unificadas.csv")

data_eventos = cargar_y_procesar_eventos(ruta_csv_eventos)
df_eventos = data_eventos["df"]

df_carreras = pd.read_csv(ruta_csv_carreras)

# === TABS ===
tabs = st.tabs(["🏃 Calendario carreras", "🗓️ Próximo evento", "⭐ Cuentas fieles", "📢 Recomendador de post", "📊 Análisis externos"])

# === COLUMNAS métricas ===
col1, main, col2 = st.columns([1.5, 4, 1.5], gap="large")

with col1:
    st.subheader("Próximo evento")
    if data_eventos["proximo_evento"]:
        st.markdown(f"**{data_eventos['proximo_evento']}**")
        st.markdown(f"👥 {data_eventos['apuntadas']} apuntadas")
        st.markdown(f"💰 {data_eventos['recaudado']:.2f} € recaudados")
        st.markdown(f"🗓️ Faltan {data_eventos['dias_restantes']} días")
    else:
        st.markdown("No hay próximos eventos.")

    st.subheader("Cuentas más fieles")
    for (_, nombre), asistencias in data_eventos["top_fieles"].items():
        st.markdown(f"✅ {nombre} ({asistencias} asistencias)")

    st.subheader("Cuentas menos fieles")
    for (_, nombre), asistencias in data_eventos["top_inactivas"].items():
        st.markdown(f"😴 {nombre} ({asistencias} asistencia{'s' if asistencias != 1 else ''})")

with tabs[0]:
    with main:
        st.subheader("Calendario carreras")
        mostrar_calendario(df_carreras)

with tabs[1]:
    with main:
        st.subheader("Próximo evento")
        st.markdown("(detalle del próximo evento con mapa y stats)")

with tabs[2]:
    with main:
        st.subheader("Cuentas fieles")
        st.markdown("(ranking de cuentas por participación y fidelidad)")

with tabs[3]:
    with main:
        st.subheader("Recomendador de post")
        st.markdown("(ideas de contenido a publicar según tendencias)")

with tabs[4]:
    with main:
        st.subheader("Análisis externos")
        st.markdown("(comparativa con otras cuentas y hashtags)")

with col2:
    insta = cargar_métricas_instagram()
    st.subheader("Instagram")
    st.metric("Seguidores", insta["seguidores"])
    st.metric("Nuevos esta semana", insta["nuevos"])

    st.subheader("Tendencias de la semana")
    st.markdown("**Búsquedas**: #trailrunning, #fuerzafemenina")
    st.markdown("**Posts destacados**: @run_chicas, @mujeresenmovimiento")
