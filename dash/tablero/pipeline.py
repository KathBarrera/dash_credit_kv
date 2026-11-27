# -*- coding: utf-8 -*-
"""Pipeline del proyecto: el botón «Pipeline» y la ventana con todas las etapas, de los datos al tablero.

El botón se pone donde haga falta con pipeline_btn(etapa); al pulsarlo se abre la ventana (assets/pipeline.js)
y la etapa pedida queda resaltada. El contenido se dibuja en el idioma activo con el callback de callbacks/pipeline.py.
"""

from dash import dcc, html

from tablero.config import L, tx
from tablero.iconos import icon

# (id, fase, número, (título es, en), (texto es, en), [cifras], (ruta del tablero, (rótulo es, en)) o None)
FASES = [
    ("datos", ("A · Datos y validación", "A · Data and validation")),
    ("modelos", ("B · Modelos de referencia y modelo original", "B · Baseline models and original model")),
    ("mejora", ("C · Mejora del F1: de CS-FOF a HIB", "C · Improving F1: from CS-FOF to HIB")),
    ("entrega", ("D · Entrega", "D · Delivery")),
]

ETAPAS = [
    ("datos", "datos", ("Datos", "Data"),
     ("UCI «Default of Credit Card Clients» (Yeh y Lien, 2009): clientes de un banco de Taiwán entre abril y septiembre de 2005. "
      "Se quitan los duplicados, se reagrupan las categorías sin documentar de EDUCATION y MARRIAGE y se resumen las seis "
      "facturas en tres variables; cupo y pagos pasan a logaritmo.",
      "UCI “Default of Credit Card Clients” (Yeh and Lien, 2009): clients of a Taiwanese bank between April and September 2005. "
      "Duplicates are removed, the undocumented categories of EDUCATION and MARRIAGE are regrouped and the six bills are "
      "summarized in three variables; limit and payments go to logarithms."),
     ["30 000 → 29 965", ("20 variables", "20 variables"), ("22.1 % default", "22.1% default")],
     ("/introduccion", ("Ver Introducción", "See Introduction"))),
    ("eda", "datos", ("Análisis exploratorio", "Exploratory analysis"),
     ("EDA univariado y multivariado con filtros globales: χ² con V de Cramér, Mann-Whitney, t de Welch, Kruskal-Wallis, "
      "correlación de Spearman, multicolinealidad de las facturas y desbalance de clases. Cada hallazgo decide un paso del preprocesamiento.",
      "Univariate and multivariate EDA with global filters: χ² with Cramér's V, Mann-Whitney, Welch's t, Kruskal-Wallis, "
      "Spearman correlation, collinearity of the bills and class imbalance. Each finding drives a preprocessing step."),
     [("PAY_0 = señal dominante", "PAY_0 = dominant signal"), ("ρ de Spearman", "Spearman ρ")],
     ("/univariado", ("Ver EDA", "See EDA"))),
    ("cv", "datos", ("Validación anidada 5 × 5", "Nested 5 × 5 validation"),
     ("5 pliegues externos estratificados evalúan y, dentro de cada entrenamiento, 5 internos eligen los hiperparámetros (semilla 42). "
      "Escalado, balanceo y umbral de decisión se ajustan solo con el entrenamiento del pliegue: no hay fuga de datos. "
      "Métrica principal: F1 de la clase default.",
      "5 stratified outer folds evaluate and, inside each training set, 5 inner folds choose the hyperparameters (seed 42). "
      "Scaling, balancing and the decision threshold are fitted only on the fold's training set: no data leakage. "
      "Main metric: F1 of the default class."),
     [("5 × 5 = 25 evaluaciones", "5 × 5 = 25 evaluations"), ("umbral en el bucle interno", "threshold in the inner loop")], None),
    ("base", "modelos", ("112 combinaciones de referencia", "112 baseline combinations"),
     ("7 modelos (Naive Bayes, regresión logística, árbol, Random Forest, XGBoost, KNN y SVM) × 4 técnicas de balanceo (ninguna, SMOTE, "
      "ADASYN y pesos de clase) × 4 optimizadores (malla, aleatoria, Optuna y genético). La mejor: XGBoost con pesos de clase, F1 0.5466.",
      "7 models (Naive Bayes, logistic regression, tree, Random Forest, XGBoost, KNN and SVM) × 4 balancing techniques (none, SMOTE, "
      "ADASYN and class weights) × 4 optimizers (grid, random, Optuna and genetic). The best: XGBoost with class weights, F1 0.5466."),
     ["7 × 4 × 4 = 112", ("mejor F1 0.5466", "best F1 0.5466")],
     ("/modelos", ("Ver Modelos", "See Models"))),
    ("csfof", "modelos", ("Modelo original: CS-FOF", "Original model: CS-FOF"),
     ("Bosque aleatorio con cortes oblicuos de Fisher ponderados por costo, programado desde cero con numpy, con el mismo presupuesto de "
      "búsqueda que los demás, 14 pruebas unitarias y estudios de ablación. F1 0.5479: el mayor, pero sin diferencia significativa con XGBoost.",
      "Random forest with cost-weighted Fisher oblique cuts, written from scratch with numpy, with the same search budget as the "
      "others, 14 unit tests and ablation studies. F1 0.5479: the highest, but not significantly different from XGBoost."),
     ["F1 0.5479", "ROC-AUC 0.785"],
     ("/modelo-original", ("Ver Modelo original", "See Original model"))),
    ("pruebas", "modelos", ("Pruebas estadísticas", "Statistical tests"),
     ("Friedman con Nemenyi, t corregida de Nadeau-Bengio, Wilcoxon con Holm, DeLong (AUC) y McNemar, más el tamaño de efecto δ de Cliff. "
      "Nadeau-Bengio es la más conservadora porque tiene en cuenta que los pliegues comparten datos.",
      "Friedman with Nemenyi, Nadeau-Bengio corrected t, Wilcoxon with Holm, DeLong (AUC) and McNemar, plus Cliff's δ effect size. "
      "Nadeau-Bengio is the most conservative because it accounts for folds sharing data."),
     ["Wilcoxon-Holm", "DeLong", "McNemar", "Friedman"], None),
    ("explorar", "mejora", ("Del CS-FOF a los ensambles", "From CS-FOF to ensembles"),
     ("Como CS-FOF empató con XGBoost, se combinó con XGBoost, CatBoost, LightGBM, Random Forest, Extra Trees, HistGradientBoosting y "
      "regresión logística para subir el F1: promedios, logit ponderado, pesos por PAY_0 y selección de Caruana, con 45 variables "
      "(las 20 base más razones de facturas y pagos). 2 582 combinaciones en 10 pliegues de desarrollo.",
      "Since CS-FOF tied with XGBoost, it was combined with XGBoost, CatBoost, LightGBM, Random Forest, Extra Trees, HistGradientBoosting "
      "and logistic regression to raise F1: averages, weighted logit, weights by PAY_0 and Caruana selection, with 45 variables "
      "(the 20 base plus bill and payment ratios). 2,582 combinations on 10 development folds."),
     [("2 582 combinaciones", "2,582 combinations"), ("8 miembros", "8 members"), ("45 variables", "45 variables")],
     ("/modelo-original", ("Ver pestaña «Del CS-FOF al HIB»", "See the “From CS-FOF to HIB” tab"))),
    ("congelar", "mejora", ("Candidatos congelados", "Frozen candidates"),
     ("Los 13 mejores candidatos se congelan antes de probarlos con semillas nuevas. Todos quedan +0.003 a +0.004 de F1 sobre XGBoost: "
      "significativo con Wilcoxon-Holm, pero no con Nadeau-Bengio.",
      "The 13 best candidates are frozen before testing them with new seeds. All end up +0.003 to +0.004 F1 above XGBoost: "
      "significant with Wilcoxon-Holm, but not with Nadeau-Bengio."),
     [("13 candidatos", "13 candidates"), ("25 pliegues", "25 folds")], None),
    ("hib", "mejora", ("HIB: ensamble con pesos para un F1 suave", "HIB: ensemble with weights for a soft F1"),
     ("HIB toma los logits fuera de muestra de los 8 modelos y aprende sus pesos con L-BFGS-B para maximizar un F1 suave, con una "
      "penalización que los acerca al promedio uniforme (τ = 0.3, λ = 0.05). El umbral final maximiza el F1 duro.",
      "HIB takes the out-of-sample logits of the 8 models and learns their weights with L-BFGS-B to maximize a soft F1, with a "
      "penalty pulling them toward the uniform average (τ = 0.3, λ = 0.05). The final threshold maximizes the hard F1."),
     [("8 miembros", "8 members"), "τ = 0.3", "λ = 0.05"],
     ("/modelo-original", ("Ver HIB", "See HIB"))),
    ("confirmar", "mejora", ("Confirmación pre-registrada", "Pre-registered confirmation"),
     ("Dos corridas con protocolo fijado antes de generar los datos (v1: semillas 5000–5004; v2: 7100–7104), de 5 × 5 pliegues. HIB frente a los 7 "
      "modelos base con Wilcoxon-Holm, DeLong y McNemar y Friedman global: gana a los 7. Frente a XGBoost, +0.0037 de F1.",
      "Two runs with the protocol fixed before generating the data (v1: seeds 5000–5004; v2: 7100–7104), of 5 × 5 folds. HIB against the 7 "
      "baseline models with Wilcoxon-Holm, DeLong and McNemar and global Friedman: it beats all 7. Against XGBoost, +0.0037 F1."),
     ["F1 0.5505", ("+0.0037 vs XGBoost", "+0.0037 vs XGBoost"), ("gana a los 7", "beats all 7")],
     ("/modelo-original", ("Ver resultados", "See results"))),
    ("entrega", "entrega", ("Interpretación y entrega", "Interpretation and delivery"),
     ("SHAP y LIME, predicción conforme y calibración. Los modelos XGBoost y CS-FOF se serializan con joblib y alimentan el formulario "
      "«Predecir» de este tablero (Dash en Render, con una versión en R + Shiny).",
      "SHAP and LIME, conformal prediction and calibration. The XGBoost and CS-FOF models are serialized with joblib and feed the "
      "“Predict” form of this dashboard (Dash on Render, with an R + Shiny version)."),
     ["joblib (.pkl)", "Dash + Plotly", "ES / EN"],
     ("/predecir", ("Ver Predecir", "See Predict"))),
]


