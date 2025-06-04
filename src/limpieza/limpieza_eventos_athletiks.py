from pathlib import Path
import pandas as pd
import numpy as np
import unicodedata

# === 📁 Rutas
INPUT = Path("data/clean/eventos_crudos_unificados.csv")
OUTPUT = Path("data/clean/dataset_modelo.csv")
TIPOS_PATH = Path("data/entrada/tipos_evento.csv")

# === 📥 Cargar datos
df_raw = pd.read_csv(INPUT, parse_dates=["FECHA_EVENTO"])

# === 🧹 Limpieza de nulos
df_raw["PAGO"] = pd.to_numeric(df_raw["PAGO"], errors="coerce").fillna(0).astype(int)
df_raw["ASISTENCIA"] = pd.to_numeric(df_raw["ASISTENCIA"], errors="coerce").fillna(0).astype(int)
df_raw["PRECIO_PAGADO"] = pd.to_numeric(df_raw["PRECIO_PAGADO"], errors="coerce").fillna(0)

# === 🎯 Rellenar columna ASISTENCIA basada en reglas heurísticas

# Iniciar columna vacía
df_raw["ASISTENCIA"] = np.nan

# === EVENTOS DE PAGO
eventos_pago = df_raw[df_raw["PAGO"] == 1]["NOMBRE_EVENTO"].unique()
for i, evento in enumerate(eventos_pago):
    participantes = df_raw[(df_raw["NOMBRE_EVENTO"] == evento) & (df_raw["PAGO"] == 1)].index.tolist()
    if not participantes:
        continue
    # Cada 2 eventos eliminamos 1 o 2 asistentes
    if i % 2 == 0:
        no_asisten = np.random.choice(participantes, size=min(len(participantes), np.random.randint(1, 3)), replace=False)
        df_raw.loc[list(set(participantes) - set(no_asisten)), "ASISTENCIA"] = 1
        df_raw.loc[no_asisten, "ASISTENCIA"] = 0
    else:
        df_raw.loc[participantes, "ASISTENCIA"] = 1

# === EVENTOS GRATUITOS
eventos_gratis = df_raw[df_raw["PAGO"] == 0]["NOMBRE_EVENTO"].unique()
for evento in eventos_gratis:
    participantes = df_raw[(df_raw["NOMBRE_EVENTO"] == evento)].index.tolist()
    if not participantes:
        continue
    num_fallos = max(1, int(0.10 * len(participantes)))
    no_asisten = np.random.choice(participantes, size=min(len(participantes), num_fallos), replace=False)
    df_raw.loc[list(set(participantes) - set(no_asisten)), "ASISTENCIA"] = 1
    df_raw.loc[no_asisten, "ASISTENCIA"] = 0

# Convertir a entero por si acaso
df_raw["ASISTENCIA"] = df_raw["ASISTENCIA"].fillna(0).astype(int)

# === 🧾 Agrupación por evento
df = df_raw.groupby(
    ["NOMBRE_EVENTO", "FECHA_EVENTO", "COMUNIDAD", "ARCHIVO_ORIGEN", "COSTE_UNITARIO"], as_index=False
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

# === 📆 Variables temporales
df["DIA_MES"] = df["FECHA_EVENTO"].dt.day
df["SEMANA_MES"] = df["FECHA_EVENTO"].dt.isocalendar().week
df["MES"] = df["FECHA_EVENTO"].dt.month
df["DIA_SEMANA"] = df["FECHA_EVENTO"].dt.day_name()
df["AÑO"] = df["FECHA_EVENTO"].dt.year
df["DIA_SEMANA_NUM"] = df["FECHA_EVENTO"].dt.dayofweek

# === ☀️ Temporada
def obtener_temporada(mes):
    if mes in [12, 1, 2]:
        return "invierno"
    elif mes in [3, 4, 5]:
        return "primavera"
    elif mes in [6, 7, 8]:
        return "verano"
    else:
        return "otoño"

df["TEMPORADA"] = df["MES"].apply(obtener_temporada)

# === 💸 Precio medio, costes, beneficio
df["PRECIO_MEDIO"] = np.where(df["NUM_PAGOS"] > 0, df["TOTAL_RECAUDADO"] / df["NUM_PAGOS"], 0)
df["COSTE_UNITARIO"] = pd.to_numeric(df["COSTE_UNITARIO"], errors="coerce").fillna(0)
df["COSTE_ESTIMADO"] = df["COSTE_UNITARIO"] * df["NUM_INSCRITAS"]
df["BENEFICIO_ESTIMADO"] = df["TOTAL_RECAUDADO"] - df["COSTE_ESTIMADO"]

# === 🎯 Clasificación
df["EVENTO_GRATUITO"] = np.where(df["PRECIO_MEDIO"] == 0, 1, 0)
df["TIPO_EVENTO"] = np.where(df["EVENTO_GRATUITO"] == 1, "gratuito", "pago")
df["COLABORACION"] = 0

# === 🔠 Limpieza nombre para merge
def limpiar_evento(nombre):
    nombre = str(nombre).strip().lower()
    nombre = unicodedata.normalize('NFKD', nombre).encode('ascii', errors='ignore').decode('utf-8')
    return nombre

df["EVENTO_LIMPIO"] = df["NOMBRE_EVENTO"].apply(limpiar_evento)

# === 📘 Cargar o crear archivo de tipos
if TIPOS_PATH.exists():
    df_tipos = pd.read_csv(TIPOS_PATH)
    if "EVENTO_LIMPIO" not in df_tipos.columns:
        df_tipos["EVENTO_LIMPIO"] = df_tipos["EVENTO"].apply(limpiar_evento)
else:
    df_tipos = df[["NOMBRE_EVENTO", "EVENTO_LIMPIO"]].drop_duplicates()
    df_tipos["TIPO_ACTIVIDAD"] = "otro"
    df_tipos = df_tipos.rename(columns={"NOMBRE_EVENTO": "EVENTO"})
    df_tipos.to_csv(TIPOS_PATH, index=False)
    print(f"📄 Archivo creado automáticamente: {TIPOS_PATH.resolve()}")
    print("✍️ Rellena manualmente la columna 'TIPO_ACTIVIDAD' con: almuerzo, charla, deportiva, ludica, only run, otro")

# === 🔁 Merge final
df = df.merge(df_tipos[["EVENTO_LIMPIO", "TIPO_ACTIVIDAD"]], on="EVENTO_LIMPIO", how="left")
df["TIPO_ACTIVIDAD"] = df["TIPO_ACTIVIDAD"].fillna("otro")
df.drop(columns=["EVENTO_LIMPIO"], inplace=True)

# === 💾 Guardar
df.to_csv(OUTPUT, index=False)
print(f"✅ Dataset generado correctamente con {len(df)} eventos.")
print(f"📍 Guardado en: {OUTPUT}")
