import streamlit as st
import pandas as pd
import os
import matplotlib.pyplot as plt

# === Ruta del CSV ===
RUTA_CSV = os.path.join(os.path.dirname(__file__), "..", "data", "user_insights.csv")

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os

def mostrar_interacciones_diarias():
    path = os.path.join("data", "user_insights.csv")
    if not os.path.exists(path):
        st.warning("No se encontró el archivo de métricas de usuario.")
        return

    df = pd.read_csv(path)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df[df["metric"] == "total_interactions"]

    if df.empty:
        st.info("No hay datos suficientes de interacciones para mostrar.")
        return

    df = df.groupby(df["timestamp"].dt.date)["value"].sum().reset_index()
    df.columns = ["Fecha", "Interacciones"]

    fig, ax = plt.subplots()
    ax.plot(df["Fecha"], df["Interacciones"], marker="o", linestyle="-", color="#a26ec6")
    ax.set_title("Interacciones Diarias")
    ax.set_xlabel("Fecha")
    ax.set_ylabel("Total de interacciones")
    ax.grid(True)

    st.pyplot(fig)

# === Función para cargar y preparar los datos ===
def cargar_datos_insights():
    if not os.path.exists(RUTA_CSV):
        st.warning("No se encontró el archivo user_insights.csv")
        return pd.DataFrame()

    df = pd.read_csv(RUTA_CSV)
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df = df[df["timestamp"].notna()].copy()
    df.sort_values("timestamp", inplace=True)
    return df

# === Función para mostrar las métricas disponibles ===
def mostrar_evolucion_metricas():
    st.markdown("## 📈 Evolución de métricas de Instagram")
    df = cargar_datos_insights()

    if df.empty:
        st.info("No hay datos disponibles para mostrar.")
        return

    métricas_disponibles = df["metric"].unique().tolist()

    # Corrección: Validación segura de valores por defecto
    valores_por_defecto = ["accounts_engaged", "profile_views", "followers_count"]
    seleccion_por_defecto = [m for m in valores_por_defecto if m in métricas_disponibles]

    seleccionadas = st.multiselect(
        "Selecciona métricas a mostrar",
        options=métricas_disponibles,
        default=seleccion_por_defecto
    )

    if not seleccionadas:
        st.info("Selecciona al menos una métrica para visualizar.")
        return

    for metric in seleccionadas:
        st.markdown(f"### {metric.replace('_', ' ').capitalize()}")
        df_metric = df[df["metric"] == metric]

        fig, ax = plt.subplots()
        ax.plot(df_metric["timestamp"], df_metric["value"], marker="o")
        ax.set_xlabel("Fecha")
        ax.set_ylabel("Valor")
        ax.set_title(metric.replace("_", " ").capitalize())
        ax.grid(True)
        st.pyplot(fig)

def mostrar_top_engagement():
    path = os.path.join("data", "user_insights.csv")
    if not os.path.exists(path):
        st.warning("No se encontró el archivo de métricas de usuario.")
        return

    df = pd.read_csv(path)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df[df["metric"] == "total_interactions"]

    if df.empty:
        st.info("No hay datos suficientes de engagement.")
        return

    df = df.groupby(df["timestamp"].dt.date)["value"].sum().reset_index()
    df.columns = ["Fecha", "Interacciones"]
    top = df.sort_values("Interacciones", ascending=False).head(5)

    fig, ax = plt.subplots()
    ax.barh(top["Fecha"].astype(str), top["Interacciones"], color="#a26ec6")
    ax.set_title("Top 5 días con más engagement")
    ax.set_xlabel("Interacciones")
    ax.invert_yaxis()
    st.pyplot(fig)

def mostrar_post_mas_viral():
    path = os.path.join("data", "media_insights.csv")
    if not os.path.exists(path):
        st.warning("No se encontró el archivo media_insights.csv.")
        return

    df = pd.read_csv(path)

    # Nos aseguramos de que sea del tipo correcto
    df = df[df["metric"] == "reach"]
    df = df.sort_values("value", ascending=False)

    if df.empty:
        st.info("No hay datos de publicaciones con 'reach'.")
        return

    top = df.iloc[0]

    st.markdown("### 🌟 Post más viral")
    st.markdown(f"- 📅 Fecha: **{pd.to_datetime(top['timestamp']).strftime('%d %b %Y')}**")
    st.markdown(f"- 📷 Tipo: **{top['media_type']}**")
    st.markdown(f"- 👁️ Alcance: **{top['value']}**")
    st.markdown(f"- 🔗 [Ver en Instagram]({top['permalink']})")

    # Mostrar imagen si está disponible
    if "media_url" in top and pd.notna(top["media_url"]):
        st.image(top["media_url"], width=400) 

    # Mostrar métricas adicionales si existen
    metrics = df[df["media_id"] == top["media_id"]]
    for _, row in metrics.iterrows():
        if row["metric"] != "reach":
            st.markdown(f"- {row['metric'].capitalize()}: **{row['value']}**")
