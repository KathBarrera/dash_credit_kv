"""Calibra la predicción conforme del modelo del tablero (se ejecuta una vez, no en el servidor).

Predicción conforme Mondrian (por clase) con alfa = 0.10: el conjunto de predicción de un cliente
contiene cada clase c cuyo puntaje de no conformidad 1 - p_c no supera el cuantil q_c calculado con
clientes de esa clase. Así la cobertura de 90 % se garantiza en ambas clases.

La partición de prueba del entrenamiento (20 %, semilla 42) nunca se usó para ajustar el modelo. Se
divide en dos mitades estratificadas: una calibra q_0 y q_1 y la otra verifica la cobertura empírica.
Los resultados se guardan en modelo_credito.json (clave "conformal").

Uso (desde dash/): python -m modelo.conformal
"""
import json

import joblib
import numpy as np
from sklearn.model_selection import train_test_split

from modelo.entrenar import META_PATH, MODEL_PATH, RANDOM_STATE, cargar_datos

ALFA = 0.10


def cuantil(s, alfa):
    n = len(s)
    return float(np.quantile(s, min(1.0, np.ceil((n + 1) * (1 - alfa)) / n), method="higher"))


def main():
    X, y = cargar_datos()
    _, X_te, _, y_te = train_test_split(X, y, test_size=0.2, stratify=y, random_state=RANDOM_STATE)
    X_cal, X_ver, y_cal, y_ver = train_test_split(X_te, y_te, test_size=0.5, stratify=y_te, random_state=RANDOM_STATE)
    modelo = joblib.load(MODEL_PATH)
    p_cal, p_ver = modelo.predict_proba(X_cal)[:, 1], modelo.predict_proba(X_ver)[:, 1]
    y_cal, y_ver = y_cal.to_numpy(), y_ver.to_numpy()
    q0 = cuantil(p_cal[y_cal == 0], ALFA)            # 1 - (1 - p) = p
    q1 = cuantil(1 - p_cal[y_cal == 1], ALFA)
    incl0, incl1 = p_ver <= q0, 1 - p_ver <= q1      # la clase entra al conjunto si su puntaje cabe
    cubre = np.where(y_ver == 1, incl1, incl0)
    tam = incl0.astype(int) + incl1.astype(int)
    res = {"alfa": ALFA, "cobertura_nominal": 1 - ALFA, "q0": round(q0, 6), "q1": round(q1, 6),
           "solo_no_incumple_si_p_menor_que": round(1 - q1, 4), "solo_incumple_si_p_mayor_que": round(q0, 4),
           "n_calibracion": int(len(y_cal)), "n_verificacion": int(len(y_ver)),
           "cobertura_empirica": round(float(cubre.mean()), 4),
           "cobertura_no_incumple": round(float(cubre[y_ver == 0].mean()), 4),
           "cobertura_incumple": round(float(cubre[y_ver == 1].mean()), 4),
           "tamano_medio": round(float(tam.mean()), 4), "fraccion_un_solo_valor": round(float((tam == 1).mean()), 4),
           "fraccion_vacio": round(float((tam == 0).mean()), 4)}
    meta = json.loads(META_PATH.read_text(encoding="utf-8"))
    meta["conformal"] = res
    META_PATH.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(res, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
