import streamlit as st
from datetime import datetime
from limpieza_eventos import cargar_y_procesar_eventos
from instadata import cargar_métricas_instagram
import os

# Configuración de página
st.set_page_config(page_title="SismIA Dashboard", layout="wide")

with open("style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

#carga de datos 
ruta_csv = os.path.join(os.path.dirname(__file__), "..", "data", "clean", "events_athletiks_limpio.csv")
data = cargar_y_procesar_eventos(ruta_csv)

df = data["df"]
proximo_evento = data["proximo_evento"]
apuntadas = data["apuntadas"]
recaudado = data["recaudado"]
dias_restantes = data["dias_restantes"]
top_fieles = data["top_fieles"]
top_inactivas = data["top_inactivas"]

# --- HEADER ---
st.markdown(f"""
    <div style='text-align: center; font-size: 36px; font-weight: bold;'>
        Hola Eva :)<br>
        <span style='font-size: 20px;'>Hoy es {datetime.now().strftime('%A, %d de %B de %Y')}</span>
    </div>
""", unsafe_allow_html=True)

# --- TABS ---
tabs = st.tabs(["🏃 Calendario carreras", "🗓️ Próximo evento", "⭐ Cuentas fieles", "📢 Recomendador de post", "📊 Análisis externos"])

# --- COLUMNAS ---
col1, main, col2 = st.columns([1.5, 4, 1.5], gap="large")

with col1:
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
    insta = cargar_métricas_instagram()

    st.subheader("Instagram")
    st.metric("Seguidores", insta["seguidores"])
    st.metric("Nuevos esta semana", insta["nuevos"])

    st.subheader("Tendencias de la semana")
    st.markdown("**Búsquedas**: #trailrunning, #fuerzafemenina")
    st.markdown("**Posts destacados**: @run_chicas, @mujeresenmovimiento")
