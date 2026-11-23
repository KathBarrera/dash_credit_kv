# -*- coding: utf-8 -*-
"""Resultados de los modelos del repositorio Credit_Card_Project (notebooks 04, 05, 06, 07 y 09):
tabla de 112 combinaciones, diagnóstico, SHAP, LIME y curvas anytime.
"""

import json
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from dash import dash_table
from plotly.subplots import make_subplots

from tablero.componentes import _tbl, interp_block
from tablero.config import (
    BASE_DIR, BRIGHT_GOLD, BROWN, CREAM, DEEP_NAVY, GREY_BLUE, L, MID_BLUE, NAVY, PALE_GOLD, SEQ_GOLD,
    WARM_GOLD, WHITE, tx)
from tablero.utilidades import _rgba, style_fig

# results/model_results.csv resume las combinaciones evaluadas con validación cruzada anidada 5 x 5. El tablero usa:
#   - 112 de los 7 modelos base (4 técnicas de balanceo x 4 métodos de optimización);
#   - 4 del modelo original CS-FOF (pesos de clase con los 4 métodos).
# Sale de results/master_table_e3.csv del proyecto (src/build_master_table_e3.py). Las 112 base vienen de
# results/master_table_112.csv (notebook 08_tabla_maestra_svm):
#   - 80 filas en CPU local y 16 de KNN en Colab con GPU (cuML); métricas complementarias
#     de posthoc_metrics. Todas las desviaciones usan ddof=1.
#   - 16 filas de SVM corridas en Colab con GPU (cuML), con el F1 tal como se reportó.
#     f1_cpu_refit_mean es el F1 al reajustarlas con scikit-learn en CPU (mismos
#     hiperparámetros y folds); su PR-AUC también sale de ese reajuste.
# Otros archivos de results/ (notebooks 06 y 09):
#   - shap_by_fold.csv: importancia SHAP media por fold (Random Forest y XGBoost).
#   - lime_vs_shap.csv: acuerdo entre LIME y SHAP en 200 observaciones por modelo.
#   - anytime_curves.csv / anytime_summary.csv: curvas anytime y costo de los optimizadores.
MODEL_RESULTS_PATH = BASE_DIR / "results" / "model_results.csv"
MR = pd.read_csv(MODEL_RESULTS_PATH)
# Alcance del tablero: el modelo original (CS-FOF) frente a los siete modelos de referencia exigidos por el curso.
# El archivo conserva las corridas de CatBoost y LightGBM, que quedan fuera de la comparación.
MR = MR[~MR["model"].isin(["catboost", "lightgbm"])].reset_index(drop=True)
# El PR-AUC de CS-FOF (búsqueda aleatoria) sale del reajuste fuera de pliegue
# (experiments/comparacion_final/delong.py); el de las demás combinaciones nuevas no se calculó (n/d).

MODEL_INFO = {   # textos bilingües (es, en): se leen con minfo(modelo, campo)
    "random_forest": {
        "label": ("Random Forest", "Random Forest"),
        "family": ("Ensamble de árboles (bagging)", "Tree ensemble (bagging)"),
        "desc": ("Promedia muchos árboles entrenados sobre muestras distintas de clientes; capta relaciones no "
                 "lineales entre el historial de pagos y el riesgo.",
                 "Averages many trees trained on different samples of clients; captures non-linear "
                 "relationships between payment history and risk."),
        "note": ("A solo 0.0027 de CS-FOF: una diferencia menor que la variación entre folds. Con sus 16 "
                 "combinaciones tiene el mejor rango medio de los siete modelos base, y es el que usa la página "
                 "Predecir. CS-FOF parte de él y le agrega cortes oblicuos.",
                 "Only 0.0027 behind CS-FOF: a difference smaller than the variation between folds. Across its "
                 "16 combinations it has the best mean rank of the seven base models, and it is the one used by the "
                 "Predict page. CS-FOF starts from it and adds oblique splits.")},
    "xgboost": {
        "label": ("XGBoost", "XGBoost"),
        "family": ("Ensamble de árboles (boosting)", "Tree ensemble (boosting)"),
        "desc": ("Construye árboles en secuencia: cada uno corrige los errores del anterior.",
                 "Builds trees in sequence: each one corrects the errors of the previous one."),
        "note": ("Mayor F1 de los siete modelos de referencia. Con CS-FOF y Random Forest forma un grupo de tres que "
                 "las pruebas no separan: en la práctica empatan.",
                 "Highest F1 of the seven baseline models. With CS-FOF and Random Forest it forms a group of three "
                 "that the tests do not separate: in practice they tie.")},
    "cs_fof": {
        "label": ("CS-FOF (original)", "CS-FOF (original)"),
        "family": ("Modelo original · bosque oblicuo con costo", "Original model · cost-sensitive oblique forest"),
        "desc": ("Bosque aleatorio propio: en cada nodo compara los cortes de una variable con un corte oblicuo "
                 "en la dirección de Fisher, ponderada por el costo de no detectar a quien incumple.",
                 "Our own random forest: at each node it compares single-variable splits with an oblique split "
                 "along the Fisher direction, weighted by the cost of missing a defaulter."),
        "note": ("Programado desde cero con numpy. Tiene el mayor F1 medio (+0.0014 sobre XGBoost) y el mayor "
                 "ROC-AUC, pero la diferencia con XGBoost y Random Forest no es significativa.",
                 "Programmed from scratch with numpy. It has the highest mean F1 (+0.0014 over XGBoost) and the "
                 "highest ROC-AUC, but the difference with XGBoost and Random Forest is not significant.")},
    "svm": {
        "label": ("SVM", "SVM"),
        "family": ("Máquina de vectores de soporte (kernel RBF)", "Support vector machine (RBF kernel)"),
        "desc": ("Busca la frontera que separa mejor a quienes pagan de quienes incumplen, con un margen máximo.",
                 "Looks for the boundary that best separates payers from defaulters, with maximum margin."),
        "note": ("Corrió en Colab con GPU (cuML). Al reajustarlo en CPU con scikit-learn, con los mismos "
                 "hiperparámetros y folds, el F1 sube en promedio 0.009: su mejor combinación pasa de 0.539 a "
                 "0.545, a 0.002 de XGBoost. Aquí se muestra el valor de Colab, tal como se reportó.",
                 "Run on Colab with a GPU (cuML). Refitting it on CPU with scikit-learn, with the same "
                 "hyperparameters and folds, raises F1 by 0.009 on average: its best combination goes from 0.539 "
                 "to 0.545, 0.002 behind XGBoost. The Colab value is shown here, as reported.")},
    "knn": {
        "label": ("KNN", "KNN"),
        "family": ("Vecinos más cercanos", "Nearest neighbors"),
        "desc": ("Clasifica a cada cliente según lo que hicieron los clientes más parecidos a él.",
                 "Classifies each client according to what the most similar clients did."),
        "note": ("Con pesos de clase usa un ajuste propio del proyecto (el voto de cada vecino se pondera por la "
                 "rareza de su clase), no un mecanismo estándar de scikit-learn. Corrió en GPU (cuML), pero sus "
                 "predicciones coinciden con las de scikit-learn en 99.98 % a 100 % de los casos.",
                 "With class weights it uses a project-specific adjustment (each neighbor's vote is weighted by "
                 "the rarity of its class), not a standard scikit-learn mechanism. It ran on a GPU (cuML), but its "
                 "predictions match scikit-learn's in 99.98% to 100% of cases.")},
    "decision_tree": {
        "label": ("Árbol de decisión", "Decision tree"),
        "family": ("Árbol de clasificación", "Classification tree"),
        "desc": ("Una secuencia de preguntas sí/no sobre las variables; fácil de leer, pero inestable.",
                 "A sequence of yes/no questions about the variables; easy to read, but unstable."),
        "note": ("Queda por debajo del grupo superior, aunque la diferencia con Random Forest está justo en el "
                 "límite de la significancia (Nemenyi, p = 0.050) y con XGBoost no lo es (p = 0.12).",
                 "It falls below the top group, although the difference with Random Forest is right at the edge "
                 "of significance (Nemenyi, p = 0.050) and with XGBoost it is not significant (p = 0.12).")},
    "logistic_regression": {
        "label": ("Regresión logística", "Logistic regression"),
        "family": ("Modelo lineal · línea base", "Linear model · baseline"),
        "desc": ("Modelo de referencia: combina las variables de forma lineal para estimar la probabilidad de default.",
                 "Reference model: combines the variables linearly to estimate the probability of default."),
        "note": ("Sin balanceo es la combinación con menor F1 (0.378): solo detecta 27 % de quienes incumplen. "
                 "Con SMOTE o pesos de clase sube a 0.516, con un ROC-AUC casi igual.",
                 "Without balancing it is the combination with the lowest F1 (0.378): it detects only 27% of "
                 "defaulters. With SMOTE or class weights it rises to 0.516, with almost the same ROC-AUC.")},
    "naive_bayes": {
        "label": ("Naive Bayes", "Naive Bayes"),
        "family": ("Probabilístico (gaussiano)", "Probabilistic (Gaussian)"),
        "desc": ("Aplica el teorema de Bayes suponiendo que las variables son independientes entre sí.",
                 "Applies Bayes' theorem assuming the variables are independent of each other."),
        "note": ("Ese supuesto no se cumple con el historial de pagos, muy correlacionado mes a mes; "
                 "por eso el balanceo casi no lo cambia (F1 entre 0.495 y 0.499).",
                 "That assumption does not hold for payment history, which is highly correlated month to month; "
                 "that is why balancing barely changes it (F1 between 0.495 and 0.499).")},
}


