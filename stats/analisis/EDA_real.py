import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from sklearn.linear_model import LinearRegression
from dateutil.relativedelta import relativedelta


# Semilla para reproducibilidad
# === CONFIGURACIÓN INICIAL ===
sns.set_theme(style="whitegrid")
plt.rcParams["figure.figsize"] = (10, 6)

# === CARGA DE DATOS ===
ruta_csv = Path("data/clean/dataset_modelo.csv")
df = pd.read_csv(ruta_csv)
df["FECHA_EVENTO"] = pd.to_datetime(df["FECHA_EVENTO"], errors="coerce")

# === NUEVAS VARIABLES CALCULADAS ===
df["TASA_ASISTENCIA"] = (df["NUM_ASISTENCIAS"] / df["NUM_INSCRITAS"]).fillna(0).clip(0, 1)
df["INGRESO_POR_ASISTENTE"] = (df["TOTAL_RECAUDADO"] / df["NUM_ASISTENCIAS"]).replace([np.inf, -np.inf], 0).fillna(0)

# === ANÁLISIS ESTADÍSTICO ===
eventos_por_mes = df.groupby(["COMUNIDAD", "TIPO_EVENTO", "MES"]).size().reset_index(name="NUM_EVENTOS")
mes_mas_eventos = eventos_por_mes.sort_values("NUM_EVENTOS", ascending=False).groupby(["COMUNIDAD", "TIPO_EVENTO"]).first().reset_index()
estadisticas = df.groupby(["COMUNIDAD", "TIPO_EVENTO"]).agg({
    "NUM_ASISTENCIAS": "mean",
    "BENEFICIO_ESTIMADO": "mean",
    "NUM_INSCRITAS": "mean",
    "NUM_PAGOS": "mean",
    "TOTAL_RECAUDADO": "mean"
}).reset_index()
eventos_totales = df.groupby(["COMUNIDAD", "TIPO_EVENTO"]).size().reset_index(name="TOTAL_EVENTOS")
eventos_por_dia = df.groupby(["COMUNIDAD", "TIPO_EVENTO", "DIA_SEMANA"]).size().reset_index(name="NUM_EVENTOS")
evento_max_asistencia = df.loc[df["NUM_ASISTENCIAS"].idxmax()][["NOMBRE_EVENTO", "COMUNIDAD", "TIPO_EVENTO", "NUM_ASISTENCIAS"]]
eventos_deficitarios = df[df["BENEFICIO_ESTIMADO"] <= 0]
eventos_baja_asistencia = df[df["TASA_ASISTENCIA"] < 0.5]
eventos_cero_asistencia = df[df["NUM_ASISTENCIAS"] == 0]

# === RESULTADOS POR TERMINAL ===
print("\nEventos por mes:\n", eventos_por_mes)
print("\nMes con más eventos por grupo:\n", mes_mas_eventos)
print("\nEstadísticas medias:\n", estadisticas)
print("\nTotal de eventos por grupo:\n", eventos_totales)
print("\nEventos por día de la semana:\n", eventos_por_dia)
print("\nEvento con más asistentes:\n", evento_max_asistencia.to_string())
print("\nEventos deficitarios (primeros 10):\n", eventos_deficitarios.head(10))
print("\nEventos con baja asistencia (<50%) (primeros 10):\n", eventos_baja_asistencia.head(10))
print("\nEventos con 0 asistentes (primeros 10):\n", eventos_cero_asistencia.head(10))

# === GRÁFICOS ===
# 1. Eventos por mes
plt.figure()
sns.countplot(data=df, x="MES", hue="COMUNIDAD")
plt.title("Número de eventos por mes y comunidad")
plt.tight_layout()
plt.show()

# 2. Asistencias por tipo de evento
plt.figure()
sns.boxplot(data=df, x="TIPO_EVENTO", y="NUM_ASISTENCIAS", hue="COMUNIDAD")
plt.title("Distribución de asistentes por tipo de evento")
plt.tight_layout()
plt.show()

# 3. Beneficio vs asistentes
plt.figure()
sns.scatterplot(data=df, x="NUM_ASISTENCIAS", y="BENEFICIO_ESTIMADO", hue="COMUNIDAD", style="TIPO_EVENTO")
plt.title("Relación entre asistentes y beneficio")
plt.tight_layout()
plt.show()

