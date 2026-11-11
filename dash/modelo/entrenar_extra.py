"""Entrena los otros dos modelos del selector de «Predecir»: CatBoost (mejor global) y CS-FOF (original).

Se ejecuta una vez, fuera del servidor; el tablero solo carga los .pkl.

- Mismas variables y la misma partición 80/20 (semilla 42) que el Random Forest de ``entrenar.py``, para
  que las métricas de prueba de los tres modelos sean comparables.
- Hiperparámetros FIJOS: los del artefacto final de cada modelo en el proyecto
  (``artifacts/metadata_catboost.json`` y ``artifacts/metadata.json`` de Credit_Card_Project), que salen de
  la validación anidada 5 × 5. Aquí no hay búsqueda de hiperparámetros.
- Pesos de clase en ambos (la mejor técnica de balanceo de los dos en la validación anidada).

Uso (desde dash/): python -m modelo.entrenar_extra && python -m modelo.conformal
"""
import json
import sys
import time
from datetime import date

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.compose import ColumnTransformer
from sklearn.metrics import (average_precision_score, confusion_matrix, f1_score, precision_score,
                             recall_score, roc_auc_score)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, OneHotEncoder

from modelo.entrenar import HERE, RANDOM_STATE, cargar_datos
from modelo.features import CAT_COLS, INPUT_COLS, preparar_variables

# Hiperparámetros finales del proyecto (artifacts/ de Credit_Card_Project)
PARAMS = {
    "catboost": {"bagging_temperature": 0.230893825622149, "depth": 5, "iterations": 466,
                 "l2_leaf_reg": 5.408216580718498, "learning_rate": 0.03243662696724643,
                 "random_strength": 3.159255390701748},
    "cs_fof": {"eps": 0.3241326804195627, "max_depth": 11, "max_features": "log2", "min_samples_leaf": 51,
               "n_estimators": 359},
}
NOMBRE = {"catboost": "CatBoost", "cs_fof": "CS-FOF (modelo original)"}


def estimador(clave):
    if clave == "catboost":
        from catboost import CatBoostClassifier
        return CatBoostClassifier(auto_class_weights="Balanced", random_seed=RANDOM_STATE, thread_count=1,
                                  verbose=0, allow_writing_files=False, **PARAMS["catboost"])
    from modelo.cs_fof.original_model import CSFisherObliqueForest
    return CSFisherObliqueForest(class_weight="balanced", random_state=RANDOM_STATE, n_jobs=1, **PARAMS["cs_fof"])


def pipeline(clave):
    return Pipeline([
        ("variables", FunctionTransformer(preparar_variables)),
        ("onehot", ColumnTransformer([("cat", OneHotEncoder(handle_unknown="ignore", drop="if_binary"), CAT_COLS)],
                                     remainder="passthrough")),
        ("modelo", estimador(clave)),
    ])


def main(claves):
    X, y = cargar_datos()
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, stratify=y, random_state=RANDOM_STATE)
    for clave in claves:
        t0 = time.time()
        modelo = pipeline(clave).fit(X_tr, y_tr)
        seg = round(time.time() - t0, 1)
        ruta = HERE / f"modelo_{clave}.pkl"
        joblib.dump(modelo, ruta, compress=3)
        proba = modelo.predict_proba(X_te)[:, 1]
        pred = (proba >= 0.5).astype(int)
        tn, fp, fn, tp = confusion_matrix(y_te, pred).ravel()
        ida_y_vuelta = bool(np.array_equal(proba, joblib.load(ruta).predict_proba(X_te)[:, 1]))
        meta = {
            "modelo": NOMBRE[clave], "balanceo": "pesos de clase (balanced)",
            "busqueda": "sin búsqueda: hiperparámetros finales de la validación anidada 5 × 5 del proyecto",
            "hiperparametros": PARAMS[clave],
            "prueba": {"n": int(len(y_te)), "f1": round(f1_score(y_te, pred), 4),
                       "precision": round(precision_score(y_te, pred), 4), "recall": round(recall_score(y_te, pred), 4),
                       "roc_auc": round(roc_auc_score(y_te, proba), 4),
                       "pr_auc": round(average_precision_score(y_te, proba), 4),
                       "matriz_confusion": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)}},
            "n_entrenamiento": int(len(y_tr)), "tasa_default_entrenamiento": round(float(y_tr.mean()), 4),
            "umbral": 0.5, "entradas": INPUT_COLS, "prueba_ida_y_vuelta": ida_y_vuelta,
            "versiones": {"python": sys.version.split()[0], "scikit-learn": sklearn.__version__,
                          "numpy": np.__version__, "pandas": pd.__version__, "joblib": joblib.__version__},
            "fecha": date.today().isoformat(), "segundos_entrenamiento": seg,
            "tamano_mb": round(ruta.stat().st_size / 2**20, 2),
        }
        if clave == "catboost":
            import catboost
            meta["versiones"]["catboost"] = catboost.__version__
        (HERE / f"modelo_{clave}.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
        print(clave, json.dumps(meta["prueba"]), "ida y vuelta", ida_y_vuelta, meta["tamano_mb"], "MB", seg, "s")


if __name__ == "__main__":
    main(sys.argv[1:] or ["catboost", "cs_fof"])
