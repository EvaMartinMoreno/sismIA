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
REAL_PATH = Path("data/clean/dataset_modelo.csv")
SIM_PATH = Path("data/raw/simulacion_datos_girona.csv")
REAL_OUTPUT = Path("data/clean/dataset_modelo.csv")  # Sobrescribe
SIM_OUTPUT = Path("data/clean/simulacion_datos_girona.csv")

# Función para añadir temperatura
def añadir_temperatura(df: pd.DataFrame, ciudad_point: Point, verbose: str) -> pd.DataFrame:
    df["FECHA_EVENTO"] = pd.to_datetime(df["FECHA_EVENTO"], errors="coerce")
    df["TEMPERATURA"] = np.nan

    for idx, row in tqdm(df.iterrows(), total=len(df), desc=f"{verbose}: Añadiendo temperatura"):
        fecha = row["FECHA_EVENTO"]
        if pd.notnull(fecha):
            try:
                data = Daily(ciudad_point, fecha, fecha).fetch()
                if not data.empty and "tavg" in data.columns:
                    df.at[idx, "TEMPERATURA"] = data["tavg"].values[0]
                else:
                    print(f" No hay datos disponibles para {fecha.date()}")
            except Exception as e:
                print(f" Error en {fecha.date()}: {e}")
            time.sleep(1.2)
    return df

# Ejecutar
if __name__ == "__main__":
    df_real = pd.read_csv(REAL_PATH)
    df_real = añadir_temperatura(df_real, punto_estacion, "Reales")
    df_real.to_csv(REAL_OUTPUT, index=False)
    print("Dataset real actualizado con temperatura.")

    df_sim = pd.read_csv(SIM_PATH)
    df_sim = añadir_temperatura(df_sim, punto_estacion, "Simulados")
    df_sim.to_csv(SIM_OUTPUT, index=False)
    print(" Dataset simulado actualizado con temperatura.")
