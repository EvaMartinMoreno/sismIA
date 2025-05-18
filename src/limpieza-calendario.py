import pandas as pd
import os
from glob import glob
import re
from datetime import datetime
import unidecode


def limpiar_rockthesport(df):
    df = df.copy()
    df = df.rename(columns={"Nombre": "nombre", "Fecha": "fecha", "Ubicación": "localidad", "Tipología": "tipo"})
    df["fuente"] = "rockthesport"
    df["distancia"] = None
    return df[["nombre", "fecha", "localidad", "tipo", "distancia", "fuente"]]

def limpiar_brotons(df):
    df = df.copy()
    df = df.rename(columns={"Nombre": "nombre", "Fecha": "fecha"})
    df["fuente"] = "brotons"
    df["localidad"] = None
    df["tipo"] = "Running/Atletismo"
    df["distancia"] = None
    return df[["nombre", "fecha", "localidad", "tipo", "distancia", "fuente"]]

def limpiar_runedia(folder_path):
    archivos = glob(os.path.join(folder_path, "carreras_runedia_*.csv"))
    dfs = []
    for archivo in archivos:
        df = pd.read_csv(archivo)
        df = df.rename(columns={
            "titulo": "nombre",
            "dia": "fecha_dia",
            "mes": "fecha_mes",
            "localidad": "localidad",
            "tipo": "tipo",
            "distancia": "distancia"
        })
        df["fecha"] = df["fecha_dia"].astype(str) + " " + df["fecha_mes"]
        df["fuente"] = "runedia"
        dfs.append(df[["nombre", "fecha", "localidad", "tipo", "distancia", "fuente"]])
    return pd.concat(dfs, ignore_index=True)

def unificar_carreras(rock_path, brotons_path, runedia_folder):
    rock = limpiar_rockthesport(pd.read_csv(rock_path))
    brotons = limpiar_brotons(pd.read_csv(brotons_path))
    runedia = limpiar_runedia(runedia_folder)
    unificado = pd.concat([rock, brotons, runedia], ignore_index=True)
    return unificado

df_carreras = unificar_carreras(
    "data/raw/races/carreras_alicante_rockthesport.csv",
    "data/raw/races/carreras_grupobrotons.csv",
    "data/raw/races"
)

print(df_carreras)

# Diccionario para traducir días en español a su forma estándar
DIAS_MAP = {
    "Lunes": "Mon", "Martes": "Tue", "Miércoles": "Wed", "Jueves": "Thu",
    "Viernes": "Fri", "Sábado": "Sat", "Domingo": "Sun",
    "L": "Mon", "M": "Tue", "X": "Wed", "J": "Thu", "V": "Fri", "S": "Sat", "D": "Sun"
}

# Diccionario para convertir meses
MESES_MAP = {
    "Enero": 1, "Febrero": 2, "Marzo": 3, "Abril": 4, "Mayo": 5, "Junio": 6,
    "Julio": 7, "Agosto": 8, "Septiembre": 9, "Octubre": 10, "Noviembre": 11, "Diciembre": 12
}

def estandarizar_fecha(fecha_str):
    try:
        # Elimina tildes y normaliza
        fecha_str = unidecode.unidecode(fecha_str).strip()
        # Elimina el nombre del día si está
        partes = fecha_str.split()
        if len(partes) == 3:
            _, dia, mes = partes
        elif len(partes) == 2:
            dia, mes = partes
        else:
            return None

        dia = re.sub(r"\D", "", dia)  # quita letras si hay
        mes = mes.capitalize()
        mes_num = MESES_MAP.get(mes)
        if mes_num is None:
            return None

        año = datetime.now().year  # Asumimos año actual si no se especifica
        return datetime(año, mes_num, int(dia))
    except Exception as e:
        return None

def limpiar_distancia(dist):
    if pd.isna(dist):
        return None
    dist = str(dist).lower().strip()
    dist = dist.replace("km", "").replace("m", "")
    try:
        valor = float(dist)
        if valor > 1000:  # si es en metros
            return round(valor / 1000, 2)
        return round(valor, 2)
    except:
        return None

def limpiar_dataframe_carreras(df):
    df = df.copy()
    # Normalizar y estandarizar fechas
    df["fecha_datetime"] = df["fecha"].apply(estandarizar_fecha)
    df["año"] = df["fecha_datetime"].dt.year
    df["mes"] = df["fecha_datetime"].dt.month
    df["día_semana"] = df["fecha_datetime"].dt.day_name(locale="es_ES")

    # Normalizar distancias
    df["distancia_km"] = df["distancia"].apply(limpiar_distancia)

    # Opcional: renombrar columnas para consistencia
    df.rename(columns={"nombre": "nombre_evento"}, inplace=True)

    return df

df_limpio = limpiar_dataframe_carreras(df_carreras)
print(df_limpio.head())

df_limpio.to_csv("data/proceed/carreras_unificadas.csv", index=False)
print("DataFrame limpio guardado en 'data/processed/carreras_unificadas.csv'")