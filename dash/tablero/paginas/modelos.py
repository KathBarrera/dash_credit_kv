# -*- coding: utf-8 -*-
"""Página Modelos: carrusel de los siete clasificadores y resultados de la validación cruzada anidada."""

import pandas as pd
from dash import dcc, html

from tablero.componentes import (card, control, interp_block, kpi, page_title)
from tablero.config import tx
from tablero.iconos import icon
from tablero.resultados import (
    ANY_MODELS, BASELINE, BEST, BEST_BASE, BEST_BY_MODEL, CSFOF_CM, DIAG_MODELS, MR, N_BASE, N_EXTRA,
    TECH_ORDER, XGB_CM, fig_best_cm, fig_models_heat, fig_models_scatter, leaderboard, lime_shap_table,
    method_lbl, minfo, tech_lbl)


# ---------------------------------------------------------------- Modelos
F1_MAX = float(BEST["f1_mean"])   # referencia de las tarjetas: el mayor F1 medio


def _mc_bar(label, v, scale=1.0, cls=""):
    """Fila de métrica con barra (v se dibuja como fracción de `scale`)."""
    if pd.isna(v):
        return html.Div([html.Span(label), html.Div(className="mc-bar na"),
                         html.B(tx("n/d", "n/a"), title=tx("No calculado", "Not computed"))],
                        className="mc-metric")
    return html.Div([html.Span(label),
                     html.Div(html.Span(style={"width": f"{min(v / scale, 1) * 100:.1f}%"}), className="mc-bar"),
                     html.B(f"{v:.3f}")], className=f"mc-metric {cls}".strip())


def model_slide(row, rank):
    """Tarjeta de un modelo dentro del carrusel (mejor combinación de ese modelo)."""
    m = row["model"]
    best = rank == 1
    sub = MR[MR["model"] == m]
    by_tech = sub.groupby("technique")["f1_mean"].max()
    top = html.Div([html.Span(f"#{rank}", className="mc-rank"),
                    html.Span([icon("trophy"), tx("Mayor F1 medio", "Highest mean F1")], className="mc-badge") if best
                    else html.Span(tx(f"{row['f1_mean'] - F1_MAX:+.4f} F1 vs. el mejor",
                                      f"{row['f1_mean'] - F1_MAX:+.4f} F1 vs. the best"), className="mc-fam-top")],
                   className="mc-top")
    return html.Article([
        html.Div(className="cc-gloss"),
        top,
        html.H3(minfo(m, "label"), className="mc-name"),
        html.Div(minfo(m, "family"), className="mc-family"),
        html.Div([
            html.Div(className="cc-chip mc-chip"),
            html.Div([html.Span(tx("F1 · clase default", "F1 · default class"), className="cc-lbl"),
                      html.Div([html.Span(f"{row['f1_mean']:.3f}", className="mc-f1"),
                                html.Span(f"± {row['f1_std']:.3f}", className="mc-std")])]),
        ], className="mc-score"),
        html.Div([html.Span(tech_lbl(row["technique"]), className="mc-pill"),
                  html.Span(method_lbl(row["method"]), className="mc-pill")], className="mc-config",
                 title=tx("Técnica de balanceo y método de optimización de su mejor combinación",
                          "Balancing technique and optimization method of its best combination")),
        html.Div([_mc_bar(tx("Precisión", "Precision"), row["precision_mean"]), _mc_bar("Recall", row["recall_mean"]),
                  _mc_bar("ROC-AUC", row["roc_auc_mean"]), _mc_bar("PR-AUC", row["pr_auc_mean"])],
                 className="mc-metrics"),
        html.Div([html.Span(tx("Mejor F1 con cada técnica de balanceo", "Best F1 with each balancing technique"),
                            className="cc-lbl"),
                  *[_mc_bar(tech_lbl(t), by_tech.get(t), F1_MAX, "on" if t == row["technique"] else "")
                    for t in TECH_ORDER]], className="mc-metrics mc-tech"),
        html.P(minfo(m, "desc"), className="mc-desc"),
        html.P(minfo(m, "note"), className="mc-note"),
        html.Div(tx(f"{len(sub)} combinaciones · F1 de {sub['f1_mean'].min():.3f} a {sub['f1_mean'].max():.3f}",
                    f"{len(sub)} combinations · F1 from {sub['f1_mean'].min():.3f} to {sub['f1_mean'].max():.3f}"),
                 className="mc-foot"),
    ], className="mc-slide" + (" best" if best else ""),
        **{"aria-label": tx(f"Puesto {rank}: {minfo(m, 'label')}, F1 {row['f1_mean']:.3f}",
                            f"Rank {rank}: {minfo(m, 'label')}, F1 {row['f1_mean']:.3f}")})


