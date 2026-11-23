# -*- coding: utf-8 -*-
"""EDA multivariado: correlación de Spearman, tasas por grupo, cupo, edad, cruce de variables y
matriz de dispersión, con sus interpretaciones y los hallazgos clave.

Las funciones que dependen del filtro global reciben el subconjunto en `data` (por defecto, todos los clientes).
"""

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy import stats

from tablero.config import (
    DEEP_NAVY, DIVERGING, GOLD_DARK, GOLD_MID, GOLD_SOFT, GREY_BLUE, MID_BLUE, NAVY, PALETTE, PALE_GOLD,
    SEQ_GOLD, WARM_GOLD, tx)
from tablero.datos import (
    BILL_COLS, DF, DISCRETE, MONTH_ORDER, NUM_COLS, PAYAMT_COLS, PAY_COLS, TARGET, _CAT_LABELS, as_cat,
    cat_labels, cat_order, month_lbl)
from tablero.utilidades import (GLOBAL_RATE, cramers_v, fmt_val, nt, sig, style_fig)

# ----- 4.1 Matriz de correlación: SOLO Spearman, sobre los datos originales ----
# Spearman trabaja con rangos: no exige linealidad ni normalidad, resiste los
# valores extremos y es adecuado para PAY_x (ordinales) y la variable objetivo
# (binaria). Al ser invariante a transformaciones monótonas, no se winsoriza.


def _corr_input(data=DF):
    return data[NUM_COLS + [TARGET]].rename(columns={TARGET: "default"})


CORR = _corr_input().corr(method="spearman")


def spearman(data=DF):
    """Matriz de Spearman de `data` (la de todos los clientes se calcula una sola vez)."""
    return CORR if data is DF else _corr_input(data).corr(method="spearman")


def fig_corr(data=DF):
    c = spearman(data)
    fig = go.Figure(go.Heatmap(
        z=c.values, x=c.columns, y=c.columns, colorscale=DIVERGING, zmid=0, zmin=-1, zmax=1,
        text=c.round(2).values, texttemplate="%{text}", textfont=dict(size=8),
        colorbar=dict(title="ρ", thickness=14),
        hovertemplate="%{y} vs %{x}<br>" + tx("correlación", "correlation") + " (ρ): %{z:.3f}<extra></extra>"))
    fig.update_layout(title=tx("Matriz de correlación de Spearman (datos originales)",
                               "Spearman correlation matrix (original data)"))
    fig.update_yaxes(autorange="reversed")
    return style_fig(fig, 740, legend_top=False)


def interp_corr():
    c = CORR
    iu = np.triu_indices(6, 1)
    bill = c.loc[BILL_COLS, BILL_COLS].values[iu]
    pay = c.loc[PAY_COLS, PAY_COLS].values[iu]
    pamt = c.loc[PAYAMT_COLS, PAYAMT_COLS].values[iu]
    tgt = c["default"].drop("default").abs().sort_values(ascending=False).head(4)
    tgt_txt = ", ".join(f"{k} ({c.loc[k, 'default']:+.2f})" for k in tgt.index)
    basic = tx(
        "Las seis facturas mensuales (BILL_AMT) se mueven casi igual: quien debe mucho un mes suele "
        "deber mucho al siguiente, por eso aparece un gran bloque dorado. Los estados de pago (PAY) "
        "también se parecen entre sí. En cambio, lo que realmente se pagó (PAY_AMT) casi no se "
        f"relaciona con nada. La variable más ligada al incumplimiento es {tgt.index[0]}.",
        "The six monthly bills (BILL_AMT) move almost identically: whoever owes a lot one month usually "
        "owes a lot the next, which is why a large gold block appears. The repayment statuses (PAY) are "
        "also similar to each other. In contrast, what was actually paid (PAY_AMT) is barely related to "
        f"anything. The variable most linked to default is {tgt.index[0]}.")
    tech = tx(
        f"Spearman (ρ): correlación entre BILL_AMT1 a BILL_AMT6 de {bill.min():.2f} a {bill.max():.2f} "
        f"(multicolinealidad severa; el VIF del notebook supera 20 en BILL_AMT2 a BILL_AMT5); entre PAY_x "
        f"de {pay.min():.2f} a {pay.max():.2f}; entre PAY_AMT de {pamt.min():.2f} a {pamt.max():.2f}. "
        f"Mayor asociación con default (|ρ|): {tgt_txt}. Se usa Spearman y no Pearson porque las variables "
        "monetarias son muy asimétricas y con colas extremas, PAY_x es ordinal y la variable objetivo es "
        "binaria; los rangos no exigen linealidad ni normalidad. Recomendación: no usar las seis BILL_AMT "
        "por separado en modelos lineales (usar nivel promedio + tendencia, solo la más reciente o PCA).",
        f"Spearman (ρ): correlation among BILL_AMT1 to BILL_AMT6 from {bill.min():.2f} to {bill.max():.2f} "
        f"(severe multicollinearity; the notebook's VIF exceeds 20 for BILL_AMT2 to BILL_AMT5); among PAY_x "
        f"from {pay.min():.2f} to {pay.max():.2f}; among PAY_AMT from {pamt.min():.2f} to {pamt.max():.2f}. "
        f"Strongest association with default (|ρ|): {tgt_txt}. Spearman is used instead of Pearson because the "
        "monetary variables are highly skewed with extreme tails, PAY_x is ordinal and the target is binary; "
        "ranks require neither linearity nor normality. Recommendation: do not use the six BILL_AMT separately "
        "in linear models (use average level + trend, only the most recent one, or PCA).")
    return basic, tech


