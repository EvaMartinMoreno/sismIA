import pandas as pd
import os
from glob import glob
import re
from datetime import datetime
import calendar
import unidecode
import streamlit as st

# === Funciones por fuente ===
def limpiar_rockthesport(df):
    df = df.rename(columns={"Nombre": "nombre", "Fecha": "fecha", "Ubicación": "localidad", "Tipología": "tipo"})
    df["fuente"] = "rockthesport"
    df["distancia"] = None
    return df[["nombre", "fecha", "localidad", "tipo", "distancia", "fuente"]]

def limpiar_brotons(df):
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

# === Parsing utilidades ===
DIAS_MAP = {"Lunes": "Mon", "Martes": "Tue", "Miércoles": "Wed", "Jueves": "Thu", "Viernes": "Fri", "Sábado": "Sat", "Domingo": "Sun"}
MESES_MAP = {"Enero": 1, "Febrero": 2, "Marzo": 3, "Abril": 4, "Mayo": 5, "Junio": 6, "Julio": 7, "Agosto": 8, "Septiembre": 9, "Octubre": 10, "Noviembre": 11, "Diciembre": 12}

def estandarizar_fecha(fecha_str):
    try:
        fecha_str = unidecode.unidecode(fecha_str).strip()
        partes = fecha_str.split()
        if len(partes) == 3:
            _, dia, mes = partes
        elif len(partes) == 2:
            dia, mes = partes
        else:
            return None
        dia = re.sub(r"\D", "", dia)
        mes = mes.capitalize()
        mes_num = MESES_MAP.get(mes)
        if mes_num is None:
            return None
        anio = datetime.now().year
        return datetime(anio, mes_num, int(dia))
    except:
        return None

def limpiar_distancia(dist):
    if pd.isna(dist):
        return None
    dist = str(dist).lower().strip().replace(",", ".")
    dist = re.sub(r"[^0-9\.]", "", dist)
    try:
        valor = float(dist)
        if valor > 1000:
            return round(valor / 1000, 2)
        return round(valor, 2)
    except:
        return None

# === Lógica completa de limpieza y exportación ===
def unificar_y_limpiar_carreras(rock_path, brotons_path, runedia_folder, path_salida):
    rock = limpiar_rockthesport(pd.read_csv(rock_path))
    brotons = limpiar_brotons(pd.read_csv(brotons_path))
    runedia = limpiar_runedia(runedia_folder)
    df = pd.concat([rock, brotons, runedia], ignore_index=True)

    df["fecha_datetime"] = df["fecha"].apply(estandarizar_fecha)
    df["fecha_datetime"] = pd.to_datetime(df["fecha_datetime"], errors="coerce")
    df = df[df["fecha_datetime"].notna()].copy()
    df["año"] = df["fecha_datetime"].dt.year
    df["mes"] = df["fecha_datetime"].dt.month
    df["día_semana"] = df["fecha_datetime"].dt.day_name(locale="es_ES")

    df["distancia_km"] = df["distancia"].apply(limpiar_distancia)
    df["nombre_evento"] = df["nombre"]
    df.drop(columns=["nombre", "fecha"], inplace=True)

    df["localidad"] = df["localidad"].astype(str).str.strip().str.title()
    df = df.drop_duplicates(subset=["nombre_evento", "localidad", "tipo", "distancia_km", "fuente"])

    df["semana"] = df["fecha_datetime"].dt.isocalendar().week
    semana_eventos = df.groupby(["año", "semana"]).size().reset_index(name="eventos_semana")
    df = df.merge(semana_eventos, on=["año", "semana"], how="left")
    df["semana_libre"] = df["eventos_semana"] <= 1

    df = df.sort_values("fecha_datetime").reset_index(drop=True)

    os.makedirs(os.path.dirname(path_salida), exist_ok=True)
    df.to_csv(path_salida, index=False)
    print(f"✅ Archivo unificado y limpio guardado en: {path_salida}")
    return df

# === Función para mostrar calendario ===
def mostrar_calendario(df):
    df["fecha_datetime"] = pd.to_datetime(df["fecha_datetime"], errors="coerce")

    meses = {1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio",
             7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"}

    año_seleccionado = st.selectbox("Selecciona un año", sorted(df["año"].unique()))
    mes_seleccionado = st.selectbox("Selecciona un mes", list(meses.keys()), format_func=lambda x: meses[x])

    df_filtrado = df[(df["año"] == año_seleccionado) & (df["mes"] == mes_seleccionado)]

    cal = calendar.Calendar()
    semanas = cal.monthdatescalendar(año_seleccionado, mes_seleccionado)

    data = []
    for semana in semanas:
        fila = []
        for dia in semana:
            if dia.month != mes_seleccionado:
                fila.append("")
            else:
                eventos = df_filtrado[df_filtrado["fecha_datetime"].dt.date == dia]
                if not eventos.empty:
                    resumen = f"{dia.day}\n" + "\n".join(eventos["nombre_evento"].values[:2])
                else:
                    resumen = str(dia.day)
                fila.append(resumen)
        data.append(fila)

    dias_semana = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
    df_calendario = pd.DataFrame(data, columns=dias_semana)
    st.table(df_calendario)

# === Ejecutar si se llama desde terminal ===
if __name__ == "__main__":
    unificar_y_limpiar_carreras(
        "data/raw/races/carreras_alicante_rockthesport.csv",
        "data/raw/races/carreras_grupobrotons.csv",
        "data/raw/races",
        "data/processed/carreras_unificadas.csv"
    )
