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
     5. Componentes de interfaz (tarjetas, KPIs, interpretaciones)
     6. Páginas (Portada, Introducción, Problema, Marco, Univariado, Multivariado, Enlaces)
     7. Aplicación, CSS, navegación y callbacks
===============================================================================
"""

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
from dash import Dash, Input, Output, State, dcc, html

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
    # --- nuevos: detalles de tarjeta de crédito ---
    "card": '<rect x="2" y="5" width="20" height="14" rx="2.5"/><path d="M2 10h20M6 15h4"/>',
    "chip": '<rect x="4" y="5" width="16" height="14" rx="3"/><path d="M4 10h16M4 14h16M10 5v14M14 5v14"/>',
    "contactless": '<path d="M8.5 8.5a5 5 0 0 1 0 7M12 6a9 9 0 0 1 0 12M15.5 3.5a13 13 0 0 1 0 17"/>',
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
              "EDA Univariado": "bars", "EDA Multivariado": "scatter", "Enlaces": "link"}


# =============================================================================
# 5. COMPONENTES DE INTERFAZ
# =============================================================================
def card(title, children, subtitle=None, cls=""):
    head = [html.H3(title, className="card-title")]
    if subtitle:
        head.append(html.P(subtitle, className="card-sub"))
    return html.Div(head + (children if isinstance(children, list) else [children]),
                    className=f"card {cls}".strip())


def kpi(label, value, note="", ico=None):
    return html.Div([html.Div([icon(ico) if ico else None, html.Div(label, className="kpi-label")],
                              className="kpi-head"),
                     html.Div(value, className="kpi-value"),
                     html.Div(note, className="kpi-note")], className="kpi")


def interp_block(basic, tech):
    """Bloques desplegables: Interpretación Básica + Técnica."""
    return html.Div([
        html.Details([html.Summary("Interpretación básica"), html.P(basic)],
                     open=True, className="interp basic"),
        html.Details([html.Summary("Interpretación técnica"), html.P(tech)],
                     open=False, className="interp tech"),
    ], className="interp-wrap")


def control(label, comp):
    return html.Div([html.Label(label, className="ctl-label"), comp], className="control")


def page_title(title, sub):
    ic = PAGE_ICONS.get(title)
    return html.Div([html.H2([icon(ic, "pt-ico"), title] if ic else title), html.P(sub)],
                    className="page-title")


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
                html.P("El análisis se organiza en tres capas: fundamentos (problema, objetivos y marco teórico), "
                       "exploración univariada y exploración multivariada. Cada gráfico trae una interpretación "
                       "básica (lenguaje cotidiano) y una técnica (estadísticos y recomendaciones de modelado)."),
            ], cls="span-2"),
            card("Fuente y alcance", [
                html.P("Yeh, I-C. & Lien, C. (2009). The comparisons of data mining techniques for the predictive "
                       "accuracy of probability of default of credit card clients. Expert Systems with Applications, "
                       "36(2), 2473–2480. Datos: UCI Machine Learning Repository."),
                html.P("Cifras monetarias en dólares taiwaneses (NT$)."),
                html.P("Alcance: descriptivo y exploratorio. No se estima causalidad ni se entrena un modelo predictivo.",
                       className="muted"),
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
                "No se construye ni evalúa un modelo predictivo; solo se derivan lineamientos para hacerlo.",
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
    F = lambda t: html.Div(t, className="formula")
    return html.Div([
        page_title("Marco Teórico", "Conceptos, métodos estadísticos y variables que sustentan el análisis"),
        html.Div([
            card("1. Riesgo de crédito y default", [
                html.P("El riesgo de crédito es la posibilidad de que una entidad sufra pérdidas porque un deudor "
                       "no cumple, total o parcialmente, sus obligaciones. En la regulación bancaria (Basilea II) la "
                       "pérdida esperada se descompone así:"),
                F("EL = PD × LGD × EAD"),
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
                F("Atípico (Tukey): x < Q1 − 1.5·IQR  ó  x > Q3 + 1.5·IQR,  con IQR = Q3 − Q1"),
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
                F("Spearman: ρ = Pearson( rango(X), rango(Y) )"),
                html.P("Spearman (1904) mide asociación monótona usando los rangos de los datos. No exige linealidad "
                       "ni normalidad y resiste los valores extremos. Se eligió sobre Pearson porque los montos "
                       "(BILL_AMT, PAY_AMT) son muy asimétricos y con colas largas, las variables PAY_x son ordinales "
                       "y la variable objetivo es binaria."),
                F("VIF_j = 1 / (1 − R²_j)"),
                html.P("Hay multicolinealidad cuando las predictoras son casi redundantes: se inflan las varianzas de "
                       "los coeficientes. Un VIF > 10 (algunos autores usan > 5) es señal de alerta."),
            ]),
            card("7. Asociación entre variables categóricas", [
                html.P("La prueba χ² de independencia contrasta si dos variables categóricas están asociadas. Su "
                       "tamaño de efecto se mide con la V de Cramér, que va de 0 a 1:"),
                F("V = √( χ² / ( n · min(r − 1, c − 1) ) )"),
                html.P("Como regla orientativa, V < 0.1 es un efecto pequeño y V ≈ 0.3 uno moderado."),
            ]),
            card("8. Comparación de grupos y tamaño del efecto", [
                _ul(["Mann–Whitney U: compara dos grupos sin suponer normalidad.",
                     "Kruskal–Wallis H: extiende la comparación a tres o más grupos.",
                     "t de Welch: compara medias con varianzas distintas."]),
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
                html.P("Este tablero no repite ese modelado: se concentra en la etapa previa, entender los datos."),
            ]),
            card("Referencias", html.Ul([html.Li(r) for r in refs], className="refs")),
        ], className="grid g2"),
        card("Diccionario de variables", _tbl(["Variable", "Tipo", "Descripción"],
                                              [(html.Code(v), t, d) for v, t, d in var_table]),
             subtitle="Variables explicativas y variable objetivo (default_payment_next_month)"),
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


# =============================================================================
# 7. APLICACIÓN, CSS, NAVEGACIÓN Y CALLBACKS
# =============================================================================
app = Dash(__name__, suppress_callback_exceptions=True, title="EDA · Riesgo Crediticio")
server = app.server   # <- para despliegue (gunicorn app:server)

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
.page-title p { margin:6px 0 22px; color:var(--muted); }
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
.interp-wrap { margin-top:10px; display:grid; gap:10px; }
.interp { border-radius:8px; padding:10px 14px; }
.interp summary { cursor:pointer; font-weight:700; font-size:13.5px; }
.interp p { margin:8px 0 2px !important; font-size:14px; }
.interp.basic { background:var(--note-bg); border-left:3px solid var(--note-line); }
.interp.tech { background:var(--tech-bg); border-left:3px solid var(--tech-line); }

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
"""
CSS += NEW_CSS
CSS += _icon_css()


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
  <script>{COVER_JS}</script>
  {{%config%}}{{%scripts%}}{{%renderer%}}
</body>
</html>"""

# ---------- Barra lateral fija: título, navegación y AUTORES ------------------
NAV = [("/", "Inicio", "home"), ("/introduccion", "Introducción", "info"),
       ("/problema", "Problema y Objetivos", "target"), ("/marco", "Marco Teórico", "book"),
       ("/univariado", "EDA Univariado", "bars"), ("/multivariado", "EDA Multivariado", "scatter"),
       ("/enlaces", "Enlaces", "link")]

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

app.layout = html.Div([
    dcc.Location(id="url"),
    dcc.Store(id="theme", storage_type="local", data="light"),
    # interruptor de tema de la portada (solo visible en la portada, ver CSS)
    html.Button([icon("sun", "t-sun"), icon("moon", "t-moon")], id="theme-btn2", n_clicks=0,
                className="theme-toggle cover-toggle", title="Cambiar entre modo claro y oscuro",
                **{"aria-label": "Cambiar entre modo claro y oscuro"}),
    sidebar,
    html.Div([topbar, html.Div(id="page", className="content"), footer], className="main"),
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
    if path == "/enlaces":
        return page_links()
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


# =============================================================================
if __name__ == "__main__":
    app.run(debug=True, port=8050)