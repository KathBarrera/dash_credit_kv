# -*- coding: utf-8 -*-
"""Utilidades: formato de números, estadísticos (Tukey, V de Cramér) y estilo común de las figuras."""

import numpy as np
from scipy import stats

from tablero.config import DEEP_NAVY, DEEP_RGBA, WHITE
from tablero.datos import DF, TARGET


def nt(x):
    """Formato de dinero en dólares taiwaneses."""
    return f"-NT${abs(x):,.0f}" if x < 0 else f"NT${x:,.0f}"


def sig(p):
    return "p<0.001" if p < 0.001 else f"p={p:.3f}"


def is_money(col):
    return col == "LIMIT_BAL" or col.startswith("BILL_AMT") or col.startswith("PAY_AMT")


def fmt_val(col, v):
    return nt(v) if is_money(col) else f"{v:,.1f}"


def style_fig(fig, h=460, legend_top=True, **kw):
    """Estilo común de todas las figuras."""
    fig.update_layout(
        height=h, margin=dict(l=55, r=30, t=70, b=50),
        title_font=dict(size=16, color=DEEP_NAVY),
        hoverlabel=dict(bgcolor=DEEP_NAVY, font_color=WHITE),
        **kw)
    if legend_top:
        fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.0,
                                      xanchor="right", x=1))
    fig.update_xaxes(gridcolor=f"{DEEP_RGBA}0.08)", zeroline=False)
    fig.update_yaxes(gridcolor=f"{DEEP_RGBA}0.08)", zeroline=False)
    return fig


def tukey_outliers_pct(s):
    q1, q3 = s.quantile([0.25, 0.75])
    iqr = q3 - q1
    return ((s < q1 - 1.5 * iqr) | (s > q3 + 1.5 * iqr)).mean() * 100


def cramers_v(ct):
    chi2 = stats.chi2_contingency(ct, correction=False)[0]
    n = ct.values.sum()
    k = min(ct.shape) - 1
    return float(np.sqrt(chi2 / (n * k))) if k > 0 else 0.0


def winsorize(s, lo=0.01, hi=0.99):
    return s.clip(s.quantile(lo), s.quantile(hi))


GLOBAL_RATE = DF[TARGET].mean()


def _rgba(hex_color, a):
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{a})"
