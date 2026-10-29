# =============================================================================
# 0. CONFIGURACIÓN GENERAL: idioma, autores, enlaces y paleta
# =============================================================================
# Shiny carga automáticamente los archivos de esta carpeta R/ (en orden alfabético)
# antes de app.R. Aquí están los datos editables del proyecto.

# ---------- Idioma (español / inglés) ----------------------------------------
# Cada render fija el idioma elegido con set_lang(); tx("texto", "text") devuelve la
# versión activa. Los textos guardados en constantes van como pares c(es, en) y se
# leen con L(par).
.I18N <- new.env()
.I18N$lang <- "es"

set_lang <- function(lang) .I18N$lang <- if (identical(lang, "en")) "en" else "es"
lang_actual <- function() .I18N$lang
tx <- function(es, en) if (.I18N$lang == "en") en else es
L <- function(v) if (is.character(v) && length(v) == 2) tx(v[[1]], v[[2]]) else v

# ---------- Autores, institución y curso (editable) --------------------------
AUTHORS <- list(
  list(name = "Katherin Barrera", email = "lkatherin@uninorte.edu.co"),
  list(name = "Valeria Florez", email = "florezvaleria@uninorte.edu.co")
)
INSTITUTION <- c("Universidad del Norte · Ciencia de Datos", "Universidad del Norte · Data Science")
COURSE <- c("Proyecto de Análisis Exploratorio de Datos (EDA)", "Exploratory Data Analysis (EDA) Project")
PROJECT_TITLE <- c("Riesgo de Incumplimiento en Tarjetas de Crédito", "Credit Card Default Risk")
PROJECT_SUBTITLE <- c("Análisis Exploratorio · Default of Credit Card Clients (UCI)",
                      "Exploratory Analysis · Default of Credit Card Clients (UCI)")

# ---------- Equipo (página Equipo) --------------------------------------------
TEAM <- list(
  list(name = "Katherin Barrera López", short = "Kath",
       role = c("Estudiante de Ciencia de Datos · Universidad del Norte",
                "Data Science student · Universidad del Norte"),
       bio = c("Me gusta convertir datos en historias claras: del ETL y el análisis exploratorio a tableros interactivos como este.",
               "I like turning data into clear stories: from ETL and exploratory analysis to interactive dashboards like this one."),
       photo = "team/katherin.jpg", card_no = "0001",
       github = "https://github.com/KathBarrera",
       linkedin = "https://www.linkedin.com/in/katherin-barrera-l%C3%B3pez-454b47392/",
       email = "lkatherin@uninorte.edu.co"),
  list(name = "Valeria Florez Sarmiento", short = "Vale",
       role = c("Estudiante de Ciencia de Datos · Universidad del Norte",
                "Data Science student · Universidad del Norte"),
       bio = c("Me apasiona el aprendizaje automático reproducible: del pipeline de modelado al Jupyter Book que documenta el proyecto.",
               "I am passionate about reproducible machine learning: from the modeling pipeline to the Jupyter Book that documents the project."),
       photo = "team/valeria.jpg", card_no = "0002",
       github = "https://github.com/valeriaflorezs",
       linkedin = "https://www.linkedin.com/in/valeriaflorezs/",
       email = "florezvaleria@uninorte.edu.co")
)

