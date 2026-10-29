# =============================================================================
# 3. EDA UNIVARIADO: FIGURAS E INTERPRETACIONES
# =============================================================================

fig_target <- function() {
  vc <- table(df[[TARGET]]); pr <- vc / sum(vc)
  p <- plot_ly(x = fx(c("No default (0)", "Default (1)")), y = as.numeric(vc), type = "bar",
               marker = list(color = MONO), textposition = "outside", cliponaxis = FALSE,
               text = sprintf("%s<br><b>%s</b>", num(as.numeric(vc)), pct(as.numeric(pr))),
               hovertemplate = paste0("%{x}<br>%{y:,} ", tx("clientes", "clients"), "<extra></extra>"))
  p <- layout(p, yaxis = list(title = tx("Número de clientes", "Number of clients"), range = c(0, max(vc) * 1.18)),
              xaxis = list(title = ""), showlegend = FALSE)
  style_fig(p, 478, legend_top = FALSE,
            title = tx("Variable objetivo: default payment next month", "Target variable: default payment next month"))
}

target_strip <- function() {
  vc <- table(df[[TARGET]]); p0 <- vc[["0"]] / nrow(df); p1 <- vc[["1"]] / nrow(df)
  div(class = "target-strip",
      div(class = "ts-head", tags$span(class = "ts-lbl", tx("Proporción de clases", "Class proportion")),
          tags$span(class = "ts-ratio", tx("Razón ", "Ratio "), tags$b(sprintf("%.1f : 1", vc[["0"]] / vc[["1"]])))),
      div(class = "ts-bar",
          div(class = "ts-seg ts-0", style = sprintf("width:%.2f%%", 100 * p0), paste("No default", pct(p0))),
          div(class = "ts-seg ts-1", style = sprintf("width:%.2f%%", 100 * p1), paste("Default", pct(p1)))))
}

interp_target <- function() {
  vc <- table(df[[TARGET]]); n1 <- vc[["1"]]; n0 <- vc[["0"]]
  p1 <- n1 / nrow(df); p0 <- n0 / nrow(df); ratio <- n0 / n1
  basic <- tx(
    sprintf("Aproximadamente %.0f de cada 100 clientes (%s personas) no pagó la tarjeta al mes siguiente. El resto (%s) sí cumplió. Hay muchos más clientes cumplidos que incumplidos, lo que hay que tener en cuenta al construir modelos.",
            p1 * 100, num(n1), pct(p0)),
    sprintf("About %.0f out of every 100 clients (%s people) did not pay their card the following month. The rest (%s) did pay. There are many more paying clients than defaulting ones, which must be taken into account when building models.",
            p1 * 100, num(n1), pct(p0)))
  tech <- tx(
    sprintf("Desbalance de clases: %s (clase 0) vs. %s (clase 1), razón ≈ %.1f:1. Un clasificador sin ajustes tenderá a favorecer la clase mayoritaria; se recomienda class_weight='balanced', remuestreo (SMOTE/ADASYN) o umbrales ajustados, y evaluar con AUC-ROC, F1 y recall de la clase 1 en lugar de accuracy.",
            pct(p0), pct(p1), ratio),
    sprintf("Class imbalance: %s (class 0) vs. %s (class 1), ratio ≈ %.1f:1. An unadjusted classifier will tend to favor the majority class; class_weight='balanced', resampling (SMOTE/ADASYN) or adjusted thresholds are recommended, and evaluation should use ROC-AUC, F1 and class-1 recall instead of accuracy.",
            pct(p0), pct(p1), ratio))
  list(basic, tech)
}

