from pathlib import Path
import re
import numpy as np
import pandas as pd
from datetime import datetime
from unidecode import unidecode

# =========================
# 📁 Rutas
# =========================
BASE_DIR = Path("data")
REVISION_PATH = BASE_DIR / "entrada" / "revision_asistencias.csv"
COSTES_PATH = BASE_DIR / "clean" / "costes_eventos.csv"
OUTPUT_DIR = BASE_DIR / "clean"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_PREDICTIVO = OUTPUT_DIR / "dataset_modelo.csv"

# =========================
# 📆 Diccionario meses
# =========================
MESES = {
    "enero": 1, "gener": 1,
    "febrero": 2, "febrer": 2, "de febrer": 2,
    "marzo": 3, "març": 3, "de marc":3, "marc": 3,
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

# =========================
# 📌 Correcciones manuales por comunidad
# =========================
eventos_elche_exactos = [
    "afterwork-run-by-dash-and-stars-17-dabril-del-2025-a1ca86.csv",
    "new-year-runbreakfast-12-de-gener-del-2025-994f68.csv",
    "pre-xmas-runbrunch-elche-22-de-desembre-del-2024-4a18fe.csv",
    "runlearn-06-dabril-del-2025-9691b4.csv",
    "runtrust-09-de-marc-del-2025-eb00b7.csv"
]

eventos_elche_prefijos = ["los-jueves-con-sh-elche"]

# =========================
# 🔧 Funciones auxiliares
# =========================
def extraer_fecha(nombre_archivo: str) -> pd.Timestamp:
    nombre_archivo = nombre_archivo.lower().replace("-", " ").replace("_", " ")

    # Admite formatos como: "14 de marzo del 2024", "14 de març de 2024", "14 març 2024"
    match = re.search(r"(\d{1,2})\s*(?:de)?\s*(\w+)\s*(?:de|del)?\s*(\d{4})", nombre_archivo)
    if match:
        dia, mes, anio = match.groups()
        mes = mes.lower().strip()
        mes_num = MESES.get(mes)

        if mes_num:
            try:
                return datetime(int(anio), mes_num, int(dia))
            except ValueError:
                return pd.NaT
        else:
            print(f"⚠️ Mes no reconocido: '{mes}' en archivo '{nombre_archivo}'")

    return pd.NaT

def limpiar_nombre_evento(nombre_archivo: str) -> str:
    # Eliminar extensión, guiones y underscores
    nombre = nombre_archivo.lower().replace(".csv", "").replace("_", " ").replace("-", " ")

    # Eliminar hashes al final (códigos tipo "a1ca86", "75b84a", etc.)
    nombre = re.sub(r"\b[a-f0-9]{5,}\b$", "", nombre)

    # Eliminar cualquier fecha en formato "dd mes año" (con o sin 'de' y 'del')
    nombre = re.sub(r"\d{1,2}\s*(?:de)?\s*\w+\s*(?:de|del)?\s*\d{4}", "", nombre)

    # Quitar espacios extra y poner en formato título
    return nombre.strip().title()

def cargar_y_unificar_csvs_athletiks() -> pd.DataFrame:
    """
    Carga todos los CSVs desde 'data/raw/athletiks/GIRONA' y 'ELCHE',
    añade la columna 'COMUNIDAD' en base a la carpeta de origen,
    corrige BOM y comillas dobles, y valida que existan las columnas requeridas.
    """
    columnas_requeridas = {"name", "has_paid", "price_paid", "attendance_status"}

    def cargar_csvs_de(comunidad: str) -> pd.DataFrame:
        carpeta = BASE_DIR / "raw" / "athletiks" / comunidad.upper()
        dataframes = []

        for archivo in carpeta.glob("*.csv"):
            try:
                # Leer con separador explícito
                df = pd.read_csv(archivo, sep=";", engine="python", on_bad_lines="skip")

                # Limpiar cabeceras de posibles comillas dobles o BOM
                df.columns = [col.encode('utf-8').decode('utf-8-sig').strip().strip('"') for col in df.columns]

                # Verificación de columnas mínimas necesarias
                columnas_faltantes = columnas_requeridas - set(df.columns)
                if columnas_faltantes:
                    print(f"⚠️ {archivo.name} omitido: faltan columnas {columnas_faltantes}")
                    continue

                df["ARCHIVO_ORIGEN"] = archivo.name
                df["COMUNIDAD"] = comunidad.upper()
                dataframes.append(df)

            except Exception as e:
                print(f"❌ Error leyendo {archivo.name}: {e}")

        return pd.concat(dataframes, ignore_index=True) if dataframes else pd.DataFrame()

    df_girona = cargar_csvs_de("girona")
    df_elche = cargar_csvs_de("elche")
    df_total = pd.concat([df_girona, df_elche], ignore_index=True)

    # Ver cuántas filas tiene cada uno
    print(f"🔎 Filas GIRONA: {len(df_girona)}")
    print(f"🔎 Filas ELCHE: {len(df_elche)}")
    print(f"🧾 Total filas concatenadas: {len(df_total)}")

    # Ver si hay valores nulos en columnas clave
    print("🧼 Nulos por columna:")
    print(df_total.isna().sum())

    # Ver primeros archivos cargados
    print("📂 Archivos cargados (primeros 5):")
    print(df_total['ARCHIVO_ORIGEN'].drop_duplicates().head())


    if not df_total.empty and "COMUNIDAD" in df_total.columns:
        print("📦 CSVs cargados. Distribución por comunidad:")
        print(df_total["COMUNIDAD"].value_counts(), "\n")
    else:
        print("⚠️ No se cargó ningún CSV válido. Todos fueron omitidos por errores de formato.")

    # Cambiar comunidad por nombre exacto
    df_total.loc[df_total["ARCHIVO_ORIGEN"].isin(eventos_elche_exactos), "COMUNIDAD"] = "ELCHE"

    # Cambiar comunidad por prefijos
    for prefijo in eventos_elche_prefijos:
        mask = df_total["ARCHIVO_ORIGEN"].str.startswith(prefijo)
        df_total.loc[mask, "COMUNIDAD"] = "ELCHE"

    # 📊 DEPURACIÓN: Verificar carga inicial de eventos
    print("\n🔍 Eventos únicos tras carga inicial:", df_total["ARCHIVO_ORIGEN"].nunique())
    print("🎯 Ejemplo de eventos cargados:")
    print(df_total["ARCHIVO_ORIGEN"].drop_duplicates().sort_values().head(10).to_list())

    # Cambiar comunidad por nombre exacto
    df_total.loc[df_total["ARCHIVO_ORIGEN"].isin(eventos_elche_exactos), "COMUNIDAD"] = "ELCHE"

    # Cambiar comunidad por prefijos
    for prefijo in eventos_elche_prefijos:
        mask = df_total["ARCHIVO_ORIGEN"].str.startswith(prefijo)
        afectados = df_total.loc[mask].shape[0]
        if afectados > 0:
            print(f"🔧 {afectados} eventos corregidos a ELCHE por prefijo: '{prefijo}'")
        df_total.loc[mask, "COMUNIDAD"] = "ELCHE"

    return df_total

# =========================
# 🧼 Procesamiento principal
# =========================
def generar_dataset_predictivo():
    df = cargar_y_unificar_csvs_athletiks()

    df.rename(columns={
        "name": "ASISTENTE",
        "has_paid": "PAGO",
        "price_paid": "PRECIO_PAGADO",
        "attendance_status": "ASISTENCIA"
    }, inplace=True)

    df["ASISTENTE"] = df["ASISTENTE"].astype(str).str.strip().str.lower().apply(unidecode).str.upper()
    df["PAGO"] = df["PAGO"].astype(str).str.lower().str.contains("true|si|sí|1", na=False).astype(int)
    df["ASISTENCIA"] = df["ASISTENCIA"].str.strip().str.lower().map({
    "attended": 1,
    "absent": 0,
    "pending": pd.NA
    })

    df["PRECIO_PAGADO"] = pd.to_numeric(df.get("PRECIO_PAGADO", 0), errors="coerce").fillna(0)

    df = df[~df["ASISTENTE"].isin(["SISTERHOOD RUNNING CLUB", "SISTERHOOD RC ELCHE"])]

    df["FECHA_EVENTO"] = df["ARCHIVO_ORIGEN"].apply(extraer_fecha)
    df["NOMBRE_EVENTO"] = df["ARCHIVO_ORIGEN"].apply(limpiar_nombre_evento)
    df["DIA_SEMANA"] = df["FECHA_EVENTO"].dt.day_name()
    df["MES"] = df["FECHA_EVENTO"].dt.month
    df["SEMANA"] = df["FECHA_EVENTO"].dt.isocalendar().week

    eventos_sin_fecha = df[df["FECHA_EVENTO"].isna()]["ARCHIVO_ORIGEN"].unique().tolist()
    if eventos_sin_fecha:
        print("🚫 Eventos sin fecha reconocida, se excluirán:")
        for ev in eventos_sin_fecha:
            print(" -", ev)

    df = df[~df["FECHA_EVENTO"].isna()]  # Eliminar eventos sin fecha antes del agrupado

    if REVISION_PATH.exists():
        df_revision = pd.read_csv(REVISION_PATH)
        df_revision["FECHA_EVENTO"] = pd.to_datetime(df_revision["FECHA_EVENTO"], errors="coerce")
        df["ASISTENCIA"] = df["ASISTENCIA"].fillna(0).astype(int)

        # 🧹 Eliminar duplicados antes de hacer el merge
        df_revision = df_revision.drop_duplicates(subset=["ASISTENTE", "NOMBRE_EVENTO", "FECHA_EVENTO", "ARCHIVO_ORIGEN"])

        df.drop("ASISTENCIA", axis=1, inplace=True)
        df = df.merge(df_revision, on=["ASISTENTE", "NOMBRE_EVENTO", "FECHA_EVENTO", "ARCHIVO_ORIGEN"], how="left")

    if df["ASISTENCIA"].isna().any():
        np.random.seed(42)
        mask = df["ASISTENCIA"].isna()
        df.loc[mask, "ASISTENCIA"] = np.random.choice([1, 0], size=mask.sum(), p=[0.85, 0.15])

    # 🔄 Eventos únicos antes de agrupar
    print("\n🔄 Eventos únicos antes de agrupar:", df["ARCHIVO_ORIGEN"].nunique())
    print("🎯 Algunos nombres de eventos antes del groupby:")
    print(df["NOMBRE_EVENTO"].drop_duplicates().sort_values().head(10).to_list())

    df["ASISTENCIA"] = pd.to_numeric(df["ASISTENCIA"], errors="coerce").fillna(0).astype(int)
    df["PAGO"] = pd.to_numeric(df["PAGO"], errors="coerce").fillna(0).astype(int)

    df_evento = df.groupby(
        ["NOMBRE_EVENTO", "FECHA_EVENTO", "COMUNIDAD", "DIA_SEMANA", "MES", "SEMANA"], as_index=False
    ).agg({
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

    if COSTES_PATH.exists():
        df_costes = pd.read_csv(COSTES_PATH)
        df_costes["EVENTO_LIMPIO"] = df_costes["EVENTO"].apply(limpiar_nombre_evento)
        df_evento = df_evento.merge(
            df_costes[["EVENTO_LIMPIO", "COSTE_ESTIMADO"]],
            left_on="NOMBRE_EVENTO", right_on="EVENTO_LIMPIO", how="left"
        ).drop(columns=["EVENTO_LIMPIO"])
        df_evento["COSTE_ESTIMADO"] = df_evento["COSTE_ESTIMADO"].fillna(0)
    else:
        df_evento["COSTE_ESTIMADO"] = 0.0

    df_evento["BENEFICIO_ESTIMADO"] = df_evento["TOTAL_RECAUDADO"] - df_evento["COSTE_ESTIMADO"]

    #  Eliminar duplicados del dataframe final de eventos
    df_evento = df_evento.drop_duplicates()

    df_evento.to_csv(OUTPUT_PREDICTIVO, index=False)

    print("✅ Archivos generados:")
    print(f" - General:   {OUTPUT_PREDICTIVO}")

# =========================
# 🚀 Ejecutar
# =========================
if __name__ == "__main__":
    pd.set_option('display.max_columns', None)
    pd.set_option('display.max_rows', 100)
    generar_dataset_predictivo()
