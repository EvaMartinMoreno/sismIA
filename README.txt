** SismIA 💡** 
Plataforma inteligente para la gestión, análisis y predicción de eventos deportivos diseñada para Comunidades Runners.
Desde el scraping hasta la simulación de próximos eventos, esta app está diseñada para ayudar a tomar decisiones estratégicas basadas en datos reales.

---

 **Qué hace SismIA?**
- 📥 Scrapea eventos deportivos desde Athletiks.
- 🧹 Limpia y estructura los datos automáticamente.
- ✍️ Permite validar manualmente los eventos desde una interfaz visual.
- 📊 Entrena modelos predictivos para estimar asistencia y beneficio.
- 🔮 Simula eventos futuros y recomienda fechas óptimas.
- 📅 Muestra dashboards con próximos eventos reales y simulados.

---
**Estructura del proyecto**

sismia/
├── src/
│   ├── app-sismia.py               # App principal con Streamlit
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
├── .env
├── requirements.txt
└── README.md

**⚙️ Instalación**
1. Clona el repositorio:
git clone https://github.com/tu_usuario/sismia.git
2. Instala las dependencias:
pip install -r requirements.txt
3. Crea un archivo .env en la raíz con tus credenciales de acceso:
USUARIO_GIRONA=tu_usuario
PASSWORD_GIRONA=tu_password
USUARIO_ELCHE=tu_usuario
PASSWORD_ELCHE=tu_password

** ¿Cómo se ejecuta? **
Desde la raíz del proyecto:
streamlit run src/app-sismia.py

** ¿A quién va dirigido?**
Organizadoras de eventos deportivos (clubs, comunidades, marcas).
Gestores de marketing deportivo que quieran decisiones basadas en datos.
Proyectos que necesiten integrar scraping, limpieza, simulación y predicción.

**¿Qué está por venir?**
Integración con Instagram para cruzar engagement con asistencia.
Automatización de toda la cadena desde la app (scraping > predicción > dashboard).
Gestión multicomunidad y multiusuario.
Packs de experiencias y turismo deportivo inteligente.

"SismIA no es solo una app. Es la entrenadora personal de tus eventos deportivos." 🏃‍♀️📊