fig_uni <- function(col) {
  if (col %in% DISCRETE) {
    vc <- table(as_cat(col)); pr <- vc / sum(vc)
    p <- plot_ly(x = fx(names(vc)), y = as.numeric(vc), type = "bar", marker = list(color = MONO),
                 text = pct(as.numeric(pr)), textposition = "outside", cliponaxis = FALSE,
                 hovertemplate = paste0(col, ": %{x}<br>", tx("Clientes", "Clients"), ": %{y:,}<extra></extra>"))
    p <- layout(p, xaxis = list(title = col, type = "category", categoryorder = "array", categoryarray = names(vc)),
                yaxis = list(title = tx("Número de clientes", "Number of clients"), range = c(0, max(vc) * 1.15)),
                showlegend = FALSE)
    return(style_fig(p, 470, legend_top = FALSE,
                     title = tx(paste("Frecuencia de", pretty_var(col)), paste("Frequency of", pretty_var(col)))))
  }
  s <- df[[col]]
  q1 <- q(s, .25); q3 <- q(s, .75)
  top <- max(q(s, .99), min(q3 + 1.5 * (q3 - q1), max(s)))
  view <- s[s <= top]
  # Histograma arriba y boxplot abajo, compartiendo el eje X (ejes manuales para conservar la línea de la mediana)
  p <- plot_ly()
  p <- add_trace(p, x = view, type = "histogram", nbinsx = 60, showlegend = FALSE, yaxis = "y2",
                 marker = list(color = MONO, line = list(color = WHITE, width = 0.4)), name = tx("Frecuencia", "Frequency"))
  p <- add_trace(p, x = s, type = "box", name = "", boxpoints = "outliers", boxmean = TRUE, showlegend = FALSE, yaxis = "y",
                 marker = list(color = MONO, size = 3, opacity = 0.35), line = list(color = MONO), fillcolor = rgba(MONO, 0.5))
  lo <- min(s) - (top - min(s)) * 0.02
  n_out <- sum(s > top)
  suf <- if (n_out > 0) paste0("<br><span style='font-size:12px;font-weight:400'>",
                               tx(sprintf("%s valores extremos quedan fuera de la vista (se ven como atípicos en el boxplot)", num(n_out)),
                                  sprintf("%s extreme values fall outside the view (shown as outliers in the boxplot)", num(n_out))),
                               "</span>") else ""
  p <- layout(p,
              xaxis = list(title = pretty_var(col), range = c(lo, if (top > 0) top * 1.02 else top), anchor = "y"),
              yaxis = list(domain = c(0, 0.26), showticklabels = FALSE, title = ""),
              yaxis2 = list(domain = c(0.29, 1), title = tx("Frecuencia", "Frequency"), anchor = "x"),
              shapes = list(modifyList(vline(stats::median(s), color = WARM_GOLD, yref = "paper"), list(y0 = 0.285))),
              annotations = list(nota(tx("mediana", "median"), stats::median(s), 1, xref = "x", yref = "paper",
                                      color = WARM_GOLD, yanchor = "top")))
  style_fig(p, 520, legend_top = FALSE,
            title = tx(paste0("Distribución de ", pretty_var(col), suf), paste0("Distribution of ", pretty_var(col), suf)))
}

