# -*- coding: utf-8 -*-
"""Componentes de interfaz compartidos: tarjetas, KPIs, interpretaciones, controles, tablas y el
filtro global del EDA.
"""

from dash import dcc, html

from tablero.config import L, tx
from tablero.datos import (BILL_COLS, PAYAMT_COLS, PAY_COLS, TARGET, pretty)
from tablero.iconos import PAGE_ICONS, icon, zoom_btn
from tablero.pipeline import pipeline_btn
from tablero.prediccion import SEX_OTHER


def card(title, children, subtitle=None, cls=""):
    head = [zoom_btn(), html.H3(title, className="card-title")]   # solo el título (subtitle se ignora a propósito)
    return html.Div(head + (children if isinstance(children, list) else [children]),
                    className=f"card {cls}".strip())


def kpi(label, value, note="", ico=None):
    return html.Div([zoom_btn(),
                     html.Div([icon(ico) if ico else None, html.Div(label, className="kpi-label")],
                              className="kpi-head"),
                     html.Div(value, className="kpi-value"),
                     html.Div(note, className="kpi-note")], className="kpi")


def interp_block(basic, tech):
    """Un solo botón desplegable (cerrado) con la interpretación básica y la técnica."""
    return html.Details([
        html.Summary([icon("info"), tx("Ver interpretación", "Show interpretation"), icon("chevron", "interp-chev")],
                     className="interp-btn"),
        html.Div([html.Div([html.B(tx("Básica", "Basic")), html.P(basic)], className="interp basic"),
                  html.Div([html.B(tx("Técnica", "Technical")), html.P(tech)], className="interp tech")],
                 className="interp-body"),
    ], className="interp-wrap")


def control(label, comp, ico=None):
    lbl = html.Label([icon(ico), label] if ico else label, className="ctl-label" + (" ctl-label-ico" if ico else ""))
    return html.Div([lbl, comp], className="control")


def ico_opts(tiles):
    """Opciones de un Checklist con el ícono de cada categoría delante del texto."""
    return [{"label": html.Span([icon(ic), L(txt)], className="opt-ico"), "value": v} for v, txt, ic in tiles]


def page_title(title, sub, stage=None):
    """Título de la página; con `stage` (etapa del pipeline) agrega el botón «Pipeline» al lado."""
    ic = PAGE_ICONS.get(title)
    h2 = html.H2([icon(ic, "pt-ico"), title] if ic else title)
    if stage:
        return html.Div([h2, pipeline_btn(stage)], className="page-title pt-row")
    return html.Div(h2, className="page-title")


def var_options(cols):
    return [{"label": pretty(c), "value": c} for c in cols]


ALL_VARS = ["LIMIT_BAL", "SEX", "EDUCATION", "MARRIAGE", "AGE"] + PAY_COLS + BILL_COLS + PAYAMT_COLS + [TARGET]


def eda_filter_card():
    """Filtros globales del EDA: actualizan todos los gráficos de la página (y se conservan entre páginas)."""
    k = tx("mil", "k")
    controles = [
        html.Div([
            control(tx("Sexo", "Sex"), ico="gender", comp=dcc.Checklist(
                id="ef-sex", value=[1, 2], inline=True, className="radio",
                options=ico_opts([t for t in SEX_TILES if t[0] in (1, 2)]), **KEEP)),
            control(tx("Educación", "Education"), ico="cap", comp=dcc.Checklist(
                id="ef-edu", value=[1, 2, 3, 4], inline=True, className="radio",
                options=ico_opts(EDU_TILES), **KEEP)),
            control(tx("Estado civil", "Marital status"), ico="rings", comp=dcc.Checklist(
                id="ef-mar", value=[1, 2, 3], inline=True, className="radio",
                options=ico_opts(MAR_TILES), **KEEP)),
        ], className="controls"),
        html.Div([
            control(tx("Edad (años)", "Age (years)"), ico="calendar", comp=dcc.RangeSlider(
                id="ef-age", min=21, max=79, step=1, value=[21, 79], allowCross=False,
                marks={i: str(i) for i in range(21, 80, 10)}, tooltip={"placement": "bottom"}, **KEEP)),
            control(tx("Cupo de crédito (NT$)", "Credit limit (NT$)"), ico="card", comp=dcc.RangeSlider(
                id="ef-lim", min=10000, max=1000000, step=10000, value=[10000, 1000000], allowCross=False,
                marks={10000: f"10 {k}", 250000: f"250 {k}", 500000: f"500 {k}", 750000: f"750 {k}", 1000000: "1 M"},
                tooltip={"placement": "bottom"}, **KEEP)),
        ], className="grid g2"),
        html.Div([html.Button(tx("Quitar filtros", "Clear filters"), id="ef-reset", className="btn")],
                 className="ef-bar"),
        html.P(tx("Los filtros actualizan todos los gráficos de esta página y de la otra página del EDA. Las tarjetas de "
                  "cifras y los textos fijos describen siempre a todos los clientes.",
                  "The filters update every chart on this page and on the other EDA page. The figure cards and the fixed "
                  "texts always describe all clients."), className="muted"),
    ]
    # Tarjeta plegable: arranca cerrada con una sola fila (icono, título, resumen y botón). Los controles
    # siguen en el DOM (los oculta <details>), porque cb_eda_filter los usa como entrada. El estado
    # abierto/cerrado se conserva entre páginas del EDA con assets/ef_fold.js.
    # Sin botón de ampliar ni modo foco (clase no-zoom): es una barra de controles, no una tarjeta de contenido.
    return html.Div([html.Details([
        html.Summary([icon("filter", "ef-ico"), html.H3(tx("Filtros globales", "Global filters"), className="card-title"),
                      html.Span(id="ef-info", className="ef-info"),
                      html.Span(icon("chevron", "ef-chev"), className="ef-toggle", **{"aria-hidden": "true"})],
                     className="ef-summary"),
        html.Div(controles, className="ef-body"),
    ], id="ef-fold", className="ef-fold")], className="card ef-card no-zoom")


def _ul(items, ordered=False):
    return (html.Ol if ordered else html.Ul)([html.Li(i) for i in items])


def _tbl(header, rows):
    head = html.Tr([html.Th(h) for h in header])
    body = [html.Tr([html.Td(c) for c in r]) for r in rows]
    return html.Div(html.Table([head] + body, className="vtable"), className="table-wrap")


# ---------------------------------------------------------------- Predecir
# persistence: al cambiar de idioma la página se vuelve a dibujar y los controles conservan lo elegido
KEEP = {"persistence": True, "persistence_type": "session"}


SEX_TILES = [(1, ("Hombre", "Male"), "male"), (2, ("Mujer", "Female"), "female"), (SEX_OTHER, ("Otro", "Other"), "gender")]
EDU_TILES = [(1, ("Posgrado", "Graduate"), "cap"), (2, ("Universidad", "University"), "book"),
             (3, ("Secundaria", "High school"), "pencil"), (4, ("Otros", "Others"), "dots")]
MAR_TILES = [(1, ("Casado", "Married"), "rings"), (2, ("Soltero", "Single"), "person"), (3, ("Otros", "Others"), "dots")]
