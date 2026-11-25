# -*- coding: utf-8 -*-
"""Tema claro / oscuro de las figuras Plotly y el decorador graph_cb, que añade el tema y el idioma
como entradas de los callbacks de gráficas.
"""

import plotly.io as pio
from dash import Input

from tablero.config import (
    BROWN, CREAM, DEEP_NAVY, DEEP_RGBA, GOLD_DARK, GOLD_MID, MID_BLUE, NAVY, PALE_GOLD, WARM_GOLD,
    _rgba_prefix, set_lang)
from tablero.servidor import app


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
    """Como @app.callback, pero añade el tema y el idioma como entradas y adapta la primera salida (la figura).

    mono puede ser True/False o una función (con los mismos argumentos que el callback)
    que devuelva True cuando la figura sea de un solo color.
    """
    def deco(fn):
        @app.callback(*args, Input("theme", "data"), Input("lang", "data"))
        def wrapper(*vals):
            *vals, theme, lang = vals
            set_lang(lang)
            res = fn(*vals)
            dark = theme == "dark"
            m = mono(*vals) if callable(mono) else mono
            if isinstance(res, tuple):
                return (themed(res[0], dark, m),) + res[1:]
            return themed(res, dark, m)
        return wrapper
    return deco
