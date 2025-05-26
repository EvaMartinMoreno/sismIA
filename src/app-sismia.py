import os
import pandas as pd
import re
from datetime import datetime
import unidecode
import streamlit as st

# === CONFIGURACIÓN DE RUTAS ===
RAW_DIR = os.path.join("data", "raw", "athletiks")
OUTPUT_PATH = os.path.join("data", "clean", "events_athletiks_limpio.csv")
os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

# === DICCIONARIO MESES ===
MESES = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
    "julio": 7, "agosto": 8, "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12,
    "gener": 1, "febrer": 2, "març": 3, "abril": 4, "maig": 5, "juny": 6,
    "juliol": 7, "agost": 8, "setembre": 9, "octubre": 10, "novembre": 11, "desembre": 12
}

# === FUNCIONES AUXILIARES ===
def extraer_fecha(texto):
    texto = texto.replace("-", " ").lower()
    match = re.search(r"(\d{1,2})\s+de\s+(\w+)\s+del\s+(\d{4})", texto)
    if match:
        dia, mes, anio = match.groups()
        mes_num = MESES.get(mes, 0)
        if mes_num:
            return datetime(int(anio), mes_num, int(dia))
    return pd.NaT

def limpiar_nombre_evento(nombre):
    nombre = nombre.replace(".csv", "").replace("-", " ").replace("_", " ")
    nombre = re.split(r"\s\d{1,2}\s+de\s+\w+\s+del\s+\d{4}", nombre, flags=re.IGNORECASE)[0]
    return nombre.strip().title()

# === PROCESAMIENTO Y UNIFICACIÓN ===
def cargar_y_unificar_csvs():
    all_data = []

    for comunidad in os.listdir(RAW_DIR):
        carpeta = os.path.join(RAW_DIR, comunidad)
        if not os.path.isdir(carpeta):
            continue

        for archivo in os.listdir(carpeta):
            if archivo.endswith(".csv"):
                path = os.path.join(carpeta, archivo)
                try:
                    df = pd.read_csv(path, sep=";", engine="python", encoding="utf-8", on_bad_lines="skip")
                    if df.empty:
                        continue

                    df["COMUNIDAD"] = comunidad.upper()
                    df["ARCHIVO"] = archivo
                    df["EVENTO"] = limpiar_nombre_evento(archivo)
                    df["FECHA_EVENTO"] = extraer_fecha(archivo)

                    df.rename(columns={
                        "name": "ASISTENTE",
                        "has_paid": "PAGADO",
                        "price_paid": "PRECIO_PAGADO",
                        "attendance_status": "ASISTIO"
                    }, inplace=True)

                    for col in ["ASISTENTE", "PAGADO", "ASISTIO", "PRECIO_PAGADO"]:
                        if col not in df.columns:
                            df[col] = None

                    df["COSTE_ESTIMADO"] = None
                    all_data.append(df)
                except Exception as e:
                    print(f"❌ Error cargando {archivo}: {e}")

    if not all_data:
        return pd.DataFrame()

    df = pd.concat(all_data, ignore_index=True)
    df["ASISTENTE"] = df["ASISTENTE"].astype(str).str.strip().str.lower().apply(unidecode.unidecode).str.upper()
    df = df[~df["ASISTENTE"].isin(["SISTERHOOD RC ELCHE", "SISTERHOOD RUNNING CLUB"])]

    df["PAGADO"] = df["PAGADO"].astype(str).str.lower().str.contains("true|si|sí|1", na=False)
    df["ASISTIO"] = df["ASISTIO"].astype(str).str.lower().str.contains("attended|confirmada|asistido", na=False)
    df["PRECIO_PAGADO"] = pd.to_numeric(df["PRECIO_PAGADO"], errors="coerce").fillna(0)
    df["COSTE_ESTIMADO"] = pd.to_numeric(df["COSTE_ESTIMADO"], errors="coerce")
    df["NUM_ASISTENCIAS"] = df.groupby("ASISTENTE")["EVENTO"].transform("count")

    df_grouped = df.groupby(["EVENTO", "FECHA_EVENTO", "COMUNIDAD"], as_index=False).agg({
        "PRECIO_PAGADO": "sum",
        "COSTE_ESTIMADO": "first"
    })

    df_grouped["COMISION"] = df_grouped["PRECIO_PAGADO"] * 0.05
    df_grouped["INGRESO_EVENTO"] = df_grouped["PRECIO_PAGADO"]
    df_grouped["BENEFICIO_EVENTO"] = df_grouped["INGRESO_EVENTO"] - df_grouped["COMISION"] - df_grouped["COSTE_ESTIMADO"].fillna(0)

    df_final = df.merge(df_grouped, on=["EVENTO", "FECHA_EVENTO", "COMUNIDAD"], how="left")

    columnas_finales = [
        "EVENTO", "FECHA_EVENTO", "COMUNIDAD", "ASISTENTE", "ASISTIO", "PAGADO",
        "PRECIO_PAGADO", "COSTE_ESTIMADO", "INGRESO_EVENTO", "COMISION", "BENEFICIO_EVENTO",
        "NUM_ASISTENCIAS"
    ]
    for col in columnas_finales:
        if col not in df_final.columns:
            df_final[col] = None

    df_final = df_final[columnas_finales]
    df_final.to_csv(OUTPUT_PATH, index=False)
    return df_final