# ----- 4.2 Tasa de default por EDUCATION / MARRIAGE / SEX ---------------------
def rate_table(col, data=DF):
    g = data.groupby(col)[TARGET].agg(["mean", "size"])
    lab = cat_labels(col)
    g.index = [lab[i] for i in g.index]
    return g


def fig_rates(data=DF):
    fig = make_subplots(rows=1, cols=3, subplot_titles=[tx("Nivel educativo", "Education level"),
                                                         tx("Estado civil", "Marital status"), tx("Sexo", "Sex")],
                        shared_yaxes=True, horizontal_spacing=0.05)
    for j, col in enumerate(["EDUCATION", "MARRIAGE", "SEX"], start=1):
        t = rate_table(col, data=data)
        fig.add_trace(go.Bar(
            x=t.index, y=t["mean"], marker_color=[WARM_GOLD if r > GLOBAL_RATE else NAVY for r in t["mean"]],
            text=[f"{r:.1%}" for r in t["mean"]], textposition="outside", customdata=t["size"],
            hovertemplate="%{x}<br>" + tx("Tasa de default", "Default rate") + ": %{y:.1%}<br>"
                          + tx("Clientes", "Clients") + ": %{customdata:,}<extra></extra>",
            showlegend=False), row=1, col=j)
        fig.add_hline(y=GLOBAL_RATE, line_dash="dash", line_color=DEEP_NAVY, row=1, col=j)
    # Leyenda real (abajo, centrada) en lugar de explicar los colores en el título
    for name, kw in [(tx("Por encima del promedio", "Above average"), dict(marker=dict(color=WARM_GOLD, size=12, symbol="square"))),
                     (tx("En o bajo el promedio", "At or below average"), dict(marker=dict(color=NAVY, size=12, symbol="square"))),
                     (tx(f"Tasa global {GLOBAL_RATE:.1%}", f"Overall rate {GLOBAL_RATE:.1%}"),
                      dict(mode="lines", line=dict(color=DEEP_NAVY, dash="dash", width=2)))]:
        fig.add_trace(go.Scatter(x=[None], y=[None], mode=kw.pop("mode", "markers"), name=name,
                                 hoverinfo="skip", **kw), row=1, col=1)
    fig.update_yaxes(tickformat=".0%", range=[0, 0.32], title_text=tx("Tasa de default", "Default rate"), col=1)
    fig.update_layout(title=tx("Tasa de incumplimiento según perfil demográfico", "Default rate by demographic profile"))
    style_fig(fig, 480, legend_top=False)
    fig.update_layout(showlegend=True, margin=dict(b=90),
                      legend=dict(orientation="h", yanchor="top", y=-0.16, xanchor="center", x=0.5))
    return fig


def interp_rates():
    te, tm, ts = rate_table("EDUCATION"), rate_table("MARRIAGE"), rate_table("SEX")
    chi = {}
    for col in ["EDUCATION", "MARRIAGE", "SEX"]:
        ct = pd.crosstab(DF[col], DF[TARGET])
        chi[col] = (*stats.chi2_contingency(ct)[:2], cramers_v(ct))
    top_e = te["mean"].idxmax()
    sx = cat_labels("SEX")
    men, women = ts.loc[sx[1], "mean"], ts.loc[sx[2], "mean"]
    basic = tx(
        f"Los hombres incumplen un poco más ({men:.1%}) que las mujeres "
        f"({women:.1%}). Por educación, el grupo con más incumplimiento es "
        f"«{top_e}» ({te.loc[top_e, 'mean']:.1%}) y el menor es «{te['mean'].idxmin()}» "
        f"({te['mean'].min():.1%}). Las diferencias existen pero son moderadas: el perfil "
        "demográfico explica poco comparado con el historial de pagos.",
        f"Men default slightly more ({men:.1%}) than women ({women:.1%}). By education, the group with the "
        f"most defaults is “{top_e}” ({te.loc[top_e, 'mean']:.1%}) and the lowest is “{te['mean'].idxmin()}” "
        f"({te['mean'].min():.1%}). The differences exist but are moderate: the demographic profile explains "
        "little compared with payment history.")
    mar = ", ".join(f"{k} {v:.1%}" for k, v in tm["mean"].items())
    tech = tx(
        f"χ² EDUCATION = {chi['EDUCATION'][0]:.1f} ({sig(chi['EDUCATION'][1])}, V de Cramér = "
        f"{chi['EDUCATION'][2]:.3f}); MARRIAGE = {chi['MARRIAGE'][0]:.1f} ({sig(chi['MARRIAGE'][1])}, "
        f"V = {chi['MARRIAGE'][2]:.3f}); SEX = {chi['SEX'][0]:.1f} ({sig(chi['SEX'][1])}, "
        f"V = {chi['SEX'][2]:.3f}). Con n ≈ {len(DF):,} casi cualquier diferencia es significativa; "
        "los tamaños de efecto (V < 0.1) son pequeños, así que lo relevante es la magnitud y no el "
        f"p-value. Tasas por MARRIAGE: {mar}.",
        f"χ² EDUCATION = {chi['EDUCATION'][0]:.1f} ({sig(chi['EDUCATION'][1])}, Cramér's V = "
        f"{chi['EDUCATION'][2]:.3f}); MARRIAGE = {chi['MARRIAGE'][0]:.1f} ({sig(chi['MARRIAGE'][1])}, "
        f"V = {chi['MARRIAGE'][2]:.3f}); SEX = {chi['SEX'][0]:.1f} ({sig(chi['SEX'][1])}, "
        f"V = {chi['SEX'][2]:.3f}). With n ≈ {len(DF):,} almost any difference is significant; the effect "
        "sizes (V < 0.1) are small, so what matters is the magnitude, not the p-value. "
        f"Rates by MARRIAGE: {mar}.")
    return basic, tech


