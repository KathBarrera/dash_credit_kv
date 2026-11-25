# -*- coding: utf-8 -*-
"""Callbacks de la página Predecir: perfiles, umbral, puntaje y simulador «¿Qué pasaría si…?»."""

import plotly.graph_objects as go
from dash import Input, Output, ctx, html

from tablero.config import set_lang, tx
from tablero.datos import pretty
from tablero.paginas.predecir import predict_verdict, threshold_stats, trees_block
from tablero.prediccion import (
    INPUT_COLS, MODELO, PROFILES, _meta, _mk, _rec_thr, fig_client_history, fig_drivers, fig_whatif,
    predict_risk)
from tablero.servidor import app
from tablero.tema import themed
from tablero.utilidades import style_fig


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


def thr_info(key, thr):
    st = threshold_stats(key, thr)
    if not st:
        return ""
    rec = _rec_thr(key)
    return html.Div([
        html.Div([
            html.Div([html.Small(tx("Detecta", "Detects")), html.B(f"{st['recall']:.0%}"),
                      html.Small(tx("de quienes incumplen", "of defaulters"))], className="pf-thr-k"),
            html.Div([html.Small(tx("Acierta en", "Right about")), html.B(f"{st['precision']:.0%}"),
                      html.Small(tx("de los que marca", "of those flagged"))], className="pf-thr-k"),
            html.Div([html.Small(tx("Marca como riesgo", "Flags as risky")), html.B(f"{st['marcados']:.0%}"),
                      html.Small(tx("de los clientes", "of clients"))], className="pf-thr-k"),
            html.Div([html.Small(tx("Falsas alarmas", "False alarms")), html.B(f"{st['falsas_alarmas_por_100']:.1f}"),
                      html.Small(tx("por cada 100 clientes", "per 100 clients"))], className="pf-thr-k"),
            html.Div([html.Small("F1"), html.B(f"{st['f1']:.3f}"), html.Small(tx("clase de impago", "default class"))],
                     className="pf-thr-k")], className="pf-thr-kpis"),
        html.P(tx(f"Umbral recomendado para este modelo: {rec:.0%} (máximo F1, elegido con una mitad de la prueba y "
                  "medido con la otra; las cifras de arriba son de esa otra mitad). Bajar el umbral detecta más "
                  "incumplimientos a cambio de más falsas alarmas; subirlo hace lo contrario. El banco lo fija según "
                  "cuánto le cuesta cada tipo de error.",
                  f"Recommended threshold for this model: {rec:.0%} (maximum F1, chosen with one half of the test set "
                  "and measured on the other; the figures above come from that other half). Lowering the threshold "
                  "catches more defaults at the cost of more false alarms; raising it does the opposite. The bank sets "
                  "it according to how much each kind of error costs."), className="muted")])


@app.callback(Output("pf-thr", "value"), Input("pf-model", "value"), prevent_initial_call=True)
def cb_thr_reset(key):
    return _rec_thr(_mk(key))


def model_info(key):
    m = _meta(key)
    pr = m.get("prueba", {})
    if not pr:
        return ""
    return tx(f"{m.get('modelo', '')}: en {pr['n']:,} clientes de prueba (20 %, nunca vistos al entrenar) logra F1 "
              f"{pr['f1']:.3f}, recall {pr['recall']:.3f}, precisión {pr['precision']:.3f} y AUC-ROC {pr['roc_auc']:.3f}. "
              "Los dos modelos usan la misma partición, las mismas variables y pesos de clase.",
              f"{m.get('modelo', '')}: on {pr['n']:,} test clients (20%, never seen in training) it reaches F1 "
              f"{pr['f1']:.3f}, recall {pr['recall']:.3f}, precision {pr['precision']:.3f} and ROC-AUC {pr['roc_auc']:.3f}. "
              "Both models use the same split, the same variables and class weights.")


@app.callback(Output("pf-verdict", "children"), Output("pf-trees", "children"),
              Output("pf-history", "figure"), Output("pf-drivers", "figure"), Output("pf-model-info", "children"),
              Output("pf-thr-info", "children"),
              *[Input(f"pf-{c}", "value") for c in INPUT_COLS], Input("pf-model", "value"), Input("pf-thr", "value"),
              Input("theme", "data"), Input("lang", "data"))
def cb_predict(*vals):
    *vals, key, thr, theme, lang = vals
    key = _mk(key)
    thr = float(thr) if thr is not None else _rec_thr(key)
    set_lang(lang)
    dark = theme == "dark"
    values, missing = _pf_values(vals)
    if MODELO is None or missing:
        msg = html.P(tx("Completa los campos: ", "Fill in the fields: ") + ", ".join(missing[:4])
                     + ("…" if len(missing) > 4 else ""),
                     className="callout") if missing else ""
        empty = style_fig(go.Figure(), 340, legend_top=False)
        return msg, "", themed(empty, dark), themed(empty, dark), model_info(key), thr_info(key, thr)
    score = predict_risk(values, key)
    return (predict_verdict(values, score, key, thr), trees_block(values, key),
            themed(fig_client_history(values), dark), themed(fig_drivers(values, score, key), dark), model_info(key),
            thr_info(key, thr))


@app.callback(Output("pf-whatif", "figure"), Input("pf-whatif-var", "value"),
              *[Input(f"pf-{c}", "value") for c in INPUT_COLS], Input("pf-model", "value"), Input("pf-thr", "value"),
              Input("theme", "data"), Input("lang", "data"))
def cb_whatif(var, *vals):
    *vals, key, thr, theme, lang = vals
    key = _mk(key)
    thr = float(thr) if thr is not None else _rec_thr(key)
    set_lang(lang)
    values, missing = _pf_values(vals)
    if MODELO is None or missing:
        return themed(style_fig(go.Figure(), 360, legend_top=False), theme == "dark")
    return themed(fig_whatif(values, var or "PAY_0", predict_risk(values, key), key, thr), theme == "dark")
