# -*- coding: utf-8 -*-
"""Pipeline del proyecto en código: el botón «Pipeline» y la ventana con el código real que lo implementa.

La ventana muestra, con colores de sintaxis, los fragmentos del repositorio Credit_Card_Project: el preprocesamiento
dentro de cada pliegue, `build_pipeline` (preprocesamiento + balanceo + modelo con imblearn), la validación anidada 5 × 5,
CS-FOF dentro del mismo pipeline, las pruebas estadísticas, HIB (logits fuera de muestra y regla de pesos) y la
serialización con joblib. Los archivos están copiados en modelo/pipeline/ y modelo/hib/ (se muestran sin sus docstrings).

El botón se pone donde haga falta con pipeline_btn(etapa); al pulsarlo se abre la ventana (assets/pipeline.js) y la
sección de esa etapa queda resaltada. El contenido se dibuja en el idioma activo con el callback de callbacks/pipeline.py.
"""

import ast

from dash import html

from tablero.config import BASE_DIR, REPO_PROJECT, tx
from tablero.iconos import icon

SRC = BASE_DIR / "modelo" / "pipeline"
HIB_SRC = (BASE_DIR / "modelo" / "hib" / "hib_regla.txt").read_text(encoding="utf-8")
LEIDOS = {n: (SRC / f"{n}.py.txt").read_text(encoding="utf-8") for n in
          ("balancing", "nested_cv", "preprocessing", "gen_taiwan", "analyze_conf2")}
RAMA_HIB = "claude/wonderful-planck-tq6tc2"
URL = {"balancing": f"{REPO_PROJECT}/blob/main/src/balancing.py", "nested_cv": f"{REPO_PROJECT}/blob/main/src/nested_cv.py",
       "preprocessing": f"{REPO_PROJECT}/blob/main/src/preprocessing.py",
       "gen_taiwan": f"{REPO_PROJECT}/blob/{RAMA_HIB}/entregables_profesor/protocolo_confirmatorio_v2/gen_taiwan.py",
       "analyze_conf2": f"{REPO_PROJECT}/blob/{RAMA_HIB}/entregables_profesor/protocolo_confirmatorio_v2/analyze_conf2.py",
       "hib": f"{REPO_PROJECT}/blob/{RAMA_HIB}/entregables_profesor/protocolo_confirmatorio_v2/hib.py"}

# Etapas que piden los botones «Pipeline» de las páginas (ver pipeline_btn y page_title)
ETAPAS = ("datos", "eda", "base", "cv", "csfof", "pruebas", "explorar", "congelar", "hib", "confirmar", "entrega")

USO_CSFOF = """from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from src.original_model import CSFisherObliqueForest

modelo = make_pipeline(StandardScaler(), CSFisherObliqueForest(
    n_estimators=359, max_depth=11, min_samples_leaf=51, max_features="log2",
    eps=0.324, class_weight="balanced", random_state=42, n_jobs=8))
modelo.fit(X_train, y_train)
riesgo = modelo.predict_proba(X_test)[:, 1]          # puntaje de incumplimiento"""

USO_JOBLIB = """import joblib

joblib.dump(modelo, "modelo/modelo_cs_fof.pkl", compress=3)     # serializar el pipeline completo
modelo = joblib.load("modelo/modelo_cs_fof.pkl")                # cargar en app.py
riesgo = modelo.predict_proba(cliente)[0, 1]                    # predecir en «Predecir\""""


def _funcion(src, nombre, doc=False):
    """Código de una función de nivel superior; por defecto sin su docstring, para que el fragmento quepa en la ventana."""
    for nodo in ast.parse(src).body:
        if isinstance(nodo, ast.FunctionDef) and nodo.name == nombre:
            lineas = src.splitlines()[nodo.lineno - 1:nodo.end_lineno]
            d = nodo.body[0]
            if not doc and isinstance(d, ast.Expr) and isinstance(getattr(d, "value", None), ast.Constant) \
                    and isinstance(d.value.value, str):
                a, b = d.lineno - nodo.lineno, d.end_lineno - nodo.lineno
                lineas = lineas[:a] + lineas[b + 1:]
            return "\n".join(lineas)
    raise KeyError(nombre)


