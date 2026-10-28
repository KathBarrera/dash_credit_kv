# -*- coding: utf-8 -*-
"""
===============================================================================
 DASHBOARD EDA — DEFAULT OF CREDIT CARD CLIENTS (UCI, Taiwán 2005)
 Python · Dash · Plotly
===============================================================================
 Ejecución local (Visual Studio Code):
     1) pip install -r requirements.txt
     2) Deja este archivo junto a `default_of_credit_card_clients.xls`
        (o dentro de una carpeta `data/`). Si no lo encuentra, lo descarga
        automáticamente desde el repositorio UCI.
     3) python app.py   ->   http://127.0.0.1:8050

 Estructura del código
     0. Configuración (AUTORES, ENLACES, rutas, paleta)  <- editar nombres y links aquí
     1. Carga y limpieza de datos (igual que el notebook 00_eda.ipynb)
     2. Utilidades (formato, estadísticos, estilos de figuras)
     3. Figuras + interpretaciones: EDA Univariado
     4. Figuras + interpretaciones: EDA Multivariado
        4a. Modelos (resultados de results/model_results.csv)
        4a-bis. Predecir (carga el modelo serializado modelo/modelo_credito.pkl)
     5. Componentes de interfaz (tarjetas, KPIs, interpretaciones)
     6. Páginas (Portada, Introducción, Problema, Marco, Univariado, Multivariado, Modelos, Predecir,
        Enlaces, Equipo)
     7. Aplicación, CSS, navegación y callbacks
        (incluye el asistente Kyo: panel derecho y mascota; su lógica está en asistente/)
===============================================================================
"""

import json
import sys
import warnings
from pathlib import Path
from urllib.parse import quote

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
from plotly.subplots import make_subplots
from scipy import stats
from dash import ALL, Dash, Input, Output, State, ctx, dcc, html, no_update

warnings.filterwarnings("ignore")

# =============================================================================
# 0. CONFIGURACIÓN GENERAL
# =============================================================================

# === CAMBIAR AQUÍ NOMBRES Y CORREOS ==========================================
AUTHORS = [
    {"name": "Katherin Barrera",
     "email": "lkatherin@uninorte.edu.co"},
    {"name": "Valeria Florez",
     "email": "florezvaleria@uninorte.edu.co"},
]
INSTITUTION = "Universidad del Norte · Ciencia de Datos"   # <- editable
COURSE = "Proyecto de Análisis Exploratorio de Datos (EDA)"  # <- editable

# === CAMBIAR AQUÍ EL EQUIPO (página /equipo) ===================================
# Fotos en assets/team/ (Dash sirve la carpeta assets/ automáticamente).
TEAM = [
    {"name": "Katherin Barrera López", "short": "Kath",
     "role": "Estudiante de Ciencia de Datos · Universidad del Norte",
     "bio": "Me gusta convertir datos en historias claras: del ETL y el análisis exploratorio "
            "a tableros interactivos como este.",
     "photo": "team/katherin.jpg", "card_no": "0001",
     "github": "https://github.com/KathBarrera",
     "linkedin": "https://www.linkedin.com/in/katherin-barrera-l%C3%B3pez-454b47392/",
     "email": "lkatherin@uninorte.edu.co"},
    {"name": "Valeria Florez Sarmiento", "short": "Vale",
     "role": "Estudiante de Ciencia de Datos · Universidad del Norte",
     "bio": "Me apasiona el aprendizaje automático reproducible: del pipeline de modelado "
            "al Jupyter Book que documenta el proyecto.",
     "photo": "team/valeria.jpg", "card_no": "0002",
     "github": "https://github.com/valeriaflorezs",
     "linkedin": "https://www.linkedin.com/in/valeriaflorezs/",
     "email": "florezvaleria@uninorte.edu.co"},
]

# --- Enlaces: libro (Jupyter Book), notebooks y repositorios -------------------
REPO_PROJECT = "https://github.com/valeriaflorezs/Credit_Card_Project"
REPO_DASH = "https://github.com/KathBarrera/dash_credit_kv"
BOOK_URL = "https://valeriaflorezs.github.io/Credit_Card_Project/"
NOTEBOOK_URL = BOOK_URL + "notebooks/00_eda.html"
NOTEBOOKS = [
    ("00", "EDA: Análisis Exploratorio de Datos", "00_eda.html", "Calidad de los datos, distribuciones y relaciones entre variables."),
    ("01", "Modelo base: Regresión Logística", "01_baseline_logistic.html", "Modelo de referencia contra el cual se comparan los demás."),
    ("02", "Setup Check", "02_setup_check.html", "Verificación del entorno y de las dependencias."),
    ("03", "Desarrollo y prueba del pipeline completo", "03_pipeline_dev.html", "Construcción y prueba del flujo de datos y modelado."),
    ("04", "Ejecutar experimentos", "04_run_experiments.html", "Ejecución de los experimentos del diseño factorial."),
    ("05", "Análisis de resultados", "05_results_analysis.html", "Comparación de los resultados de los experimentos."),
    ("06", "Interpretabilidad (SHAP y LIME)", "06_interpretability.html", "Qué variables explican las predicciones del modelo."),
]
DATA_URL = "https://archive.ics.uci.edu/dataset/350/default+of+credit+card+clients"
LINKS = [
    {"icon": "book", "title": "Libro del proyecto", "url": BOOK_URL + "README.html",
     "desc": "Jupyter Book con el README y los siete notebooks del pipeline."},
    {"icon": "notebook", "title": "Notebook del EDA", "url": NOTEBOOK_URL,
     "desc": "Análisis exploratorio completo del que sale este tablero (00_eda)."},
    {"icon": "github", "title": "Repositorio del proyecto", "url": REPO_PROJECT,
     "desc": "Pipeline de datos, notebooks, resultados de los experimentos y código fuente."},
    {"icon": "github", "title": "Repositorio del tablero", "url": REPO_DASH,
     "desc": "Código fuente de esta aplicación Dash."},
    {"icon": "database", "title": "Datos originales (UCI)", "url": DATA_URL,
     "desc": "Default of Credit Card Clients, UCI Machine Learning Repository."},
]
# =============================================================================

PROJECT_TITLE = "Riesgo de Incumplimiento en Tarjetas de Crédito"
PROJECT_SUBTITLE = "Análisis Exploratorio · Default of Credit Card Clients (UCI)"


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
    BASE_DIR = Path(__file__).resolve().parent
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

# =============================================================================
# 1. CARGA Y LIMPIEZA DE DATOS (mismas decisiones que el notebook 00_eda.ipynb)
# =============================================================================
TARGET = "default_payment_next_month"
PAY_COLS = ["PAY_0", "PAY_2", "PAY_3", "PAY_4", "PAY_5", "PAY_6"]
BILL_COLS = [f"BILL_AMT{i}" for i in range(1, 7)]
PAYAMT_COLS = [f"PAY_AMT{i}" for i in range(1, 7)]
NUM_COLS = ["LIMIT_BAL", "AGE"] + PAY_COLS + BILL_COLS + PAYAMT_COLS
CAT_COLS = ["SEX", "EDUCATION", "MARRIAGE"]
DISCRETE = CAT_COLS + PAY_COLS + [TARGET]   # variables tratadas como categorías


def _read_any(src):
    """Lee .xls/.xlsx/.csv tolerando la fila extra de encabezado del archivo UCI."""
    s = str(src).lower()
    if s.endswith(".csv"):
        d = pd.read_csv(src)
        if "LIMIT_BAL" not in d.columns:
            d = pd.read_csv(src, header=1)
    else:
        d = pd.read_excel(src, header=1)
        if "LIMIT_BAL" not in d.columns:
            d = pd.read_excel(src, header=0)
    return d


def load_raw():
    """Busca el archivo local; si no existe, lo descarga desde UCI."""
    for p in LOCAL_CANDIDATES:
        if p.exists():
            print(f"[datos] leyendo {p}")
            return _read_any(p)
    print("[datos] archivo local no encontrado; descargando desde UCI ...")
    return _read_any(UCI_URL)


def prepare(raw):
    """Limpieza: nombres, duplicados, categorías no documentadas."""
    d = raw.copy()
    # nombre de la variable objetivo (varía según la fuente)
    tcol = [c for c in d.columns if "default" in str(c).lower()][0]
    d = d.rename(columns={tcol: TARGET, "PAY_1": "PAY_0"})
    d = d.drop(columns=["ID"], errors="ignore")

    info = {"filas_originales": len(d)}
    d = d.drop_duplicates().reset_index(drop=True)             # 35 duplicados exactos
    info["duplicados"] = info["filas_originales"] - len(d)

    # categorías no documentadas -> "Otros" (EDUCATION 0,5,6 -> 4 ; MARRIAGE 0 -> 3)
    info["edu_reagrupadas"] = int(d["EDUCATION"].isin([0, 5, 6]).sum())
    info["mar_reagrupadas"] = int((d["MARRIAGE"] == 0).sum())
    d["EDUCATION"] = d["EDUCATION"].replace({0: 4, 5: 4, 6: 4})
    d["MARRIAGE"] = d["MARRIAGE"].replace({0: 3})

    info["bill_neg_clientes"] = int((d[BILL_COLS] < 0).any(axis=1).sum())
    return d, info


df, DATA_INFO = prepare(load_raw())

# Grupos de edad (para el análisis AGE vs. PAY)
AGE_BINS = [20, 25, 30, 35, 40, 45, 50, 55, 60, 80]
AGE_LABELS = ["21–25", "26–30", "31–35", "36–40", "41–45",
              "46–50", "51–55", "56–60", "61+"]
df["AGE_GRP"] = pd.cut(df["AGE"], bins=AGE_BINS, labels=AGE_LABELS)

# Etiquetas de categorías
CAT_LABELS = {
    "SEX": {1: "Hombre", 2: "Mujer"},
    "EDUCATION": {1: "Posgrado", 2: "Universidad", 3: "Secundaria", 4: "Otros"},
    "MARRIAGE": {1: "Casado", 2: "Soltero", 3: "Otros"},
    TARGET: {0: "No default", 1: "Default"},
}

# Meses de referencia del dataset (abril–septiembre de 2005)
_M = {1: "Sep", 2: "Ago", 3: "Jul", 4: "Jun", 5: "May", 6: "Abr"}
MONTH_ORDER = ["PAY_6", "PAY_5", "PAY_4", "PAY_3", "PAY_2", "PAY_0"]   # cronológico
MONTH_LBL = ["Abr", "May", "Jun", "Jul", "Ago", "Sep"]


def pretty(col):
    """Nombre legible de cada variable (para menús y ejes)."""
    if col == "LIMIT_BAL":
        return "LIMIT_BAL · Límite de crédito (NT$)"
    if col == "AGE":
        return "AGE · Edad (años)"
    if col == "SEX":
        return "SEX · Sexo"
    if col == "EDUCATION":
        return "EDUCATION · Nivel educativo"
    if col == "MARRIAGE":
        return "MARRIAGE · Estado civil"
    if col == TARGET:
        return "default · Incumplimiento próximo mes"
    if col == "PAY_0":
        return "PAY_0 · Estado de pago (Sep)"
    if col.startswith("PAY_AMT"):
        return f"{col} · Monto pagado ({_M[int(col[-1])]})"
    if col.startswith("PAY_"):
        return f"{col} · Estado de pago ({_M[int(col[-1]) ]})"
    if col.startswith("BILL_AMT"):
        return f"{col} · Monto facturado ({_M[int(col[-1])]})"
    return col


def as_cat(col):
    """Devuelve la columna como categoría ordenada con etiquetas legibles."""
    if col in CAT_LABELS:
        order = list(CAT_LABELS[col].values())
        return pd.Categorical(df[col].map(CAT_LABELS[col]), categories=order, ordered=True)
    vals = sorted(df[col].unique())
    return pd.Categorical(df[col].astype(int).astype(str),
                          categories=[str(int(v)) for v in vals], ordered=True)


def cat_order(col):
    return list(as_cat(col).categories)


# =============================================================================
# 2. UTILIDADES
# =============================================================================
def nt(x):
    """Formato de dinero en dólares taiwaneses."""
    return f"-NT${abs(x):,.0f}" if x < 0 else f"NT${x:,.0f}"


def sig(p):
    return "p<0.001" if p < 0.001 else f"p={p:.3f}"


def is_money(col):
    return col == "LIMIT_BAL" or col.startswith("BILL_AMT") or col.startswith("PAY_AMT")


def fmt_val(col, v):
    return nt(v) if is_money(col) else f"{v:,.1f}"


def style_fig(fig, h=460, legend_top=True, **kw):
    """Estilo común de todas las figuras."""
    fig.update_layout(
        height=h, margin=dict(l=55, r=30, t=70, b=50),
        title_font=dict(size=16, color=DEEP_NAVY),
        hoverlabel=dict(bgcolor=DEEP_NAVY, font_color=WHITE),
        **kw)
    if legend_top:
        fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.0,
                                      xanchor="right", x=1))
    fig.update_xaxes(gridcolor=f"{DEEP_RGBA}0.08)", zeroline=False)
    fig.update_yaxes(gridcolor=f"{DEEP_RGBA}0.08)", zeroline=False)
    return fig


def tukey_outliers_pct(s):
    q1, q3 = s.quantile([0.25, 0.75])
    iqr = q3 - q1
    return ((s < q1 - 1.5 * iqr) | (s > q3 + 1.5 * iqr)).mean() * 100


def cramers_v(ct):
    chi2 = stats.chi2_contingency(ct, correction=False)[0]
    n = ct.values.sum()
    k = min(ct.shape) - 1
    return float(np.sqrt(chi2 / (n * k))) if k > 0 else 0.0


def winsorize(s, lo=0.01, hi=0.99):
    return s.clip(s.quantile(lo), s.quantile(hi))


GLOBAL_RATE = df[TARGET].mean()


# =============================================================================
# 3. EDA UNIVARIADO: FIGURAS E INTERPRETACIONES
# =============================================================================
def fig_target():
    """Barras de la variable objetivo con conteo y porcentaje (un solo color)."""
    vc = df[TARGET].value_counts().sort_index()
    pr = vc / vc.sum()
    fig = go.Figure(go.Bar(
        x=["No default (0)", "Default (1)"], y=vc.values,
        marker_color=MONO,
        text=[f"{v:,}<br><b>{p:.1%}</b>" for v, p in zip(vc.values, pr.values)],
        textposition="outside",
        hovertemplate="%{x}<br>%{y:,} clientes<extra></extra>"))
    fig.update_layout(title="Variable objetivo: default payment next month",
                      yaxis_title="Número de clientes", showlegend=False)
    fig.update_yaxes(range=[0, vc.max() * 1.18])
    return style_fig(fig, 430, legend_top=False)


def interp_target():
    vc = df[TARGET].value_counts()
    p1, p0 = vc[1] / len(df), vc[0] / len(df)
    ratio = vc[0] / vc[1]
    basic = (f"Aproximadamente {p1 * 100:.0f} de cada 100 clientes ({vc[1]:,} personas) no pagó "
             f"la tarjeta al mes siguiente. El resto ({p0:.1%}) sí cumplió. Hay "
             f"muchos más clientes cumplidos que incumplidos, lo que hay que tener en cuenta al construir modelos.")
    tech = (f"Desbalance de clases: {p0:.1%} (clase 0) vs. {p1:.1%} (clase 1), razón ≈ {ratio:.1f}:1. "
            "Un clasificador sin ajustes tenderá a favorecer la clase mayoritaria; se recomienda "
            "class_weight='balanced', remuestreo (SMOTE/ADASYN) o umbrales ajustados, y evaluar con "
            "AUC-ROC, F1 y recall de la clase 1 en lugar de accuracy.")
    return basic, tech


def fig_uni(col, clip):
    """Distribución univariada de cualquier variable (numérica o categórica), un solo color."""
    if col in DISCRETE:
        cats = as_cat(col)
        vc = pd.Series(cats).value_counts().reindex(list(cats.categories))
        pr = vc / vc.sum()
        fig = go.Figure(go.Bar(
            x=list(vc.index), y=vc.values, marker_color=MONO,
            text=[f"{p:.1%}" for p in pr.values], textposition="outside",
            hovertemplate=f"{col}: %{{x}}<br>Clientes: %{{y:,}}<extra></extra>"))
        fig.update_layout(title=f"Frecuencia de {pretty(col)}",
                          xaxis_title=col, yaxis_title="Número de clientes",
                          showlegend=False)
        fig.update_xaxes(type="category", categoryorder="array", categoryarray=list(vc.index))
        fig.update_yaxes(range=[0, vc.max() * 1.15])
        return style_fig(fig, 470, legend_top=False)

    s = df[col]
    view = s[s <= s.quantile(0.99)] if clip else s
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                        row_heights=[0.74, 0.26], vertical_spacing=0.03)
    fig.add_trace(go.Histogram(x=view, nbinsx=60, marker_color=MONO,
                               marker_line_color=WHITE, marker_line_width=0.4,
                               name="Frecuencia", showlegend=False), row=1, col=1)
    fig.add_trace(go.Box(x=view, name="", marker_color=MONO, boxpoints=False,
                         boxmean=True, showlegend=False), row=2, col=1)
    fig.add_vline(x=s.median(), line_dash="dash", line_color=WARM_GOLD, row=1, col=1,
                  annotation_text="mediana", annotation_font_color=WARM_GOLD)
    suf = " (vista recortada al P99)" if clip else ""
    fig.update_layout(title=f"Distribución de {pretty(col)}{suf}")
    fig.update_yaxes(title_text="Frecuencia", row=1, col=1)
    fig.update_xaxes(title_text=pretty(col), row=2, col=1)
    return style_fig(fig, 520, legend_top=False)


def interp_uni(col):
    """Interpretación básica y técnica para la variable elegida."""
    n = len(df)
    # ---------- variables discretas ----------
    if col in DISCRETE:
        cats = as_cat(col)
        vc = pd.Series(cats).value_counts().reindex(list(cats.categories))
        pr = vc / vc.sum()
        top = pr.idxmax()
        if col in PAY_COLS:
            al_dia = df[col].le(0).mean()
            atraso = df[col].ge(1).mean()
            basic = (f"En {_M[int(col[-1]) if col != 'PAY_0' else 1]}, {al_dia:.0%} de los clientes estaba al día "
                     f"(valores 0 o menores) y {atraso:.0%} tenía al menos un mes de atraso. "
                     f"El valor más común es {top} ({pr[top]:.0%}).")
            tech = (f"Variable ordinal con {len(vc)} niveles; moda = {top} ({pr[top]:.1%}). "
                    f"Los valores −2, −1 y 0 concentran {df[col].le(0).mean():.1%} de los casos; "
                    f"atraso ≥1 mes: {atraso:.1%}. La definición exacta de −2/−1/0 no está "
                    "estandarizada en la fuente: se conservan sin recodificar y no se sobre-interpreta "
                    "la frontera entre ellos. Se recomienda tratarla como ordinal/categórica (dummies) "
                    "pues el efecto de pasar de 'al día' a 1 mes de atraso no es lineal.")
        elif col == TARGET:
            return interp_target()
        else:
            parts = ", ".join(f"{k} {v:.1%}" for k, v in pr.items())
            basic = (f"La categoría más frecuente es «{top}» con {pr[top]:.0%} de los clientes. "
                     f"Distribución completa: {parts}.")
            tech = (f"Variable categórica nominal de {len(vc)} niveles; moda «{top}» ({pr[top]:.1%}). "
                    f"Frecuencias: {parts}. Las categorías no documentadas del archivo original "
                    "se reagruparon en «Otros» (EDUCATION 0/5/6 → 4; MARRIAGE 0 → 3).")
        return basic, tech

    # ---------- variables numéricas ----------
    s = df[col]
    q1, q3 = s.quantile([0.25, 0.75])
    iqr = q3 - q1
    sk, ku = stats.skew(s), stats.kurtosis(s)
    out = tukey_outliers_pct(s)
    f = lambda v: fmt_val(col, v)
    if sk > 1:
        shape = (f"La mayoría de clientes se ubica entre {f(q1)} y {f(q3)}, pero unos pocos tienen valores "
                 f"mucho más altos (hasta {f(s.max())}). Por eso el promedio ({f(s.mean())}) queda por "
                 f"encima de lo típico (mediana {f(s.median())}).")
    elif sk > 0.5:
        shape = (f"La mitad de los clientes tiene {f(s.median())} o menos; la distribución se inclina "
                 f"ligeramente hacia valores altos (promedio {f(s.mean())}).")
    else:
        shape = (f"Los valores se reparten de forma bastante equilibrada alrededor de {f(s.median())} "
                 f"(promedio {f(s.mean())}).")
    extra = ""
    if col.startswith("BILL_AMT") and (s < 0).any():
        extra = f" Un {(s < 0).mean():.1%} de los clientes tiene saldo a favor (monto negativo)."
    if col.startswith("PAY_AMT"):
        extra = f" Un {(s == 0).mean():.1%} de los clientes no hizo ningún pago ese mes."
    basic = shape + extra
    rec = ("Su asimetría extrema justifica una transformación logarítmica (con signo) antes de modelar."
           if abs(sk) > 2 else "No requiere transformaciones drásticas por forma.")
    tech = (f"n = {n:,}; media = {f(s.mean())}; mediana = {f(s.median())}; σ = {f(s.std())}; "
            f"IQR = {f(iqr)}; asimetría = {sk:.2f}; curtosis = {ku:.2f}; outliers de Tukey = {out:.1f}%. "
            f"{rec}")
    return basic, tech


# ----- Distribuciones de variables cuantitativas por familia ------------------
FAMILIES = {
    "LIMIT_BAL": ["LIMIT_BAL"],
    "AGE": ["AGE"],
    "BILL_AMT": BILL_COLS,
    "PAY_AMT": PAYAMT_COLS,
}


def kde_curve(x, lo, hi, n=220):
    x = x[(x >= lo) & (x <= hi)]
    if len(x) > 6000:
        x = x.sample(6000, random_state=1)
    grid = np.linspace(lo, hi, n)
    try:
        return grid, stats.gaussian_kde(x)(grid)
    except Exception:
        return grid, np.zeros_like(grid)


def _rgba(hex_color, a):
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{a})"


def fig_quant(family, kind):
    """LIMIT_BAL y AGE: un solo color. BILL_AMT y PAY_AMT: un color por mes (con leyenda)."""
    cols = FAMILIES[family]
    allv = df[cols].values.ravel()
    lo, hi = np.percentile(allv, 1), np.percentile(allv, 99)   # vista P1–P99
    fig = go.Figure()
    for i, c in enumerate(cols):
        color = SERIES6[i % 6] if len(cols) > 1 else MONO
        name = c
        if kind == "hist":
            v = df[c][(df[c] >= lo) & (df[c] <= hi)]
            fig.add_trace(go.Histogram(x=v, nbinsx=50, name=name, marker_color=color,
                                       opacity=0.65 if len(cols) > 1 else 0.95,
                                       showlegend=len(cols) > 1))
        elif kind == "box":
            fig.add_trace(go.Box(y=df[c], name=name, marker_color=color,
                                 boxpoints=False, boxmean=True, showlegend=len(cols) > 1))
        else:  # densidad
            g, d = kde_curve(df[c], lo, hi)
            fig.add_trace(go.Scatter(x=g, y=d, name=name, mode="lines",
                                     line=dict(color=color, width=2.5),
                                     fill="tozeroy",
                                     fillcolor=_rgba(color, 0.18),
                                     showlegend=len(cols) > 1))
    if kind == "hist":
        fig.update_layout(barmode="overlay", xaxis_title=family, yaxis_title="Frecuencia")
        ttl = "Histograma"
    elif kind == "box":
        fig.update_layout(yaxis_title=family)
        ttl = "Boxplot"
        if family in ("BILL_AMT", "PAY_AMT"):
            fig.update_yaxes(range=[min(0, lo * 1.1), hi * 1.1])
    else:
        fig.update_layout(xaxis_title=family, yaxis_title="Densidad")
        ttl = "Densidad (KDE)"
    sub = "" if kind == "box" and family not in ("BILL_AMT", "PAY_AMT") else " · vista P1–P99"
    fig.update_layout(title=f"{ttl} de {family}{sub}")
    return style_fig(fig, 480, legend_top=len(cols) > 1)


def interp_quant(family):
    if family == "LIMIT_BAL":
        return interp_uni("LIMIT_BAL")
    if family == "AGE":
        return interp_uni("AGE")
    cols = FAMILIES[family]
    med = df[cols].median()
    sk = df[cols].apply(stats.skew)
    if family == "BILL_AMT":
        basic = (f"Los seis meses de facturación se parecen mucho entre sí: la mediana ronda "
                 f"{nt(med.min())}–{nt(med.max())} y casi todos los meses tienen unos pocos clientes con "
                 f"saldos muy altos. Además, {df[cols].lt(0).any(axis=1).mean():.1%} de los clientes tuvo "
                 "saldo a favor (negativo) en algún mes.")
        tech = (f"Asimetría entre {sk.min():.2f} y {sk.max():.2f}; outliers de Tukey entre "
                f"{min(tukey_outliers_pct(df[c]) for c in cols):.1f}% y "
                f"{max(tukey_outliers_pct(df[c]) for c in cols):.1f}%. Distribuciones casi idénticas mes "
                "a mes (alta autocorrelación del saldo). Los montos negativos son económicamente válidos "
                "(pago en exceso) y no se eliminan. Esta redundancia anticipa multicolinealidad severa "
                "(ver VIF en el notebook / pestaña Multivariado).")
    else:
        zeros = df[cols].eq(0).mean()
        basic = (f"Los pagos son pequeños frente a las facturas: la mediana mensual va de "
                 f"{nt(med.min())} a {nt(med.max())}. Entre {zeros.min():.0%} y {zeros.max():.0%} "
                 "de los clientes no pagó nada en cada mes; unos pocos hacen pagos enormes.")
        tech = (f"Asimetría entre {sk.min():.1f} y {sk.max():.1f} (hasta ≈ {sk.max():.0f}), curtosis muy "
                f"alta y cola derecha extrema (máx. {nt(df[cols].max().max())}). La masa en cero "
                "(sin pago) y los valores extremos justifican transformación log con signo y "
                "métodos robustos (medianas, Mann-Whitney) antes de comparar grupos.")
    return basic, tech


# =============================================================================
# 4. EDA MULTIVARIADO: FIGURAS E INTERPRETACIONES
# =============================================================================
# ----- 4.1 Matriz de correlación: SOLO Spearman, sobre los datos originales ----
# Spearman trabaja con rangos: no exige linealidad ni normalidad, resiste los
# valores extremos y es adecuado para PAY_x (ordinales) y la variable objetivo
# (binaria). Al ser invariante a transformaciones monótonas, no se winsoriza.
_C = df[NUM_COLS + [TARGET]].rename(columns={TARGET: "default"})
CORR = _C.corr(method="spearman")


def fig_corr():
    c = CORR
    fig = go.Figure(go.Heatmap(
        z=c.values, x=c.columns, y=c.columns, colorscale=DIVERGING, zmid=0, zmin=-1, zmax=1,
        text=c.round(2).values, texttemplate="%{text}", textfont=dict(size=8),
        colorbar=dict(title="ρ", thickness=14),
        hovertemplate="%{y} vs %{x}<br>correlación (ρ): %{z:.3f}<extra></extra>"))
    fig.update_layout(title="Matriz de correlación de Spearman (datos originales)")
    fig.update_yaxes(autorange="reversed")
    return style_fig(fig, 740, legend_top=False)


def interp_corr():
    c = CORR
    iu = np.triu_indices(6, 1)
    bill = c.loc[BILL_COLS, BILL_COLS].values[iu]
    pay = c.loc[PAY_COLS, PAY_COLS].values[iu]
    pamt = c.loc[PAYAMT_COLS, PAYAMT_COLS].values[iu]
    tgt = c["default"].drop("default").abs().sort_values(ascending=False).head(4)
    tgt_txt = ", ".join(f"{k} ({c.loc[k, 'default']:+.2f})" for k in tgt.index)
    basic = ("Las seis facturas mensuales (BILL_AMT) se mueven casi igual: quien debe mucho un mes suele "
             "deber mucho al siguiente, por eso aparece un gran bloque dorado. Los estados de pago (PAY) "
             "también se parecen entre sí. En cambio, lo que realmente se pagó (PAY_AMT) casi no se "
             f"relaciona con nada. La variable más ligada al incumplimiento es {tgt.index[0]}.")
    tech = (f"Spearman (ρ): correlación entre BILL_AMT1–6 de {bill.min():.2f} a {bill.max():.2f} "
            f"(multicolinealidad severa; el VIF del notebook supera 20 en BILL_AMT2–5); entre PAY_x "
            f"de {pay.min():.2f} a {pay.max():.2f}; entre PAY_AMT de {pamt.min():.2f} a {pamt.max():.2f}. "
            f"Mayor asociación con default (|ρ|): {tgt_txt}. Se usa Spearman y no Pearson porque las variables "
            "monetarias son muy asimétricas y con colas extremas, PAY_x es ordinal y la variable objetivo es "
            "binaria; los rangos no exigen linealidad ni normalidad. Recomendación: no usar las seis BILL_AMT "
            "por separado en modelos lineales (usar nivel promedio + tendencia, solo la más reciente o PCA).")
    return basic, tech