# 4. Tasa de asistencia por comunidad
plt.figure()
sns.boxplot(data=df, x="COMUNIDAD", y="TASA_ASISTENCIA", hue="TIPO_EVENTO")
plt.title("Tasa de asistencia por comunidad y tipo")
plt.tight_layout()
plt.show()

# 5. Ingreso por asistente
plt.figure()
sns.histplot(data=df[df["INGRESO_POR_ASISTENTE"] > 0], x="INGRESO_POR_ASISTENTE", bins=30, kde=True)
plt.title("Distribución de ingreso por asistente")
plt.tight_layout()
plt.show()

# === EVOLUCIÓN MENSUAL DE ASISTENTES EN GIRONA (con eliminación de outliers) ===
df_girona = df[df["COMUNIDAD"].str.upper() == "GIRONA"].copy()
df_girona = df_girona[df_girona["NUM_ASISTENCIAS"] > 0]

if df_girona.empty:
    print("⚠️ No hay eventos válidos para Girona con asistentes.")
else:
    df_girona["MES"] = df_girona["FECHA_EVENTO"].dt.to_period("M")
    asistencias_girona = df_girona.groupby("MES")["NUM_ASISTENCIAS"].mean().reset_index()
    asistencias_girona["MES"] = asistencias_girona["MES"].dt.to_timestamp()

    # Eliminar outliers con método IQR
    Q1 = asistencias_girona["NUM_ASISTENCIAS"].quantile(0.25)
    Q3 = asistencias_girona["NUM_ASISTENCIAS"].quantile(0.75)
    IQR = Q3 - Q1
    filtro_outliers = (asistencias_girona["NUM_ASISTENCIAS"] >= Q1 - 1.5 * IQR) & (asistencias_girona["NUM_ASISTENCIAS"] <= Q3 + 1.5 * IQR)
    asistencias_girona = asistencias_girona[filtro_outliers]

    # Calcular edad en meses
    mes_inicio = asistencias_girona["MES"].iloc[0]
    asistencias_girona["EDAD_MESES"] = asistencias_girona["MES"].apply(
        lambda fecha: (fecha.year - mes_inicio.year) * 12 + (fecha.month - mes_inicio.month)
    )

    # Ajustar modelo lineal
    X = asistencias_girona["EDAD_MESES"].values.reshape(-1, 1)
    y = asistencias_girona["NUM_ASISTENCIAS"].values
    modelo_girona = LinearRegression().fit(X, y)

    # Visualizar crecimiento
    plt.figure()
    sns.scatterplot(data=asistencias_girona, x="EDAD_MESES", y="NUM_ASISTENCIAS", label="Asistencia real")
    plt.plot(asistencias_girona["EDAD_MESES"], modelo_girona.predict(X), color="red", label="Regresión (modelo)")
    plt.title("Crecimiento de asistentes en Girona por mes (sin outliers)")
    plt.xlabel("Edad en meses")
    plt.ylabel("Asistencias medias")
    plt.legend()
    plt.tight_layout()
    plt.show()

# === EVOLUCIÓN DE EVENTOS DE PAGO EN GIRONA ===
df_girona_pago = df[
    (df["COMUNIDAD"] == "GIRONA") &
    (df["TIPO_EVENTO"] == "pago") &
    (df["NUM_ASISTENCIAS"] > 0)
].copy()

df_girona_pago["MES"] = df_girona_pago["FECHA_EVENTO"].dt.to_period("M")
asistencias_pago = df_girona_pago.groupby("MES")["NUM_ASISTENCIAS"].mean().reset_index()
asistencias_pago["MES"] = asistencias_pago["MES"].dt.to_timestamp()

mes_inicio = asistencias_pago["MES"].iloc[0]
asistencias_pago["EDAD_MESES"] = asistencias_pago["MES"].apply(
    lambda fecha: (fecha.year - mes_inicio.year) * 12 + (fecha.month - mes_inicio.month)
)

