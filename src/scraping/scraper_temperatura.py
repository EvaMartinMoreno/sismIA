from meteostat import Point, Daily
import pandas as pd
import numpy as np
from datetime import datetime
from tqdm import tqdm
import time
from pathlib import Path

# Coordenadas de Girona
punto_estacion = Point(41.9794, 2.8214)

# Paths
REAL_PATH = Path("data/raw/dataset_modelo_validado.csv")
SIM_PATH = Path("data/raw/simulacion_datos_girona.csv")

def necesita_temperatura(path: Path) -> bool:
    if not path.exists():
        return False
    df = pd.read_csv(path, parse_dates=["FECHA_EVENTO"])
    hoy = pd.Timestamp.today().normalize()
    if "TEMPERATURA" not in df.columns:
        return True
    # Comprueba si hay fechas pasadas sin temperatura
    return df[(df["FECHA_EVENTO"] < hoy) & (df["TEMPERATURA"].isna())].shape[0] > 0

def añadir_temperatura_a_csv(path: Path, ciudad_point: Point, verbose: str):
    df = pd.read_csv(path)
    df["FECHA_EVENTO"] = pd.to_datetime(df["FECHA_EVENTO"], errors="coerce")
    if "TEMPERATURA" not in df.columns:
        df["TEMPERATURA"] = np.nan

    hoy = pd.Timestamp.today().normalize()

    for idx, row in tqdm(df.iterrows(), total=len(df), desc=f"{verbose}: Añadiendo temperatura"):
        fecha = row["FECHA_EVENTO"]
        if pd.isna(row["TEMPERATURA"]) and pd.notna(fecha) and fecha < hoy:
            try:
                data = Daily(ciudad_point, fecha, fecha).fetch()
                if not data.empty and "tavg" in data.columns:
                    df.at[idx, "TEMPERATURA"] = data["tavg"].values[0]
                else:
                    print(f"⚠️ No hay datos disponibles para {fecha.date()}")
            except Exception as e:
                print(f"❌ Error en {fecha.date()}: {e}")
            time.sleep(1.2)  # Evita bloqueo

    df.to_csv(path, index=False)
    print(f"✅ {verbose}: Temperatura añadida y guardada en {path.name}")

# === EJECUCIÓN DIRECTA AL LLAMAR EL SCRIPT DESDE TERMINAL
print("🌡️ Comprobando si se necesita añadir temperatura...")

if necesita_temperatura(REAL_PATH):
    print("🌡️ Añadiendo temperatura a datos REALES...")
    añadir_temperatura_a_csv(REAL_PATH, punto_estacion, "Reales")
else:
    print("✅ Datos REALES ya tienen temperatura.")

if necesita_temperatura(SIM_PATH):
    print("🌡️ Añadiendo temperatura a datos SIMULADOS...")
    añadir_temperatura_a_csv(SIM_PATH, punto_estacion, "Simulados")
else:
    print("✅ Datos SIMULADOS ya tienen temperatura.")