# ----- 4.2 Tasa de default por EDUCATION / MARRIAGE / SEX ---------------------
def rate_table(col):
    g = df.groupby(col)[TARGET].agg(["mean", "size"])
    g.index = [CAT_LABELS[col][i] for i in g.index]
    return g


def fig_rates():
    fig = make_subplots(rows=1, cols=3, subplot_titles=["Nivel educativo", "Estado civil", "Sexo"],
                        shared_yaxes=True, horizontal_spacing=0.05)
    for j, col in enumerate(["EDUCATION", "MARRIAGE", "SEX"], start=1):
        t = rate_table(col)
        fig.add_trace(go.Bar(
            x=t.index, y=t["mean"], marker_color=[WARM_GOLD if r > GLOBAL_RATE else NAVY for r in t["mean"]],
            text=[f"{r:.1%}" for r in t["mean"]], textposition="outside", customdata=t["size"],
            hovertemplate="%{x}<br>Tasa de default: %{y:.1%}<br>Clientes: %{customdata:,}<extra></extra>",
            showlegend=False), row=1, col=j)
        fig.add_hline(y=GLOBAL_RATE, line_dash="dash", line_color=DEEP_NAVY, row=1, col=j)
    fig.add_annotation(x=1, y=GLOBAL_RATE, xref="x3 domain", yref="y", xanchor="right", yanchor="bottom",
                       text=f"Tasa global {GLOBAL_RATE:.1%}", showarrow=False, font=dict(color=DEEP_NAVY, size=11))
    fig.update_yaxes(tickformat=".0%", range=[0, 0.32], title_text="Tasa de default", col=1)
    fig.update_layout(title="Tasa de incumplimiento según perfil demográfico (dorado = por encima del promedio)")
    return style_fig(fig, 460, legend_top=False)


def interp_rates():
    te, tm, ts = rate_table("EDUCATION"), rate_table("MARRIAGE"), rate_table("SEX")
    chi = {}
    for col in ["EDUCATION", "MARRIAGE", "SEX"]:
        ct = pd.crosstab(df[col], df[TARGET])
        chi[col] = (*stats.chi2_contingency(ct)[:2], cramers_v(ct))
    top_e = te["mean"].idxmax()
    basic = (f"Los hombres incumplen un poco más ({ts.loc['Hombre', 'mean']:.1%}) que las mujeres "
             f"({ts.loc['Mujer', 'mean']:.1%}). Por educación, el grupo con más incumplimiento es "
             f"«{top_e}» ({te.loc[top_e, 'mean']:.1%}) y el menor es «{te['mean'].idxmin()}» "
             f"({te['mean'].min():.1%}). Las diferencias existen pero son moderadas: el perfil "
             "demográfico explica poco comparado con el historial de pagos.")
    tech = (f"χ² EDUCATION = {chi['EDUCATION'][0]:.1f} ({sig(chi['EDUCATION'][1])}, V de Cramér = "
            f"{chi['EDUCATION'][2]:.3f}); MARRIAGE = {chi['MARRIAGE'][0]:.1f} ({sig(chi['MARRIAGE'][1])}, "
            f"V = {chi['MARRIAGE'][2]:.3f}); SEX = {chi['SEX'][0]:.1f} ({sig(chi['SEX'][1])}, "
            f"V = {chi['SEX'][2]:.3f}). Con n ≈ {len(df):,} casi cualquier diferencia es significativa; "
            "los tamaños de efecto (V < 0.1) son pequeños, así que lo relevante es la magnitud y no el "
            "p-value. Tasas por MARRIAGE: " +
            ", ".join(f"{k} {v:.1%}" for k, v in tm["mean"].items()) + ".")
    return basic, tech


# ----- 4.3 Boxplot LIMIT_BAL por estado de default ----------------------------
def fig_limit_box(scale):
    fig = go.Figure()
    for k, name, color in [(0, "No default", DEEP_NAVY), (1, "Default", WARM_GOLD)]:
        fig.add_trace(go.Box(y=df.loc[df[TARGET] == k, "LIMIT_BAL"], name=name, marker_color=color,
                             boxmean=True, boxpoints="outliers", marker_size=3, line_width=1.6))
    fig.update_layout(title="Límite de crédito (LIMIT_BAL) según estado de incumplimiento",
                      yaxis_title="LIMIT_BAL (NT$)", showlegend=False)
    if scale == "log":
        fig.update_yaxes(type="log")
    return style_fig(fig, 470, legend_top=False)


def interp_limit():
    g0 = df.loc[df[TARGET] == 0, "LIMIT_BAL"]
    g1 = df.loc[df[TARGET] == 1, "LIMIT_BAL"]
    u, p = stats.mannwhitneyu(g0, g1, alternative="two-sided")
    tt, pt = stats.ttest_ind(g0, g1, equal_var=False)
    basic = (f"Los clientes que cayeron en default tenían, en la mitad de los casos, un límite de "
             f"{nt(g1.median())} o menos, frente a {nt(g0.median())} de quienes pagaron. Es decir, "
             "quienes incumplen suelen tener líneas de crédito más bajas.")
    tech = (f"Media: {nt(g0.mean())} (no default) vs. {nt(g1.mean())} (default); mediana "
            f"{nt(g0.median())} vs. {nt(g1.median())}. Mann-Whitney U = {u:,.0f} ({sig(p)}); "
            f"t de Welch = {tt:.2f} ({sig(pt)}). Diferencia significativa y de relevancia de negocio: "
            "un límite alto actúa como proxy de buena calificación crediticia previa. Distribución muy "
            "sesgada a la derecha, por eso se prefieren pruebas no paramétricas (alterna la escala log).")
    return basic, tech


# ----- 4.4 AGE vs. patrones de atraso -----------------------------------------
def fig_age(view):
    fig = go.Figure()
    if view == "lines":
        g = df.groupby("AGE_GRP", observed=True)[MONTH_ORDER].mean()
        cols = [DEEP_NAVY, NAVY, MID_BLUE, GREY_BLUE, PALE_GOLD, GOLD_SOFT, WARM_GOLD, GOLD_MID, GOLD_DARK]
        for i, grp in enumerate(g.index):
            fig.add_trace(go.Scatter(x=MONTH_LBL, y=g.loc[grp], mode="lines+markers", name=str(grp),
                                     line=dict(color=cols[i % len(cols)], width=2.4)))
        fig.update_layout(title="Atraso promedio (PAY) por mes y grupo de edad",
                          xaxis_title="Mes (abril → septiembre 2005)", yaxis_title="PAY promedio")
        return style_fig(fig, 470)
    if view == "heat":
        g = (df[MONTH_ORDER].ge(1).groupby(df["AGE_GRP"], observed=True).mean() * 100)
        fig.add_trace(go.Heatmap(
            z=g.values, x=MONTH_LBL, y=[str(i) for i in g.index], colorscale=SEQ_GOLD,
            text=g.round(1).values, texttemplate="%{text}%", colorbar=dict(title="% con atraso", thickness=14),
            hovertemplate="Edad %{y} · %{x}<br>%{z:.1f}% con atraso ≥1 mes<extra></extra>"))
        fig.update_layout(title="% de clientes con atraso (PAY ≥ 1) por grupo de edad y mes",
                          xaxis_title="Mes", yaxis_title="Grupo de edad")
        fig.update_yaxes(autorange="reversed")
        return style_fig(fig, 470, legend_top=False)
    g = df.groupby("AGE_GRP", observed=True)[TARGET].agg(["mean", "size"])
    fig.add_trace(go.Bar(x=[str(i) for i in g.index], y=g["mean"],
                         marker_color=[WARM_GOLD if r > GLOBAL_RATE else NAVY for r in g["mean"]],
                         text=[f"{r:.1%}" for r in g["mean"]], textposition="outside", customdata=g["size"],
                         hovertemplate="Edad %{x}<br>Tasa de default: %{y:.1%}<br>Clientes: %{customdata:,}<extra></extra>"))
    fig.add_hline(y=GLOBAL_RATE, line_dash="dash", line_color=DEEP_NAVY,
                  annotation_text=f"Global {GLOBAL_RATE:.1%}", annotation_position="top left")
    fig.update_layout(title="Tasa de default por grupo de edad", xaxis_title="Grupo de edad",
                      yaxis_title="Tasa de default", yaxis_tickformat=".0%", showlegend=False)
    fig.update_yaxes(range=[0, g["mean"].max() * 1.2])
    return style_fig(fig, 470, legend_top=False)


def interp_age(view):
    gm = df.groupby("AGE_GRP", observed=True)[MONTH_ORDER].mean()
    gd = df.groupby("AGE_GRP", observed=True)[TARGET].mean()
    gp = df[MONTH_ORDER].ge(1).groupby(df["AGE_GRP"], observed=True).mean()
    rho, p = stats.spearmanr(df["AGE"], df["PAY_0"])
    hi, lo = gd.idxmax(), gd.idxmin()
    if view == "lines":
        basic = ("Todas las edades siguen una forma parecida: el atraso promedio sube hacia los últimos meses "
                 f"(septiembre). El grupo con atraso más alto en el mes más reciente es {gm['PAY_0'].idxmax()} "
                 f"años ({gm['PAY_0'].max():.2f}) y el más bajo es {gm['PAY_0'].idxmin()} "
                 f"({gm['PAY_0'].min():.2f}).")
        tech = (f"Correlación de Spearman AGE–PAY_0: ρ = {rho:+.3f} ({sig(p)}), relación muy débil. "
                "Los promedios de PAY mezclan los códigos −2/−1/0 (sin atraso) con atrasos ≥1, por lo que "
                "se complementan con la vista de % con atraso.")
    elif view == "heat":
        mx = np.unravel_index(np.argmax(gp.values), gp.shape)
        basic = (f"Cada celda indica qué porcentaje de ese grupo de edad llevaba al menos un mes de atraso. "
                 f"El valor más alto aparece en {gp.index[mx[0]]} años, mes de {MONTH_LBL[mx[1]]} "
                 f"({gp.values[mx] * 100:.1f}%). Las diferencias entre edades son pequeñas comparadas con "
                 "las diferencias entre meses.")
        tech = (f"Proporción con PAY ≥ 1 entre {gp.values.min():.1%} y {gp.values.max():.1%}. "
                f"Spearman AGE–PAY_0: ρ = {rho:+.3f} ({sig(p)}). La edad aporta información marginal; el "
                "estado de pago de meses previos es el predictor dominante (ver SHAP en el notebook).")
    else:
        basic = (f"El riesgo es más alto en el grupo de {hi} años ({gd.max():.1%}) y más bajo en el de "
                 f"{lo} ({gd.min():.1%}). La relación con la edad es suave y no tan marcada como la del "
                 "historial de pagos.")
        tech = (f"Tasa de default por grupo entre {gd.min():.1%} y {gd.max():.1%} (global {GLOBAL_RATE:.1%}). "
                "Patrón posiblemente no lineal (en forma de U suave); los grupos extremos de edad tienen "
                "menos observaciones y, por ende, estimaciones más inestables. Conviene considerar AGE "
                "con términos no lineales o categorizada en modelos paramétricos.")
    return basic, tech


# ----- 4.5 Módulo interactivo de cruce de variables ---------------------------
def cross_fig(x, y, c, clip):
    """Cruza 2 (o 3) variables y devuelve (figura, interpretación básica, técnica)."""
    cdisc = c not in (None, "none") and c in DISCRETE
    cnum = c not in (None, "none") and c not in DISCRETE
    xd, yd = x in DISCRETE, y in DISCRETE

    # ------ numérica × numérica: dispersión + recta de tendencia --------------
    if not xd and not yd:
        d = df.sample(min(4000, len(df)), random_state=7).copy()
        if cdisc:
            d["_c"] = pd.Series(as_cat(c), index=df.index).loc[d.index].astype(str)
            fig = px.scatter(d, x=x, y=y, color="_c", opacity=0.55, color_discrete_sequence=PALETTE,
                             category_orders={"_c": cat_order(c)}, labels={"_c": c})
        elif cnum:
            fig = px.scatter(d, x=x, y=y, color=c, opacity=0.6,
                             color_continuous_scale=[[0, NAVY], [1, WARM_GOLD]])
        else:
            fig = px.scatter(d, x=x, y=y, opacity=0.45, color_discrete_sequence=[NAVY])
        if x != y:
            m, b = np.polyfit(df[x], df[y], 1)
            xs = np.array([df[x].min(), df[x].max()])
            fig.add_trace(go.Scatter(x=xs, y=m * xs + b, mode="lines", name="Tendencia lineal",
                                     line=dict(color=WARM_GOLD, width=3, dash="dash")))
        if clip:
            fig.update_xaxes(range=[df[x].min(), df[x].quantile(0.99) * 1.05])
            fig.update_yaxes(range=[df[y].min(), df[y].quantile(0.99) * 1.05])
        fig.update_layout(title=f"{y} vs. {x} (muestra de {len(d):,} clientes)")
        r, pr = stats.pearsonr(df[x], df[y])
        rho, ps = stats.spearmanr(df[x], df[y])
        fuerza = "muy débil" if abs(rho) < 0.2 else "débil" if abs(rho) < 0.4 else "moderada" if abs(rho) < 0.7 else "fuerte"
        sentido = "positiva (suben juntas)" if rho > 0 else "negativa (una sube cuando la otra baja)"
        basic = (f"Entre {x} y {y} hay una relación {fuerza} y {sentido}. "
                 "Cada punto es un cliente; la línea dorada resume la tendencia general.")
        tech = (f"Spearman ρ = {rho:+.3f} ({sig(ps)}); Pearson r = {r:+.3f} ({sig(pr)}); n = {len(df):,}. "
                f"Pendiente OLS = {m:.4g}." if x != y else "x e y son la misma variable.")
        return style_fig(fig, 520), basic, tech

    # ------ discreta × discreta -----------------------------------------------
    if xd and yd:
        if x == y:
            fig = go.Figure()
            fig.update_layout(title="Elige dos variables distintas")
            return style_fig(fig, 420), "Selecciona variables distintas en X e Y.", ""
        if TARGET in (x, y):
            other = y if x == TARGET else x
            d = pd.DataFrame({"_o": as_cat(other), TARGET: df[TARGET]})
            if cdisc and c not in (other, TARGET):
                d["_c"] = as_cat(c)
                g = d.groupby(["_o", "_c"], observed=True)[TARGET].agg(["mean", "size"]).reset_index()
                fig = px.bar(g, x="_o", y="mean", color="_c", barmode="group",
                             color_discrete_sequence=PALETTE, category_orders={"_o": cat_order(other), "_c": cat_order(c)},
                             labels={"_o": other, "mean": "Tasa de default", "_c": c}, custom_data=["size"])
                fig.update_traces(hovertemplate="%{x}<br>Tasa: %{y:.1%}<br>n=%{customdata[0]:,}<extra></extra>")
            else:
                g = d.groupby("_o", observed=True)[TARGET].agg(["mean", "size"]).reset_index()
                fig = go.Figure(go.Bar(
                    x=g["_o"].astype(str), y=g["mean"], customdata=g["size"],
                    marker_color=[WARM_GOLD if r > GLOBAL_RATE else NAVY for r in g["mean"]],
                    text=[f"{r:.1%}" for r in g["mean"]], textposition="outside",
                    hovertemplate="%{x}<br>Tasa: %{y:.1%}<br>n=%{customdata:,}<extra></extra>"))
                fig.update_xaxes(type="category", categoryorder="array", categoryarray=cat_order(other))
            fig.add_hline(y=GLOBAL_RATE, line_dash="dash", line_color=DEEP_NAVY,
                          annotation_text=f"Global {GLOBAL_RATE:.1%}", annotation_position="top left")
            fig.update_layout(title=f"Tasa de default según {other}", xaxis_title=other,
                              yaxis_title="Tasa de default", yaxis_tickformat=".0%")
            tab = d.groupby("_o", observed=True)[TARGET].agg(["mean", "size"])
            tab = tab[tab["size"] >= 30]
            ct = pd.crosstab(df[other], df[TARGET])
            chi, p, dof, _ = stats.chi2_contingency(ct)
            basic = (f"La tasa de default más alta aparece en «{tab['mean'].idxmax()}» "
                     f"({tab['mean'].max():.1%}) y la más baja en «{tab['mean'].idxmin()}» "
                     f"({tab['mean'].min():.1%}), frente a {GLOBAL_RATE:.1%} en promedio.")
            tech = (f"χ²({dof}) = {chi:.1f} ({sig(p)}); V de Cramér = {cramers_v(ct):.3f}. "
                    "Se muestran categorías con n ≥ 30 en el texto; las de muy baja frecuencia "
                    "tienen tasas inestables.")
            if cnum:
                tech += " (La variable de color numérica se ignora en este gráfico.)"
            return style_fig(fig, 500, legend_top=bool(cdisc)), basic, tech
        # discreta × discreta (sin target): heatmap de la tasa de default por celda
        g = df.groupby([y, x])[TARGET].agg(["mean", "size"]).reset_index()
        piv = g.pivot(index=y, columns=x, values="mean")
        cnt = g.pivot(index=y, columns=x, values="size")
        ylab = [CAT_LABELS[y][i] if y in CAT_LABELS else str(int(i)) for i in piv.index]
        xlab = [CAT_LABELS[x][i] if x in CAT_LABELS else str(int(i)) for i in piv.columns]
        fig = go.Figure(go.Heatmap(
            z=piv.values, x=xlab, y=ylab, colorscale=SEQ_GOLD, customdata=cnt.values,
            text=np.where(cnt.values >= 30, np.round(piv.values * 100, 1).astype(str) + "%", ""),
            texttemplate="%{text}", colorbar=dict(title="Tasa default", tickformat=".0%", thickness=14),
            hovertemplate=f"{x}: %{{x}}<br>{y}: %{{y}}<br>Tasa: %{{z:.1%}}<br>n=%{{customdata:,}}<extra></extra>"))
        fig.update_xaxes(type="category")
        fig.update_yaxes(type="category", autorange="reversed")
        fig.update_layout(title=f"Tasa de default por combinación de {x} × {y} (celdas con n ≥ 30 rotuladas)",
                          xaxis_title=x, yaxis_title=y)
        ct = pd.crosstab(df[x], df[y])
        chi, p, dof, _ = stats.chi2_contingency(ct)
        ok = g[g["size"] >= 30]
        top = ok.loc[ok["mean"].idxmax()]
        lab = lambda col, v: CAT_LABELS[col][v] if col in CAT_LABELS else str(int(v))
        basic = (f"La combinación con más incumplimiento (con al menos 30 clientes) es {x} = "
                 f"{lab(x, top[x])} y {y} = {lab(y, top[y])}, con {top['mean']:.1%} de default "
                 f"({int(top['size']):,} clientes).")
        tech = (f"Asociación entre {x} y {y}: χ²({dof}) = {chi:.1f} ({sig(p)}), V de Cramér = "
                f"{cramers_v(ct):.3f}. El color muestra la tasa de default por celda; el módulo ignora "
                "la variable de color en este tipo de cruce.")
        return style_fig(fig, 520, legend_top=False), basic, tech

    # ------ discreta × numérica (cualquier orientación) ------------------------
    catv, numv = (x, y) if xd else (y, x)
    d = pd.DataFrame({"_k": as_cat(catv), numv: df[numv]})
    horizontal = not xd
    kw = dict(category_orders={"_k": cat_order(catv)}, labels={"_k": catv})
    if cdisc and c != catv:
        d["_c"] = as_cat(c)
        kw["category_orders"]["_c"] = cat_order(c)
        kw["labels"]["_c"] = c
        kw["color"] = "_c"
        kw["color_discrete_sequence"] = PALETTE
    else:
        kw["color_discrete_sequence"] = [NAVY]
    if horizontal:
        fig = px.box(d, x=numv, y="_k", orientation="h", points=False, **kw)
    else:
        fig = px.box(d, x="_k", y=numv, points=False, **kw)
    fig.update_traces(boxmean=True)
    lim = [df[numv].min(), df[numv].quantile(0.99) * 1.05]
    if clip:
        (fig.update_xaxes if horizontal else fig.update_yaxes)(range=lim)
    fig.update_layout(title=f"{numv} según {catv}")
    groups = [df.loc[as_cat(catv) == k, numv] for k in cat_order(catv)]
    groups = [g for g in groups if len(g) > 5]
    meds = {k: df.loc[as_cat(catv) == k, numv].median() for k in cat_order(catv)}
    meds_txt = "; ".join(f"{k}: {fmt_val(numv, v)}" for k, v in list(meds.items())[:8])
    hi_k, lo_k = max(meds, key=meds.get), min(meds, key=meds.get)
    if len(groups) >= 2:
        H, p = stats.kruskal(*groups)
        eps = H / (len(df) - 1)
    else:
        H, p, eps = np.nan, np.nan, np.nan
    basic = (f"La mediana de {numv} es mayor en «{hi_k}» ({fmt_val(numv, meds[hi_k])}) y menor en "
             f"«{lo_k}» ({fmt_val(numv, meds[lo_k])}). Las cajas muestran dónde está el 50% central de cada grupo.")
    tech = (f"Kruskal-Wallis H = {H:.1f} ({sig(p)}), ε² = {eps:.4f}. Medianas por grupo → {meds_txt}. "
            "Con muestras grandes el p-value es casi siempre significativo; se debe valorar el tamaño del efecto.")
    return style_fig(fig, 520, legend_top=bool(cdisc and c != catv)), basic, tech


def fig_splom(vars_):
    d = df.sample(min(1500, len(df)), random_state=3)
    fig = go.Figure(go.Splom(
        dimensions=[dict(label=v, values=d[v]) for v in vars_],
        marker=dict(color=d[TARGET], colorscale=[[0, NAVY], [1, WARM_GOLD]], size=4, opacity=0.55,
                    line=dict(width=0)),
        diagonal_visible=True, showupperhalf=False,
        text=np.where(d[TARGET] == 1, "Default", "No default"), hoverinfo="text+x+y"))
    fig.update_layout(title="Matriz de dispersión (azul = no default · dorado = default) · muestra de 1,500 clientes")
    return style_fig(fig, max(480, 170 * len(vars_) + 120), legend_top=False)


def interp_splom(vars_):
    sub = _C[[("default" if v == TARGET else v) for v in vars_]]
    c = sub.corr(method="spearman")
    iu = np.triu_indices(len(vars_), 1)
    pairs = [(c.index[i], c.columns[j], c.values[i, j]) for i, j in zip(*iu)]
    pairs.sort(key=lambda t: -abs(t[2]))
    a, b, r = pairs[0]
    basic = (f"De las variables elegidas, las que más se parecen entre sí son {a} y {b} "
             f"(relación {'directa' if r > 0 else 'inversa'}). Si los puntos dorados (default) se "
             "agrupan en una zona, esa combinación de variables separa a los clientes de riesgo.")
    tech = ("Spearman de los pares más fuertes: " +
            "; ".join(f"{p[0]}–{p[1]} ρ = {p[2]:+.2f}" for p in pairs[:4]) +
            ". Útil para detectar colinealidad entre predictores y regiones del espacio donde se concentra la clase 1.")
    return basic, tech


# ----- 4.6 Hallazgos clave (tarjetas finales) ---------------------------------
def key_findings():
    c = CORR
    bill = c.loc[BILL_COLS, BILL_COLS].values[np.triu_indices(6, 1)]
    t_ser = c["default"].drop("default")
    t_top = t_ser.abs().idxmax()
    t_rho = t_ser[t_top]
    g1 = df.loc[df[TARGET] == 1, "LIMIT_BAL"].median()
    g0 = df.loc[df[TARGET] == 0, "LIMIT_BAL"].median()
    r_pay0 = df.groupby(df["PAY_0"].ge(1))[TARGET].mean()
    te = rate_table("EDUCATION")["mean"]
    return [
        ("El historial de pagos domina",
         f"{t_top} es la variable más asociada al default (ρ de Spearman = {t_rho:+.2f}). Los clientes con "
         f"≥1 mes de atraso en PAY_0 incumplen en {r_pay0[True]:.1%} de los casos, frente a "
         f"{r_pay0[False]:.1%} de quienes están al día."),
        ("Multicolinealidad en la facturación",
         f"Las seis BILL_AMT se correlacionan (Spearman) entre {bill.min():.2f} y {bill.max():.2f}. "
         "Para modelos lineales conviene resumirlas (promedio + tendencia) o usar PCA."),
        ("Límite de crédito más bajo en default",
         f"Mediana de LIMIT_BAL: {nt(g1)} (default) vs. {nt(g0)} (no default). "
         "Un menor cupo se asocia con mayor riesgo."),
        ("El perfil demográfico pesa poco",
         f"Las tasas por educación van de {te.min():.1%} a {te.max():.1%}: diferencias significativas pero "
         "con tamaño de efecto pequeño. La edad tampoco separa por sí sola."),
    ]


# =============================================================================
# 4a. MODELOS (resultados del repositorio Credit_Card_Project, notebooks 04, 05 y 07)
# =============================================================================
# results/model_results.csv resume las 112 combinaciones (7 modelos x 4 técnicas de
# balanceo x 4 métodos de optimización, validación cruzada anidada 3 x 3):
#   - 96 filas locales: results/experiments_posthoc_metrics.csv (F1, precisión, recall,
#     ROC-AUC y PR-AUC; desviación del F1 con ddof=1).
#   - 16 filas de SVM: results/svm_gpu_results_colab.csv (Colab con GPU; sin PR-AUC).
MODEL_RESULTS_PATH = BASE_DIR / "results" / "model_results.csv"
MR = pd.read_csv(MODEL_RESULTS_PATH)

MODEL_INFO = {
    "random_forest": {
        "label": "Random Forest", "family": "Ensamble de árboles (bagging)",
        "desc": "Promedia muchos árboles entrenados sobre muestras distintas de clientes; capta relaciones no "
                "lineales entre el historial de pagos y el riesgo.",
        "note": "Mayor F1 medio de las 112 combinaciones. Encabeza el grupo superior junto a XGBoost y SVM, "
                "sin diferencia significativa entre los tres (Nemenyi, p ≥ 0.88)."},
    "xgboost": {
        "label": "XGBoost", "family": "Ensamble de árboles (boosting)",
        "desc": "Construye árboles en secuencia: cada uno corrige los errores del anterior.",
        "note": "A menos de una milésima del primer lugar: la diferencia es mucho menor que la variación "
                "entre folds, así que en la práctica empata con Random Forest."},
    "svm": {
        "label": "SVM", "family": "Máquina de vectores de soporte (kernel RBF)",
        "desc": "Busca la frontera que separa mejor a quienes pagan de quienes incumplen, con un margen máximo.",
        "note": "Corrida en Colab con GPU (cuML): no es estrictamente comparable con los demás modelos "
                "y no tiene PR-AUC calculado."},
    "knn": {
        "label": "KNN", "family": "Vecinos más cercanos",
        "desc": "Clasifica a cada cliente según lo que hicieron los clientes más parecidos a él.",
        "note": "Con pesos de clase usa un ajuste propio del proyecto (el voto de cada vecino se pondera por la "
                "rareza de su clase), no un mecanismo estándar de scikit-learn."},
    "decision_tree": {
        "label": "Árbol de decisión", "family": "Árbol de clasificación",
        "desc": "Una secuencia de preguntas sí/no sobre las variables; fácil de leer, pero inestable.",
        "note": "Queda por debajo del grupo superior: Random Forest lo supera de forma significativa (p = 0.018)."},
    "logistic_regression": {
        "label": "Regresión logística", "family": "Modelo lineal · línea base",
        "desc": "Modelo de referencia: combina las variables de forma lineal para estimar la probabilidad de default.",
        "note": "Sin balanceo es la combinación con menor F1 (0.378): solo detecta 26 % de quienes incumplen. "
                "Con SMOTE o pesos de clase sube a 0.515, con un ROC-AUC casi igual."},
    "naive_bayes": {
        "label": "Naive Bayes", "family": "Probabilístico (gaussiano)",
        "desc": "Aplica el teorema de Bayes suponiendo que las variables son independientes entre sí.",
        "note": "Ese supuesto no se cumple con el historial de pagos, muy correlacionado mes a mes; "
                "por eso el balanceo casi no lo cambia (F1 entre 0.494 y 0.499)."},
}
TECH_LBL = {"none": "Sin balanceo", "class_weight": "Pesos de clase", "smote": "SMOTE", "adasyn": "ADASYN"}
TECH_ORDER = ["none", "class_weight", "smote", "adasyn"]
METHOD_LBL = {"grid_search": "Grid search", "random_search": "Random search",
              "bayesian_optuna": "Bayesiana (Optuna)", "genetic_deap": "Genética (DEAP)"}

# Mejor combinación de cada modelo (por F1 medio), ordenadas de mejor a peor
BEST_BY_MODEL = (MR.loc[MR.groupby("model")["f1_mean"].idxmax()]
                 .sort_values("f1_mean", ascending=False).reset_index(drop=True))