def minfo(model, key):
    return L(MODEL_INFO[model][key])


_TECH_LBL = {"none": ("Sin balanceo", "No balancing"), "class_weight": ("Pesos de clase", "Class weights"),
             "smote": ("SMOTE", "SMOTE"), "adasyn": ("ADASYN", "ADASYN")}
TECH_ORDER = ["none", "class_weight", "smote", "adasyn"]
_METHOD_LBL = {"grid_search": ("Grid search", "Grid search"), "random_search": ("Random search", "Random search"),
               "bayesian_optuna": ("Bayesiana (Optuna)", "Bayesian (Optuna)"),
               "genetic_deap": ("Genética (DEAP)", "Genetic (DEAP)")}


# Tiempo de inferencia (ms por 1,000 clientes, 25 columnas, pliegue 0, 4 núcleos), medido en
# experiments/robustez/escalabilidad.csv del proyecto. Solo se midió para los tres mejores modelos.
INFER_MS = {"cs_fof": 253.1, "xgboost": 4.8, "random_forest": 9.4}


def leaderboard():
    """Tabla de líderes: todas las combinaciones, ordenable y filtrable (mejor de cada modelo marcada)."""
    d = MR.copy()
    best = d.loc[d.groupby("model")["f1_mean"].idxmax()].index
    d["mejor"] = np.where(d.index.isin(best), "★", "")
    d = d.sort_values("f1_mean", ascending=False).reset_index(drop=True)
    d["rank"] = np.arange(1, len(d) + 1)
    rows = [{"rank": int(r["rank"]), "mejor": r["mejor"], "modelo": minfo(r["model"], "label"),
             "balanceo": tech_lbl(r["technique"]), "busqueda": method_lbl(r["method"]),
             "f1": f"{r['f1_mean']:.4f} ± {r['f1_std']:.4f}", "f1_num": r["f1_mean"],
             "auc": None if pd.isna(r["roc_auc_mean"]) else round(r["roc_auc_mean"], 4),
             "recall": None if pd.isna(r["recall_mean"]) else round(r["recall_mean"], 4),
             "precision": None if pd.isna(r["precision_mean"]) else round(r["precision_mean"], 4),
             "inferencia": INFER_MS.get(r["model"]) if r["mejor"] else None} for _, r in d.iterrows()]
    cols = [("rank", "#", "numeric"), ("mejor", tx("Mejor", "Best"), "text"), ("modelo", tx("Modelo", "Model"), "text"),
            ("balanceo", tx("Balanceo", "Balancing"), "text"), ("busqueda", tx("Búsqueda", "Search"), "text"),
            ("f1", tx("F1 media ± d.e.", "F1 mean ± s.d."), "text"), ("auc", "AUC-ROC", "numeric"),
            ("recall", "Recall", "numeric"), ("precision", tx("Precisión", "Precision"), "numeric"),
            ("inferencia", tx("Inferencia (ms / 1,000)", "Inference (ms / 1,000)"), "numeric")]
    return dash_table.DataTable(
        id="mdl-leaderboard", data=rows,
        columns=[{"name": n, "id": i, "type": t} for i, n, t in cols],
        sort_action="native", filter_action="native", page_size=10, sort_mode="single",
        filter_options={"case": "insensitive", "placeholder_text": tx("filtrar…", "filter…")},
        style_table={"overflowX": "auto"},
        style_cell={"fontFamily": "inherit", "fontSize": 13, "padding": "6px 10px", "textAlign": "left",
                    "backgroundColor": "var(--surface)", "color": "var(--text)",
                    "border": "1px solid var(--line)"},
        style_header={"fontWeight": 700, "backgroundColor": "rgba(54,69,109,.10)"},
        style_filter={"backgroundColor": "rgba(210,187,137,.12)"},
        style_data_conditional=[{"if": {"filter_query": '{mejor} = "★"'}, "fontWeight": 700},
                                {"if": {"filter_query": '{modelo} contains "CS-FOF"'}, "color": WARM_GOLD}],
    )