def pipeline_btn(etapa="", label=None, cls="", compact=False, title=None):
    """Botón que abre la ventana del pipeline y resalta la etapa `etapa` (por ejemplo «hib»)."""
    txt = label if label is not None else tx("Pipeline del proyecto", "Project pipeline")
    return html.Button([icon("pipeline"), html.Span(txt, className="pipe-btn-txt")], type="button",
                       className=f"btn pipe-btn {'compact' if compact else ''} {cls}".strip(),
                       title=title or tx("Ver el pipeline del proyecto, de los datos al tablero",
                                         "See the project pipeline, from data to dashboard"),
                       **{"data-pipe-open": etapa})


def pipeline_modal():
    """La ventana (cerrada) del pipeline; su contenido lo escribe el callback según el idioma."""
    return html.Div([
        html.Div(className="pipe-bg", **{"data-pipe-close": "1"}),
        html.Div([
            html.Div([html.H3(id="pipe-title"),
                      html.Button(icon("close"), type="button", id="pipe-close", className="icon-btn",
                                  **{"data-pipe-close": "1", "aria-label": "Cerrar / Close"})], className="pipe-head"),
            html.Div(id="pipe-body", className="pipe-body"),
        ], className="pipe-dialog", role="dialog", **{"aria-modal": "true", "aria-labelledby": "pipe-title"}),
    ], id="pipe-modal", className="pipe-modal")


