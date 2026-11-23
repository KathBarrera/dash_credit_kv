# -*- coding: utf-8 -*-
"""Carga y limpieza del dataset (las mismas decisiones del notebook 00_eda.ipynb) y filtro global del EDA.

DF es la tabla de todos los clientes y no cambia nunca después de cargarse. El filtro del EDA no la
modifica: aplicar_filtro(f) devuelve un subconjunto que cada callback pasa a las figuras como `data=`.
"""

import pandas as pd

from tablero.config import (L, LANG, LOCAL_CANDIDATES, UCI_URL, tx)

TARGET = "default_payment_next_month"
PAY_COLS = ["PAY_0", "PAY_2", "PAY_3", "PAY_4", "PAY_5", "PAY_6"]
BILL_COLS = [f"BILL_AMT{i}" for i in range(1, 7)]
PAYAMT_COLS = [f"PAY_AMT{i}" for i in range(1, 7)]
NUM_COLS = ["LIMIT_BAL", "AGE"] + PAY_COLS + BILL_COLS + PAYAMT_COLS
CAT_COLS = ["SEX", "EDUCATION", "MARRIAGE"]
DISCRETE = CAT_COLS + PAY_COLS + [TARGET]   # variables tratadas como categorías


def _read_any(src):
    """Lee .xls/.xlsx/.csv tolerando la fila extra de encabezado del archivo UCI."""
    s = str(src).lower()
    if s.endswith(".csv"):
        d = pd.read_csv(src)
        if "LIMIT_BAL" not in d.columns:
            d = pd.read_csv(src, header=1)
    else:
        d = pd.read_excel(src, header=1)
        if "LIMIT_BAL" not in d.columns:
            d = pd.read_excel(src, header=0)
    return d


def load_raw():
    """Busca el archivo local; si no existe, lo descarga desde UCI."""
    for p in LOCAL_CANDIDATES:
        if p.exists():
            print(f"[datos] leyendo {p}")
            return _read_any(p)
    print("[datos] archivo local no encontrado; descargando desde UCI ...")
    return _read_any(UCI_URL)


def prepare(raw):
    """Limpieza: nombres, duplicados, categorías no documentadas."""
    d = raw.copy()
    # nombre de la variable objetivo (varía según la fuente)
    tcol = [c for c in d.columns if "default" in str(c).lower()][0]
    d = d.rename(columns={tcol: TARGET, "PAY_1": "PAY_0"})
    d = d.drop(columns=["ID"], errors="ignore")

    info = {"filas_originales": len(d)}
    d = d.drop_duplicates().reset_index(drop=True)             # 35 duplicados exactos
    info["duplicados"] = info["filas_originales"] - len(d)

    # categorías no documentadas -> "Otros" (EDUCATION 0,5,6 -> 4 ; MARRIAGE 0 -> 3)
    info["edu_reagrupadas"] = int(d["EDUCATION"].isin([0, 5, 6]).sum())
    info["mar_reagrupadas"] = int((d["MARRIAGE"] == 0).sum())
    d["EDUCATION"] = d["EDUCATION"].replace({0: 4, 5: 4, 6: 4})
    d["MARRIAGE"] = d["MARRIAGE"].replace({0: 3})

    info["bill_neg_clientes"] = int((d[BILL_COLS] < 0).any(axis=1).sum())
    return d, info


DF, DATA_INFO = prepare(load_raw())

# Grupos de edad (para el análisis AGE vs. PAY)
AGE_BINS = [20, 25, 30, 35, 40, 45, 50, 55, 60, 80]
AGE_LABELS = ["21-25", "26-30", "31-35", "36-40", "41-45",
              "46-50", "51-55", "56-60", "61+"]
DF["AGE_GRP"] = pd.cut(DF["AGE"], bins=AGE_BINS, labels=AGE_LABELS)

# ----- Filtros globales del EDA ------------------------------------------------
# DF no cambia nunca después de cargarse. Cada callback del EDA calcula el subconjunto con
# `aplicar_filtro(f)` y se lo pasa a la función de la figura como `data=`; las funciones lo usan
# en lugar de DF. Así dos peticiones simultáneas (hilos o workers) no comparten ningún estado.
EDA_MIN_ROWS = 200