BEST = BEST_BY_MODEL.iloc[0]
BASELINE = MR[(MR["model"] == "logistic_regression") & (MR["technique"] == "none")]["f1_mean"].max()
# Matriz de confusión out-of-fold de la mejor combinación (05_results_analysis.ipynb)
BEST_CM = {"tn": 19295, "fp": 4040, "fn": 2624, "tp": 4006}
TECH_COLORS = {"none": GREY_BLUE, "class_weight": WARM_GOLD, "smote": DEEP_NAVY, "adasyn": MID_BLUE}


def fig_models_heat():
    """Mejor F1 de cada modelo con cada técnica de balanceo (máximo sobre los 4 métodos)."""
    order = list(BEST_BY_MODEL["model"])
    pv = MR.pivot_table(index="model", columns="technique", values="f1_mean", aggfunc="max").loc[order, TECH_ORDER]
    fig = go.Figure(go.Heatmap(
        z=pv.values, x=[TECH_LBL[t] for t in TECH_ORDER], y=[MODEL_INFO[m]["label"] for m in order],
        colorscale=SEQ_GOLD, texttemplate="%{z:.3f}", textfont=dict(size=13), xgap=3, ygap=3,
        colorbar=dict(title="F1", thickness=12),
        hovertemplate="%{y} · %{x}<br>Mejor F1: %{z:.4f}<extra></extra>"))
    style_fig(fig, 400, legend_top=False)
    fig.update_layout(margin=dict(l=130, r=20, t=24, b=40))
    fig.update_yaxes(autorange="reversed", showgrid=False)
    fig.update_xaxes(side="top", showgrid=False)
    return fig


def fig_models_scatter():
    """Las 112 combinaciones: F1 frente a ROC-AUC, coloreadas por técnica de balanceo."""
    fig = go.Figure()
    for t in TECH_ORDER:
        d = MR[MR["technique"] == t]
        fig.add_trace(go.Scatter(
            x=d["roc_auc_mean"], y=d["f1_mean"], mode="markers", name=TECH_LBL[t],
            marker=dict(size=9, color=TECH_COLORS[t], opacity=.85, line=dict(width=.6, color=WHITE)),
            customdata=np.stack([d["model"].map(lambda m: MODEL_INFO[m]["label"]),
                                 d["method"].map(METHOD_LBL), d["recall_mean"]], axis=-1),
            hovertemplate="<b>%{customdata[0]}</b> · " + TECH_LBL[t] + "<br>%{customdata[1]}"
                          "<br>F1: %{y:.4f}<br>ROC-AUC: %{x:.4f}<br>Recall: %{customdata[2]:.3f}<extra></extra>"))
    fig.add_trace(go.Scatter(
        x=[BEST["roc_auc_mean"]], y=[BEST["f1_mean"]], mode="markers", name="Mejor combinación",
        marker=dict(symbol="star", size=20, color=PALE_GOLD, line=dict(width=1.5, color=GOLD_DARK)),
        hovertemplate=f"<b>Mejor: {MODEL_INFO[BEST['model']]['label']}</b><br>{TECH_LBL[BEST['technique']]} · "
                      f"{METHOD_LBL[BEST['method']]}<br>F1: %{{y:.4f}}<br>ROC-AUC: %{{x:.4f}}<extra></extra>"))
    style_fig(fig, 420)
    fig.update_layout(margin=dict(l=60, r=20, t=50, b=55),
                      xaxis_title="ROC-AUC (capacidad de ordenar clientes)", yaxis_title="F1 de la clase default")
    return fig


def fig_best_cm():
    """Matriz de confusión out-of-fold de la mejor combinación (umbral 0.5)."""
    c = BEST_CM
    z = [[c["tn"], c["fp"]], [c["fn"], c["tp"]]]
    txt = [[f"<b>{c['tn']:,}</b><br>Bien clasificados", f"<b>{c['fp']:,}</b><br>Falsas alarmas"],
           [f"<b>{c['fn']:,}</b><br>No detectados", f"<b>{c['tp']:,}</b><br>Detectados"]]
    fig = go.Figure(go.Heatmap(
        z=z, x=["Predice: paga", "Predice: incumple"], y=["Real: paga", "Real: incumple"],
        text=txt, texttemplate="%{text}", textfont=dict(size=13), showscale=False, xgap=4, ygap=4,
        colorscale=[[0, CREAM], [0.25, PALE_GOLD], [1, NAVY]],
        hovertemplate="%{y} · %{x}<br>Clientes: %{z:,}<extra></extra>"))
    style_fig(fig, 340, legend_top=False)
    fig.update_layout(margin=dict(l=100, r=20, t=24, b=40))
    fig.update_yaxes(autorange="reversed", showgrid=False)
    fig.update_xaxes(side="top", showgrid=False)
    return fig


# =============================================================================
# 4a-bis. PREDECIR: modelo serializado con joblib (modelo/modelo_credito.pkl)
# =============================================================================
# El .pkl lo genera `python -m modelo.entrenar` (ver modelo/entrenar.py). Es un
# Pipeline completo: transforma las 23 variables originales, aplica one-hot y
# predice con un Random Forest con pesos de clase. Aquí solo se CARGA y se usa.
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))   # para que joblib encuentre modelo.features
MODEL_FILE = BASE_DIR / "modelo" / "modelo_credito.pkl"
MODEL_META_FILE = BASE_DIR / "modelo" / "modelo_credito.json"
try:
    import joblib
    from modelo.features import INPUT_COLS
    MODELO = joblib.load(MODEL_FILE)
    MODELO_META = json.loads(MODEL_META_FILE.read_text(encoding="utf-8"))
    MODELO_ERROR = None
except Exception as _e:   # el tablero sigue funcionando aunque falte el modelo
    MODELO, MODELO_META, MODELO_ERROR = None, {}, f"{type(_e).__name__}: {_e}"
    INPUT_COLS = (["LIMIT_BAL", "SEX", "EDUCATION", "MARRIAGE", "AGE"] + PAY_COLS + BILL_COLS + PAYAMT_COLS)
    print(f"[modelo] no se pudo cargar {MODEL_FILE.name}: {MODELO_ERROR}")

# Columnas del formulario en orden cronológico (Abr ... Sep)
PAY_CHRONO = MONTH_ORDER                                         # PAY_6 ... PAY_0
BILL_CHRONO = [f"BILL_AMT{i}" for i in range(6, 0, -1)]          # BILL_AMT6 = abril
PAYAMT_CHRONO = [f"PAY_AMT{i}" for i in range(6, 0, -1)]


def _profile_typical():
    """Cliente «típico»: mediana de las numéricas y moda de las categóricas."""
    out = {c: int(df[c].mode()[0]) for c in CAT_COLS + PAY_COLS}
    out.update({c: int(round(df[c].median(), -2)) for c in BILL_COLS + PAYAMT_COLS})
    out["LIMIT_BAL"] = int(round(df["LIMIT_BAL"].median(), -4))
    out["AGE"] = int(df["AGE"].median())
    return out


PROFILES = {
    "tipico": ("Cliente típico", _profile_typical()),
    "al-dia": ("Al día, cupo alto", {
        "LIMIT_BAL": 360000, "SEX": 2, "EDUCATION": 1, "MARRIAGE": 2, "AGE": 36,
        **{c: -1 for c in PAY_COLS},
        **dict(zip(BILL_COLS, [18500, 21000, 15800, 19200, 12400, 16900])),
        **dict(zip(PAYAMT_COLS, [21000, 15800, 19200, 12400, 16900, 14000]))}),
    "atrasos": ("Atrasos recientes", {
        "LIMIT_BAL": 50000, "SEX": 1, "EDUCATION": 3, "MARRIAGE": 1, "AGE": 47,
        **dict(zip(PAY_COLS, [2, 2, 2, 0, 0, 0])),
        **dict(zip(BILL_COLS, [49200, 48100, 46800, 45100, 44300, 43000])),
        **dict(zip(PAYAMT_COLS, [0, 0, 1500, 1600, 1700, 1800]))}),
}


SEX_OTHER = 3   # «Otro»: el dataset solo registra 1 = hombre y 2 = mujer
# Grupos de variables para «¿Qué empuja su riesgo?»
DRIVER_GROUPS = [("Historial de pagos", PAY_COLS), ("Montos pagados", PAYAMT_COLS), ("Facturación", BILL_COLS),
                 ("Cupo de crédito", ["LIMIT_BAL"]), ("Perfil demográfico", ["AGE", "SEX", "EDUCATION", "MARRIAGE"])]
# Variables del simulador «¿Qué pasaría si…?»: (etiqueta corta, valores, título del eje)
WHATIF = {
    "PAY_0": ("Atraso en septiembre", list(range(-2, 9)), "Estado de pago en septiembre"),
    "LIMIT_BAL": ("Cupo", list(range(10000, 1000001, 30000)), "Cupo de crédito (NT$)"),
    "PAY_AMT1": ("Pago de septiembre", [0] + sorted({int(round(v, -2)) for v in np.geomspace(500, 200000, 22)}),
                 "Monto pagado en septiembre (NT$)"),
    "AGE": ("Edad", list(range(21, 76, 2)), "Edad (años)"),
}
PAY_SHORT = {-2: "Sin uso", -1: "Al día", 0: "Mínimo"}


def _pay_short(v):
    return PAY_SHORT.get(v, f"{v} m atraso")


def predict_scores(rows):
    """Lista de dicts con las 23 variables -> puntajes (0-1) del modelo serializado.

    Para SEX = 3 («Otro») promedia las predicciones como hombre y como mujer, porque el
    modelo solo aprendió esas dos categorías.
    """
    d = pd.DataFrame([[r[c] for c in INPUT_COLS] for r in rows], columns=INPUT_COLS)
    other = (d["SEX"] == SEX_OTHER).to_numpy()
    d.loc[other, "SEX"] = 1
    p = MODELO.predict_proba(d)[:, 1]
    if other.any():
        d2 = d[other].copy()
        d2["SEX"] = 2
        p[other] = (p[other] + MODELO.predict_proba(d2)[:, 1]) / 2
    return p


def predict_risk(values):
    return float(predict_scores([values])[0])


def tree_votes(values):
    """Cuántos árboles del bosque dan probabilidad ≥ 0.5 de incumplir (los «votos»)."""
    rows = [values] if values["SEX"] != SEX_OTHER else [{**values, "SEX": 1}, {**values, "SEX": 2}]
    X = pd.DataFrame([[r[c] for c in INPUT_COLS] for r in rows], columns=INPUT_COLS)
    Xt = MODELO[:-1].transform(X)
    trees = MODELO[-1].estimators_
    yes = np.mean([np.mean(t.predict_proba(Xt)[:, 1] >= 0.5) for t in trees]) * len(trees)
    return int(round(yes)), len(trees)


def fig_risk_gauge(score=None):
    """Indicador del puntaje de riesgo con el umbral de decisión (0.5)."""
    thr = MODELO_META.get("umbral", 0.5) * 100
    val = 0 if score is None else score * 100
    color = WARM_GOLD if val >= thr else NAVY
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=val, number=dict(suffix="%", valueformat=".0f", font=dict(size=46)),
        gauge=dict(
            axis=dict(range=[0, 100], ticksuffix="%", tickwidth=1, tickcolor=GREY_BLUE),
            bar=dict(color=color, thickness=.32), bgcolor="rgba(0,0,0,0)", borderwidth=0,
            steps=[dict(range=[0, thr], color=f"{DEEP_RGBA}0.06)"), dict(range=[thr, 100], color="rgba(184,143,61,0.16)")],
            threshold=dict(line=dict(color=DEEP_NAVY, width=3), thickness=.85, value=thr))))
    fig.update_layout(height=240, margin=dict(l=30, r=30, t=16, b=6), paper_bgcolor=WHITE,
                      font=dict(color=DEEP_NAVY, family="Inter, 'Segoe UI', Roboto, Arial, sans-serif"))
    return fig


def fig_client_history(values):
    """Facturado vs. pagado por mes y estado de pago (eje derecho)."""
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(x=MONTH_LBL, y=[values[c] or 0 for c in BILL_CHRONO], name="Facturado",
                         marker_color=NAVY, hovertemplate="%{x} · facturado: NT$ %{y:,.0f}<extra></extra>"))
    fig.add_trace(go.Bar(x=MONTH_LBL, y=[values[c] or 0 for c in PAYAMT_CHRONO], name="Pagado",
                         marker_color=PALE_GOLD, hovertemplate="%{x} · pagado: NT$ %{y:,.0f}<extra></extra>"))
    st = [values[c] for c in PAY_CHRONO]
    fig.add_trace(go.Scatter(
        x=MONTH_LBL, y=st, name="Estado de pago", mode="lines+markers", customdata=[_pay_short(v) for v in st],
        line=dict(color=WARM_GOLD, width=2.5),
        marker=dict(size=12, color=[WARM_GOLD if v >= 1 else GREY_BLUE for v in st], line=dict(width=1.5, color=WHITE)),
        hovertemplate="%{x} · estado: %{customdata}<extra></extra>"), secondary_y=True)
    style_fig(fig, 340)
    fig.update_layout(barmode="group", bargap=.28, margin=dict(l=60, r=55, t=40, b=36))
    fig.update_yaxes(title_text="NT$", secondary_y=False, tickformat="~s")
    fig.update_yaxes(title_text="Estado de pago", secondary_y=True, range=[-2.8, 9.2], showgrid=False,
                     tickvals=[-2, -1, 0, 2, 4, 6, 8],
                     ticktext=["Sin uso", "Al día", "Mínimo", "2 m", "4 m", "6 m", "8 m"])
    return fig


def fig_drivers(values, score):
    """Cuánto cambia el puntaje si cada grupo de variables fuera el de un cliente típico."""
    typical = PROFILES["tipico"][1]
    rows = [{**values, **{c: typical[c] for c in cols}} for _, cols in DRIVER_GROUPS]
    alt = predict_scores(rows)
    d = pd.DataFrame({"grupo": [g for g, _ in DRIVER_GROUPS], "aporte": (score - alt) * 100})
    d = d.reindex(d["aporte"].abs().sort_values().index)
    fig = go.Figure(go.Bar(
        x=d["aporte"], y=d["grupo"], orientation="h",
        marker_color=[WARM_GOLD if v > 0 else NAVY for v in d["aporte"]],
        text=[f"{v:+.1f} pts" for v in d["aporte"]], textposition="outside", cliponaxis=False,
        hovertemplate="%{y}: %{x:+.1f} puntos frente a un cliente típico<extra></extra>"))
    lim = max(5, d["aporte"].abs().max() * 1.6)
    fig.add_vline(x=0, line_color=GREY_BLUE, line_width=1)
    style_fig(fig, 340, legend_top=False)
    fig.update_layout(margin=dict(l=150, r=30, t=20, b=46), showlegend=False,
                      xaxis_title="Puntos de riesgo que suma (+) o resta (−)")
    fig.update_xaxes(range=[-lim, lim], zeroline=False)
    return fig


def fig_whatif(values, var, score):
    """Puntaje del cliente si solo cambiara una variable."""
    lbl, grid, xtitle = WHATIF[var]
    p = predict_scores([{**values, var: x} for x in grid]) * 100
    thr = MODELO_META.get("umbral", 0.5) * 100
    cur = values[var]
    is_pay = var == "PAY_0"
    xs = [_pay_short(x) if is_pay else x for x in grid]
    fig = go.Figure()
    fig.add_hrect(y0=thr, y1=100, fillcolor="rgba(184,143,61,0.10)", line_width=0)
    fig.add_trace(go.Scatter(x=xs, y=p, mode="lines+markers", line=dict(color=NAVY, width=3, shape="spline" if not is_pay else "linear"),
                             marker=dict(size=7, color=NAVY), name=lbl,
                             hovertemplate=f"{xtitle}: %{{x}}<br>Puntaje: %{{y:.0f}}%<extra></extra>"))
    fig.add_trace(go.Scatter(x=[_pay_short(cur) if is_pay else cur], y=[score * 100], mode="markers+text",
                             marker=dict(symbol="star", size=20, color=PALE_GOLD, line=dict(width=1.5, color=GOLD_DARK)),
                             text=["Este cliente"], textposition="top center", textfont=dict(color=GOLD_DARK),
                             name="Este cliente", hovertemplate="Este cliente: %{y:.0f}%<extra></extra>"))
    fig.add_hline(y=thr, line_dash="dash", line_color=WARM_GOLD, line_width=1.5,
                  annotation_text=f"Umbral {thr:.0f}%: por encima, «riesgo alto»", annotation_position="top left",
                  annotation_font_color=GOLD_MID)
    style_fig(fig, 360, legend_top=False)
    fig.update_layout(margin=dict(l=60, r=24, t=24, b=50), showlegend=False,
                      xaxis_title=xtitle, yaxis_title="Puntaje de riesgo (%)")
    fig.update_yaxes(range=[0, 100], ticksuffix="%")
    if is_pay:
        fig.update_xaxes(type="category")
    elif var != "AGE":
        fig.update_xaxes(tickformat="~s")
    return fig


# =============================================================================
# 4b. ICONOS (SVG propios, sin dependencias ni emojis; toman el color del texto)
# =============================================================================
ICONS = {
    "panel": '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M9 4v16"/>',
    "sun": '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M6.3 17.7l-1.4 1.4M19.1 4.9l-1.4 1.4"/>',
    "moon": '<path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9z"/>',
    "home": '<path d="M3 10.5 12 3l9 7.5"/><path d="M5 9.5V21h14V9.5"/><path d="M10 21v-6h4v6"/>',
    "info": '<circle cx="12" cy="12" r="9"/><path d="M12 11v5M12 8h.01"/>',
    "target": '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1"/>',
    "book": '<path d="M2 4h6a4 4 0 0 1 4 4v13a3 3 0 0 0-3-3H2z"/><path d="M22 4h-6a4 4 0 0 0-4 4v13a3 3 0 0 1 3-3h7z"/>',
    "bars": '<path d="M3 3v18h18"/><path d="M8 17v-5M13 17V8M18 17v-9"/>',
    "scatter": '<circle cx="7" cy="16" r="2"/><circle cx="12" cy="8" r="2"/><circle cx="18" cy="14" r="2"/><path d="M8.4 14.3l2.3-4.5M13.5 9.4l3.3 3.2"/>',
    "link": '<path d="M10 13a5 5 0 0 0 7.07 0l3-3a5 5 0 0 0-7.07-7.07l-1.5 1.5"/><path d="M14 11a5 5 0 0 0-7.07 0l-3 3a5 5 0 0 0 7.07 7.07l1.5-1.5"/>',
    "github": '<path d="M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.4 5.4 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4"/><path d="M9 18c-4.51 2-5-2-7-2"/>',
    "notebook": '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6M8 13h8M8 17h8M8 9h2"/>',
    "external": '<path d="M15 3h6v6M10 14 21 3M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>',
    "database": '<ellipse cx="12" cy="5" rx="8" ry="3"/><path d="M4 5v14c0 1.7 3.6 3 8 3s8-1.3 8-3V5"/><path d="M4 12c0 1.7 3.6 3 8 3s8-1.3 8-3"/>',
    "users": '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/>',
    "arrow": '<path d="M5 12h14M13 6l6 6-6 6"/>',
    "alert": '<path d="M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z"/><path d="M12 9v4M12 17h.01"/>',
    "calendar": '<rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/>',
    "columns": '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M9 4v16M15 4v16"/>',
    "coin": '<circle cx="12" cy="12" r="9"/><path d="M14.5 9a2.5 2.5 0 0 0-2.5-1.5c-1.4 0-2.5.9-2.5 2s1.1 1.7 2.5 2 2.5.9 2.5 2-1.1 2-2.5 2a2.5 2.5 0 0 1-2.5-1.5M12 6v1.5M12 16.5V18"/>',
    "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    "mail": '<rect x="2" y="4" width="20" height="16" rx="2"/><path d="m22 7-10 5L2 7"/>',
    "linkedin": '<path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-4 0v7h-4v-7a6 6 0 0 1 6-6z"/><rect x="2" y="9" width="4" height="12"/><circle cx="4" cy="4" r="2"/>',
    "flip": '<path d="M3 12a9 9 0 0 1 15.5-6.2L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-15.5 6.2L3 16"/><path d="M3 21v-5h5"/>',
    # --- nuevos: detalles de tarjeta de crédito ---
    "card": '<rect x="2" y="5" width="20" height="14" rx="2.5"/><path d="M2 10h20M6 15h4"/>',
    "chip": '<rect x="4" y="5" width="16" height="14" rx="3"/><path d="M4 10h16M4 14h16M10 5v14M14 5v14"/>',
    "contactless": '<path d="M8.5 8.5a5 5 0 0 1 0 7M12 6a9 9 0 0 1 0 12M15.5 3.5a13 13 0 0 1 0 17"/>',
    # --- página Modelos ---
    "layers": '<path d="m12 2 10 5-10 5L2 7z"/><path d="m2 17 10 5 10-5"/><path d="m2 12 10 5 10-5"/>',
    "trophy": '<path d="M8 21h8M12 17v4M7 4h10v5a5 5 0 0 1-10 0z"/><path d="M17 5h3v2a3 3 0 0 1-3 3M7 5H4v2a3 3 0 0 0 3 3"/>',
    "chevron": '<path d="m9 6 6 6-6 6"/>',
    "gauge": '<path d="M3.5 18a9.5 9.5 0 1 1 17 0"/><path d="m12 13 4.5-4.5"/><circle cx="12" cy="13" r="1.4"/>',
    "male": '<circle cx="10" cy="14" r="6"/><path d="M14.5 9.5 20 4M15 4h5v5"/>',
    "female": '<circle cx="12" cy="9" r="6"/><path d="M12 15v7M9 19h6"/>',
    "gender": '<circle cx="11" cy="12" r="5"/><path d="M14.5 8.5 19 4M15 4h4v4M11 17v5M8.5 19.5h5"/>',
    "cap": '<path d="m2 9 10-5 10 5-10 5z"/><path d="M6 11v5c3 2 9 2 12 0v-5M22 9v6"/>',
    "pencil": '<path d="M17 3l4 4L8 20H4v-4z"/><path d="m14 6 4 4"/>',
    "dots": '<circle cx="5" cy="12" r="1.6"/><circle cx="12" cy="12" r="1.6"/><circle cx="19" cy="12" r="1.6"/>',
    "rings": '<circle cx="9" cy="14" r="5.5"/><circle cx="15" cy="14" r="5.5"/><path d="m10 5 2-2 2 2-2 2z"/>',
    "person": '<circle cx="12" cy="7" r="4"/><path d="M5 21a7 7 0 0 1 14 0"/>',
    "tree": '<path d="M12 22v-5"/><path d="M12 17H6l3-4H7l3-4H8.5L12 3l3.5 6H14l3 4h-2l3 4z"/>',
    "save": '<path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><path d="M17 21v-8H7v8M7 3v5h8"/>',
    # --- asistente Kyo ---
    "close": '<path d="M6 6l12 12M18 6 6 18"/>',
    "send": '<path d="M22 2 11 13"/><path d="M22 2 15 22l-4-9-9-4z"/>',
    "reset": '<path d="M3 12a9 9 0 1 0 3-6.7L3 8"/><path d="M3 3v5h5"/>',
}


def _icon_css():
    out = []
    for name, body in ICONS.items():
        svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="black" '
               'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">' + body + '</svg>')
        out.append(f'.ico-{name}{{--ico:url("data:image/svg+xml,{quote(svg)}");}}')
    return "\n".join(out)


def icon(name, cls=""):
    """Ícono decorativo: <span class="ico ico-nombre">, coloreado con el color del texto."""
    return html.Span(className=f"ico ico-{name} {cls}".strip(), **{"aria-hidden": "true"})


PAGE_ICONS = {"Introducción": "info", "Problema y Objetivos": "target", "Marco Teórico": "book",
              "EDA Univariado": "bars", "EDA Multivariado": "scatter", "Modelos": "layers", "Predecir": "gauge", "Enlaces": "link", "Equipo": "users"}


# =============================================================================
# 5. COMPONENTES DE INTERFAZ
# =============================================================================
def card(title, children, subtitle=None, cls=""):
    head = [html.H3(title, className="card-title")]   # solo el título (subtitle se ignora a propósito)
    return html.Div(head + (children if isinstance(children, list) else [children]),
                    className=f"card {cls}".strip())


def kpi(label, value, note="", ico=None):
    return html.Div([html.Div([icon(ico) if ico else None, html.Div(label, className="kpi-label")],
                              className="kpi-head"),
                     html.Div(value, className="kpi-value"),
                     html.Div(note, className="kpi-note")], className="kpi")


def interp_block(basic, tech):
    """Un solo botón desplegable (cerrado) con la interpretación básica y la técnica."""
    return html.Details([
        html.Summary([icon("info"), "Ver interpretación", icon("chevron", "interp-chev")], className="interp-btn"),
        html.Div([html.Div([html.B("Básica"), html.P(basic)], className="interp basic"),
                  html.Div([html.B("Técnica"), html.P(tech)], className="interp tech")], className="interp-body"),
    ], className="interp-wrap")


def control(label, comp):
    return html.Div([html.Label(label, className="ctl-label"), comp], className="control")


def page_title(title, sub):
    ic = PAGE_ICONS.get(title)
    return html.Div(html.H2([icon(ic, "pt-ico"), title] if ic else title), className="page-title")


def var_options(cols):
    return [{"label": pretty(c), "value": c} for c in cols]


ALL_VARS = ["LIMIT_BAL", "SEX", "EDUCATION", "MARRIAGE", "AGE"] + PAY_COLS + BILL_COLS + PAYAMT_COLS + [TARGET]


# =============================================================================
# 6. PÁGINAS
# =============================================================================
def page_uni():
    b_t, t_t = interp_target()
    return html.Div([
        page_title("EDA Univariado", "Distribución y calidad de cada variable por separado"),
        html.Div([
            kpi("Total de registros", f"{len(df):,}", "tras eliminar duplicados", ico="users"),
            kpi("Tasa global de default", f"{GLOBAL_RATE:.1%}", f"{int(df[TARGET].sum()):,} clientes", ico="alert"),
            kpi("Límite de crédito promedio", nt(df["LIMIT_BAL"].mean()), f"mediana {nt(df['LIMIT_BAL'].median())}", ico="coin"),
            kpi("Edad promedio", f"{df['AGE'].mean():.1f} años", f"mediana {df['AGE'].median():.0f}", ico="clock"),
        ], className="kpi-row k4"),
        html.Div([
            card("Variable objetivo: Default vs. No Default",
                 [dcc.Graph(id="target-graph", figure=fig_target(), config={"displaylogo": False}), interp_block(b_t, t_t)],
                 subtitle="Conteo y porcentaje de clientes por clase"),
            card("Explorador univariado",
                 [html.Div([
                     control("Variable", dcc.Dropdown(id="uni-var", options=var_options(ALL_VARS),
                                                      value="LIMIT_BAL", clearable=False)),
                     control("Opciones", dcc.Checklist(
                         id="uni-clip", options=[{"label": " Recortar cola superior (P99) en la vista", "value": "clip"}],
                         value=["clip"], className="check")),
                 ], className="controls"),
                  dcc.Loading(dcc.Graph(id="uni-graph", config={"displaylogo": False}), type="dot", color=WARM_GOLD),
                  html.Div(id="uni-interp")],
                 subtitle="Elige cualquier variable: numéricas (histograma + boxplot) o categóricas (barras)"),
        ], className="grid g2"),
        card("Distribuciones de variables cuantitativas",
             [html.Div([
                 control("Variable / familia", dcc.RadioItems(
                     id="q-family", value="LIMIT_BAL", className="radio",
                     options=[{"label": "LIMIT_BAL", "value": "LIMIT_BAL"}, {"label": "AGE", "value": "AGE"},
                              {"label": "BILL_AMT (1–6)", "value": "BILL_AMT"}, {"label": "PAY_AMT (1–6)", "value": "PAY_AMT"}])),
                 control("Tipo de gráfico", dcc.RadioItems(
                     id="q-kind", value="hist", className="radio",
                     options=[{"label": "Histograma", "value": "hist"}, {"label": "Boxplot", "value": "box"},
                              {"label": "Densidad", "value": "dens"}])),
             ], className="controls"),
              dcc.Loading(dcc.Graph(id="q-graph", config={"displaylogo": False}), type="dot", color=WARM_GOLD),
              html.Div(id="q-interp")],
             subtitle="Comparación de LIMIT_BAL, AGE y los seis meses de BILL_AMT y PAY_AMT"),
    ])


