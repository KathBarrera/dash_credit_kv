# -*- coding: utf-8 -*-
"""Callback de la ventana del pipeline: título y etapas en el idioma elegido."""

from dash import Input, Output

from tablero.config import set_lang, tx
from tablero.pipeline import pipeline_body
from tablero.servidor import app


@app.callback(Output("pipe-title", "children"), Output("pipe-body", "children"), Input("lang", "data"))
def cb_pipeline(lang):
    set_lang(lang)
    return tx("Pipeline del proyecto", "Project pipeline"), pipeline_body()