def models_carousel():
    rows = list(BEST_BY_MODEL.iterrows())
    slides = [model_slide(r, i + 1) for i, r in rows]
    dots = [html.Button(className="mc-dot", n_clicks=0,
                        **{"data-i": str(i), "type": "button", "title": minfo(r["model"], "label"),
                           "aria-label": f"{tx('Ver', 'Show')} {minfo(r['model'], 'label')}"})
            for i, r in rows]
    return html.Div([
        html.Div([
            html.Button(icon("chevron"), className="mc-nav mc-prev", n_clicks=0,
                        **{"type": "button", "title": tx("Modelo anterior", "Previous model"),
                           "aria-label": tx("Modelo anterior", "Previous model")}),
            html.Div(slides, className="mc-track", tabIndex=0,
                     **{"role": "region", "aria-label": tx("Carrusel de modelos; usa las flechas para desplazarte",
                                                           "Model carousel; use the arrows to move")}),
            html.Button(icon("chevron"), className="mc-nav mc-next", n_clicks=0,
                        **{"type": "button", "title": tx("Modelo siguiente", "Next model"),
                           "aria-label": tx("Modelo siguiente", "Next model")}),
        ], className="mc-stage"),
        html.Div(dots, className="mc-dots"),
        html.P(tx(f"Desliza, usa las flechas o los puntos para recorrer los {len(rows)} modelos.",
                  f"Swipe, or use the arrows or dots to browse the {len(rows)} models."), className="muted mc-hint"),
    ], className="mc-wrap")


