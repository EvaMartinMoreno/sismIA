import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
import matplotlib.pyplot as plt

# === CARGA DE DATOS ===
df_real = pd.read_csv("stats/dataset_modelo.csv", parse_dates=["FECHA_EVENTO"])
df_fake = pd.read_csv("stats/eventos_simulados_girona.csv", parse_dates=["FECHA_EVENTO"])

df_real["REAL"] = 1
df_fake["REAL"] = 0

df = pd.concat([df_real, df_fake], ignore_index=True)

# === FILTRAR SOLO EVENTOS DE PAGO ===
df = df[df["TOTAL_RECAUDADO"] > 0].copy()

# === VARIABLES DISPONIBLES ANTES DEL EVENTO ===
vars_previas = ["COSTE_ESTIMADO", "SEMANA", "DIA_SEMANA", "MES", "TIPO_EVENTO", "COMUNIDAD"]
df_cluster = df[vars_previas].copy()

# === TRANSFORMACIÓN CATEGÓRICAS ===
df_cluster = pd.get_dummies(df_cluster, columns=["DIA_SEMANA", "MES", "TIPO_EVENTO", "COMUNIDAD"], drop_first=True)

# === ESCALADO ===
scaler = StandardScaler()
X_scaled = scaler.fit_transform(df_cluster)

# === ELECCIÓN DE K ÓPTIMO ===
sil_scores = []
K_range = range(2, 10)

for k in K_range:
    kmeans = KMeans(n_clusters=k, random_state=42)
    labels = kmeans.fit_predict(X_scaled)
    score = silhouette_score(X_scaled, labels)
    sil_scores.append(score)

plt.figure(figsize=(8, 4))
plt.plot(K_range, sil_scores, marker='o', color='orange')
plt.xlabel("Número de clusters (K)")
plt.ylabel("Silhouette Score")
plt.title("🧠 Elección de K - Clustering Eventos Girona")
plt.grid(True)
plt.tight_layout()
plt.show()

# === APLICAR K-MEANS CON K=3 (puedes cambiarlo si ves otro mejor en el gráfico) ===
k_optimo = 3
kmeans = KMeans(n_clusters=k_optimo, random_state=42)
df["CLUSTER_EVENTO"] = kmeans.fit_predict(X_scaled)

# === PERFIL DE CLÚSTERES ===
print("\n🎯 Perfil de cada clúster:")
print(df.groupby("CLUSTER_EVENTO")[["NUM_ASISTENCIAS", "TOTAL_RECAUDADO", "COSTE_ESTIMADO"]].mean())

# === GUARDAR CSV RESULTADO ===
df.to_csv("stats/dataset_modelo_clusterizado.csv", index=False)
print("\n💾 Archivo guardado: stats/dataset_modelo_clusterizado.csv")

# === CARGA DEL DATASET CON CLUSTER ASIGNADO ===
df = pd.read_csv("stats/dataset_modelo_clusterizado.csv", parse_dates=["FECHA_EVENTO"])

# === 1. ¿QUÉ TIPO DE EVENTO SE CONCENTRA EN CADA CLÚSTER? ===
print("\n🎯 Tipo de evento por clúster:")
print(df.groupby(["CLUSTER_EVENTO", "TIPO_EVENTO"]).size().unstack(fill_value=0))

# === 2. ¿HAY MÁS EVENTOS REALES O SIMULADOS EN CADA CLÚSTER? ===
print("\n🧪 Eventos reales (1) vs simulados (0) por clúster:")
print(df.groupby(["CLUSTER_EVENTO", "REAL"]).size().unstack(fill_value=0))

# === 3. ¿DÍA DE LA SEMANA MÁS COMÚN EN CADA CLÚSTER? ===
print("\n📆 Día de la semana dominante por clúster:")
print(df.groupby(["CLUSTER_EVENTO", "DIA_SEMANA"]).size().unstack(fill_value=0))

# === 4. ¿MES MÁS FRECUENTE POR CLÚSTER? ===
print("\n🗓️ Mes dominante por clúster:")
print(df.groupby(["CLUSTER_EVENTO", "MES"]).size().unstack(fill_value=0))
