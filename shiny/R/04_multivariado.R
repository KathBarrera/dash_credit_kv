# =============================================================================
# 4. EDA MULTIVARIADO: FIGURAS E INTERPRETACIONES
# =============================================================================
# Spearman trabaja con rangos: no exige linealidad ni normalidad, resiste los valores
# extremos y es adecuado para PAY_x (ordinales) y la variable objetivo (binaria).

triu <- function(m) m[upper.tri(m)]

fig_corr <- function() {
  c <- CORR
  p <- plot_ly(z = c, x = colnames(c), y = rownames(c), type = "heatmap", colorscale = DIVERGING,
               zmid = 0, zmin = -1, zmax = 1, text = round(c, 2), texttemplate = "%{text}",
               textfont = list(size = 8), colorbar = list(title = "ρ", thickness = 14),
               hovertemplate = paste0("%{y} vs %{x}<br>", tx("correlación", "correlation"), " (ρ): %{z:.3f}<extra></extra>"))
  p <- layout(p, yaxis = list(autorange = "reversed", title = ""), xaxis = list(title = ""))
  style_fig(p, 740, legend_top = FALSE,
            title = tx("Matriz de correlación de Spearman (datos originales)", "Spearman correlation matrix (original data)"))
}

interp_corr <- function() {
  c <- CORR
  bill <- triu(c[BILL_COLS, BILL_COLS]); pay <- triu(c[PAY_COLS, PAY_COLS]); pamt <- triu(c[PAYAMT_COLS, PAYAMT_COLS])
  t <- c[, "default"][rownames(c) != "default"]
  tgt <- head(t[order(-abs(t))], 4)
  tgt_txt <- paste(sprintf("%s (%s)", names(tgt), sprintf("%+.2f", tgt)), collapse = ", ")
  basic <- tx(paste0("Las seis facturas mensuales (BILL_AMT) se mueven casi igual: quien debe mucho un mes suele deber mucho al siguiente, por eso aparece un gran bloque dorado. Los estados de pago (PAY) también se parecen entre sí. En cambio, lo que realmente se pagó (PAY_AMT) casi no se relaciona con nada. La variable más ligada al incumplimiento es ", names(tgt)[1], "."),
              paste0("The six monthly bills (BILL_AMT) move almost identically: whoever owes a lot one month usually owes a lot the next, which is why a large gold block appears. The repayment statuses (PAY) are also similar to each other. In contrast, what was actually paid (PAY_AMT) is barely related to anything. The variable most linked to default is ", names(tgt)[1], "."))
  tech <- tx(sprintf("Spearman (ρ): correlación entre BILL_AMT1–6 de %.2f a %.2f (multicolinealidad severa; el VIF del notebook supera 20 en BILL_AMT2–5); entre PAY_x de %.2f a %.2f; entre PAY_AMT de %.2f a %.2f. Mayor asociación con default (|ρ|): %s. Se usa Spearman y no Pearson porque las variables monetarias son muy asimétricas y con colas extremas, PAY_x es ordinal y la variable objetivo es binaria; los rangos no exigen linealidad ni normalidad. Recomendación: no usar las seis BILL_AMT por separado en modelos lineales (usar nivel promedio + tendencia, solo la más reciente o PCA).",
                     min(bill), max(bill), min(pay), max(pay), min(pamt), max(pamt), tgt_txt),
             sprintf("Spearman (ρ): correlation among BILL_AMT1–6 from %.2f to %.2f (severe multicollinearity; the notebook's VIF exceeds 20 for BILL_AMT2–5); among PAY_x from %.2f to %.2f; among PAY_AMT from %.2f to %.2f. Strongest association with default (|ρ|): %s. Spearman is used instead of Pearson because the monetary variables are highly skewed with extreme tails, PAY_x is ordinal and the target is binary; ranks require neither linearity nor normality. Recommendation: do not use the six BILL_AMT separately in linear models (use average level + trend, only the most recent one, or PCA).",
                     min(bill), max(bill), min(pay), max(pay), min(pamt), max(pamt), tgt_txt))
  list(basic, tech)
}

# ----- Tasa de default por EDUCATION / MARRIAGE / SEX ---------------------
rate_table <- function(col) {
  g <- stats::aggregate(df[[TARGET]], list(k = df[[col]]), function(v) c(mean = mean(v), size = length(v)))
  out <- data.frame(label = unname(cat_labels(col)[as.character(g$k)]), mean = g$x[, "mean"], size = g$x[, "size"])
  out
}

