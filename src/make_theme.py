import os

# Ruta al directorio de configuración de Streamlit (carpeta oculta)
config_dir = os.path.join(os.path.expanduser("~"), ".streamlit")
os.makedirs(config_dir, exist_ok=True)

# Ruta al archivo config.toml
config_path = os.path.join(config_dir, "config.toml")

# Contenido del tema personalizado
config_content = """
[theme]
base = "light"
primaryColor = "#a26ec6"
backgroundColor = "#fbffe0"
secondaryBackgroundColor = "#ffffff"
textColor = "#4b286d"
font = "sans serif"
""".strip()

# Guardar el archivo con codificación UTF-8
with open(config_path, "w", encoding="utf-8") as f:
    f.write(config_content)

print(f"✅ Archivo 'config.toml' creado correctamente en:\n{config_path}")