def codigo_pipeline():
    """Los fragmentos de código de la ventana: (id, etapas, título, explicación, archivo (clave de URL, rótulo), código)."""
    prep = _funcion(LEIDOS["preprocessing"], "build_column_transformer") + "\n\n\n" + \
        _funcion(LEIDOS["preprocessing"], "get_preprocessing_steps")
    hib = LEIDOS["gen_taiwan"].rstrip() + "\n\n\n# --- hib.py: la regla de pesos sobre esos logits ---\n" + HIB_SRC.rstrip()
    pruebas = _funcion(LEIDOS["analyze_conf2"], "holm") + "\n\n\n" + _funcion(LEIDOS["analyze_conf2"], "cliff") + """


# extracto abreviado de analyze_conf2.py: Wilcoxon sobre las 25 diferencias de F1 por pliegue; Holm sobre los 7 contrastes
for b in BENCH:
    x = (F1["HIB"] - F1[b]).values
    pw = stats.wilcoxon(F1["HIB"], F1[b]).pvalue
T["holm_P1_wilcoxon"] = holm(T["p_P1_wilcoxon"].values)"""
    return [
        ("prep", "datos eda", tx("1 · Preprocesamiento dentro de cada pliegue", "1 · Preprocessing inside each fold"),
         tx("Codificación one-hot y escalado son un paso más del pipeline: se ajustan solo con el entrenamiento de cada pliegue, nunca con "
            "todo el conjunto, así no hay fuga de datos.",
            "One-hot encoding and scaling are one more pipeline step: they are fitted only on each fold's training set, never on the whole "
            "dataset, so there is no data leakage."), ("preprocessing", "src/preprocessing.py"), prep),
        ("build", "base", tx("2 · build_pipeline: preprocesamiento + balanceo + modelo", "2 · build_pipeline: preprocessing + balancing + model"),
         tx("Un solo Pipeline de imblearn por combinación. SMOTE y ADASYN se ajustan solo con el entrenamiento y se omiten al predecir; "
            "«class_weight» calcula el peso con el y de entrenamiento.",
            "A single imblearn Pipeline per combination. SMOTE and ADASYN are fitted on the training set only and skipped when predicting; "
            "“class_weight” computes the weight from the training y."), ("balancing", "src/balancing.py"),
         _funcion(LEIDOS["balancing"], "build_pipeline")),
        ("cv", "cv", tx("3 · Validación anidada 5 × 5: run_nested_cv", "3 · Nested 5 × 5 validation: run_nested_cv"),
         tx("El bucle externo evalúa y, dentro de cada entrenamiento externo, el interno elige los hiperparámetros con el optimizador "
            "(malla, aleatoria, Optuna o genético). El mejor pipeline se reajusta con todo el entrenamiento externo y se evalúa en el pliegue "
            "de prueba, que nunca se vio.",
            "The outer loop evaluates and, inside each outer training set, the inner one picks the hyperparameters with the optimizer "
            "(grid, random, Optuna or genetic). The best pipeline is refitted on the whole outer training set and evaluated on the test fold, "
            "which was never seen."), ("nested_cv", "src/nested_cv.py"), _funcion(LEIDOS["nested_cv"], "run_nested_cv")),
        ("csfof", "csfof", tx("4 · CS-FOF dentro del mismo pipeline", "4 · CS-FOF inside the same pipeline"),
         tx("El modelo original es un estimador de scikit-learn (fit, predict, predict_proba), así que entra en los mismos pipelines que los "
            "demás.",
            "The original model is a scikit-learn estimator (fit, predict, predict_proba), so it goes into the same pipelines as the others."),
         None, USO_CSFOF),
        ("tests", "pruebas", tx("5 · Pruebas estadísticas: Wilcoxon con Holm", "5 · Statistical tests: Wilcoxon with Holm"),
         tx("Wilcoxon sobre las 25 diferencias de F1 por pliegue, con Holm sobre los 7 contrastes, y el δ de Cliff como tamaño de efecto. "
            "DeLong, McNemar, Friedman y Nadeau-Bengio están en el mismo script.",
            "Wilcoxon on the 25 per-fold F1 differences, with Holm over the 7 contrasts, and Cliff's δ as effect size. DeLong, McNemar, "
            "Friedman and Nadeau-Bengio are in the same script."), ("analyze_conf2", "analyze_conf2.py"), pruebas),
        ("hib", "explorar congelar hib confirmar", tx("6 · Del CS-FOF al HIB: logits fuera de muestra y regla de pesos", "6 · From CS-FOF to HIB: out-of-sample logits and weight rule"),
         tx("Cada miembro (CS-FOF, XGBoost, CatBoost, LightGBM, Random Forest, Extra Trees, HistGradientBoosting y regresión logística) deja sus "
            "logits fuera de muestra con 3 pliegues internos; HIB aprende los pesos con L-BFGS-B para un F1 suave. 5 repeticiones × 5 pliegues, "
            "con semillas fijadas de antemano.",
            "Each member (CS-FOF, XGBoost, CatBoost, LightGBM, Random Forest, Extra Trees, HistGradientBoosting and logistic regression) leaves "
            "its out-of-sample logits with 3 inner folds; HIB learns the weights with L-BFGS-B for a soft F1. 5 repetitions × 5 folds, "
            "with seeds fixed beforehand."), ("gen_taiwan", "gen_taiwan.py"), hib),
        ("entrega", "entrega", tx("7 · Entrega: el pipeline serializado", "7 · Delivery: the serialized pipeline"),
         tx("El pipeline completo se guarda con joblib y la sección «Predecir» de este tablero solo lo carga y predice.",
            "The whole pipeline is saved with joblib and this dashboard's “Predict” section only loads it and predicts."),
         None, USO_JOBLIB),
    ]