fig_rates <- function() {
  titles <- c(tx("Nivel educativo", "Education level"), tx("Estado civil", "Marital status"), tx("Sexo", "Sex"))
  cols <- c("EDUCATION", "MARRIAGE", "SEX")
  dom <- list(c(0, 0.317), c(0.342, 0.658), c(0.683, 1))     # tres paneles con el mismo eje Y
  p <- plot_ly()
  lay <- list()
  for (j in 1:3) {
    t <- rate_table(cols[j]); ax <- if (j == 1) "x" else paste0("x", j)
    p <- add_trace(p, x = fx(t$label), y = t$mean, type = "bar", customdata = t$size, showlegend = FALSE, xaxis = ax,
                   marker = list(color = ifelse(t$mean > GLOBAL_RATE, WARM_GOLD, NAVY)),
                   text = pct(t$mean), textposition = "outside", cliponaxis = FALSE,
                   hovertemplate = paste0("%{x}<br>", tx("Tasa de default", "Default rate"), ": %{y:.1%}<br>",
                                          tx("Clientes", "Clients"), ": %{customdata:,}<extra></extra>"))
    lay[[if (j == 1) "xaxis" else paste0("xaxis", j)]] <- list(domain = dom[[j]], anchor = "y", type = "category", title = "", categoryorder = "array", categoryarray = t$label)
  }
  # leyenda: dos colores y la línea de la tasa global
  ley <- list(list(tx("Por encima del promedio", "Above average"), list(mode = "markers", marker = list(color = WARM_GOLD, size = 12, symbol = "square"))),
              list(tx("En o bajo el promedio", "At or below average"), list(mode = "markers", marker = list(color = NAVY, size = 12, symbol = "square"))),
              list(tx(paste("Tasa global", pct(GLOBAL_RATE)), paste("Overall rate", pct(GLOBAL_RATE))),
                   list(mode = "lines", line = list(color = DEEP_NAVY, dash = "dash", width = 2))))
  for (l in ley) p <- do.call(add_trace, c(list(p, x = rate_table("EDUCATION")$label[1], y = -1, type = "scatter", name = l[[1]],
                                                showlegend = TRUE, hoverinfo = "skip"), l[[2]]))
  ann <- lapply(1:3, function(j) list(text = paste0("<b>", titles[j], "</b>"), x = mean(dom[[j]]), y = 1.02, xref = "paper",
                                      yref = "paper", xanchor = "center", yanchor = "bottom", showarrow = FALSE, font = list(size = 13)))
  p <- do.call(layout, c(list(p, yaxis = list(tickformat = ".0%", range = c(0, 0.32), title = tx("Tasa de default", "Default rate")),
                              shapes = list(hline(GLOBAL_RATE, xref = "paper", yref = "y")), annotations = ann), lay))
  p <- style_fig(p, 480, legend_top = FALSE, margin = list(l = 55, r = 30, t = 90, b = 90),
                 title = tx("Tasa de incumplimiento según perfil demográfico", "Default rate by demographic profile"))
  layout(p, showlegend = TRUE, legend = list(orientation = "h", yanchor = "top", y = -0.16, xanchor = "center", x = 0.5))
}

interp_rates <- function() {
  te <- rate_table("EDUCATION"); tm <- rate_table("MARRIAGE"); ts <- rate_table("SEX")
  chi <- lapply(c(EDUCATION = "EDUCATION", MARRIAGE = "MARRIAGE", SEX = "SEX"), function(col) {
    ct <- table(df[[col]], df[[TARGET]]); r <- chi2_test(ct)
    c(unname(r$statistic), r$p.value, cramers_v(ct))
  })
  sx <- cat_labels("SEX")
  men <- ts$mean[ts$label == sx[["1"]]]; women <- ts$mean[ts$label == sx[["2"]]]
  top_e <- te$label[which.max(te$mean)]; low_e <- te$label[which.min(te$mean)]
  basic <- tx(sprintf("Los hombres incumplen un poco más (%s) que las mujeres (%s). Por educación, el grupo con más incumplimiento es «%s» (%s) y el menor es «%s» (%s). Las diferencias existen pero son moderadas: el perfil demográfico explica poco comparado con el historial de pagos.",
                      pct(men), pct(women), top_e, pct(max(te$mean)), low_e, pct(min(te$mean))),
              sprintf("Men default slightly more (%s) than women (%s). By education, the group with the most defaults is “%s” (%s) and the lowest is “%s” (%s). The differences exist but are moderate: the demographic profile explains little compared with payment history.",
                      pct(men), pct(women), top_e, pct(max(te$mean)), low_e, pct(min(te$mean))))
  mar <- paste(sprintf("%s %s", tm$label, pct(tm$mean)), collapse = ", ")
  f <- function(k, lbl) sprintf("%.1f (%s, %s = %.3f)", chi[[k]][1], sig(chi[[k]][2]), lbl, chi[[k]][3])
  tech <- tx(sprintf("χ² EDUCATION = %s; MARRIAGE = %s; SEX = %s. Con n ≈ %s casi cualquier diferencia es significativa; los tamaños de efecto (V < 0.1) son pequeños, así que lo relevante es la magnitud y no el p-value. Tasas por MARRIAGE: %s.",
                     f("EDUCATION", "V de Cramér"), f("MARRIAGE", "V"), f("SEX", "V"), num(nrow(df)), mar),
             sprintf("χ² EDUCATION = %s; MARRIAGE = %s; SEX = %s. With n ≈ %s almost any difference is significant; the effect sizes (V < 0.1) are small, so what matters is the magnitude, not the p-value. Rates by MARRIAGE: %s.",
                     f("EDUCATION", "Cramér's V"), f("MARRIAGE", "V"), f("SEX", "V"), num(nrow(df)), mar))
  list(basic, tech)
}

