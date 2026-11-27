# -*- coding: utf-8 -*-
"""Barra lateral, barra superior, plantilla HTML y layout final de la aplicación."""

from dash import dcc, html

from tablero.config import (
    AUTHORS, INSTITUTION, L, LINKS, NAV, NOTEBOOK_URL, PROJECT_SUBTITLE, PROJECT_TITLE, REPO_PROJECT, tx)
from tablero.estilos import (BOT_JS, COVER_JS, CSS, WALKER_HTML)
from tablero.iconos import icon
from tablero.glosario import glossary_script
from tablero.kyo import bot_panel
from tablero.pipeline import pipeline_btn, pipeline_modal
from tablero.servidor import app


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
  {glossary_script()}
</head>
<body>
  {{%app_entry%}}
  {WALKER_HTML}
  <script>{COVER_JS}</script>
  <script>{BOT_JS}</script>
  {{%config%}}{{%scripts%}}{{%renderer%}}
</body>
</html>"""


def sidebar_content(path):
    """Contenido del menú lateral en el idioma activo (se redibuja al cambiar de idioma o de página)."""
    return [
        dcc.Link([html.Div([icon("card"), tx("Proyecto EDA", "EDA Project")], className="brand-tag"),
                  html.Div(L(PROJECT_TITLE), className="brand-title"),
                  html.P(L(PROJECT_SUBTITLE), className="brand-sub")], href="/", className="brand",
                 title=tx("Ir a la portada", "Go to the cover")),
        html.Div([dcc.Link([icon(ic), html.Span(L(lbl))], href=p, id=f"nav-{i}",
                           className="active" if path == p else "")
                  for i, (p, lbl, ic) in enumerate(NAV)], className="nav"),
        # === CAMBIAR AQUÍ NOMBRES Y CORREOS (se editan en AUTHORS, al inicio del archivo) ===
        html.Div([
            html.H4(tx("Autores", "Authors")),
            *[html.Div([html.Div(a["name"], className="nm"), html.Div(a["email"], className="em")], className="author")
              for a in AUTHORS],
            html.Div(L(INSTITUTION), className="inst"),
        ], className="authors"),
    ]


def footer_content():
    # === CAMBIAR AQUÍ NOMBRES Y CORREOS (pie de página; se alimenta de AUTHORS) ===
    return [
        html.Div([
            html.Div([html.B(tx("Autores: ", "Authors: ")), " · ".join(f"{a['name']} ({a['email']})" for a in AUTHORS)]),
            html.Div(f"{L(INSTITUTION)} · {tx('Datos', 'Data')}: UCI Machine Learning Repository (Yeh & Lien, 2009)"),
        ]),
        html.Div([html.A([icon(lk["icon"]), L(lk["title"])], href=lk["url"], target="_blank", rel="noopener noreferrer")
                  for lk in LINKS], className="footer-links"),
    ]


sidebar = html.Div(id="sidebar", className="sidebar")
footer = html.Div(id="footer", className="footer")


def lang_switch(id_, cls=""):
    """Botón ES | EN: el idioma activo queda resaltado (ver CSS [data-lang])."""
    return html.Button([html.Span("ES", className="ls-es"), html.Span("EN", className="ls-en")], id=id_, n_clicks=0,
                       type="button", className=f"lang-switch {cls}".strip(),
                       title="Español / English", **{"aria-label": "Cambiar idioma / Change language"})


# ---------- Layout final: tema, barra lateral plegable, botones -------------------
topbar = html.Div([
    html.Div([
        html.Button(icon("panel"), id="sb-btn", className="icon-btn"),
        html.Div([html.Div(id="tb-title", className="t1"), html.Div(id="tb-course", className="t2")]),
    ], className="tb-left"),
    html.Div([
        html.Div(id="tb-badge", className="badge"),
        pipeline_btn(label="Pipeline", compact=True, cls="tb-pipe",
                     title="Pipeline · de los datos al tablero / from data to dashboard"),
        html.A(icon("notebook"), id="tb-nb", href=NOTEBOOK_URL, target="_blank", rel="noopener noreferrer",
               className="icon-btn"),
        html.A(icon("github"), id="tb-gh", href=REPO_PROJECT, target="_blank", rel="noopener noreferrer",
               className="icon-btn"),
        lang_switch("lang-btn"),
        html.Button([icon("sun", "t-sun"), icon("moon", "t-moon")], id="theme-btn", n_clicks=0,
                    className="theme-toggle"),
    ], className="tb-right"),
], className="topbar")


app.layout = html.Div([
    dcc.Location(id="url"),
    dcc.Store(id="theme", storage_type="local", data="light"),
    dcc.Store(id="lang", storage_type="local", data="es"),
    # interruptores de idioma y tema de la portada (solo visibles en la portada, ver CSS)
    html.Div([lang_switch("lang-btn2"),
              html.Button([icon("sun", "t-sun"), icon("moon", "t-moon")], id="theme-btn2", n_clicks=0,
                          className="theme-toggle", title="☀ / ☾",
                          **{"aria-label": "Cambiar entre modo claro y oscuro / Toggle light and dark mode"})],
             className="cover-toggle"),
    sidebar,
    html.Div([topbar, html.Div(id="page", className="content"), footer], className="main"),
    dcc.Store(id="bot-store", storage_type="session", data=[]),
    dcc.Store(id="eda-filter", storage_type="session", data=None),
    pipeline_modal(),
    bot_panel(),
], id="shell", className="app")
