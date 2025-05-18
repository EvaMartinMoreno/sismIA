import streamlit as st
import pandas as pd
from datetime import datetime

# Configuración de página
st.set_page_config(page_title="SismIA Dashboard", layout="wide")

# --- Header ---
st.markdown("""
    <div style='text-align: center; font-size: 36px; font-weight: bold;'>
        Hola Eva :)<br>
        <span style='font-size: 20px;'>Hoy es {}</span>
    </div>
""".format(datetime.now().strftime("%A, %d de %B de %Y")), unsafe_allow_html=True)

# --- Tabs estilo menú horizontal ---
tabs = st.tabs(["🏃 Calendario carreras", "📅 Próximo evento", "⭐ Cuentas fieles", "📢 Recomendador de post", "📊 Análisis externos"])

# --- Columna Izquierda y Derecha: se muestran en todas las pestañas ---
col1, main, col2 = st.columns([1.5, 4, 1.5], gap="large")

# --- Columna Izquierda ---
with col1:
    st.subheader("Próximo evento")
    st.markdown("**Running Sisterhood**")
    st.markdown("👥 58 apuntadas")
    st.markdown("💰 145€ recaudados")
    st.markdown("📅 Faltan 12 días")

    st.subheader("Cuentas más fieles")
    st.markdown("1. @laura_runner")
    st.markdown("2. @cris.fit")
    st.markdown("3. @marta.trail")

    st.subheader("Cuentas menos fieles")
    st.markdown("1. @cami.runner")
    st.markdown("2. @ines_slow")
    st.markdown("3. @lucia.never")

# --- Contenido central según la pestaña seleccionada ---
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

# --- Columna Derecha ---
with col2:
    st.subheader("Instagram")
    st.metric("Seguidores", "1.245")
    st.metric("Nuevos esta semana", "+54")

    st.subheader("Tendencias de la semana")
    st.markdown("**Búsquedas**: #trailrunning, #fuerzafemenina")
    st.markdown("**Posts destacados**: @run_chicas, @mujeresenmovimiento")
