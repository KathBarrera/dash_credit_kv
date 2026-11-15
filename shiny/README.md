# Riesgo de Incumplimiento en Tarjetas de Crédito · versión Shiny (R)

Réplica en **R + Shiny + Plotly** del tablero Dash de la carpeta [`../dash`](../dash). Tiene las mismas páginas, el mismo diseño, los mismos textos en español e inglés, modo claro u oscuro, el formulario **Predecir** con dos modelos (un Random Forest serializado y el modelo original CS-FOF) y el asistente **Kyo**.

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
│   ├── 05_modelos.R           # Modelos: tabla de líderes, diagnóstico, diferencia crítica y SHAP (CS-FOF y los 7 de referencia)
│   ├── 06_variables.R         # Variables del modelo (mismas transformaciones del proyecto)
│   ├── 06b_cs_fof.R           # CS-FOF en R: recorre los árboles exportados del modelo del Dash
│   ├── 07_predecir.R          # Página Predecir
│   ├── 08_paginas.R           # Páginas, menú y navegación
│   ├── 09_kyo.R               # Asistente Kyo (TF-IDF + regresión logística)
│   └── 10_modelo_original.R   # Modelo original CS-FOF: teoría, metodología, código y resultados
├── modelo/
│   ├── cs_fof/                # Copia de original_model.py y sus pruebas (se muestran en la pestaña Código)
│   ├── entrenar_modelo.R      # Entrena y serializa el Random Forest (Rscript modelo/entrenar_modelo.R)
│   ├── modelo_credito.rds     # Modelo serializado con saveRDS
│   ├── modelo_credito.json    # Métricas, umbral ajustable, predicción conforme, hiperparámetros y versiones
│   ├── particion_dash.csv.gz  # Partición 80/20 del Dash (la usan los dos modelos de Predecir)
│   ├── cs_fof_bosque.bin.gz   # Nodos de los 359 árboles de CS-FOF (exportados del Dash)
│   ├── cs_fof_meta.json       # Columnas, estandarización, métricas, umbral y predicción conforme de CS-FOF
│   └── cs_fof_verificacion.csv # 300 clientes de prueba con la probabilidad de Python, para comprobar la réplica
├── kyo/                       # Conocimiento de Kyo (exportado del Dash), pruebas y modelo entrenado
├── www/                       # estilos.css, comun.js, card_focus.js y ef_fold.js (los mismos del Dash), shiny.css,
│                              # app.js, leaderboard.js (orden y filtro de la tabla de líderes), fotos y Kyo
│   └── vendor/                # MathJax 3.2.2 y highlight.js 11.9.0 incluidos (no dependen de una CDN)
├── data/                      # Dataset UCI (.xls)
├── results/                   # Los mismos CSV de dash/results: modelos (5 x 5), SHAP por fold, LIME vs SHAP y anytime
└── herramientas/
    ├── exportar_desde_dash.py # Copia del Dash el CSS, el JS y el conocimiento de Kyo
    ├── exportar_cs_fof.py     # Exporta los árboles de CS-FOF y la partición del Dash a modelo/
    └── evaluar_kyo.R          # Evalúa a Kyo con las mismas preguntas de prueba del Dash
```

## Modelos de la página Predecir

El selector de Predecir ofrece dos modelos. Los dos usan la misma partición 80/20 del Dash (`modelo/particion_dash.csv.gz`), así que sus métricas de prueba se comparan sobre los mismos 5,993 clientes.

**Random Forest.** El `.pkl` de scikit-learn no se puede abrir en R, así que este modelo se volvió a entrenar en R:

- Es un Random Forest del paquete `ranger` con pesos de clase balanceados.
- Usa los mismos hiperparámetros del modelo del Dash: 291 árboles, profundidad 14, 4 variables por corte y hojas de al menos 10 clientes.
- Usa las mismas variables transformadas del proyecto.
- En el 20 % de prueba logra F1 0.532, recall 0.587 y ROC-AUC 0.773 (el del Dash: F1 0.533).
- `entrenar_modelo.R` también calcula el umbral recomendado (máximo F1 en una mitad de la prueba) y la predicción conforme al 90 %.

```r
modelo <- ranger(x = X, y = y, probability = TRUE, case.weights = pesos, num.trees = 291, max.depth = 14, mtry = 4)
saveRDS(modelo, "modelo/modelo_credito.rds")      # serializar
modelo <- readRDS("modelo/modelo_credito.rds")    # cargar en la app
riesgo <- predict(modelo, cliente)$predictions[, "1"]
```

**CS-FOF (modelo original).** Se entrenó en Python, en el Dash. `herramientas/exportar_cs_fof.py` exporta sus 359 árboles (columnas, coeficientes, umbral, hijos y valor de cada nodo) y `R/06b_cs_fof.R` los recorre igual que `original_model.py`. Da la misma probabilidad que Python en 300 clientes de prueba (diferencia máxima menor que 10⁻¹⁵). Las sumas se hacen en el mismo orden que numpy, porque algunos clientes caen justo en el umbral de un corte y una diferencia en el último decimal cambiaría la rama.

Para actualizar los archivos de CS-FOF después de reentrenarlo en el Dash, desde la raíz del repositorio:

```bash
python shiny/herramientas/exportar_cs_fof.py
```

## Kyo

Kyo usa el mismo motor que la versión Dash, reescrito en R:

- Normaliza el texto y lo convierte en vectores TF-IDF de palabras y de letras.
- Clasifica con una regresión logística multinomial con penalización L2 (C = 25, optimizador L-BFGS).
- Usa la misma base de conocimiento que el Dash.

Se evalúa con las mismas preguntas de prueba del Dash. Resultados del Dash con la base de conocimiento actual (la versión R debería dar lo mismo; compruébalo con el comando de abajo):

| Prueba | Resultado (Dash) |
|---|---|
| Preguntas nuevas en español | 81/81 |
| Preguntas nuevas en inglés | 35/36 |
| Preguntas ajenas al tablero rechazadas | 17/17 |
| Sugerencias que llevan al mismo tema en ambos idiomas | 83/83 |

```bash
cd shiny && Rscript herramientas/evaluar_kyo.R
```

Si cambias el diseño o el contenido de Kyo en el Dash, cópialo a esta versión con `python shiny/herramientas/exportar_desde_dash.py`, ejecutado desde la raíz del repositorio. Kyo se vuelve a entrenar solo al arrancar.
