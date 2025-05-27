import os
import pandas as pd
import re
import numpy as np
from datetime import datetime
from unidecode import unidecode

# =========================
# 📁 Rutas de entrada/salida
# =========================
INPUT_PATH = os.path.join("data", "clean", "events_athletiks_unificado.csv")
REVISION_PATH = os.path.join("data", "entrada", "revision_asistencias.csv")
COSTES_PATH = os.path.join("data", "clean", "costes_eventos.csv")
OUTPUT_PREDICTIVO = os.path.join("data", "clean", "dataset_modelo.csv")
OUTPUT_PREDICTIVO_PAGO = os.path.join("data", "clean", "dataset_modelo_pago.csv")
OUTPUT_PREDICTIVO_GRATUITO = os.path.join("data", "clean", "dataset_modelo_gratuito.csv")
os.makedirs(os.path.dirname(OUTPUT_PREDICTIVO), exist_ok=True)

# =========================
# 🗓 Diccionario meses
# =========================
MESES = {
    "enero": 1, "gener": 1,
    "febrero": 2, "febrer": 2, "de febrer": 2,
    "marzo": 3, "març": 3, "de marc": 3,
    "abril": 4, "dabril": 4,
    "mayo": 5, "maig": 5,
    "junio": 6, "juny": 6,
    "julio": 7, "juliol": 7,
    "agosto": 8, "agost": 8,
    "septiembre": 9, "setembre": 9,
    "octubre": 10, "doctubre": 10,
    "noviembre": 11, "novembre": 11,
    "diciembre": 12, "desembre": 12
}

# ============================
# 🔧 FUNCIONES AUXILIARES
# ============================
def extraer_fecha(archivo):
    archivo = archivo.lower().replace("-", " ").replace("_", " ")
    match = re.search(r"(\d{1,2})\s+de\s+(\w+)\s+del\s+(\d{4})", archivo)
    if match:
        dia, mes, anio = match.groups()
        mes = mes.lower()
        mes_num = MESES.get(mes, 0)
        if mes_num:
            return datetime(int(anio), mes_num, int(dia))
    return pd.NaT

def limpiar_nombre_evento(archivo):
    archivo = archivo.lower().replace(".csv", "").replace("_", " ").replace("-", " ")
    partes = re.split(r"\s+\d{1,2}\s+de\s+\w+\s+del\s+\d{4}", archivo, flags=re.IGNORECASE)
    return partes[0].strip().title() if partes else archivo.title()

def extraer_comunidad(archivo):
    archivo = archivo.lower()
    if "girona" in archivo:
        return "GIRONA"
    elif "elche" in archivo:
        return "ELCHE"
    else:
        return "DESCONOCIDA"

