# -*- coding: utf-8 -*-
"""Exporta el XGBoost entrenado del Dash (dash/modelo/modelo_xgboost.pkl) a archivos que R puede leer.

El .pkl de scikit-learn no se abre en R. En lugar de reentrenar en R (con otro algoritmo y otro resultado),
se exportan los 147 árboles del mismo modelo y shiny/R/06c_xgboost.R los recorre como lo hace XGBoost:

- en cada nodo interno el cliente va a la izquierda si  x[col] < umbral  (comparación en float32, como XGBoost);
- el puntaje es  sigmoide(margen base + suma de los valores de hoja de todos los árboles).

Los umbrales y los valores de hoja se toman del JSON interno del modelo (save_raw), que guarda los float32
exactos; la tabla de trees_to_dataframe los redondea.

Uso (desde la raíz del repositorio):
    python shiny/herramientas/exportar_xgboost.py

Genera en shiny/modelo/:
    xgboost_arboles.bin.gz     nodos de todos los árboles (binario little-endian, comprimido con gzip)
    xgboost_meta.json          columnas, margen base, tamaño de cada árbol y metadatos del Dash (métricas, umbral, conforme)
    xgboost_verificacion.csv   300 clientes de prueba con la probabilidad que da Python, para comprobar la réplica
"""
import gzip
import json
import math
import sys
from pathlib import Path

import joblib
import numpy as np

RAIZ = Path(__file__).resolve().parents[2]
DASH, SALIDA = RAIZ / "dash", RAIZ / "shiny" / "modelo"
sys.path.insert(0, str(DASH))

from modelo.entrenar import RANDOM_STATE, cargar_datos  # noqa: E402
from sklearn.model_selection import train_test_split  # noqa: E402

pipe = joblib.load(DASH / "modelo" / "modelo_xgboost.pkl")
booster = pipe.named_steps["modelo"].get_booster()
modelo = json.loads(booster.save_raw("json"))["learner"]
arboles = modelo["gradient_booster"]["model"]["trees"]
base_score = float(modelo["learner_model_param"]["base_score"].strip("[]"))
margen_base = math.log(base_score / (1 - base_score))         # binary:logistic guarda la base como probabilidad

izq, der, col, defecto_izq, umbral = [], [], [], [], []
for a in arboles:
    izq.append(np.asarray(a["left_children"], dtype="<i4"))   # -1 = hoja (índices locales a cada árbol)
    der.append(np.asarray(a["right_children"], dtype="<i4"))
    col.append(np.asarray(a["split_indices"], dtype="<i4"))
    defecto_izq.append(np.asarray(a["default_left"], dtype="<i4"))
    umbral.append(np.asarray(a["split_conditions"], dtype="<f4"))   # en las hojas, el valor de la hoja
izq, der, col, defecto_izq = map(np.concatenate, (izq, der, col, defecto_izq))
umbral = np.concatenate(umbral)
with gzip.open(SALIDA / "xgboost_arboles.bin.gz", "wb", compresslevel=9) as fh:
    for arr in (izq, der, col, defecto_izq):
        fh.write(np.ascontiguousarray(arr, dtype="<i4").tobytes())
    fh.write(np.ascontiguousarray(umbral, dtype="<f4").tobytes())

columnas = [c.split("__", 1)[1] for c in pipe.named_steps["onehot"].get_feature_names_out()]
cs_fof = json.loads((SALIDA / "cs_fof_meta.json").read_text(encoding="utf-8"))
assert columnas == cs_fof["columnas"], "XGBoost y CS-FOF deben usar las mismas 25 columnas del pipeline"

meta_dash = json.loads((DASH / "modelo" / "modelo_xgboost.json").read_text(encoding="utf-8"))
meta = {
    "columnas": columnas, "margen_base": margen_base,
    "nodos_por_arbol": [len(a["left_children"]) for a in arboles], "n_nodos": int(len(umbral)),
    **{k: meta_dash[k] for k in ("modelo", "balanceo", "busqueda", "hiperparametros", "prueba", "n_entrenamiento",
                                 "tasa_default_entrenamiento", "umbral", "conformal", "umbral_ajustable", "fecha")
       if k in meta_dash},
    "versiones": {"python (entrenamiento)": meta_dash.get("versiones", {})},
}
(SALIDA / "xgboost_meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")

# Verificación de la réplica en R: los mismos 300 clientes de prueba que usa CS-FOF, con la probabilidad de Python
X, y = cargar_datos()
_, X_te, _, _ = train_test_split(X, y, test_size=0.2, stratify=y, random_state=RANDOM_STATE)
v = X_te.sample(300, random_state=0).copy()
v["p_python"] = pipe.predict_proba(v[X.columns])[:, 1]
v.to_csv(SALIDA / "xgboost_verificacion.csv", index=False)

# Comprobación en Python de que la regla de recorrido reproduce a XGBoost
Xt = np.asarray(pipe[:-1].transform(v[X.columns]), dtype=np.float32)
inicio = np.concatenate([[0], np.cumsum(meta["nodos_por_arbol"])[:-1]])
margen = np.full(len(Xt), margen_base, dtype=np.float64)
for o in inicio:
    nodo = np.zeros(len(Xt), dtype=np.int64)
    while True:
        hoja = izq[o + nodo] < 0
        if hoja.all():
            break
        i = np.where(~hoja)[0]
        g = o + nodo[i]
        x = Xt[i, col[g]]
        a_izq = np.where(np.isnan(x), defecto_izq[g] == 1, x < umbral[g])
        nodo[i] = np.where(a_izq, izq[g], der[g])
    margen += umbral[o + nodo].astype(np.float64)
dif = np.abs(1 / (1 + np.exp(-margen)) - v["p_python"].to_numpy()).max()
print("árboles:", len(arboles), "· nodos:", len(umbral), "· margen base:", round(margen_base, 6),
      "· tamaño:", round((SALIDA / "xgboost_arboles.bin.gz").stat().st_size / 1e6, 2), "MB",
      "· diferencia máxima con XGBoost:", f"{dif:.2e}")