def tech_lbl(t):
    return L(_TECH_LBL[t])


def method_lbl(m):
    return L(_METHOD_LBL[m])


# Mejor combinación de cada modelo (por F1 medio), ordenadas de mejor a peor
BEST_BY_MODEL = (MR.loc[MR.groupby("model")["f1_mean"].idxmax()]
                 .sort_values("f1_mean", ascending=False).reset_index(drop=True))
BEST = BEST_BY_MODEL.iloc[0]
# Las 112 combinaciones del diseño factorial (7 modelos base) y, aparte, las corridas de CS-FOF, que buscan
# superar el mejor F1 de esas 112.
BASE_MODELS = ["random_forest", "xgboost", "svm", "knn", "decision_tree", "logistic_regression", "naive_bayes"]
N_BASE = int(MR["model"].isin(BASE_MODELS).sum())
N_EXTRA = len(MR) - N_BASE
BEST_BASE = BEST_BY_MODEL[BEST_BY_MODEL["model"].isin(BASE_MODELS)].iloc[0]
# Tasa de cambio promedio de 2005 (Banco Central de la República de China): 32.2 NT$ por US$
TWD_PER_USD_2005 = 32.2
BASELINE = MR[(MR["model"] == "logistic_regression") & (MR["technique"] == "none")]["f1_mean"].max()
# Matrices de confusión fuera de pliegue (umbral 0.5) de CS-FOF y de XGBoost, el mejor modelo de referencia,
# reajustadas con los hiperparámetros de cada fold (experiments/comparacion_final/probabilidades_oof.npz).
XGB_CM = {"tn": 19087, "fp": 4248, "fn": 2557, "tp": 4073}
CSFOF_CM = {"tn": 19660, "fp": 3675, "fn": 2737, "tp": 3893}
TECH_COLORS = {"none": GREY_BLUE, "class_weight": WARM_GOLD, "smote": DEEP_NAVY, "adasyn": MID_BLUE}


def fig_models_heat():
    """Mejor F1 de cada modelo con cada técnica de balanceo (máximo sobre los 4 métodos)."""
    order = list(BEST_BY_MODEL["model"])
    pv = MR.pivot_table(index="model", columns="technique", values="f1_mean", aggfunc="max").loc[order, TECH_ORDER]
    fig = go.Figure(go.Heatmap(
        z=pv.values, x=[tech_lbl(t) for t in TECH_ORDER], y=[minfo(m, "label") for m in order],
        colorscale=SEQ_GOLD, texttemplate="%{z:.3f}", textfont=dict(size=13), xgap=3, ygap=3,
        showscale=False,   # cada celda ya muestra su valor: sin barra de color hay más ancho
        hovertemplate="%{y} · %{x}<br>" + tx("Mejor F1", "Best F1") + ": %{z:.4f}<extra></extra>"))
    style_fig(fig, 480, legend_top=False)
    fig.update_layout(margin=dict(l=125, r=10, t=30, b=20))
    fig.update_yaxes(autorange="reversed", showgrid=False)
    fig.update_xaxes(side="top", showgrid=False)
    return fig


def fig_models_scatter():
    """Todas las combinaciones: F1 frente a ROC-AUC, coloreadas por técnica de balanceo."""
    fig = go.Figure()
    for t in TECH_ORDER:
        d = MR[MR["technique"] == t]
        fig.add_trace(go.Scatter(
            x=d["roc_auc_mean"], y=d["f1_mean"], mode="markers", name=tech_lbl(t),
            marker=dict(size=9, color=TECH_COLORS[t], opacity=.85, line=dict(width=.6, color=WHITE)),
            customdata=np.stack([d["model"].map(lambda m: minfo(m, "label")),
                                 d["method"].map(method_lbl), d["recall_mean"]], axis=-1),
            hovertemplate="<b>%{customdata[0]}</b> · " + tech_lbl(t) + "<br>%{customdata[1]}"
                          "<br>F1: %{y:.4f}<br>ROC-AUC: %{x:.4f}<br>Recall: %{customdata[2]:.3f}<extra></extra>"))
    # Modelo original: rombos con borde oscuro
    d = MR[MR["model"] == "cs_fof"]
    fig.add_trace(go.Scatter(
        x=d["roc_auc_mean"], y=d["f1_mean"], mode="markers", name="CS-FOF",
        marker=dict(symbol="diamond", size=12, color=WARM_GOLD, line=dict(width=1.6, color=NAVY)),
        customdata=d["method"].map(method_lbl),
        hovertemplate="<b>CS-FOF</b> · %{customdata}<br>F1: %{y:.4f}<br>ROC-AUC: %{x:.4f}<extra></extra>"))
    # Mejor modelo: punto dorado brillante con un halo suave (en vez de estrella)
    fig.add_trace(go.Scatter(
        x=[BEST["roc_auc_mean"]], y=[BEST["f1_mean"]], mode="markers", showlegend=False, hoverinfo="skip",
        marker=dict(size=34, color="rgba(245,196,81,0.28)", line=dict(width=0))))
    fig.add_trace(go.Scatter(
        x=[BEST["roc_auc_mean"]], y=[BEST["f1_mean"]], mode="markers", name=tx("Mejor combinación", "Best combination"),
        marker=dict(symbol="circle", size=17, color=BRIGHT_GOLD, line=dict(width=2, color=WHITE)),
        hovertemplate=f"<b>{tx('Mejor', 'Best')}: {minfo(BEST['model'], 'label')}</b><br>{tech_lbl(BEST['technique'])} · "
                      f"{method_lbl(BEST['method'])}<br>F1: %{{y:.4f}}<br>ROC-AUC: %{{x:.4f}}<extra></extra>"))
    style_fig(fig, 420)
    fig.update_layout(margin=dict(l=60, r=20, t=50, b=55),
                      xaxis_title=tx("ROC-AUC (capacidad de ordenar clientes)", "ROC-AUC (ability to rank clients)"),
                      yaxis_title=tx("F1 de la clase default", "F1 of the default class"))
    return fig


