# -*- coding: utf-8 -*-
"""Página Conclusiones y resumen del libro del proyecto."""

import numpy as np
import pandas as pd
from dash import dcc, html

from tablero.componentes import (_tbl, _ul, card, kpi, page_title)
from tablero.config import (BOOK_URL, L, NOTEBOOKS, tx)
from tablero.datos import DF, TARGET
from tablero.eda_multi import CORR
from tablero.iconos import icon
from tablero.resultados import (BEST, BEST_BASE, CSFOF_CM, N_BASE, minfo, tech_lbl)
from tablero.utilidades import GLOBAL_RATE, cramers_v


# ---------------------------------------------------------------- Enlaces
def book_summary():
    return card(tx("Sobre el proyecto", "About the project"), [
        html.P(tx("Flujo completo de ciencia de datos y aprendizaje automático para predecir el incumplimiento de pago "
                  "en clientes de tarjetas de crédito, a partir de los 30,000 registros del repositorio UCI.",
                  "A complete data science and machine learning workflow to predict payment default among credit card "
                  "clients, based on the 30,000 records of the UCI repository.")),
        html.P(tx("Incluye un pipeline de extracción, limpieza y transformación (ETL), un análisis exploratorio centrado "
                  "en el desbalance de clases y la multicolinealidad severa entre los montos facturados, y un diseño "
                  "factorial de 112 configuraciones que compara algoritmos, representaciones de variables, técnicas de "
                  "balanceo y optimización (genética y bayesiana), y un modelo original (CS-FOF, un bosque con cortes "
                  "oblicuos sensibles al costo). El resultado mejora el F1 de la "
                  "clase minoritaria y reduce los falsos negativos frente a la regresión logística base.",
                  "It includes an extraction, cleaning and transformation (ETL) pipeline, an exploratory analysis "
                  "focused on class imbalance and the severe multicollinearity among billed amounts, and a factorial "
                  "design of 112 configurations comparing algorithms, feature representations, balancing techniques "
                  "and optimization (genetic and Bayesian), plus an original model (CS-FOF, a forest with "
                  "cost-sensitive oblique splits). The result improves the "
                  "minority-class F1 and reduces false negatives compared with the baseline logistic regression.")),
    ])


PIPE_ICONS = {"00": "receipt", "01": "card", "02": "pos", "03": "chip", "04": "wallet", "05": "cardpay",
              "06": "contactless", "08": "layers", "09": "bars"}


def pipeline_card():
    rows = [html.A([html.Span([icon(PIPE_ICONS.get(n, "card")), html.Span(n, className="nb-n")], className="nb-num"),
                    html.Div([html.Div(L(t), className="nb-t"), html.P(L(d))], className="nb-body"),
                    icon("external", "nb-ext")],
                   href=f if f.startswith("http") else BOOK_URL + "notebooks/" + f, target="_blank",
                   rel="noopener noreferrer", className="nb-row")
            for n, t, f, d in NOTEBOOKS]
    return card(tx("Pipeline completo", "Full pipeline"), html.Div(rows, className="nb-list"))