X = asistencias_pago["EDAD_MESES"].values.reshape(-1, 1)
y = asistencias_pago["NUM_ASISTENCIAS"].values
modelo_pago = LinearRegression().fit(X, y)

plt.figure()
sns.scatterplot(data=asistencias_pago, x="EDAD_MESES", y="NUM_ASISTENCIAS", label="Datos reales (pago)")
plt.plot(asistencias_pago["EDAD_MESES"], modelo_pago.predict(X), color="red", label="Tendencia (pago)")
plt.title("📈 Evolución de asistentes en eventos de pago - Girona")
plt.xlabel("Edad en meses desde primer evento")
plt.ylabel("Media de asistentes por mes")
plt.legend()
plt.tight_layout()
plt.show()

# === EVOLUCIÓN MENSUAL DE ASISTENTES EN ELCHE (con eliminación de outliers) ===
df_elche = df[df["COMUNIDAD"].str.upper() == "ELCHE"].copy()
df_elche = df_elche[df_elche["NUM_ASISTENCIAS"] > 0]

if df_elche.empty:
    print("⚠️ No hay eventos válidos para Elche con asistentes.")
else:
    df_elche["MES"] = df_elche["FECHA_EVENTO"].dt.to_period("M")
    asistencias_elche = df_elche.groupby("MES")["NUM_ASISTENCIAS"].mean().reset_index()
    asistencias_elche["MES"] = asistencias_elche["MES"].dt.to_timestamp()

    # Eliminar outliers con método IQR
    Q1 = asistencias_elche["NUM_ASISTENCIAS"].quantile(0.25)
    Q3 = asistencias_elche["NUM_ASISTENCIAS"].quantile(0.75)
    IQR = Q3 - Q1
    filtro_outliers = (asistencias_elche["NUM_ASISTENCIAS"] >= Q1 - 1.5 * IQR) & (asistencias_elche["NUM_ASISTENCIAS"] <= Q3 + 1.5 * IQR)
    asistencias_elche = asistencias_elche[filtro_outliers]

    # Calcular edad en meses
    mes_inicio_elche = asistencias_elche["MES"].iloc[0]
    asistencias_elche["EDAD_MESES"] = asistencias_elche["MES"].apply(
        lambda fecha: (fecha.year - mes_inicio_elche.year) * 12 + (fecha.month - mes_inicio_elche.month)
    )

    # Ajustar modelo de regresión lineal
    X = asistencias_elche["EDAD_MESES"].values.reshape(-1, 1)
    y = asistencias_elche["NUM_ASISTENCIAS"].values
    modelo_elche = LinearRegression().fit(X, y)

    # Visualización
    plt.figure()
    sns.scatterplot(data=asistencias_elche, x="EDAD_MESES", y="NUM_ASISTENCIAS", label="Asistencia real")
    plt.plot(asistencias_elche["EDAD_MESES"], modelo_elche.predict(X), color="red", label="Regresión (modelo)")
    plt.title("Crecimiento de asistentes en Elche por mes (sin outliers)")
    plt.xlabel("Edad en meses")
    plt.ylabel("Asistencias medias")
    plt.legend()
    plt.tight_layout()
    plt.show()

# === 🔍 Distribución colaboración y tipos de actividad en eventos de pago de GIRONA ===
df_girona_pago = df[(df["COMUNIDAD"].str.upper() == "GIRONA") & (df["TIPO_EVENTO"] == "pago")]

# Porcentaje de colaboración
porcentaje_colaboracion = df_girona_pago["COLABORACION"].value_counts(normalize=True) * 100
print("\n📊 Porcentaje de eventos con/sin colaboración (GIRONA - Pago):")
print(porcentaje_colaboracion.rename({0: "Sin colaboración", 1: "Con colaboración"}).round(2))

# Distribución de tipo de actividad
df_girona_pago["TIPO_ACTIVIDAD"] = df_girona_pago["TIPO_ACTIVIDAD"].astype(str).str.strip().str.lower()
distribucion_actividad = df_girona_pago["TIPO_ACTIVIDAD"].value_counts(normalize=True) * 100
print("\n📊 Distribución de tipos de actividad (GIRONA - Pago):")
print(distribucion_actividad.round(2))