# ----- 4.3 Boxplot LIMIT_BAL por estado de default ----------------------------
def fig_limit_box(scale, data=DF):
    fig = go.Figure()
    for k, name, color in [(0, "No default", DEEP_NAVY), (1, "Default", WARM_GOLD)]:
        fig.add_trace(go.Box(y=data.loc[data[TARGET] == k, "LIMIT_BAL"], name=name, marker_color=color,
                             boxmean=True, boxpoints="outliers", marker_size=3, line_width=1.6))
    fig.update_layout(title=tx("Límite de crédito (LIMIT_BAL) según estado de incumplimiento",
                               "Credit limit (LIMIT_BAL) by default status"),
                      yaxis_title="LIMIT_BAL (NT$)", showlegend=False)
    if scale == "log":
        fig.update_yaxes(type="log")
    return style_fig(fig, 470, legend_top=False)


def interp_limit():
    g0 = DF.loc[DF[TARGET] == 0, "LIMIT_BAL"]
    g1 = DF.loc[DF[TARGET] == 1, "LIMIT_BAL"]
    u, p = stats.mannwhitneyu(g0, g1, alternative="two-sided")
    tt, pt = stats.ttest_ind(g0, g1, equal_var=False)
    basic = tx(f"Los clientes que cayeron en default tenían, en la mitad de los casos, un límite de "
               f"{nt(g1.median())} o menos, frente a {nt(g0.median())} de quienes pagaron. Es decir, "
               "quienes incumplen suelen tener líneas de crédito más bajas.",
               f"Half of the clients who defaulted had a limit of {nt(g1.median())} or less, compared with "
               f"{nt(g0.median())} for those who paid. In other words, defaulters tend to have lower credit lines.")
    tech = tx(f"Media: {nt(g0.mean())} (no default) vs. {nt(g1.mean())} (default); mediana "
              f"{nt(g0.median())} vs. {nt(g1.median())}. Mann-Whitney U = {u:,.0f} ({sig(p)}); "
              f"t de Welch = {tt:.2f} ({sig(pt)}). Diferencia significativa y de relevancia de negocio: "
              "un límite alto actúa como proxy de buena calificación crediticia previa. Distribución muy "
              "sesgada a la derecha, por eso se prefieren pruebas no paramétricas (alterna la escala log).",
              f"Mean: {nt(g0.mean())} (no default) vs. {nt(g1.mean())} (default); median "
              f"{nt(g0.median())} vs. {nt(g1.median())}. Mann-Whitney U = {u:,.0f} ({sig(p)}); "
              f"Welch's t = {tt:.2f} ({sig(pt)}). A significant and business-relevant difference: a high limit "
              "acts as a proxy for a good prior credit rating. The distribution is strongly right-skewed, so "
              "non-parametric tests are preferred (toggle the log scale).")
    return basic, tech


