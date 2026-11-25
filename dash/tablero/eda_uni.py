# -*- coding: utf-8 -*-
"""EDA univariado: figuras e interpretaciones de la variable objetivo y de cada variable.

Las funciones que dependen del filtro global reciben el subconjunto en `data` (por defecto, todos los clientes).
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from dash import html
from plotly.subplots import make_subplots
from scipy import stats

from tablero.config import (MONO, SERIES6, WARM_GOLD, WHITE, tx)
from tablero.datos import (BILL_COLS, DF, DISCRETE, PAYAMT_COLS, PAY_COLS, TARGET, as_cat, month, pretty)
from tablero.utilidades import (_rgba, fmt_val, nt, style_fig, tukey_outliers_pct)


def fig_target(data=DF):
    """Barras de la variable objetivo con conteo y porcentaje (un solo color)."""
    vc = data[TARGET].value_counts().sort_index()
    pr = vc / vc.sum()
    fig = go.Figure(go.Bar(
        x=["No default (0)", "Default (1)"], y=vc.values,
        marker_color=MONO,
        text=[f"{v:,}<br><b>{p:.1%}</b>" for v, p in zip(vc.values, pr.values)],
        textposition="outside",
        hovertemplate="%{x}<br>%{y:,} " + tx("clientes", "clients") + "<extra></extra>"))
    fig.update_layout(title=tx("Variable objetivo: default payment next month",
                               "Target variable: default payment next month"),
                      yaxis_title=tx("Número de clientes", "Number of clients"), showlegend=False)
    fig.update_yaxes(range=[0, vc.max() * 1.18])
    return style_fig(fig, 478, legend_top=False)


def target_strip():
    """Barra apilada 100 % con la proporción de clases y la razón de desbalance."""
    vc = DF[TARGET].value_counts()
    p0, p1 = vc[0] / len(DF), vc[1] / len(DF)
    return html.Div([
        html.Div([html.Span(tx("Proporción de clases", "Class proportion"), className="ts-lbl"),
                  html.Span([tx("Razón ", "Ratio "), html.B(f"{vc[0] / vc[1]:.1f} : 1")], className="ts-ratio")],
                 className="ts-head"),
        html.Div([html.Div(f"No default {p0:.1%}", className="ts-seg ts-0", style={"width": f"{p0:.2%}"}),
                  html.Div(f"Default {p1:.1%}", className="ts-seg ts-1", style={"width": f"{p1:.2%}"})],
                 className="ts-bar"),
    ], className="target-strip")


def interp_target(data=DF):
    vc = data[TARGET].value_counts()
    p1, p0 = vc[1] / len(data), vc[0] / len(data)
    ratio = vc[0] / vc[1]
    basic = tx(
        f"Aproximadamente {p1 * 100:.0f} de cada 100 clientes ({vc[1]:,} personas) no pagó "
        f"la tarjeta al mes siguiente. El resto ({p0:.1%}) sí cumplió. Hay "
        f"muchos más clientes cumplidos que incumplidos, lo que hay que tener en cuenta al construir modelos.",
        f"About {p1 * 100:.0f} out of every 100 clients ({vc[1]:,} people) did not pay their card the "
        f"following month. The rest ({p0:.1%}) did pay. There are many more paying clients than defaulting "
        f"ones, which must be taken into account when building models.")
    tech = tx(
        f"Desbalance de clases: {p0:.1%} (clase 0) vs. {p1:.1%} (clase 1), razón ≈ {ratio:.1f}:1. "
        "Un clasificador sin ajustes tenderá a favorecer la clase mayoritaria; se recomienda "
        "class_weight='balanced', remuestreo (SMOTE/ADASYN) o umbrales ajustados, y evaluar con "
        "AUC-ROC, F1 y recall de la clase 1 en lugar de accuracy.",
        f"Class imbalance: {p0:.1%} (class 0) vs. {p1:.1%} (class 1), ratio ≈ {ratio:.1f}:1. "
        "An unadjusted classifier will tend to favor the majority class; class_weight='balanced', "
        "resampling (SMOTE/ADASYN) or adjusted thresholds are recommended, and evaluation should use "
        "ROC-AUC, F1 and class-1 recall instead of accuracy.")
    return basic, tech


def fig_uni(col, data=DF):
    """Distribución univariada de cualquier variable (numérica o categórica), un solo color."""
    if col in DISCRETE:
        cats = as_cat(col, data=data)
        vc = pd.Series(cats).value_counts().reindex(list(cats.categories))
        pr = vc / vc.sum()
        fig = go.Figure(go.Bar(
            x=list(vc.index), y=vc.values, marker_color=MONO,
            text=[f"{p:.1%}" for p in pr.values], textposition="outside",
            hovertemplate=f"{col}: %{{x}}<br>{tx('Clientes', 'Clients')}: %{{y:,}}<extra></extra>"))
        fig.update_layout(title=tx(f"Frecuencia de {pretty(col)}", f"Frequency of {pretty(col)}"),
                          xaxis_title=col, yaxis_title=tx("Número de clientes", "Number of clients"),
                          showlegend=False)
        fig.update_xaxes(type="category", categoryorder="array", categoryarray=list(vc.index))
        fig.update_yaxes(range=[0, vc.max() * 1.15])
        return style_fig(fig, 470, legend_top=False)

    s = data[col]
    q1, q3 = s.quantile([0.25, 0.75])
    top = max(s.quantile(0.99), min(q3 + 1.5 * (q3 - q1), s.max()))
    view = s[s <= top]
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                        row_heights=[0.74, 0.26], vertical_spacing=0.03)
    fig.add_trace(go.Histogram(x=view, nbinsx=60, marker_color=MONO,
                               marker_line_color=WHITE, marker_line_width=0.4,
                               name=tx("Frecuencia", "Frequency"), showlegend=False), row=1, col=1)
    fig.add_trace(go.Box(x=s, name="", marker_color=MONO, boxpoints="outliers", marker_size=3,
                         marker_opacity=0.35, boxmean=True, showlegend=False), row=2, col=1)
    lo = s.min() - (top - s.min()) * 0.02
    fig.update_xaxes(range=[lo, top * 1.02 if top > 0 else top], row=2, col=1)
    fig.add_vline(x=s.median(), line_dash="dash", line_color=WARM_GOLD, row=1, col=1,
                  annotation_text=tx("mediana", "median"), annotation_font_color=WARM_GOLD)
    n_out = int((s > top).sum())
    suf = ("<br><span style='font-size:12px;font-weight:400'>"
           + tx(f"{n_out:,} valores extremos quedan fuera de la vista (se ven como atípicos en el boxplot)",
                f"{n_out:,} extreme values fall outside the view (shown as outliers in the boxplot)")
           + "</span>" if n_out else "")
    fig.update_layout(title=tx(f"Distribución de {pretty(col)}{suf}", f"Distribution of {pretty(col)}{suf}"))
    fig.update_yaxes(title_text=tx("Frecuencia", "Frequency"), row=1, col=1)
    fig.update_xaxes(title_text=pretty(col), row=2, col=1)
    return style_fig(fig, 520, legend_top=False)


def interp_uni(col, data=DF):
    """Interpretación básica y técnica para la variable elegida."""
    n = len(data)
    # ---------- variables discretas ----------
    if col in DISCRETE:
        cats = as_cat(col, data=data)
        vc = pd.Series(cats).value_counts().reindex(list(cats.categories))
        pr = vc / vc.sum()
        top = pr.idxmax()
        if col in PAY_COLS:
            al_dia = data[col].le(0).mean()
            atraso = data[col].ge(1).mean()
            mes = month(int(col[-1]) if col != "PAY_0" else 1)
            basic = tx(
                f"En {mes}, {al_dia:.0%} de los clientes estaba al día "
                f"(valores 0 o menores) y {atraso:.0%} tenía al menos un mes de atraso. "
                f"El valor más común es {top} ({pr[top]:.0%}).",
                f"In {mes}, {al_dia:.0%} of clients were up to date "
                f"(values of 0 or less) and {atraso:.0%} were at least one month late. "
                f"The most common value is {top} ({pr[top]:.0%}).")
            tech = tx(
                f"Variable ordinal con {len(vc)} niveles; moda = {top} ({pr[top]:.1%}). "
                f"Los valores −2, −1 y 0 concentran {data[col].le(0).mean():.1%} de los casos; "
                f"atraso ≥1 mes: {atraso:.1%}. La definición exacta de −2/−1/0 no está "
                "estandarizada en la fuente: se conservan sin recodificar y no se sobre-interpreta "
                "la frontera entre ellos. Se recomienda tratarla como ordinal/categórica (dummies) "
                "pues el efecto de pasar de 'al día' a 1 mes de atraso no es lineal.",
                f"Ordinal variable with {len(vc)} levels; mode = {top} ({pr[top]:.1%}). "
                f"Values −2, −1 and 0 account for {data[col].le(0).mean():.1%} of cases; "
                f"delay ≥1 month: {atraso:.1%}. The exact definition of −2/−1/0 is not "
                "standardized in the source: they are kept without recoding and the boundary between "
                "them is not over-interpreted. Treating it as ordinal/categorical (dummies) is "
                "recommended, since going from 'up to date' to 1 month late is not a linear effect.")
        elif col == TARGET:
            return interp_target(data=data)
        else:
            parts = ", ".join(f"{k} {v:.1%}" for k, v in pr.items())
            basic = tx(f"La categoría más frecuente es «{top}» con {pr[top]:.0%} de los clientes. "
                       f"Distribución completa: {parts}.",
                       f"The most frequent category is “{top}” with {pr[top]:.0%} of clients. "
                       f"Full distribution: {parts}.")
            tech = tx(f"Variable categórica nominal de {len(vc)} niveles; moda «{top}» ({pr[top]:.1%}). "
                      f"Frecuencias: {parts}. Las categorías no documentadas del archivo original "
                      "se reagruparon en «Otros» (EDUCATION 0/5/6 → 4; MARRIAGE 0 → 3).",
                      f"Nominal categorical variable with {len(vc)} levels; mode “{top}” ({pr[top]:.1%}). "
                      f"Frequencies: {parts}. Undocumented categories in the original file were "
                      "grouped into “Others” (EDUCATION 0/5/6 → 4; MARRIAGE 0 → 3).")
        return basic, tech

    # ---------- variables numéricas ----------
    s = data[col]
    q1, q3 = s.quantile([0.25, 0.75])
    iqr = q3 - q1
    sk, ku = stats.skew(s), stats.kurtosis(s)
    out = tukey_outliers_pct(s)
    f = lambda v: fmt_val(col, v)
    if sk > 1:
        shape = tx(f"La mayoría de clientes se ubica entre {f(q1)} y {f(q3)}, pero unos pocos tienen valores "
                   f"mucho más altos (hasta {f(s.max())}). Por eso el promedio ({f(s.mean())}) queda por "
                   f"encima de lo típico (mediana {f(s.median())}).",
                   f"Most clients fall between {f(q1)} and {f(q3)}, but a few have much higher values "
                   f"(up to {f(s.max())}). That is why the mean ({f(s.mean())}) sits above the typical value "
                   f"(median {f(s.median())}).")
    elif sk > 0.5:
        shape = tx(f"La mitad de los clientes tiene {f(s.median())} o menos; la distribución se inclina "
                   f"ligeramente hacia valores altos (promedio {f(s.mean())}).",
                   f"Half of the clients have {f(s.median())} or less; the distribution leans slightly "
                   f"toward high values (mean {f(s.mean())}).")
    else:
        shape = tx(f"Los valores se reparten de forma bastante equilibrada alrededor de {f(s.median())} "
                   f"(promedio {f(s.mean())}).",
                   f"Values are fairly evenly spread around {f(s.median())} (mean {f(s.mean())}).")
    extra = ""
    if col.startswith("BILL_AMT") and (s < 0).any():
        extra = tx(f" Un {(s < 0).mean():.1%} de los clientes tiene saldo a favor (monto negativo).",
                   f" {(s < 0).mean():.1%} of clients have a credit balance (negative amount).")
    if col.startswith("PAY_AMT"):
        extra = tx(f" Un {(s == 0).mean():.1%} de los clientes no hizo ningún pago ese mes.",
                   f" {(s == 0).mean():.1%} of clients made no payment that month.")
    basic = shape + extra
    rec = (tx("Su asimetría extrema justifica una transformación logarítmica (con signo) antes de modelar.",
              "Its extreme skewness justifies a (signed) log transformation before modeling.")
           if abs(sk) > 2 else tx("No requiere transformaciones drásticas por forma.",
                                  "Its shape does not require drastic transformations."))
    tech = tx(f"n = {n:,}; media = {f(s.mean())}; mediana = {f(s.median())}; σ = {f(s.std())}; "
              f"IQR = {f(iqr)}; asimetría = {sk:.2f}; curtosis = {ku:.2f}; outliers de Tukey = {out:.1f}%. "
              f"{rec}",
              f"n = {n:,}; mean = {f(s.mean())}; median = {f(s.median())}; σ = {f(s.std())}; "
              f"IQR = {f(iqr)}; skewness = {sk:.2f}; kurtosis = {ku:.2f}; Tukey outliers = {out:.1f}%. "
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


def fig_quant(family, kind, data=DF):
    """LIMIT_BAL y AGE: un solo color. BILL_AMT y PAY_AMT: un color por mes (con leyenda)."""
    cols = FAMILIES[family]
    allv = data[cols].values.ravel()
    lo, hi = np.percentile(allv, 1), np.percentile(allv, 99)   # vista P1 a P99
    fig = go.Figure()
    for i, c in enumerate(cols):
        color = SERIES6[i % 6] if len(cols) > 1 else MONO
        name = c
        if kind == "hist":
            v = data[c][(data[c] >= lo) & (data[c] <= hi)]
            fig.add_trace(go.Histogram(x=v, nbinsx=50, name=name, marker_color=color,
                                       opacity=0.65 if len(cols) > 1 else 0.95,
                                       showlegend=len(cols) > 1))
        elif kind == "box":
            fig.add_trace(go.Box(y=data[c], name=name, marker_color=color,
                                 boxpoints=False, boxmean=True, showlegend=len(cols) > 1))
        else:  # densidad
            g, d = kde_curve(data[c], lo, hi)
            fig.add_trace(go.Scatter(x=g, y=d, name=name, mode="lines",
                                     line=dict(color=color, width=2.5),
                                     fill="tozeroy",
                                     fillcolor=_rgba(color, 0.18),
                                     showlegend=len(cols) > 1))
    if kind == "hist":
        fig.update_layout(barmode="overlay", xaxis_title=family, yaxis_title=tx("Frecuencia", "Frequency"))
        ttl = tx("Histograma", "Histogram")
    elif kind == "box":
        fig.update_layout(yaxis_title=family)
        ttl = "Boxplot"
        if family in ("BILL_AMT", "PAY_AMT"):
            fig.update_yaxes(range=[min(0, lo * 1.1), hi * 1.1])
    else:
        fig.update_layout(xaxis_title=family, yaxis_title=tx("Densidad", "Density"))
        ttl = tx("Densidad (KDE)", "Density (KDE)")
    sub = "" if kind == "box" and family not in ("BILL_AMT", "PAY_AMT") else tx(" · vista P1 a P99", " · P1 to P99 view")
    fig.update_layout(title=tx(f"{ttl} de {family}{sub}", f"{ttl} of {family}{sub}"))
    return style_fig(fig, 480, legend_top=len(cols) > 1)


def interp_quant(family, data=DF):
    if family == "LIMIT_BAL":
        return interp_uni("LIMIT_BAL", data=data)
    if family == "AGE":
        return interp_uni("AGE", data=data)
    cols = FAMILIES[family]
    med = data[cols].median()
    sk = data[cols].apply(stats.skew)
    if family == "BILL_AMT":
        neg = data[cols].lt(0).any(axis=1).mean()
        o_lo = min(tukey_outliers_pct(data[c]) for c in cols)
        o_hi = max(tukey_outliers_pct(data[c]) for c in cols)
        basic = tx(f"Los seis meses de facturación se parecen mucho entre sí: la mediana ronda "
                   f"{nt(med.min())} a {nt(med.max())} y casi todos los meses tienen unos pocos clientes con "
                   f"saldos muy altos. Además, {neg:.1%} de los clientes tuvo saldo a favor (negativo) en algún mes.",
                   f"The six billing months look very much alike: the median is around "
                   f"{nt(med.min())} to {nt(med.max())} and almost every month has a few clients with very high "
                   f"balances. Also, {neg:.1%} of clients had a credit (negative) balance in some month.")
        tech = tx(f"Asimetría entre {sk.min():.2f} y {sk.max():.2f}; outliers de Tukey entre "
                  f"{o_lo:.1f}% y {o_hi:.1f}%. Distribuciones casi idénticas mes "
                  "a mes (alta autocorrelación del saldo). Los montos negativos son económicamente válidos "
                  "(pago en exceso) y no se eliminan. Esta redundancia anticipa multicolinealidad severa "
                  "(ver VIF en el notebook / pestaña Multivariado).",
                  f"Skewness between {sk.min():.2f} and {sk.max():.2f}; Tukey outliers between "
                  f"{o_lo:.1f}% and {o_hi:.1f}%. Nearly identical distributions month after month (high "
                  "autocorrelation of the balance). Negative amounts are economically valid (overpayment) and "
                  "are kept. This redundancy anticipates severe multicollinearity (see VIF in the notebook / "
                  "Multivariate page).")
    else:
        zeros = data[cols].eq(0).mean()
        basic = tx(f"Los pagos son pequeños frente a las facturas: la mediana mensual va de "
                   f"{nt(med.min())} a {nt(med.max())}. Entre {zeros.min():.0%} y {zeros.max():.0%} "
                   "de los clientes no pagó nada en cada mes; unos pocos hacen pagos enormes.",
                   f"Payments are small compared with bills: the monthly median ranges from "
                   f"{nt(med.min())} to {nt(med.max())}. Between {zeros.min():.0%} and {zeros.max():.0%} "
                   "of clients paid nothing in each month; a few make huge payments.")
        tech = tx(f"Asimetría entre {sk.min():.1f} y {sk.max():.1f} (hasta ≈ {sk.max():.0f}), curtosis muy "
                  f"alta y cola derecha extrema (máx. {nt(data[cols].max().max())}). La masa en cero "
                  "(sin pago) y los valores extremos justifican transformación log con signo y "
                  "métodos robustos (medianas, Mann-Whitney) antes de comparar grupos.",
                  f"Skewness between {sk.min():.1f} and {sk.max():.1f} (up to ≈ {sk.max():.0f}), very high "
                  f"kurtosis and an extreme right tail (max. {nt(data[cols].max().max())}). The mass at zero "
                  "(no payment) and the extreme values justify a signed log transformation and robust "
                  "methods (medians, Mann-Whitney) before comparing groups.")
    return basic, tech