def aplicar_filtro(f):
    """Subconjunto de DF según el filtro global del EDA (None o vacío = todos los clientes)."""
    if not f:
        return DF
    m = pd.Series(True, index=DF.index)
    for col, key in (("SEX", "sex"), ("EDUCATION", "edu"), ("MARRIAGE", "mar")):
        if f.get(key):
            m &= DF[col].isin(f[key])
    if f.get("age"):
        m &= DF["AGE"].between(*f["age"])
    if f.get("lim"):
        m &= DF["LIMIT_BAL"].between(*f["lim"])
    sub = DF[m]
    return sub if len(sub) >= EDA_MIN_ROWS else DF


# Etiquetas de categorías (es, en)
_CAT_LABELS = {
    "SEX": {1: ("Hombre", "Male"), 2: ("Mujer", "Female")},
    "EDUCATION": {1: ("Posgrado", "Graduate school"), 2: ("Universidad", "University"),
                  3: ("Secundaria", "High school"), 4: ("Otros", "Others")},
    "MARRIAGE": {1: ("Casado", "Married"), 2: ("Soltero", "Single"), 3: ("Otros", "Others")},
    TARGET: {0: ("No default", "No default"), 1: ("Default", "Default")},
}


def cat_labels(col):
    """Etiquetas de las categorías de una variable en el idioma activo."""
    return {k: L(v) for k, v in _CAT_LABELS[col].items()}


# Meses de referencia del dataset (abril–septiembre de 2005)
_M_ES = {1: "Sep", 2: "Ago", 3: "Jul", 4: "Jun", 5: "May", 6: "Abr"}
_M_EN = {1: "Sep", 2: "Aug", 3: "Jul", 4: "Jun", 5: "May", 6: "Apr"}
MONTH_ORDER = ["PAY_6", "PAY_5", "PAY_4", "PAY_3", "PAY_2", "PAY_0"]   # cronológico


def month(i):
    """Mes abreviado: 1 = septiembre … 6 = abril (índice de las columnas del dataset)."""
    return (_M_EN if LANG.get() == "en" else _M_ES)[i]


def month_lbl():
    """Meses en orden cronológico (abril → septiembre)."""
    return [month(i) for i in range(6, 0, -1)]


def pretty(col):
    """Nombre legible de cada variable (para menús y ejes)."""
    if col == "LIMIT_BAL":
        return tx("LIMIT_BAL · Límite de crédito (NT$)", "LIMIT_BAL · Credit limit (NT$)")
    if col == "AGE":
        return tx("AGE · Edad (años)", "AGE · Age (years)")
    if col == "SEX":
        return tx("SEX · Sexo", "SEX · Sex")
    if col == "EDUCATION":
        return tx("EDUCATION · Nivel educativo", "EDUCATION · Education level")
    if col == "MARRIAGE":
        return tx("MARRIAGE · Estado civil", "MARRIAGE · Marital status")
    if col == TARGET:
        return tx("default · Incumplimiento próximo mes", "default · Default next month")
    if col == "PAY_0":
        return tx("PAY_0 · Estado de pago (Sep)", "PAY_0 · Repayment status (Sep)")
    if col.startswith("PAY_AMT"):
        return f"{col} · {tx('Monto pagado', 'Amount paid')} ({month(int(col[-1]))})"
    if col.startswith("PAY_"):
        return f"{col} · {tx('Estado de pago', 'Repayment status')} ({month(int(col[-1]))})"
    if col.startswith("BILL_AMT"):
        return f"{col} · {tx('Monto facturado', 'Bill amount')} ({month(int(col[-1]))})"
    return col


def as_cat(col, data=DF):
    """Devuelve la columna como categoría ordenada con etiquetas legibles."""
    if col in _CAT_LABELS:
        lab = cat_labels(col)
        order = list(lab.values())
        return pd.Categorical(data[col].map(lab), categories=order, ordered=True)
    vals = sorted(data[col].unique())
    return pd.Categorical(data[col].astype(int).astype(str),
                          categories=[str(int(v)) for v in vals], ordered=True)


def cat_order(col, data=DF):
    return list(as_cat(col, data=data).categories)
