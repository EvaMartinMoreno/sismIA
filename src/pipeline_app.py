# src/actualizar_datos.py
from scraper_athletiks import scrappear_eventos

def actualizar_datos_girona():
    return scrappear_eventos(
        usuario="sisterhoodrunningclub@gmail.com",
        password="SHcarlota23",
        comunidad="GIRONA"
    )

def actualizar_datos_elche():
    return scrappear_eventos(
        usuario="evamartinmoreno9@gmail.com",
        password="SHeva2024",
        comunidad="ELCHE"
    )