def fig_best_cm():
    """Matriz de confusión out-of-fold de CS-FOF, el modelo de mayor F1 medio (umbral 0.5)."""
    c = CSFOF_CM
    z = [[c["tn"], c["fp"]], [c["fn"], c["tp"]]]
    txt = [[f"<b>{c['tn']:,}</b><br>{tx('Bien clasificados', 'Correctly classified')}",
            f"<b>{c['fp']:,}</b><br>{tx('Falsas alarmas', 'False alarms')}"],
           [f"<b>{c['fn']:,}</b><br>{tx('No detectados', 'Missed')}",
            f"<b>{c['tp']:,}</b><br>{tx('Detectados', 'Detected')}"]]
    fig = go.Figure(go.Heatmap(
        z=z, x=[tx("Predice: paga", "Predicted: pays"), tx("Predice: incumple", "Predicted: defaults")],
        y=[tx("Real: paga", "Actual: pays"), tx("Real: incumple", "Actual: defaults")],
        text=txt, texttemplate="%{text}", textfont=dict(size=13), showscale=False, xgap=4, ygap=4,
        colorscale=[[0, CREAM], [0.25, PALE_GOLD], [1, NAVY]],
        hovertemplate="%{y} · %{x}<br>" + tx("Clientes", "Clients") + ": %{z:,}<extra></extra>"))
    style_fig(fig, 380, legend_top=False)
    fig.update_layout(margin=dict(l=100, r=20, t=30, b=20))
    fig.update_yaxes(autorange="reversed", showgrid=False)
    fig.update_xaxes(side="top", showgrid=False)
    return fig


# ----- Diagnóstico del modelo elegido, diagrama de diferencia crítica y SHAP global de CS-FOF y XGBoost -----
# results/diagnosticos.json lo genera herramientas/diagnosticos_desde_proyecto.py a partir de las predicciones
# fuera de pliegue del proyecto (mejor combinación de cada modelo, mismos 5 pliegues externos).
DIAG = json.loads((BASE_DIR / "results" / "diagnosticos.json").read_text(encoding="utf-8"))
DIAG_MODELS = list(DIAG["modelos"])


def fig_diag(model):
    """ROC, precisión-recall y calibración del modelo elegido frente a CS-FOF (o frente a XGBoost si se elige CS-FOF)."""
    ref = "xgboost" if model == "cs_fof" else "cs_fof"
    fig = make_subplots(rows=1, cols=3, horizontal_spacing=0.09,
                        subplot_titles=(tx("Curva ROC", "ROC curve"), tx("Precisión-recall", "Precision-recall"),
                                        tx("Calibración (10 grupos)", "Calibration (10 bins)")))
    for m, col, dash_ in ((ref, PALE_GOLD if ref == "cs_fof" else GREY_BLUE, "dot"), (model, WARM_GOLD if model == "cs_fof" else NAVY, "solid")):
        d = DIAG["modelos"][m]; nm = minfo(m, "label")
        fig.add_trace(go.Scatter(x=d["roc"][0], y=d["roc"][1], name=nm, legendgroup=m, line=dict(color=col, width=2.5, dash=dash_),
                                 hovertemplate=nm + "<br>FPR %{x:.2f} · TPR %{y:.2f}<extra></extra>"), 1, 1)
        fig.add_trace(go.Scatter(x=d["pr"][0], y=d["pr"][1], name=nm, legendgroup=m, showlegend=False,
                                 line=dict(color=col, width=2.5, dash=dash_),
                                 hovertemplate=nm + "<br>Recall %{x:.2f} · " + tx("precisión", "precision") + " %{y:.2f}<extra></extra>"), 1, 2)
        cal = d["cal"]
        fig.add_trace(go.Scatter(x=[c[0] for c in cal], y=[c[1] for c in cal], name=nm, legendgroup=m, showlegend=False,
                                 mode="lines+markers", line=dict(color=col, width=2.5, dash=dash_), customdata=[c[2] for c in cal],
                                 hovertemplate=nm + "<br>" + tx("Predicho", "Predicted") + " %{x:.2f} · " + tx("observado", "observed")
                                 + " %{y:.2f}<br>%{customdata:,} " + tx("clientes", "clients") + "<extra></extra>"), 1, 3)
    for c in (1, 3):
        fig.add_trace(go.Scatter(x=[0, 1], y=[0, 1], mode="lines", line=dict(color=GREY_BLUE, width=1, dash="dash"),
                                 showlegend=False, hoverinfo="skip"), 1, c)
    fig.add_hline(y=DIAG["tasa"], line=dict(color=GREY_BLUE, width=1, dash="dash"), row=1, col=2)
    style_fig(fig, 380)
    fig.update_xaxes(title_text=tx("Tasa de falsos positivos", "False positive rate"), row=1, col=1)
    fig.update_yaxes(title_text=tx("Tasa de verdaderos positivos", "True positive rate"), row=1, col=1)
    fig.update_xaxes(title_text="Recall", row=1, col=2); fig.update_yaxes(title_text=tx("Precisión", "Precision"), row=1, col=2)
    fig.update_xaxes(title_text=tx("Probabilidad predicha", "Predicted probability"), range=[0, 1], row=1, col=3)
    fig.update_yaxes(title_text=tx("Tasa real de impago", "Observed default rate"), range=[0, 1], row=1, col=3)
    fig.update_layout(margin=dict(l=60, r=20, t=50, b=95),
                      legend=dict(orientation="h", x=0.5, xanchor="center", y=-0.28, yanchor="top"))
    return fig