def pipeline_body():
    """Las etapas del pipeline, agrupadas por fase, en el idioma activo."""
    out = [html.P(tx("De los datos al tablero: cada etapa dice qué se hizo y dónde verlo. Los botones «Pipeline» del tablero "
                     "abren esta ventana en la etapa que se está mirando.",
                     "From data to dashboard: each stage says what was done and where to see it. The “Pipeline” buttons "
                     "across the dashboard open this window at the stage being viewed."), className="muted pipe-intro")]
    n = 0
    for fid, ftitle in FASES:
        items = []
        for eid, fase, title, text, chips, link in ETAPAS:
            if fase != fid:
                continue
            n += 1
            body = [html.Div([html.Span(str(n), className="pipe-num"), html.H4(L(title))], className="pipe-st-head"),
                    html.P(L(text)),
                    html.Div([html.Span(L(c), className="pipe-chip") for c in chips], className="pipe-chips")]
            if link:
                body.append(dcc.Link([L(link[1]), icon("arrow")], href=link[0], className="pipe-link"))
            items.append(html.Div(body, className="pipe-stage", **{"data-stage": eid}))
        out.append(html.Div([html.H5(L(ftitle), className=f"pipe-phase pipe-phase-{fid}"),
                             html.Div(items, className="pipe-flow")], className="pipe-group"))
    return out
