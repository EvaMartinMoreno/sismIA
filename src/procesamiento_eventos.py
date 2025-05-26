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
OUTPUT_PERSONA = os.path.join("data", "clean", "datos_persona.csv")
OUTPUT_EVENTOS = os.path.join("data", "clean", "datos_eventos.csv")
REVISION_PATH = os.path.join("data", "entrada", "revision_asistencias.csv")
os.makedirs(os.path.dirname(OUTPUT_PERSONA), exist_ok=True)
os.makedirs(os.path.dirname(REVISION_PATH), exist_ok=True)

# =========================
# 📅 Diccionario meses (castellano + catalán)
# =========================
MESES = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
    "julio": 7, "agosto": 8, "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12,
    "gener": 1, "febrer": 2, "març": 3, "maig": 5, "juny": 6,
    "juliol": 7, "agost": 8, "setembre": 9, "novembre": 11, "desembre": 12
}

# ============================
# 🔎 Correcciones manuales de comunidad
# ============================
EVENTOS_ELCHE_CORREGIDOS = [
    "afterwork-run-by-dash-and-stars-17-dabril-del-2025-a1ca86.csv",
    "los-jueves-con-sh-elche-03-dabril-del-2025-ae05d9.csv",
    "los-jueves-con-sh-elche-06-de-febrer-del-2025-cf139a.csv",
    "los-jueves-con-sh-elche-06-de-marc-del-2025-432204.csv",
    "los-jueves-con-sh-elche-10-dabril-del-2025-1800c7.csv",
    "los-jueves-con-sh-elche-13-de-febrer-del-2025-a74613.csv",
    "los-jueves-con-sh-elche-13-de-marc-del-2025-dd2845.csv",
    "los-jueves-con-sh-elche-20-de-febrer-del-2025-99908a.csv",
    "los-jueves-con-sh-elche-20-de-marc-del-2025-ada6f3.csv",
    "los-jueves-con-sh-elche-23-de-gener-del-2025-551e6b.csv",
    "los-jueves-con-sh-elche-24-dabril-del-2025-e0d544.csv",
    "los-jueves-con-sh-elche-27-de-febrer-del-2025-7c70e9.csv",
    "los-jueves-con-sh-elche-27-de-marc-del-2025-834306.csv",
    "los-jueves-con-sh-elche-30-de-gener-del-2025-b66f8b.csv",
    "new-year-runbreakfast-12-de-gener-del-2025-994f68.csv",
    "pre-xmas-runbrunch-elche-22-de-desembre-del-2024-4a18fe.csv"
]

# ===================
# 🗓 Extraer fecha desde ARCHIVO_ORIGEN
# ===================
def extraer_fecha(archivo):
    archivo = archivo.lower().replace("-", " ").replace("_", " ")
    match = re.search(r"(\d{1,2})\s+de\s+(\w+)\s+del\s+(\d{4})", archivo)
    if match:
        dia, mes, anio = match.groups()
        mes_num = MESES.get(mes, 0)
        if mes_num:
            return datetime(int(anio), mes_num, int(dia))
    return pd.NaT

# =========================
# 🌆 Limpiar nombre del evento
# =========================
def limpiar_nombre_evento(archivo):
    base = archivo.replace(".csv", "").replace("_", " ").replace("-", " ")
    return re.split(r"\s+\d{1,2}\s+de\s+\w+\s+del\s+\d{4}", base, flags=re.IGNORECASE)[0].strip().title()

# ============================
# 🧼 Limpieza principal
# ============================
def limpiar_datos_eventos():
    df = pd.read_csv(INPUT_PATH)

    renames = {
        "name": "ASISTENTE",
        "has_paid": "PAGO",
        "price_paid": "PRECIO_PAGADO",
        "attendance_status": "ASISTENCIA"
    }
    df.rename(columns={k: v for k, v in renames.items() if k in df.columns}, inplace=True)

    df["ASISTENTE"] = df["ASISTENTE"].astype(str).str.strip().str.lower().apply(unidecode).str.upper()

    df["PAGO"] = df["PAGO"].astype(str).str.lower().str.contains("true|si|sí|1", na=False)
    df["ASISTENCIA"] = df["ASISTENCIA"].str.strip().str.lower().map({
        "attended": True,
        "absent": False,
        "pending": pd.NA
    })
    df["PRECIO_PAGADO"] = pd.to_numeric(df.get("PRECIO_PAGADO", 0), errors="coerce").fillna(0)

    df = df[~df["ASISTENTE"].isin(["SISTERHOOD RUNNING CLUB", "SISTERHOOD RC ELCHE"])]

    if "COMUNIDAD" in df.columns:
        df["COMUNIDAD"] = df["COMUNIDAD"].astype(str).str.strip().str.lower().apply(unidecode).str.upper()
        df.loc[df["ARCHIVO_ORIGEN"].isin(EVENTOS_ELCHE_CORREGIDOS), "COMUNIDAD"] = "ELCHE"

    df["FECHA_EVENTO"] = df["ARCHIVO_ORIGEN"].apply(extraer_fecha)
    df["NOMBRE_EVENTO"] = df["ARCHIVO_ORIGEN"].apply(limpiar_nombre_evento)

    posibles_columnas_email = ["Mail", "email", "Nos facilitas tu mail?"]
    columnas_presentes = [col for col in posibles_columnas_email if col in df.columns]

    if columnas_presentes:
        df["EMAIL_TEMP"] = df[columnas_presentes].bfill(axis=1).iloc[:, 0].astype(str).str.strip()
        email_por_asistente = (
            df[["ASISTENTE", "EMAIL_TEMP"]]
            .replace("", pd.NA)
            .dropna()
            .groupby("ASISTENTE")["EMAIL_TEMP"]
            .first()
            .reset_index()
            .rename(columns={"EMAIL_TEMP": "EMAIL"})
        )
        df.drop(columns=columnas_presentes + ["EMAIL_TEMP"], inplace=True, errors="ignore")
        df = df.merge(email_por_asistente, on="ASISTENTE", how="left")
    else:
        df["EMAIL"] = None

    columnas_validas = [
        "NOMBRE_EVENTO", "FECHA_EVENTO", "COMUNIDAD", "ARCHIVO_ORIGEN",
        "ASISTENTE", "PAGO", "ASISTENCIA", "PRECIO_PAGADO", "EMAIL"
    ]
    df = df[[col for col in columnas_validas if col in df.columns]]

    return df

