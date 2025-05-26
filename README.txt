### 🛠 Correcciones manuales

Este proyecto incluye una revisión manual del campo `ASISTENCIA`, ya que los datos originales de la plataforma Athletiks no marcaban correctamente si una persona asistió o no (muchos valores aparecen como `"pending"`).

Para ello:

- Se genera el archivo `data/entrada/revision_asistencias.csv`.
- Debes revisar y editar manualmente la columna `ASISTENCIA` (con `TRUE` o `FALSE`).
- El script de procesamiento aplicará automáticamente esas correcciones si el archivo existe.

Si quieres trabajar con tus propios datos, deberás generar este archivo o adaptar tu flujo.
### 🛠 Correcciones manuales

Este proyecto incluye una revisión manual del campo `ASISTENCIA`, ya que los datos originales de la plataforma Athletiks no marcaban correctamente si una persona asistió o no (muchos valores aparecen como `"pending"`).

Para ello:

- Se genera el archivo `data/entrada/revision_asistencias.csv`.
- Debes revisar y editar manualmente la columna `ASISTENCIA` (con `TRUE` o `FALSE`).
- El script de procesamiento aplicará automáticamente esas correcciones si el archivo existe.

Si quieres trabajar con tus propios datos, deberás generar este archivo o adaptar tu flujo.
