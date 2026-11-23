# -*- coding: utf-8 -*-
"""Callbacks de las páginas Modelos y Modelo original."""

from dash import Input, Output, dcc

from tablero.componentes import interp_block
from tablero.config import set_lang
from tablero.paginas.modelo_original import (_rival, cs_vs_rf_interp, fig_cs_vs_rf, fig_csfof_toy)
from tablero.resultados import (
    DIAG, anytime_table, cd_interp, diag_interp, fig_anytime, fig_best_cm, fig_cd, fig_diag, fig_lime_cells,
    fig_models_heat, fig_models_scatter, fig_shap_folds, fig_shap_global, interp_anytime, interp_shap_folds,
    shap_global_interp)
from tablero.servidor import app
from tablero.tema import graph_cb, themed


# ---------- Callbacks: Modelos ------------------------------------------------
@graph_cb(Output("mdl-heat", "figure"))
def cb_models_heat():
    return fig_models_heat()


# Un gráfico nuevo (id distinto) por escenario y rival: así una animación en curso no sigue sobre el escenario nuevo.
@app.callback(Output("csrf-box", "children"), Input("csrf-scn", "value"), Input("csrf-rival", "value"),
              Input("theme", "data"), Input("lang", "data"))
def cb_cs_vs_rf(scn, rival, theme, lang):
    set_lang(lang)
    scn, rival = scn or "folds", _rival(rival)
    fig = themed(fig_cs_vs_rf(scn, rival), theme == "dark")
    return [dcc.Graph(id=f"csrf-graph-{scn}-{rival}", figure=fig, config={"displaylogo": False, "displayModeBar": False}),
            cs_vs_rf_interp(scn, rival)]


@graph_cb(Output("cs-toy-tree", "figure"))
def cb_cs_toy_tree():
    return fig_csfof_toy("tree")


@graph_cb(Output("cs-toy-obl", "figure"))
def cb_cs_toy_obl():
    return fig_csfof_toy("oblique")


@graph_cb(Output("mdl-scatter", "figure"))
def cb_models_scatter():
    return fig_models_scatter()


@graph_cb(Output("mdl-cm", "figure"))
def cb_best_cm():
    return fig_best_cm()


@graph_cb(Output("lime-graph", "figure"))
def cb_lime_cells():
    return fig_lime_cells()


@graph_cb(Output("shap-graph", "figure"), Output("shap-interp", "children"), Input("shap-model", "value"))
def cb_shap(model):
    if model == "cs_fof":
        return fig_shap_global(model), shap_global_interp(model)
    return fig_shap_folds(model), interp_block(*interp_shap_folds(model))


@graph_cb(Output("diag-graph", "figure"), Output("diag-interp", "children"), Input("diag-model", "value"))
def cb_diag(model):
    model = model if model in DIAG["modelos"] else "cs_fof"
    return fig_diag(model), diag_interp(model)


@graph_cb(Output("cd-graph", "figure"), Output("cd-interp", "children"), Input("cd-src", "value"))
def cb_cd(fuente):
    fuente = fuente if fuente in DIAG["friedman"] else "taiwan"
    return fig_cd(fuente), cd_interp(fuente)


@graph_cb(Output("any-graph", "figure"), Output("any-table", "children"), Output("any-interp", "children"),
          Input("any-model", "value"))
def cb_anytime(model):
    return fig_anytime(model), anytime_table(model), interp_block(*interp_anytime(model))