# ----- 4.4 AGE vs. patrones de atraso -----------------------------------------
def fig_age(view, data=DF):
    fig = go.Figure()
    ml = month_lbl()
    if view == "lines":
        g = data.groupby("AGE_GRP", observed=True)[MONTH_ORDER].mean()
        cols = [DEEP_NAVY, NAVY, MID_BLUE, GREY_BLUE, PALE_GOLD, GOLD_SOFT, WARM_GOLD, GOLD_MID, GOLD_DARK]
        for i, grp in enumerate(g.index):
            fig.add_trace(go.Scatter(x=ml, y=g.loc[grp], mode="lines+markers", name=str(grp),
                                     line=dict(color=cols[i % len(cols)], width=2.4)))
        fig.update_layout(title=tx("Atraso promedio (PAY) por mes y grupo de edad",
                                   "Average delay (PAY) by month and age group"),
                          xaxis_title=tx("Mes (abril → septiembre 2005)", "Month (April → September 2005)"),
                          yaxis_title=tx("PAY promedio", "Average PAY"))
        return style_fig(fig, 470)
    if view == "heat":
        g = (data[MONTH_ORDER].ge(1).groupby(data["AGE_GRP"], observed=True).mean() * 100)
        fig.add_trace(go.Heatmap(
            z=g.values, x=ml, y=[str(i) for i in g.index], colorscale=SEQ_GOLD,
            text=g.round(1).values, texttemplate="%{text}%",
            colorbar=dict(title=tx("% con atraso", "% late"), thickness=14),
            hovertemplate=tx("Edad", "Age") + " %{y} · %{x}<br>%{z:.1f}% "
                          + tx("con atraso ≥1 mes", "with ≥1 month delay") + "<extra></extra>"))
        fig.update_layout(title=tx("% de clientes con atraso (PAY ≥ 1) por grupo de edad y mes",
                                   "% of clients with a delay (PAY ≥ 1) by age group and month"),
                          xaxis_title=tx("Mes", "Month"), yaxis_title=tx("Grupo de edad", "Age group"))
        fig.update_yaxes(autorange="reversed")
        return style_fig(fig, 470, legend_top=False)
    g = data.groupby("AGE_GRP", observed=True)[TARGET].agg(["mean", "size"])
    fig.add_trace(go.Bar(x=[str(i) for i in g.index], y=g["mean"],
                         marker_color=[WARM_GOLD if r > GLOBAL_RATE else NAVY for r in g["mean"]],
                         text=[f"{r:.1%}" for r in g["mean"]], textposition="outside", customdata=g["size"],
                         hovertemplate=tx("Edad", "Age") + " %{x}<br>" + tx("Tasa de default", "Default rate")
                                       + ": %{y:.1%}<br>" + tx("Clientes", "Clients")
                                       + ": %{customdata:,}<extra></extra>"))
    fig.add_hline(y=GLOBAL_RATE, line_dash="dash", line_color=DEEP_NAVY,
                  annotation_text=f"Global {GLOBAL_RATE:.1%}", annotation_position="top left")
    fig.update_layout(title=tx("Tasa de default por grupo de edad", "Default rate by age group"),
                      xaxis_title=tx("Grupo de edad", "Age group"),
                      yaxis_title=tx("Tasa de default", "Default rate"), yaxis_tickformat=".0%", showlegend=False)
    fig.update_yaxes(range=[0, g["mean"].max() * 1.2])
    return style_fig(fig, 470, legend_top=False)


def interp_age(view, data=DF):
    gm = data.groupby("AGE_GRP", observed=True)[MONTH_ORDER].mean()
    gd = data.groupby("AGE_GRP", observed=True)[TARGET].mean()
    gp = data[MONTH_ORDER].ge(1).groupby(data["AGE_GRP"], observed=True).mean()
    rho, p = stats.spearmanr(data["AGE"], data["PAY_0"])
    hi, lo = gd.idxmax(), gd.idxmin()
    if view == "lines":
        basic = tx("Todas las edades siguen una forma parecida: el atraso promedio sube hacia los últimos meses "
                   f"(septiembre). El grupo con atraso más alto en el mes más reciente es {gm['PAY_0'].idxmax()} "
                   f"años ({gm['PAY_0'].max():.2f}) y el más bajo es {gm['PAY_0'].idxmin()} "
                   f"({gm['PAY_0'].min():.2f}).",
                   "All ages follow a similar shape: the average delay rises toward the last months "
                   f"(September). The group with the highest delay in the most recent month is "
                   f"{gm['PAY_0'].idxmax()} years ({gm['PAY_0'].max():.2f}) and the lowest is "
                   f"{gm['PAY_0'].idxmin()} ({gm['PAY_0'].min():.2f}).")
        tech = tx(f"Correlación de Spearman AGE-PAY_0: ρ = {rho:+.3f} ({sig(p)}), relación muy débil. "
                  "Los promedios de PAY mezclan los códigos −2/−1/0 (sin atraso) con atrasos ≥1, por lo que "
                  "se complementan con la vista de % con atraso.",
                  f"Spearman correlation AGE-PAY_0: ρ = {rho:+.3f} ({sig(p)}), a very weak relationship. "
                  "PAY averages mix the codes −2/−1/0 (no delay) with delays ≥1, so they are complemented by "
                  "the % late view.")
    elif view == "heat":
        mx = np.unravel_index(np.argmax(gp.values), gp.shape)
        mes = month_lbl()[mx[1]]
        basic = tx(f"Cada celda indica qué porcentaje de ese grupo de edad llevaba al menos un mes de atraso. "
                   f"El valor más alto aparece en {gp.index[mx[0]]} años, mes de {mes} "
                   f"({gp.values[mx] * 100:.1f}%). Las diferencias entre edades son pequeñas comparadas con "
                   "las diferencias entre meses.",
                   f"Each cell shows what percentage of that age group was at least one month late. "
                   f"The highest value is at {gp.index[mx[0]]} years, in {mes} ({gp.values[mx] * 100:.1f}%). "
                   "Differences between ages are small compared with differences between months.")
        tech = tx(f"Proporción con PAY ≥ 1 entre {gp.values.min():.1%} y {gp.values.max():.1%}. "
                  f"Spearman AGE-PAY_0: ρ = {rho:+.3f} ({sig(p)}). La edad aporta información marginal; el "
                  "estado de pago de meses previos es el predictor dominante (ver SHAP en el notebook).",
                  f"Share with PAY ≥ 1 between {gp.values.min():.1%} and {gp.values.max():.1%}. "
                  f"Spearman AGE-PAY_0: ρ = {rho:+.3f} ({sig(p)}). Age adds marginal information; the "
                  "repayment status of previous months is the dominant predictor (see SHAP in the notebook).")
    else:
        basic = tx(f"El riesgo es más alto en el grupo de {hi} años ({gd.max():.1%}) y más bajo en el de "
                   f"{lo} ({gd.min():.1%}). La relación con la edad es suave y no tan marcada como la del "
                   "historial de pagos.",
                   f"Risk is highest in the {hi} age group ({gd.max():.1%}) and lowest in the {lo} group "
                   f"({gd.min():.1%}). The relationship with age is mild and not as strong as that of "
                   "payment history.")
        tech = tx(f"Tasa de default por grupo entre {gd.min():.1%} y {gd.max():.1%} (global {GLOBAL_RATE:.1%}). "
                  "Patrón posiblemente no lineal (en forma de U suave); los grupos extremos de edad tienen "
                  "menos observaciones y, por ende, estimaciones más inestables. Conviene considerar AGE "
                  "con términos no lineales o categorizada en modelos paramétricos.",
                  f"Default rate by group between {gd.min():.1%} and {gd.max():.1%} (overall {GLOBAL_RATE:.1%}). "
                  "Possibly non-linear pattern (a mild U shape); the extreme age groups have fewer observations "
                  "and therefore less stable estimates. AGE should be considered with non-linear terms or "
                  "binned in parametric models.")
    return basic, tech