# ----- Boxplot LIMIT_BAL por estado de default ----------------------------
fig_limit_box <- function(scale) {
  p <- plot_ly()
  for (k in 0:1) {
    color <- if (k == 0) DEEP_NAVY else WARM_GOLD
    p <- add_trace(p, y = df$LIMIT_BAL[df[[TARGET]] == k], type = "box", name = if (k == 0) "No default" else "Default",
                   boxmean = TRUE, boxpoints = "outliers", marker = list(color = color, size = 3),
                   line = list(color = color, width = 1.6), fillcolor = rgba(color, 0.5))
  }
  p <- layout(p, yaxis = list(title = "LIMIT_BAL (NT$)", type = if (scale == "log") "log" else "linear"), showlegend = FALSE)
  style_fig(p, 470, legend_top = FALSE,
            title = tx("Límite de crédito (LIMIT_BAL) según estado de incumplimiento", "Credit limit (LIMIT_BAL) by default status"))
}

interp_limit <- function() {
  g0 <- df$LIMIT_BAL[df[[TARGET]] == 0]; g1 <- df$LIMIT_BAL[df[[TARGET]] == 1]
  w <- stats::wilcox.test(g0, g1, exact = FALSE); tt <- stats::t.test(g0, g1)
  basic <- tx(sprintf("Los clientes que cayeron en default tenían, en la mitad de los casos, un límite de %s o menos, frente a %s de quienes pagaron. Es decir, quienes incumplen suelen tener líneas de crédito más bajas.",
                      nt(stats::median(g1)), nt(stats::median(g0))),
              sprintf("Half of the clients who defaulted had a limit of %s or less, compared with %s for those who paid. In other words, defaulters tend to have lower credit lines.",
                      nt(stats::median(g1)), nt(stats::median(g0))))
  tech <- tx(sprintf("Media: %s (no default) vs. %s (default); mediana %s vs. %s. Mann-Whitney U = %s (%s); t de Welch = %.2f (%s). Diferencia significativa y de relevancia de negocio: un límite alto actúa como proxy de buena calificación crediticia previa. Distribución muy sesgada a la derecha, por eso se prefieren pruebas no paramétricas (alterna la escala log).",
                     nt(mean(g0)), nt(mean(g1)), nt(stats::median(g0)), nt(stats::median(g1)),
                     num(unname(w$statistic)), sig(w$p.value), unname(tt$statistic), sig(tt$p.value)),
             sprintf("Mean: %s (no default) vs. %s (default); median %s vs. %s. Mann-Whitney U = %s (%s); Welch's t = %.2f (%s). A significant and business-relevant difference: a high limit acts as a proxy for a good prior credit rating. The distribution is strongly right-skewed, so non-parametric tests are preferred (toggle the log scale).",
                     nt(mean(g0)), nt(mean(g1)), nt(stats::median(g0)), nt(stats::median(g1)),
                     num(unname(w$statistic)), sig(w$p.value), unname(tt$statistic), sig(tt$p.value)))
  list(basic, tech)
}

# ----- AGE vs. patrones de atraso -----------------------------------------
age_means <- function(cols, fun = mean) {
  sapply(cols, function(c) tapply(df[[c]], df$AGE_GRP, fun))
}

fig_age <- function(view) {
  ml <- month_lbl()
  if (view == "lines") {
    g <- age_means(MONTH_ORDER)
    cols <- c(DEEP_NAVY, NAVY, MID_BLUE, GREY_BLUE, PALE_GOLD, GOLD_SOFT, WARM_GOLD, GOLD_MID, GOLD_DARK)
    p <- plot_ly()
    for (i in seq_len(nrow(g))) {
      p <- add_trace(p, x = ml, y = unname(g[i, ]), type = "scatter", mode = "lines+markers", name = rownames(g)[i],
                     line = list(color = cols[(i - 1) %% 9 + 1], width = 2.4), marker = list(color = cols[(i - 1) %% 9 + 1]))
    }
    p <- layout(p, xaxis = list(title = tx("Mes (abril → septiembre 2005)", "Month (April → September 2005)"),
                                categoryorder = "array", categoryarray = ml),
                yaxis = list(title = tx("PAY promedio", "Average PAY")))
    return(style_fig(p, 470, title = tx("Atraso promedio (PAY) por mes y grupo de edad", "Average delay (PAY) by month and age group")))
  }
  if (view == "heat") {
    g <- age_means(MONTH_ORDER, function(v) mean(v >= 1)) * 100
    p <- plot_ly(z = unname(g), x = ml, y = rownames(g), type = "heatmap", colorscale = SEQ_GOLD,
                 text = round(unname(g), 1), texttemplate = "%{text}%",
                 colorbar = list(title = tx("% con atraso", "% late"), thickness = 14),
                 hovertemplate = paste0(tx("Edad", "Age"), " %{y} · %{x}<br>%{z:.1f}% ",
                                        tx("con atraso ≥1 mes", "with ≥1 month delay"), "<extra></extra>"))
    p <- layout(p, xaxis = list(title = tx("Mes", "Month")), yaxis = list(title = tx("Grupo de edad", "Age group"), autorange = "reversed"))
    return(style_fig(p, 470, legend_top = FALSE,
                     title = tx("% de clientes con atraso (PAY ≥ 1) por grupo de edad y mes", "% of clients with a delay (PAY ≥ 1) by age group and month")))
  }
  r <- tapply(df[[TARGET]], df$AGE_GRP, mean); n <- tapply(df[[TARGET]], df$AGE_GRP, length)
  p <- plot_ly(x = fx(names(r)), y = as.numeric(r), type = "bar", customdata = as.numeric(n),
               marker = list(color = ifelse(r > GLOBAL_RATE, WARM_GOLD, NAVY)),
               text = pct(as.numeric(r)), textposition = "outside", cliponaxis = FALSE,
               hovertemplate = paste0(tx("Edad", "Age"), " %{x}<br>", tx("Tasa de default", "Default rate"), ": %{y:.1%}<br>",
                                      tx("Clientes", "Clients"), ": %{customdata:,}<extra></extra>"))
  p <- layout(p, xaxis = list(title = tx("Grupo de edad", "Age group")),
              yaxis = list(title = tx("Tasa de default", "Default rate"), tickformat = ".0%", range = c(0, max(r) * 1.2)),
              showlegend = FALSE, shapes = list(hline(GLOBAL_RATE)),
              annotations = list(nota(paste("Global", pct(GLOBAL_RATE)), 0, GLOBAL_RATE)))
  style_fig(p, 470, legend_top = FALSE, title = tx("Tasa de default por grupo de edad", "Default rate by age group"))
}

