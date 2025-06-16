import pandas as pd
from pathlib import Path

# Cargar el dataset
csv_path = Path("data/clean/dataset_modelo.csv")
df = pd.read_csv(csv_path)

# === CAMBIOS MANUALES: asigna 1 a eventos colaborativos ===
# Puedes añadir aquí todos los nombres exactos o parciales
eventos_colaborativos = [
    "Afterwork Run By Dash And Stars",
    "Dash And Stars Run",
    "Lace Up Run",
    "Rundeo By Primetime I Sisterhood",
    "Runlearn",
    "Sisterhood X Zel Hotels",
    "Sisterhood Codepilates",
    "Sunkissed Run By Dash And Stars"
]

# Actualizar la columna en función del nombre
df['COLABORACION'] = df['NOMBRE_EVENTO'].apply(
    lambda x: 1 if any(evento.lower() in x.lower() for evento in eventos_colaborativos) else 0
)

# Guardar el CSV actualizado
df.to_csv(csv_path, index=False)
print("✅ COLABORACION actualizada manualmente en el dataset.")
