# -*- coding: utf-8 -*-
"""Páginas EDA Univariado y EDA Multivariado."""

from dash import dcc, html

from tablero.componentes import (
    ALL_VARS, card, control, eda_filter_card, interp_block, kpi, page_title, var_options)
from tablero.config import WARM_GOLD, tx
from tablero.datos import DF, NUM_COLS, TARGET
from tablero.eda_multi import (fig_corr, fig_rates, interp_corr, interp_limit, interp_rates, key_findings)
from tablero.eda_uni import fig_target, interp_target, target_strip
from tablero.utilidades import GLOBAL_RATE, nt


def page_uni():
    b_t, t_t = interp_target()
    return html.Div([
        page_title(tx("EDA Univariado", "Univariate EDA"), "", stage="eda"),
        eda_filter_card(),
        html.Div([
            kpi(tx("Total de registros", "Total records"), f"{len(DF):,}",
                tx("tras eliminar duplicados", "after removing duplicates"), ico="users"),
            kpi(tx("Tasa global de default", "Overall default rate"), f"{GLOBAL_RATE:.1%}",
                f"{int(DF[TARGET].sum()):,} {tx('clientes', 'clients')}", ico="alert"),
            kpi(tx("Límite de crédito promedio", "Average credit limit"), nt(DF["LIMIT_BAL"].mean()),
                f"{tx('mediana', 'median')} {nt(DF['LIMIT_BAL'].median())}", ico="coin"),
            kpi(tx("Edad promedio", "Average age"), f"{DF['AGE'].mean():.1f} {tx('años', 'years')}",
                f"{tx('mediana', 'median')} {DF['AGE'].median():.0f}", ico="clock"),
        ], className="kpi-row k4"),
        html.Div([
            card(tx("Variable objetivo: Default vs. No Default", "Target variable: Default vs. No Default"),
                 [dcc.Graph(id="target-graph", figure=fig_target(), config={"displaylogo": False}), target_strip(),
                  interp_block(b_t, t_t)]),
            card(tx("Explorador univariado", "Univariate explorer"),
                 [html.Div([
                     control("Variable", dcc.Dropdown(id="uni-var", options=var_options(ALL_VARS),
                                                      value="LIMIT_BAL", clearable=False)),
                 ], className="controls"),
                  dcc.Loading(dcc.Graph(id="uni-graph", config={"displaylogo": False}), type="dot", color=WARM_GOLD),
                  html.Div(id="uni-interp")]),
        ], className="grid g2"),
        card(tx("Distribuciones de variables cuantitativas", "Distributions of quantitative variables"),
             [html.Div([
                 control(tx("Variable / familia", "Variable / family"), dcc.RadioItems(
                     id="q-family", value="LIMIT_BAL", className="radio",
                     options=[{"label": "LIMIT_BAL", "value": "LIMIT_BAL"}, {"label": "AGE", "value": "AGE"},
                              {"label": "BILL_AMT (1-6)", "value": "BILL_AMT"}, {"label": "PAY_AMT (1-6)", "value": "PAY_AMT"}])),
                 control(tx("Tipo de gráfico", "Chart type"), dcc.RadioItems(
                     id="q-kind", value="hist", className="radio",
                     options=[{"label": tx("Histograma", "Histogram"), "value": "hist"}, {"label": "Boxplot", "value": "box"},
                              {"label": tx("Densidad", "Density"), "value": "dens"}])),
             ], className="controls"),
              dcc.Loading(dcc.Graph(id="q-graph", config={"displaylogo": False}), type="dot", color=WARM_GOLD),
              html.Div(id="q-interp")]),
    ])


def page_multi():
    findings = [html.Div([html.Div(t, className="find-title"), html.P(x)], className="finding")
                for t, x in key_findings()]
    num_opts = var_options(NUM_COLS)
    return html.Div([
        page_title(tx("EDA Multivariado", "Multivariate EDA"), "", stage="eda"),
        eda_filter_card(),
        card(tx("Matriz de correlación de Spearman", "Spearman correlation matrix"),
             [dcc.Graph(id="corr-graph", figure=fig_corr(), config={"displaylogo": False}),
              interp_block(*interp_corr())]),
        html.Div([
            card(tx("Incumplimiento por educación, estado civil y sexo", "Default by education, marital status and sex"),
                 [dcc.Graph(id="rates-graph", figure=fig_rates(), config={"displaylogo": False}),
                  interp_block(*interp_rates())]),
            card(tx("Límite de crédito según estado de default", "Credit limit by default status"),
                 [html.Div([control(tx("Escala del eje Y", "Y-axis scale"), dcc.RadioItems(
                     id="lim-scale", value="linear", className="radio",
                     options=[{"label": tx("Lineal", "Linear"), "value": "linear"},
                              {"label": tx("Logarítmica", "Logarithmic"), "value": "log"}]))],
                     className="controls"),
                  dcc.Graph(id="lim-graph", config={"displaylogo": False}),
                  interp_block(*interp_limit())]),
        ], className="grid g2"),
        card(tx("Edad y patrones de atraso en pagos (PAY_0 a PAY_6)", "Age and payment delay patterns (PAY_0 to PAY_6)"),
             [html.Div([control(tx("Vista", "View"), dcc.RadioItems(
                 id="age-view", value="lines", className="radio",
                 options=[{"label": tx("Atraso promedio por mes", "Average delay by month"), "value": "lines"},
                          {"label": tx("% con atraso ≥ 1 mes", "% with delay ≥ 1 month"), "value": "heat"},
                          {"label": tx("Tasa de default por edad", "Default rate by age"), "value": "rate"}]))],
                 className="controls"),
              dcc.Graph(id="age-graph", config={"displaylogo": False}),
              html.Div(id="age-interp")]),
        card(tx("Módulo interactivo: cruce de variables", "Interactive module: variable cross"),
             [html.Div([
                 control(tx("Variable X", "X variable"),
                         dcc.Dropdown(id="x-var", options=var_options(ALL_VARS), value="EDUCATION", clearable=False)),
                 control(tx("Variable Y", "Y variable"),
                         dcc.Dropdown(id="y-var", options=var_options(ALL_VARS), value="LIMIT_BAL", clearable=False)),
                 control(tx("Color / grupo (opcional)", "Color / group (optional)"), dcc.Dropdown(
                     id="c-var", options=[{"label": tx("(ninguna)", "(none)"), "value": "none"}] + var_options(ALL_VARS),
                     value=TARGET, clearable=False)),
             ], className="controls"),
              dcc.Loading(dcc.Graph(id="x-graph", config={"displaylogo": False}), type="dot", color=WARM_GOLD),
              html.Div(id="x-interp")]),
        card(tx("Matriz de dispersión: 2 o más variables numéricas", "Scatter matrix: 2 or more numeric variables"),
             [html.Div([control(tx("Variables (elige entre 2 y 6)", "Variables (choose 2 to 6)"), dcc.Dropdown(
                 id="s-vars", options=num_opts, multi=True,
                 value=["LIMIT_BAL", "AGE", "PAY_0", "BILL_AMT1", "PAY_AMT1"]))], className="controls"),
              dcc.Loading(dcc.Graph(id="s-graph", config={"displaylogo": False}), type="dot", color=WARM_GOLD),
              html.Div(id="s-interp")]),
        html.Div([html.H3(tx("Hallazgos multivariados clave", "Key multivariate findings"), className="section-h"),
                  html.Div(findings, className="grid g4")], className="findings"),
    ])