interp_age <- function(view) {
  gm <- age_means(MONTH_ORDER); gd <- tapply(df[[TARGET]], df$AGE_GRP, mean)
  gp <- age_means(MONTH_ORDER, function(v) mean(v >= 1))
  sp <- spearman(df$AGE, df$PAY_0); rho <- unname(sp$estimate); p <- sp$p.value
  hi <- names(gd)[which.max(gd)]; lo <- names(gd)[which.min(gd)]
  if (view == "lines") {
    pay0 <- gm[, "PAY_0"]
    basic <- tx(sprintf("Todas las edades siguen una forma parecida: el atraso promedio sube hacia los últimos meses (septiembre). El grupo con atraso más alto en el mes más reciente es %s años (%.2f) y el más bajo es %s (%.2f).",
                        names(pay0)[which.max(pay0)], max(pay0), names(pay0)[which.min(pay0)], min(pay0)),
                sprintf("All ages follow a similar shape: the average delay rises toward the last months (September). The group with the highest delay in the most recent month is %s years (%.2f) and the lowest is %s (%.2f).",
                        names(pay0)[which.max(pay0)], max(pay0), names(pay0)[which.min(pay0)], min(pay0)))
    tech <- tx(sprintf("Correlación de Spearman AGE–PAY_0: ρ = %+.3f (%s), relación muy débil. Los promedios de PAY mezclan los códigos −2/−1/0 (sin atraso) con atrasos ≥1, por lo que se complementan con la vista de %% con atraso.", rho, sig(p)),
               sprintf("Spearman correlation AGE–PAY_0: ρ = %+.3f (%s), a very weak relationship. PAY averages mix the codes −2/−1/0 (no delay) with delays ≥1, so they are complemented by the %% late view.", rho, sig(p)))
  } else if (view == "heat") {
    mx <- which(gp == max(gp), arr.ind = TRUE)[1, ]
    mes <- month_lbl()[mx[2]]; grp <- rownames(gp)[mx[1]]; v <- gp[mx[1], mx[2]] * 100
    basic <- tx(sprintf("Cada celda indica qué porcentaje de ese grupo de edad llevaba al menos un mes de atraso. El valor más alto aparece en %s años, mes de %s (%.1f%%). Las diferencias entre edades son pequeñas comparadas con las diferencias entre meses.", grp, mes, v),
                sprintf("Each cell shows what percentage of that age group was at least one month late. The highest value is at %s years, in %s (%.1f%%). Differences between ages are small compared with differences between months.", grp, mes, v))
    tech <- tx(sprintf("Proporción con PAY ≥ 1 entre %s y %s. Spearman AGE–PAY_0: ρ = %+.3f (%s). La edad aporta información marginal; el estado de pago de meses previos es el predictor dominante (ver SHAP en el notebook).", pct(min(gp)), pct(max(gp)), rho, sig(p)),
               sprintf("Share with PAY ≥ 1 between %s and %s. Spearman AGE–PAY_0: ρ = %+.3f (%s). Age adds marginal information; the repayment status of previous months is the dominant predictor (see SHAP in the notebook).", pct(min(gp)), pct(max(gp)), rho, sig(p)))
  } else {
    basic <- tx(sprintf("El riesgo es más alto en el grupo de %s años (%s) y más bajo en el de %s (%s). La relación con la edad es suave y no tan marcada como la del historial de pagos.", hi, pct(max(gd)), lo, pct(min(gd))),
                sprintf("Risk is highest in the %s age group (%s) and lowest in the %s group (%s). The relationship with age is mild and not as strong as that of payment history.", hi, pct(max(gd)), lo, pct(min(gd))))
    tech <- tx(sprintf("Tasa de default por grupo entre %s y %s (global %s). Patrón posiblemente no lineal (en forma de U suave); los grupos extremos de edad tienen menos observaciones y, por ende, estimaciones más inestables. Conviene considerar AGE con términos no lineales o categorizada en modelos paramétricos.", pct(min(gd)), pct(max(gd)), pct(GLOBAL_RATE)),
               sprintf("Default rate by group between %s and %s (overall %s). Possibly non-linear pattern (a mild U shape); the extreme age groups have fewer observations and therefore less stable estimates. AGE should be considered with non-linear terms or binned in parametric models.", pct(min(gd)), pct(max(gd)), pct(GLOBAL_RATE)))
  }
  list(basic, tech)
}

