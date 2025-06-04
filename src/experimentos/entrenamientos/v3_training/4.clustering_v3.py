import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
import matplotlib.pyplot as plt

# === CARGA ===
df = pd.read_csv("stats/dataset_modelo.csv", parse_dates=["FECHA_EVENTO"])
df = df[df["TOTAL_RECAUDADO"] > 0].copy()  # solo eventos de pago

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

# === BUSCAR K ÓPTIMO CON SILHOUETTE ===
sil_scores = []
K_range = range(2, 10)

for k in K_range:
    kmeans = KMeans(n_clusters=k, random_state=42)
    labels = kmeans.fit_predict(X_scaled)
    score = silhouette_score(X_scaled, labels)
    sil_scores.append(score)

# === GRAFICAR SILHOUETTE ===
plt.plot(K_range, sil_scores, marker='o')
plt.xlabel("Número de clusters (K)")
plt.ylabel("Silhouette Score")
plt.title("🧠 Elección de K - Clustering Eventos")
plt.grid(True)
plt.tight_layout()
plt.show()

# === AJUSTAR CON K ÓPTIMO (elige el que veas mejor tras la gráfica, aquí usamos K=3 como ejemplo) ===
k_optimo = 3
kmeans = KMeans(n_clusters=k_optimo, random_state=42)
df["CLUSTER_EVENTO"] = kmeans.fit_predict(X_scaled)

# === PERFILADO DE CLÚSTERES ===
print("\n🎯 Perfil de cada clúster:")
print(df.groupby("CLUSTER_EVENTO")[["NUM_ASISTENCIAS", "TOTAL_RECAUDADO", "COSTE_ESTIMADO"]].mean())

# === OPCIONAL: GUARDAR CSV ===
df.to_csv("stats/dataset_modelo_clusterizado.csv", index=False)
