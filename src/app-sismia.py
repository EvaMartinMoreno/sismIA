import streamlit as st
import pandas as pd
import os
import subprocess

# =========================
# 📁 Rutas de entrada/salida
# =========================
COSTES_PATH = os.path.join("data", "clean", "costes_eventos.csv")
OUTPUT_EVENTOS = os.path.join("data", "clean", "datos_eventos.csv")
OUTPUT_PERSONA = os.path.join("data", "clean", "datos_persona.csv")
ACTUALIZAR_SCRIPT = os.path.join("src", "actualizar_datos.py")

# =========================
# 🚀 Streamlit App Principal
# =========================
st.set_page_config(page_title="SismIA - Gestión de Eventos", layout="wide")
st.title("💡 Panel de Control SismIA")

# Botón para actualizar datos desde procesamiento_eventos.py
if st.button("🔄 Actualizar datos automáticamente"):
    with st.spinner("Ejecutando actualización..."):
        result = subprocess.run(["python", ACTUALIZAR_SCRIPT], capture_output=True, text=True)
        if result.returncode == 0:
            st.success("✅ Datos actualizados correctamente.")
        else:
            st.error("❌ Error en la ejecución del script.")
            st.text(result.stderr)

# =========================
# 🧾 Gestión de costes por evento
# =========================
st.header("🧾 Introducción de costes por evento")

if os.path.exists(OUTPUT_EVENTOS):
    df_eventos = pd.read_csv(OUTPUT_EVENTOS)
    eventos_unicos = pd.DataFrame({"EVENTO": df_eventos["EVENTO"].unique()})
else:
    eventos_unicos = pd.DataFrame(columns=["EVENTO"])

if os.path.exists(COSTES_PATH):
    df_costes = pd.read_csv(COSTES_PATH)
else:
    df_costes = pd.DataFrame(columns=["EVENTO", "COSTE_ESTIMADO"])

# Unificamos eventos para asegurar que estén todos en la tabla de costes
df_costes_full = eventos_unicos.merge(df_costes, on="EVENTO", how="left").fillna(0)
df_costes_edit = st.data_editor(
    df_costes_full[["EVENTO", "COSTE_ESTIMADO"]],
    num_rows="dynamic",
    use_container_width=True
)

if st.button("💾 Guardar costes"):
    df_costes_edit.to_csv(COSTES_PATH, index=False)
    st.success("✅ Costes guardados correctamente")