# ----- Módulo interactivo de cruce de variables ---------------------------
cross_fig <- function(x, y, c) {
  cdisc <- !is.null(c) && c != "none" && c %in% DISCRETE
  cnum <- !is.null(c) && c != "none" && !(c %in% DISCRETE)
  xd <- x %in% DISCRETE; yd <- y %in% DISCRETE
  rate_lbl <- tx("Tasa de default", "Default rate")

  # ------ numérica × numérica: dispersión + recta de tendencia --------------
  if (!xd && !yd) {
    set.seed(7); idx <- sample.int(nrow(df), min(4000, nrow(df))); d <- df[idx, ]
    p <- plot_ly()
    if (cdisc) {
      k <- as_cat(c, d[[c]]); lv <- levels(k)
      for (i in seq_along(lv)) {
        s <- k == lv[i]
        p <- add_trace(p, x = d[[x]][s], y = d[[y]][s], type = "scatter", mode = "markers", name = lv[i],
                       marker = list(color = PALETTE[(i - 1) %% 6 + 1], opacity = 0.55, size = 6), legendgroup = c)
      }
    } else if (cnum) {
      p <- add_trace(p, x = d[[x]], y = d[[y]], type = "scatter", mode = "markers", name = "",
                     marker = list(color = d[[c]], colorscale = list(c(0, NAVY), c(1, WARM_GOLD)), opacity = 0.6, size = 6,
                                   showscale = TRUE, colorbar = list(title = c, thickness = 14)), showlegend = FALSE)
    } else {
      p <- add_trace(p, x = d[[x]], y = d[[y]], type = "scatter", mode = "markers", name = "",
                     marker = list(color = NAVY, opacity = 0.45, size = 6), showlegend = FALSE)
    }
    m <- NA
    if (x != y) {
      fit <- stats::lm(df[[y]] ~ df[[x]]); m <- unname(stats::coef(fit)[2]); b0 <- unname(stats::coef(fit)[1])
      xs <- c(min(df[[x]]), max(df[[x]]))
      p <- add_trace(p, x = xs, y = m * xs + b0, type = "scatter", mode = "lines", name = tx("Tendencia lineal", "Linear trend"),
                     line = list(color = WARM_GOLD, width = 3, dash = "dash"))
    }
    p <- layout(p, xaxis = list(title = x, range = c(min(df[[x]]), q(df[[x]], .99) * 1.05)),
                yaxis = list(title = y, range = c(min(df[[y]]), q(df[[y]], .99) * 1.05)))
    p <- style_fig(p, 520, title = tx(sprintf("%s vs. %s (muestra de %s clientes)", y, x, num(nrow(d))),
                                       sprintf("%s vs. %s (sample of %s clients)", y, x, num(nrow(d)))))
    pr <- suppressWarnings(stats::cor.test(df[[x]], df[[y]])); sp <- spearman(df[[x]], df[[y]])
    rho <- unname(sp$estimate); a <- abs(rho)
    fuerza <- if (a < 0.2) tx("muy débil", "very weak") else if (a < 0.4) tx("débil", "weak") else
      if (a < 0.7) tx("moderada", "moderate") else tx("fuerte", "strong")
    sentido <- if (rho > 0) tx("positiva (suben juntas)", "positive (they rise together)") else
      tx("negativa (una sube cuando la otra baja)", "negative (one rises when the other falls)")
    basic <- tx(sprintf("Entre %s y %s hay una relación %s y %s. Cada punto es un cliente; la línea dorada resume la tendencia general.", x, y, fuerza, sentido),
                sprintf("There is a %s, %s relationship between %s and %s. Each point is a client; the gold line summarizes the overall trend.", fuerza, sentido, x, y))
    tech <- if (x != y) sprintf("Spearman ρ = %+.3f (%s); Pearson r = %+.3f (%s); n = %s. %s = %s.", rho, sig(sp$p.value),
                                unname(pr$estimate), sig(pr$p.value), num(nrow(df)), tx("Pendiente OLS", "OLS slope"), format(signif(m, 4))) else
      tx("x e y son la misma variable.", "x and y are the same variable.")
    return(list(p, basic, tech))
  }

  # ------ discreta × discreta -----------------------------------------------
  if (xd && yd) {
    if (x == y) {
      p <- style_fig(plot_ly(type = "scatter", mode = "markers"), 420,
                     title = tx("Elige dos variables distintas", "Choose two different variables"))
      return(list(p, tx("Selecciona variables distintas en X e Y.", "Select different variables for X and Y."), ""))
    }
    if (TARGET %in% c(x, y)) {
      other <- if (x == TARGET) y else x
      o <- as_cat(other); tgt <- df[[TARGET]]
      p <- plot_ly()
      if (cdisc && !(c %in% c(other, TARGET))) {
        k <- as_cat(c); lv <- levels(k)
        for (i in seq_along(lv)) {
          s <- k == lv[i]
          r <- tapply(tgt[s], droplevels(o[s]), mean); n <- tapply(tgt[s], droplevels(o[s]), length)
          p <- add_trace(p, x = names(r), y = as.numeric(r), type = "bar", name = lv[i], customdata = as.numeric(n),
                         marker = list(color = PALETTE[(i - 1) %% 6 + 1]),
                         hovertemplate = paste0("%{x}<br>", tx("Tasa", "Rate"), ": %{y:.1%}<br>n=%{customdata:,}<extra></extra>"))
        }
        p <- layout(p, barmode = "group")
      } else {
        r <- tapply(tgt, o, mean); n <- tapply(tgt, o, length); r <- r[!is.na(r)]; n <- n[names(r)]
        p <- add_trace(p, x = names(r), y = as.numeric(r), type = "bar", customdata = as.numeric(n), showlegend = FALSE,
                       marker = list(color = ifelse(r > GLOBAL_RATE, WARM_GOLD, NAVY)),
                       text = pct(as.numeric(r)), textposition = "outside", cliponaxis = FALSE,
                       hovertemplate = paste0("%{x}<br>", tx("Tasa", "Rate"), ": %{y:.1%}<br>n=%{customdata:,}<extra></extra>"))
      }
      p <- layout(p, xaxis = list(title = other, type = "category", categoryorder = "array", categoryarray = cat_order(other)),
                  yaxis = list(title = rate_lbl, tickformat = ".0%"),
                  shapes = list(hline(GLOBAL_RATE)), annotations = list(nota(paste("Global", pct(GLOBAL_RATE)), 0, GLOBAL_RATE)))
      p <- style_fig(p, 500, legend_top = cdisc, title = tx(paste("Tasa de default según", other), paste("Default rate by", other)))
      r <- tapply(tgt, o, mean); n <- tapply(tgt, o, length); ok <- !is.na(n) & n >= 30
      r <- r[ok]
      ct <- table(df[[other]], tgt); ch <- chi2_test(ct)
      basic <- tx(sprintf("La tasa de default más alta aparece en «%s» (%s) y la más baja en «%s» (%s), frente a %s en promedio.",
                          names(r)[which.max(r)], pct(max(r)), names(r)[which.min(r)], pct(min(r)), pct(GLOBAL_RATE)),
                  sprintf("The highest default rate is in “%s” (%s) and the lowest in “%s” (%s), versus %s on average.",
                          names(r)[which.max(r)], pct(max(r)), names(r)[which.min(r)], pct(min(r)), pct(GLOBAL_RATE)))
      tech <- tx(sprintf("χ²(%d) = %.1f (%s); V de Cramér = %.3f. Se muestran categorías con n ≥ 30 en el texto; las de muy baja frecuencia tienen tasas inestables.",
                         unname(ch$parameter), unname(ch$statistic), sig(ch$p.value), cramers_v(ct)),
                 sprintf("χ²(%d) = %.1f (%s); Cramér's V = %.3f. The text only mentions categories with n ≥ 30; very rare ones have unstable rates.",
                         unname(ch$parameter), unname(ch$statistic), sig(ch$p.value), cramers_v(ct)))
      if (cnum) tech <- paste0(tech, tx(" (La variable de color numérica se ignora en este gráfico.)",
                                        " (The numeric color variable is ignored in this chart.)"))
      return(list(p, basic, tech))
    }
    # discreta × discreta (sin target): heatmap de la tasa de default por celda
    lab <- function(col, v) if (col %in% names(CAT_LABELS)) unname(cat_labels(col)[as.character(v)]) else as.character(as.integer(v))
    xv <- sort(unique(df[[x]])); yv <- sort(unique(df[[y]]))
    piv <- tapply(df[[TARGET]], list(factor(df[[y]], yv), factor(df[[x]], xv)), mean)
    cnt <- tapply(df[[TARGET]], list(factor(df[[y]], yv), factor(df[[x]], xv)), length)
    txt <- ifelse(!is.na(cnt) & cnt >= 30, paste0(formatC(round(piv * 100, 1), format = "f", digits = 1), "%"), "")
    p <- plot_ly(z = unname(piv), x = lab(x, xv), y = lab(y, yv), type = "heatmap", colorscale = SEQ_GOLD,
                 customdata = unname(cnt), text = unname(txt), texttemplate = "%{text}",
                 colorbar = list(title = tx("Tasa default", "Default rate"), tickformat = ".0%", thickness = 14),
                 hovertemplate = paste0(x, ": %{x}<br>", y, ": %{y}<br>", tx("Tasa", "Rate"), ": %{z:.1%}<br>n=%{customdata:,}<extra></extra>"))
    p <- layout(p, xaxis = list(type = "category", title = x), yaxis = list(type = "category", autorange = "reversed", title = y))
    p <- style_fig(p, 520, legend_top = FALSE,
                   title = tx(sprintf("Tasa de default por combinación de %s × %s (celdas con n ≥ 30 rotuladas)", x, y),
                              sprintf("Default rate by combination of %s × %s (cells with n ≥ 30 labeled)", x, y)))
    ct <- table(df[[x]], df[[y]]); ch <- chi2_test(ct)
    ok <- which(!is.na(cnt) & cnt >= 30, arr.ind = TRUE)
    best <- ok[which.max(piv[ok]), ]
    tx_ <- lab(x, xv[best[2]]); ty_ <- lab(y, yv[best[1]]); v <- piv[best[1], best[2]]; n <- cnt[best[1], best[2]]
    basic <- tx(sprintf("La combinación con más incumplimiento (con al menos 30 clientes) es %s = %s y %s = %s, con %s de default (%s clientes).", x, tx_, y, ty_, pct(v), num(n)),
                sprintf("The combination with the most defaults (with at least 30 clients) is %s = %s and %s = %s, with %s default (%s clients).", x, tx_, y, ty_, pct(v), num(n)))
    tech <- tx(sprintf("Asociación entre %s y %s: χ²(%d) = %.1f (%s), V de Cramér = %.3f. El color muestra la tasa de default por celda; el módulo ignora la variable de color en este tipo de cruce.",
                       x, y, unname(ch$parameter), unname(ch$statistic), sig(ch$p.value), cramers_v(ct)),
               sprintf("Association between %s and %s: χ²(%d) = %.1f (%s), Cramér's V = %.3f. The color shows the default rate per cell; the module ignores the color variable in this type of cross.",
                       x, y, unname(ch$parameter), unname(ch$statistic), sig(ch$p.value), cramers_v(ct)))
    return(list(p, basic, tech))
  }

  # ------ discreta × numérica (cualquier orientación) ------------------------
  catv <- if (xd) x else y; numv <- if (xd) y else x
  horizontal <- !xd
  k <- as_cat(catv); v <- df[[numv]]
  grupos <- list(list(sel = rep(TRUE, nrow(df)), name = "", color = NAVY))
  colorear <- cdisc && c != catv
  if (colorear) {
    kc <- as_cat(c); lv <- levels(kc)
    grupos <- lapply(seq_along(lv), function(i) list(sel = kc == lv[i], name = lv[i], color = PALETTE[(i - 1) %% 6 + 1]))
  }
  p <- plot_ly()
  his <- c(); los <- c()
  for (g in grupos) {
    kk <- k[g$sel]; vv <- v[g$sel]
    args <- list(p, type = "box", name = g$name, boxpoints = "outliers", boxmean = TRUE, showlegend = colorear,
                 marker = list(color = g$color, size = 3, opacity = 0.3), line = list(color = g$color),
                 fillcolor = rgba(g$color, 0.5), legendgroup = g$name)
    if (horizontal) { args$x <- vv; args$y <- as.character(kk); args$orientation <- "h" } else { args$x <- as.character(kk); args$y <- vv }
    p <- do.call(add_trace, args)
    for (lv_ in unique(as.character(kk))) {
      s <- vv[as.character(kk) == lv_]
      q1 <- q(s, .25); q3 <- q(s, .75)
      his <- c(his, min(q3 + 1.5 * (q3 - q1), max(s))); los <- c(los, max(q1 - 1.5 * (q3 - q1), min(s)))
    }
  }
  hi <- max(his); lo <- min(los); pad <- (hi - lo) * 0.06
  cat_ax <- list(title = catv, type = "category", categoryorder = "array", categoryarray = cat_order(catv))
  num_ax <- list(title = numv, range = c(lo - pad, hi + pad))
  p <- if (horizontal) layout(p, xaxis = num_ax, yaxis = cat_ax) else layout(p, xaxis = cat_ax, yaxis = num_ax)
  if (colorear) p <- layout(p, boxmode = "group")
  p <- style_fig(p, 520, legend_top = colorear, title = tx(paste(numv, "según", catv), paste(numv, "by", catv)))
  meds <- tapply(v, k, stats::median); meds <- meds[!is.na(meds)]
  meds_txt <- paste(sprintf("%s: %s", names(meds), vapply(meds, function(z) fmt_val(numv, z), ""))[seq_len(min(8, length(meds)))], collapse = "; ")
  groups <- split(v, k); groups <- groups[vapply(groups, length, 0) > 5]
  if (length(groups) >= 2) {
    kw <- stats::kruskal.test(groups); H <- unname(kw$statistic); p_ <- kw$p.value; eps <- H / (nrow(df) - 1)
  } else { H <- NA; p_ <- NA; eps <- NA }
  hk <- names(meds)[which.max(meds)]; lk <- names(meds)[which.min(meds)]
  basic <- tx(sprintf("La mediana de %s es mayor en «%s» (%s) y menor en «%s» (%s). Las cajas muestran dónde está el 50%% central de cada grupo.",
                      numv, hk, fmt_val(numv, max(meds)), lk, fmt_val(numv, min(meds))),
              sprintf("The median of %s is highest in “%s” (%s) and lowest in “%s” (%s). The boxes show where the middle 50%% of each group lies.",
                      numv, hk, fmt_val(numv, max(meds)), lk, fmt_val(numv, min(meds))))
  tech <- tx(sprintf("Kruskal-Wallis H = %.1f (%s), ε² = %.4f. Medianas por grupo → %s. Con muestras grandes el p-value es casi siempre significativo; se debe valorar el tamaño del efecto.", H, sig(p_), eps, meds_txt),
             sprintf("Kruskal-Wallis H = %.1f (%s), ε² = %.4f. Medians by group → %s. With large samples the p-value is almost always significant; the effect size should be assessed.", H, sig(p_), eps, meds_txt))
  list(p, basic, tech)
}