def diag_interp(model):
    d = DIAG["modelos"][model]; cs = DIAG["modelos"]["cs_fof"]; nm = minfo(model, "label")
    c = d["cm"]; pos = c["tp"] + c["fn"]
    base = tx(f"{nm}: AUC-ROC {d['auc']:.3f}, precisión media (AUC-PR) {d['ap']:.3f}, Brier {d['brier']:.3f} y error de "
              f"calibración ECE {d['ece']:.3f}. Con umbral 0.5 detecta {c['tp']:,} de {pos:,} incumplimientos con "
              f"{c['fp']:,} falsas alarmas.",
              f"{nm}: ROC-AUC {d['auc']:.3f}, average precision (PR-AUC) {d['ap']:.3f}, Brier {d['brier']:.3f} and "
              f"calibration error ECE {d['ece']:.3f}. At the 0.5 threshold it detects {c['tp']:,} of {pos:,} defaults "
              f"with {c['fp']:,} false alarms.")
    if model != "cs_fof":
        base += " " + tx(f"CS-FOF (línea punteada): AUC-ROC {cs['auc']:.3f} y ECE {cs['ece']:.3f}.",
                         f"CS-FOF (dotted line): ROC-AUC {cs['auc']:.3f} and ECE {cs['ece']:.3f}.")
    tech = tx("Predicciones fuera de pliegue de los 29,965 clientes: cada modelo se reentrenó con los hiperparámetros que "
              "eligió en cada pliegue externo. Las curvas ROC y precisión-recall miden cómo ordena a los clientes, sin "
              "depender del umbral; la de calibración compara la probabilidad predicha con la tasa real en 10 grupos (la "
              "diagonal es la calibración perfecta). Todos los modelos con pesos de clase o SMOTE quedan por debajo de la "
              "diagonal: sobreestiman el riesgo.",
              "Out-of-fold predictions for the 29,965 clients: each model was refit with the hyperparameters it chose in "
              "each outer fold. The ROC and precision-recall curves measure how it ranks clients, regardless of the "
              "threshold; the calibration curve compares the predicted probability with the observed rate in 10 bins (the "
              "diagonal is perfect calibration). All models with class weights or SMOTE fall below the diagonal: they "
              "overestimate risk.")
    return interp_block(base, tech)


def fig_cd(fuente):
    """Diagrama de diferencia crítica (Nemenyi) con CS-FOF incluido."""
    F = DIAG["friedman"][fuente]
    r = pd.Series(F["rangos"]).sort_values(); k = len(r); cd = F["cd"]
    fig = go.Figure()
    fig.add_shape(type="line", x0=1, x1=k, y0=0, y1=0, line=dict(color=GREY_BLUE, width=1.5))
    # grupos sin diferencia significativa (barras)
    vals = list(r.values); grupos = []
    for a in range(k):
        b = max(j for j in range(k) if vals[j] - vals[a] <= cd)
        if b > a and (not grupos or b > grupos[-1][1]):
            grupos.append((a, b))
    for g, (a, b) in enumerate(grupos):
        fig.add_shape(type="line", x0=vals[a] - .05, x1=vals[b] + .05, y0=-0.35 - 0.18 * g, y1=-0.35 - 0.18 * g,
                      line=dict(color=NAVY, width=6))
    fig.add_shape(type="line", x0=1, x1=1 + cd, y0=0.9, y1=0.9, line=dict(color=WARM_GOLD, width=4))
    fig.add_annotation(x=1 + cd / 2, y=1.05, text=tx(f"Diferencia crítica = {cd:.2f}", f"Critical difference = {cd:.2f}"),
                       showarrow=False, font=dict(color=WARM_GOLD, size=12))
    fig.add_trace(go.Scatter(
        x=list(r.values), y=[0] * k, mode="markers+text", text=[minfo(m, "label") for m in r.index],
        textposition=["top center" if i % 2 == 0 else "bottom center" for i in range(k)],
        marker=dict(size=[16 if m == "cs_fof" else 11 for m in r.index],
                    color=[WARM_GOLD if m == "cs_fof" else NAVY for m in r.index], line=dict(width=1.5, color=WHITE)),
        textfont=dict(size=11), customdata=list(r.values),
        hovertemplate="%{text}<br>" + tx("Rango medio", "Mean rank") + ": %{customdata:.2f}<extra></extra>", showlegend=False))
    style_fig(fig, 340, legend_top=False)
    fig.update_xaxes(range=[0.5, k + 0.5], dtick=1, title_text=tx("Rango medio (1 = mejor)", "Mean rank (1 = best)"), showgrid=False)
    fig.update_yaxes(visible=False, range=[-0.35 - 0.18 * len(grupos) - 0.2, 1.2])
    fig.update_layout(margin=dict(l=30, r=30, t=30, b=50))
    return fig


def cd_interp(fuente):
    F = DIAG["friedman"][fuente]; r = pd.Series(F["rangos"]).sort_values()
    if fuente == "taiwan":
        base = tx(f"CS-FOF tiene el mejor rango medio ({r['cs_fof']:.1f}), seguido de XGBoost ({r['xgboost']:.1f}) y Random "
                  f"Forest ({r['random_forest']:.1f}). Las barras azules unen modelos que no se distinguen: CS-FOF queda en "
                  "el mismo grupo que esos dos.",
                  f"CS-FOF has the best mean rank ({r['cs_fof']:.1f}), followed by XGBoost ({r['xgboost']:.1f}) and Random "
                  f"Forest ({r['random_forest']:.1f}). The blue bars join models that cannot be told apart: CS-FOF is in "
                  "the same group as those two.")
        tech = tx(f"Friedman sobre los 5 pliegues externos de Taiwán: χ² = {F['chi2']:.1f}, p = {F['p']:.1e}; diferencia "
                  f"crítica de Nemenyi {F['cd']:.2f}. Con un solo conjunto los pliegues no son bloques independientes, así "
                  "que esta vista es descriptiva; la comparación entre conjuntos es la que usa bloques independientes.",
                  f"Friedman over the 5 outer folds of Taiwan: χ² = {F['chi2']:.1f}, p = {F['p']:.1e}; Nemenyi critical "
                  f"difference {F['cd']:.2f}. With a single dataset the folds are not independent blocks, so this view is "
                  "descriptive; the across-datasets comparison is the one with independent blocks.")
    else:
        base = tx(f"En los 4 conjuntos (Taiwán, German, Australian y Polish), XGBoost es primero ({r['xgboost']:.2f}), "
                  f"seguido de Random Forest ({r['random_forest']:.2f}) y de CS-FOF ({r['cs_fof']:.2f}), que pierde terreno "
                  "en Polish, con 4 % de quiebras.",
                  f"Across the 4 datasets (Taiwan, German, Australian and Polish), XGBoost is first ({r['xgboost']:.2f}), "
                  f"followed by Random Forest ({r['random_forest']:.2f}) and CS-FOF ({r['cs_fof']:.2f}), which loses "
                  "ground on Polish, with 4% bankruptcies.")
        tech = tx(f"Friedman con corrección de Iman-Davenport, cada conjunto como bloque: F = {F['F']:.2f}, p = {F['p']:.4f}; "
                  f"diferencia crítica de Nemenyi {F['cd']:.2f}. Con 4 conjuntos la potencia es baja.",
                  f"Friedman with the Iman-Davenport correction, each dataset as a block: F = {F['F']:.2f}, p = {F['p']:.4f}; "
                  f"Nemenyi critical difference {F['cd']:.2f}. With 4 datasets the power is low.")
    return interp_block(base, tech)