# ----- 4.5 Módulo interactivo de cruce de variables ---------------------------
def cross_fig(x, y, c, data=DF):
    """Cruza 2 (o 3) variables y devuelve (figura, interpretación básica, técnica)."""
    cdisc = c not in (None, "none") and c in DISCRETE
    cnum = c not in (None, "none") and c not in DISCRETE
    xd, yd = x in DISCRETE, y in DISCRETE
    rate_lbl = tx("Tasa de default", "Default rate")

    # ------ numérica × numérica: dispersión + recta de tendencia --------------
    if not xd and not yd:
        d = data.sample(min(4000, len(data)), random_state=7).copy()
        if cdisc:
            d["_c"] = pd.Series(as_cat(c, data=data), index=data.index).loc[d.index].astype(str)
            fig = px.scatter(d, x=x, y=y, color="_c", opacity=0.55, color_discrete_sequence=PALETTE,
                             category_orders={"_c": cat_order(c, data=data)}, labels={"_c": c})
        elif cnum:
            fig = px.scatter(d, x=x, y=y, color=c, opacity=0.6,
                             color_continuous_scale=[[0, NAVY], [1, WARM_GOLD]])
        else:
            fig = px.scatter(d, x=x, y=y, opacity=0.45, color_discrete_sequence=[NAVY])
        if x != y:
            m, b = np.polyfit(data[x], data[y], 1)
            xs = np.array([data[x].min(), data[x].max()])
            fig.add_trace(go.Scatter(x=xs, y=m * xs + b, mode="lines", name=tx("Tendencia lineal", "Linear trend"),
                                     line=dict(color=WARM_GOLD, width=3, dash="dash")))
        fig.update_xaxes(range=[data[x].min(), data[x].quantile(0.99) * 1.05])
        fig.update_yaxes(range=[data[y].min(), data[y].quantile(0.99) * 1.05])
        fig.update_layout(title=tx(f"{y} vs. {x} (muestra de {len(d):,} clientes)",
                                   f"{y} vs. {x} (sample of {len(d):,} clients)"))
        r, pr = stats.pearsonr(data[x], data[y])
        rho, ps = stats.spearmanr(data[x], data[y])
        a = abs(rho)
        fuerza = (tx("muy débil", "very weak") if a < 0.2 else tx("débil", "weak") if a < 0.4
                  else tx("moderada", "moderate") if a < 0.7 else tx("fuerte", "strong"))
        sentido = (tx("positiva (suben juntas)", "positive (they rise together)") if rho > 0
                   else tx("negativa (una sube cuando la otra baja)", "negative (one rises when the other falls)"))
        basic = tx(f"Entre {x} y {y} hay una relación {fuerza} y {sentido}. "
                   "Cada punto es un cliente; la línea dorada resume la tendencia general.",
                   f"There is a {fuerza}, {sentido} relationship between {x} and {y}. "
                   "Each point is a client; the gold line summarizes the overall trend.")
        tech = (f"Spearman ρ = {rho:+.3f} ({sig(ps)}); Pearson r = {r:+.3f} ({sig(pr)}); n = {len(data):,}. "
                + tx("Pendiente OLS", "OLS slope") + f" = {m:.4g}." if x != y
                else tx("x e y son la misma variable.", "x and y are the same variable."))
        return style_fig(fig, 520), basic, tech

    # ------ discreta × discreta -----------------------------------------------
    if xd and yd:
        if x == y:
            fig = go.Figure()
            fig.update_layout(title=tx("Elige dos variables distintas", "Choose two different variables"))
            return (style_fig(fig, 420), tx("Selecciona variables distintas en X e Y.",
                                            "Select different variables for X and Y."), "")
        if TARGET in (x, y):
            other = y if x == TARGET else x
            d = pd.DataFrame({"_o": as_cat(other, data=data), TARGET: data[TARGET]})
            if cdisc and c not in (other, TARGET):
                d["_c"] = as_cat(c, data=data)
                g = d.groupby(["_o", "_c"], observed=True)[TARGET].agg(["mean", "size"]).reset_index()
                fig = px.bar(g, x="_o", y="mean", color="_c", barmode="group",
                             color_discrete_sequence=PALETTE, category_orders={"_o": cat_order(other, data=data), "_c": cat_order(c, data=data)},
                             labels={"_o": other, "mean": rate_lbl, "_c": c}, custom_data=["size"])
                fig.update_traces(hovertemplate="%{x}<br>" + tx("Tasa", "Rate")
                                                + ": %{y:.1%}<br>n=%{customdata[0]:,}<extra></extra>")
            else:
                g = d.groupby("_o", observed=True)[TARGET].agg(["mean", "size"]).reset_index()
                fig = go.Figure(go.Bar(
                    x=g["_o"].astype(str), y=g["mean"], customdata=g["size"],
                    marker_color=[WARM_GOLD if r > GLOBAL_RATE else NAVY for r in g["mean"]],
                    text=[f"{r:.1%}" for r in g["mean"]], textposition="outside",
                    hovertemplate="%{x}<br>" + tx("Tasa", "Rate") + ": %{y:.1%}<br>n=%{customdata:,}<extra></extra>"))
                fig.update_xaxes(type="category", categoryorder="array", categoryarray=cat_order(other, data=data))
            fig.add_hline(y=GLOBAL_RATE, line_dash="dash", line_color=DEEP_NAVY,
                          annotation_text=f"Global {GLOBAL_RATE:.1%}", annotation_position="top left")
            fig.update_layout(title=tx(f"Tasa de default según {other}", f"Default rate by {other}"),
                              xaxis_title=other, yaxis_title=rate_lbl, yaxis_tickformat=".0%")
            tab = d.groupby("_o", observed=True)[TARGET].agg(["mean", "size"])
            tab = tab[tab["size"] >= 30]
            ct = pd.crosstab(data[other], data[TARGET])
            chi, p, dof, _ = stats.chi2_contingency(ct)
            basic = tx(f"La tasa de default más alta aparece en «{tab['mean'].idxmax()}» "
                       f"({tab['mean'].max():.1%}) y la más baja en «{tab['mean'].idxmin()}» "
                       f"({tab['mean'].min():.1%}), frente a {GLOBAL_RATE:.1%} en promedio.",
                       f"The highest default rate is in “{tab['mean'].idxmax()}” ({tab['mean'].max():.1%}) and the "
                       f"lowest in “{tab['mean'].idxmin()}” ({tab['mean'].min():.1%}), versus {GLOBAL_RATE:.1%} "
                       "on average.")
            tech = tx(f"χ²({dof}) = {chi:.1f} ({sig(p)}); V de Cramér = {cramers_v(ct):.3f}. "
                      "Se muestran categorías con n ≥ 30 en el texto; las de muy baja frecuencia "
                      "tienen tasas inestables.",
                      f"χ²({dof}) = {chi:.1f} ({sig(p)}); Cramér's V = {cramers_v(ct):.3f}. "
                      "The text only mentions categories with n ≥ 30; very rare ones have unstable rates.")
            if cnum:
                tech += tx(" (La variable de color numérica se ignora en este gráfico.)",
                           " (The numeric color variable is ignored in this chart.)")
            return style_fig(fig, 500, legend_top=bool(cdisc)), basic, tech
        # discreta × discreta (sin target): heatmap de la tasa de default por celda
        g = data.groupby([y, x])[TARGET].agg(["mean", "size"]).reset_index()
        piv = g.pivot(index=y, columns=x, values="mean")
        cnt = g.pivot(index=y, columns=x, values="size")
        lab = lambda col, v: cat_labels(col)[v] if col in _CAT_LABELS else str(int(v))
        ylab = [lab(y, i) for i in piv.index]
        xlab = [lab(x, i) for i in piv.columns]
        fig = go.Figure(go.Heatmap(
            z=piv.values, x=xlab, y=ylab, colorscale=SEQ_GOLD, customdata=cnt.values,
            text=np.where(cnt.values >= 30, np.round(piv.values * 100, 1).astype(str) + "%", ""),
            texttemplate="%{text}", colorbar=dict(title=tx("Tasa default", "Default rate"), tickformat=".0%",
                                                  thickness=14),
            hovertemplate=f"{x}: %{{x}}<br>{y}: %{{y}}<br>{tx('Tasa', 'Rate')}: %{{z:.1%}}<br>n=%{{customdata:,}}<extra></extra>"))
        fig.update_xaxes(type="category")
        fig.update_yaxes(type="category", autorange="reversed")
        fig.update_layout(title=tx(f"Tasa de default por combinación de {x} × {y} (celdas con n ≥ 30 rotuladas)",
                                   f"Default rate by combination of {x} × {y} (cells with n ≥ 30 labeled)"),
                          xaxis_title=x, yaxis_title=y)
        ct = pd.crosstab(data[x], data[y])
        chi, p, dof, _ = stats.chi2_contingency(ct)
        ok = g[g["size"] >= 30]
        top = ok.loc[ok["mean"].idxmax()]
        basic = tx(f"La combinación con más incumplimiento (con al menos 30 clientes) es {x} = "
                   f"{lab(x, top[x])} y {y} = {lab(y, top[y])}, con {top['mean']:.1%} de default "
                   f"({int(top['size']):,} clientes).",
                   f"The combination with the most defaults (with at least 30 clients) is {x} = "
                   f"{lab(x, top[x])} and {y} = {lab(y, top[y])}, with {top['mean']:.1%} default "
                   f"({int(top['size']):,} clients).")
        tech = tx(f"Asociación entre {x} y {y}: χ²({dof}) = {chi:.1f} ({sig(p)}), V de Cramér = "
                  f"{cramers_v(ct):.3f}. El color muestra la tasa de default por celda; el módulo ignora "
                  "la variable de color en este tipo de cruce.",
                  f"Association between {x} and {y}: χ²({dof}) = {chi:.1f} ({sig(p)}), Cramér's V = "
                  f"{cramers_v(ct):.3f}. The color shows the default rate per cell; the module ignores the "
                  "color variable in this type of cross.")
        return style_fig(fig, 520, legend_top=False), basic, tech

    # ------ discreta × numérica (cualquier orientación) ------------------------
    catv, numv = (x, y) if xd else (y, x)
    d = pd.DataFrame({"_k": as_cat(catv, data=data), numv: data[numv]})
    horizontal = not xd
    kw = dict(category_orders={"_k": cat_order(catv, data=data)}, labels={"_k": catv})
    if cdisc and c != catv:
        d["_c"] = as_cat(c, data=data)
        kw["category_orders"]["_c"] = cat_order(c, data=data)
        kw["labels"]["_c"] = c
        kw["color"] = "_c"
        kw["color_discrete_sequence"] = PALETTE
    else:
        kw["color_discrete_sequence"] = [NAVY]
    if horizontal:
        fig = px.box(d, x=numv, y="_k", orientation="h", points="outliers", **kw)
    else:
        fig = px.box(d, x="_k", y=numv, points="outliers", **kw)
    # Bigotes en 1,5·IQR (Tukey) y eje ajustado a ellos: los atípicos quedan como puntos tenues
    # y no estiran la escala hasta el máximo.
    fig.update_traces(boxmean=True, marker=dict(size=3, opacity=0.3))
    grp = d.groupby(["_k"] + (["_c"] if "_c" in d else []), observed=True)[numv]
    q1, q3 = grp.quantile(0.25), grp.quantile(0.75)
    hi = float(np.minimum(q3 + 1.5 * (q3 - q1), grp.max()).max())
    lo = float(np.maximum(q1 - 1.5 * (q3 - q1), grp.min()).min())
    pad = (hi - lo) * 0.06
    (fig.update_xaxes if horizontal else fig.update_yaxes)(range=[lo - pad, hi + pad])
    fig.update_layout(title=tx(f"{numv} según {catv}", f"{numv} by {catv}"))
    cats = as_cat(catv, data=data)
    groups = [data.loc[cats == k, numv] for k in cat_order(catv, data=data)]
    groups = [g for g in groups if len(g) > 5]
    meds = {k: data.loc[cats == k, numv].median() for k in cat_order(catv, data=data)}
    meds_txt = "; ".join(f"{k}: {fmt_val(numv, v)}" for k, v in list(meds.items())[:8])
    hi_k, lo_k = max(meds, key=meds.get), min(meds, key=meds.get)
    if len(groups) >= 2:
        H, p = stats.kruskal(*groups)
        eps = H / (len(data) - 1)
    else:
        H, p, eps = np.nan, np.nan, np.nan
    basic = tx(f"La mediana de {numv} es mayor en «{hi_k}» ({fmt_val(numv, meds[hi_k])}) y menor en "
               f"«{lo_k}» ({fmt_val(numv, meds[lo_k])}). Las cajas muestran dónde está el 50% central de cada grupo.",
               f"The median of {numv} is highest in “{hi_k}” ({fmt_val(numv, meds[hi_k])}) and lowest in "
               f"“{lo_k}” ({fmt_val(numv, meds[lo_k])}). The boxes show where the middle 50% of each group lies.")
    tech = tx(f"Kruskal-Wallis H = {H:.1f} ({sig(p)}), ε² = {eps:.4f}. Medianas por grupo → {meds_txt}. "
              "Con muestras grandes el p-value es casi siempre significativo; se debe valorar el tamaño del efecto.",
              f"Kruskal-Wallis H = {H:.1f} ({sig(p)}), ε² = {eps:.4f}. Medians by group → {meds_txt}. "
              "With large samples the p-value is almost always significant; the effect size should be assessed.")
    return style_fig(fig, 520, legend_top=bool(cdisc and c != catv)), basic, tech


