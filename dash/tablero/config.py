# -*- coding: utf-8 -*-
"""Configuración general: autores, equipo, enlaces, rutas, paleta, plantilla de Plotly e idioma (ES/EN).

Es el único archivo que hay que tocar para cambiar nombres, correos o enlaces.
"""

import plotly.io as pio
import warnings
from contextvars import ContextVar
from pathlib import Path

warnings.filterwarnings("ignore")

# =============================================================================
# IDIOMA (español / inglés)
# =============================================================================
# Cada callback que dibuja texto recibe el idioma elegido (dcc.Store "lang") y lo fija aquí;
# tx("texto", "text") devuelve la versión del idioma activo. Los textos que se guardan en
# constantes van como pares (es, en) y se leen con L(par).
LANG = ContextVar("lang", default="es")


def set_lang(lang):
    LANG.set("en" if lang == "en" else "es")


def tx(es, en):
    return en if LANG.get() == "en" else es


def L(v):
    """Texto bilingüe guardado como (es, en); cualquier otro valor se devuelve igual."""
    return tx(*v) if isinstance(v, tuple) and len(v) == 2 else v

# =============================================================================
# CONFIGURACIÓN GENERAL
# =============================================================================


# === CAMBIAR AQUÍ NOMBRES Y CORREOS ==========================================
AUTHORS = [
    {"name": "Katherin Barrera",
     "email": "lkatherin@uninorte.edu.co"},
    {"name": "Valeria Florez",
     "email": "florezvaleria@uninorte.edu.co"},
]
INSTITUTION = ("Universidad del Norte · Ciencia de Datos", "Universidad del Norte · Data Science")   # <- editable
COURSE = ("Proyecto de Análisis Exploratorio de Datos (EDA)", "Exploratory Data Analysis (EDA) Project")  # <- editable

# === CAMBIAR AQUÍ EL EQUIPO (página /equipo) ===================================
# Fotos en assets/team/ (Dash sirve la carpeta assets/ automáticamente).
TEAM = [
    {"name": "Katherin Barrera López", "short": "Kath",
     "role": ("Estudiante de Ciencia de Datos · Universidad del Norte",
              "Data Science student · Universidad del Norte"),
     "bio": ("Me gusta convertir datos en historias claras: del ETL y el análisis exploratorio "
             "a tableros interactivos como este.",
             "I like turning data into clear stories: from ETL and exploratory analysis "
             "to interactive dashboards like this one."),
     "photo": "team/katherin.jpg", "card_no": "0001",
     "github": "https://github.com/KathBarrera",
     "linkedin": "https://www.linkedin.com/in/katherin-barrera-l%C3%B3pez-454b47392/",
     "email": "lkatherin@uninorte.edu.co"},
    {"name": "Valeria Florez Sarmiento", "short": "Vale",
     "role": ("Estudiante de Ciencia de Datos · Universidad del Norte",
              "Data Science student · Universidad del Norte"),
     "bio": ("Me apasiona el aprendizaje automático reproducible: del pipeline de modelado "
             "al Jupyter Book que documenta el proyecto.",
             "I am passionate about reproducible machine learning: from the modeling pipeline "
             "to the Jupyter Book that documents the project."),
     "photo": "team/valeria.jpg", "card_no": "0002",
     "github": "https://github.com/valeriaflorezs",
     "linkedin": "https://www.linkedin.com/in/valeriaflorezs/",
     "email": "florezvaleria@uninorte.edu.co"},
]