interp_uni <- function(col) {
  n <- nrow(df)
  if (col == TARGET) return(interp_target())
  if (col %in% DISCRETE) {
    vc <- table(as_cat(col)); pr <- vc / sum(vc)
    top <- names(pr)[which.max(pr)]
    if (col %in% PAY_COLS) {
      al_dia <- mean(df[[col]] <= 0); atraso <- mean(df[[col]] >= 1)
      mes <- month(if (col == "PAY_0") 1 else as.integer(substring(col, 5)))
      basic <- tx(sprintf("En %s, %s de los clientes estaba al día (valores 0 o menores) y %s tenía al menos un mes de atraso. El valor más común es %s (%s).",
                          mes, pct(al_dia, 0), pct(atraso, 0), top, pct(pr[[top]], 0)),
                  sprintf("In %s, %s of clients were up to date (values of 0 or less) and %s were at least one month late. The most common value is %s (%s).",
                          mes, pct(al_dia, 0), pct(atraso, 0), top, pct(pr[[top]], 0)))
      tech <- tx(sprintf("Variable ordinal con %d niveles; moda = %s (%s). Los valores −2, −1 y 0 concentran %s de los casos; atraso ≥1 mes: %s. La definición exacta de −2/−1/0 no está estandarizada en la fuente: se conservan sin recodificar y no se sobre-interpreta la frontera entre ellos. Se recomienda tratarla como ordinal/categórica (dummies) pues el efecto de pasar de 'al día' a 1 mes de atraso no es lineal.",
                         length(vc), top, pct(pr[[top]]), pct(al_dia), pct(atraso)),
                 sprintf("Ordinal variable with %d levels; mode = %s (%s). Values −2, −1 and 0 account for %s of cases; delay ≥1 month: %s. The exact definition of −2/−1/0 is not standardized in the source: they are kept without recoding and the boundary between them is not over-interpreted. Treating it as ordinal/categorical (dummies) is recommended, since going from 'up to date' to 1 month late is not a linear effect.",
                         length(vc), top, pct(pr[[top]]), pct(al_dia), pct(atraso)))
      return(list(basic, tech))
    }
    parts <- paste(sprintf("%s %s", names(pr), pct(as.numeric(pr))), collapse = ", ")
    basic <- tx(sprintf("La categoría más frecuente es «%s» con %s de los clientes. Distribución completa: %s.", top, pct(pr[[top]], 0), parts),
                sprintf("The most frequent category is “%s” with %s of clients. Full distribution: %s.", top, pct(pr[[top]], 0), parts))
    tech <- tx(sprintf("Variable categórica nominal de %d niveles; moda «%s» (%s). Frecuencias: %s. Las categorías no documentadas del archivo original se reagruparon en «Otros» (EDUCATION 0/5/6 → 4; MARRIAGE 0 → 3).",
                       length(vc), top, pct(pr[[top]]), parts),
               sprintf("Nominal categorical variable with %d levels; mode “%s” (%s). Frequencies: %s. Undocumented categories in the original file were grouped into “Others” (EDUCATION 0/5/6 → 4; MARRIAGE 0 → 3).",
                       length(vc), top, pct(pr[[top]]), parts))
    return(list(basic, tech))
  }
  s <- df[[col]]
  q1 <- q(s, .25); q3 <- q(s, .75); iqr <- q3 - q1
  sk <- skewness(s); ku <- kurtosis(s); out <- tukey_outliers_pct(s)
  f <- function(v) fmt_val(col, v)
  shape <- if (sk > 1) {
    tx(sprintf("La mayoría de clientes se ubica entre %s y %s, pero unos pocos tienen valores mucho más altos (hasta %s). Por eso el promedio (%s) queda por encima de lo típico (mediana %s).",
               f(q1), f(q3), f(max(s)), f(mean(s)), f(stats::median(s))),
       sprintf("Most clients fall between %s and %s, but a few have much higher values (up to %s). That is why the mean (%s) sits above the typical value (median %s).",
               f(q1), f(q3), f(max(s)), f(mean(s)), f(stats::median(s))))
  } else if (sk > 0.5) {
    tx(sprintf("La mitad de los clientes tiene %s o menos; la distribución se inclina ligeramente hacia valores altos (promedio %s).", f(stats::median(s)), f(mean(s))),
       sprintf("Half of the clients have %s or less; the distribution leans slightly toward high values (mean %s).", f(stats::median(s)), f(mean(s))))
  } else {
    tx(sprintf("Los valores se reparten de forma bastante equilibrada alrededor de %s (promedio %s).", f(stats::median(s)), f(mean(s))),
       sprintf("Values are fairly evenly spread around %s (mean %s).", f(stats::median(s)), f(mean(s))))
  }
  extra <- ""
  if (startsWith(col, "BILL_AMT") && any(s < 0))
    extra <- tx(sprintf(" Un %s de los clientes tiene saldo a favor (monto negativo).", pct(mean(s < 0))),
                sprintf(" %s of clients have a credit balance (negative amount).", pct(mean(s < 0))))
  if (startsWith(col, "PAY_AMT"))
    extra <- tx(sprintf(" Un %s de los clientes no hizo ningún pago ese mes.", pct(mean(s == 0))),
                sprintf(" %s of clients made no payment that month.", pct(mean(s == 0))))
  rec <- if (abs(sk) > 2) tx("Su asimetría extrema justifica una transformación logarítmica (con signo) antes de modelar.",
                             "Its extreme skewness justifies a (signed) log transformation before modeling.") else
    tx("No requiere transformaciones drásticas por forma.", "Its shape does not require drastic transformations.")
  tech <- tx(sprintf("n = %s; media = %s; mediana = %s; σ = %s; IQR = %s; asimetría = %.2f; curtosis = %.2f; outliers de Tukey = %.1f%%. %s",
                     num(n), f(mean(s)), f(stats::median(s)), f(stats::sd(s)), f(iqr), sk, ku, out, rec),
             sprintf("n = %s; mean = %s; median = %s; σ = %s; IQR = %s; skewness = %.2f; kurtosis = %.2f; Tukey outliers = %.1f%%. %s",
                     num(n), f(mean(s)), f(stats::median(s)), f(stats::sd(s)), f(iqr), sk, ku, out, rec))
  list(paste0(shape, extra), tech)
}