def page_multi():
    findings = [html.Div([html.Div(t, className="find-title"), html.P(x)], className="finding")
                for t, x in key_findings()]
    num_opts = var_options(NUM_COLS)
    return html.Div([
        page_title("EDA Multivariado", "Relaciones entre variables y su asociación con el incumplimiento"),
        card("Matriz de correlación de Spearman",
             [dcc.Graph(id="corr-graph", figure=fig_corr(), config={"displaylogo": False}),
              interp_block(*interp_corr())],
             subtitle="Correlación de Spearman (basada en rangos, robusta a valores extremos) sobre las variables "
                      "numéricas y la variable objetivo (escala de azul a dorado)"),
        html.Div([
            card("Incumplimiento por educación, estado civil y sexo",
                 [dcc.Graph(id="rates-graph", figure=fig_rates(), config={"displaylogo": False}),
                  interp_block(*interp_rates())],
                 subtitle="Tasa de default por categoría vs. tasa global"),
            card("Límite de crédito según estado de default",
                 [html.Div([control("Escala del eje Y", dcc.RadioItems(
                     id="lim-scale", value="linear", className="radio",
                     options=[{"label": "Lineal", "value": "linear"}, {"label": "Logarítmica", "value": "log"}]))],
                     className="controls"),
                  dcc.Graph(id="lim-graph", config={"displaylogo": False}),
                  interp_block(*interp_limit())],
                 subtitle="Boxplots comparativos de LIMIT_BAL por default"),
        ], className="grid g2"),
        card("Edad y patrones de atraso en pagos (PAY_0 a PAY_6)",
             [html.Div([control("Vista", dcc.RadioItems(
                 id="age-view", value="lines", className="radio",
                 options=[{"label": "Atraso promedio por mes", "value": "lines"},
                          {"label": "% con atraso ≥ 1 mes", "value": "heat"},
                          {"label": "Tasa de default por edad", "value": "rate"}]))],
                 className="controls"),
              dcc.Graph(id="age-graph", config={"displaylogo": False}),
              html.Div(id="age-interp")],
             subtitle="Grupos de edad vs. estado de pago de abril (PAY_6) a septiembre (PAY_0)"),
        card("Módulo interactivo: cruce de variables",
             [html.Div([
                 control("Variable X", dcc.Dropdown(id="x-var", options=var_options(ALL_VARS), value="EDUCATION", clearable=False)),
                 control("Variable Y", dcc.Dropdown(id="y-var", options=var_options(ALL_VARS), value="LIMIT_BAL", clearable=False)),
                 control("Color / grupo (opcional)", dcc.Dropdown(
                     id="c-var", options=[{"label": "(ninguna)", "value": "none"}] + var_options(ALL_VARS),
                     value=TARGET, clearable=False)),
                 control("Opciones", dcc.Checklist(
                     id="x-clip",
                     options=[{"label": " Ejes ajustados al percentil 99 para facilitar la lectura", "value": "clip"}],
                     value=["clip"], className="check")),
             ], className="controls"),
              dcc.Loading(dcc.Graph(id="x-graph", config={"displaylogo": False}), type="dot", color=WARM_GOLD),
              html.Div(id="x-interp")],
             subtitle="Cruza 2 variables y agrega una tercera como color. El tipo de gráfico se ajusta solo "
                      "(dispersión · boxplot · barras de tasa · mapa de calor). La opción «ejes ajustados al "
                      "percentil 99 para facilitar la lectura» corta la vista en el valor por debajo del cual "
                      "está el 99% de los clientes, para que unos pocos montos extremos no aplasten el gráfico."),
        card("Matriz de dispersión: 2 o más variables numéricas",
             [html.Div([control("Variables (elige entre 2 y 6)", dcc.Dropdown(
                 id="s-vars", options=num_opts, multi=True,
                 value=["LIMIT_BAL", "AGE", "PAY_0", "BILL_AMT1", "PAY_AMT1"]))], className="controls"),
              dcc.Loading(dcc.Graph(id="s-graph", config={"displaylogo": False}), type="dot", color=WARM_GOLD),
              html.Div(id="s-interp")],
             subtitle="Cruza varias variables a la vez, coloreadas por estado de default"),
        html.Div([html.H3("Hallazgos multivariados clave", className="section-h"),
                  html.Div(findings, className="grid g4")], className="findings"),
    ])


def _ul(items, ordered=False):
    return (html.Ol if ordered else html.Ul)([html.Li(i) for i in items])


def _tbl(header, rows):
    head = html.Tr([html.Th(h) for h in header])
    body = [html.Tr([html.Td(c) for c in r]) for r in rows]
    return html.Div(html.Table([head] + body, className="vtable"), className="table-wrap")


def page_intro():
    n_def = int(df[TARGET].sum())
    I = DATA_INFO
    return html.Div([
        page_title("Introducción", "Contexto general del proyecto y del conjunto de datos"),
        quick_look(),
        html.Div([
            kpi("Clientes analizados", f"{len(df):,}", "tras la limpieza", ico="users"),
            kpi("Variables", "24", "23 predictoras + 1 objetivo", ico="columns"),
            kpi("Tasa de default", f"{GLOBAL_RATE:.1%}", f"{n_def:,} clientes", ico="alert"),
            kpi("Periodo", "Abr–Sep 2005", "banco de Taiwán", ico="calendar"),
        ], className="kpi-row k4"),
        html.Div([
            card("Introducción", [
                html.P("Las tarjetas de crédito son una de las líneas de la banca minorista con mayor exposición "
                       "al riesgo: cada cliente recibe un cupo (límite de crédito) y se espera que lo pague en las "
                       "fechas pactadas. Cuando no lo hace, la entidad enfrenta pérdidas, mayores costos de cobranza "
                       "y la necesidad de provisionar capital."),
                html.P(f"Este tablero presenta un análisis exploratorio de datos (EDA) del conjunto Default of Credit "
                       f"Card Clients (UCI), con {I['filas_originales']:,} clientes observados entre abril y septiembre "
                       "de 2005. Para cada cliente se conoce su límite de crédito, sus características demográficas, "
                       "su historial de pagos de seis meses, los montos facturados, los montos pagados y si incumplió "
                       "el pago del mes siguiente (variable objetivo)."),
                html.P("El análisis se organiza en cuatro capas: fundamentos (problema, objetivos y marco teórico), "
                       "exploración univariada, exploración multivariada y los resultados de los modelos "
                       "predictivos del proyecto. Cada gráfico trae una interpretación "
                       "básica (lenguaje cotidiano) y una técnica (estadísticos y recomendaciones de modelado)."),
            ], cls="span-2"),
            card("Fuente y alcance", [
                html.P("Yeh, I-C. & Lien, C. (2009). The comparisons of data mining techniques for the predictive "
                       "accuracy of probability of default of credit card clients. Expert Systems with Applications, "
                       "36(2), 2473–2480. Datos: UCI Machine Learning Repository."),
                html.P("Cifras monetarias en dólares taiwaneses (NT$)."),
                html.P("Alcance: el EDA es descriptivo y no estima causalidad. La sección Modelos resume los "
                       "clasificadores entrenados en el repositorio del proyecto.", className="muted"),
            ]),
        ], className="grid g3"),
        html.Div([
            card("Preparación de los datos", _ul([
                f"Se eliminaron {I['duplicados']} filas duplicadas exactas.",
                f"{I['edu_reagrupadas']} registros con EDUCATION = 0, 5 o 6 (códigos no documentados) pasaron a «Otros».",
                f"{I['mar_reagrupadas']} registros con MARRIAGE = 0 (no documentado) pasaron a «Otros».",
                f"Se conservaron {I['bill_neg_clientes']:,} clientes con saldo facturado negativo (saldo a favor, económicamente válido).",
                "El estado de pago de septiembre se llama PAY_0 (el dataset no incluye PAY_1).",
                "La matriz de correlación usa Spearman sobre los datos originales: al basarse en rangos, es robusta a valores extremos y no requiere recortarlos.",
            ])),
            card("Cómo recorrer este tablero", _ul([
                "Problema y Objetivos: qué se quiere responder, hipótesis y metas del análisis.",
                "Marco Teórico: conceptos y pruebas estadísticas usadas, más el diccionario de variables.",
                "EDA Univariado: calidad y distribución de cada variable, y desbalance de la variable objetivo.",
                "EDA Multivariado: correlaciones, perfiles de riesgo, cruces interactivos y hallazgos clave.",
                "Enlaces: libro del proyecto, notebooks y repositorios.",
                "Con el botón de panel de la barra superior ocultas el menú lateral; el interruptor de sol y luna cambia entre modo claro y oscuro.",
                "Al final de cada página, los botones Anterior y Siguiente te llevan por el tablero en orden.",
            ])),
        ], className="grid g2"),
    ])


def page_problem():
    n_def = int(df[TARGET].sum())
    exposure = df.loc[df[TARGET] == 1, "LIMIT_BAL"].sum()
    bill_def = df.loc[df[TARGET] == 1, "BILL_AMT1"].clip(lower=0).sum()
    hip = [
        ("H1", "El historial reciente de pagos (PAY_0 … PAY_6) es el factor más fuertemente asociado al incumplimiento.",
         "Multivariado · Matriz de correlación"),
        ("H2", "Los clientes con menor límite de crédito (LIMIT_BAL) presentan una mayor tasa de default.",
         "Multivariado · Límite según default"),
        ("H3", "Las variables demográficas (sexo, educación, estado civil, edad) se asocian con el default, pero con un tamaño de efecto pequeño.",
         "Multivariado · Tasas por perfil y edad"),
        ("H4", "Los montos facturados mensuales (BILL_AMT1–6) están fuertemente correlacionados entre sí (multicolinealidad).",
         "Univariado y Multivariado"),
        ("H5", "La clase «default» es minoritaria, por lo que el problema presenta desbalance de clases.",
         "Univariado · Variable objetivo"),
    ]
    objs = [
        ("Describir la calidad de los datos y documentar la limpieza aplicada (duplicados, categorías no documentadas, saldos negativos).", "Introducción"),
        ("Caracterizar la distribución de cada variable, su asimetría y la presencia de valores atípicos.", "EDA Univariado"),
        ("Cuantificar el desbalance de clases de la variable objetivo.", "EDA Univariado"),
        ("Comparar a los clientes con y sin default según variables demográficas, de crédito y de pagos.", "EDA Multivariado"),
        ("Identificar relaciones entre variables y detectar multicolinealidad (correlaciones, VIF).", "EDA Multivariado"),
        ("Definir lineamientos de preprocesamiento para una futura etapa de modelado predictivo.", "Hallazgos clave"),
    ]
    return html.Div([
        page_title("Problema y Objetivos", "Planteamiento, pregunta de investigación, hipótesis y metas del análisis"),
        html.Div([
            card("Planteamiento del problema", [
                html.P("Una entidad financiera otorga crédito sin saber con certeza quién pagará. Si concede cupos "
                       "demasiado altos a clientes que luego incumplen, la cartera se deteriora: se pierde el capital "
                       "no recuperado, aumentan los costos de cobranza y se deben constituir mayores provisiones. Si, "
                       "por el contrario, restringe el crédito en exceso, pierde ingresos por intereses y comisiones."),
                html.P(f"En esta muestra, {GLOBAL_RATE:.1%} de los clientes ({n_def:,}) no pagó su tarjeta el mes "
                       "siguiente. Identificar tempranamente qué perfiles y comportamientos anticipan ese "
                       "incumplimiento es la base para fijar límites, priorizar la cobranza preventiva y alimentar "
                       "un modelo de scoring."),
                html.Div([
                    kpi("Clientes en default", f"{n_def:,}", f"{GLOBAL_RATE:.1%} de la muestra"),
                    kpi("Límite expuesto", f"NT${exposure / 1e6:,.0f} M", "suma de LIMIT_BAL de quienes incumplen"),
                    kpi("Saldo facturado (Sep)", f"NT${bill_def / 1e6:,.0f} M", "BILL_AMT1 positivo de quienes incumplen"),
                ], className="kpi-row k3"),
                html.P("Los errores no son simétricos: no detectar a quien incumplirá (falso negativo) suele costar "
                       "más que revisar de más a quien sí pagaría (falso positivo).", className="muted"),
            ], cls="span-2"),
            card("Pregunta de investigación", [
                html.Div("¿Qué características del cliente, de su línea de crédito y de su historial reciente de pagos "
                         "se asocian con el incumplimiento del mes siguiente, y con qué intensidad?", className="callout"),
                html.P(html.B("Preguntas específicas")),
                _ul(["¿Cómo se distribuyen las variables y qué problemas de calidad presentan?",
                     "¿Qué tan desbalanceada está la variable objetivo?",
                     "¿Qué variables separan mejor a los clientes que incumplen?",
                     "¿Existe redundancia entre las variables predictoras?"]),
            ]),
        ], className="grid g3"),
        html.Div([
            card("Justificación", [
                html.P("Un EDA riguroso evita errores costosos en el modelado: revela datos mal codificados, "
                       "variables redundantes, sesgos de muestreo y desbalance antes de que afecten al modelo."),
                html.P("Además permite explicar a perfiles no técnicos (riesgos, cobranza, gerencia) qué señales "
                       "preceden al incumplimiento, con evidencia visual y estadística."),
            ]),
            card("Alcance y limitaciones", _ul([
                "Datos de un solo banco de Taiwán y de un periodo corto (abril–septiembre de 2005): no se generalizan sin cautela a otros mercados o épocas.",
                "El análisis es asociativo; una correlación no implica causalidad.",
                "El EDA no construye modelos: deriva lineamientos para hacerlo. Los modelos se entrenan en el "
                "repositorio del proyecto y sus resultados se resumen en la sección Modelos.",
                "Los códigos −2 y 0 de PAY_x no están documentados con precisión en la fuente; se conservan sin recodificar.",
            ])),
        ], className="grid g2"),
        card("Hipótesis exploratorias",
             _tbl(["#", "Hipótesis", "Dónde se evalúa"], [(html.B(a), b, c) for a, b, c in hip]),
             subtitle="Se contrastan de forma descriptiva y visual a lo largo del tablero"),
        html.Div([
            card("Objetivo general", [
                html.Div("Analizar los factores que se asocian con el incumplimiento de pago (default) de los clientes "
                         "de tarjetas de crédito mediante un análisis exploratorio de datos univariado y multivariado.",
                         className="callout"),
            ]),
            card("Objetivos específicos", html.Ol(
                [html.Li([t, html.Span(s, className="tag")]) for t, s in objs])),
        ], className="grid g2"),
    ])


def page_marco():
    refs = [
        "Basel Committee on Banking Supervision (2006). International Convergence of Capital Measurement and Capital Standards (Basilea II).",
        "Chawla, N. V., Bowyer, K. W., Hall, L. O. & Kegelmeyer, W. P. (2002). SMOTE: Synthetic Minority Over-sampling Technique. Journal of Artificial Intelligence Research, 16, 321–357.",
        "Cramér, H. (1946). Mathematical Methods of Statistics. Princeton University Press.",
        "Kruskal, W. H. & Wallis, W. A. (1952). Use of ranks in one-criterion variance analysis. Journal of the American Statistical Association, 47(260), 583–621.",
        "Mann, H. B. & Whitney, D. R. (1947). On a test of whether one of two random variables is stochastically larger than the other. Annals of Mathematical Statistics, 18(1), 50–60.",
        "Spearman, C. (1904). The proof and measurement of association between two things. The American Journal of Psychology, 15(1), 72–101.",
        "Tukey, J. W. (1977). Exploratory Data Analysis. Addison-Wesley.",
        "Yeh, I-C. & Lien, C. (2009). The comparisons of data mining techniques for the predictive accuracy of probability of default of credit card clients. Expert Systems with Applications, 36(2), 2473–2480.",
    ]
    var_table = [
        ("LIMIT_BAL", "Numérica continua", "Monto del crédito otorgado (individual + familiar/suplementario) en dólares taiwaneses (NT$)."),
        ("SEX", "Categórica", "Género: 1 = hombre, 2 = mujer."),
        ("EDUCATION", "Categórica ordinal", "1 = posgrado, 2 = universidad, 3 = secundaria, 4 = otros (los códigos 0, 5 y 6 no documentados se reagrupan en «Otros»)."),
        ("MARRIAGE", "Categórica", "Estado civil: 1 = casado, 2 = soltero, 3 = otros (el código 0 se reagrupa en «Otros»)."),
        ("AGE", "Numérica discreta", "Edad en años."),
        ("PAY_0, PAY_2–PAY_6", "Ordinal", "Estado de pago mensual de septiembre (PAY_0) hacia abril (PAY_6). −2/−1/0 = sin atraso; 1 = un mes de atraso; …; 8–9 = ≥8–9 meses."),
        ("BILL_AMT1–6", "Numérica continua", "Monto facturado en el estado de cuenta de septiembre (1) a abril (6), en NT$. Puede ser negativo (saldo a favor)."),
        ("PAY_AMT1–6", "Numérica continua", "Monto efectivamente pagado de septiembre (1) a abril (6), en NT$."),
        ("default_payment_next_month", "Binaria (objetivo)", "1 = el cliente incumple el pago el mes siguiente (octubre 2005); 0 = no incumple."),
    ]
    # Fórmulas en LaTeX (MathJax incluido en Dash); r"..." evita escapar las barras
    F = lambda tex: dcc.Markdown(f"$$\\displaystyle {tex}$$", mathjax=True, className="formula")
    return html.Div([
        page_title("Marco Teórico", "Conceptos, métodos estadísticos y variables que sustentan el análisis"),
        html.Div([
            card("1. Riesgo de crédito y default", [
                html.P("El riesgo de crédito es la posibilidad de que una entidad sufra pérdidas porque un deudor "
                       "no cumple, total o parcialmente, sus obligaciones. En la regulación bancaria (Basilea II) la "
                       "pérdida esperada se descompone así:"),
                F(r"\mathrm{EL} = \mathrm{PD} \times \mathrm{LGD} \times \mathrm{EAD}"),
                _ul(["PD: probabilidad de incumplimiento en un horizonte dado (lo que estudian estos datos).",
                     "LGD: porcentaje de la exposición que se pierde si hay incumplimiento.",
                     "EAD: monto expuesto en el momento del incumplimiento."]),
                html.P("En este proyecto, default es la variable binaria que indica si el cliente no pagó en el mes siguiente."),
            ]),
            card("2. Scoring crediticio", [
                html.P("Los modelos de scoring estiman la PD a partir de variables del cliente: comportamiento de pago, "
                       "límite, deuda y perfil demográfico. Sirven para aprobar o rechazar solicitudes, fijar cupos y "
                       "priorizar la cobranza."),
                html.P("Antes de modelar, el EDA revela la calidad de los datos, las variables más informativas y los "
                       "problemas (colinealidad, desbalance, atípicos) que condicionarán al modelo."),
            ]),
            card("3. Análisis exploratorio de datos (EDA)", [
                html.P("Propuesto por John W. Tukey (1977): explorar los datos con resúmenes numéricos y gráficos, "
                       "antes de ajustar modelos, para descubrir patrones, anomalías y supuestos."),
                _ul(["Univariado: una variable a la vez (frecuencias, histograma, boxplot).",
                     "Bivariado y multivariado: relaciones entre dos o más variables (correlaciones, tablas cruzadas, dispersión, comparación por grupos)."]),
            ]),
            card("4. Estadística descriptiva y valores atípicos", [
                html.P("La asimetría (skewness) indica hacia dónde se alarga la cola de una distribución; la curtosis, "
                       "qué tan pesadas son sus colas. Los montos de dinero suelen ser muy asimétricos."),
                F(r"x < Q_1 - 1.5\,\mathrm{IQR} \quad \text{ó} \quad x > Q_3 + 1.5\,\mathrm{IQR}, \qquad \mathrm{IQR} = Q_3 - Q_1"),
                html.P("La winsorización recorta los extremos a percentiles (por ejemplo P1–P99) sin eliminar clientes. "
                       "La transformación logarítmica con signo suaviza colas largas cuando hay ceros o negativos."),
            ]),
            card("5. Desbalance de clases", [
                html.P("Cuando una clase es mucho menos frecuente, un clasificador puede lograr alta exactitud "
                       "ignorándola. Por eso se recomienda:"),
                _ul(["Ponderar las clases (class_weight) o sobremuestrear la minoritaria (SMOTE, Chawla et al., 2002).",
                     "Ajustar el umbral de decisión.",
                     "Evaluar con AUC-ROC, F1 y recall de la clase minoritaria en lugar de accuracy."]),
            ]),
            card("6. Correlación de Spearman y multicolinealidad", [
                F(r"\rho_s = r\big(\mathrm{rango}(X),\, \mathrm{rango}(Y)\big) = 1 - \frac{6 \sum d_i^2}{n\,(n^2 - 1)}"),
                html.P("La segunda forma vale cuando no hay empates (dᵢ es la diferencia de rangos de cada cliente)."),
                html.P("Spearman (1904) mide asociación monótona usando los rangos de los datos. No exige linealidad "
                       "ni normalidad y resiste los valores extremos. Se eligió sobre Pearson porque los montos "
                       "(BILL_AMT, PAY_AMT) son muy asimétricos y con colas largas, las variables PAY_x son ordinales "
                       "y la variable objetivo es binaria."),
                F(r"\mathrm{VIF}_j = \frac{1}{1 - R_j^2}"),
                html.P("Hay multicolinealidad cuando las predictoras son casi redundantes: se inflan las varianzas de "
                       "los coeficientes. Un VIF > 10 (algunos autores usan > 5) es señal de alerta."),
            ]),
            card("7. Asociación entre variables categóricas", [
                html.P("La prueba χ² de independencia contrasta si dos variables categóricas están asociadas. Su "
                       "tamaño de efecto se mide con la V de Cramér, que va de 0 a 1:"),
                F(r"V = \sqrt{\frac{\chi^2}{n \cdot \min(r - 1,\; c - 1)}}"),
                html.P("Como regla orientativa, V < 0.1 es un efecto pequeño y V ≈ 0.3 uno moderado."),
            ]),
            card("8. Comparación de grupos y tamaño del efecto", [
                _ul(["Mann–Whitney U: compara dos grupos sin suponer normalidad.",
                     "Kruskal–Wallis H: extiende la comparación a tres o más grupos.",
                     "t de Welch: compara medias con varianzas distintas."]),
                F(r"U_1 = R_1 - \frac{n_1 (n_1 + 1)}{2}"),
                F(r"H = \frac{12}{N (N + 1)} \sum_{g} \frac{R_g^2}{n_g} - 3 (N + 1)"),
                F(r"t = \frac{\bar{x}_1 - \bar{x}_2}{\sqrt{\dfrac{s_1^2}{n_1} + \dfrac{s_2^2}{n_2}}}"),
                html.P("Con n ≈ 30 000 casi cualquier diferencia resulta significativa; por eso se reporta el tamaño del "
                       "efecto y la relevancia práctica, no solo el p-value."),
            ]),
        ], className="grid g2"),
        html.Div([
            card("Antecedentes", [
                html.P("Yeh y Lien (2009) compararon seis técnicas de minería de datos (regresión logística, análisis "
                       "discriminante, k vecinos, Naive Bayes, redes neuronales y árboles de clasificación) para "
                       "predecir el incumplimiento con estos mismos datos, y propusieron un método de suavizado por "
                       "ordenamiento (Sorting Smoothing Method) para estimar la probabilidad real de incumplimiento."),
                html.P("La sección Modelos retoma esa comparación con siete clasificadores, cuatro técnicas de "
                       "balanceo y cuatro métodos de optimización de hiperparámetros."),
            ]),
        ], className="grid"),
        card("Diccionario de variables", _tbl(["Variable", "Tipo", "Descripción"],
                                              [(html.Code(v), t, d) for v, t, d in var_table]),
             subtitle="Variables explicativas y variable objetivo (default_payment_next_month)"),
        html.Details([html.Summary([icon("book"), f"Referencias ({len(refs)})"]),
                      html.Ul([html.Li(r) for r in refs], className="refs")], className="card fold"),
    ])


# ---------------------------------------------------------------- Portada y vistazo rápido
def fig_home():
    """Tasa de default según el estado de pago de septiembre (el hallazgo más claro del EDA)."""
    g = df.groupby("PAY_0")[TARGET].agg(["mean", "size"])
    g = g[g["size"] >= 100]
    fig = go.Figure(go.Bar(
        x=[str(int(i)) for i in g.index], y=g["mean"] * 100, marker_color=MONO, customdata=g["size"],
        hovertemplate="PAY_0 = %{x}<br>Default: %{y:.1f}%<br>Clientes: %{customdata:,}<extra></extra>"))
    fig.add_hline(y=GLOBAL_RATE * 100, line_dash="dash", line_color=WARM_GOLD, line_width=1.6,
                  annotation_text=f"Tasa global {GLOBAL_RATE:.1%}", annotation_position="top left",
                  annotation_font_color=WARM_GOLD)
    style_fig(fig, 310, legend_top=False)
    fig.update_layout(margin=dict(l=55, r=20, t=24, b=55), showlegend=False,
                      xaxis_title="Estado de pago en septiembre (PAY_0)",
                      yaxis_title="% que incumple el mes siguiente")
    fig.update_xaxes(type="category")
    return fig


def link_cards(compact=False):
    items = []
    for L in LINKS:
        body = [html.Div([html.Span(icon(L["icon"]), className="lc-ico"), icon("external", "lc-ext")],
                         className="lc-top"),
                html.Div(L["title"], className="lc-title")]
        if not compact:
            body.append(html.P(L["desc"]))
        body.append(html.Div(L["url"].split("//", 1)[-1], className="lc-url"))
        items.append(html.A(body, href=L["url"], target="_blank", rel="noopener noreferrer",
                            className="link-card", title=f"Abrir: {L['title']}"))
    return html.Div(items, className="link-grid")


def quick_look():
    """Gráfica de PAY_0 (antes en la portada), ahora al inicio de Introducción."""
    r_late = df.loc[df["PAY_0"] >= 2, TARGET].mean()
    r_ok = df.loc[df["PAY_0"] <= 0, TARGET].mean()
    return card("Vistazo rápido: el atraso de septiembre anticipa el incumplimiento",
                [dcc.Graph(id="home-graph", figure=fig_home(),
                           config={"displaylogo": False, "displayModeBar": False}),
                 html.P(f"Entre quienes tenían 2 o más meses de atraso en septiembre, {r_late:.0%} incumplió el mes "
                        f"siguiente; entre quienes iban al día o pagaban el mínimo, {r_ok:.0%}.", className="muted")],
                subtitle="Tasa de default según PAY_0 (grupos con al menos 100 clientes)")


def _stat(label, value):
    return html.Div([html.Span(label), html.B(value)], className="sig-stat")


def page_home():
    """Portada a pantalla completa: una tarjeta de crédito interactiva (inclina con el mouse, se voltea)."""
    front = html.Div([
        html.Div(className="cc-gloss"),
        html.Div([html.Span("Riesgo de crédito", className="cc-brand"), icon("contactless", "cc-nfc")],
                 className="cc-top"),
        html.Div(className="cc-chip"),
        html.Div("•••• •••• •••• 2005", className="cc-number"),
        html.Div([
            html.Div([html.Span("Titulares", className="cc-lbl"),
                      *[html.Div(a["name"], className="cc-name") for a in AUTHORS]]),
            html.Div([html.Span("Periodo de datos", className="cc-lbl"),
                      html.Div("ABR 2005 – SEP 2005", className="cc-name")], className="cc-valid"),
        ], className="cc-bottom"),
    ], className="cc-face cc-front")
    back = html.Div([
        html.Div(className="cc-gloss"),
        html.Div(className="cc-mag"),
        html.Div([_stat("Clientes", f"{len(df):,}"), _stat("Default", f"{GLOBAL_RATE:.1%}"),
                  _stat("Periodo", "Abr–Sep 2005")], className="cc-sig"),
        html.P("Datos: UCI · Banco de Taiwán · Yeh & Lien (2009)", className="cc-fine"),
    ], className="cc-face cc-back")
    card3d = html.Div(html.Div([front, back], className="cc-inner"), id="cc", tabIndex=0, className="cc",
                      **{"aria-label": "Tarjeta del proyecto. Púlsala para voltearla"})
    return html.Div([
        html.Div(className="bill-bg"),
        html.Div([
            html.Div(html.Div(card3d, className="cc-settle"), className="cc-scene"),
            html.Div([
                html.Div([icon("card"), "Proyecto EDA"], className="cover-tag"),
                html.H1(PROJECT_TITLE),
                html.P(f"Quién deja de pagar el mes siguiente y qué señales lo anticipan: {len(df):,} clientes de "
                       "tarjeta de crédito de un banco de Taiwán, de abril a septiembre de 2005.", className="hero-lead"),
                dcc.Link(["Iniciar recorrido", icon("arrow")], href="/introduccion", className="btn primary big"),
                html.Div([html.Span("Haz clic o toca la tarjeta para voltearla."), html.Span(INSTITUTION)],
                         className="cover-hint"),
            ], className="cover-copy"),
        ], className="cover-hero"),
    ], className="cover")


# ---------------------------------------------------------------- Modelos
F1_MAX = MR["f1_mean"].max()


def _mc_bar(label, v, scale=1.0, cls=""):
    """Fila de métrica con barra (v se dibuja como fracción de `scale`)."""
    if pd.isna(v):
        return html.Div([html.Span(label), html.Div(className="mc-bar na"), html.B("n/d", title="No calculado")],
                        className="mc-metric")
    return html.Div([html.Span(label),
                     html.Div(html.Span(style={"width": f"{min(v / scale, 1) * 100:.1f}%"}), className="mc-bar"),
                     html.B(f"{v:.3f}")], className=f"mc-metric {cls}".strip())


