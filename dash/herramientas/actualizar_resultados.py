# -*- coding: utf-8 -*-
"""Copia al tablero los resultados del repositorio Credit_Card_Project (corrida 5 x 5).

Uso (desde la carpeta dash/):
    python herramientas/actualizar_resultados.py RUTA/Credit_Card_Project/results results

Genera en results/:
    model_results.csv    tabla maestra de las 112 combinaciones (master_table_112.csv)
    shap_by_fold.csv     importancia SHAP media por fold (Random Forest y XGBoost)
    lime_vs_shap.csv     acuerdo entre LIME y SHAP en 200 observaciones por modelo
    anytime_curves.csv   mediana y rango del arrepentimiento entre folds, frente al costo
    anytime_summary.csv  evaluaciones, costo, costo hasta el objetivo y F1 externo por método

Las curvas y el resumen anytime se calculan igual que en notebooks/09_anytime_multifidelidad.ipynb.
"""
import glob
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

EPS = 0.002   # "cerca del mejor": a menos de 0.002 de F1 interno de la referencia


def _leer(src, patron):
    return pd.concat([pd.read_csv(f) for f in sorted(glob.glob(str(src / patron)))], ignore_index=True)


def tabla_modelos(src, out):
    m = pd.read_csv(src / "master_table_112.csv")
    mr = m[["model", "technique", "method", "f1_mean", "f1_std", "precision_mean", "recall_mean",
            "roc_auc_mean", "pr_auc_mean"]].copy()
    mr["f1_cpu_refit_mean"] = m["f1_cpu_refit_mean"]   # solo SVM: F1 al reajustar en CPU con scikit-learn
    mr["origen"] = m["source"].map({"local_cpu_sklearn": "local", "colab_gpu_cuml": "colab_gpu"}).fillna(m["source"])
    mr = mr.sort_values("f1_mean", ascending=False).round(4)
    mr.to_csv(out / "model_results.csv", index=False)
    return mr


def interpretabilidad(src, out):
    sh = _leer(src, "interpretability/shap_importance_by_fold_*.csv")
    sh[["model", "fold", "feature", "mean_abs_shap", "rank"]].round(5).to_csv(out / "shap_by_fold.csv", index=False)
    lv = _leer(src, "interpretability/lime_vs_shap_*.csv")
    lv[["model", "fold", "outcome", "spearman_abs", "top5_overlap", "sign_agreement_topk",
        "lime_seed_topk_overlap"]].round(4).to_csv(out / "lime_vs_shap.csv", index=False)


def anytime(src, out):
    tr = _leer(src, "anytime/trace__*.csv")
    fi = _leer(src, "anytime/final__*.csv")
    # Referencia por (modelo, fold): mejor score interno visto por cualquier método a fidelidad completa.
    ref = tr[tr["fidelity"] >= 1.0].groupby(["model", "fold"])["score"].max().rename("reference")
    tr = tr.merge(ref, on=["model", "fold"])
    tr["regret"] = tr["reference"] - tr["best_so_far"]

    filas = []
    for model, sub in tr.groupby("model"):
        grid = np.logspace(np.log10(max(sub["cum_cost_seconds"].min(), 0.1)),
                           np.log10(sub["cum_cost_seconds"].max()), 80)
        for method, run in sub.groupby("method"):
            curvas = []
            for _, r in run.groupby(["fold", "seed"]):
                r = r.dropna(subset=["regret"]).sort_values("cum_cost_seconds")
                curvas.append(np.interp(grid, r["cum_cost_seconds"], r["regret"], left=np.nan))
            a = np.array(curvas)
            fin = run.groupby(["fold", "seed"])["cum_cost_seconds"].max().min()   # termina cuando termina el método
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")   # nanmedian sobre tramos sin datos
                med, lo, hi = np.nanmedian(a, 0), np.nanmin(a, 0), np.nanmax(a, 0)
            for x, m_, l_, h_ in zip(grid, med, lo, hi):
                if x <= fin and not np.isnan(m_):
                    filas.append((model, method, x, m_, l_, h_))
    pd.DataFrame(filas, columns=["model", "method", "cost_s", "regret_med", "regret_min", "regret_max"]) \
        .round(5).to_csv(out / "anytime_curves.csv", index=False)

    res = []
    for (model, fold, seed, method), r in tr.groupby(["model", "fold", "seed", "method"]):
        hit = r[r["regret"] <= EPS]
        res.append({"model": model, "fold": fold, "seed": seed, "method": method,
                    "cost_to_target": hit["cum_cost_seconds"].min() if len(hit) else np.nan})
    res = pd.DataFrame(res).merge(
        fi[["model", "fold", "seed", "method", "n_evaluations", "total_cost_seconds", "outer_f1"]],
        on=["model", "fold", "seed", "method"])
    t = (res.groupby(["model", "method"])
         .agg(evaluaciones=("n_evaluations", "mean"), costo_total_s=("total_cost_seconds", "mean"),
              costo_objetivo_s=("cost_to_target", "median"),
              llegan=("cost_to_target", lambda s: int(s.notna().sum())),
              f1_externo=("outer_f1", "mean"), f1_externo_std=("outer_f1", lambda s: s.std(ddof=1)))
         .round(4).reset_index())
    t.to_csv(out / "anytime_summary.csv", index=False)
    return t


def main(src, out):
    src, out = Path(src), Path(out)
    out.mkdir(parents=True, exist_ok=True)
    mr = tabla_modelos(src, out)
    interpretabilidad(src, out)
    t = anytime(src, out)
    print(f"Listo: {len(mr)} combinaciones y {len(t)} filas de resumen anytime en {out}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