# ----- Distribuciones de variables cuantitativas por familia ------------------
FAMILIES <- list(LIMIT_BAL = "LIMIT_BAL", AGE = "AGE", BILL_AMT = BILL_COLS, PAY_AMT = PAYAMT_COLS)

kde_curve <- function(x, lo, hi, n = 220) {
  x <- x[x >= lo & x <= hi]
  if (length(x) > 6000) { set.seed(1); x <- sample(x, 6000) }
  bw <- stats::sd(x) * length(x)^(-1 / 5)          # regla de Scott (= scipy gaussian_kde)
  if (!is.finite(bw) || bw <= 0) return(list(x = seq(lo, hi, length.out = n), y = rep(0, n)))
  d <- stats::density(x, bw = bw, from = lo, to = hi, n = n)
  list(x = d$x, y = d$y)
}

fig_quant <- function(family, kind) {
  cols <- FAMILIES[[family]]
  allv <- unlist(df[cols], use.names = FALSE)
  lo <- q(allv, .01); hi <- q(allv, .99)            # vista P1–P99
  multi <- length(cols) > 1
  p <- plot_ly()
  for (i in seq_along(cols)) {
    c <- cols[i]; color <- if (multi) SERIES6[(i - 1) %% 6 + 1] else MONO
    if (kind == "hist") {
      v <- df[[c]][df[[c]] >= lo & df[[c]] <= hi]
      p <- add_trace(p, x = v, type = "histogram", nbinsx = 50, name = c, showlegend = multi,
                     marker = list(color = color), opacity = if (multi) 0.65 else 0.95)
    } else if (kind == "box") {
      p <- add_trace(p, y = df[[c]], type = "box", name = c, boxpoints = FALSE, boxmean = TRUE, showlegend = multi,
                     marker = list(color = color), line = list(color = color), fillcolor = rgba(color, 0.5))
    } else {
      k <- kde_curve(df[[c]], lo, hi)
      p <- add_trace(p, x = k$x, y = k$y, type = "scatter", mode = "lines", name = c, showlegend = multi,
                     line = list(color = color, width = 2.5), fill = "tozeroy", fillcolor = rgba(color, 0.18))
    }
  }
  if (kind == "hist") {
    p <- layout(p, barmode = "overlay", xaxis = list(title = family), yaxis = list(title = tx("Frecuencia", "Frequency")))
    ttl <- tx("Histograma", "Histogram")
  } else if (kind == "box") {
    ya <- list(title = family)
    if (family %in% c("BILL_AMT", "PAY_AMT")) ya$range <- c(min(0, lo * 1.1), hi * 1.1)
    p <- layout(p, yaxis = ya, xaxis = list(title = ""))
    ttl <- "Boxplot"
  } else {
    p <- layout(p, xaxis = list(title = family), yaxis = list(title = tx("Densidad", "Density")))
    ttl <- tx("Densidad (KDE)", "Density (KDE)")
  }
  sub <- if (kind == "box" && !family %in% c("BILL_AMT", "PAY_AMT")) "" else tx(" · vista P1–P99", " · P1–P99 view")
  style_fig(p, 480, legend_top = multi,
            title = tx(sprintf("%s de %s%s", ttl, family, sub), sprintf("%s of %s%s", ttl, family, sub)))
}