def model_slide(row, rank):
    """Tarjeta de un modelo dentro del carrusel (mejor combinación de ese modelo)."""
    m = row["model"]
    info = MODEL_INFO[m]
    best = rank == 1
    sub = MR[MR["model"] == m]
    by_tech = sub.groupby("technique")["f1_mean"].max()
    top = html.Div([html.Span(f"#{rank}", className="mc-rank"),
                    html.Span([icon("trophy"), "Mejor modelo"], className="mc-badge") if best
                    else html.Span(f"{row['f1_mean'] - F1_MAX:+.4f} F1 vs. el mejor", className="mc-fam-top")],
                   className="mc-top")
    return html.Article([
        html.Div(className="cc-gloss"),
        top,
        html.H3(info["label"], className="mc-name"),
        html.Div(info["family"], className="mc-family"),
        html.Div([
            html.Div(className="cc-chip mc-chip"),
            html.Div([html.Span("F1 · clase default", className="cc-lbl"),
                      html.Div([html.Span(f"{row['f1_mean']:.3f}", className="mc-f1"),
                                html.Span(f"± {row['f1_std']:.3f}", className="mc-std")])]),
        ], className="mc-score"),
        html.Div([html.Span(TECH_LBL[row["technique"]], className="mc-pill"),
                  html.Span(METHOD_LBL[row["method"]], className="mc-pill")], className="mc-config",
                 title="Técnica de balanceo y método de optimización de su mejor combinación"),
        html.Div([_mc_bar("Precisión", row["precision_mean"]), _mc_bar("Recall", row["recall_mean"]),
                  _mc_bar("ROC-AUC", row["roc_auc_mean"]), _mc_bar("PR-AUC", row["pr_auc_mean"])],
                 className="mc-metrics"),
        html.Div([html.Span("Mejor F1 con cada técnica de balanceo", className="cc-lbl"),
                  *[_mc_bar(TECH_LBL[t], by_tech.get(t), F1_MAX, "on" if t == row["technique"] else "")
                    for t in TECH_ORDER]], className="mc-metrics mc-tech"),
        html.P(info["desc"], className="mc-desc"),
        html.P(info["note"], className="mc-note"),
        html.Div(f"16 combinaciones · F1 de {sub['f1_mean'].min():.3f} a {sub['f1_mean'].max():.3f}",
                 className="mc-foot"),
    ], className="mc-slide" + (" best" if best else ""),
        **{"aria-label": f"Puesto {rank}: {info['label']}, F1 {row['f1_mean']:.3f}"})


def models_carousel():
    rows = list(BEST_BY_MODEL.iterrows())
    slides = [model_slide(r, i + 1) for i, r in rows]
    dots = [html.Button(className="mc-dot", n_clicks=0,
                        **{"data-i": str(i), "type": "button", "title": MODEL_INFO[r["model"]]["label"],
                           "aria-label": f"Ver {MODEL_INFO[r['model']]['label']}"})
            for i, r in rows]
    return html.Div([
        html.Div([
            html.Button(icon("chevron"), className="mc-nav mc-prev", n_clicks=0,
                        **{"type": "button", "title": "Modelo anterior", "aria-label": "Modelo anterior"}),
            html.Div(slides, className="mc-track", tabIndex=0,
                     **{"role": "region", "aria-label": "Carrusel de modelos; usa las flechas para desplazarte"}),
            html.Button(icon("chevron"), className="mc-nav mc-next", n_clicks=0,
                        **{"type": "button", "title": "Modelo siguiente", "aria-label": "Modelo siguiente"}),
        ], className="mc-stage"),
        html.Div(dots, className="mc-dots"),
        html.P("Desliza, usa las flechas o los puntos para recorrer los siete modelos.", className="muted mc-hint"),
    ], className="mc-wrap")


def page_models():
    b, info = BEST, MODEL_INFO[BEST["model"]]
    c = BEST_CM
    pos, flagged = c["tp"] + c["fn"], c["tp"] + c["fp"]
    gcfg = {"displaylogo": False, "displayModeBar": False}
    return html.Div([
        page_title("Modelos", "Siete clasificadores comparados con validación cruzada anidada; desliza para ver cada uno"),
        html.Div([
            kpi("Combinaciones evaluadas", f"{len(MR)}", "7 modelos × 4 balanceos × 4 optimizadores", "layers"),
            kpi("Mejor F1 (clase default)", f"{b['f1_mean']:.3f}", f"{info['label']} · {TECH_LBL[b['technique']]}",
                "trophy"),
            kpi("Mejora sobre la línea base", f"+{b['f1_mean'] - BASELINE:.3f}",
                f"Regresión logística sin balanceo: {BASELINE:.3f}", "bars"),
            kpi("Incumplimientos detectados", f"{b['recall_mean']:.0%}", "Recall del mejor modelo (umbral 0.5)",
                "target"),
        ], className="kpi-row k4"),
        card("Comparación de modelos", models_carousel(),
             subtitle="Mejor combinación de cada modelo, ordenados por F1 medio en los 3 folds externos. "
                      "El borde dorado marca el mejor."),
        html.Div([
            card("F1 por modelo y técnica de balanceo", [
                dcc.Graph(id="mdl-heat", figure=fig_models_heat(), config=gcfg),
                interp_block(
                    "Cada celda es el mejor F1 que logró el modelo con esa técnica. Sin balanceo todos rinden peor, "
                    "porque casi no detectan a quienes incumplen; con pesos de clase, Random Forest y XGBoost "
                    "llegan a 0.55.",
                    "Comparación por factor (Friedman con 28 bloques modelo × método): χ² = 59.8, p ≈ 7·10⁻¹³. "
                    "Sin balanceo el F1 medio es 0.453, frente a 0.526 (pesos de clase), 0.519 (SMOTE) y 0.513 "
                    "(ADASYN); «sin balanceo» es peor que las tres (Nemenyi, p ≤ 10⁻⁴). Pesos de clase supera a "
                    "ADASYN (p = 0.020) y no se distingue de SMOTE (p = 0.67). Naive Bayes es el único modelo "
                    "al que el balanceo casi no le cambia el F1."),
            ]),
            card("Balancear mueve el umbral, no la capacidad de ordenar", [
                dcc.Graph(id="mdl-scatter", figure=fig_models_scatter(), config=gcfg),
                interp_block(
                    "Cada punto es una de las 112 combinaciones. Las que no balancean (gris) quedan abajo: "
                    "aciertan poco con quienes incumplen. Pero no quedan más a la izquierda: ordenan a los clientes "
                    "casi igual de bien; lo que cambia es dónde se pone el corte entre «paga» e «incumple».",
                    "ROC-AUC medio por técnica (96 combinaciones locales): 0.758 sin balanceo, 0.761 con pesos de "
                    "clase, 0.754 con SMOTE y 0.749 con ADASYN. Al umbral de 0.5 el recall pasa de 0.377 a 0.610 y "
                    "la precisión baja de 0.618 a 0.460, así que la ganancia de F1 (0.456 → 0.523) viene en gran "
                    "parte del umbral y no de un modelo que discrimine mejor."),
            ]),
        ], className="grid g2"),
        html.Div([
            card(f"Mejor combinación: {info['label']}", [
                dcc.Graph(id="mdl-cm", figure=fig_best_cm(), config=gcfg),
                interp_block(
                    f"De los {pos:,} clientes que incumplieron, el modelo detecta {c['tp']:,} ({c['tp'] / pos:.0%}). "
                    f"A cambio marca {c['fp']:,} falsas alarmas: de los {flagged:,} clientes que señala como "
                    f"riesgosos, {c['tp'] / flagged:.0%} sí incumple.",
                    f"{TECH_LBL[b['technique']]} y optimización {METHOD_LBL[b['method']].lower()}. Predicciones "
                    "out-of-fold de los tres modelos de los folds externos, con umbral 0.5 (AUC agrupado 0.781). "
                    "Las probabilidades no están calibradas (ECE = 0.196) porque el balanceo infla la clase "
                    "positiva; una recalibración isotónica la baja a 0.017 en un fold. Ajustar el umbral según el "
                    "costo de cada tipo de error es el siguiente paso natural."),
            ], subtitle=f"Matriz de confusión out-of-fold sobre {sum(c.values()):,} clientes"),
            card("Qué variables pesan más en el mejor modelo (SHAP)", [
                _ul([
                    [html.B("PAY_0 domina: "), "el atraso de septiembre es, con diferencia, la variable más "
                     "importante; más meses de atraso empujan la predicción hacia el default."],
                    [html.B("Le siguen PAY_2 y PAY_3, "), "y más abajo PAY_4 a PAY_6: en todas, más atraso, más riesgo."],
                    [html.B("Mayor límite de crédito, menor riesgo: "), "los valores altos de LIMIT_BAL reducen la "
                     "probabilidad de default."],
                    [html.B("Montos pagados y facturados: "), "pagar más se asocia con menor riesgo, pero con un "
                     "efecto individual pequeño; la facturación media aparece quinta y discrimina poco."],
                ]),
                html.P("Coincide con el EDA: el historial de pagos es la señal más fuerte del incumplimiento y el "
                       "perfil demográfico pesa poco.", className="callout"),
                html.P("SHAP del Random Forest sobre 100 clientes de un fold (06_interpretability.ipynb). Con "
                       "variables correlacionadas SHAP reparte la importancia entre ellas, así que el orden "
                       "exacto entre PAY_2 … PAY_6 es aproximado.", className="muted"),
            ], subtitle="Resumen del notebook de interpretabilidad"),
        ], className="grid g2"),
    ])


# ---------------------------------------------------------------- Predecir
def _pf_field(label, comp, hint=None, cls=""):
    return html.Div([html.Label(label, htmlFor=getattr(comp, "id", None), className="ctl-label"), comp,
                     html.Div(hint, className="pf-hint") if hint else None], className=f"pf-field {cls}".strip())


def _num(id_, value, step="any", min_=None):
    return dcc.Input(id=f"pf-{id_}", type="number", value=value, step=step, min=min_, debounce=True,
                     className="pf-input", placeholder=pretty(id_))


def _tiles(id_, options, value):
    """Opciones como tarjetas con ícono (RadioItems con estilo)."""
    return dcc.RadioItems(
        id=f"pf-{id_}", value=value, className="pf-tiles", inputClassName="pf-tile-in", labelClassName="pf-tile",
        options=[{"label": html.Span([icon(ic, "pf-tile-ico"), html.Span(txt, className="pf-tile-txt")]), "value": v}
                 for v, txt, ic in options])


SEX_TILES = [(1, "Hombre", "male"), (2, "Mujer", "female"), (SEX_OTHER, "Otro", "gender")]
EDU_TILES = [(1, "Posgrado", "cap"), (2, "Universidad", "book"), (3, "Secundaria", "pencil"), (4, "Otros", "dots")]
MAR_TILES = [(1, "Casado", "rings"), (2, "Soltero", "person"), (3, "Otros", "dots")]


def _pay_slider(col, value):
    return dcc.Slider(id=f"pf-{col}", min=-2, max=8, step=1, value=value, included=False,
                      marks={i: {"label": str(i)} for i in range(-2, 9)}, className="pf-pay-slider",
                      allow_direct_input=False)


SERIALIZE_CODE = """import joblib

# 1) Entrenar y guardar (modelo/entrenar.py)
modelo = busqueda.best_estimator_            # Pipeline: variables + one-hot + Random Forest
joblib.dump(modelo, "modelo/modelo_credito.pkl", compress=3)

# 2) Cargar en el tablero (app.py), una sola vez al arrancar
modelo = joblib.load("modelo/modelo_credito.pkl")

# 3) Predecir con los datos del formulario
cliente = pd.DataFrame([valores], columns=INPUT_COLS)
riesgo = modelo.predict_proba(cliente)[0, 1]  # puntaje de 0 a 1"""


def model_info_card():
    m = MODELO_META
    pr = m.get("prueba", {})
    hp = m.get("hiperparametros", {})
    ver = m.get("versiones", {})
    rows = [("Modelo", f"{m.get('modelo', '—')} · {m.get('balanceo', '')}"),
            ("Búsqueda", m.get("busqueda", "—")),
            ("Hiperparámetros", ", ".join(f"{k} = {v}" for k, v in hp.items()) or "—"),
            ("Prueba (20 %)", f"F1 {pr.get('f1', 0):.3f} · recall {pr.get('recall', 0):.3f} · precisión "
                              f"{pr.get('precision', 0):.3f} · ROC-AUC {pr.get('roc_auc', 0):.3f}" if pr else "—"),
            ("Entrenado", f"{m.get('n_entrenamiento', 0):,} clientes · {m.get('fecha', '—')}"),
            ("Versiones", f"scikit-learn {ver.get('scikit-learn', '—')} · joblib {ver.get('joblib', '—')}")]
    steps = [("Entrenar", "Se ajusta el bosque con los datos históricos (modelo/entrenar.py).", "tree"),
             ("Guardar", "joblib.dump escribe el modelo en un archivo .pkl.", "save"),
             ("Cargar", "El tablero lo lee con joblib.load al arrancar, sin reentrenar.", "notebook"),
             ("Predecir", "Cada cambio del formulario llama a predict_proba.", "gauge")]
    return card("Cómo se serializó el modelo", [
        html.P("Serializar es guardar un modelo ya entrenado en un archivo para usarlo después sin volver a "
               "entrenarlo. Así funciona esta sección:"),
        html.Div([html.Div([html.Span(f"{i + 1}", className="pf-step-n"), icon(ic, "pf-step-ico"),
                            html.B(t), html.P(d)], className="pf-step") for i, (t, d, ic) in enumerate(steps)],
                 className="pf-steps"),
        html.Details([html.Summary("Ver el código"), html.Pre(SERIALIZE_CODE, className="formula pf-code")],
                     className="pf-details"),
        html.Div(_tbl(["Detalle", "Valor"], rows), className="table-wrap"),
        html.P(["El archivo guarda todo el pipeline, incluidas las transformaciones del proyecto (logaritmos y "
                "resumen de las facturas), que viven en ", html.Code("modelo/features.py"),
                ". Para cargarlo hay que usar la misma versión de scikit-learn con la que se guardó."],
               className="muted"),
    ], subtitle="Entrenar → guardar (.pkl) → cargar → predecir")


def _flow():
    n = len(MODELO[-1].estimators_) if MODELO is not None else 0
    items = [("users", "1. Datos del cliente", "Perfil, pagos y montos de abril a septiembre."),
             ("layers", "2. Se transforman", "Logaritmos y resumen de las facturas, igual que en el proyecto."),
             ("tree", f"3. {n} árboles opinan", "Cada árbol del bosque estima si el cliente incumplirá."),
             ("gauge", "4. Puntaje y decisión", "Se promedian sus opiniones; desde 50 % es «riesgo alto».")]
    out = []
    for i, (ic, t, d) in enumerate(items):
        out.append(html.Div([html.Span(icon(ic), className="pf-flow-ico"), html.Div([html.B(t), html.P(d)])],
                            className="pf-flow-item"))
        if i < len(items) - 1:
            out.append(html.Span(icon("chevron"), className="pf-flow-arrow"))
    return html.Div(out, className="pf-flow")


def page_predict():
    head = page_title("Predecir", "Estima el riesgo de incumplimiento de un cliente con el modelo serializado")
    if MODELO is None:
        return html.Div([head, card("El modelo no está disponible", [
            html.P(["No se encontró ", html.Code("modelo/modelo_credito.pkl"), " o no se pudo cargar."]),
            html.P(["Para generarlo, desde la carpeta ", html.Code("dash/"), " ejecuta ",
                    html.Code("python -m modelo.entrenar"), "."]),
            html.P(MODELO_ERROR, className="muted")])])
    base = PROFILES["tipico"][1]
    gcfg = {"displaylogo": False, "displayModeBar": False}
    form = card("Datos del cliente", [
        html.Div([html.Span("Prueba un ejemplo:", className="pf-hint"),
                  *[html.Button([icon(ic), lbl], id=f"pf-prof-{k}", n_clicks=0, className="btn ghost pf-prof",
                                type="button")
                    for (k, (lbl, _v)), ic in zip(PROFILES.items(), ["users", "target", "alert"])]],
                 className="pf-profiles"),
        html.H4([icon("users"), "Perfil"], className="pf-h"),
        html.Div([
            _pf_field("Cupo de crédito", dcc.Slider(
                id="pf-LIMIT_BAL", min=10000, max=1000000, step=10000, value=base["LIMIT_BAL"],
                marks={10000: "10 mil", 250000: "250 mil", 500000: "500 mil", 750000: "750 mil", 1000000: "1 M"},
                tooltip={"placement": "top", "always_visible": True, "template": "NT$ {value}"},
                className="pf-slider", allow_direct_input=False)),
            _pf_field("Edad", dcc.Slider(
                id="pf-AGE", min=21, max=79, step=1, value=base["AGE"],
                marks={i: str(i) for i in range(30, 80, 10)},
                tooltip={"placement": "top", "always_visible": True, "template": "{value} años"},
                className="pf-slider", allow_direct_input=False)),
        ], className="pf-grid pf-g2"),
        _pf_field("Sexo", _tiles("SEX", SEX_TILES, base["SEX"])),
        html.P("El dataset solo registra hombre y mujer; con «Otro» el modelo promedia ambas predicciones.",
               className="pf-hint pf-note"),
        _pf_field("Educación", _tiles("EDUCATION", EDU_TILES, base["EDUCATION"]), cls="pf-row"),
        _pf_field("Estado civil", _tiles("MARRIAGE", MAR_TILES, base["MARRIAGE"]), cls="pf-row"),
        html.H4([icon("calendar"), "Estado de pago por mes (2005)"], className="pf-h"),
        html.Div([html.Span("−2 sin consumo", className="pf-key k-ok"), html.Span("−1 pagó todo", className="pf-key k-ok"),
                  html.Span("0 pago mínimo", className="pf-key k-mid"),
                  html.Span("1 a 8: meses de atraso", className="pf-key k-late")], className="pf-keys"),
        html.Div([html.Div([html.Span(m, className="pf-pay-m"), _pay_slider(c, base[c])], className="pf-pay-row")
                  for m, c in zip(MONTH_LBL, PAY_CHRONO)], className="pf-pay"),
        html.H4([icon("coin"), "Montos por mes (NT$)"], className="pf-h"),
        html.Div(html.Div([
            html.Span(), *[html.Span(m, className="pf-mh") for m in MONTH_LBL],
            html.Span("Facturado", className="pf-rh"), *[_num(c, base[c]) for c in BILL_CHRONO],
            html.Span("Pagado", className="pf-rh"), *[_num(c, base[c], min_=0) for c in PAYAMT_CHRONO],
        ], className="pf-amounts"), className="table-wrap"),
    ], cls="pf-form")
    result = card("Resultado", [
        dcc.Graph(id="pf-gauge", figure=fig_risk_gauge(), config=gcfg),
        html.Div(id="pf-verdict"),
        html.Div(id="pf-trees"),
    ], subtitle="Se actualiza en vivo con cada cambio", cls="pf-result")
    return html.Div([
        head,
        _flow(),
        html.Div([form, html.Div(result, className="pf-side")], className="pf-layout"),
        html.Div([
            card("Historial del cliente", [
                dcc.Graph(id="pf-history", config=gcfg),
                interp_block(
                    "Las barras comparan lo que le facturaron con lo que pagó cada mes; la línea dorada muestra su "
                    "estado de pago. Cuando la línea sube por encima de 0 hay atraso, y cuando las barras doradas "
                    "son mucho más bajas que las azules, el cliente está pagando poco de su deuda.",
                    "El modelo no usa las seis facturas por separado: las resume en nivel medio (log con signo), "
                    "tendencia mensual y número de meses con saldo a favor, como en el proyecto. Los estados de "
                    "pago (PAY_0 … PAY_6) sí entran uno por uno y son las variables más importantes según SHAP."),
            ], subtitle="Facturado, pagado y estado de pago de abril a septiembre"),
            card("¿Qué empuja su riesgo?", [
                dcc.Graph(id="pf-drivers", config=gcfg),
                interp_block(
                    "Cada barra responde: «si en este grupo de datos el cliente fuera como un cliente típico, ¿cuánto "
                    "cambiaría su puntaje?». Las barras doradas suben el riesgo y las azules lo bajan.",
                    "Explicación local por sustitución: se reemplaza cada grupo de variables por los valores del "
                    "cliente típico (mediana o moda) y se mide la diferencia en el puntaje. Es aproximada: no suma "
                    "exactamente el total porque los grupos interactúan dentro del bosque (a diferencia de SHAP)."),
            ], subtitle="Aporte de cada grupo de variables frente a un cliente típico"),
        ], className="grid g2"),
        card("¿Qué pasaría si…?", [
            dcc.RadioItems(id="pf-whatif-var", value="PAY_0", className="pf-tiles pf-seg", inputClassName="pf-tile-in",
                           labelClassName="pf-tile", options=[{"label": v[0], "value": k} for k, v in WHATIF.items()]),
            dcc.Graph(id="pf-whatif", config=gcfg),
            interp_block(
                "La línea muestra el puntaje que tendría este mismo cliente si solo cambiara la variable elegida; "
                "la estrella es su situación actual. Por ejemplo, con «Atraso en septiembre» se ve cuánto sube el "
                "riesgo con cada mes de atraso.",
                "Es una curva de dependencia individual (ICE): se fija el resto de variables y se recorre una sola. "
                "En un bosque la curva tiene escalones porque cada árbol corta la variable en umbrales; no implica "
                "causalidad, solo describe cómo responde el modelo."),
        ], subtitle="Mueve una sola variable y mira cómo cambia el puntaje de este cliente"),
        model_info_card(),
    ])


def trees_block(values):
    yes, n = tree_votes(values)
    share = yes / n if n else 0
    cells = int(round(share * 100))
    return html.Div([
        html.Div([icon("tree"), html.B(f"{yes} de {n} árboles votan «incumple»")], className="pf-trees-h"),
        html.Div([html.Span(className="pf-cell" + (" on" if i < cells else "")) for i in range(100)],
                 className="pf-waffle", title=f"{share:.0%} de los árboles"),
        html.P("Cada cuadro es 1 % del bosque. El puntaje promedia las probabilidades de todos los árboles, "
               "por eso puede diferir un poco de esta proporción.", className="muted"),
    ], className="pf-trees")


def predict_verdict(values, score):
    thr = MODELO_META.get("umbral", 0.5)
    high = score >= thr
    pr = MODELO_META.get("prueba", {})
    late = [m for m, c in zip(MONTH_LBL, PAY_CHRONO) if (values.get(c) or 0) >= 1]
    signals = []
    if (values.get("PAY_0") or 0) >= 1:
        n = values["PAY_0"]
        signals.append(("alert", f"{n} {'mes' if n == 1 else 'meses'} de atraso en septiembre: la señal que más "
                                 "pesa en el modelo."))
    elif late:
        signals.append(("calendar", f"Tuvo atrasos en {', '.join(late)}, aunque en septiembre está al día."))
    else:
        signals.append(("target", "Sin atrasos en los seis meses."))
    bills = sum(values.get(c) or 0 for c in BILL_COLS)
    paid = sum(values.get(c) or 0 for c in PAYAMT_COLS)
    if bills > 0:
        signals.append(("coin", f"Pagó el {min(paid / bills, 9.99):.0%} de lo facturado en el periodo."))
    q = (df["LIMIT_BAL"] < (values.get("LIMIT_BAL") or 0)).mean()
    signals.append(("card", f"Su cupo supera al de {q:.0%} de los clientes."))
    return html.Div([
        html.Div([icon("alert" if high else "target"),
                  html.Div([html.B("Riesgo alto: probable incumplimiento" if high else "Riesgo bajo: probable pago"),
                            html.Span(f"Puntaje {score:.0%} · umbral {thr:.0%}")])],
                 className="pf-badge " + ("hi" if high else "lo")),
        html.Ul([html.Li([icon(ic), html.Span(s)]) for ic, s in signals], className="pf-signals"),
        html.Details([html.Summary("¿Cómo leer el puntaje?"), html.P(
            (f"Con el umbral de 50 % el modelo detecta {pr.get('recall', 0):.0%} de quienes incumplen y acierta en "
             f"{pr.get('precision', 0):.0%} de los clientes que marca como riesgosos (datos de prueba). " if pr else "")
            + "No es una probabilidad calibrada: el modelo se entrenó con pesos de clase, que lo hacen sobrestimar "
              "el riesgo frente a la tasa real (22 %). Sirve para ordenar y clasificar clientes.")],
            className="pf-details"),
    ])


# ---------------------------------------------------------------- Enlaces
def book_summary():
    return card("Sobre el proyecto", [
        html.P("Flujo completo de ciencia de datos y aprendizaje automático para predecir el incumplimiento de pago "
               "en clientes de tarjetas de crédito, a partir de los 30,000 registros del repositorio UCI."),
        html.P("Incluye un pipeline de extracción, limpieza y transformación (ETL), un análisis exploratorio centrado "
               "en el desbalance de clases y la multicolinealidad severa entre los montos facturados, y un diseño "
               "factorial de 112 configuraciones que compara algoritmos, representaciones de variables, técnicas de "
               "balanceo y optimización (genética y bayesiana). El resultado mejora el F1 de la clase minoritaria y "
               "reduce los falsos negativos frente a la regresión logística base."),
    ], subtitle="Resumen basado en el README del Jupyter Book")


def pipeline_card():
    rows = [html.A([html.Span(n, className="nb-num"),
                    html.Div([html.Div(t, className="nb-t"), html.P(d)], className="nb-body"),
                    icon("external", "nb-ext")],
                   href=BOOK_URL + "notebooks/" + f, target="_blank", rel="noopener noreferrer", className="nb-row")
            for n, t, f, d in NOTEBOOKS]
    return card("Pipeline completo", html.Div(rows, className="nb-list"),
                subtitle="Los siete notebooks del libro, en el orden del flujo de trabajo")


def page_links():
    return html.Div([
        page_title("Enlaces", "Libro del proyecto, notebooks, repositorios y fuente de los datos"),
        book_summary(),
        link_cards(),
        pipeline_card(),
        card("Reproducir el análisis", _ul([
            ["Clona el repositorio del proyecto e instala las dependencias con ", html.Code("pip install -r requirements.txt"),
             " (la guía del repositorio usa un entorno Conda con Python 3.12)."],
            ["Abre el notebook del EDA desde la carpeta ", html.Code("notebooks/"), " y ejecútalo en VS Code."],
            ["Para correr este tablero: ", html.Code("python app.py"), " y abre ", html.Code("http://127.0.0.1:8050"), "."],
        ], ordered=True)),
    ])


# ---------------------------------------------------------------- Equipo
def _team_link(ic, label, href):
    ext = {} if href.startswith("mailto:") else {"target": "_blank", "rel": "noopener noreferrer"}
    return html.A([icon(ic), html.Span(label)], href=href, className="tc-link", title=label, **ext)


def _copy_email(email):
    """Botón que copia el correo al portapapeles (ver TEAM_JS) y avisa con «¡Correo copiado!»."""
    return html.Button([icon("mail"), html.Span(email, className="tc-copy-txt"),
                        html.Span("¡Correo copiado!", className="tc-copy-ok", **{"aria-live": "polite"})],
                       className="tc-link tc-copy", title=f"Copiar {email}", n_clicks=0,
                       **{"data-email": email, "type": "button"})


def team_card(m, i):
    """Tarjeta de crédito vertical: frente con foto y rol; reverso con bio y enlaces (se voltea)."""
    front = html.Div([
        html.Div(className="cc-gloss"),
        html.Div([html.Span("Equipo · Uninorte", className="cc-brand"), icon("contactless", "cc-nfc")],
                 className="cc-top"),
        html.Div(html.Img(src=app.get_asset_url(m["photo"]), alt=f"Foto de {m['name']}"),
                 className="tc-photo"),
        html.Div([html.Div(className="cc-chip tc-chip"),
                  html.Div(f"•••• •••• •••• {m['card_no']}", className="tc-number")], className="tc-mid"),
        html.Div([html.Span("Titular", className="cc-lbl"), html.Div(m["name"], className="tc-name"),
                  html.Div(m["role"], className="tc-role")]),
        html.Div([icon("flip"), "Toca para ver contacto"], className="tc-hint"),
    ], className="cc-face tc-front")
    back = html.Div([
        html.Div(className="cc-gloss"),
        html.Div(className="cc-mag tc-mag"),
        html.Div([html.Span("Firma autorizada", className="tc-sig-lbl"),
                  html.Div(m["short"], className="tc-sig-name")], className="tc-sig"),
        html.P(m["bio"], className="tc-bio"),
        html.Div([_team_link("github", "GitHub", m["github"]),
                  _team_link("linkedin", "LinkedIn", m["linkedin"]),
                  _copy_email(m["email"])], className="tc-links"),
        html.P("Universidad del Norte · Ciencia de Datos", className="cc-fine tc-fine"),
    ], className="cc-face tc-back")
    return html.Div(html.Div([front, back], className="tc-inner"), className="tc", tabIndex=0,
                    **{"role": "button", "aria-pressed": "false",
                       "aria-label": f"Tarjeta de {m['name']}. Púlsala para ver su contacto"})