def pipeline_btn(etapa="", label=None, cls="", compact=False, title=None):
    """Botón que abre la ventana del pipeline (el código) y resalta la sección de la etapa `etapa`."""
    txt = label if label is not None else tx("Pipeline (código)", "Pipeline (code)")
    return html.Button([icon("pipeline"), html.Span(txt, className="pipe-btn-txt")], type="button",
                       className=f"btn pipe-btn {'compact' if compact else ''} {cls}".strip(),
                       title=title or tx("Ver el código del pipeline del proyecto", "See the code of the project pipeline"),
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
    """Las secciones de código del pipeline, en el idioma activo."""
    from tablero.paginas.modelo_original import py_code   # import tardío: modelo_original importa componentes, que importa este módulo
    out = [html.P(tx("El código real del pipeline, del preprocesamiento a la serialización: se muestra tal como está en el repositorio, sin "
                     "los docstrings. Los botones «Pipeline» del tablero abren esta ventana en la sección que corresponde a la página.",
                     "The real pipeline code, from preprocessing to serialization: shown as it is in the repository, without the "
                     "docstrings. The “Pipeline” buttons across the dashboard open this window at the section matching the page."),
                  className="muted pipe-intro")]
    for sid, etapas, titulo, texto, archivo, codigo in codigo_pipeline():
        cab = [html.H4(titulo), html.P(texto, className="muted")]
        if archivo:
            cab.append(html.A([icon("github"), tx(f"Ver {archivo[1]} en GitHub", f"See {archivo[1]} on GitHub")], href=URL[archivo[0]],
                              target="_blank", rel="noopener noreferrer", className="cs-link"))
        out.append(html.Div([*cab, py_code(codigo)], className="pipe-stage", **{"data-stage": etapas, "id": f"pipe-{sid}"}))
    return out