interp_quant <- function(family) {
  if (family %in% c("LIMIT_BAL", "AGE")) return(interp_uni(family))
  cols <- FAMILIES[[family]]
  med <- vapply(df[cols], stats::median, 0)
  sk <- vapply(df[cols], skewness, 0)
  if (family == "BILL_AMT") {
    neg <- mean(apply(df[cols] < 0, 1, any))
    o <- vapply(df[cols], tukey_outliers_pct, 0)
    basic <- tx(sprintf("Los seis meses de facturación se parecen mucho entre sí: la mediana ronda %s–%s y casi todos los meses tienen unos pocos clientes con saldos muy altos. Además, %s de los clientes tuvo saldo a favor (negativo) en algún mes.",
                        nt(min(med)), nt(max(med)), pct(neg)),
                sprintf("The six billing months look very much alike: the median is around %s–%s and almost every month has a few clients with very high balances. Also, %s of clients had a credit (negative) balance in some month.",
                        nt(min(med)), nt(max(med)), pct(neg)))
    tech <- tx(sprintf("Asimetría entre %.2f y %.2f; outliers de Tukey entre %.1f%% y %.1f%%. Distribuciones casi idénticas mes a mes (alta autocorrelación del saldo). Los montos negativos son económicamente válidos (pago en exceso) y no se eliminan. Esta redundancia anticipa multicolinealidad severa (ver VIF en el notebook / pestaña Multivariado).",
                       min(sk), max(sk), min(o), max(o)),
               sprintf("Skewness between %.2f and %.2f; Tukey outliers between %.1f%% and %.1f%%. Nearly identical distributions month after month (high autocorrelation of the balance). Negative amounts are economically valid (overpayment) and are kept. This redundancy anticipates severe multicollinearity (see VIF in the notebook / Multivariate page).",
                       min(sk), max(sk), min(o), max(o)))
  } else {
    zeros <- vapply(df[cols], function(x) mean(x == 0), 0)
    mx <- max(unlist(df[cols]))
    basic <- tx(sprintf("Los pagos son pequeños frente a las facturas: la mediana mensual va de %s a %s. Entre %s y %s de los clientes no pagó nada en cada mes; unos pocos hacen pagos enormes.",
                        nt(min(med)), nt(max(med)), pct(min(zeros), 0), pct(max(zeros), 0)),
                sprintf("Payments are small compared with bills: the monthly median ranges from %s to %s. Between %s and %s of clients paid nothing in each month; a few make huge payments.",
                        nt(min(med)), nt(max(med)), pct(min(zeros), 0), pct(max(zeros), 0)))
    tech <- tx(sprintf("Asimetría entre %.1f y %.1f (hasta ≈ %.0f), curtosis muy alta y cola derecha extrema (máx. %s). La masa en cero (sin pago) y los valores extremos justifican transformación log con signo y métodos robustos (medianas, Mann-Whitney) antes de comparar grupos.",
                       min(sk), max(sk), max(sk), nt(mx)),
               sprintf("Skewness between %.1f and %.1f (up to ≈ %.0f), very high kurtosis and an extreme right tail (max. %s). The mass at zero (no payment) and the extreme values justify a signed log transformation and robust methods (medians, Mann-Whitney) before comparing groups.",
                       min(sk), max(sk), max(sk), nt(mx)))
  }
  list(basic, tech)
}
