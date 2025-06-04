import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.model_selection import GridSearchCV
import matplotlib.pyplot as plt

# === CARGA DE DATOS ===
df_real = pd.read_csv("stats/dataset_modelo.csv", parse_dates=["FECHA_EVENTO"])
df_fake = pd.read_csv("stats/eventos_simulados_girona.csv", parse_dates=["FECHA_EVENTO"])

df_real["REAL"] = 1
df_fake["REAL"] = 0

df = pd.concat([df_real, df_fake], ignore_index=True)
df = df[df["TOTAL_RECAUDADO"] > 0].copy()  # solo eventos de pago en Girona

# === VARIABLES PRE-EVENTO ===
vars_previas = [
    "COSTE_ESTIMADO", "SEMANA", "DIA_SEMANA", "MES", "TIPO_EVENTO", "COMUNIDAD"
]

df_cluster = df[vars_previas].copy()

# === TRANSFORMACIÓN CATEGÓRICAS ===
df_cluster = pd.get_dummies(df_cluster, columns=["DIA_SEMANA", "MES", "TIPO_EVENTO", "COMUNIDAD"], drop_first=True)

# === ESCALADO ===
scaler = StandardScaler()
X_scaled = scaler.fit_transform(df_cluster)

# === DEFINICIÓN DE SCORER PARA GRIDSEARCH ===
def my_silhouette_scorer(estimator, X):
    labels = estimator.fit_predict(X)
    return silhouette_score(X, labels) if len(set(labels)) > 1 else float('nan')

# === GRIDSEARCH CON DIFERENTES CONFIGURACIONES ===
param_grid = {
    'n_clusters': list(range(2, 10)),
    'init': ['k-means++', 'random'],
    'n_init': [10, 20],
    'max_iter': [300, 500]
}

kmeans = KMeans(random_state=42)
grid_search = GridSearchCV(
    estimator=kmeans,
    param_grid=param_grid,
    scoring=my_silhouette_scorer,
    cv=3,
    verbose=2,
    n_jobs=-1
)

grid_search.fit(X_scaled)

# === MEJOR RESULTADO ===
print("\n🧠 Mejor configuración encontrada:")
print(grid_search.best_params_)
print("\n🏆 Mejor silhouette score:")
print(grid_search.best_score_)

# === USAMOS EL MEJOR MODELO ===
best_kmeans = grid_search.best_estimator_
df["CLUSTER_EVENTO"] = best_kmeans.predict(X_scaled)

# === PERFILADO DE CLÚSTERES ===
print("\n🎯 Perfil de cada clúster:")
print(df.groupby("CLUSTER_EVENTO")[["NUM_ASISTENCIAS", "TOTAL_RECAUDADO", "COSTE_ESTIMADO"]].mean())

# === GUARDAR CSV ===
df.to_csv("stats/dataset_modelo_clusterizado_v2.csv",index=False)
print("\n💾 Archivo guardado: stats/dataset_modelo_clusterizado_v2.csv")

# === ANÁLISIS POR CLÚSTER ===
import seaborn as sns

# === TIPO DE EVENTO POR CLÚSTER ===
print("🎯 Tipo de evento por clúster:")
print(df.groupby("CLUSTER_EVENTO")["TIPO_EVENTO"].value_counts().unstack(fill_value=0))

# === EVENTOS REALES VS SIMULADOS POR CLÚSTER ===
print("\n🧪 Eventos reales (1) vs simulados (0) por clúster:")
print(df.groupby("CLUSTER_EVENTO")["REAL"].value_counts().unstack(fill_value=0))

# === DÍA DE LA SEMANA POR CLÚSTER ===
print("\n📆 Día de la semana dominante por clúster:")
print(pd.crosstab(df["CLUSTER_EVENTO"], df["DIA_SEMANA"]))

# === MES DEL AÑO POR CLÚSTER ===
print("\n🗓️ Mes dominante por clúster:")
print(pd.crosstab(df["CLUSTER_EVENTO"], df["MES"]))

# === RENTABILIDAD POR CLÚSTER ===
df["RENTABILIDAD"] = df["TOTAL_RECAUDADO"] - df["COSTE_ESTIMADO"]
print("\n💰 Rentabilidad media por clúster:")
print(df.groupby("CLUSTER_EVENTO")["RENTABILIDAD"].mean())

# === SCATTER DE RECAUDADO VS ASISTENCIAS POR CLÚSTER ===
import matplotlib.pyplot as plt

plt.figure(figsize=(10, 6))
sns.scatterplot(data=df, x="NUM_ASISTENCIAS", y="TOTAL_RECAUDADO", hue="CLUSTER_EVENTO", palette="tab10")
plt.title("🎨 Asistencias vs Recaudado por Clúster")
plt.xlabel("Número de Asistencias")
plt.ylabel("Total Recaudado")
plt.grid(True)
plt.tight_layout()
plt.show()

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import math
from sklearn.cluster import KMeans

# Cargar datos
df = pd.read_csv("stats/dataset_modelo_clusterizado_v2.csv", parse_dates=["FECHA_EVENTO"])

# Revisar clusters
print(df["CLUSTER_EVENTO"].value_counts())

# Seleccionamos las variables numéricas (excepto la fecha y la target si está)
vars_numericas = df.select_dtypes(include=["float64", "int64"]).drop(columns=["CLUSTER_EVENTO", "NUM_ASISTENCIAS"], errors='ignore').columns

# Grid de subplots para boxplots
a = math.floor(math.sqrt(len(vars_numericas))) + 1
fig, axes = plt.subplots(a, a, figsize=(25, 25))
axes = axes.flatten()

for i, col in enumerate(vars_numericas):
    sns.boxplot(x="CLUSTER_EVENTO", y=col, data=df, orient="v", ax=axes[i])
    axes[i].set_title(col)

# Eliminar subplots vacíos
for j in range(i+1, len(axes)):
    fig.delaxes(axes[j])

plt.tight_layout()
plt.show()

from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA

# Escalado + PCA
X = df.select_dtypes(include=["float64", "int64"]).drop(columns=["CLUSTER_EVENTO", "NUM_ASISTENCIAS"], errors="ignore")
X_scaled = StandardScaler().fit_transform(X)

pca = PCA(n_components=2)
X_pca = pca.fit_transform(X_scaled)

# Añadir clusters
df["PCA1"] = X_pca[:, 0]
df["PCA2"] = X_pca[:, 1]

# Plot
plt.figure(figsize=(10, 8))
sns.scatterplot(data=df, x="PCA1", y="PCA2", hue="CLUSTER_EVENTO", palette="tab10", s=100)
plt.title("Distribución PCA de los clusters")
plt.grid(True)
plt.show()

# Reentrenamos KMeans si necesitas los centroides
kmeans = KMeans(n_clusters=df["CLUSTER_EVENTO"].nunique(), random_state=77)
kmeans.fit(X_scaled)
centers = kmeans.cluster_centers_
centers_pca = pca.transform(centers)

# Dibujamos centroides
plt.figure(figsize=(10, 8))
sns.scatterplot(data=df, x="PCA1", y="PCA2", hue="CLUSTER_EVENTO", palette="tab10", s=80)
plt.scatter(centers_pca[:, 0], centers_pca[:, 1], marker="X", s=300, c="black", label="Centroides")
plt.title("Centroides KMeans sobre PCA")
plt.legend()
plt.grid(True)
plt.show()