def fig_splom(vars_, data=DF):
    d = data.sample(min(1500, len(data)), random_state=3)
    fig = go.Figure(go.Splom(
        dimensions=[dict(label=v, values=d[v]) for v in vars_],
        marker=dict(color=d[TARGET], colorscale=[[0, NAVY], [1, WARM_GOLD]], size=4, opacity=0.55,
                    line=dict(width=0)),
        diagonal_visible=True, showupperhalf=False,
        text=np.where(d[TARGET] == 1, "Default", "No default"), hoverinfo="text+x+y"))
    fig.update_layout(title=tx("Matriz de dispersión (azul = no default · dorado = default) · muestra de 1,500 clientes",
                               "Scatter matrix (blue = no default · gold = default) · sample of 1,500 clients"))
    return style_fig(fig, max(480, 170 * len(vars_) + 120), legend_top=False)


def interp_splom(vars_, data=DF):
    sub = _corr_input(data)[[("default" if v == TARGET else v) for v in vars_]]
    c = sub.corr(method="spearman")
    iu = np.triu_indices(len(vars_), 1)
    pairs = [(c.index[i], c.columns[j], c.values[i, j]) for i, j in zip(*iu)]
    pairs.sort(key=lambda t: -abs(t[2]))
    a, b, r = pairs[0]
    basic = tx(f"De las variables elegidas, las que más se parecen entre sí son {a} y {b} "
               f"(relación {'directa' if r > 0 else 'inversa'}). Si los puntos dorados (default) se "
               "agrupan en una zona, esa combinación de variables separa a los clientes de riesgo.",
               f"Among the chosen variables, the most similar are {a} and {b} "
               f"({'direct' if r > 0 else 'inverse'} relationship). If the gold points (default) cluster in one "
               "area, that combination of variables separates the risky clients.")
    pares = "; ".join(f"{p[0]}-{p[1]} ρ = {p[2]:+.2f}" for p in pairs[:4])
    tech = tx(f"Spearman de los pares más fuertes: {pares}. Útil para detectar colinealidad entre predictores "
              "y regiones del espacio donde se concentra la clase 1.",
              f"Spearman of the strongest pairs: {pares}. Useful to detect collinearity between predictors and "
              "regions of the space where class 1 concentrates.")
    return basic, tech


