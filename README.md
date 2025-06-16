**SismIA** 💡
**Plataforma inteligente para la gestión, análisis y predicción de eventos deportivos diseñada para Comunidades Runners.** 
Desde el scraping hasta la simulación de próximos eventos, esta app está diseñada para ayudar a saber si un evento de social run será viable o no.

---

 **Qué hace SismIA?**
- 📥 Scrapea eventos deportivos desde Athletiks.
- 🧹 Limpia y estructura los datos automáticamente.
- ✍️ Permite validar manualmente los eventos desde una interfaz visual.
- 📊 Entrena modelos predictivos para estimar asistencia y beneficio.
- 🔮 Simula eventos futuros y recomienda fechas óptimas.
- 📅 Muestra dashboards con próximos eventos reales y simulados.

## 🗂️ Estructura del proyecto
```text
sismia/
├── src/
│   ├── main.py               # App principal con Streamlit
│   ├── pipeline_app.py             # Pipeline completo
│   ├── scraping/
│   │   ├── scraper_athletiks.py
│   │   └── scraper_temperatura.py
│   ├── limpieza_eventos_athletiks.py
│   ├── simulacion_datos.py
│   └── modelos/
│       ├── modelo_asistencias_Girona.py
│       ├── modelo_beneficio_Girona.py
│       └── eventos_futuros_Girona.py
├── data/
│   ├── raw/
│   │   ├── dataset_modelo.csv
│   │   └── dataset_modelo_validado.csv
│   └── predicciones/
│       └── simulaciones_futuras.csv
├── secrets.toml
├── requirements.txt
└── README.md
```

**⚙️ Instalación**
1. Clona el repositorio:
git clone https://github.com/tu_usuario/sismia.git
2. Crea el entorno virtual (sismia_env) y actívalo
python -m venv sismia_env
.\sismia_env\scripts\activate
3. Instala las dependencias:
pip install -r requirements.txt
4. Crea un archivo secrets.toml en la raíz con tus credenciales de acceso:
USUARIO="tu_usuario"
PASSWORD="tu_password"

**¿Cómo se ejecuta?**
Desde la raíz del proyecto:
streamlit run main.py

**¿A quién va dirigido?**
Proyectos que necesiten integrar scraping, limpieza, simulación y predicción.
Organizadores de eventos deportivos de social run. 
Gestores de marketing deportivo que quieran decisiones basadas en datos de comunidades.

**¿Qué está por venir?**
Integración con Instagram para cruzar engagement con asistencia.
Gestión multicomunidad y multiusuario.

"**SismIA no es solo una app. Es la entrenadora personal de tus eventos deportivos.
Porque tu evento no se intuye, tu evento se entrena**".

**Demo de la app**
*Puedes probar la app desplegada en Streamlit aquí:*
🔗 **[sismia.streamlit.app](https://sismia.streamlit.app)**

*Esta versión utiliza mis propias credenciales y datos (almacenados de forma segura mediante `secrets.toml`, no accesibles públicamente) para mostrar cómo funciona el sistema completo: scraping, limpieza, simulación, predicción y dashboard.*

> *⚠️ Por privacidad, los datos de acceso a plataformas externas (como Athletiks o Instagram) no están incluidos en el repositorio. Sin embargo, puedes clonar el proyecto y usar tus propias credenciales para adaptarlo a tu comunidad o entorno.*
