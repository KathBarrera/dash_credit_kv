# -*- coding: utf-8 -*-
"""Callbacks de tema, idioma, barra lateral, portada y enrutador de páginas."""

from dash import Input, Output, State, dcc, html

from tablero.config import (COURSE, L, NAV, PROJECT_TITLE, set_lang, tx)
from tablero.datos import DF
from tablero.iconos import icon
from tablero.layout import footer_content, sidebar_content
from tablero.paginas.conclusiones import page_conclusions
from tablero.paginas.contexto import page_intro, page_marco, page_problem
from tablero.paginas.eda import page_multi, page_uni
from tablero.paginas.enlaces import page_links
from tablero.paginas.equipo import page_team
from tablero.paginas.inicio import fig_home, page_home
from tablero.paginas.modelo_original import page_original
from tablero.paginas.modelos import page_models
from tablero.paginas.predecir import page_predict
from tablero.servidor import app
from tablero.tema import graph_cb
from tablero.utilidades import GLOBAL_RATE


@app.callback(Output("theme", "data"), Input("theme-btn", "n_clicks"), Input("theme-btn2", "n_clicks"),
              State("theme", "data"), prevent_initial_call=True)
def toggle_theme(n, n2, t):
    return "light" if t == "dark" else "dark"


# Resumen del umbral en la cabecera plegable de Predecir («52 %»), sin ir al servidor
app.clientside_callback(
    "function(v){ if (v === null || v === undefined) { return ''; } return Math.round(v * 100) + ' %'; }",
    Output("pf-thr-sum", "children"), Input("pf-thr", "value"))


app.clientside_callback(
    """function(t, l) { t = t || 'light'; document.documentElement.setAttribute('data-theme', t);
         var en = l === 'en';
         return t === 'dark' ? (en ? 'Switch to light mode' : 'Cambiar a modo claro')
                             : (en ? 'Switch to dark mode' : 'Cambiar a modo oscuro'); }""",
    Output("theme-btn", "title"), Input("theme", "data"), Input("lang", "data"))


# ---------- Idioma: botón ES/EN, atributos de la página y textos fijos -------------
@app.callback(Output("lang", "data"), Input("lang-btn", "n_clicks"), Input("lang-btn2", "n_clicks"),
              State("lang", "data"), prevent_initial_call=True)
def toggle_lang(n, n2, lang):
    return "es" if lang == "en" else "en"


app.clientside_callback(
    """function(l) { l = l === 'en' ? 'en' : 'es';
         document.documentElement.setAttribute('lang', l); document.documentElement.setAttribute('data-lang', l);
         document.title = l === 'en' ? 'EDA · Credit Risk' : 'EDA · Riesgo Crediticio';
         return l === 'en' ? 'Cambiar a español' : 'Switch to English'; }""",
    Output("lang-btn", "title"), Input("lang", "data"))


@app.callback(Output("sidebar", "children"), Output("footer", "children"),
              Output("tb-title", "children"), Output("tb-course", "children"), Output("tb-badge", "children"),
              Output("sb-btn", "title"), Output("tb-nb", "title"), Output("tb-gh", "title"),
              Output("bot-sub", "children"), Output("bot-foot", "children"), Output("bot-input", "placeholder"),
              Output("bot-reset", "title"), Output("bot-close", "title"), Output("bot-send", "title"),
              Input("lang", "data"), Input("url", "pathname"))
def cb_chrome(lang, path):
    """Textos fijos del marco (menú, barra superior, pie y panel de Kyo) en el idioma elegido."""
    set_lang(lang)
    path = (path or "/").rstrip("/") or "/"
    return (sidebar_content(path), footer_content(),
            L(PROJECT_TITLE), L(COURSE),
            [icon("chip"), tx(f"{len(DF):,} clientes · {GLOBAL_RATE:.1%} default",
                              f"{len(DF):,} clients · {GLOBAL_RATE:.1%} default")],
            tx("Mostrar u ocultar el menú lateral", "Show or hide the side menu"),
            tx("Abrir el notebook del EDA", "Open the EDA notebook"),
            tx("Abrir el repositorio del proyecto", "Open the project repository"),
            tx("Asistente del tablero · entrenado con su contenido", "Dashboard assistant · trained on its content"),
            tx("Respondo con lo que aprendí del contenido de este tablero; no uso servicios externos.",
               "I answer with what I learned from this dashboard's content; I don't use external services."),
            tx("Pregúntame por cualquier parte del tablero…", "Ask me about any part of the dashboard…"),
            tx("Nueva conversación", "New conversation"), tx("Cerrar (Esc)", "Close (Esc)"), tx("Enviar", "Send"))


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


def nav_buttons(path):
    """Botones Anterior / Siguiente para recorrer el tablero en orden."""
    order = [p for p, _, _ in NAV]
    i = order.index(path) if path in order else 0
    left = right = html.Span()
    if i > 0:
        left = dcc.Link([icon("arrow", "flip"), html.Div([html.Small(tx("Anterior", "Previous")),
                                                          html.B(L(NAV[i - 1][1]))])],
                        href=order[i - 1], className="pn prev")
    if i < len(order) - 1:
        right = dcc.Link([html.Div([html.Small(tx("Siguiente", "Next")), html.B(L(NAV[i + 1][1]))]), icon("arrow")],
                         href=order[i + 1], className="pn next")
    return html.Div([left, right], className="pn-row")


@app.callback(Output("page", "children"), Input("url", "pathname"), Input("lang", "data"))
def route(path, lang):
    set_lang(lang)
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
    if path == "/modelo-original":
        return page_original()
    if path == "/predecir":
        return page_predict()
    if path == "/conclusiones":
        return page_conclusions()
    if path == "/enlaces":
        return page_links()
    if path == "/equipo":
        return page_team()
    return page_home()