def page_conclusions():
    """Cierre del proyecto: responde la pregunta de investigación y da veredicto a cada hipótesis."""
    rho = CORR["default"].drop("default")
    r_late = DF.loc[DF["PAY_0"] >= 2, TARGET].mean()
    q = DF.groupby(pd.qcut(DF["LIMIT_BAL"], 4), observed=True)[TARGET].mean()
    med = DF.groupby(TARGET)["LIMIT_BAL"].median()
    cv = {v: cramers_v(pd.crosstab(DF[v], DF[TARGET])) for v in ["SEX", "EDUCATION", "MARRIAGE"]}
    bill = [f"BILL_AMT{i}" for i in range(1, 7)]
    bc = DF[bill].corr(method="spearman").values[np.triu_indices(6, 1)]
    ratio = (1 - GLOBAL_RATE) / GLOBAL_RATE
    c = CSFOF_CM
    pos, flagged = c["tp"] + c["fn"], c["tp"] + c["fp"]
    best_lbl = minfo(BEST["model"], "label")
    tech = tech_lbl(BEST["technique"]).lower()
    yes = html.Span(tx("Se cumple", "Supported"), className="tag verdict")

    hyp = [
        ("H1", tx("El historial reciente de pagos es el factor más asociado al default.",
                  "Recent payment history is the factor most associated with default."), yes,
         tx(f"PAY_0 tiene la correlación más alta con el default (ρ = {rho['PAY_0']:.2f}), seguida de PAY_2 a PAY_4. "
            f"Con 2 o más meses de atraso en septiembre, el {r_late:.0%} incumple.",
            f"PAY_0 has the highest correlation with default (ρ = {rho['PAY_0']:.2f}), followed by PAY_2 to PAY_4. "
            f"With 2 or more months late in September, {r_late:.0%} default.")),
        ("H2", tx("A menor límite de crédito, mayor tasa de default.",
                  "The lower the credit limit, the higher the default rate."), yes,
         tx(f"La tasa baja de {q.iloc[0]:.0%} en el cuartil de límite más bajo a {q.iloc[-1]:.0%} en el más alto. "
            f"Mediana del límite: NT${med[1]:,.0f} (default) frente a NT${med[0]:,.0f} (paga); ρ = {rho['LIMIT_BAL']:.2f}.",
            f"The rate drops from {q.iloc[0]:.0%} in the lowest limit quartile to {q.iloc[-1]:.0%} in the highest. "
            f"Median limit: NT${med[1]:,.0f} (default) vs NT${med[0]:,.0f} (pays); ρ = {rho['LIMIT_BAL']:.2f}.")),
        ("H3", tx("Las variables demográficas se asocian con el default, pero con efecto pequeño.",
                  "Demographic variables are associated with default, but with a small effect."), yes,
         tx(f"Diferencias significativas, pero V de Cramér ≤ {max(cv.values()):.2f} (educación {cv['EDUCATION']:.2f}, "
            f"sexo {cv['SEX']:.2f}, estado civil {cv['MARRIAGE']:.2f}). La edad casi no influye (ρ = {rho['AGE']:.3f}).",
            f"Significant differences, but Cramér's V ≤ {max(cv.values()):.2f} (education {cv['EDUCATION']:.2f}, "
            f"sex {cv['SEX']:.2f}, marital status {cv['MARRIAGE']:.2f}). Age barely matters (ρ = {rho['AGE']:.3f}).")),
        ("H4", tx("Los montos facturados BILL_AMT1 a BILL_AMT6 son muy redundantes entre sí.",
                  "Bill amounts BILL_AMT1 to BILL_AMT6 are highly redundant with each other."), yes,
         tx(f"Correlaciones entre {bc.min():.2f} y {bc.max():.2f} entre meses y VIF mayor a 20 en BILL_AMT2 a BILL_AMT5: "
            "multicolinealidad severa.",
            f"Correlations between {bc.min():.2f} and {bc.max():.2f} across months and VIF above 20 for BILL_AMT2 to BILL_AMT5: "
            "severe multicollinearity.")),
        ("H5", tx("La clase default es minoritaria (desbalance).", "The default class is the minority (imbalance)."),
         yes,
         tx(f"Solo el {GLOBAL_RATE:.1%} incumple ({ratio:.1f} : 1). Sin balanceo el F1 medio es 0.455; con pesos de "
            "clase sube a 0.526, así que corregir el desbalance era necesario.",
            f"Only {GLOBAL_RATE:.1%} default ({ratio:.1f} : 1). Without balancing the mean F1 is 0.455; with class "
            "weights it rises to 0.526, so correcting the imbalance was necessary.")),
    ]

    return html.Div([
        page_title(tx("Conclusiones", "Conclusions"), "", stage="confirmar"),
        card(tx("Respuesta a la pregunta de investigación", "Answer to the research question"), [
            html.Div(tx("El incumplimiento del mes siguiente lo anticipa sobre todo el comportamiento de pago "
                        "reciente: cuántos meses de atraso lleva el cliente, en especial en septiembre. Le sigue, "
                        "con menos fuerza, el límite de crédito (a menor cupo, más riesgo). Los datos demográficos "
                        "aportan muy poco.",
                        "Next month's default is anticipated mainly by recent payment behavior: how many months "
                        "late the client is, especially in September. It is followed, less strongly, by the credit "
                        "limit (the lower the limit, the higher the risk). Demographics add very little."),
                     className="callout"),
            html.P(tx(f"Con esas señales, el modelo con mayor F1 medio ({best_lbl} con {tech}) logra un F1 medio de "
                      f"{BEST['f1_mean']:.3f} en la validación anidada 5 × 5. En sus predicciones fuera de pliegue "
                      f"(una sola corrida, umbral 0.5) detecta {c['tp']:,} de los {pos:,} incumplimientos "
                      f"({c['tp'] / pos:.0%}) y, de cada dos clientes que marca como riesgo, uno realmente incumple "
                      f"({c['tp'] / flagged:.0%}).",
                      f"With those signals, the model with the highest mean F1 ({best_lbl} with {tech}) reaches a mean F1 of "
                      f"{BEST['f1_mean']:.3f} in the nested 5 × 5 validation. In its out-of-fold predictions (a single "
                      f"run, threshold 0.5) it detects {c['tp']:,} of the {pos:,} defaults ({c['tp'] / pos:.0%}) and, "
                      f"out of every two clients it flags as risky, one actually defaults ({c['tp'] / flagged:.0%}).")),
            html.Div([
                kpi(tx("Señal más fuerte", "Strongest signal"), "PAY_0",
                    tx(f"ρ = {rho['PAY_0']:.2f} con el default", f"ρ = {rho['PAY_0']:.2f} with default"), "alert"),
                kpi(tx("Mayor F1 medio", "Highest mean F1"), f"F1 {BEST['f1_mean']:.3f}", f"{best_lbl} · {tech}", "trophy"),
                kpi(tx("Incumplimientos detectados", "Defaults detected"), f"{c['tp'] / pos:.0%}",
                    tx(f"{c['tp']:,} de {pos:,}", f"{c['tp']:,} of {pos:,}"), "target"),
            ], className="kpi-row k3"),
        ]),
        card(tx("Veredicto de las hipótesis", "Hypothesis verdicts"),
             _tbl(["#", tx("Hipótesis", "Hypothesis"), tx("Veredicto", "Verdict"), tx("Evidencia", "Evidence")],
                  [(html.B(a), b, v, e) for a, b, v, e in hyp])),
        card(tx(f"¿Superó CS-FOF a las {N_BASE} combinaciones?", f"Did CS-FOF beat the {N_BASE} combinations?"), [
            html.Div(tx("CS-FOF obtiene el mayor F1 medio, pero no de forma significativa: en la práctica empata con "
                        "XGBoost y Random Forest.",
                        "CS-FOF has the highest mean F1, but not significantly: in practice it ties with XGBoost and "
                        "Random Forest."),
                     className="callout"),
            html.Div([
                kpi(tx(f"Mejor de las {N_BASE}", f"Best of the {N_BASE}"), f"F1 {BEST_BASE['f1_mean']:.3f}",
                    minfo(BEST_BASE["model"], "label") + " · " + tech_lbl(BEST_BASE["technique"]).lower(), "layers"),
                kpi("CS-FOF", "F1 0.548", tx("+0.0014 sobre XGBoost; gana en 4 de 5 pliegues", "+0.0014 over XGBoost; wins in 4 of 5 folds"),
                    "tree"),
                kpi("Random Forest", "F1 0.545", tx("CS-FOF queda +0.0027 por encima; gana en 4 de 5 pliegues",
                                                    "CS-FOF is +0.0027 above; it wins in 4 of 5 folds"), "layers"),
            ], className="kpi-row k3"),
            _ul([tx("Frente a XGBoost y Random Forest, ni Nadeau-Bengio (p > 0.6 con Holm), ni "
                    "Wilcoxon, ni DeLong encuentran diferencias significativas; la diferencia de F1 es menor que 0.003.",
                    "Against XGBoost and Random Forest, neither Nadeau-Bengio (p > 0.6 with Holm), "
                    "nor Wilcoxon, nor DeLong finds significant differences; the F1 difference is below 0.003."),
                 tx("Sí es significativamente mejor que SVM, KNN, el árbol de decisión, la regresión logística y Naive Bayes, "
                    "con tamaños de efecto grandes.",
                    "It is significantly better than SVM, the decision tree, logistic regression and Naive Bayes, with "
                    "large effect sizes."),
                 tx("Aporta estabilidad (la menor variación entre pliegues de los tres mejores) y las probabilidades mejor "
                    "calibradas de esos tres, pero en los otros conjuntos de crédito queda por detrás de XGBoost.",
                    "It brings stability (the lowest variation between folds of the top three) and the best-calibrated "
                    "probabilities of those three, but on the other credit datasets it falls behind XGBoost.")]),
            dcc.Link([tx("Ver el detalle en Modelo original", "See the details in Original model"), icon("arrow")],
                     href="/modelo-original", className="btn"),
        ]),
        card(tx("¿Se pudo mejorar el F1? De CS-FOF a HIB", "Could F1 be raised? From CS-FOF to HIB"), [
            html.Div(tx("A partir del modelo original se hizo un ensamble (stacking) con XGBoost, CatBoost, LightGBM, Random Forest, Extra "
                        "Trees, HistGradientBoosting y regresión logística: HIB. Gana a los 7 modelos base con Wilcoxon-Holm, DeLong y McNemar, "
                        "pero la mejora sobre XGBoost es pequeña.",
                        "From the original model an ensemble (stacking) was built with XGBoost, CatBoost, LightGBM, Random Forest, Extra "
                        "Trees, HistGradientBoosting and logistic regression: HIB. It beats the 7 baseline models with Wilcoxon-Holm, DeLong "
                        "and McNemar, but the improvement over XGBoost is small."), className="callout"),
            html.Div([
                kpi("HIB · F1", "0.5505", tx("+0.0037 sobre XGBoost (0.5468); gana en 21 de 25 pliegues",
                                             "+0.0037 over XGBoost (0.5468); wins 21 of 25 folds"), "trophy"),
                kpi(tx("Wilcoxon con Holm", "Wilcoxon with Holm"), "p = 0.0001",
                    tx("frente a XGBoost; DeLong p = 0.0003 y McNemar p < 0.0001", "vs XGBoost; DeLong p = 0.0003 and McNemar p < 0.0001"), "target"),
                kpi(tx("Frente a un promedio simple", "Against a plain average"), "+0.0004",
                    tx("p = 0.33: la ventaja viene de combinar 8 modelos, no de la regla de pesos",
                       "p = 0.33: the advantage comes from combining 8 models, not from the weighting rule"), "layers"),
            ], className="kpi-row k3"),
            _ul([tx("Nadeau-Bengio, que corrige la dependencia entre pliegues, no rechaza frente a XGBoost (p = 0.049 sin ajustar, no sobrevive a Holm).",
                    "Nadeau-Bengio, which corrects for dependence between folds, does not reject against XGBoost (p = 0.049 unadjusted, it does not survive Holm)."),
                 tx("Los modelos alcanzan una meseta de F1 ≈ 0.55 y AUC ≈ 0.78: el límite está en la información de las variables, no en el modelo.",
                    "The models reach a plateau of F1 ≈ 0.55 and AUC ≈ 0.78: the limit is in the information in the variables, not in the model.")]),
            dcc.Link([tx("Ver el detalle en «Del CS-FOF al HIB»", "See the details in “From CS-FOF to HIB”"), icon("arrow")],
                     href="/modelo-original", className="btn"),
        ]),
        html.Div([
            card(tx("Qué significa para el banco", "What it means for the bank"), _ul([
                tx("Vigilar el atraso reciente como alerta temprana: un cliente con 2 o más meses de atraso merece "
                   "cobranza preventiva antes del siguiente corte.",
                   "Monitor recent delays as an early warning: a client 2 or more months late deserves preventive "
                   "collection before the next billing cycle."),
                tx("Revisar con más cuidado los cupos bajos, donde se concentra la mayor tasa de incumplimiento.",
                   "Review low limits more carefully, where the highest default rate is concentrated."),
                tx(f"Usar el modelo como filtro, no como decisión final: marca a {flagged:,} clientes y "
                   f"{c['fp']:,} de ellos sí pagarían, así que la alerta debe pasar por un analista.",
                   f"Use the model as a filter, not as the final decision: it flags {flagged:,} clients and "
                   f"{c['fp']:,} of them would pay, so the alert should go through an analyst."),
                tx("No basar decisiones en sexo, edad o estado civil: aportan poco y crean riesgo de discriminación.",
                   "Do not base decisions on sex, age or marital status: they add little and create a "
                   "discrimination risk."),
            ])),
            card(tx("Limitaciones y próximos pasos", "Limitations and next steps"), _ul([
                tx("Las 112 combinaciones comparan los siete modelos de referencia exigidos por el curso. CatBoost y LightGBM "
                   "entran solo como miembros del ensamble HIB y como referencias, sin el mismo presupuesto de ajuste.",
                   "The 112 combinations compare the seven baseline models required by the course. CatBoost and LightGBM "
                   "enter only as members of the HIB ensemble and as references, without the same tuning budget."),
                tx("Datos de un solo banco de Taiwán en 2005: antes de usarlo en otro mercado hay que reentrenarlo con "
                   "datos actuales.",
                   "Data from a single Taiwanese bank in 2005: before using it in another market it must be retrained "
                   "with current data."),
                tx("El análisis es asociativo: muestra qué anticipa el default, no qué lo causa.",
                   "The analysis is associative: it shows what anticipates default, not what causes it."),
                tx("Las métricas de la validación usan el umbral 0.5. En «Predecir» el umbral es ajustable y muestra "
                   "su efecto en recall, precisión y falsas alarmas; fijarlo con el costo real de cada error (un "
                   "incumplimiento no detectado cuesta más que una falsa alarma) es el paso siguiente para usarlo.",
                   "Validation metrics use the 0.5 threshold. In “Predict” the threshold is adjustable and shows its "
                   "effect on recall, precision and false alarms; setting it with the real cost of each error (a "
                   "missed default costs more than a false alarm) is the next step to use it."),
                tx("Sumar variables que hoy no están (ingresos, deudas en otras entidades) y vigilar que el modelo no "
                   "pierda precisión con el tiempo.",
                   "Add variables that are missing today (income, debts at other institutions) and monitor that the "
                   "model does not lose accuracy over time."),
            ])),
        ], className="grid g2"),
    ])