fig_splom <- function(vars_) {
  set.seed(3); d <- df[sample.int(nrow(df), min(1500, nrow(df))), ]
  p <- plot_ly(type = "splom", dimensions = lapply(vars_, function(v) list(label = v, values = d[[v]])),
               marker = list(color = d[[TARGET]], colorscale = list(c(0, NAVY), c(1, WARM_GOLD)), size = 4,
                             opacity = 0.55, line = list(width = 0)),
               diagonal = list(visible = TRUE), showupperhalf = FALSE,
               text = ifelse(d[[TARGET]] == 1, "Default", "No default"), hoverinfo = "text+x+y")
  style_fig(p, max(480, 170 * length(vars_) + 120), legend_top = FALSE,
            title = tx("Matriz de dispersión (azul = no default · dorado = default) · muestra de 1,500 clientes",
                       "Scatter matrix (blue = no default · gold = default) · sample of 1,500 clients"))
}

interp_splom <- function(vars_) {
  nm <- ifelse(vars_ == TARGET, "default", vars_)
  c <- CORR[nm, nm, drop = FALSE]
  idx <- which(upper.tri(c), arr.ind = TRUE)
  pairs <- data.frame(a = rownames(c)[idx[, 1]], b = colnames(c)[idx[, 2]], r = c[idx])
  pairs <- pairs[order(-abs(pairs$r)), ]
  a <- pairs$a[1]; b <- pairs$b[1]; r <- pairs$r[1]
  basic <- tx(sprintf("De las variables elegidas, las que más se parecen entre sí son %s y %s (relación %s). Si los puntos dorados (default) se agrupan en una zona, esa combinación de variables separa a los clientes de riesgo.",
                      a, b, if (r > 0) "directa" else "inversa"),
              sprintf("Among the chosen variables, the most similar are %s and %s (%s relationship). If the gold points (default) cluster in one area, that combination of variables separates the risky clients.",
                      a, b, if (r > 0) "direct" else "inverse"))
  top <- head(pairs, 4)
  pares <- paste(sprintf("%s–%s ρ = %+.2f", top$a, top$b, top$r), collapse = "; ")
  tech <- tx(sprintf("Spearman de los pares más fuertes: %s. Útil para detectar colinealidad entre predictores y regiones del espacio donde se concentra la clase 1.", pares),
             sprintf("Spearman of the strongest pairs: %s. Useful to detect collinearity between predictors and regions of the space where class 1 concentrates.", pares))
  list(basic, tech)
}