# --- Enlaces: libro (Jupyter Book), notebooks y repositorios -------------------
REPO_PROJECT = "https://github.com/valeriaflorezs/Credit_Card_Project"
REPO_DASH = "https://github.com/KathBarrera/dash_credit_kv"
BOOK_URL = "https://valeriaflorezs.github.io/Credit_Card_Project/"
# Video del proyecto (página Enlaces). Pega aquí el enlace de YouTube, de cualquier forma:
# https://www.youtube.com/watch?v=XXXX, https://youtu.be/XXXX o https://www.youtube.com/shorts/XXXX.
# Mientras esté vacío, la página muestra un espacio con «Video próximamente».
PROJECT_VIDEO_URL = "https://youtu.be/Cgmp3mpy-kk"
NOTEBOOK_URL = BOOK_URL + "notebooks/00_eda.html"
NOTEBOOKS = [
    ("00", ("EDA: Análisis Exploratorio de Datos", "EDA: Exploratory Data Analysis"), "00_eda.html",
     ("Calidad de los datos, distribuciones y relaciones entre variables.",
      "Data quality, distributions and relationships between variables.")),
    ("01", ("Modelo base: Regresión Logística", "Baseline model: Logistic Regression"), "01_baseline_logistic.html",
     ("Modelo de referencia contra el cual se comparan los demás.",
      "Reference model against which the others are compared.")),
    ("02", ("Setup Check", "Setup Check"), "02_setup_check.html",
     ("Verificación del entorno y de las dependencias.", "Check of the environment and dependencies.")),
    ("03", ("Desarrollo y prueba del pipeline completo", "Development and testing of the full pipeline"),
     "03_pipeline_dev.html",
     ("Construcción y prueba del flujo de datos y modelado.", "Building and testing the data and modeling flow.")),
    ("04", ("Ejecutar experimentos", "Running the experiments"), "04_run_experiments.html",
     ("Ejecución de los experimentos del diseño factorial.", "Execution of the factorial-design experiments.")),
    ("05", ("Análisis de resultados", "Results analysis"), "05_results_analysis.html",
     ("Comparación de los resultados de los experimentos.", "Comparison of the experiment results.")),
    ("06", ("Interpretabilidad (SHAP y LIME)", "Interpretability (SHAP and LIME)"), "06_interpretability.html",
     ("Qué variables explican las predicciones del modelo, en los 5 folds.",
      "Which variables explain the model's predictions, across the 5 folds.")),
    # 08 y 09 aún no están en el libro publicado (gh-pages se construyó el 2026-10-05): por ahora se
    # enlazan en GitHub. Cuando se reconstruya el libro, cambiar por "08_tabla_maestra_svm.html", etc.
    ("08", ("Tabla maestra y comparabilidad del SVM", "Master table and SVM comparability"),
     REPO_PROJECT + "/blob/main/notebooks/08_tabla_maestra_svm.ipynb",
     ("Las 112 combinaciones en una tabla y el reajuste del SVM en CPU.",
      "The 112 combinations in one table and the SVM refit on CPU.")),
    ("09", ("Curvas anytime y multi-fidelidad", "Anytime curves and multi-fidelity"),
     REPO_PROJECT + "/blob/main/notebooks/09_anytime_multifidelidad.ipynb",
     ("Costo de cada optimizador y Hyperband frente a Random Search.",
      "Cost of each optimizer and Hyperband versus Random Search.")),
]
DATA_URL = "https://archive.ics.uci.edu/dataset/350/default+of+credit+card+clients"
LINKS = [
    {"icon": "book", "title": ("Libro del proyecto", "Project book"), "url": BOOK_URL + "README.html",
     "desc": ("Jupyter Book con el README y los notebooks del pipeline.",
              "Jupyter Book with the README and the pipeline notebooks.")},
    {"icon": "notebook", "title": ("Notebook del EDA", "EDA notebook"), "url": NOTEBOOK_URL,
     "desc": ("Análisis exploratorio completo del que sale este tablero (00_eda).",
              "Full exploratory analysis this dashboard is based on (00_eda).")},
    {"icon": "tree", "title": ("Ficha del modelo (model card)", "Model card"), "url": BOOK_URL + "MODEL_CARD.html",
     "desc": ("Uso previsto de CS-FOF, datos de entrenamiento, métricas, limitaciones, riesgos y usos no recomendados.",
              "Intended use of CS-FOF, training data, metrics, limitations, risks and uses not recommended.")},
    {"icon": "database", "title": ("Declaración de los datos", "Data statement"), "url": BOOK_URL + "DATA_STATEMENT.html",
     "desc": ("Procedencia, licencia y sesgos conocidos del conjunto de datos.",
              "Provenance, license and known biases of the dataset.")},
    {"icon": "github", "title": ("Repositorio del proyecto", "Project repository"), "url": REPO_PROJECT,
     "desc": ("Pipeline de datos, notebooks, resultados de los experimentos y código fuente.",
              "Data pipeline, notebooks, experiment results and source code.")},
    {"icon": "github", "title": ("Repositorio del tablero", "Dashboard repository"), "url": REPO_DASH,
     "desc": ("Código fuente de esta aplicación Dash.", "Source code of this Dash app.")},
    {"icon": "database", "title": ("Datos originales (UCI)", "Original data (UCI)"), "url": DATA_URL,
     "desc": ("Default of Credit Card Clients, UCI Machine Learning Repository.",
              "Default of Credit Card Clients, UCI Machine Learning Repository.")},
]
# =============================================================================

