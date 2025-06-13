# src/cleaning/limpieza_eventos_athletiks.py

from pathlib import Path
import pandas as pd
import numpy as np
import unicodedata
import os

def limpiar_evento(nombre):
    nombre = str(nombre).strip().lower()
    nombre = unicodedata.normalize('NFKD', nombre).encode('ascii', errors='ignore').decode('utf-8')
    return nombre

def obtener_temporada(mes):
    return ["invierno", "primavera", "verano", "otoño"][(mes % 12) // 3]

def cargar_csvs_en_uno(directorio):
    archivos = list(Path(directorio).rglob("*.csv"))
    dfs = []
    for archivo in archivos:
        try:
            df = pd.read_csv(archivo, sep=",", engine="python")
            df["ARCHIVO_ORIGEN"] = archivo.name
            dfs.append(df)
        except Exception as e:
            print(f"⚠️ Error leyendo {archivo.name}: {e}")
    if not dfs:
        raise ValueError("No se pudieron leer archivos válidos.")
    return pd.concat(dfs, ignore_index=True)

def generar_dataset_modelo(input_dir, output_path):
    df_raw = cargar_csvs_en_uno(input_dir)
    df_raw["FECHA_EVENTO"] = pd.to_datetime(df_raw["FECHA_EVENTO"], errors="coerce")
    df_raw = df_raw.dropna(subset=["FECHA_EVENTO"])
    df_raw["PAGO"] = pd.to_numeric(df_raw["PAGO"], errors="coerce").fillna(0).astype(int)
    df_raw["ASISTENCIA"] = np.nan
    df_raw["PRECIO_PAGADO"] = pd.to_numeric(df_raw["PRECIO_PAGADO"], errors="coerce").fillna(0)

    df_raw.loc[df_raw["PAGO"] == 1, "ASISTENCIA"] = 1
    df_raw.loc[df_raw["PAGO"] == 0, "ASISTENCIA"] = 1
    df_raw["ASISTENCIA"] = df_raw["ASISTENCIA"].fillna(0).astype(int)

    df = df_raw.groupby(
        ["NOMBRE_EVENTO", "FECHA_EVENTO", "COMUNIDAD", "ARCHIVO_ORIGEN"], as_index=False
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

    df["DIA_MES"] = df["FECHA_EVENTO"].dt.day
    df["SEMANA_MES_AÑO"] = df["FECHA_EVENTO"].dt.isocalendar().week
    df["SEMANA_DENTRO_DEL_MES"] = (df["FECHA_EVENTO"].dt.day - 1) // 7 + 1
    df["MES"] = df["FECHA_EVENTO"].dt.month
    df["DIA_SEMANA"] = df["FECHA_EVENTO"].dt.day_name()
    df["AÑO"] = df["FECHA_EVENTO"].dt.year
    df["DIA_SEMANA_NUM"] = df["FECHA_EVENTO"].dt.dayofweek
    df["TEMPORADA"] = df["MES"].apply(obtener_temporada)
    df["PRECIO_MEDIO"] = np.where(df["NUM_PAGOS"] > 0, df["TOTAL_RECAUDADO"] / df["NUM_PAGOS"], 0)
    df["EVENTO_GRATUITO"] = np.where(df["PRECIO_MEDIO"] == 0, 1, 0)
    df["TIPO_EVENTO"] = np.where(df["EVENTO_GRATUITO"] == 1, "gratuito", "pago")

    columnas_manuales = ["COSTE_UNITARIO", "COSTE_UNITARIO_VALIDADO", "COLABORACION", "TIPO_ACTIVIDAD"]
    if os.path.exists(output_path):
        try:
            df_validados = pd.read_csv(output_path)
            df = pd.merge(
                df,
                df_validados[["NOMBRE_EVENTO", "FECHA_EVENTO"] + columnas_manuales],
                on=["NOMBRE_EVENTO", "FECHA_EVENTO"],
                how="left"
            )
        except:
            for col in columnas_manuales:
                df[col] = np.nan if "COSTE" in col or "COLAB" in col else ""

    else:
        for col in columnas_manuales:
            df[col] = np.nan if "COSTE" in col or "COLAB" in col else ""

    df.to_csv(output_path, index=False)
    print(f"✅ Dataset generado correctamente con {len(df)} eventos.")
    print(f"📁 Guardado en: {output_path}")

if __name__ == "__main__":
    generar_dataset_modelo(
        input_dir="data/raw/athletiks",
        output_path="data/raw/dataset_modelo.csv"
    )