# ============================
# 📊 Agrupar por evento
# ============================
def analizar_eventos(df):
    df_grouped = df.groupby(["ARCHIVO_ORIGEN", "COMUNIDAD"], as_index=False).agg({
        "PRECIO_PAGADO": ["sum", "mean"],
        "ASISTENTE": "count",
        "PAGO": "sum",
        "ASISTENCIA": "sum"
    })

    df_grouped.columns = [
        "EVENTO", "COMUNIDAD",
        "TOTAL_RECAUDADO", "PRECIO_MEDIO",
        "NUM_INSCRITAS", "NUM_PAGOS", "NUM_ASISTENCIAS"
    ]
    df_grouped["EVENTO_GRATUITO"] = df_grouped["TOTAL_RECAUDADO"] == 0
    df_grouped["TASA_ASISTENCIA"] = (df_grouped["NUM_ASISTENCIAS"] / df_grouped["NUM_INSCRITAS"]).round(2)

    return df_grouped

# ============================
# 🔹 Ejecutar
# ============================
if __name__ == "__main__":
    pd.set_option('display.max_columns', None)
    pd.set_option('display.max_rows', 100)

    df_persona = limpiar_datos_eventos()

    # ========================================
    # 🔧 CORRECCIÓN MANUAL DE ASISTENCIA + SIMULACIÓN AUTOMÁTICA
    # ========================================
    if not os.path.exists(REVISION_PATH):
        df_persona[["ASISTENTE", "NOMBRE_EVENTO", "FECHA_EVENTO", "ARCHIVO_ORIGEN", "ASISTENCIA"]].drop_duplicates().to_csv(REVISION_PATH, index=False)
        print(f"📤 Archivo de revisión de asistencias exportado a: {REVISION_PATH}\nRevisa y corrige manualmente la columna 'ASISTENCIA' con TRUE o FALSE.")
    else:
        df_revision = pd.read_csv(REVISION_PATH)
        df_revision["FECHA_EVENTO"] = pd.to_datetime(df_revision["FECHA_EVENTO"], errors="coerce")
        df_revision["ASISTENCIA"] = df_revision["ASISTENCIA"].astype(bool)
        df_persona.drop("ASISTENCIA", axis=1, inplace=True)
        df_persona = df_persona.merge(
            df_revision,
            on=["ASISTENTE", "NOMBRE_EVENTO", "FECHA_EVENTO", "ARCHIVO_ORIGEN"],
            how="left"
        )
        print("✅ Asistencia corregida manualmente desde archivo externo.")

    # Automatizar valores NA restantes (simulación)
    if df_persona["ASISTENCIA"].isna().sum() > 0:
        np.random.seed(42)
        mask = df_persona["ASISTENCIA"].isna()
        asignaciones = np.random.choice([True, False], size=mask.sum(), p=[0.85, 0.15])
        df_persona.loc[mask, "ASISTENCIA"] = asignaciones
        print(f"🤖 Simulación: Asignados {mask.sum()} valores de asistencia con 85% TRUE y 15% FALSE.")

    df_eventos = analizar_eventos(df_persona)

    total = df_persona[df_persona["ASISTENCIA"] == True].groupby("ASISTENTE")["NOMBRE_EVENTO"].nunique().reset_index(name="NUM_ASISTENCIAS_TOTAL")
    gratis = df_persona[(df_persona["ASISTENCIA"] == True) & (~df_persona["PAGO"])] \
        .groupby("ASISTENTE")["NOMBRE_EVENTO"].nunique().reset_index(name="NUM_ASISTENCIAS_GRATUITO")
    pago = df_persona[(df_persona["ASISTENCIA"] == True) & (df_persona["PAGO"])] \
        .groupby("ASISTENTE")["NOMBRE_EVENTO"].nunique().reset_index(name="NUM_ASISTENCIAS_PAGO")

    df_persona = df_persona.merge(total, on="ASISTENTE", how="left")
    df_persona = df_persona.merge(gratis, on="ASISTENTE", how="left")
    df_persona = df_persona.merge(pago, on="ASISTENTE", how="left")

    df_persona[["NUM_ASISTENCIAS_TOTAL", "NUM_ASISTENCIAS_GRATUITO", "NUM_ASISTENCIAS_PAGO"]] = \
        df_persona[["NUM_ASISTENCIAS_TOTAL", "NUM_ASISTENCIAS_GRATUITO", "NUM_ASISTENCIAS_PAGO"]].fillna(0).astype(int)

    costes_evento = {}
    df_eventos["COSTE_ESTIMADO"] = df_eventos["EVENTO"].map(costes_evento).fillna(0)
    df_eventos["BENEFICIO_ESTIMADO"] = df_eventos["TOTAL_RECAUDADO"] - df_eventos["COSTE_ESTIMADO"]

    df_persona.to_csv(OUTPUT_PERSONA, index=False)
    df_eventos.to_csv(OUTPUT_EVENTOS, index=False)

    print("\n🔍 Vista previa eventos agrupados:")
    print(df_eventos.head(10))
    print("\n🔍 Vista previa personas:")
    print(df_persona.head(10))
