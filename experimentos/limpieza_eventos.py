import pandas as pd
import os
from glob import glob
import re
from datetime import datetime
from unidecode import unidecode

def extraer_fecha_evento(nombre_archivo):
    nombre_base = os.path.basename(nombre_archivo).lower()
    match = re.search(r'(\d{1,2})[- ]*de[- ]*(\w+)[- ]*del[- ]*(\d{4})', nombre_base)
    if match:
        dia, mes_texto, anio = match.groups()
        meses = {
            'enero': '01', 'febrero': '02', 'marzo': '03', 'abril': '04',
            'mayo': '05', 'junio': '06', 'julio': '07', 'agosto': '08',
            'septiembre': '09', 'setembre': '09', 'octubre': '10', 'noviembre': '11', 'diciembre': '12',
            'gener': '01', 'febrer': '02', 'març': '03', 'abril': '04',
            'maig': '05', 'juny': '06', 'juliol': '07', 'agost': '08',
            'setembre': '09', 'octubre': '10', 'novembre': '11', 'desembre': '12'
        }
        mes = meses.get(mes_texto.strip(), "01")
        return f"{anio}-{mes.zfill(2)}-{dia.zfill(2)}"
    return None

def detectar_ubicacion(evento):
    evento = unidecode(str(evento).lower())
    catalan = ['gener', 'febrer', 'març', 'abril', 'maig', 'juny', 'juliol', 'agost',
               'setembre', 'octubre', 'novembre', 'desembre', 'dimecres']
    return 'Girona' if any(palabra in evento for palabra in catalan) else 'Elche'

def cargar_y_procesar_eventos(path_csv):
    df = pd.read_csv(path_csv)
    
    # Limpiar y asegurar campos clave
    df["evento"] = df["evento"].fillna("").astype(str)
    df["fecha_evento"] = pd.to_datetime(df["fecha_evento"], errors="coerce")
    df["ubicacion"] = df["evento"].apply(detectar_ubicacion)
    
    # Calcular asistencias
    df["asistencias"] = df.groupby("user_id")["user_id"].transform("count")
    
    # Obtener datos del próximo evento
    hoy = pd.Timestamp.today().normalize()
    df_futuros = df[df["fecha_evento"] >= hoy].sort_values("fecha_evento")

    if not df_futuros.empty:
        proximo_evento = df_futuros.iloc[0]["evento"]
        fecha_evento = df_futuros.iloc[0]["fecha_evento"]
        apuntadas = df_futuros[df_futuros["evento"] == proximo_evento].shape[0]
        recaudado = df_futuros[df_futuros["evento"] == proximo_evento]["price_paid"].sum()
        dias_restantes = (fecha_evento - hoy).days
    else:
        proximo_evento, apuntadas, recaudado, dias_restantes = None, 0, 0.0, None

    # Top usuarias
    top_fieles = df.groupby(["user_id", "nombre_completo"])["asistencias"].max().sort_values(ascending=False).head(3)
    top_inactivas = df.groupby(["user_id", "nombre_completo"])["asistencias"].max().sort_values().head(3)

    return {
        "df": df,
        "proximo_evento": proximo_evento,
        "apuntadas": apuntadas,
        "recaudado": recaudado,
        "dias_restantes": dias_restantes,
        "top_fieles": top_fieles,
        "top_inactivas": top_inactivas
    }


def detectar_ubicacion(evento):
    catalan_keywords = ['dimecres', 'gener', 'febrer', 'març', 'abril', 'maig', 'juny',
                        'juliol', 'agost', 'setembre', 'octubre', 'novembre', 'desembre']
    evento_lower = unidecode(evento.lower())
    return 'Girona' if any(mes in evento_lower for mes in catalan_keywords) else 'Elche'

def limpiar_nombre_evento(nombre_evento):
    return re.split(r'\d', nombre_evento.strip())[0].strip().title()

def limpiar_evento(df, nombre_archivo):
    df.columns = [col.strip().lower().replace('"', '').replace("\ufeff", "") for col in df.columns]

    nombre_evento = os.path.basename(nombre_archivo).split("__")[0].replace("-", " ").capitalize()
    fecha_evento = extraer_fecha_evento(nombre_archivo)
    ubicacion = detectar_ubicacion(nombre_evento)

    df["evento"] = limpiar_nombre_evento(nombre_evento)
    df["fecha_evento"] = fecha_evento
    df["ubicacion"] = ubicacion

    # Eliminar registros de Sisterhood en 'name'
    if "name" in df.columns:
        df = df[~df["name"].fillna("").str.lower().str.contains("sisterhood")].copy()
        df.loc[:, "nombre_completo"] = df["name"].fillna("desconocido").apply(
            lambda x: unidecode(str(x).strip()).upper()
        )

    fecha_cols = [col for col in df.columns if "fecha" in col]
    if fecha_cols:
        df.loc[:, "fecha_inscripcion"] = pd.to_datetime(df[fecha_cols[0]], errors="coerce")

    columnas_deseadas = [
        "nombre_completo", "email", "has_paid", "price_paid",
        "attendance_status", "ticket", "fecha_inscripcion",
        "fecha_evento", "evento", "ubicacion"
    ]
    return df[[col for col in columnas_deseadas if col in df.columns]]