# ============================
# 🧼 PROCESAMIENTO Y CREACION DE DATASET PREDICTIVO
# ============================
def generar_dataset_predictivo():
    df = pd.read_csv(INPUT_PATH)
    df.rename(columns={
        "name": "ASISTENTE",
        "has_paid": "PAGO",
        "price_paid": "PRECIO_PAGADO",
        "attendance_status": "ASISTENCIA"
    }, inplace=True)

    df["ASISTENTE"] = df["ASISTENTE"].astype(str).str.strip().str.lower().apply(unidecode).str.upper()
    df["PAGO"] = df["PAGO"].astype(str).str.lower().str.contains("true|si|sí|1", na=False)
    df["ASISTENCIA"] = df["ASISTENCIA"].str.strip().str.lower().map({
        "attended": True,
        "absent": False,
        "pending": pd.NA
    })
    df["PRECIO_PAGADO"] = pd.to_numeric(df.get("PRECIO_PAGADO", 0), errors="coerce").fillna(0)
    df = df[~df["ASISTENTE"].isin(["SISTERHOOD RUNNING CLUB", "SISTERHOOD RC ELCHE"])]

    df["FECHA_EVENTO"] = df["ARCHIVO_ORIGEN"].apply(extraer_fecha)
    df["NOMBRE_EVENTO"] = df["ARCHIVO_ORIGEN"].apply(limpiar_nombre_evento)
    df["COMUNIDAD"] = df["ARCHIVO_ORIGEN"].apply(extraer_comunidad).str.upper()
    df["DIA_SEMANA"] = df["FECHA_EVENTO"].dt.day_name()
    df["MES"] = df["FECHA_EVENTO"].dt.month
    df["SEMANA"] = df["FECHA_EVENTO"].dt.isocalendar().week

    print("\n🔍 Verificación de valores únicos en COMUNIDAD:")
    print(df["COMUNIDAD"].value_counts(dropna=False))

    if os.path.exists(REVISION_PATH):
        df_revision = pd.read_csv(REVISION_PATH)
        df_revision["FECHA_EVENTO"] = pd.to_datetime(df_revision["FECHA_EVENTO"], errors="coerce")
        df_revision["ASISTENCIA"] = df_revision["ASISTENCIA"].astype(bool)
        df.drop("ASISTENCIA", axis=1, inplace=True)
        df = df.merge(df_revision, on=["ASISTENTE", "NOMBRE_EVENTO", "FECHA_EVENTO", "ARCHIVO_ORIGEN"], how="left")

    if df["ASISTENCIA"].isna().sum() > 0:
        np.random.seed(42)
        mask = df["ASISTENCIA"].isna()
        df.loc[mask, "ASISTENCIA"] = np.random.choice([True, False], size=mask.sum(), p=[0.85, 0.15])

    df_evento = df.groupby(["NOMBRE_EVENTO", "FECHA_EVENTO", "COMUNIDAD", "DIA_SEMANA", "MES", "SEMANA"], as_index=False).agg({
        "ASISTENTE": "count",
        "PAGO": "sum",
        "ASISTENCIA": "sum",
        "PRECIO_PAGADO": "sum"
    }).rename(columns={
        "ASISTENTE": "NUM_INSCRITAS",
        "PAGO": "NUM_PAGOS",
        "ASISTENCIA": "NUM_ASISTENCIAS",
        "PRECIO_PAGADO": "TOTAL_RECAUDADO"
    })

    df_evento["EVENTO_GRATUITO"] = df_evento["TOTAL_RECAUDADO"] == 0
    df_evento["TIPO_EVENTO"] = np.where(df_evento["EVENTO_GRATUITO"], "gratuito", "pago")

    if os.path.exists(COSTES_PATH):
        df_costes = pd.read_csv(COSTES_PATH)
        df_costes["EVENTO_LIMPIO"] = df_costes["EVENTO"].apply(limpiar_nombre_evento)
        df_evento = df_evento.merge(df_costes[["EVENTO_LIMPIO", "COSTE_ESTIMADO"]], left_on="NOMBRE_EVENTO", right_on="EVENTO_LIMPIO", how="left")
        df_evento.drop(columns=["EVENTO_LIMPIO"], inplace=True)
        df_evento["COSTE_ESTIMADO"] = df_evento["COSTE_ESTIMADO"].fillna(0)
    else:
        df_evento["COSTE_ESTIMADO"] = 0.0

    df_evento["BENEFICIO_ESTIMADO"] = df_evento["TOTAL_RECAUDADO"] - df_evento["COSTE_ESTIMADO"]

    df_evento.to_csv(OUTPUT_PREDICTIVO, index=False)
    df_evento[df_evento["TIPO_EVENTO"] == "pago"].to_csv(OUTPUT_PREDICTIVO_PAGO, index=False)
    df_evento[df_evento["TIPO_EVENTO"] == "gratuito"].to_csv(OUTPUT_PREDICTIVO_GRATUITO, index=False)

    print("\n✅ Dataset general creado:", OUTPUT_PREDICTIVO)
    print("✅ Dataset pago creado:", OUTPUT_PREDICTIVO_PAGO)
    print("✅ Dataset gratuito creado:", OUTPUT_PREDICTIVO_GRATUITO)

# ============================
# 🚀 MAIN
# ============================
if __name__ == "__main__":
    pd.set_option('display.max_columns', None)
    pd.set_option('display.max_rows', 100)
    generar_dataset_predictivo()