def page_team():
    return html.Div([
        page_title("Equipo", "Quiénes hicimos este análisis y cómo contactarnos"),
        html.Div([html.Div(team_card(m, i), className="tc-scene") for i, m in enumerate(TEAM)],
                 className="team-grid"),
        html.P("Haz clic o toca una tarjeta para voltearla y ver la bio y los enlaces.", className="muted team-hint"),
    ])


# =============================================================================
# 7. APLICACIÓN, CSS, NAVEGACIÓN Y CALLBACKS
# =============================================================================
app = Dash(__name__, suppress_callback_exceptions=True, title="EDA · Riesgo Crediticio")
server = app.server   # <- para despliegue (gunicorn app:server)


@server.route("/ping")
def ping():
    """Respuesta mínima para monitores (UptimeRobot, GitHub Actions) que mantienen despierto el
    servicio gratis de Render, sin cargar la página completa."""
    return "ok", 200, {"Content-Type": "text/plain; charset=utf-8", "Cache-Control": "no-store"}

CSS = """
:root {
  --deep:%%DEEP%%; --navy:%%NAVY%%; --pale:%%PALE%%; --gold:%%GOLD%%; --cream:%%CREAM%%;
  --bg:%%CREAM%%; --surface:#FFFFFF; --surface-2:#F8F6F0;
  --text:%%DEEP%%; --muted:#5D667F; --line:rgba(26,35,61,.10); --line-strong:rgba(26,35,61,.24);
  --accent:%%NAVY%%; --on-accent:#FFFFFF; --accent-2:%%GOLD%%;
  --side-bg:%%DEEP%%; --side-text:#D3D8E5; --side-muted:#9AA3BA; --side-line:rgba(255,255,255,.10);
  --note-bg:#F6F0E1; --note-line:%%GOLD%%; --tech-bg:#ECEEF4; --tech-line:%%NAVY%%;
  --code-bg:#EBE5D5; --th-bg:%%DEEP%%; --zebra:#FAF8F3; --focus:%%GOLD%%;
}
[data-theme="dark"] {
  color-scheme: dark;
  --bg:#141A2B; --surface:#1B2338; --surface-2:#222B43;
  --text:#E8E4DA; --muted:#A7B0C6; --line:rgba(232,228,218,.10); --line-strong:rgba(232,228,218,.26);
  --accent:%%PALE%%; --on-accent:#1A233D; --accent-2:%%PALE%%;
  --side-bg:#10162A; --side-text:#D3D8E5; --side-muted:#98A1B8; --side-line:rgba(255,255,255,.08);
  --note-bg:rgba(210,187,137,.12); --note-line:%%PALE%%; --tech-bg:rgba(142,156,198,.14); --tech-line:#8E9CC6;
  --code-bg:rgba(210,187,137,.16); --th-bg:#2A3552; --zebra:rgba(255,255,255,.03); --focus:%%PALE%%;
}
* { box-sizing:border-box; }
html { scroll-behavior:smooth; }
html, body { margin:0; padding:0; background:var(--bg); color:var(--text);
  font-family:Inter,'Segoe UI',Roboto,Helvetica,Arial,sans-serif; font-size:15px; line-height:1.55; }
a { color:inherit; }
:focus-visible { outline:2px solid var(--focus); outline-offset:2px; border-radius:6px; }

/* ---------- Íconos ---------- */
.ico { display:inline-block; flex:none; width:1.2em; height:1.2em; background-color:currentColor;
  -webkit-mask:var(--ico) center/contain no-repeat; mask:var(--ico) center/contain no-repeat; }

/* ---------- Barra lateral ---------- */
.sidebar { position:fixed; top:0; left:0; bottom:0; width:272px; background:var(--side-bg); color:var(--side-text);
  padding:24px 18px; display:flex; flex-direction:column; border-right:1px solid var(--side-line); overflow-y:auto;
  z-index:50; transition:transform .3s ease; }
.brand { display:block; color:inherit; text-decoration:none; padding:0 6px 18px; }
.brand-tag { color:var(--pale); font-size:12px; font-weight:600; }
.brand-title { font-size:20px; line-height:1.25; font-weight:700; margin:6px 0 4px; color:#fff; }
.brand-sub { color:var(--side-muted); font-size:12.5px; margin:0; }
.nav { border-top:1px solid var(--side-line); padding-top:12px; }
.nav a { display:flex; align-items:center; gap:11px; padding:9px 12px; margin:2px 0; border-radius:8px; color:var(--side-text);
  text-decoration:none; font-weight:500; position:relative; transition:background .15s, color .15s; }
.nav a .ico { opacity:.8; }
.nav a:hover { background:rgba(255,255,255,.07); color:#fff; }
.nav a.active { background:rgba(255,255,255,.10); color:#fff; font-weight:600; }
.nav a.active::before { content:''; position:absolute; left:0; top:8px; bottom:8px; width:3px; border-radius:3px; background:var(--pale); }
.nav a.active .ico { opacity:1; color:var(--pale); }
.authors { margin-top:auto; padding:16px 6px 0; border-top:1px solid var(--side-line); }
.authors h4 { margin:0 0 10px; color:var(--pale); font-size:12.5px; font-weight:600; }
.author { margin-bottom:10px; }
.author .nm { font-weight:600; font-size:13.5px; color:#fff; }
.author .em { font-size:12px; color:var(--side-muted); word-break:break-all; }
.inst { font-size:11.5px; color:var(--side-muted); margin-top:8px; }
.app.collapsed .sidebar { transform:translateX(-100%); }
.app.collapsed .main { margin-left:0; }

/* ---------- Estructura y barra superior ---------- */
.main { margin-left:272px; min-height:100vh; display:flex; flex-direction:column; transition:margin-left .3s ease; }
.topbar { background:var(--surface); color:var(--text); padding:12px 32px; border-bottom:1px solid var(--line);
  display:flex; justify-content:space-between; align-items:center; gap:16px; position:sticky; top:0; z-index:40; }
.tb-left, .tb-right { display:flex; align-items:center; gap:12px; }
.topbar .t1 { font-weight:700; font-size:16px; }
.topbar .t2 { color:var(--muted); font-size:12.5px; }
.badge { color:var(--muted); font-size:12.5px; font-weight:500; padding:5px 12px; border-radius:999px;
  border:1px solid var(--line-strong); white-space:nowrap; }
.icon-btn { display:inline-flex; align-items:center; justify-content:center; width:36px; height:36px; padding:0;
  background:transparent; border:1px solid var(--line-strong); border-radius:8px; color:var(--text); cursor:pointer;
  text-decoration:none; font-family:inherit; transition:background .15s, border-color .15s, color .15s; }
.icon-btn .ico { width:18px; height:18px; }
.icon-btn:hover { background:var(--surface-2); border-color:var(--accent-2); color:var(--accent-2); }
.theme-toggle { position:relative; display:inline-flex; align-items:center; width:62px; height:32px; padding:3px;
  border-radius:999px; border:1px solid var(--line-strong); background:var(--surface-2); cursor:pointer; }
.theme-toggle::before { content:''; position:absolute; top:3px; left:3px; width:24px; height:24px; border-radius:50%;
  background:var(--accent); transition:transform .2s ease; }
[data-theme="dark"] .theme-toggle::before { transform:translateX(30px); }
.theme-toggle .ico { position:relative; z-index:1; width:24px; height:24px; -webkit-mask-size:14px; mask-size:14px; }
.theme-toggle .t-sun { color:var(--on-accent); } .theme-toggle .t-moon { color:var(--muted); margin-left:6px; }
[data-theme="dark"] .theme-toggle .t-sun { color:var(--muted); }
[data-theme="dark"] .theme-toggle .t-moon { color:var(--on-accent); }
.content { padding:28px 32px 10px; flex:1; }

/* ---------- Títulos ---------- */
.page-title h2 { margin:0; font-size:27px; font-weight:700; letter-spacing:-.01em; display:flex; align-items:center; gap:12px; }
.page-title .pt-ico { width:26px; height:26px; color:var(--accent-2); }
.page-title { margin-bottom:22px; } .page-title p { margin:6px 0 22px; color:var(--muted); }
.section-h { font-size:18px; font-weight:700; margin:30px 0 12px; }

/* ---------- Tarjetas y KPI ---------- */
.card { background:var(--surface); border-radius:10px; padding:20px 22px; margin-bottom:20px; border:1px solid var(--line); min-width:0; }
.card-title { margin:0 0 4px; font-size:17px; font-weight:700; }
.card-sub { margin:0 0 12px; color:var(--muted); font-size:13px; }
.card p { margin:8px 0; }
.card ul { margin:6px 0 6px 20px; padding:0; } .card li { margin:4px 0; }
.card ol { margin:6px 0 6px 22px; padding:0; }
.muted { color:var(--muted); font-size:13.5px; }
.refs li { font-size:13.5px; }
.grid { display:grid; gap:20px; } .g2 { grid-template-columns:repeat(2,minmax(0,1fr)); }
.g3 { grid-template-columns:repeat(3,minmax(0,1fr)); } .g4 { grid-template-columns:repeat(4,minmax(0,1fr)); }
.span-2 { grid-column:span 2; }
.kpi-row { display:grid; gap:16px; margin-bottom:20px; } .k4 { grid-template-columns:repeat(4,minmax(0,1fr)); }
.k3 { grid-template-columns:repeat(3,minmax(0,1fr)); margin:12px 0; }
.kpi { background:var(--surface); border:1px solid var(--line); border-left:3px solid var(--accent-2); border-radius:10px; padding:14px 16px; }
.kpi-head { display:flex; align-items:center; gap:8px; color:var(--muted); }
.kpi-head .ico { color:var(--accent-2); width:17px; height:17px; }
.kpi-label { font-size:12.5px; font-weight:600; }
.kpi-value { font-size:26px; font-weight:700; margin:6px 0 2px; letter-spacing:-.01em; }
.kpi-note { font-size:12px; color:var(--muted); }

/* ---------- Controles ---------- */
.controls { display:flex; flex-wrap:wrap; gap:18px; margin:6px 0 12px; align-items:flex-end; }
.control { min-width:220px; flex:1; }
.ctl-label { display:block; font-size:12.5px; font-weight:600; color:var(--muted); margin-bottom:5px; }
.radio label, .check label { display:inline-flex; align-items:center; gap:5px; margin-right:16px; cursor:pointer; font-size:14px; }
.radio input, .check input { accent-color:var(--accent); }

/* ---------- Interpretaciones ---------- */
.interp-wrap { margin-top:12px; }
.interp-btn { display:inline-flex; align-items:center; gap:8px; cursor:pointer; list-style:none; user-select:none;
  padding:7px 14px; border-radius:999px; border:1px solid var(--line-strong); font-weight:600; font-size:13px;
  color:var(--text); background:var(--surface-2); transition:border-color .15s, color .15s; }
.interp-btn::-webkit-details-marker { display:none; }
.interp-btn:hover { border-color:var(--accent-2); color:var(--accent-2); }
.interp-btn .ico { width:15px; height:15px; }
.interp-chev { transition:transform .2s ease; }
.interp-wrap[open] .interp-chev { transform:rotate(90deg); }
.interp-wrap[open] .interp-btn { border-color:var(--accent-2); }
.interp-body { margin-top:10px; display:grid; gap:10px; }
.interp { border-radius:8px; padding:10px 14px; }
.interp b { font-size:13px; }
.interp p { margin:6px 0 2px !important; font-size:14px; }
.interp.basic { background:var(--note-bg); border-left:3px solid var(--note-line); }
.interp.tech { background:var(--tech-bg); border-left:3px solid var(--tech-line); }
/* desplegable tipo tarjeta (Referencias del Marco Teórico) */
details.fold > summary { cursor:pointer; list-style:none; display:flex; align-items:center; gap:10px;
  font-weight:700; font-size:16px; }
details.fold > summary::-webkit-details-marker { display:none; }
details.fold > summary::after { content:'+'; margin-left:auto; font-size:20px; font-weight:400; color:var(--accent-2); }
details.fold[open] > summary::after { content:'−'; }
details.fold > summary .ico { color:var(--accent-2); }
details.fold[open] > summary { margin-bottom:10px; }
/* fórmulas LaTeX (MathJax) */
.formula.dash-markdown, .formula > div { overflow-x:auto; }
.formula { text-align:center; }
.formula mjx-container { margin:2px 0 !important; font-size:118% !important; }
.formula p { margin:0; }

/* ---------- Contenido de texto ---------- */
.callout { background:var(--note-bg); border-left:3px solid var(--note-line); border-radius:8px; padding:14px 18px; font-size:15.5px; font-weight:600; }
.formula { background:var(--tech-bg); border-left:3px solid var(--tech-line); border-radius:8px; padding:9px 14px; margin:8px 0;
  font-family:Consolas,'Courier New',monospace; font-size:13.5px; overflow-x:auto; }
.tag { display:inline-block; background:var(--accent); color:var(--on-accent); border-radius:999px; font-size:11.5px;
  font-weight:600; padding:2px 10px; margin-left:8px; white-space:nowrap; }
code { background:var(--code-bg); color:var(--text); padding:2px 6px; border-radius:6px; font-size:13px; }
.table-wrap { overflow-x:auto; }
.vtable { border-collapse:collapse; width:100%; font-size:14px; }
.vtable th { background:var(--th-bg); color:#fff; text-align:left; padding:10px 12px; font-weight:600; }
.vtable th:first-child { border-top-left-radius:8px; } .vtable th:last-child { border-top-right-radius:8px; }
.vtable td { padding:9px 12px; border-bottom:1px solid var(--line); vertical-align:top; }
.vtable tr:nth-child(even) td { background:var(--zebra); }
.finding { background:var(--surface); border:1px solid var(--line); border-left:3px solid var(--accent-2); border-radius:10px; padding:14px 16px; }
.find-title { font-weight:700; margin-bottom:4px; } .finding p { margin:4px 0; font-size:14px; }

/* ---------- Portada (texto) ---------- */
.hero-lead { font-size:17px; color:var(--muted); max-width:52ch; margin:0 0 24px; }
.btn { display:inline-flex; align-items:center; gap:9px; padding:10px 16px; border-radius:8px; font-weight:600; font-size:14.5px;
  text-decoration:none; border:1px solid transparent; transition:background .15s, border-color .15s, transform .15s; }
.btn .ico { width:17px; height:17px; }
.btn.primary { background:var(--accent); color:var(--on-accent); }
.btn.primary:hover { filter:brightness(1.12); } .btn.primary:hover .ico { transform:translateX(3px); }
.btn.primary .ico { transition:transform .15s; }
.btn.ghost { border-color:var(--line-strong); color:var(--text); }
.btn.ghost:hover { background:var(--surface-2); border-color:var(--accent-2); }
.link-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(250px,1fr)); gap:14px; margin-bottom:20px; }
.link-card { display:flex; flex-direction:column; gap:8px; padding:16px; background:var(--surface); border:1px solid var(--line);
  border-radius:10px; text-decoration:none; color:var(--text); transition:border-color .15s, background .15s; }
.link-card:hover { border-color:var(--accent-2); background:var(--surface-2); }
.lc-top { display:flex; justify-content:space-between; align-items:center; }
.lc-ico { display:inline-flex; align-items:center; justify-content:center; width:34px; height:34px; border-radius:8px;
  background:var(--surface-2); border:1px solid var(--line); color:var(--accent-2); }
.lc-ext { width:16px; height:16px; color:var(--muted); transition:color .15s; }
.link-card:hover .lc-ext { color:var(--accent-2); }
.lc-title { font-weight:700; }
.link-card p { margin:0; color:var(--muted); font-size:13.5px; }
.lc-url { color:var(--muted); font-size:12px; word-break:break-all; margin-top:auto; }

/* ---------- Pie ---------- */
.footer { background:var(--surface); color:var(--muted); padding:16px 32px; border-top:1px solid var(--line); font-size:12.5px;
  display:flex; flex-wrap:wrap; gap:8px 24px; justify-content:space-between; align-items:center; margin-top:24px; }
.footer b { color:var(--text); }
.footer-links { display:flex; flex-wrap:wrap; gap:6px 18px; }
.footer-links a { display:inline-flex; align-items:center; gap:6px; color:var(--muted); text-decoration:none; }
.footer-links a:hover { color:var(--accent-2); }
.footer-links .ico { width:15px; height:15px; }

/* ---------- Menús desplegables (Dash) en modo oscuro ---------- */
[data-theme="dark"] .Select-control, [data-theme="dark"] .Select-menu-outer, [data-theme="dark"] .Select-menu,
[data-theme="dark"] .VirtualizedSelectOption, [data-theme="dark"] .dash-dropdown,
[data-theme="dark"] .dash-dropdown-content { background:var(--surface-2) !important; color:var(--text) !important;
  border-color:var(--line-strong) !important; }
[data-theme="dark"] .Select-value-label, [data-theme="dark"] .Select-placeholder,
[data-theme="dark"] .Select--single > .Select-control .Select-value, [data-theme="dark"] .Select-input > input,
[data-theme="dark"] .dash-dropdown * { color:var(--text) !important; }
[data-theme="dark"] .VirtualizedSelectFocusedOption, [data-theme="dark"] .Select-option.is-focused { background:var(--th-bg) !important; }
[data-theme="dark"] .Select-value { background:transparent !important; }
[data-theme="dark"] .Select-arrow { border-top-color:var(--text) !important; }

/* ---------- Adaptación a pantallas pequeñas ---------- */
@media (max-width:1100px) { .g3,.g4,.k4 { grid-template-columns:repeat(2,minmax(0,1fr)); } .span-2 { grid-column:span 2; } }
@media (max-width:900px) {
  .sidebar { position:static; width:100%; } .main { margin-left:0; } .app.collapsed .sidebar { display:none; }
  .g2,.g3,.g4,.k4,.k3 { grid-template-columns:1fr; } .span-2 { grid-column:auto; }
  .topbar { position:static; flex-wrap:wrap; padding:12px 16px; } .content { padding:20px 16px; } .footer { padding:16px; } }
@media (prefers-reduced-motion:reduce) { * { transition:none !important; scroll-behavior:auto !important; } }
"""
for _tok, _val in {"%%DEEP%%": DEEP_NAVY, "%%NAVY%%": NAVY, "%%PALE%%": PALE_GOLD,
                   "%%GOLD%%": WARM_GOLD, "%%CREAM%%": CREAM}.items():
    CSS = CSS.replace(_tok, _val)

