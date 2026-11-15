# -*- coding: utf-8 -*-
"""Exporta el CS-FOF entrenado del Dash (dash/modelo/modelo_cs_fof.pkl) a archivos que R puede leer.

El .pkl de scikit-learn no se abre en R, pero CS-FOF es un modelo propio con una estructura simple: cada
árbol guarda, por nodo, las columnas que usa, sus coeficientes, el umbral, los hijos y el valor de hoja.
shiny/R/07_predecir.R recorre esos árboles igual que `_ArbolCSFOF.proba1` y da las mismas probabilidades.

Uso (desde la raíz del repositorio):
    python shiny/herramientas/exportar_cs_fof.py

Genera en shiny/modelo/:
    cs_fof_bosque.bin.gz    nodos de todos los árboles (binario little-endian, comprimido con gzip)
    cs_fof_meta.json        columnas del one-hot, estandarización, tamaño de cada árbol y metadatos del Dash
    cs_fof_verificacion.csv 300 clientes de prueba con la probabilidad que da Python, para comprobar la réplica
    particion_dash.csv.gz   los 29,965 clientes con su conjunto (entrenamiento, calibración o verificación)
"""
import gzip
import json
import sys
from pathlib import Path

import joblib
import numpy as np

RAIZ = Path(__file__).resolve().parents[2]
DASH, SALIDA = RAIZ / "dash", RAIZ / "shiny" / "modelo"
sys.path.insert(0, str(DASH))

from modelo.entrenar import RANDOM_STATE, cargar_datos  # noqa: E402
from sklearn.model_selection import train_test_split  # noqa: E402

pipe = joblib.load(DASH / "modelo" / "modelo_cs_fof.pkl")
enc = pipe.named_steps["onehot"].named_transformers_["cat"]
bosque = pipe.named_steps["modelo"]
arboles = bosque.arboles_
ancho = arboles[0].feat_.shape[1]

feat = np.concatenate([a.feat_.astype("<i4") for a in arboles])          # (nodos, ancho), -1 = sin columna
coef = np.concatenate([a.coef_.astype("<f8") for a in arboles])
thr = np.concatenate([a.thr_.astype("<f8") for a in arboles])
izq = np.concatenate([a.izq_.astype("<i4") for a in arboles])            # índices locales a cada árbol, -1 = hoja
der = np.concatenate([a.der_.astype("<i4") for a in arboles])
valor = np.concatenate([a.valor_.astype("<f8") for a in arboles])
with gzip.open(SALIDA / "cs_fof_bosque.bin.gz", "wb", compresslevel=9) as fh:
    for arr in (feat.ravel(order="C"), izq, der):
        fh.write(np.ascontiguousarray(arr, dtype="<i4").tobytes())
    for arr in (coef.ravel(order="C"), thr, valor):
        fh.write(np.ascontiguousarray(arr, dtype="<f8").tobytes())

meta_dash = json.loads((DASH / "modelo" / "modelo_cs_fof.json").read_text(encoding="utf-8"))
meta = {
    "columnas": [c.split("__", 1)[1] for c in pipe.named_steps["onehot"].get_feature_names_out()],
    "categorias": {c: [int(v) for v in cats] for c, cats in zip(["SEX", "EDUCATION", "MARRIAGE"], enc.categories_)},
    "descartada": {c: (None if d is None else int(enc.categories_[i][int(d)]))
                   for i, (c, d) in enumerate(zip(["SEX", "EDUCATION", "MARRIAGE"], enc.drop_idx_))},
    "media": bosque.media_.tolist(), "escala": bosque.escala_.tolist(),
    "ancho": int(ancho), "nodos_por_arbol": [int(len(a.thr_)) for a in arboles], "n_nodos": int(len(thr)),
    **{k: meta_dash[k] for k in ("modelo", "balanceo", "busqueda", "hiperparametros", "prueba", "n_entrenamiento",
                                 "tasa_default_entrenamiento", "umbral", "conformal", "umbral_ajustable", "fecha")
       if k in meta_dash},
    "versiones": {"python (entrenamiento)": meta_dash.get("versiones", {})},
}
(SALIDA / "cs_fof_meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")

# Partición del Dash (80/20 estratificada, semilla 42; la prueba se divide en calibración y verificación):
# el Random Forest de R (modelo/entrenar_modelo.R) se entrena y evalúa con los mismos clientes.
X, y = cargar_datos()
X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, stratify=y, random_state=RANDOM_STATE)
X_cal, X_ver, _, _ = train_test_split(X_te, y_te, test_size=0.5, stratify=y_te, random_state=RANDOM_STATE)
part = X.copy()
part["default_payment_next_month"] = y
part["conjunto"] = "entrenamiento"
part.loc[X_cal.index, "conjunto"] = "calibracion"
part.loc[X_ver.index, "conjunto"] = "verificacion"
part.to_csv(SALIDA / "particion_dash.csv.gz", index=False, compression="gzip")

# Verificación de la réplica en R: 300 clientes de prueba con la probabilidad de Python
v = X_te.sample(300, random_state=0).copy()
v["p_python"] = pipe.predict_proba(v[X.columns])[:, 1]
v.to_csv(SALIDA / "cs_fof_verificacion.csv", index=False)
print("árboles:", len(arboles), "· nodos:", len(thr), "· tamaño:",
      round((SALIDA / "cs_fof_bosque.bin.gz").stat().st_size / 1e6, 1), "MB")
