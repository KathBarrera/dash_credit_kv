# -*- coding: utf-8 -*-
"""Variables del modelo: las mismas transformaciones del proyecto Credit_Card_Project.

Réplica fila a fila de `src/preprocessing.py::build_final_dataset` (sin la
deduplicación, que solo aplica al entrenar):

1. EDUCATION 0, 5, 6 -> 4 («Otros») y MARRIAGE 0 -> 3 («Otros»).
2. BILL_AMT1-BILL_AMT6 se resumen en nivel medio (log con signo), tendencia
   mensual (log con signo) y número de meses con saldo a favor.
3. Log con signo de LIMIT_BAL y PAY_AMT1-PAY_AMT6.

Este archivo debe acompañar al .pkl: `joblib.load` necesita importar
`preparar_variables`, que forma parte del pipeline serializado.
"""

import numpy as np
import pandas as pd

PAY_COLS = ["PAY_0", "PAY_2", "PAY_3", "PAY_4", "PAY_5", "PAY_6"]
BILL_COLS = [f"BILL_AMT{i}" for i in range(1, 7)]      # BILL_AMT1 = septiembre (mes más reciente)
PAYAMT_COLS = [f"PAY_AMT{i}" for i in range(1, 7)]
CAT_COLS = ["SEX", "EDUCATION", "MARRIAGE"]
# Columnas de entrada del modelo (las del dataset original de UCI, sin ID ni el objetivo)
INPUT_COLS = ["LIMIT_BAL", "SEX", "EDUCATION", "MARRIAGE", "AGE"] + PAY_COLS + BILL_COLS + PAYAMT_COLS


def signed_log1p(x):
    """sign(x) · log(1 + |x|): tolera ceros y saldos negativos."""
    return np.sign(x) * np.log1p(np.abs(x))


def preparar_variables(X):
    """Convierte las 23 variables originales en las 21 que usa el modelo."""
    d = pd.DataFrame(X, columns=INPUT_COLS).copy()
    d["EDUCATION"] = d["EDUCATION"].replace({0: 4, 5: 4, 6: 4})
    d["MARRIAGE"] = d["MARRIAGE"].replace({0: 3})

    bills = d[BILL_COLS].to_numpy(dtype=float)
    t = np.arange(len(BILL_COLS) - 1, -1, -1, dtype=float)   # BILL_AMT6 -> 0, ..., BILL_AMT1 -> 5
    tc = t - t.mean()
    slope = bills @ tc / (tc @ tc)
    d["BILL_AMT_MEAN_6M_LOG"] = signed_log1p(bills.mean(axis=1))
    d["BILL_AMT_TREND_6M_LOG"] = signed_log1p(slope)
    d["N_CREDIT_BALANCE_MONTHS"] = (bills < 0).sum(axis=1).astype(int)
    d = d.drop(columns=BILL_COLS)

    for c in ["LIMIT_BAL"] + PAYAMT_COLS:
        d[c + "_LOG"] = signed_log1p(d[c].astype(float))
        d = d.drop(columns=c)
    return d