def fig_shap_global(model):
    """SHAP por permutación (300 clientes del pliegue externo 1) de CS-FOF, con XGBoost como referencia."""
    S = DIAG["shap_global"]; otro = "xgboost" if model == "cs_fof" else "cs_fof"
    d = pd.DataFrame({"f": S["variables"], "m": S[model], "o": S[otro]}).sort_values("m").tail(10)
    fig = go.Figure()
    fig.add_trace(go.Bar(y=[feat_lbl(f) for f in d.f], x=d.o, orientation="h", name=minfo(otro, "label"),
                         marker_color=PALE_GOLD if otro == "cs_fof" else GREY_BLUE, opacity=.55,
                         hovertemplate="%{y}: %{x:.4f}<extra>" + minfo(otro, "label") + "</extra>"))
    fig.add_trace(go.Bar(y=[feat_lbl(f) for f in d.f], x=d.m, orientation="h", name=minfo(model, "label"),
                         marker_color=WARM_GOLD if model == "cs_fof" else NAVY,
                         hovertemplate="%{y}: %{x:.4f}<extra>" + minfo(model, "label") + "</extra>"))
    style_fig(fig, 400)
    fig.update_layout(barmode="group", margin=dict(l=170, r=20, t=40, b=46),
                      xaxis_title=tx("Importancia media |SHAP| (probabilidad)", "Mean |SHAP| importance (probability)"))
    return fig


def shap_global_interp(model):
    S = DIAG["shap_global"]

    def _p2(m):   # peso de PAY_2 relativo a PAY_0 en el modelo m
        v = dict(zip(S["variables"], S[m]))
        return v["PAY_2"] / v["PAY_0"]
    return interp_block(
        tx(f"CS-FOF y XGBoost usan casi las mismas variables (correlación de Spearman {S['spearman']:.2f} entre sus "
           "importancias): el atraso de septiembre (PAY_0) y el cupo dominan. En CS-FOF el atraso de agosto (PAY_2) pesa "
           f"el {_p2('cs_fof'):.0%} de PAY_0; en XGBoost, el {_p2('xgboost'):.0%}.",
           f"CS-FOF and XGBoost use almost the same variables (Spearman correlation {S['spearman']:.2f} between their "
           "importances): the September delay (PAY_0) and the limit dominate. In CS-FOF the August delay (PAY_2) weighs "
           f"{_p2('cs_fof'):.0%} of PAY_0; in XGBoost, {_p2('xgboost'):.0%}."),
        tx("SHAP por permutación (el mismo explicador para los dos, porque CS-FOF no es un árbol de scikit-learn) en 300 "
           "clientes de prueba del pliegue externo 1, con 50 clientes de fondo; los valores suman exactamente la "
           "probabilidad de cada cliente. Las barras tenues son el otro modelo.",
           "Permutation SHAP (the same explainer for both, because CS-FOF is not a scikit-learn tree) on 300 test clients "
           "of outer fold 1, with 50 background clients; the values add up exactly to each client's probability. The faint "
           "bars are the other model."))


# ----- Interpretabilidad en los 5 folds (06_interpretability, secciones 5 y 6) -----
SHAP_FOLDS = pd.read_csv(BASE_DIR / "results" / "shap_by_fold.csv")
LIME_SHAP = pd.read_csv(BASE_DIR / "results" / "lime_vs_shap.csv")
_FEAT_LBL = {"LIMIT_BAL_LOG": "LIMIT_BAL (log)", "BILL_AMT_MEAN_6M_LOG": ("BILL_AMT media 6 m (log)", "BILL_AMT 6-mo mean (log)"),
             "BILL_AMT_TREND_6M_LOG": ("BILL_AMT tendencia 6 m (log)", "BILL_AMT 6-mo trend (log)"),
             "N_CREDIT_BALANCE_MONTHS": ("Meses con saldo a favor", "Months with credit balance")}


def feat_lbl(f):
    v = _FEAT_LBL.get(f)
    if v is None:
        return f.replace("_LOG", " (log)") if f.endswith("_LOG") else f
    return v if isinstance(v, str) else L(v)


def shap_stability(model):
    """Spearman medio entre folds, Jaccard medio del top 5 y variables que siempre están en el top 5."""
    d = SHAP_FOLDS[SHAP_FOLDS["model"] == model]
    rk = d.pivot_table(index="feature", columns="fold", values="mean_abs_shap")
    folds = list(rk.columns)
    sp = [rk[a].corr(rk[b], method="spearman") for i, a in enumerate(folds) for b in folds[i + 1:]]
    tops = [set(rk[f].nlargest(5).index) for f in folds]
    jac = [len(a & b) / len(a | b) for i, a in enumerate(tops) for b in tops[i + 1:]]
    always = [f for f in rk.mean(axis=1).sort_values(ascending=False).index if all(f in t for t in tops)]
    return float(np.mean(sp)), float(np.mean(jac)), always


