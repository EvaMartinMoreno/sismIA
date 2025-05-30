import pandas as pd
from sklearn.preprocessing import MinMaxScaler
import matplotlib.pyplot as plt
import seaborn as sns

# === CARGA DE DATOS ===
df_real = pd.read_csv("stats/dataset_modelo.csv", parse_dates=["FECHA_EVENTO"])
df_fake = pd.read_csv("stats/eventos_simulados_girona.csv", parse_dates=["FECHA_EVENTO"])

# === MARCAR ORIGEN DE DATOS ===
df_real["REAL"] = 1
df_fake["REAL"] = 0

# === UNIFICAR ===
df = pd.concat([df_real, df_fake], ignore_index=True)

# === ELIMINAR COLUMNAS INÚTILES ===
df.drop(columns=["NOMBRE_EVENTO", "NUM_INSCRITAS"], inplace=True)

# === CREAR EVENTO_GRATUITO A PARTIR DE TOTAL_RECAUDADO ===
# 1 = de pago, 0 = gratuito
df["EVENTO_GRATUITO"] = (df["TOTAL_RECAUDADO"] > 0).astype(int)

# === FILTRAR SOLO EVENTOS DE PAGO ===
df = df[df["EVENTO_GRATUITO"] == 1].copy()

# === ONE-HOT ENCODING ===
df = pd.get_dummies(df, columns=["COMUNIDAD", "DIA_SEMANA", "MES", "TIPO_EVENTO"], drop_first=True, dtype=int)

# === NORMALIZAR VARIABLES NUMÉRICAS ===
cols_a_normalizar = [
    'NUM_PAGOS',
    'TOTAL_RECAUDADO',
    'COSTE_ESTIMADO',
    'BENEFICIO_ESTIMADO',
    'SEMANA'
]

scaler = MinMaxScaler()
df[cols_a_normalizar] = scaler.fit_transform(df[cols_a_normalizar])

# === FORZAR TIPO NUMÉRICO 0/1 POR SI QUEDA ALGÚN BOOLEANO SUELTO ===
df = df.applymap(lambda x: int(x) if isinstance(x, bool) else x)

# === GUARDAR RESULTADO FINAL ===
df.to_csv("stats/dataset_entrenamiento_pago.csv", index=False)
print("✅ Dataset de eventos de pago guardado como 'dataset_entrenamiento_pago.csv'.")

# === VISUALIZACIÓN DE VARIABLES NORMALIZADAS ===
plt.figure(figsize=(15, 10))
for i, col in enumerate(cols_a_normalizar):
    plt.subplot(2, 3, i+1)
    df[col].hist(bins=30, edgecolor='black')
    plt.title(f'Distribución de {col} (solo pago)')
    plt.xlabel(col)
    plt.ylabel('Frecuencia')
    plt.grid(False)

plt.tight_layout()
plt.show()

# === VISUALIZACIÓN DE OUTLIERS POR MES ===

variables = [
    'NUM_PAGOS',
    'TOTAL_RECAUDADO',
    'COSTE_ESTIMADO',
    'BENEFICIO_ESTIMADO',
    'NUM_ASISTENCIAS'
]

plt.figure(figsize=(15, 10))
for i, col in enumerate(variables):
    plt.subplot(2, 3, i+1)
    sns.boxplot(x=df[col])
    plt.title(f'Boxplot de {col}')
    plt.grid(True)

plt.tight_layout()
plt.show()

# === MATRIZ DE CORRELACIÓN NUMÉRICA ===
correlaciones = df.corr(numeric_only=True)

# === HEATMAP ===
plt.figure(figsize=(16, 12))
sns.heatmap(correlaciones, annot=True, fmt=".2f", cmap="coolwarm", square=True, linewidths=0.5)
plt.title("🔍 Matriz de correlación entre variables (solo eventos de pago)", fontsize=16)
plt.xticks(rotation=45, ha='right')
plt.yticks(rotation=0)
plt.tight_layout()
plt.show()
