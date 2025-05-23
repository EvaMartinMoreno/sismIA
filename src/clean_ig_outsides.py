import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from glob import glob

# === 1. Cargar todos los CSVs ===
carpeta_csvs = "data/raw/externos"
csv_files = glob(os.path.join(carpeta_csvs, "instagram_*.csv"))

df_total = pd.concat([
    pd.read_csv(f).assign(cuenta=os.path.basename(f).replace("instagram_", "").replace(".csv", ""))
    for f in csv_files
], ignore_index=True)

# === 2. Limpiar tipos y calcular engagement ===
df_total["fecha"] = pd.to_datetime(df_total["fecha"], errors='coerce')
df_total["likes"] = pd.to_numeric(df_total["likes"], errors='coerce')
df_total["comentarios"] = pd.to_numeric(df_total["comentarios"], errors='coerce')
df_total["engagement"] = df_total["likes"].fillna(0) + df_total["comentarios"].fillna(0)

df_total["texto_largo"] = df_total["texto"].fillna("").apply(lambda x: len(x.split()))
df_total["engagement_por_palabra"] = df_total["engagement"] / df_total["texto_largo"].replace(0, 1)

# === 3. Extraer hora y día de la semana en español ===
df_total["hora"] = df_total["fecha"].dt.hour
df_total["dia_semana"] = df_total["fecha"].dt.day_name(locale='es_ES.utf8')
df_total["dia_semana"] = df_total["dia_semana"].str.capitalize()

# Vista previa
print(df_total.head())

# === 4. Gráficos ===

# Orden correcto de los días en español
orden_dias_es = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

# --- Análisis 1: Nº de publicaciones por día ---
plt.figure(figsize=(10, 4))
sns.countplot(x="dia_semana", data=df_total, order=orden_dias_es)
plt.title("Nº de publicaciones por día de la semana")
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()

# --- Análisis 2: Engagement medio por día ---
df_total.groupby("dia_semana")["engagement"].mean().reindex(orden_dias_es).plot(
    kind="bar", figsize=(10, 4), title="Engagement medio por día de la semana", color="skyblue"
)
plt.ylabel("Engagement")
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()

# --- Análisis 3: Engagement medio por hora ---
df_total.groupby("hora")["engagement"].mean().plot(
    kind="line", marker="o", title="Engagement medio por hora de publicación"
)
plt.xlabel("Hora")
plt.ylabel("Engagement")
plt.grid(True)
plt.tight_layout()
plt.show()

# --- Análisis 4: Tipo de post vs engagement ---
sns.boxplot(data=df_total, x="tipo", y="engagement")
plt.title("Tipo de post vs engagement")
plt.tight_layout()
plt.show()