# ---------- CSS nuevo: detalles de tarjeta, portada, Anterior/Siguiente, pipeline ----------
NEW_CSS = """
/* ---- detalles sobrios de tarjeta ---- */
.kpi-value { font-variant-numeric:tabular-nums; letter-spacing:.04em; }
.brand-tag { display:flex; align-items:center; gap:7px; }
.badge { display:inline-flex; align-items:center; gap:7px; }
.brand-tag .ico { width:15px; height:15px; color:var(--pale); }
.badge .ico { width:15px; height:15px; color:var(--accent-2); }

/* ---- portada: sin menú, barra superior ni pie ---- */
.app.cover .sidebar, .app.cover .topbar, .app.cover .footer { display:none; }
.app.cover .main { margin-left:0; } .app.cover .content { padding:0; }
.cover-toggle { display:none; }
.app.cover .cover-toggle { display:inline-flex; position:fixed; top:18px; right:22px; z-index:60; }
.cover { position:relative; min-height:100vh; display:flex; align-items:center; overflow:hidden; }
.bill-bg { position:absolute; inset:0; opacity:.7; pointer-events:none;
  background:repeating-linear-gradient(115deg, var(--line) 0 1px, transparent 1px 13px),
             repeating-linear-gradient(35deg, var(--line) 0 1px, transparent 1px 17px);
  -webkit-mask-image:radial-gradient(ellipse at 30% 50%, #000 20%, transparent 80%);
  mask-image:radial-gradient(ellipse at 30% 50%, #000 20%, transparent 80%); }
.cover-hero { position:relative; width:100%; display:grid; grid-template-columns:minmax(0,1.1fr) minmax(0,1fr);
  gap:56px; align-items:center; padding:56px 7vw; }
.cover-tag { display:inline-flex; align-items:center; gap:8px; color:var(--accent-2); font-weight:700; font-size:14px; margin-bottom:14px; }
.cover-copy h1 { font-size:clamp(32px,4.2vw,50px); line-height:1.1; letter-spacing:-.02em; margin:0 0 16px; }
.btn.big { padding:14px 24px; font-size:16px; }
.cover-hint { display:flex; flex-direction:column; gap:3px; margin-top:22px; font-size:12.5px; color:var(--muted); }

/* ---- tarjeta ---- */
.cc-scene { perspective:1200px; display:flex; justify-content:center; }
.cc-settle, .cc, .cc-inner { transform-style:preserve-3d; }
.cc-settle { width:min(540px,88vw); animation:cc-settle .9s cubic-bezier(.2,.8,.2,1) both; }
.cc { position:relative; aspect-ratio:1.586; border-radius:22px; cursor:pointer; outline:none;
  transition:transform .18s ease-out; transform:rotateX(var(--rx,0deg)) rotateY(var(--ry,0deg)); }
.cc:focus-visible { box-shadow:0 0 0 3px var(--focus); }
.cc-inner { position:absolute; inset:0; transition:transform .8s cubic-bezier(.3,.7,.2,1); }
.cc.flipped .cc-inner { transform:rotateY(180deg); }
.cc-face { position:absolute; inset:0; border-radius:22px; overflow:hidden; color:#F3EFE7; padding:6.5% 7%;
  backface-visibility:hidden; -webkit-backface-visibility:hidden; border:1px solid rgba(210,187,137,.38);
  background:repeating-radial-gradient(circle at 88% 12%, rgba(210,187,137,.08) 0 1px, transparent 1px 8px),
             linear-gradient(135deg, #2A3860 0%, #1A233D 60%, #141B30 100%);
  box-shadow:0 34px 60px -24px rgba(8,12,30,.6), inset 0 1px 0 rgba(255,255,255,.08); }
.cc-front { display:flex; flex-direction:column; justify-content:space-between; }
.cc-back { transform:rotateY(180deg); padding:0; display:flex; flex-direction:column; }
.cc-gloss { position:absolute; inset:0; pointer-events:none; mix-blend-mode:soft-light; opacity:.9;
  background:radial-gradient(circle at var(--mx,28%) var(--my,18%), rgba(255,255,255,.5), transparent 46%); }
.cc-top { display:flex; justify-content:space-between; align-items:center; }
.cc-brand { font-size:clamp(11px,1.5vw,13px); font-weight:700; letter-spacing:.14em; color:#D2BB89; }
.cc-nfc { width:26px; height:26px; color:#D2BB89; }
.cc-chip { position:relative; width:17%; aspect-ratio:1.25; border-radius:9px;
  background:linear-gradient(135deg, #E6D3A3, #B88F3D 60%, #D2BB89); }
.cc-chip::before { content:''; position:absolute; left:0; right:0; top:50%; height:1px; background:rgba(26,35,61,.45);
  box-shadow:0 -9px 0 rgba(26,35,61,.35), 0 9px 0 rgba(26,35,61,.35); }
.cc-chip::after { content:''; position:absolute; top:0; bottom:0; left:50%; width:1px; background:rgba(26,35,61,.45); }
.cc-number { font-family:Consolas,'Courier New',monospace; font-size:clamp(17px,3.3vw,27px); letter-spacing:.14em;
  font-variant-numeric:tabular-nums; text-shadow:0 1px 0 rgba(0,0,0,.45), 0 -1px 0 rgba(255,255,255,.14); }
.cc-bottom { display:flex; justify-content:space-between; align-items:flex-end; gap:12px; }
.cc-lbl { display:block; font-size:10px; letter-spacing:.1em; color:#9AA3BA; margin-bottom:2px; }
.cc-name { font-size:clamp(11px,1.7vw,14px); font-weight:600; letter-spacing:.1em; text-transform:uppercase; }
.cc-valid { text-align:right; }
.cc-mag { height:17%; margin-top:8%; background:#0B1020; }
.cc-sig { margin:7% 7% 0; padding:3.5% 4%; border-radius:6px; display:grid; grid-template-columns:repeat(3,1fr); gap:8px;
  background:repeating-linear-gradient(135deg, #F3EFE7 0 6px, #E9E3D3 6px 12px); color:#1A233D; }
.sig-stat { display:flex; flex-direction:column; }
.sig-stat span { font-size:10px; letter-spacing:.06em; color:#5D667F; }
.sig-stat b { font-size:clamp(12px,2.2vw,17px); font-variant-numeric:tabular-nums; }
.cc-fine { margin:auto 7% 6%; font-size:10.5px; color:#9AA3BA; }
@keyframes cc-settle { from { opacity:0; transform:translateY(-26px) rotate(-3deg) scale(.96); } to { opacity:1; transform:none; } }

/* ---- Anterior / Siguiente ---- */
.pn-row { display:flex; justify-content:space-between; gap:16px; margin:8px 0 18px; }
.pn { display:inline-flex; align-items:center; gap:12px; padding:12px 18px; border:1px solid var(--line-strong); border-radius:10px;
  background:var(--surface); color:var(--text); text-decoration:none; transition:border-color .15s, background .15s; }
.pn:hover { border-color:var(--accent-2); background:var(--surface-2); }
.pn small { display:block; font-size:11.5px; color:var(--muted); } .pn b { font-size:14.5px; }
.pn .ico { color:var(--accent-2); } .pn .flip { transform:scaleX(-1); }
.pn.next { text-align:right; margin-left:auto; }

/* ---- Pipeline completo ---- */
.nb-list { display:grid; gap:10px; }
.nb-row { display:flex; align-items:center; gap:14px; padding:12px 14px; border:1px solid var(--line); border-radius:10px;
  background:var(--surface); color:var(--text); text-decoration:none; transition:border-color .15s, background .15s; }
.nb-row:hover { border-color:var(--accent-2); background:var(--surface-2); }
.nb-num { flex:none; width:36px; height:36px; display:inline-flex; align-items:center; justify-content:center; border-radius:8px;
  background:var(--accent); color:var(--on-accent); font-weight:700; font-size:13px; font-variant-numeric:tabular-nums; }
.nb-body { flex:1; min-width:0; } .nb-t { font-weight:700; } .nb-body p { margin:2px 0 0; color:var(--muted); font-size:13.5px; }
.nb-ext { width:16px; height:16px; color:var(--muted); } .nb-row:hover .nb-ext { color:var(--accent-2); }

@media (max-width:900px) { .cover-hero { grid-template-columns:1fr; gap:32px; padding:72px 6vw 40px; } .cc-scene { order:-1; } }
@media (prefers-reduced-motion:reduce) { .cc-settle { animation:none; } }

/* ---- Equipo: tarjetas de crédito verticales ---- */
.team-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(260px,330px)); justify-content:center;
  gap:clamp(24px,4vw,56px); margin:8px 0 6px; }
.tc-scene { perspective:1200px; animation:cc-settle .8s cubic-bezier(.2,.8,.2,1) both; animation-delay:var(--d,0s); }
.tc-scene:nth-child(2) { animation-delay:.12s; }
.tc, .tc-inner { transform-style:preserve-3d; }
.tc { position:relative; aspect-ratio:0.63; border-radius:22px; cursor:pointer; outline:none;
  transition:transform .18s ease-out; transform:rotateX(var(--rx,0deg)) rotateY(var(--ry,0deg)); }
.tc:focus-visible { box-shadow:0 0 0 3px var(--focus); }
.tc-inner { position:absolute; inset:0; transition:transform .8s cubic-bezier(.3,.7,.2,1); }
.tc.flipped .tc-inner, .tc:has(.tc-link:focus-visible) .tc-inner { transform:rotateY(180deg); }
.tc .cc-face { padding:8% 8.5%; display:flex; flex-direction:column; }
.tc-front { gap:4.5%; }
.tc-front .cc-top, .tc-front .tc-photo, .tc-front .tc-mid { position:relative; }
.tc-photo { flex:1; min-height:0; border-radius:14px; overflow:hidden; border:1px solid rgba(210,187,137,.45);
  box-shadow:inset 0 0 0 1px rgba(0,0,0,.2); background:#141B30; }
.tc-photo img { width:100%; height:100%; object-fit:cover; object-position:50% 22%; display:block;
  filter:saturate(.92) contrast(1.03); }
.tc-mid { display:flex; align-items:center; gap:12px; }
.tc-chip { width:44px; flex:none; border-radius:7px; }
.tc-chip::before { box-shadow:0 -6px 0 rgba(26,35,61,.35), 0 6px 0 rgba(26,35,61,.35); }
.tc-number { font-family:Consolas,'Courier New',monospace; font-size:clamp(13px,1.35vw,15.5px); letter-spacing:.12em;
  white-space:nowrap; text-shadow:0 1px 0 rgba(0,0,0,.45), 0 -1px 0 rgba(255,255,255,.14); }
.tc-name { font-size:15px; font-weight:700; letter-spacing:.08em; text-transform:uppercase; line-height:1.25; }
.tc-role { margin-top:4px; font-size:12.5px; color:#D2BB89; line-height:1.4; }
.tc-hint { display:inline-flex; align-items:center; gap:6px; font-size:11px; color:#9AA3BA; letter-spacing:.04em; }
.tc-hint .ico { width:13px; height:13px; }
.tc-back { transform:rotateY(180deg); padding:0 !important; }
.tc-mag { height:auto; aspect-ratio:5.2; margin-top:12%; flex:none; }
.tc-sig { margin:7% 8.5% 0; padding:9px 12px; border-radius:6px; color:#1A233D;
  background:repeating-linear-gradient(135deg, #F3EFE7 0 6px, #E9E3D3 6px 12px); }
.tc-sig-lbl { display:block; font-size:9.5px; letter-spacing:.08em; color:#5D667F; text-transform:uppercase; }
.tc-sig-name { font-family:'Brush Script MT','Segoe Script',cursive; font-size:24px; line-height:1.15; }
.tc-bio { position:relative; margin:7% 8.5% 0; font-size:13.5px; line-height:1.55; color:#E3DED3; }
.tc-links { position:relative; display:grid; gap:8px; margin:auto 8.5% 0; }
.tc-link { display:flex; align-items:center; gap:10px; padding:9px 12px; border-radius:10px; min-width:0;
  border:1px solid rgba(210,187,137,.32); background:rgba(255,255,255,.04); color:#F3EFE7; text-decoration:none;
  font-size:13px; transition:background .15s, border-color .15s; }
.tc-link span { overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.tc-link .ico { color:#D2BB89; }
.tc-link:hover, .tc-link:focus-visible { background:rgba(210,187,137,.14); border-color:#D2BB89; }
button.tc-link { width:100%; font:inherit; font-size:13px; text-align:left; cursor:pointer; }
.tc-copy { position:relative; }
.tc-copy-ok { position:absolute; inset:0; display:flex; align-items:center; justify-content:center; gap:6px;
  border-radius:10px; background:#D2BB89; color:#1A233D; font-weight:700; opacity:0; transform:scale(.96);
  transition:opacity .2s, transform .2s; pointer-events:none; }
.tc-copy.copied .tc-copy-ok { opacity:1; transform:none; }
.tc-fine { position:relative; margin:5% 8.5% 7% !important; }
.team-hint { text-align:center; font-size:13px; margin:18px 0 8px; }
@media (max-width:600px) { .team-grid { grid-template-columns:minmax(0,320px); } }
@media (prefers-reduced-motion:reduce) { .tc-scene { animation:none; } .tc-inner { transition:none; } }

/* ---- Modelos: carrusel deslizable de tarjetas ---- */
@property --mc-ang { syntax:'<angle>'; initial-value:0deg; inherits:false; }
.mc-wrap { --mc-w:min(370px, 80%); }
.mc-stage { position:relative; margin:0 -8px; }
.mc-track { position:relative; display:flex; gap:22px; overflow-x:auto; overscroll-behavior-x:contain;
  scroll-snap-type:x mandatory; scroll-behavior:smooth; scrollbar-width:none;
  padding:30px calc((100% - var(--mc-w)) / 2) 34px; outline:none; border-radius:14px; }
.mc-track::-webkit-scrollbar { display:none; }
.mc-track:focus-visible { box-shadow:inset 0 0 0 2px var(--focus); }
.mc-slide { position:relative; flex:0 0 var(--mc-w); scroll-snap-align:center; display:flex; flex-direction:column;
  gap:12px; padding:20px 22px 18px; border-radius:20px; overflow:hidden; color:#F3EFE7;
  border:1px solid rgba(210,187,137,.30);
  background:repeating-radial-gradient(circle at 88% 12%, rgba(210,187,137,.07) 0 1px, transparent 1px 8px),
             linear-gradient(150deg, #2A3860 0%, #1A233D 58%, #141B30 100%);
  box-shadow:0 26px 46px -26px rgba(8,12,30,.65), inset 0 1px 0 rgba(255,255,255,.07);
  opacity:.72; filter:saturate(.8); transform:scale(.95); transition:opacity .35s ease, transform .35s ease, filter .35s ease; }
.mc-slide.is-active { opacity:1; filter:none; transform:none; }
.mc-slide .cc-gloss { opacity:.45; }
.mc-slide > *:not(.cc-gloss) { position:relative; }
/* el mejor: borde con luz dorada que recorre el contorno + halo suave */
.mc-slide.best { border-color:transparent; opacity:.8;
  animation:mc-glow 3.4s ease-in-out infinite; }
.mc-slide.best.is-active { opacity:1; }
.mc-slide.best::after { content:''; position:absolute; inset:0; border-radius:inherit; padding:2px; pointer-events:none;
  background:conic-gradient(from var(--mc-ang), rgba(210,187,137,.35) 0deg, rgba(210,187,137,.35) 200deg,
             #B88F3D 250deg, #F6E7C1 290deg, #D2BB89 315deg, rgba(210,187,137,.35) 350deg);
  -webkit-mask:linear-gradient(#000 0 0) content-box, linear-gradient(#000 0 0);
  -webkit-mask-composite:xor; mask-composite:exclude; animation:mc-spin 5s linear infinite; }
@keyframes mc-spin { to { --mc-ang:360deg; } }
@keyframes mc-glow {
  0%,100% { box-shadow:0 0 0 1px rgba(210,187,137,.45), 0 0 22px 0 rgba(210,187,137,.35), 0 26px 46px -26px rgba(8,12,30,.65); }
  50%     { box-shadow:0 0 0 1px rgba(210,187,137,.75), 0 0 38px 4px rgba(210,187,137,.55), 0 26px 46px -26px rgba(8,12,30,.65); } }
.mc-top { display:flex; justify-content:space-between; align-items:center; gap:10px; }
.mc-rank { font-family:Consolas,'Courier New',monospace; font-weight:700; font-size:14px; letter-spacing:.12em; color:#D2BB89; }
.mc-fam-top { font-size:10.5px; letter-spacing:.12em; text-transform:uppercase; color:#9AA3BA; text-align:right; }
.mc-badge { display:inline-flex; align-items:center; gap:6px; padding:4px 11px; border-radius:999px; font-size:11.5px;
  font-weight:700; letter-spacing:.06em; text-transform:uppercase; color:#1A233D;
  background:linear-gradient(135deg, #F1E1B6, #D2BB89 55%, #B88F3D); box-shadow:0 0 14px rgba(210,187,137,.55); }
.mc-badge .ico { width:14px; height:14px; }
.mc-name { margin:2px 0 0; font-size:23px; font-weight:800; letter-spacing:-.01em; color:#fff; }
.mc-family { margin-top:-8px; font-size:12.5px; color:#D2BB89; }
.mc-score { display:flex; align-items:center; gap:14px; padding:10px 0 2px; }
.mc-chip { width:46px; flex:none; border-radius:8px; }
.mc-chip::before { box-shadow:0 -7px 0 rgba(26,35,61,.35), 0 7px 0 rgba(26,35,61,.35); }
.mc-f1 { font-family:Consolas,'Courier New',monospace; font-size:36px; font-weight:700; letter-spacing:.06em;
  font-variant-numeric:tabular-nums; text-shadow:0 1px 0 rgba(0,0,0,.45), 0 -1px 0 rgba(255,255,255,.14); }
.mc-slide.best .mc-f1 { color:#F1E1B6; }
.mc-std { margin-left:8px; white-space:nowrap; font-size:12.5px; color:#9AA3BA; font-variant-numeric:tabular-nums; }
.mc-config { display:flex; flex-wrap:wrap; gap:6px; }
.mc-pill { font-size:12px; font-weight:600; padding:3px 10px; border-radius:999px; color:#F3EFE7;
  border:1px solid rgba(210,187,137,.38); background:rgba(255,255,255,.05); }
.mc-metrics { display:grid; gap:7px; padding-top:10px; border-top:1px solid rgba(255,255,255,.08); }
.mc-metric { display:grid; grid-template-columns:92px 1fr 44px; align-items:center; gap:10px; font-size:12.5px; color:#D3D8E5; }
.mc-tech .mc-metric { grid-template-columns:104px 1fr 44px; }
.mc-metric b { text-align:right; font-variant-numeric:tabular-nums; color:#F3EFE7; font-weight:600; }
.mc-bar { height:7px; border-radius:99px; background:rgba(255,255,255,.08); overflow:hidden; }
.mc-bar > span { display:block; height:100%; border-radius:inherit; background:linear-gradient(90deg, #66749C, #AEB8D6); }
.mc-bar.na { background:repeating-linear-gradient(135deg, rgba(255,255,255,.08) 0 4px, transparent 4px 8px); }
.mc-tech .mc-bar > span { background:linear-gradient(90deg, #4A5679, #8089A0); }
.mc-tech .mc-metric.on { color:#F1E1B6; font-weight:600; }
.mc-tech .mc-metric.on .mc-bar > span { background:linear-gradient(90deg, #B88F3D, #F1E1B6); }
.mc-desc { margin:2px 0 0 !important; font-size:13px; line-height:1.5; color:#E3DED3; }
.mc-note { margin:0 !important; font-size:12.5px; line-height:1.5; color:#B9C1D6; padding-left:10px;
  border-left:2px solid rgba(210,187,137,.55); }
.mc-foot { margin-top:auto; padding-top:8px; font-size:11px; letter-spacing:.06em; color:#9AA3BA;
  font-variant-numeric:tabular-nums; }
.mc-nav { position:absolute; top:50%; z-index:2; width:42px; height:42px; margin-top:-21px; display:inline-flex;
  align-items:center; justify-content:center; padding:0; border-radius:50%; cursor:pointer; color:var(--text);
  background:var(--surface); border:1px solid var(--line-strong); box-shadow:0 6px 18px -8px rgba(8,12,30,.45);
  transition:background .15s, border-color .15s, color .15s, opacity .15s; }
.mc-nav:hover { border-color:var(--accent-2); color:var(--accent-2); }
.mc-nav .ico { width:20px; height:20px; }
.mc-prev { left:4px; } .mc-prev .ico { transform:scaleX(-1); } .mc-next { right:4px; }
.mc-nav[disabled] { opacity:.35; cursor:default; }
.mc-dots { display:flex; justify-content:center; gap:8px; margin-top:2px; }
.mc-dot { width:9px; height:9px; padding:0; border-radius:99px; cursor:pointer; border:0; background:var(--line-strong);
  transition:width .25s ease, background .25s ease; }
.mc-dot.on { width:26px; background:var(--accent-2); }
.mc-dot:first-child { box-shadow:0 0 0 2px rgba(210,187,137,.45); }
.mc-hint { text-align:center; font-size:12.5px; margin:10px 0 0; }
@media (max-width:600px) { .mc-wrap { --mc-w:86%; } .mc-nav { display:none; } .mc-track { gap:14px; }
  .mc-slide { padding:18px 16px 16px; } .mc-f1 { font-size:30px; } .mc-chip { width:38px; }
  .mc-metric, .mc-tech .mc-metric { grid-template-columns:84px 1fr 40px; gap:8px; } }
@media (prefers-reduced-motion:reduce) {
  .mc-slide.best, .mc-slide.best::after { animation:none; }
  .mc-slide.best { box-shadow:0 0 0 1px rgba(210,187,137,.7), 0 0 30px 2px rgba(210,187,137,.45); }
  .mc-track { scroll-behavior:auto; } }

/* ---- Predecir: flujo, formulario visual y resultado ---- */
.pf-flow { display:flex; align-items:stretch; gap:10px; margin:0 0 20px; }
.pf-flow-item { flex:1; display:flex; gap:12px; align-items:flex-start; padding:14px 16px; border-radius:12px;
  background:var(--surface); border:1px solid var(--line); animation:pf-in .5s ease both; }
.pf-flow-item:nth-child(3) { animation-delay:.08s; } .pf-flow-item:nth-child(5) { animation-delay:.16s; }
.pf-flow-item:nth-child(7) { animation-delay:.24s; }
.pf-flow-item b { display:block; font-size:14px; } .pf-flow-item p { margin:2px 0 0; font-size:12.5px; color:var(--muted); }
.pf-flow-ico { flex:none; width:38px; height:38px; border-radius:10px; display:inline-flex; align-items:center;
  justify-content:center; background:var(--accent); color:var(--on-accent); }
.pf-flow-ico .ico { width:20px; height:20px; }
.pf-flow-arrow { align-self:center; color:var(--accent-2); } .pf-flow-arrow .ico { width:18px; height:18px; }
@keyframes pf-in { from { opacity:0; transform:translateY(8px); } to { opacity:1; transform:none; } }
.pf-layout { display:grid; grid-template-columns:minmax(0,1.55fr) minmax(310px,1fr); gap:20px; align-items:start; }
.pf-side { position:sticky; top:84px; }
.pf-profiles { display:flex; flex-wrap:wrap; align-items:center; gap:8px; margin:4px 0 6px; }
.pf-prof { padding:6px 12px; font-size:13px; cursor:pointer; background:transparent; font-family:inherit; }
.pf-prof .ico { width:15px; height:15px; color:var(--accent-2); }
.pf-h { margin:20px 0 12px; font-size:13px; font-weight:700; letter-spacing:.06em; text-transform:uppercase;
  color:var(--accent-2); display:flex; align-items:center; gap:8px; }
.pf-h .ico { width:16px; height:16px; }
.pf-h::after { content:''; flex:1; height:1px; background:var(--line); }
.pf-grid { display:grid; gap:14px 22px; margin-bottom:12px; }
.pf-g2 { grid-template-columns:repeat(2,minmax(0,1fr)); }
.pf-field { min-width:0; } .pf-field .ctl-label { margin-bottom:8px; }
.pf-hint { font-size:12.5px; color:var(--muted); } .pf-note { margin:6px 0 12px; } .pf-row { margin-bottom:14px; }
.pf-slider { padding-top:34px; }
.pf-form { --Dash-Fill-Interactive-Strong:var(--accent-2); --Dash-Fill-Inverse-Strong:var(--surface);
  --Dash-Text-Strong:var(--text); --Dash-Fill-Disabled:var(--line-strong); --Dash-Text-Primary:var(--muted); }
.pf-form .dash-slider-tooltip { color:var(--text); font-weight:700; font-variant-numeric:tabular-nums;
  white-space:nowrap; padding:6px 9px; }
.pf-form .dash-slider-mark { color:var(--muted); font-size:11.5px; }
.pf-form .dash-slider-thumb { width:18px; height:18px; }
/* tarjetas con ícono */
.pf-tiles { display:flex !important; flex-direction:row; flex-wrap:wrap; gap:8px; }
.pf-tiles .dash-options-list-option { flex:1 1 0; min-width:84px; position:relative; display:flex; padding:0;
  margin:0; background:transparent; align-items:stretch; }
.pf-tiles .dash-options-list-option-wrapper { position:absolute; width:1px; height:1px; overflow:hidden; opacity:0; }
.pf-tile { flex:1; display:flex; }
.pf-tile > span { flex:1; display:flex; flex-direction:column; align-items:center; justify-content:center; gap:6px;
  padding:12px 8px 10px; border-radius:12px; border:1.5px solid var(--line-strong); background:var(--surface);
  color:var(--muted); font-size:13px; font-weight:600; text-align:center;
  transition:border-color .15s, background .15s, color .15s, transform .15s, box-shadow .15s; }
.dash-options-list-option:hover .pf-tile > span { border-color:var(--accent-2); color:var(--text); transform:translateY(-2px); }
.pf-tile-ico { width:28px; height:28px; }
.dash-options-list-option.selected .pf-tile > span { border-color:var(--accent-2); color:var(--text);
  background:linear-gradient(180deg, rgba(210,187,137,.20), rgba(210,187,137,.06));
  box-shadow:0 0 0 3px rgba(210,187,137,.25), 0 8px 18px -12px rgba(184,143,61,.8); }
.dash-options-list-option.selected .pf-tile-ico { color:var(--accent-2); }
.dash-options-list-option:has(input:focus-visible) .pf-tile > span { outline:2px solid var(--focus); outline-offset:2px; }
.pf-seg { margin-bottom:6px; } .pf-seg .pf-tile > span { padding:9px 10px; flex-direction:row; }
/* estado de pago */
.pf-keys { display:flex; flex-wrap:wrap; gap:6px; margin-bottom:8px; }
.pf-key { font-size:11.5px; font-weight:600; padding:3px 9px; border-radius:999px; border:1px solid var(--line-strong); }
.pf-key.k-ok { background:var(--tech-bg); } .pf-key.k-mid { background:var(--surface-2); }
.pf-key.k-late { background:rgba(184,143,61,.16); border-color:rgba(184,143,61,.5); }
.pf-pay { display:grid; gap:2px; }
.pf-pay-row { display:grid; grid-template-columns:44px 1fr; align-items:center; gap:10px; }
.pf-pay-m { font-size:13px; font-weight:700; color:var(--muted); }
.pf-pay-slider { padding:6px 0 0; }
/* montos */
.pf-input { width:100%; height:36px; padding:6px 8px; border-radius:6px; border:1px solid var(--line-strong);
  background:var(--surface); color:var(--text); font:inherit; font-size:13px; font-variant-numeric:tabular-nums; }
.pf-input:focus { outline:none; border-color:var(--accent-2); box-shadow:0 0 0 3px rgba(184,143,61,.18); }
.pf-amounts { display:grid; grid-template-columns:78px repeat(6,minmax(0,1fr)); gap:8px; align-items:center; }
.pf-mh { font-size:12.5px; font-weight:600; color:var(--muted); text-align:center; }
.pf-rh { font-size:12.5px; font-weight:600; color:var(--muted); }
/* resultado */
.pf-result { border-top:3px solid var(--accent-2); }
.pf-badge { display:flex; align-items:center; gap:12px; padding:12px 14px; border-radius:10px; margin:0 0 10px;
  animation:pf-in .35s ease both; }
.pf-badge .ico { width:26px; height:26px; flex:none; }
.pf-badge b { display:block; font-size:15px; } .pf-badge span { font-size:12.5px; color:var(--muted); }
.pf-badge.hi { background:rgba(184,143,61,.14); border:1px solid rgba(184,143,61,.55); }
.pf-badge.hi .ico { color:var(--accent-2); }
.pf-badge.lo { background:var(--tech-bg); border:1px solid var(--line-strong); }
.pf-badge.lo .ico { color:var(--tech-line); }
.pf-signals { list-style:none; margin:0 0 8px; padding:0; display:grid; gap:7px; }
.card .pf-signals li { display:flex; gap:9px; align-items:flex-start; margin:0; font-size:13.5px; }
.pf-signals .ico { width:17px; height:17px; margin-top:2px; color:var(--accent-2); }
.pf-details { margin:8px 0; font-size:13.5px; } .pf-details summary { cursor:pointer; font-weight:700; color:var(--accent); }
.pf-details p { color:var(--muted); }
.pf-trees { margin-top:12px; padding-top:12px; border-top:1px solid var(--line); }
.pf-trees-h { display:flex; align-items:center; gap:8px; margin-bottom:8px; font-size:14px; }
.pf-trees-h .ico { width:20px; height:20px; color:var(--accent-2); }
.pf-waffle { display:grid; grid-template-columns:repeat(20,1fr); gap:3px; max-width:340px; }
.pf-cell { aspect-ratio:1; border-radius:3px; background:var(--line-strong); transition:background .4s ease; }
.pf-cell.on { background:var(--accent-2); }
/* serialización */
.pf-steps { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:12px; margin:12px 0; }
.pf-step { position:relative; padding:14px 14px 12px; border-radius:12px; background:var(--surface-2); border:1px solid var(--line); }
.pf-step-n { position:absolute; top:10px; right:12px; font-size:22px; font-weight:800; color:var(--line-strong); }
.pf-step-ico { width:24px; height:24px; color:var(--accent-2); }
.pf-step b { display:block; margin-top:6px; } .card .pf-step p { margin:4px 0 0; font-size:12.5px; color:var(--muted); }
.pf-code { white-space:pre; line-height:1.55; margin:10px 0 !important; }
@media (max-width:1250px) { .pf-layout { grid-template-columns:1fr; } .pf-side { position:static; }
  .pf-flow { flex-wrap:wrap; } .pf-flow-item { flex:1 1 40%; } .pf-flow-arrow { display:none; } }
@media (max-width:700px) { .pf-g2, .pf-steps { grid-template-columns:1fr; } .pf-flow-item { flex-basis:100%; }
  .pf-amounts { min-width:600px; }
  .pf-tiles .dash-options-list-option { min-width:64px; } .pf-tile > span { font-size:12px; padding:10px 4px 8px; } }
@media (prefers-reduced-motion:reduce) { .pf-flow-item, .pf-badge { animation:none; } }
"""

# ---------- JS de la portada: inclinación con el mouse, brillo y volteo ----------
COVER_JS = """
(function () {
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var fine = window.matchMedia('(hover: hover) and (pointer: fine)').matches;
  function cc() { return document.getElementById('cc'); }
  function setRole() { var c = cc(); if (c && !c.getAttribute('role')) c.setAttribute('role', 'button'); }
  function reset(c) { ['--rx', '--ry', '--mx', '--my'].forEach(function (k) { c.style.removeProperty(k); }); }
  document.addEventListener('mousemove', function (e) {
    var c = cc(); if (!c) return; setRole();
    if (reduce || !fine) return;
    var r = c.getBoundingClientRect();
    var x = Math.min(1.3, Math.max(-0.3, (e.clientX - r.left) / r.width));
    var y = Math.min(1.3, Math.max(-0.3, (e.clientY - r.top) / r.height));
    c.style.setProperty('--rx', ((0.5 - y) * 14).toFixed(2) + 'deg');
    c.style.setProperty('--ry', ((x - 0.5) * 18).toFixed(2) + 'deg');
    c.style.setProperty('--mx', (x * 100).toFixed(1) + '%');
    c.style.setProperty('--my', (y * 100).toFixed(1) + '%');
  });
  document.documentElement.addEventListener('mouseleave', function () { var c = cc(); if (c) reset(c); });
  function flip() { var c = cc(); if (!c) return; c.classList.toggle('flipped');
    c.setAttribute('aria-pressed', c.classList.contains('flipped') ? 'true' : 'false'); }
  document.addEventListener('click', function (e) { if (e.target.closest && e.target.closest('#cc')) flip(); });
  document.addEventListener('keydown', function (e) {
    var a = document.activeElement;
    if ((e.key === 'Enter' || e.key === ' ') && a && a.id === 'cc') { e.preventDefault(); flip(); }
  });
})();

// ---------- Equipo: tarjetas verticales (.tc) — inclinación, brillo y volteo ----------
(function () {
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var fine = window.matchMedia('(hover: hover) and (pointer: fine)').matches;
  function clear(c) { ['--rx', '--ry', '--mx', '--my'].forEach(function (k) { c.style.removeProperty(k); }); }
  document.addEventListener('mousemove', function (e) {
    if (reduce || !fine) return;
    var hit = e.target.closest ? e.target.closest('.tc') : null;
    document.querySelectorAll('.tc').forEach(function (c) {
      if (c !== hit) { clear(c); return; }
      var r = c.getBoundingClientRect();
      var x = (e.clientX - r.left) / r.width, y = (e.clientY - r.top) / r.height;
      c.style.setProperty('--rx', ((0.5 - y) * 10).toFixed(2) + 'deg');
      c.style.setProperty('--ry', ((x - 0.5) * 12).toFixed(2) + 'deg');
      c.style.setProperty('--mx', (x * 100).toFixed(1) + '%');
      c.style.setProperty('--my', (y * 100).toFixed(1) + '%');
    });
  });
  function copyEmail(btn) {
    var email = btn.getAttribute('data-email');
    function done() { btn.classList.add('copied'); clearTimeout(btn._t);
      btn._t = setTimeout(function () { btn.classList.remove('copied'); }, 1800); }
    function fallback() { var t = document.createElement('textarea'); t.value = email;
      t.style.position = 'fixed'; t.style.opacity = '0'; document.body.appendChild(t); t.select();
      try { document.execCommand('copy'); done(); } catch (err) { window.prompt('Copia el correo:', email); }
      document.body.removeChild(t); }
    if (navigator.clipboard && window.isSecureContext) navigator.clipboard.writeText(email).then(done, fallback);
    else fallback();
  }
  function flip(c) { c.classList.toggle('flipped');
    c.setAttribute('aria-pressed', c.classList.contains('flipped') ? 'true' : 'false'); }
  document.addEventListener('click', function (e) {
    if (!e.target.closest) return;
    var cp = e.target.closest('.tc-copy');
    if (cp) { copyEmail(cp); return; }
    if (e.target.closest('a, button')) return;   // los enlaces funcionan sin voltear
    var c = e.target.closest('.tc'); if (c) flip(c);
  });
  document.addEventListener('keydown', function (e) {
    var a = document.activeElement;
    if ((e.key === 'Enter' || e.key === ' ') && a && a.classList && a.classList.contains('tc')) {
      e.preventDefault(); flip(a); }
  });
})();

// ---------- Modelos: carrusel deslizable (flechas, puntos y tarjeta activa) ----------
(function () {
  function slides(t) { return t.querySelectorAll('.mc-slide'); }
  function current(t) {           // tarjeta cuyo centro está más cerca del centro visible
    var mid = t.scrollLeft + t.clientWidth / 2, best = 0, d = Infinity;
    slides(t).forEach(function (s, i) {
      var dd = Math.abs(s.offsetLeft + s.offsetWidth / 2 - mid); if (dd < d) { d = dd; best = i; } });
    return best;
  }
  function go(t, i) {
    var s = slides(t)[i]; if (!s) return;
    t.scrollTo({ left: s.offsetLeft - (t.clientWidth - s.offsetWidth) / 2, behavior: 'smooth' });
  }
  function sync(t) {
    var w = t.closest('.mc-wrap'); if (!w) return;
    var i = current(t), n = slides(t).length;
    slides(t).forEach(function (s, k) { s.classList.toggle('is-active', k === i); });
    w.querySelectorAll('.mc-dot').forEach(function (d, k) {
      d.classList.toggle('on', k === i);
      if (k === i) d.setAttribute('aria-current', 'true'); else d.removeAttribute('aria-current'); });
    var p = w.querySelector('.mc-prev'), nx = w.querySelector('.mc-next');
    if (p) p.disabled = i <= 0;
    if (nx) nx.disabled = i >= n - 1;
  }
  document.addEventListener('click', function (e) {
    if (!e.target.closest) return;
    var b = e.target.closest('.mc-prev, .mc-next, .mc-dot'); if (!b) return;
    var w = b.closest('.mc-wrap'), t = w && w.querySelector('.mc-track'); if (!t) return;
    if (b.classList.contains('mc-dot')) go(t, +b.getAttribute('data-i'));
    else go(t, current(t) + (b.classList.contains('mc-next') ? 1 : -1));
  });
  document.addEventListener('keydown', function (e) {
    var t = document.activeElement;
    if (!t || !t.classList || !t.classList.contains('mc-track')) return;
    if (e.key === 'ArrowRight' || e.key === 'ArrowLeft') {
      e.preventDefault(); go(t, current(t) + (e.key === 'ArrowRight' ? 1 : -1)); }
  });
  var raf = 0;
  document.addEventListener('scroll', function (e) {
    var t = e.target;
    if (!t.classList || !t.classList.contains('mc-track')) return;
    cancelAnimationFrame(raf); raf = requestAnimationFrame(function () { sync(t); });
  }, true);
  // Dash dibuja la página después de cargar: sincroniza cuando aparece un carrusel nuevo
  function scan() {
    document.querySelectorAll('.mc-track:not([data-ready])').forEach(function (t) {
      t.setAttribute('data-ready', '1'); t.scrollLeft = 0; sync(t); });
  }
  new MutationObserver(scan).observe(document.documentElement, { childList: true, subtree: true });
  window.addEventListener('resize', function () {
    document.querySelectorAll('.mc-track').forEach(function (t) { sync(t); }); });
})();
"""
CSS += NEW_CSS
CSS += _icon_css()


# ---------- Asistente Kyo: panel lateral derecho (tipo Copilot) y mascota fija ----------
# La lógica del bot vive en asistente/ (motor entrenado, base de conocimiento y mascota SVG).
from asistente import Asistente, construir_conocimiento, mascota_svg, mascota_uri  # noqa: E402

