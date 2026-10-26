# -*- coding: utf-8 -*-
"""Entrena y SERIALIZA el modelo de la página «Predecir».

Uso (desde la carpeta dash/):
    python -m modelo.entrenar

Necesita `default_of_credit_card_clients.xls` (o .csv) en dash/ o en dash/data/.

Modelo: Random Forest con pesos de clase (class_weight="balanced"), la técnica
de balanceo con la que ganó en el proyecto Credit_Card_Project. Los
hiperparámetros se buscan con RandomizedSearchCV (F1, 3 folds) en el mismo
espacio que usa el proyecto (src/models.py). Se evalúa en un 20 % de prueba
que no participa en la búsqueda.

Salidas (junto a este archivo):
    modelo_credito.pkl    pipeline completo (variables + one-hot + bosque), con joblib
    modelo_credito.json   métricas, hiperparámetros y versiones
"""

import json
import sys
import time
from datetime import date
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn
from scipy.stats import randint
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (average_precision_score, confusion_matrix, f1_score, precision_score,
                             recall_score, roc_auc_score)
from sklearn.model_selection import RandomizedSearchCV, StratifiedKFold, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, OneHotEncoder

from modelo.features import CAT_COLS, INPUT_COLS, preparar_variables

HERE = Path(__file__).resolve().parent
DASH_DIR = HERE.parent
MODEL_PATH = HERE / "modelo_credito.pkl"
META_PATH = HERE / "modelo_credito.json"
TARGET = "default_payment_next_month"
RANDOM_STATE = 42


def cargar_datos():
    for p in [DASH_DIR / "default_of_credit_card_clients.xls", DASH_DIR / "data" / "default_of_credit_card_clients.xls",
              DASH_DIR / "default_of_credit_card_clients.csv", DASH_DIR / "data" / "default_of_credit_card_clients.csv"]:
        if p.exists():
            if p.suffix == ".csv":
                d = pd.read_csv(p)
                if "LIMIT_BAL" not in d.columns:
                    d = pd.read_csv(p, header=1)
            else:
                d = pd.read_excel(p, header=1)
            print(f"[datos] {p}")
            break
    else:
        sys.exit("No se encontró default_of_credit_card_clients.xls en dash/ ni en dash/data/.")
    tcol = [c for c in d.columns if "default" in str(c).lower()][0]
    d = d.rename(columns={tcol: TARGET, "PAY_1": "PAY_0"}).drop(columns=["ID"], errors="ignore")
    # mismo orden del proyecto: reagrupar categorías y luego quitar duplicados exactos
    d["EDUCATION"] = d["EDUCATION"].replace({0: 4, 5: 4, 6: 4})
    d["MARRIAGE"] = d["MARRIAGE"].replace({0: 3})
    d = d.drop_duplicates().reset_index(drop=True)
    return d[INPUT_COLS], d[TARGET].astype(int)


def construir_pipeline():
    return Pipeline([
        ("variables", FunctionTransformer(preparar_variables)),
        ("onehot", ColumnTransformer([("cat", OneHotEncoder(handle_unknown="ignore", drop="if_binary"), CAT_COLS)],
                                     remainder="passthrough")),
        ("modelo", RandomForestClassifier(class_weight="balanced", random_state=RANDOM_STATE, n_jobs=-1)),
    ])


def main(n_iter=20):
    X, y = cargar_datos()
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, stratify=y, random_state=RANDOM_STATE)
    espacio = {   # mismo espacio de src/models.py del proyecto
        "modelo__n_estimators": randint(100, 501),
        "modelo__max_depth": randint(3, 31),
        "modelo__min_samples_split": randint(2, 51),
        "modelo__min_samples_leaf": randint(1, 21),
        "modelo__max_features": ["sqrt", "log2"],
    }
    busqueda = RandomizedSearchCV(construir_pipeline(), espacio, n_iter=n_iter, scoring="f1",
                                  cv=StratifiedKFold(3, shuffle=True, random_state=RANDOM_STATE),
                                  random_state=RANDOM_STATE, n_jobs=1, refit=True)
    t0 = time.time()
    busqueda.fit(X_tr, y_tr)
    modelo = busqueda.best_estimator_
    proba = modelo.predict_proba(X_te)[:, 1]
    pred = (proba >= 0.5).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_te, pred).ravel()

    # --- Serialización (igual que en la guía: joblib.dump / joblib.load) ---
    joblib.dump(modelo, MODEL_PATH, compress=3)

    meta = {
        "modelo": "Random Forest",
        "balanceo": "class_weight='balanced'",
        "busqueda": f"RandomizedSearchCV, {n_iter} combinaciones, F1, 3 folds",
        "hiperparametros": {k.replace("modelo__", ""): (v.item() if hasattr(v, "item") else v)
                            for k, v in busqueda.best_params_.items()},
        "f1_cv": round(float(busqueda.best_score_), 4),
        "prueba": {
            "n": int(len(y_te)),
            "f1": round(f1_score(y_te, pred), 4), "precision": round(precision_score(y_te, pred), 4),
            "recall": round(recall_score(y_te, pred), 4), "roc_auc": round(roc_auc_score(y_te, proba), 4),
            "pr_auc": round(average_precision_score(y_te, proba), 4),
            "matriz_confusion": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)},
        },
        "n_entrenamiento": int(len(y_tr)),
        "tasa_default_entrenamiento": round(float(y_tr.mean()), 4),
        "umbral": 0.5,
        "entradas": INPUT_COLS,
        "versiones": {"python": sys.version.split()[0], "scikit-learn": sklearn.__version__,
                      "numpy": np.__version__, "pandas": pd.__version__, "joblib": joblib.__version__},
        "fecha": date.today().isoformat(),
        "segundos_entrenamiento": round(time.time() - t0, 1),
    }
    META_PATH.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(meta, indent=2, ensure_ascii=False))
    print(f"Modelo guardado en {MODEL_PATH} ({MODEL_PATH.stat().st_size / 1e6:.1f} MB)")

    # --- Verificación: cargar el .pkl y predecir de nuevo ---
    cargado = joblib.load(MODEL_PATH)
    assert np.allclose(cargado.predict_proba(X_te)[:, 1], proba), "El modelo cargado no coincide"
    print("Verificación: el modelo cargado da las mismas predicciones.")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 20)