# ----- 4.6 Hallazgos clave (tarjetas finales) ---------------------------------
def key_findings():
    c = CORR
    bill = c.loc[BILL_COLS, BILL_COLS].values[np.triu_indices(6, 1)]
    t_ser = c["default"].drop("default")
    t_top = t_ser.abs().idxmax()
    t_rho = t_ser[t_top]
    g1 = DF.loc[DF[TARGET] == 1, "LIMIT_BAL"].median()
    g0 = DF.loc[DF[TARGET] == 0, "LIMIT_BAL"].median()
    r_pay0 = DF.groupby(DF["PAY_0"].ge(1))[TARGET].mean()
    te = rate_table("EDUCATION")["mean"]
    return [
        (tx("El historial de pagos domina", "Payment history dominates"),
         tx(f"{t_top} es la variable más asociada al default (ρ de Spearman = {t_rho:+.2f}). Los clientes con "
            f"≥1 mes de atraso en PAY_0 incumplen en {r_pay0[True]:.1%} de los casos, frente a "
            f"{r_pay0[False]:.1%} de quienes están al día.",
            f"{t_top} is the variable most associated with default (Spearman ρ = {t_rho:+.2f}). Clients with "
            f"≥1 month of delay in PAY_0 default in {r_pay0[True]:.1%} of cases, versus "
            f"{r_pay0[False]:.1%} of those who are up to date.")),
        (tx("Multicolinealidad en la facturación", "Multicollinearity in billing"),
         tx(f"Las seis BILL_AMT se correlacionan (Spearman) entre {bill.min():.2f} y {bill.max():.2f}. "
            "Para modelos lineales conviene resumirlas (promedio + tendencia) o usar PCA.",
            f"The six BILL_AMT correlate (Spearman) between {bill.min():.2f} and {bill.max():.2f}. "
            "For linear models it is better to summarize them (average + trend) or use PCA.")),
        (tx("Límite de crédito más bajo en default", "Lower credit limit among defaulters"),
         tx(f"Mediana de LIMIT_BAL: {nt(g1)} (default) vs. {nt(g0)} (no default). "
            "Un menor cupo se asocia con mayor riesgo.",
            f"Median LIMIT_BAL: {nt(g1)} (default) vs. {nt(g0)} (no default). "
            "A lower limit is associated with higher risk.")),
        (tx("El perfil demográfico pesa poco", "The demographic profile matters little"),
         tx(f"Las tasas por educación van de {te.min():.1%} a {te.max():.1%}: diferencias significativas pero "
            "con tamaño de efecto pequeño. La edad tampoco separa por sí sola.",
            f"Rates by education range from {te.min():.1%} to {te.max():.1%}: significant differences but with "
            "a small effect size. Age alone does not separate either.")),
    ]