BOT_W = 400   # ancho del panel en px
BOT_CSS = """
/* ---- panel del asistente: se abre a la derecha y empuja el contenido ---- */
.bot-panel { position:fixed; top:0; right:0; bottom:0; width:%%W%%px; max-width:100vw; z-index:10002;
  display:flex; flex-direction:column; background:var(--surface); color:var(--text);
  border-left:1px solid var(--line-strong); box-shadow:-12px 0 32px rgba(10,14,30,.14);
  transform:translateX(100%); visibility:hidden; transition:transform .3s ease, visibility 0s linear .3s; }
.bot-open .bot-panel { transform:none; visibility:visible; transition:transform .3s ease, visibility 0s; }
.main { transition:margin-left .3s ease, margin-right .3s ease; }
@media (min-width:1101px) { .bot-open .main { margin-right:%%W%%px; } }
.bot-head { display:flex; align-items:center; gap:10px; padding:12px 14px; border-bottom:1px solid var(--line); }
.bot-av { width:40px; height:48px; flex:none; }
.bot-id { flex:1; min-width:0; }
.bot-name { font-weight:700; font-size:15px; display:flex; align-items:center; gap:8px; }
.bot-dot { width:8px; height:8px; border-radius:50%; background:#3FB27F; box-shadow:0 0 0 3px rgba(63,178,127,.18); }
.bot-sub { color:var(--muted); font-size:12px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.bot-head .icon-btn { width:32px; height:32px; }
.bot-where { padding:8px 16px; font-size:12px; color:var(--muted); border-bottom:1px solid var(--line);
  background:var(--surface-2); display:flex; align-items:center; gap:6px; }
.bot-where b { color:var(--text); font-weight:600; }
.bot-where .ico { width:14px; height:14px; color:var(--accent-2); }
.bot-msgs { flex:1; overflow-y:auto; padding:16px 14px 6px; display:flex; flex-direction:column; gap:14px;
  scroll-behavior:smooth; }
.bm { display:flex; gap:8px; align-items:flex-start; animation:bot-in .25s ease both; }
.bm.user { justify-content:flex-end; }
.bm-av { width:30px; height:36px; flex:none; margin-top:2px; }
.bm-bubble { max-width:86%; padding:10px 13px; border-radius:14px; font-size:13.5px; line-height:1.5;
  overflow-wrap:anywhere; }
.bm.bot .bm-bubble { background:var(--surface-2); border:1px solid var(--line); border-top-left-radius:4px; }
.bm.user .bm-bubble { background:var(--accent); color:var(--on-accent); border-top-right-radius:4px; }
.bm-bubble p { margin:0 0 7px; } .bm-bubble p:last-child { margin-bottom:0; }
.bm-bubble ul, .bm-bubble ol { margin:4px 0 7px; padding-left:18px; } .bm-bubble li { margin:2px 0; }
.bm-bubble code { background:var(--code-bg); padding:1px 5px; border-radius:4px; font-size:12px; }
.bm-bubble > div > *:last-child { margin-bottom:0; }
.bot-go { display:inline-flex; align-items:center; gap:6px; margin-top:8px; padding:5px 10px; border-radius:999px;
  font-size:12.5px; font-weight:600; text-decoration:none; color:var(--accent-2); border:1px solid var(--accent-2); }
.bot-go .ico { width:14px; height:14px; }
.bot-go:hover { background:var(--accent-2); color:var(--on-accent); }
.bot-sugs { display:flex; flex-wrap:wrap; gap:6px; padding:8px 14px 4px; }
.bot-sug { font:inherit; font-size:12.5px; text-align:left; padding:6px 11px; border-radius:999px; cursor:pointer;
  color:var(--text); background:transparent; border:1px solid var(--line-strong); transition:background .15s, border-color .15s; }
.bot-sug:hover { border-color:var(--accent-2); background:var(--surface-2); }
.bot-form { display:flex; gap:8px; padding:10px 14px 6px; }
.bot-input { flex:1; min-width:0; font:inherit; font-size:14px; padding:10px 12px; border-radius:10px;
  border:1px solid var(--line-strong); background:var(--surface-2); color:var(--text); }
.bot-input:focus { outline:none; border-color:var(--accent-2); box-shadow:0 0 0 3px rgba(184,143,61,.18); }
.bot-send { width:42px; flex:none; border:0; border-radius:10px; cursor:pointer; background:var(--accent);
  color:var(--on-accent); display:inline-flex; align-items:center; justify-content:center; }
.bot-send .ico { width:18px; height:18px; }
.bot-foot { margin:0; padding:2px 16px 12px; font-size:11px; color:var(--muted); }
@keyframes bot-in { from { opacity:0; transform:translateY(6px); } to { opacity:1; transform:none; } }

/* ---- Kyo, fijo en la esquina inferior derecha ---- */
/* z-index por encima de la barra de depuración de Dash (10000), que solo aparece con python app.py */
.kyo-walker { position:fixed; right:22px; bottom:4px; width:68px; height:82px; z-index:10001; cursor:pointer;
  transition:opacity .25s ease; -webkit-tap-highlight-color:transparent; }
.kyo-walker:focus-visible { outline:2px solid var(--focus); outline-offset:4px; border-radius:12px; }
.bot-open .kyo-walker { opacity:0; pointer-events:none; }
.kyo-flip { width:100%; height:100%; transition:transform .25s ease; }
.kyo-svg { width:100%; height:100%; overflow:visible; display:block; filter:drop-shadow(0 4px 6px rgba(20,16,43,.25));
  transition:transform .2s ease; }
.kyo-walker:hover .kyo-svg { transform:translateY(-4px) scale(1.06); }
.kyo-svg .a-eyes { transform-box:fill-box; transform-origin:center; animation:kyo-blink 4.6s infinite; }
.kyo-svg .a-leg, .kyo-svg .a-arm { transform-box:fill-box; transform-origin:50% 0; }
.kyo-svg .a-spark { transform-box:fill-box; transform-origin:center; animation:kyo-twinkle 2.4s ease-in-out infinite; }
.kyo-bubble { position:absolute; right:58px; bottom:64px; width:max-content; max-width:210px; padding:7px 11px;
  border-radius:12px 12px 2px 12px; background:var(--surface); color:var(--text); border:1px solid var(--line-strong);
  box-shadow:0 6px 18px rgba(10,14,30,.16); font-size:12.5px; font-weight:600; line-height:1.35;
  opacity:0; transform:translateY(6px); pointer-events:none; transition:opacity .25s ease, transform .25s ease; }
.kyo-walker.talk .kyo-bubble, .kyo-walker:hover .kyo-bubble { opacity:1; transform:none; }
@keyframes kyo-blink { 0%,92%,100% { transform:scaleY(1); } 95% { transform:scaleY(.12); } }
@keyframes kyo-twinkle { 0%,100% { transform:scale(1); opacity:1; } 50% { transform:scale(.7); opacity:.6; } }
@media (max-width:900px) {
  .bot-panel { width:100%; }
  .tb-right { flex-wrap:wrap; }   /* la barra superior ya no desborda la pantalla del celular */
  .kyo-walker { width:56px; height:68px; right:12px; }
  .kyo-bubble { right:46px; bottom:52px; } }
@media (prefers-reduced-motion:reduce) {
  .kyo-svg .a-eyes, .kyo-svg .a-spark { animation:none !important; }
  .bm { animation:none; } }
""".replace("%%W%%", str(BOT_W))
CSS += BOT_CSS

# Mascota fija en la página (fuera de Dash), en la esquina inferior derecha
WALKER_HTML = (
    '<div id="kyo-walker" class="kyo-walker" role="button" tabindex="0" '
    'aria-label="Abrir a Kyo, el asistente del tablero" title="Abrir a Kyo, el asistente del tablero">'
    '<div class="kyo-bubble">¿Te explico el tablero? ¡Tócame!</div>'
    f'<div class="kyo-flip">{mascota_svg("happy", cls="kyo-svg", uid="walker")}</div></div>')

BOT_JS = """
// ---------- Kyo: abrir y cerrar el panel (Kyo se queda fijo en la esquina inferior derecha) ----------
(function () {
  var root = document.documentElement;
  function walker() { return document.getElementById('kyo-walker'); }
  function relayout() { setTimeout(function () { window.dispatchEvent(new Event('resize')); }, 330); }
  function openBot() {
    if (root.classList.contains('bot-open')) return;
    var w = walker(); if (w) w.classList.remove('talk');
    root.classList.add('bot-open'); relayout();
    setTimeout(function () { var i = document.getElementById('bot-input'); if (i) i.focus(); }, 340);
  }
  function closeBot() {
    if (!root.classList.contains('bot-open')) return;
    root.classList.remove('bot-open'); relayout();
    var w = walker(); if (w) w.focus({ preventScroll: true });
  }
  window.kyo = { open: openBot, close: closeBot };
  document.addEventListener('click', function (e) {
    if (!e.target.closest) return;
    if (e.target.closest('#kyo-walker')) { openBot(); return; }
    if (e.target.closest('#bot-close')) closeBot();
  });
  document.addEventListener('keydown', function (e) {
    var a = document.activeElement;
    if ((e.key === 'Enter' || e.key === ' ') && a && a.id === 'kyo-walker') { e.preventDefault(); openBot(); }
    if (e.key === 'Escape' && root.classList.contains('bot-open')) closeBot();
  });
  // Al entrar, Kyo saluda unos segundos con su globo y luego solo lo muestra al pasar el mouse
  setTimeout(function () {
    var w = walker(); if (!w || root.classList.contains('bot-open')) return;
    w.classList.add('talk'); setTimeout(function () { w.classList.remove('talk'); }, 5000);
  }, 1500);
  // Desplaza el chat al último mensaje cuando llega una respuesta
  new MutationObserver(function () {
    var m = document.getElementById('bot-msgs');
    if (m && m.dataset.n !== String(m.children.length)) { m.dataset.n = m.children.length; m.scrollTop = m.scrollHeight; }
  }).observe(document.documentElement, { childList: true, subtree: true });
})();
"""


app.index_string = f"""<!DOCTYPE html>
<html lang="es">
<head>
  {{%metas%}}
  <title>{{%title%}}</title>
  {{%favicon%}}
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap" rel="stylesheet">
  {{%css%}}
  <style>{CSS}</style>
</head>
<body>
  {{%app_entry%}}
  {WALKER_HTML}
  <script>{COVER_JS}</script>
  <script>{BOT_JS}</script>
  {{%config%}}{{%scripts%}}{{%renderer%}}
</body>
</html>"""

# ---------- Barra lateral fija: título, navegación y AUTORES ------------------
NAV = [("/", "Inicio", "home"), ("/introduccion", "Introducción", "info"),
       ("/problema", "Problema y Objetivos", "target"), ("/marco", "Marco Teórico", "book"),
       ("/univariado", "EDA Univariado", "bars"), ("/multivariado", "EDA Multivariado", "scatter"),
       ("/modelos", "Modelos", "layers"), ("/predecir", "Predecir", "gauge"),
       ("/enlaces", "Enlaces", "link"), ("/equipo", "Equipo", "users")]

sidebar = html.Div([
    dcc.Link([html.Div([icon("card"), "Proyecto EDA"], className="brand-tag"),
              html.Div(PROJECT_TITLE, className="brand-title"),
              html.P(PROJECT_SUBTITLE, className="brand-sub")], href="/", className="brand",
             title="Ir a la portada"),
    html.Div([dcc.Link([icon(ic), html.Span(lbl)], href=path, id=f"nav-{i}")
              for i, (path, lbl, ic) in enumerate(NAV)], className="nav"),
    # === CAMBIAR AQUÍ NOMBRES Y CORREOS (se editan en AUTHORS, al inicio del archivo) ===
    html.Div([
        html.H4("Autores"),
        *[html.Div([html.Div(a["name"], className="nm"), html.Div(a["email"], className="em")], className="author")
          for a in AUTHORS],
        html.Div(INSTITUTION, className="inst"),
    ], className="authors"),
], className="sidebar")

# === CAMBIAR AQUÍ NOMBRES Y CORREOS (pie de página; se alimenta de AUTHORS) ===
footer = html.Div([
    html.Div([
        html.Div([html.B("Autores: "), " · ".join(f"{a['name']} ({a['email']})" for a in AUTHORS)]),
        html.Div(f"{INSTITUTION} · Datos: UCI Machine Learning Repository (Yeh & Lien, 2009)"),
    ]),
    html.Div([html.A([icon(L["icon"]), L["title"]], href=L["url"], target="_blank", rel="noopener noreferrer")
              for L in LINKS], className="footer-links"),
], className="footer")


# ---------- Tema claro / oscuro para las figuras Plotly --------------------------
DARK_CARD, DARK_PLOT = "#1B2338", "#151C2E"
DARK_MAP = {          # tonos oscuros de la paleta -> versiones claras legibles sobre fondo oscuro
    DEEP_NAVY: "#AEB8D6",
    NAVY: "#8E9CC6",
    MID_BLUE: "#7F8EB9",
    BROWN: "#B39A63",
    GOLD_MID: "#BFA25A",
    GOLD_DARK: "#9C8250",
    DEEP_RGBA: "rgba(174,184,214,",
}


def themed(fig, dark, mono=False):
    """Adapta la figura al modo oscuro.

    mono=True (gráficas de un solo color del EDA Univariado): el azul profundo pasa a
    dorado pálido y la línea de la mediana (dorado cálido) pasa a crema para que contraste.
    """
    if not dark or fig is None:
        return fig
    mp = dict(DARK_MAP)
    if mono:
        mp[DEEP_NAVY] = PALE_GOLD
        mp[DEEP_RGBA] = _rgba_prefix(PALE_GOLD)
        mp[WARM_GOLD] = CREAM
    s = fig.to_json()
    for a, b in mp.items():
        s = s.replace(a, b)
    f = pio.from_json(s)
    f.update_layout(
        paper_bgcolor=DARK_CARD, plot_bgcolor=DARK_PLOT,
        font=dict(color=CREAM), title_font=dict(color=CREAM),
        hoverlabel=dict(bgcolor=CREAM, font_color=DEEP_NAVY),
        modebar=dict(bgcolor="rgba(0,0,0,0)", color="#B9C3DE", activecolor=PALE_GOLD))
    ax = dict(gridcolor="rgba(249,240,222,0.12)", zerolinecolor="rgba(249,240,222,0.25)",
              linecolor="rgba(249,240,222,0.30)")
    f.update_xaxes(**ax)
    f.update_yaxes(**ax)
    return f


def graph_cb(*args, mono=False):
    """Como @app.callback, pero añade el tema como entrada y adapta la primera salida (la figura).

    mono puede ser True/False o una función (con los mismos argumentos que el callback)
    que devuelva True cuando la figura sea de un solo color.
    """
    def deco(fn):
        @app.callback(*args, Input("theme", "data"))
        def wrapper(*vals):
            *vals, theme = vals
            res = fn(*vals)
            dark = theme == "dark"
            m = mono(*vals) if callable(mono) else mono
            if isinstance(res, tuple):
                return (themed(res[0], dark, m),) + res[1:]
            return themed(res, dark, m)
        return wrapper
    return deco


# ---------- Layout final: tema, barra lateral plegable, botones -------------------
topbar = html.Div([
    html.Div([
        html.Button(icon("panel"), id="sb-btn", className="icon-btn", title="Mostrar u ocultar el menú lateral",
                    **{"aria-label": "Mostrar u ocultar el menú lateral"}),
        html.Div([html.Div(PROJECT_TITLE, className="t1"), html.Div(COURSE, className="t2")]),
    ], className="tb-left"),
    html.Div([
        html.Div([icon("chip"), f"{len(df):,} clientes · {GLOBAL_RATE:.1%} default"], className="badge"),
        html.A(icon("notebook"), href=NOTEBOOK_URL, target="_blank", rel="noopener noreferrer",
               className="icon-btn", title="Abrir el notebook del EDA", **{"aria-label": "Abrir el notebook del EDA"}),
        html.A(icon("github"), href=REPO_PROJECT, target="_blank", rel="noopener noreferrer",
               className="icon-btn", title="Abrir el repositorio del proyecto",
               **{"aria-label": "Abrir el repositorio del proyecto"}),
        html.Button([icon("sun", "t-sun"), icon("moon", "t-moon")], id="theme-btn", n_clicks=0,
                    className="theme-toggle", title="Cambiar a modo oscuro",
                    **{"aria-label": "Cambiar entre modo claro y oscuro"}),
    ], className="tb-right"),
], className="topbar")

# ---------- Asistente Kyo: entrenamiento y panel ------------------------------------
# Se entrena una sola vez al arrancar (menos de un segundo) con el contenido de este archivo.
BOT = Asistente(*construir_conocimiento(sys.modules[__name__]))
print(f"[kyo] entrenado con {BOT.n_ejemplos} preguntas de {len(BOT.I)} temas del tablero")
BOT_AV = {m: mascota_uri(m) for m in ("happy", "thinking", "explaining", "proud", "alert")}


def bot_panel():
    return html.Aside([
        html.Div([
            html.Img(src=BOT_AV["happy"], className="bot-av", alt=""),
            html.Div([html.Div(["Kyo", html.Span(className="bot-dot", title="En línea")], className="bot-name"),
                      html.Div("Asistente del tablero · entrenado con su contenido", className="bot-sub")],
                     className="bot-id"),
            html.Button(icon("reset"), id="bot-reset", n_clicks=0, className="icon-btn", type="button",
                        title="Nueva conversación", **{"aria-label": "Nueva conversación"}),
            html.Button(icon("close"), id="bot-close", n_clicks=0, className="icon-btn", type="button",
                        title="Cerrar (Esc)", **{"aria-label": "Cerrar el asistente"}),
        ], className="bot-head"),
        html.Div(id="bot-where", className="bot-where"),
        html.Div(id="bot-msgs", className="bot-msgs", role="log", **{"aria-live": "polite"}),
        html.Div(id="bot-sugs", className="bot-sugs"),
        html.Div([
            dcc.Input(id="bot-input", type="text", n_submit=0, autoComplete="off", className="bot-input",
                      placeholder="Pregúntame por cualquier parte del tablero…", maxLength=300),
            html.Button(icon("send"), id="bot-send", n_clicks=0, className="bot-send", type="button",
                        title="Enviar", **{"aria-label": "Enviar pregunta"}),
        ], className="bot-form"),
        html.P("Respondo con lo que aprendí del contenido de este tablero; no uso servicios externos.",
               className="bot-foot"),
    ], id="bot-panel", className="bot-panel", **{"aria-label": "Asistente Kyo"})


def _bot_path(path):
    return (path or "/").rstrip("/") or "/"


def _bot_msg(m, path):
    if m["r"] == "u":
        return html.Div(html.Div(m["t"], className="bm-bubble"), className="bm user")
    body = [dcc.Markdown(m["t"], link_target="_blank")]
    if m.get("p") and m["p"] != path:
        body.append(dcc.Link([f"Ir a {m.get('n') or 'la sección'}", icon("arrow")], href=m["p"], className="bot-go"))
    return html.Div([html.Img(src=BOT_AV.get(m.get("m"), BOT_AV["happy"]), className="bm-av", alt=""),
                     html.Div(body, className="bm-bubble")], className="bm bot")


app.layout = html.Div([
    dcc.Location(id="url"),
    dcc.Store(id="theme", storage_type="local", data="light"),
    # interruptor de tema de la portada (solo visible en la portada, ver CSS)
    html.Button([icon("sun", "t-sun"), icon("moon", "t-moon")], id="theme-btn2", n_clicks=0,
                className="theme-toggle cover-toggle", title="Cambiar entre modo claro y oscuro",
                **{"aria-label": "Cambiar entre modo claro y oscuro"}),
    sidebar,
    html.Div([topbar, html.Div(id="page", className="content"), footer], className="main"),
    dcc.Store(id="bot-store", storage_type="session", data=[]),
    bot_panel(),
], id="shell", className="app")


@app.callback(Output("theme", "data"), Input("theme-btn", "n_clicks"), Input("theme-btn2", "n_clicks"),
              State("theme", "data"), prevent_initial_call=True)
def toggle_theme(n, n2, t):
    return "light" if t == "dark" else "dark"


app.clientside_callback(
    """function(t) { t = t || 'light'; document.documentElement.setAttribute('data-theme', t);
         return t === 'dark' ? 'Cambiar a modo claro' : 'Cambiar a modo oscuro'; }""",
    Output("theme-btn", "title"), Input("theme", "data"))

# Estado de pantalla unificado: portada sin marco (/) o dash con menú plegable
app.clientside_callback(
    """function(n, p) { p = p || '/'; if (p.length > 1 && p.slice(-1) === '/') p = p.slice(0, -1);
         if (p === '/') return 'app cover';
         setTimeout(function() { window.dispatchEvent(new Event('resize')); }, 350);
         return (n || 0) % 2 === 1 ? 'app collapsed' : 'app'; }""",
    Output("shell", "className"), Input("sb-btn", "n_clicks"), Input("url", "pathname"))


@graph_cb(Output("home-graph", "figure"), mono=True)
def cb_home():
    return fig_home()


@graph_cb(Output("target-graph", "figure"), mono=True)
def cb_target():
    return fig_target()


@graph_cb(Output("rates-graph", "figure"))
def cb_rates():
    return fig_rates()


@graph_cb(Output("corr-graph", "figure"))
def cb_corr():
    return fig_corr()


# ---------- Callbacks: Modelos ------------------------------------------------
@graph_cb(Output("mdl-heat", "figure"))
def cb_models_heat():
    return fig_models_heat()


@graph_cb(Output("mdl-scatter", "figure"))
def cb_models_scatter():
    return fig_models_scatter()


@graph_cb(Output("mdl-cm", "figure"))
def cb_best_cm():
    return fig_best_cm()


# ---------- Callbacks: Predecir -----------------------------------------------
@app.callback([Output(f"pf-{c}", "value") for c in INPUT_COLS],
              [Input(f"pf-prof-{k}", "n_clicks") for k in PROFILES], prevent_initial_call=True)
def cb_profile(*_clicks):
    key = str(ctx.triggered_id or "pf-prof-tipico").replace("pf-prof-", "")
    prof = PROFILES.get(key, PROFILES["tipico"])[1]
    return [prof[c] for c in INPUT_COLS]


def _pf_values(vals):
    values = dict(zip(INPUT_COLS, vals))
    missing = [pretty(c) for c, v in values.items() if v is None]
    return values, missing


@app.callback(Output("pf-gauge", "figure"), Output("pf-verdict", "children"), Output("pf-trees", "children"),
              Output("pf-history", "figure"), Output("pf-drivers", "figure"),
              *[Input(f"pf-{c}", "value") for c in INPUT_COLS], Input("theme", "data"))
def cb_predict(*vals):
    *vals, theme = vals
    dark = theme == "dark"
    values, missing = _pf_values(vals)
    if MODELO is None or missing:
        msg = html.P("Completa los campos: " + ", ".join(missing[:4]) + ("…" if len(missing) > 4 else ""),
                     className="callout") if missing else ""
        empty = style_fig(go.Figure(), 340, legend_top=False)
        return themed(fig_risk_gauge(), dark), msg, "", themed(empty, dark), themed(empty, dark)
    score = predict_risk(values)
    return (themed(fig_risk_gauge(score), dark), predict_verdict(values, score), trees_block(values),
            themed(fig_client_history(values), dark), themed(fig_drivers(values, score), dark))


@app.callback(Output("pf-whatif", "figure"), Input("pf-whatif-var", "value"),
              *[Input(f"pf-{c}", "value") for c in INPUT_COLS], Input("theme", "data"))
def cb_whatif(var, *vals):
    *vals, theme = vals
    values, missing = _pf_values(vals)
    if MODELO is None or missing:
        return themed(style_fig(go.Figure(), 360, legend_top=False), theme == "dark")
    return themed(fig_whatif(values, var or "PAY_0", predict_risk(values)), theme == "dark")


def nav_buttons(path):
    """Botones Anterior / Siguiente para recorrer el tablero en orden."""
    order = [p for p, _, _ in NAV]
    i = order.index(path) if path in order else 0
    left = right = html.Span()
    if i > 0:
        left = dcc.Link([icon("arrow", "flip"), html.Div([html.Small("Anterior"), html.B(NAV[i - 1][1])])],
                        href=order[i - 1], className="pn prev")
    if i < len(order) - 1:
        right = dcc.Link([html.Div([html.Small("Siguiente"), html.B(NAV[i + 1][1])]), icon("arrow")],
                         href=order[i + 1], className="pn next")
    return html.Div([left, right], className="pn-row")


@app.callback(Output("page", "children"), Input("url", "pathname"))
def route(path):
    path = (path or "/").rstrip("/") or "/"
    body = _route(path)
    return body if path == "/" else html.Div([body, nav_buttons(path)])


def _route(path):
    if path == "/univariado":
        return page_uni()
    if path == "/multivariado":
        return page_multi()
    if path == "/problema":
        return page_problem()
    if path == "/marco":
        return page_marco()
    if path == "/introduccion":
        return page_intro()
    if path == "/modelos":
        return page_models()
    if path == "/predecir":
        return page_predict()
    if path == "/enlaces":
        return page_links()
    if path == "/equipo":
        return page_team()
    return page_home()


@app.callback([Output(f"nav-{i}", "className") for i in range(len(NAV))], Input("url", "pathname"))
def highlight(path):
    path = (path or "/").rstrip("/") or "/"
    return ["active" if path == p else "" for p, _, _i in NAV]


# ---------- Callbacks: Univariado (gráficas de un solo color) ------------------
@graph_cb(Output("uni-graph", "figure"), Output("uni-interp", "children"),
          Input("uni-var", "value"), Input("uni-clip", "value"), mono=True)
def cb_uni(var, clip):
    return fig_uni(var, bool(clip)), interp_block(*interp_uni(var))


@graph_cb(Output("q-graph", "figure"), Output("q-interp", "children"),
          Input("q-family", "value"), Input("q-kind", "value"),
          mono=lambda family, kind: family in ("LIMIT_BAL", "AGE"))
def cb_quant(family, kind):
    return fig_quant(family, kind), interp_block(*interp_quant(family))


# ---------- Callbacks: Multivariado -------------------------------------------
@graph_cb(Output("lim-graph", "figure"), Input("lim-scale", "value"))
def cb_limit(scale):
    return fig_limit_box(scale)


@graph_cb(Output("age-graph", "figure"), Output("age-interp", "children"), Input("age-view", "value"))
def cb_age(view):
    return fig_age(view), interp_block(*interp_age(view))


@graph_cb(Output("x-graph", "figure"), Output("x-interp", "children"),
          Input("x-var", "value"), Input("y-var", "value"), Input("c-var", "value"), Input("x-clip", "value"))
def cb_cross(x, y, c, clip):
    fig, b, t = cross_fig(x, y, c, bool(clip))
    return fig, interp_block(b, t)


@graph_cb(Output("s-graph", "figure"), Output("s-interp", "children"), Input("s-vars", "value"))
def cb_splom(vars_):
    vars_ = (vars_ or [])[:6]
    if len(vars_) < 2:
        fig = go.Figure()
        fig.update_layout(title="Selecciona al menos 2 variables")
        return style_fig(fig, 380, legend_top=False), interp_block("Elige al menos dos variables numéricas.", "")
    return fig_splom(vars_), interp_block(*interp_splom(vars_))


# ---------- Callbacks: Asistente Kyo -------------------------------------------
@app.callback(Output("bot-store", "data"), Output("bot-input", "value"),
              Input("bot-send", "n_clicks"), Input("bot-input", "n_submit"),
              Input({"type": "bot-sug", "index": ALL}, "n_clicks"), Input("bot-reset", "n_clicks"),
              State("bot-input", "value"), State("url", "pathname"), State("bot-store", "data"),
              prevent_initial_call=True)
def cb_bot(_send, _enter, _sugs, _reset, text, path, hist):
    trig = ctx.triggered_id
    if trig == "bot-reset":
        return [], ""
    if isinstance(trig, dict):   # una sugerencia: su texto viaja en el id
        # (ctx.triggered pierde el valor cuando el id tiene tildes; se busca en la lista de entradas)
        clicked = any(i["id"] == trig and i.get("value") for i in ctx.inputs_list[2])
        if not clicked:          # los botones recién dibujados también disparan el callback
            return no_update, no_update
        text = trig["index"]
    text = (text or "").strip()[:300]
    if not text:
        return no_update, no_update
    hist = list(hist or [])[-38:]
    last = next((m.get("i") for m in reversed(hist) if m["r"] == "b" and m.get("i")), None)
    hist += [{"r": "u", "t": text}, {"r": "b", **BOT.responder(text, _bot_path(path), last)}]
    return hist, ""


@app.callback(Output("bot-msgs", "children"), Output("bot-sugs", "children"), Output("bot-where", "children"),
              Input("bot-store", "data"), Input("url", "pathname"))
def cb_bot_render(hist, path):
    path = _bot_path(path)
    hist = hist or []
    msgs = [BOT.bienvenida(path) | {"r": "b"}] + hist
    sugs = msgs[-1].get("s", []) if not hist else (hist[-1].get("s") or BOT.sug_de_pagina.get(path, []))
    where = [icon("info"), "Estás en ", html.B(BOT.paginas.get(path, "Inicio"))]
    return ([_bot_msg(m, path) for m in msgs],
            [html.Button(s, id={"type": "bot-sug", "index": s}, n_clicks=0, className="bot-sug", type="button")
             for s in sugs],
            where)


# =============================================================================
if __name__ == "__main__":
    app.run(debug=True, port=8050)

# Cambio de prueba 