# ----- Hallazgos clave (tarjetas finales) ---------------------------------
key_findings <- function() {
  c <- CORR
  bill <- triu(c[BILL_COLS, BILL_COLS])
  t <- c[, "default"][rownames(c) != "default"]; t_top <- names(t)[which.max(abs(t))]; t_rho <- t[[t_top]]
  g1 <- stats::median(df$LIMIT_BAL[df[[TARGET]] == 1]); g0 <- stats::median(df$LIMIT_BAL[df[[TARGET]] == 0])
  r_late <- mean(df[[TARGET]][df$PAY_0 >= 1]); r_ok <- mean(df[[TARGET]][df$PAY_0 < 1])
  te <- rate_table("EDUCATION")$mean
  list(
    list(tx("El historial de pagos domina", "Payment history dominates"),
         tx(sprintf("%s es la variable más asociada al default (ρ de Spearman = %+.2f). Los clientes con ≥1 mes de atraso en PAY_0 incumplen en %s de los casos, frente a %s de quienes están al día.", t_top, t_rho, pct(r_late), pct(r_ok)),
            sprintf("%s is the variable most associated with default (Spearman ρ = %+.2f). Clients with ≥1 month of delay in PAY_0 default in %s of cases, versus %s of those who are up to date.", t_top, t_rho, pct(r_late), pct(r_ok)))),
    list(tx("Multicolinealidad en la facturación", "Multicollinearity in billing"),
         tx(sprintf("Las seis BILL_AMT se correlacionan (Spearman) entre %.2f y %.2f. Para modelos lineales conviene resumirlas (promedio + tendencia) o usar PCA.", min(bill), max(bill)),
            sprintf("The six BILL_AMT correlate (Spearman) between %.2f and %.2f. For linear models it is better to summarize them (average + trend) or use PCA.", min(bill), max(bill)))),
    list(tx("Límite de crédito más bajo en default", "Lower credit limit among defaulters"),
         tx(sprintf("Mediana de LIMIT_BAL: %s (default) vs. %s (no default). Un menor cupo se asocia con mayor riesgo.", nt(g1), nt(g0)),
            sprintf("Median LIMIT_BAL: %s (default) vs. %s (no default). A lower limit is associated with higher risk.", nt(g1), nt(g0)))),
    list(tx("El perfil demográfico pesa poco", "The demographic profile matters little"),
         tx(sprintf("Las tasas por educación van de %s a %s: diferencias significativas pero con tamaño de efecto pequeño. La edad tampoco separa por sí sola.", pct(min(te)), pct(max(te))),
            sprintf("Rates by education range from %s to %s: significant differences but with a small effect size. Age alone does not separate either.", pct(min(te)), pct(max(te)))))
  )
}
