import streamlit as st
import pandas as pd
from datetime import datetime
from unidecode import unidecode

# Configuración de página
st.set_page_config(page_title="SismIA Dashboard", layout="wide")

# --- FUNCIONES AUXILIARES ---
def detectar_ubicacion(evento):
    evento = unidecode(str(evento).lower())
    catalan = ['gener', 'febrer', 'març', 'abril', 'maig', 'juny', 'juliol', 'agost', 'setembre', 'octubre', 'novembre', 'desembre', 'dimecres']
    return 'Girona' if any(palabra in evento for palabra in catalan) else 'Elche'

def obtener_datos_proximo_evento(df):
    hoy = pd.Timestamp.today().normalize()
    df["fecha_evento"] = pd.to_datetime(df["fecha_evento"], errors="coerce")
    df_futuros = df[df["fecha_evento"] >= hoy].sort_values("fecha_evento")
    if not df_futuros.empty:
        proximo = df_futuros.iloc[0]["evento"]
        fecha = df_futuros.iloc[0]["fecha_evento"]
        apuntadas = df_futuros[df_futuros["evento"] == proximo].shape[0]
        recaudado = df_futuros[df_futuros["evento"] == proximo]["price_paid"].sum()
        dias_restantes = (fecha - hoy).days
        return proximo, apuntadas, recaudado, dias_restantes
    return None, 0, 0.0, None

def obtener_top_usuarios(df):
    df["asistencias"] = df.groupby("user_id")["user_id"].transform("count")
    top_fieles = df.groupby("user_id")["asistencias"].max().sort_values(ascending=False).head(3)
    top_inactivas = df.groupby("user_id")["asistencias"].max().sort_values().head(3)
    return top_fieles.index.tolist(), top_inactivas.index.tolist()

# --- CARGA Y PROCESAMIENTO DE DATOS ---
df = pd.read_csv("data/clean/events_athletiks_limpio.csv")
df["ubicacion"] = df["evento"].apply(detectar_ubicacion)
proximo_evento, apuntadas, recaudado, dias_restantes = obtener_datos_proximo_evento(df)
top_fieles, top_inactivas = obtener_top_usuarios(df)

# --- HEADER ---
st.markdown(f"""
    <div style='text-align: center; font-size: 36px; font-weight: bold;'>
        Hola Eva :)<br>
        <span style='font-size: 20px;'>Hoy es {datetime.now().strftime('%A, %d de %B de %Y')}</span>
    </div>
""", unsafe_allow_html=True)

# --- TABS ---
tabs = st.tabs(["🏃 Calendario carreras", "📅 Próximo evento", "⭐ Cuentas fieles", "📢 Recomendador de post", "📊 Análisis externos"])

# --- COLUMNAS ---
col1, main, col2 = st.columns([1.5, 4, 1.5], gap="large")

with col1:
    st.subheader("Próximo evento")
    st.markdown(f"**{proximo_evento}**")
    st.markdown(f"👥 {apuntadas} apuntadas")
    st.markdown(f"💰 {recaudado:.2f}€ recaudados")
    st.markdown(f"📅 Faltan {dias_restantes} días")

    # Cuentas más fieles
    top_fieles = df.groupby("user_id").size().sort_values(ascending=False).head(3).index
    top_nombres_fieles = df[df["user_id"].isin(top_fieles)].drop_duplicates("user_id").set_index("user_id").loc[top_fieles]["nombre_completo"]

    st.subheader("Cuentas más fieles")
    for i, nombre in enumerate(top_nombres_fieles, start=1):
        st.markdown(f"{i}. {nombre.title()}")

    # Cuentas menos fieles
    bottom_fieles = df.groupby("user_id").size().sort_values(ascending=True).head(3).index
    bottom_nombres_fieles = df[df["user_id"].isin(bottom_fieles)].drop_duplicates("user_id").set_index("user_id").loc[bottom_fieles]["nombre_completo"]

    st.subheader("Cuentas menos fieles")
    for i, nombre in enumerate(bottom_nombres_fieles, start=1):
        st.markdown(f"{i}. {nombre.title()}")

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
    st.subheader("Instagram")
    st.metric("Seguidores", "1.245")
    st.metric("Nuevos esta semana", "+54")

    st.subheader("Tendencias de la semana")
    st.markdown("**Búsquedas**: #trailrunning, #fuerzafemenina")
    st.markdown("**Posts destacados**: @run_chicas, @mujeresenmovimiento")