# === STREAMLIT UI PARA EDITAR COSTES ===
def editar_costes(df):
    eventos_unicos = df[["EVENTO", "FECHA_EVENTO", "COMUNIDAD"]].drop_duplicates()
    st.subheader("💸 Introducir o editar coste estimado por evento")

    if "COSTE_CONFIRMADO" not in df.columns:
        df["COSTE_CONFIRMADO"] = False

        eventos_unicos = df[["EVENTO", "FECHA_EVENTO", "COMUNIDAD"]].drop_duplicates()
    st.subheader("💸 Introducir o validar coste estimado por evento")

    if "COSTE_CONFIRMADO" not in df.columns:
        df["COSTE_CONFIRMADO"] = False

    cambios_realizados = False

    for _, row in eventos_unicos.iterrows():
        evento, fecha, comunidad = row["EVENTO"], row["FECHA_EVENTO"], row["COMUNIDAD"]

        mask = (df["EVENTO"] == evento) & (df["FECHA_EVENTO"] == fecha) & (df["COMUNIDAD"] == comunidad)

        confirmado = df.loc[mask, "COSTE_CONFIRMADO"].dropna().unique()
        confirmado = confirmado[0] if len(confirmado) > 0 else False

        if not confirmado:
            current_value = df.loc[mask, "COSTE_ESTIMADO"].dropna().unique()
            current_value = float(current_value[0]) if len(current_value) > 0 else 0.0

            st.markdown(f"**🗓️ {evento} ({comunidad} - {fecha})**")
            nuevo_coste = st.number_input(
                f"Introduce el coste estimado (€)", key=f"coste_{evento}_{fecha}", min_value=0.0, value=current_value, step=1.0
            )
            confirmar = st.checkbox("✅ Confirmar este coste", key=f"confirmar_{evento}_{fecha}")

            if confirmar:
                df.loc[mask, "COSTE_ESTIMADO"] = nuevo_coste
                df.loc[mask, "COSTE_CONFIRMADO"] = True
                cambios_realizados = True
                st.success(f"✅ Coste confirmado para {evento}")

            st.markdown("---")

    if cambios_realizados:
        if st.button("💾 Guardar todos los costes confirmados"):
            df.to_csv(OUTPUT_PATH, index=False)
            st.success("✅ Costes guardados correctamente")


# === STREAMLIT APP ===
st.set_page_config(page_title="SismIA - Costes", layout="wide")
st.title("🧠 SismIA · Gestión de eventos Sisterhood")

df_eventos = cargar_y_unificar_csvs()

if df_eventos.empty:
    st.warning("⚠️ No hay datos de eventos disponibles para mostrar.")
else:
    editar_costes(df_eventos)
