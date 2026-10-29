# Riesgo de Incumplimiento en Tarjetas de Crédito · versión Shiny (R)

Réplica en **R + Shiny + Plotly** del tablero Dash de la carpeta [`../dash`](../dash). Tiene las mismas páginas, el mismo diseño, los mismos textos en español e inglés, modo claro u oscuro, el formulario **Predecir** con un modelo serializado y el asistente **Kyo**.

## Ejecutar en tu computador

1. Instala R (4.1 o superior) y los paquetes:

   ```r
   install.packages(c("shiny", "plotly", "ranger", "readxl", "jsonlite", "commonmark", "Matrix"))
   ```

2. Abre la carpeta `shiny/` en RStudio (o en una consola de R ubicada en ella) y ejecuta:

   ```r
   shiny::runApp()
   ```

La primera vez, Kyo se entrena en unos 20 segundos y guarda su modelo en `kyo/modelo_kyo.rds`. Las siguientes veces arranca de inmediato.

## Publicar en shinyapps.io (gratis)

1. Crea una cuenta en [shinyapps.io](https://www.shinyapps.io) y elige un nombre de cuenta (por ejemplo `kathbarrera`).
2. En shinyapps.io entra a **Account → Tokens → Show → Show secret** y copia el comando `rsconnect::setAccountInfo(...)`.
3. En R, instala rsconnect y pega ese comando:

   ```r
   install.packages("rsconnect")
   rsconnect::setAccountInfo(name = "TU_CUENTA", token = "TU_TOKEN", secret = "TU_SECRET")
   ```

4. Desde la raíz del repositorio, publica la carpeta `shiny/`:

   ```r
   rsconnect::deployApp("shiny", appName = "dash-credit-kv", appTitle = "Riesgo de Incumplimiento · Shiny")
   ```

   Al terminar abre `https://TU_CUENTA.shinyapps.io/dash-credit-kv/`. Para actualizarla después de un cambio, vuelve a ejecutar el mismo `deployApp(...)`.

El plan gratis da 25 horas activas al mes. La app se duerme si nadie la usa y despierta sola en unos segundos cuando alguien la abre.

## Estructura

```
shiny/
├── app.R                      # Interfaz y servidor (rutas, idioma, tema, gráficas, Predecir y Kyo)
├── R/                         # Shiny carga estos archivos solo, en orden
│   ├── 00_config.R            # Idioma, autores, enlaces, rutas y paleta  <- editar nombres aquí
│   ├── 01_datos.R             # Carga y limpieza (igual que el notebook 00_eda)
│   ├── 02_utils.R             # Formato, estadísticos, componentes y tema de las figuras
│   ├── 03_univariado.R        # EDA univariado
│   ├── 04_multivariado.R      # EDA multivariado
│   ├── 05_modelos.R           # Resultados de las 112 combinaciones de modelos
│   ├── 06_variables.R         # Variables del modelo (mismas transformaciones del proyecto)
│   ├── 07_predecir.R          # Página Predecir
│   ├── 08_paginas.R           # Páginas, menú y navegación
│   └── 09_kyo.R               # Asistente Kyo (TF-IDF + regresión logística)
├── modelo/
│   ├── entrenar_modelo.R      # Entrena y serializa el Random Forest (Rscript modelo/entrenar_modelo.R)
│   ├── modelo_credito.rds     # Modelo serializado con saveRDS
│   └── modelo_credito.json    # Métricas, hiperparámetros y versiones
├── kyo/                       # Conocimiento de Kyo (exportado del Dash), pruebas y modelo entrenado
├── www/                       # estilos.css y comun.js (los mismos del Dash), shiny.css, app.js, fotos y Kyo
├── data/                      # Dataset UCI (.xls)
├── results/model_results.csv  # Resultados de los modelos
└── herramientas/
    ├── exportar_desde_dash.py # Copia del Dash el CSS, el JS y el conocimiento de Kyo
    └── evaluar_kyo.R          # Evalúa a Kyo con las mismas preguntas de prueba del Dash
```

## Modelo de la página Predecir

El `.pkl` de scikit-learn no se puede abrir en R, así que el modelo se volvió a entrenar en R:

- Es un Random Forest del paquete `ranger` con pesos de clase balanceados.
- Usa los mismos hiperparámetros del modelo del Dash: 291 árboles, profundidad 14, 4 variables por corte y hojas de al menos 10 clientes.
- Usa las mismas variables transformadas del proyecto.
- En el 20 % de prueba logra F1 0.547, recall 0.610 y ROC-AUC 0.783.

```r
modelo <- ranger(x = X, y = y, probability = TRUE, case.weights = pesos, num.trees = 291, max.depth = 14, mtry = 4)
saveRDS(modelo, "modelo/modelo_credito.rds")      # serializar
modelo <- readRDS("modelo/modelo_credito.rds")    # cargar en la app
riesgo <- predict(modelo, cliente)$predictions[, "1"]
```

## Kyo

Kyo usa el mismo motor que la versión Dash, reescrito en R:

- Normaliza el texto y lo convierte en vectores TF-IDF de palabras y de letras.
- Clasifica con una regresión logística multinomial con penalización L2 (C = 25, optimizador L-BFGS).
- Usa la misma base de conocimiento que el Dash.

Con las preguntas de prueba del Dash obtiene los mismos resultados:

| Prueba | Resultado |
|---|---|
| Preguntas nuevas en español | 78/78 |
| Preguntas nuevas en inglés | 33/34 |
| Preguntas ajenas al tablero rechazadas | 17/17 |
| Sugerencias que llevan al mismo tema en ambos idiomas | 78/78 |

```bash
cd shiny && Rscript herramientas/evaluar_kyo.R
```

Si cambias el diseño o el contenido de Kyo en el Dash, cópialo a esta versión con `python shiny/herramientas/exportar_desde_dash.py`, ejecutado desde la raíz del repositorio. Kyo se vuelve a entrenar solo al arrancar.
