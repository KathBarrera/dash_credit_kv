"""Umbral de decisión ajustable para «Predecir» (se ejecuta una vez, no en el servidor).

Usa la misma división de la partición de prueba que la predicción conforme (``modelo/conformal.py``):
- mitad de calibración: se elige el umbral recomendado, el que maximiza el F1 de la clase de impago;
- mitad de verificación: se mide qué pasa con cada umbral (recall, precisión, F1, falsas alarmas).
Así el umbral recomendado no se elige y se evalúa con los mismos clientes.

Guarda en el .json de cada modelo la clave "umbral_ajustable" (umbral recomendado y curva de 5 % a 95 %).
Uso (desde dash/): python -m modelo.umbral [rf catboost cs_fof]
"""
import json
import sys

import joblib
import numpy as np
from sklearn.metrics import f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split

from modelo.conformal import rutas
from modelo.entrenar import RANDOM_STATE, cargar_datos

GRILLA = np.round(np.arange(0.05, 0.951, 0.01), 2)


def metricas(y, p, u):
    pred = (p >= u).astype(int)
    return {"umbral": float(u), "recall": round(recall_score(y, pred, zero_division=0), 4),
            "precision": round(precision_score(y, pred, zero_division=0), 4),
            "f1": round(f1_score(y, pred, zero_division=0), 4),
            "marcados": round(float(pred.mean()), 4),
            "falsas_alarmas_por_100": round(float(((pred == 1) & (y == 0)).sum() / len(y) * 100), 2)}


def main(claves):
    X, y = cargar_datos()
    _, X_te, _, y_te = train_test_split(X, y, test_size=0.2, stratify=y, random_state=RANDOM_STATE)
    X_cal, X_ver, y_cal, y_ver = train_test_split(X_te, y_te, test_size=0.5, stratify=y_te, random_state=RANDOM_STATE)
    y_cal, y_ver = y_cal.to_numpy(), y_ver.to_numpy()
    for clave in claves:
        model_path, meta_path = rutas(clave)
        modelo = joblib.load(model_path)
        p_cal, p_ver = modelo.predict_proba(X_cal)[:, 1], modelo.predict_proba(X_ver)[:, 1]
        f1_cal = [f1_score(y_cal, (p_cal >= u).astype(int), zero_division=0) for u in GRILLA]
        u_rec = float(GRILLA[int(np.argmax(f1_cal))])
        res = {"recomendado": u_rec, "criterio": "máximo F1 en la mitad de calibración de la prueba",
               "n_calibracion": int(len(y_cal)), "n_verificacion": int(len(y_ver)),
               "en_recomendado": metricas(y_ver, p_ver, u_rec), "en_0_5": metricas(y_ver, p_ver, 0.5),
               "curva": [metricas(y_ver, p_ver, u) for u in GRILLA]}
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        meta["umbral_ajustable"] = res
        meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
        print(clave, "recomendado", u_rec, "verificación:", res["en_recomendado"], "| con 0.5:", res["en_0_5"])


if __name__ == "__main__":
    main(sys.argv[1:] or ["rf", "catboost", "cs_fof"])