def fig_shap_folds(model, top=10):
    """Importancia SHAP (media de |SHAP|) de las variables principales en cada uno de los 5 folds."""
    d = SHAP_FOLDS[SHAP_FOLDS["model"] == model]
    order = d.groupby("feature")["mean_abs_shap"].mean().sort_values(ascending=False).head(top).index[::-1]
    d = d[d["feature"].isin(order)]
    labels = {f: feat_lbl(f) for f in order}
    fig = go.Figure()
    for f in order:   # rango entre folds como una línea tenue
        v = d.loc[d["feature"] == f, "mean_abs_shap"]
        fig.add_trace(go.Scatter(x=[v.min(), v.max()], y=[labels[f]] * 2, mode="lines", showlegend=False,
                                 hoverinfo="skip", line=dict(color=_rgba(DEEP_NAVY, .25), width=6)))
    fig.add_trace(go.Scatter(
        x=d["mean_abs_shap"], y=d["feature"].map(labels), mode="markers", name=tx("Cada fold", "Each fold"),
        marker=dict(size=8, color=NAVY, opacity=.75, line=dict(width=.6, color=WHITE)),
        customdata=np.stack([d["fold"] + 1, d["rank"]], axis=-1),
        hovertemplate="%{y}<br>Fold %{customdata[0]}: %{x:.3f}<br>" + tx("Puesto", "Rank")
                      + " %{customdata[1]}<extra></extra>"))
    mean = d.groupby("feature")["mean_abs_shap"].mean().reindex(order)
    fig.add_trace(go.Scatter(
        x=mean.values, y=[labels[f] for f in order], mode="markers", name=tx("Media de los 5 folds", "Mean of 5 folds"),
        marker=dict(symbol="diamond", size=12, color=WARM_GOLD, line=dict(width=1, color=WHITE)),
        hovertemplate="%{y}<br>" + tx("Media", "Mean") + ": %{x:.3f}<extra></extra>"))
    style_fig(fig, 420)
    unit = tx("log-odds", "log-odds") if model == "xgboost" else tx("probabilidad", "probability")
    fig.update_layout(margin=dict(l=170, r=20, t=50, b=55),
                      xaxis_title=tx(f"Importancia SHAP media |SHAP| ({unit})", f"Mean SHAP importance |SHAP| ({unit})"))
    fig.update_yaxes(showgrid=False)
    return fig


def interp_shap_folds(model):
    sp, jac, always = shap_stability(model)
    alw = ", ".join(feat_lbl(f) for f in always)
    if model == "random_forest":
        basic = tx("En Random Forest la explicación es estable: las cuatro primeras variables (PAY_0, PAY_2, el límite "
                   "de crédito y PAY_3) son las mismas y en el mismo orden en los cinco folds; solo cambia la quinta.",
                   "In Random Forest the explanation is stable: the top four variables (PAY_0, PAY_2, the credit "
                   "limit and PAY_3) are the same and in the same order in all five folds; only the fifth changes.")
    else:
        basic = tx("En XGBoost, PAY_0 es la primera variable en los cinco folds, pero el resto del top 5 cambia: en "
                   "algunos folds PAY_2 y PAY_3 salen y entran los montos pagados. El orden fino de los montos no "
                   "debe interpretarse.",
                   "In XGBoost, PAY_0 is the top variable in all five folds, but the rest of the top 5 changes: in "
                   "some folds PAY_2 and PAY_3 drop out and paid amounts come in. The fine order of the amounts "
                   "should not be interpreted.")
    tech = tx(f"Spearman medio entre folds = {sp:.2f}; Jaccard medio del top 5 = {jac:.2f}; siempre en el top 5: "
              f"{alw}. Cada fold usa los hiperparámetros de su propio bucle interno y SHAP (TreeExplainer, exacto) "
              "sobre 300 clientes de su fold de prueba. Las magnitudes entre folds no son estrictamente comparables; "
              "por eso la estabilidad se juzga por el orden.",
              f"Mean Spearman between folds = {sp:.2f}; mean top-5 Jaccard = {jac:.2f}; always in the top 5: {alw}. "
              "Each fold uses the hyperparameters of its own inner loop and SHAP (TreeExplainer, exact) on 300 "
              "clients from its test fold. Magnitudes across folds are not strictly comparable, so stability is "
              "judged by order.")
    return basic, tech


def lime_shap_table():
    g = LIME_SHAP.groupby("model")[["spearman_abs", "top5_overlap", "sign_agreement_topk",
                                     "lime_seed_topk_overlap"]].mean()
    rows = [(tx("Coinciden en el signo del efecto (top 5)", "Agree on the sign of the effect (top 5)"),
             "sign_agreement_topk", "{:.1%}"),
            (tx("Variables compartidas en el top 5", "Shared variables in the top 5"), "top5_overlap", "{:.2f}"),
            (tx("Correlación de orden (Spearman)", "Rank correlation (Spearman)"), "spearman_abs", "{:.2f}"),
            (tx("LIME consigo mismo entre semillas (top 5)", "LIME with itself across seeds (top 5)"),
             "lime_seed_topk_overlap", "{:.2f}")]
    return _tbl([tx("Medida", "Measure"), "Random Forest", "XGBoost"],
                [(lbl, fmt.format(g.loc["random_forest", c]), fmt.format(g.loc["xgboost", c])) for lbl, c, fmt in rows])


_CELL_LBL = {"TP": ("Verdaderos positivos", "True positives"), "FP": ("Falsas alarmas", "False alarms"),
             "TN": ("Verdaderos negativos", "True negatives"), "FN": ("No detectados", "Missed")}


def fig_lime_cells():
    """Variables principales compartidas por LIME y SHAP (de 5), según la celda de la matriz de confusión."""
    cells = ["TP", "FP", "TN", "FN"]
    g = LIME_SHAP.groupby(["model", "outcome"])["top5_overlap"].mean() * 5
    fig = go.Figure()
    for m, col in (("random_forest", NAVY), ("xgboost", WARM_GOLD)):
        v = [g.get((m, c), np.nan) for c in cells]
        fig.add_trace(go.Bar(x=[L(_CELL_LBL[c]) for c in cells], y=v, name=minfo(m, "label"), marker_color=col,
                             text=[f"{x:.1f}" for x in v], textposition="outside", cliponaxis=False,
                             hovertemplate="<b>" + minfo(m, "label") + "</b> · %{x}<br>"
                                           + tx("Variables compartidas", "Shared variables") + ": %{y:.2f} / 5<extra></extra>"))
    style_fig(fig, 330)
    fig.update_layout(barmode="group", bargap=.3, margin=dict(l=55, r=10, t=50, b=40),
                      yaxis=dict(range=[0, 5], dtick=1, title=tx("Variables compartidas (de 5)", "Shared variables (of 5)")))
    fig.update_xaxes(showgrid=False)
    return fig