def page_models():
    b = BEST
    best_lbl = minfo(BEST["model"], "label")
    c = CSFOF_CM
    pos, flagged = c["tp"] + c["fn"], c["tp"] + c["fp"]
    gcfg = {"displaylogo": False, "displayModeBar": False}
    return html.Div([
        page_title(tx("Modelos", "Models"), ""),
        html.Div([
            kpi(tx("Combinaciones evaluadas", "Combinations evaluated"), f"{N_BASE} + {N_EXTRA}",
                tx(f"{N_BASE} del diseño factorial (7 × 4 × 4) y, aparte, {N_EXTRA} corridas de CS-FOF",
                   f"{N_BASE} from the factorial design (7 × 4 × 4) and, separately, {N_EXTRA} runs of CS-FOF"),
                "layers"),
            kpi(tx("Mejor F1 (clase default)", "Best F1 (default class)"),
                f"{BEST['f1_mean']:.3f}",
                tx(f"CS-FOF, el mayor de los modelos comparados ({minfo(BEST_BASE['model'], 'label')}: "
                   f"{BEST_BASE['f1_mean']:.3f}); la diferencia no es significativa.",
                   f"CS-FOF, the highest of the models compared ({minfo(BEST_BASE['model'], 'label')}: "
                   f"{BEST_BASE['f1_mean']:.3f}); the difference is not significant."), "trophy"),
            kpi(tx("Mejora sobre la línea base", "Improvement over baseline"), f"+{b['f1_mean'] - BASELINE:.3f}",
                tx(f"Regresión logística sin balanceo: {BASELINE:.3f}", f"Logistic regression without balancing: {BASELINE:.3f}"),
                "bars"),
            kpi(tx("Incumplimientos detectados", "Defaults detected"), f"{c['tp'] / pos:.0%}",
                tx(f"{c['tp']:,} de {pos:,} · {best_lbl}, predicciones fuera de pliegue (umbral 0.5)",
                   f"{c['tp']:,} of {pos:,} · {best_lbl}, out-of-fold predictions (threshold 0.5)"), "target"),
        ], className="kpi-row k4"),
        card(tx(f"Tabla de líderes: {len(MR)} combinaciones", f"Leaderboard: {len(MR)} combinations"), [
            leaderboard(),
            interp_block(
                tx("Haz clic en un encabezado para ordenar y escribe en la fila gris para filtrar (por ejemplo, "
                   "«XGBoost» en Modelo o «> 0.54» en AUC). La estrella marca la mejor combinación de cada modelo, "
                   "elegida por el F1 medio del bucle externo de la validación anidada 5 × 5.",
                   "Click a header to sort and type in the grey row to filter (for example, “XGBoost” in Model or "
                   "“> 0.54” in AUC). The star marks each model's best combination, chosen by the mean F1 of the "
                   "outer loop of the 5 × 5 nested validation."),
                tx("El tiempo de inferencia se midió con el pliegue 0 (5,993 clientes, 4 núcleos) para los tres "
                   "mejores modelos. CS-FOF es el más lento al predecir (253 ms por cada 1,000 clientes) porque sus "
                   "árboles se recorren con numpy, sin código compilado como el de las librerías de los demás.",
                   "Inference time was measured on fold 0 (5,993 clients, 4 cores) for the three best models. CS-FOF is "
                   "the slowest to predict (253 ms per 1,000 clients) because its trees are traversed with numpy, without "
                   "compiled code like the other models' libraries.")),
        ]),
        card(tx("Comparación de modelos", "Model comparison"), models_carousel()),
        html.Div([
            card(tx("F1 por modelo y técnica de balanceo", "F1 by model and balancing technique"), [
                dcc.Graph(id="mdl-heat", figure=fig_models_heat(), config=gcfg),
                interp_block(
                    tx("Cada celda es el mejor F1 que logró el modelo con esa técnica. Sin balanceo todos rinden peor, "
                       "porque casi no detectan a quienes incumplen; con pesos de clase, los tres mejores llegan a "
                       "0.55. CS-FOF solo se corrió con pesos de clase (celdas vacías).",
                       "Each cell is the best F1 the model achieved with that technique. Without balancing all of them "
                       "perform worse, because they barely detect defaulters; with class weights, the top three reach "
                       "0.55. CS-FOF was only run with class weights (empty cells)."),
                    tx("Comparación por factor sobre las 112 combinaciones base (Friedman con 28 bloques modelo × método): χ² = 76.0, p ≈ 2·10⁻¹⁶. "
                       "Sin balanceo el F1 medio es 0.455, frente a 0.526 (pesos de clase), 0.520 (SMOTE) y 0.513 "
                       "(ADASYN); «sin balanceo» es peor que las tres (Nemenyi, p ≤ 0.010). Pesos de clase supera a "
                       "ADASYN (p < 10⁻⁴) y no se distingue de SMOTE (p = 0.35); SMOTE supera a ADASYN (p = 0.007). "
                       "Naive Bayes es el único modelo al que el balanceo casi no le cambia el F1.",
                       "Comparison by factor over the 112 base combinations (Friedman with 28 model × method blocks): χ² = 76.0, p ≈ 2·10⁻¹⁶. "
                       "Without balancing the mean F1 is 0.455, versus 0.526 (class weights), 0.520 (SMOTE) and 0.513 "
                       "(ADASYN); “no balancing” is worse than all three (Nemenyi, p ≤ 0.010). Class weights beat "
                       "ADASYN (p < 10⁻⁴) and are indistinguishable from SMOTE (p = 0.35); SMOTE beats ADASYN "
                       "(p = 0.007). Naive Bayes is the only model whose F1 barely changes with balancing.")),
            ]),
            card(tx("Balancear mueve el umbral, no la capacidad de ordenar",
                    "Balancing moves the threshold, not the ranking ability"), [
                dcc.Graph(id="mdl-scatter", figure=fig_models_scatter(), config=gcfg),
                interp_block(
                    tx(f"Cada punto es una combinación: las {N_BASE} del diseño factorial y las {N_EXTRA} corridas de CS-FOF (rombos). Las que no balancean (gris) quedan abajo: "
                       "aciertan poco con quienes incumplen. Pero no quedan más a la izquierda: ordenan a los clientes "
                       "casi igual de bien; lo que cambia es dónde se pone el corte entre «paga» e «incumple».",
                       f"Each point is one combination: the {N_BASE} from the factorial design and the {N_EXTRA} runs of CS-FOF (diamonds). Those without balancing (grey) sit at the bottom: "
                       "they rarely get defaulters right. But they are not further to the left: they rank clients "
                       "almost equally well; what changes is where the cut between “pays” and “defaults” is placed."),
                    tx("ROC-AUC medio por técnica (96 combinaciones sin SVM): 0.759 sin balanceo, 0.762 con pesos de "
                       "clase, 0.754 con SMOTE y 0.750 con ADASYN. Al umbral de 0.5 el recall pasa de 0.378 a 0.607 y "
                       "la precisión baja de 0.621 a 0.464, así que la ganancia de F1 (0.458 → 0.524) viene en gran "
                       "parte del umbral y no de un modelo que discrimine mejor.",
                       "Mean ROC-AUC by technique (96 combinations without SVM): 0.759 without balancing, 0.762 with "
                       "class weights, 0.754 with SMOTE and 0.750 with ADASYN. At the 0.5 threshold recall goes from "
                       "0.378 to 0.607 and precision drops from 0.621 to 0.464, so the F1 gain (0.458 → 0.524) comes "
                       "largely from the threshold rather than from a model that discriminates better.")),
            ]),
        ], className="grid g2"),
        html.Div([
            card(tx(f"Mayor F1 medio: {best_lbl}", f"Highest mean F1: {best_lbl}"), [
                dcc.Graph(id="mdl-cm", figure=fig_best_cm(), config=gcfg),
                html.Div([
                    kpi("Recall", f"{c['tp'] / pos:.0%}", tx("incumplimientos detectados", "defaults detected"), "target"),
                    kpi(tx("Precisión", "Precision"), f"{c['tp'] / flagged:.0%}",
                        tx("de los señalados sí incumple", "of those flagged do default"), "alert"),
                    kpi(tx("Especificidad", "Specificity"), f"{c['tn'] / (c['tn'] + c['fp']):.0%}",
                        tx("de quienes pagan, bien clasificados", "of payers, correctly classified"), "users"),
                    kpi(tx("Exactitud", "Accuracy"), f"{(c['tp'] + c['tn']) / (pos + c['tn'] + c['fp']):.0%}",
                        tx("de todos los clientes", "of all clients"), "bars"),
                ], className="kpi-row k2 kpi-compact"),
                interp_block(
                    tx(f"De los {pos:,} clientes que incumplieron, el modelo detecta {c['tp']:,} ({c['tp'] / pos:.0%}). "
                       f"A cambio marca {c['fp']:,} falsas alarmas: de los {flagged:,} clientes que señala como "
                       f"riesgosos, {c['tp'] / flagged:.0%} sí incumple.",
                       f"Of the {pos:,} clients who defaulted, the model detects {c['tp']:,} ({c['tp'] / pos:.0%}). "
                       f"In exchange it raises {c['fp']:,} false alarms: of the {flagged:,} clients it flags as risky, "
                       f"{c['tp'] / flagged:.0%} actually default."),
                    tx(f"{tech_lbl(b['technique'])} y optimización {method_lbl(b['method']).lower()}. Predicciones "
                       "out-of-fold de los cinco modelos de los folds externos, con umbral 0.5 (AUC agrupado 0.783). "
                       "Las probabilidades no están calibradas (ECE = 0.180) porque el peso de costo infla la clase "
                       "positiva. Ajustar el umbral según el costo de cada tipo de error es el siguiente paso natural. "
                       f"XGBoost, el mejor modelo de referencia, detecta {XGB_CM['tp']:,} incumplimientos con {XGB_CM['fp']:,} falsas alarmas.",
                       f"{tech_lbl(b['technique'])} and {method_lbl(b['method']).lower()} optimization. Out-of-fold "
                       "predictions from the five outer-fold models, with a 0.5 threshold (pooled AUC 0.783). The "
                       "probabilities are not calibrated (ECE = 0.180) because the cost weight inflates the positive "
                       "class. Tuning the threshold to the cost of each type of error is the natural next step. "
                       f"XGBoost, the best baseline model, detects {XGB_CM['tp']:,} defaults with {XGB_CM['fp']:,} false alarms.")),
            ]),
            card(tx("Qué variables pesan más: SHAP global", "Which variables matter most: global SHAP"), [
                html.Div([control(tx("Modelo", "Model"), dcc.RadioItems(
                    id="shap-model", value="xgboost", className="radio",
                    options=[{"label": "XGBoost", "value": "xgboost"},
                             {"label": "Random Forest", "value": "random_forest"},
                             {"label": "CS-FOF", "value": "cs_fof"}]))], className="controls"),
                dcc.Graph(id="shap-graph", config=gcfg),
                html.Div(id="shap-interp"),
                html.P(tx("Coincide con el EDA: el historial de pagos (PAY_0 primero) es la señal más fuerte del "
                          "incumplimiento, le sigue el límite de crédito, y el perfil demográfico pesa poco.",
                          "This matches the EDA: payment history (PAY_0 first) is the strongest signal of default, "
                          "followed by the credit limit, and the demographic profile matters little."),
                       className="callout"),
            ]),
        ], className="grid g2"),
        card(tx("Diagnóstico del modelo seleccionado", "Diagnostics of the selected model"), [
            html.Div([control(tx("Modelo", "Model"), dcc.RadioItems(
                id="diag-model", value="cs_fof", className="radio",
                options=[{"label": minfo(m, "label"), "value": m} for m in DIAG_MODELS]))], className="controls"),
            dcc.Graph(id="diag-graph", config=gcfg),
            html.Div(id="diag-interp"),
        ]),
        card(tx("Comparación estadística: diagrama de diferencia crítica", "Statistical comparison: critical difference diagram"), [
            html.Div([control(tx("Comparar sobre", "Compare over"), dcc.RadioItems(
                id="cd-src", value="taiwan", className="radio",
                options=[{"label": tx("Taiwán (5 pliegues)", "Taiwan (5 folds)"), "value": "taiwan"},
                         {"label": tx("4 conjuntos de datos", "4 datasets"), "value": "conjuntos"}]))], className="controls"),
            dcc.Graph(id="cd-graph", config=gcfg),
            html.Div(id="cd-interp"),
        ]),
        card(tx("¿LIME y SHAP explican lo mismo?", "Do LIME and SHAP explain the same thing?"), [
            html.Div([
                html.Div([lime_shap_table()]),
                dcc.Graph(id="lime-graph", config=gcfg),
            ], className="grid g2"),
            interp_block(
                tx("Casi siempre coinciden en la dirección: si una variable sube el riesgo para SHAP, también lo "
                   "sube para LIME. Pero no en el orden: comparten entre 3 y 4 de sus 5 variables principales.",
                   "They almost always agree on direction: if a variable raises the risk for SHAP, it also raises "
                   "it for LIME. But not on order: they share 3 to 4 of their top 5 variables."),
                tx("200 observaciones por modelo (10 al azar de cada celda de la matriz de confusión en cada fold) y "
                   "LIME con 3 semillas. Como LIME coincide más consigo mismo (0.85 y 0.88) que con SHAP (0.72 y "
                   "0.63), la diferencia entre métodos no es solo ruido de LIME. El acuerdo es mayor en los "
                   "verdaderos positivos. Solo se comparan orden y signo: SHAP está en log-odds (XGBoost) o "
                   "probabilidad (Random Forest) y LIME en probabilidad.",
                   "200 observations per model (10 at random from each confusion-matrix cell in each fold) and "
                   "LIME with 3 seeds. Since LIME agrees more with itself (0.85 and 0.88) than with SHAP (0.72 and "
                   "0.63), the difference between methods is not just LIME noise. Agreement is highest on true "
                   "positives. Only order and sign are compared: SHAP is in log-odds (XGBoost) or probability "
                   "(Random Forest) and LIME in probability.")),
        ]),
        card(tx("Optimizadores: mismo destino, distinto costo", "Optimizers: same destination, different cost"), [
            html.Div([control(tx("Modelo", "Model"), dcc.RadioItems(
                id="any-model", value="xgboost", className="radio",
                options=[{"label": minfo(m, "label"), "value": m} for m in ANY_MODELS]))], className="controls"),
            html.Div([
                dcc.Graph(id="any-graph", config=gcfg),
                html.Div(id="any-table"),
            ], className="grid g2"),
            html.Div(id="any-interp"),
        ]),
    ])
