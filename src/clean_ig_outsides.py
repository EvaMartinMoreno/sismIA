import os
import pandas as pd
from glob import glob

# Ruta donde se han guardado los CSVs
carpeta_csvs = "data/raw/externos"
csv_files = glob(os.path.join(carpeta_csvs, "instagram_*.csv"))

# Cargar todos los archivos con una columna extra de cuenta (extraída del nombre del archivo)
df_total = pd.concat([
    pd.read_csv(f).assign(cuenta=os.path.basename(f).replace("instagram_", "").replace(".csv", ""))
    for f in csv_files
], ignore_index=True)

# Asegurar tipos
df_total["fecha"] = pd.to_datetime(df_total["fecha"], errors='coerce')
df_total["likes"] = pd.to_numeric(df_total["likes"], errors='coerce')
df_total["comentarios"] = pd.to_numeric(df_total["comentarios"], errors='coerce')

# Engagement total
df_total["engagement"] = df_total["likes"].fillna(0) + df_total["comentarios"].fillna(0)

# Engagement por palabra del texto
df_total["texto_largo"] = df_total["texto"].fillna("").apply(lambda x: len(x.split()))
df_total["engagement_por_palabra"] = df_total["engagement"] / df_total["texto_largo"].replace(0, 1)

# Vista previa del DataFrame
print(df_total.head())

# Guardar dataset consolidado
df_total.to_csv("data/processed/instagram_analisis_engagement.csv", index=False, encoding="utf-8")
print("✅ Archivo combinado y guardado en data/processed/instagram_analisis_engagement.csv")