# ----- Optimizadores: curvas anytime y multi-fidelidad (09_anytime_multifidelidad) -----
ANYTIME = pd.read_csv(BASE_DIR / "results" / "anytime_curves.csv")
ANYTIME_SUM = pd.read_csv(BASE_DIR / "results" / "anytime_summary.csv")
ANY_METHODS = ["grid_search", "random_search", "bayesian_optuna", "genetic_deap", "hyperband"]
ANY_COLORS = {"grid_search": GREY_BLUE, "random_search": MID_BLUE, "bayesian_optuna": WARM_GOLD,
              "genetic_deap": DEEP_NAVY, "hyperband": BROWN}
_METHOD_LBL["hyperband"] = ("Hyperband (multi-fidelidad)", "Hyperband (multi-fidelity)")
ANY_MODELS = ["xgboost", "decision_tree", "logistic_regression"]


def fig_anytime(model):
    """Arrepentimiento (mejor F1 interno posible - mejor F1 hallado) frente al costo acumulado."""
    d = ANYTIME[ANYTIME["model"] == model]
    fig = go.Figure()
    for m in ANY_METHODS:
        r = d[d["method"] == m].sort_values("cost_s")
        if r.empty:
            continue
        col = ANY_COLORS[m]
        fig.add_trace(go.Scatter(x=list(r["cost_s"]) + list(r["cost_s"][::-1]),
                                 y=list(r["regret_max"]) + list(r["regret_min"][::-1]), fill="toself",
                                 fillcolor=_rgba(col, .10), line=dict(width=0), hoverinfo="skip",
                                 showlegend=False, legendgroup=m))
        fig.add_trace(go.Scatter(x=r["cost_s"], y=r["regret_med"], mode="lines", name=method_lbl(m), legendgroup=m,
                                 line=dict(color=col, width=2.4, dash={"hyperband": "dash", "genetic_deap": "dot"}.get(m, "solid")),
                                 hovertemplate="<b>" + method_lbl(m) + "</b><br>" + tx("Costo", "Cost")
                                               + ": %{x:.0f} s<br>" + tx("Arrepentimiento", "Regret")
                                               + ": %{y:.4f}<extra></extra>"))
    fig.add_hline(y=0.002, line=dict(color=WARM_GOLD, width=1, dash="dot"),
                  annotation_text=tx("objetivo: a 0.002 del mejor", "target: within 0.002 of the best"),
                  annotation_position="top left", annotation_font_size=11)
    style_fig(fig, 460, legend_top=False)
    fig.update_layout(margin=dict(l=60, r=20, t=24, b=40),
                      legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="center", x=0.5),
                      xaxis_title=tx("Costo de cómputo acumulado (s, escala log)", "Cumulative compute cost (s, log scale)"),
                      yaxis_title=tx("Arrepentimiento en F1 interno", "Regret in inner F1"))
    fig.update_xaxes(type="log")
    return fig


def anytime_table(model):
    d = ANYTIME_SUM[ANYTIME_SUM["model"] == model].set_index("method").reindex(ANY_METHODS)
    rows = []
    for m, r in d.iterrows():
        tgt = (f"{r['costo_objetivo_s']:,.0f} s ({int(r['llegan'])}/3)" if r["llegan"] > 0
               else tx("no llega (0/3)", "never (0/3)"))
        rows.append((method_lbl(m), f"{r['evaluaciones']:.0f}", f"{r['costo_total_s']:,.0f} s", tgt,
                     f"{r['f1_externo']:.3f} ± {r['f1_externo_std']:.3f}"))
    return _tbl([tx("Método", "Method"), tx("Evaluaciones", "Evaluations"), tx("Costo total", "Total cost"),
                 tx("Costo hasta el objetivo", "Cost to target"), tx("F1 externo", "Outer F1")], rows)


def interp_anytime(model):
    d = ANYTIME_SUM[ANYTIME_SUM["model"] == model].set_index("method")
    lo, hi = d["f1_externo"].min(), d["f1_externo"].max()
    cheap = d["costo_total_s"].idxmin()
    basic = tx(f"Cada línea muestra qué tan lejos está cada método del mejor resultado posible a medida que gasta "
               f"tiempo de cómputo. Todos terminan muy cerca: el F1 en datos nuevos va de {lo:.3f} a {hi:.3f}. Lo que "
               f"cambia es el costo para llegar; aquí el más barato es {method_lbl(cheap)}.",
               f"Each line shows how far each method is from the best possible result as it spends compute time. "
               f"All of them end very close: the F1 on new data ranges from {lo:.3f} to {hi:.3f}. What changes is the "
               f"cost to get there; here the cheapest is {method_lbl(cheap)}.")
    tech = tx("Mediana y rango entre los folds externos 0 a 2 (de 5), con pesos de clase y una semilla; arrepentimiento = "
              "mejor F1 interno visto por cualquier método a fidelidad completa − mejor F1 del método hasta ese punto. "
              "En la tabla maestra los cuatro optimizadores empatan (Friedman con 28 bloques, p = 0.080; F1 medio entre "
              "0.5022 y 0.5040). Hyperband, implementado desde cero con la fracción de filas como fidelidad, logra un F1 "
              "externo 0.0022 mayor que Random Search (desviación 0.0051, 9 corridas) con un costo 1.12 veces mayor: "
              "no demuestra ventaja.",
              "Median and range over outer folds 0 to 2 (of 5), with class weights and one seed; regret = best inner F1 "
              "seen by any method at full fidelity − the method's best F1 so far. In the master table the four "
              "optimizers tie (Friedman with 28 blocks, p = 0.080; mean F1 between 0.5022 and 0.5040). Hyperband, "
              "implemented from scratch with the fraction of rows as fidelity, reaches an outer F1 0.0022 higher than "
              "Random Search (SD 0.0051, 9 runs) at 1.12 times the cost: it shows no advantage.")
    return basic, tech
