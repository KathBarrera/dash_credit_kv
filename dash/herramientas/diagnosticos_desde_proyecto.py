"""Genera results/diagnosticos.json para la página Modelos (se ejecuta una vez, no en el servidor).

Lee las predicciones fuera de pliegue de CS-FOF y de los 7 modelos de referencia del proyecto Credit_Card_Project (mejor combinación
de cada uno, hiperparámetros de cada pliegue externo, mismos 5 pliegues) y guarda, por modelo:
- curva ROC y curva precisión-recall (reducidas a ~150 puntos), AUC-ROC y precisión media;
- curva de calibración con 10 bins, Brier y ECE;
- matriz de confusión con umbral 0.5.
También copia los rangos de Friedman (Taiwán, 5 pliegues, y 4 conjuntos de datos) y el SHAP global por
permutación de CS-FOF y XGBoost.

Uso (desde dash/): python -m herramientas.diagnosticos_desde_proyecto RUTA/AL/Credit_Card_Project
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import (average_precision_score, brier_score_loss, confusion_matrix, precision_recall_curve,
                             roc_auc_score, roc_curve)

DASH = Path(__file__).resolve().parents[1]
MODELOS = ["cs_fof", "xgboost", "random_forest", "svm", "knn", "decision_tree",
           "logistic_regression", "naive_bayes"]


def reducir(x, y, n=150):
    i = np.unique(np.linspace(0, len(x) - 1, n).round().astype(int))
    return [round(float(v), 4) for v in np.asarray(x)[i]], [round(float(v), 4) for v in np.asarray(y)[i]]


def ece(y, p, bins=10):
    b = np.minimum((p * bins).astype(int), bins - 1)
    return float(sum(abs(p[b == k].mean() - y[b == k].mean()) * (b == k).mean() for k in range(bins) if (b == k).any()))


def main(proyecto):
    P = Path(proyecto)
    oof = dict(np.load(P / "experiments/comparacion_final/probabilidades_oof.npz"))
    oof.update(dict(np.load(P / "experiments/paper/probabilidades_oof_extra.npz")))
    y = oof["y"].astype(int)
    out = {"n": int(len(y)), "tasa": float(y.mean()), "modelos": {}}
    for m in MODELOS:
        p = oof[m]
        fpr, tpr, _ = roc_curve(y, p); pr, rc, _ = precision_recall_curve(y, p)
        bins = np.minimum((p * 10).astype(int), 9)
        cal = [(float(p[bins == k].mean()), float(y[bins == k].mean()), int((bins == k).sum())) for k in range(10) if (bins == k).sum() >= 30]
        tn, fp, fn, tp = confusion_matrix(y, p >= 0.5).ravel()
        out["modelos"][m] = dict(roc=reducir(fpr, tpr), pr=reducir(rc[::-1], pr[::-1]), auc=float(roc_auc_score(y, p)),
                                 ap=float(average_precision_score(y, p)), brier=float(brier_score_loss(y, p)), ece=ece(y, p),
                                 cal=cal, cm=dict(tn=int(tn), fp=int(fp), fn=int(fn), tp=int(tp)))
    # Friedman y Nemenyi con CS-FOF y los siete modelos de referencia exigidos (experiments/paper/friedman_exigidos.json)
    fe = json.loads((P / "experiments/paper/friedman_exigidos.json").read_text())
    tw, cj = fe["taiwan"], fe["conjuntos"]
    out["friedman"] = {"taiwan": dict(rangos=tw["rangos"], cd=tw["nemenyi_cd"], chi2=tw["chi2"], p=tw["p_chi2"], n=tw["n"]),
                       "conjuntos": dict(rangos=cj["rangos"], cd=cj["nemenyi_cd"], F=cj["iman_davenport_F"], p=cj["p_F"], n=cj["n"])}
    # SHAP global por permutación de CS-FOF frente a XGBoost, el mejor modelo de referencia
    W = pd.read_csv(P / "experiments/robustez/shap_cs_fof_xgboost.csv", index_col=0)
    res = json.loads((P / "experiments/robustez/shap_resumen_xgboost.json").read_text())
    out["shap_global"] = {"variables": list(W.index), "cs_fof": [round(float(v), 5) for v in W.cs_fof],
                          "xgboost": [round(float(v), 5) for v in W.xgboost], "spearman": res["spearman_importancias"]}
    (DASH / "results" / "diagnosticos.json").write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
    print("ok", (DASH / "results" / "diagnosticos.json").stat().st_size // 1024, "KB")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "../../credit_card_project")
