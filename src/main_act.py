import os
from instagram_api import run_actualizacion_unica
#from scraping_athletiks import actualizar_datos_athletiks  # TODO: Crear e importar
#from limpieza_carreras import unificar_y_limpiar_carreras  # TODO: Crear función si no existe

def actualizar_todo():
    """
    Ejecuta todos los scripts de actualización de datos:
    - Instagram API
    - Scraping Athletiks
    - Limpieza y unificación de calendario de carreras
    """
    try:
        print("\n📸 Actualizando métricas de Instagram...")
        run_actualizacion_unica()

        print("\n🏃‍♀️ Actualizando datos de Athletiks...")
        # actualizar_datos_athletiks()  # Descomentar cuando esté disponible

        print("\n📅 Limpiando y actualizando calendario de carreras...")
        # unificar_y_limpiar_carreras(
        #     "data/raw/races/carreras_alicante_rockthesport.csv",
        #     "data/raw/races/carreras_grupobrotons.csv",
        #     "data/raw/races",
        #     "data/processed/carreras_unificadas.csv"
        # )

        print("\n✅ Todo actualizado correctamente.")
    except Exception as e:
        print(f"❌ Error durante la actualización: {e}")
