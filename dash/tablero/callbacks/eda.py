# -*- coding: utf-8 -*-
"""Callbacks del EDA: filtro global y gráficas univariadas y multivariadas.

Cada callback calcula el subconjunto con aplicar_filtro(f) y se lo pasa a las figuras: no hay estado
global, así que las peticiones simultáneas no se mezclan.
"""

import plotly.graph_objects as go
from dash import Input, Output

from tablero.componentes import interp_block
from tablero.config import set_lang, tx
from tablero.datos import (DF, EDA_MIN_ROWS, TARGET, aplicar_filtro)
from tablero.eda_multi import (
    cross_fig, fig_age, fig_corr, fig_limit_box, fig_rates, fig_splom, interp_age, interp_splom)
from tablero.eda_uni import (fig_quant, fig_target, fig_uni, interp_quant, interp_uni)
from tablero.servidor import app
from tablero.tema import graph_cb
from tablero.utilidades import GLOBAL_RATE, style_fig


@app.callback(Output("eda-filter", "data"), Output("ef-info", "children"),
              Input("ef-sex", "value"), Input("ef-edu", "value"), Input("ef-mar", "value"),
              Input("ef-age", "value"), Input("ef-lim", "value"), Input("lang", "data"))
def cb_eda_filter(sex, edu, mar, age, lim, lang):
    set_lang(lang)
    f = {"sex": sex or [], "edu": edu or [], "mar": mar or [], "age": age, "lim": lim}
    todos = (set(sex or []) >= {1, 2} and set(edu or []) >= {1, 2, 3, 4} and set(mar or []) >= {1, 2, 3}
             and (not age or list(age) == [21, 79]) and (not lim or list(lim) == [10000, 1000000]))
    if todos:
        return None, tx(f"Mostrando a todos los clientes ({len(DF):,}).", f"Showing all clients ({len(DF):,}).")
    sub = aplicar_filtro(f)
    if sub is DF:
        return None, tx(f"El filtro deja menos de {EDA_MIN_ROWS} clientes: se muestran todos.",
                        f"The filter leaves fewer than {EDA_MIN_ROWS} clients: showing all of them.")
    return f, tx(f"Mostrando {len(sub):,} de {len(DF):,} clientes ({len(sub) / len(DF):.0%}); tasa de impago "
                 f"{sub[TARGET].mean():.1%} (global {GLOBAL_RATE:.1%}).",
                 f"Showing {len(sub):,} of {len(DF):,} clients ({len(sub) / len(DF):.0%}); default rate "
                 f"{sub[TARGET].mean():.1%} (overall {GLOBAL_RATE:.1%}).")


@app.callback(Output("ef-sex", "value"), Output("ef-edu", "value"), Output("ef-mar", "value"),
              Output("ef-age", "value"), Output("ef-lim", "value"), Input("ef-reset", "n_clicks"), prevent_initial_call=True)
def cb_eda_reset(_):
    return [1, 2], [1, 2, 3, 4], [1, 2, 3], [21, 79], [10000, 1000000]


@graph_cb(Output("target-graph", "figure"), Input("eda-filter", "data"), mono=True)
def cb_target(f):
    data = aplicar_filtro(f)
    return fig_target(data=data)


@graph_cb(Output("rates-graph", "figure"), Input("eda-filter", "data"))
def cb_rates(f):
    data = aplicar_filtro(f)
    return fig_rates(data=data)


@graph_cb(Output("corr-graph", "figure"), Input("eda-filter", "data"))
def cb_corr(f):
    data = aplicar_filtro(f)
    return fig_corr(data=data)


# ---------- Callbacks: Univariado (gráficas de un solo color) ------------------
@graph_cb(Output("uni-graph", "figure"), Output("uni-interp", "children"),
          Input("uni-var", "value"), Input("eda-filter", "data"), mono=True)
def cb_uni(var, f):
    data = aplicar_filtro(f)
    return fig_uni(var, data=data), interp_block(*interp_uni(var, data=data))


@graph_cb(Output("q-graph", "figure"), Output("q-interp", "children"),
          Input("q-family", "value"), Input("q-kind", "value"), Input("eda-filter", "data"),
          mono=lambda family, kind, f: family in ("LIMIT_BAL", "AGE"))
def cb_quant(family, kind, f):
    data = aplicar_filtro(f)
    return fig_quant(family, kind, data=data), interp_block(*interp_quant(family, data=data))


# ---------- Callbacks: Multivariado -------------------------------------------
@graph_cb(Output("lim-graph", "figure"), Input("lim-scale", "value"), Input("eda-filter", "data"))
def cb_limit(scale, f):
    data = aplicar_filtro(f)
    return fig_limit_box(scale, data=data)


@graph_cb(Output("age-graph", "figure"), Output("age-interp", "children"), Input("age-view", "value"),
          Input("eda-filter", "data"))
def cb_age(view, f):
    data = aplicar_filtro(f)
    return fig_age(view, data=data), interp_block(*interp_age(view, data=data))


@graph_cb(Output("x-graph", "figure"), Output("x-interp", "children"),
          Input("x-var", "value"), Input("y-var", "value"), Input("c-var", "value"), Input("eda-filter", "data"))
def cb_cross(x, y, c, f):
    data = aplicar_filtro(f)
    fig, b, t = cross_fig(x, y, c, data=data)
    return fig, interp_block(b, t)


@graph_cb(Output("s-graph", "figure"), Output("s-interp", "children"), Input("s-vars", "value"),
          Input("eda-filter", "data"))
def cb_splom(vars_, f):
    data = aplicar_filtro(f)
    return _cb_splom(vars_, data=data)


def _cb_splom(vars_, data=DF):
    vars_ = (vars_ or [])[:6]
    if len(vars_) < 2:
        fig = go.Figure()
        fig.update_layout(title=tx("Selecciona al menos 2 variables", "Select at least 2 variables"))
        return style_fig(fig, 380, legend_top=False), interp_block(
            tx("Elige al menos dos variables numéricas.", "Choose at least two numeric variables."), "")
    return fig_splom(vars_, data=data), interp_block(*interp_splom(vars_, data=data))