PROJECT_TITLE = ("Riesgo de Incumplimiento en Tarjetas de Crédito", "Credit Card Default Risk")
PROJECT_SUBTITLE = ("Análisis Exploratorio · Default of Credit Card Clients (UCI)",
                    "Exploratory Analysis · Default of Credit Card Clients (UCI)")


# --- Paleta: los mismos colores de siempre, con la saturación reducida -------
def _rgba_prefix(h):
    r, g, b = (int(h[i:i + 2], 16) for i in (1, 3, 5))
    return f"rgba({r},{g},{b},"


DEEP_NAVY = "#1A233D"   # fondo / encabezados        (antes #0C1A41)
NAVY = "#36456D"        # botones / bordes           (antes #1B3071)
PALE_GOLD = "#D2BB89"   # detalles / acentos suaves  (antes #E8C871)
WARM_GOLD = "#B88F3D"   # métricas / destacados      (antes #C9930C)
CREAM = "#F3EFE7"       # fondo general              (antes #F9F0DE)
WHITE = "#FFFFFF"
GREY_BLUE = "#8089A0"   # auxiliar neutro
MID_BLUE = "#66749C"    # tonos intermedios para series con muchas categorías
BROWN = "#8A6E3A"
GOLD_SOFT = "#C9A85F"
GOLD_MID = "#9A7A33"
GOLD_DARK = "#6E5628"
BRIGHT_GOLD = "#F2C14E"  # punto del mejor modelo (dorado más luminoso)
DEEP_RGBA = _rgba_prefix(DEEP_NAVY)   # para gridlines y rellenos translúcidos
PALETTE = [DEEP_NAVY, WARM_GOLD, NAVY, PALE_GOLD, GREY_BLUE, BROWN]
SERIES6 = [DEEP_NAVY, NAVY, MID_BLUE, PALE_GOLD, WARM_GOLD, BROWN]  # 6 meses
DIVERGING = [[0.0, DEEP_NAVY], [0.5, CREAM], [1.0, WARM_GOLD]]
SEQ_GOLD = [[0.0, CREAM], [0.5, PALE_GOLD], [1.0, WARM_GOLD]]

# Color único de las gráficas del EDA Univariado que no necesitan leyenda:
# azul profundo en modo claro (en modo oscuro se cambia a dorado pálido en `themed`).
MONO = DEEP_NAVY

# --- Plantilla Plotly con la paleta -----------------------------------------
pio.templates["navy_gold"] = pio.templates["plotly_white"]
pio.templates["navy_gold"].layout.colorway = PALETTE
pio.templates["navy_gold"].layout.paper_bgcolor = WHITE
pio.templates["navy_gold"].layout.plot_bgcolor = CREAM
pio.templates["navy_gold"].layout.font = dict(
    color=DEEP_NAVY, family="Inter, 'Segoe UI', Roboto, Arial, sans-serif")
pio.templates.default = "navy_gold"

# --- Origen de los datos -----------------------------------------------------
try:
    BASE_DIR = Path(__file__).resolve().parent.parent   # la carpeta dash/
except NameError:  # por si se ejecuta en una celda interactiva
    BASE_DIR = Path.cwd()

LOCAL_CANDIDATES = [
    BASE_DIR / "default_of_credit_card_clients.xls",
    BASE_DIR / "data" / "default_of_credit_card_clients.xls",
    BASE_DIR / "default_of_credit_card_clients.csv",
    BASE_DIR / "data" / "default_of_credit_card_clients.csv",
]
UCI_URL = ("https://archive.ics.uci.edu/ml/machine-learning-databases/00350/"
           "default%20of%20credit%20card%20clients.xls")

# --- Páginas del menú: (ruta, título es/en, ícono). Las usan la barra lateral, el enrutador y Kyo ---
NAV = [("/", ("Inicio", "Home"), "home"), ("/introduccion", ("Introducción", "Introduction"), "info"),
       ("/problema", ("Problema y Objetivos", "Problem and Objectives"), "target"),
       ("/marco", ("Marco Teórico", "Theoretical Framework"), "book"),
       ("/univariado", ("EDA Univariado", "Univariate EDA"), "bars"),
       ("/multivariado", ("EDA Multivariado", "Multivariate EDA"), "scatter"),
       ("/modelos", ("Modelos", "Models"), "layers"),
       ("/modelo-original", ("Modelo original", "Original model"), "tree"),
       ("/predecir", ("Predecir", "Predict"), "gauge"),
       ("/conclusiones", ("Conclusiones", "Conclusions"), "flag"),
       ("/enlaces", ("Enlaces", "Links"), "link"), ("/equipo", ("Equipo", "Team"), "users")]
