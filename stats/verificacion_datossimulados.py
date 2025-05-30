import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import mean_absolute_error, mean_squared_error
from pathlib import Path
import numpy as np

# === CARGA DE DATOS ===
archivo_simulado = Path("stats/eventos_simulados_girona.csv")
archivo_real = Path("stats/dataset_modelo.csv")

df_sim = pd.read_csv(archivo_simulado, parse_dates=["FECHA_EVENTO"])
df_real = pd.read_csv(archivo_real, parse_dates=["FECHA_EVENTO"])

# === FILTRAMOS SOLO GIRONA y EVENTOS DE PAGO ===
df_sim = df_sim[(df_sim["COMUNIDAD"].str.upper() == "GIRONA") & (df_sim["TIPO_EVENTO"] == "pago")]
df_real = df_real[(df_real["COMUNIDAD"].str.upper() == "GIRONA") & (df_real["TIPO_EVENTO"] == "pago")]

# Añadir columna MES
df_sim["MES"] = df_sim["FECHA_EVENTO"].dt.to_period("M").dt.to_timestamp()
df_real["MES"] = df_real["FECHA_EVENTO"].dt.to_period("M").dt.to_timestamp()

# Agrupar por MES y calcular media mensual
sim_mensual = df_sim.groupby("MES")["NUM_ASISTENCIAS"].mean().reset_index()
real_mensual = df_real.groupby("MES")["NUM_ASISTENCIAS"].mean().reset_index()

# === COMPARACIÓN DE DATOS ===
df_comparado = pd.merge(sim_mensual, real_mensual, on="MES", how="inner", suffixes=("_sim", "_real"))

# Calcular métricas de error
mae = mean_absolute_error(df_comparado["NUM_ASISTENCIAS_real"], df_comparado["NUM_ASISTENCIAS_sim"])
rmse = np.sqrt(mean_squared_error(df_comparado["NUM_ASISTENCIAS_real"], df_comparado["NUM_ASISTENCIAS_sim"]))

print(f"📉 Margen de error:")
print(f"MAE (Error absoluto medio): {mae:.2f}")
print(f"RMSE (Raíz cuadrada del error cuadrático medio): {rmse:.2f}")

# === VISUALIZACIÓN COMPLETA ===
# Añadir columna para distinguir tipo
df_sim["TIPO"] = "simulado"
df_real["TIPO"] = "real"

df_union = pd.concat([df_sim, df_real], ignore_index=True)
df_union_grouped = df_union.groupby(["MES", "TIPO"])["NUM_ASISTENCIAS"].mean().reset_index()

# Plot
plt.figure(figsize=(12, 6))
sns.lineplot(data=df_union_grouped, x="MES", y="NUM_ASISTENCIAS", hue="TIPO", marker="o")
plt.title("📈 Evolución mensual de asistentes en Girona (eventos de pago)")
plt.xlabel("Mes del evento")
plt.ylabel("Media de asistentes por evento")
plt.xticks(rotation=45)
plt.grid(True)
plt.tight_layout()
plt.show()
