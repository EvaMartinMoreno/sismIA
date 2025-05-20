import streamlit as st
from datetime import datetime
from limpieza_eventos import cargar_y_procesar_eventos
from instadata import cargar_métricas_instagram
import os
import locale
import time

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

# === Splash animado con logo ===
logo_path = os.path.join(os.path.dirname(__file__), "assets", "logo_sismia.png")

# Mostrar logo como splash
with st.container():
    st.image(logo_path, width=220)
    st.markdown("""
        <style>
            [data-testid="stImage"] img {
                animation: fadeOut 2s ease-in-out forwards;
                animation-delay: 1.8s;
            }

            @keyframes fadeOut {
                0% { opacity: 1; }
                100% { opacity: 0; height: 0; display: none; }
            }
        </style>
    """, unsafe_allow_html=True)
    time.sleep(2.2)

# Mensaje de bienvenida tras splash
locale.setlocale(locale.LC_TIME, "es_ES.UTF-8")
st.markdown(f"""
    <div style='text-align: center; margin-top: -50px;' class='fade-in'>
        <h2 style='color: #a26ec6;'>¡Bienvenida, Eva!</h2>
        <p style='font-size: 18px; color: #4b286d;'>Hoy es {datetime.now().strftime('%A, %#d de %B de %Y')}</p>
    </div>
""", unsafe_allow_html=True)

# === Cargar datos desde CSV ===
ruta_csv = os.path.join(os.path.dirname(__file__), "..", "data", "clean", "events_athletiks_limpio.csv")
data = cargar_y_procesar_eventos(ruta_csv)

df = data["df"]
proximo_evento = data["proximo_evento"]
apuntadas = data["apuntadas"]
recaudado = data["recaudado"]
dias_restantes = data["dias_restantes"]
top_fieles = data["top_fieles"]
top_inactivas = data["top_inactivas"]

# === TABS principales ===
tabs = st.tabs(["🏃 Calendario carreras", "🗓️ Próximo evento", "⭐ Cuentas fieles", "📢 Recomendador de post", "📊 Análisis externos"])

# === COLUMNAS métricas ===
col1, main, col2 = st.columns([1.5, 4, 1.5], gap="large")

with col1:
    with st.container():
        st.subheader("Próximo evento")
        if proximo_evento:
            st.markdown(f"**{proximo_evento}**")
            st.markdown(f"👥 {apuntadas} apuntadas")
            st.markdown(f"💰 {recaudado:.2f} € recaudados")
            st.markdown(f"🗓️ Faltan {dias_restantes} días")
        else:
            st.markdown("No hay próximos eventos.")

        st.subheader("Cuentas más fieles")
        for (_, nombre), asistencias in top_fieles.items():
            st.markdown(f"✅ {nombre} ({asistencias} asistencias)")

        st.subheader("Cuentas menos fieles")
        for (_, nombre), asistencias in top_inactivas.items():
            st.markdown(f"😴 {nombre} ({asistencias} asistencia{'s' if asistencias != 1 else ''})")

with tabs[0]:
    with main:
        st.subheader("Calendario carreras")
        st.markdown("(aquí va el calendario interactivo)")

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
    with st.container():
        insta = cargar_métricas_instagram()

        st.subheader("Instagram")
        st.metric("Seguidores", insta["seguidores"])
        st.metric("Nuevos esta semana", insta["nuevos"])

        st.subheader("Tendencias de la semana")
        st.markdown("**Búsquedas**: #trailrunning, #fuerzafemenina")
        st.markdown("**Posts destacados**: @run_chicas, @mujeresenmovimiento")