def limpiar_todos_los_eventos(carpeta_entrada, salida):
    archivos = glob(os.path.join(carpeta_entrada, "*.csv"))
    eventos = []

    for archivo in archivos:
        try:
            df = pd.read_csv(archivo, sep=None, engine="python")
            df_limpio = limpiar_evento(df, archivo)
            eventos.append(df_limpio)
        except Exception as e:
            print(f"⚠️ Error al procesar {archivo}: {e}")

    if eventos:
        df_eventos = pd.concat(eventos, ignore_index=True)

        # Crear user_id
        contador_g, contador_e = 1, 1
        user_ids = {}
        for i, row in df_eventos.iterrows():
            clave = (row.get("nombre_completo", ""), row.get("email", ""))
            if clave not in user_ids:
                if row.get("ubicacion") == "Girona":
                    user_ids[clave] = f"G{contador_g}"
                    contador_g += 1
                else:
                    user_ids[clave] = f"E{contador_e}"
                    contador_e += 1
            df_eventos.at[i, "user_id"] = user_ids[clave]

        # Normalizar pagos
        df_eventos["has_paid"] = df_eventos["has_paid"].astype(str).str.strip().str.lower().map({
            "yes": True, "no": False
        })
        df_eventos["has_paid"] = df_eventos["has_paid"].fillna(False).astype(bool)

        df_eventos["price_paid"] = pd.to_numeric(df_eventos["price_paid"], errors="coerce").fillna(0)
        df_eventos["coste_evento"] = 0.0
        df_eventos["beneficio_evento"] = df_eventos["price_paid"] - df_eventos["coste_evento"]

        # Asistencias
        asistencias = df_eventos[df_eventos["has_paid"] == True]["user_id"].value_counts().to_dict()
        df_eventos["asistencias"] = df_eventos["user_id"].map(asistencias).fillna(0).astype(int)

        df_eventos.drop(columns=["ticket", "name", "fecha_inscripcion"], errors="ignore", inplace=True)

        columnas_ordenadas = [
            "user_id", "nombre_completo", "email", "has_paid", "price_paid",
            "asistencias", "coste_evento", "beneficio_evento", "fecha_evento", "evento", "ubicacion"
        ]
        df_eventos = df_eventos[[col for col in columnas_ordenadas if col in df_eventos.columns]]

        os.makedirs(os.path.dirname(salida), exist_ok=True)
        df_eventos.to_csv(salida, index=False)
        print(f"✅ Archivo limpio guardado en: {salida}")
        return df_eventos
    else:
        print("❌ No se encontraron archivos válidos.")
        return pd.DataFrame()

# === EJECUCIÓN FINAL ===
if __name__ == "__main__":
    carpeta_raw = "data/raw"
    archivo_salida = "data/clean/events_athletiks_limpio.csv"
    df = limpiar_todos_los_eventos(carpeta_raw, archivo_salida)

    print("🔍 Total tras cargar CSV:", len(df))

    # Ubicación por idioma (seguro)
    df["ubicacion"] = df["evento"].apply(detectar_ubicacion)
    print("📍 Ubicaciones asignadas:", df["ubicacion"].value_counts().to_dict())

    # Fechas
    df["fecha_evento"] = pd.to_datetime(df["fecha_evento"], errors="coerce")
    print("📅 Filas con fecha válida:", df["fecha_evento"].notna().sum())

    # Asistencias
    df["asistencias"] = df.groupby("user_id")["user_id"].transform("count")
    print("🧾 Asistencias calculadas")

    # Próximo evento
    hoy = pd.Timestamp.today().normalize()
    df_futuros = df[df["fecha_evento"] >= hoy].sort_values("fecha_evento")

    if not df_futuros.empty:
        proximo_evento = df_futuros.iloc[0]["evento"]
        fecha_evento = df_futuros.iloc[0]["fecha_evento"]
        apuntadas = df_futuros[df_futuros["evento"] == proximo_evento].shape[0]
        recaudado = df_futuros[df_futuros["evento"] == proximo_evento]["price_paid"].sum()
        dias_restantes = (fecha_evento - hoy).days
    else:
        proximo_evento, apuntadas, recaudado, dias_restantes = None, 0, 0.0, None

    # Top 3
    top_fieles = df.groupby(["user_id", "nombre_completo"])["asistencias"].max().sort_values(ascending=False).head(3)
    top_inactivas = df.groupby(["user_id", "nombre_completo"])["asistencias"].max().sort_values().head(3)

    # Mostrar resumen
    print(f"\n🏃 Próximo evento: {proximo_evento}")
    print(f"👥 {apuntadas} apuntadas")
    print(f"💰 {recaudado:.2f} € recaudados")
    print(f"📅 Faltan {dias_restantes} días\n")

    print("⭐ Cuentas más fieles:")
    print(top_fieles)

    print("\n😴 Cuentas menos fieles:")
    print(top_inactivas)