# ---------- Enlaces: libro, notebooks y repositorios ---------------------------
REPO_PROJECT <- "https://github.com/valeriaflorezs/Credit_Card_Project"
REPO_DASH <- "https://github.com/KathBarrera/dash_credit_kv"
BOOK_URL <- "https://valeriaflorezs.github.io/Credit_Card_Project/"
NOTEBOOK_URL <- paste0(BOOK_URL, "notebooks/00_eda.html")
DATA_URL <- "https://archive.ics.uci.edu/dataset/350/default+of+credit+card+clients"
NOTEBOOKS <- list(
  list("00", c("EDA: Análisis Exploratorio de Datos", "EDA: Exploratory Data Analysis"), "00_eda.html",
       c("Calidad de los datos, distribuciones y relaciones entre variables.",
         "Data quality, distributions and relationships between variables.")),
  list("01", c("Modelo base: Regresión Logística", "Baseline model: Logistic Regression"), "01_baseline_logistic.html",
       c("Modelo de referencia contra el cual se comparan los demás.",
         "Reference model against which the others are compared.")),
  list("02", c("Setup Check", "Setup Check"), "02_setup_check.html",
       c("Verificación del entorno y de las dependencias.", "Check of the environment and dependencies.")),
  list("03", c("Desarrollo y prueba del pipeline completo", "Development and testing of the full pipeline"),
       "03_pipeline_dev.html",
       c("Construcción y prueba del flujo de datos y modelado.", "Building and testing the data and modeling flow.")),
  list("04", c("Ejecutar experimentos", "Running the experiments"), "04_run_experiments.html",
       c("Ejecución de los experimentos del diseño factorial.", "Execution of the factorial-design experiments.")),
  list("05", c("Análisis de resultados", "Results analysis"), "05_results_analysis.html",
       c("Comparación de los resultados de los experimentos.", "Comparison of the experiment results.")),
  list("06", c("Interpretabilidad (SHAP y LIME)", "Interpretability (SHAP and LIME)"), "06_interpretability.html",
       c("Qué variables explican las predicciones del modelo.", "Which variables explain the model's predictions."))
)
LINKS <- list(
  list(icon = "book", title = c("Libro del proyecto", "Project book"), url = paste0(BOOK_URL, "README.html"),
       desc = c("Jupyter Book con el README y los siete notebooks del pipeline.",
                "Jupyter Book with the README and the seven pipeline notebooks.")),
  list(icon = "notebook", title = c("Notebook del EDA", "EDA notebook"), url = NOTEBOOK_URL,
       desc = c("Análisis exploratorio completo del que sale este tablero (00_eda).",
                "Full exploratory analysis this dashboard is based on (00_eda).")),
  list(icon = "github", title = c("Repositorio del proyecto", "Project repository"), url = REPO_PROJECT,
       desc = c("Pipeline de datos, notebooks, resultados de los experimentos y código fuente.",
                "Data pipeline, notebooks, experiment results and source code.")),
  list(icon = "github", title = c("Repositorio del tablero", "Dashboard repository"), url = REPO_DASH,
       desc = c("Código fuente de este tablero (versiones Dash y Shiny).",
                "Source code of this dashboard (Dash and Shiny versions).")),
  list(icon = "database", title = c("Datos originales (UCI)", "Original data (UCI)"), url = DATA_URL,
       desc = c("Default of Credit Card Clients, UCI Machine Learning Repository.",
                "Default of Credit Card Clients, UCI Machine Learning Repository."))
)

# ---------- Navegación: rutas del tablero (en orden) ---------------------------
NAV <- list(
  list("/", c("Inicio", "Home"), "home"),
  list("/introduccion", c("Introducción", "Introduction"), "info"),
  list("/problema", c("Problema y Objetivos", "Problem and Objectives"), "target"),
  list("/marco", c("Marco Teórico", "Theoretical Framework"), "book"),
  list("/univariado", c("EDA Univariado", "Univariate EDA"), "bars"),
  list("/multivariado", c("EDA Multivariado", "Multivariate EDA"), "scatter"),
  list("/modelos", c("Modelos", "Models"), "layers"),
  list("/predecir", c("Predecir", "Predict"), "gauge"),
  list("/conclusiones", c("Conclusiones", "Conclusions"), "flag"),
  list("/enlaces", c("Enlaces", "Links"), "link"),
  list("/equipo", c("Equipo", "Team"), "users")
)
NAV_PATHS <- vapply(NAV, `[[`, "", 1)

# ---------- Paleta (la misma del Dash) -----------------------------------------
DEEP_NAVY <- "#1A233D"; NAVY <- "#36456D"; PALE_GOLD <- "#D2BB89"; WARM_GOLD <- "#B88F3D"
CREAM <- "#F3EFE7"; WHITE <- "#FFFFFF"; GREY_BLUE <- "#8089A0"; MID_BLUE <- "#66749C"
BROWN <- "#8A6E3A"; GOLD_SOFT <- "#C9A85F"; GOLD_MID <- "#9A7A33"; GOLD_DARK <- "#6E5628"
BRIGHT_GOLD <- "#F2C14E"
MONO <- DEEP_NAVY
PALETTE <- c(DEEP_NAVY, WARM_GOLD, NAVY, PALE_GOLD, GREY_BLUE, BROWN)
SERIES6 <- c(DEEP_NAVY, NAVY, MID_BLUE, PALE_GOLD, WARM_GOLD, BROWN)
DIVERGING <- list(c(0, DEEP_NAVY), c(0.5, CREAM), c(1, WARM_GOLD))
SEQ_GOLD <- list(c(0, CREAM), c(0.5, PALE_GOLD), c(1, WARM_GOLD))
FONT_FAMILY <- "Inter, 'Segoe UI', Roboto, Arial, sans-serif"

rgba <- function(hex, a) {
  v <- grDevices::col2rgb(hex)
  sprintf("rgba(%d,%d,%d,%s)", v[1], v[2], v[3], format(a))
}
DEEP_RGBA <- "rgba(26,35,61,"   # prefijo para líneas de cuadrícula translúcidas
