# =============================================================================
# 6. VARIABLES DEL MODELO (las mismas transformaciones del proyecto Credit_Card_Project)
# =============================================================================
# Réplica de src/preprocessing.py::build_final_dataset (y de dash/modelo/features.py):
#   1. EDUCATION 0, 5, 6 -> 4 («Otros») y MARRIAGE 0 -> 3 («Otros»).
#   2. BILL_AMT1–6 se resumen en nivel medio (log con signo), tendencia mensual (log con
#      signo) y número de meses con saldo a favor.
#   3. Log con signo de LIMIT_BAL y PAY_AMT1–6.

signed_log1p <- function(x) sign(x) * log1p(abs(x))

preparar_variables <- function(X) {
  d <- as.data.frame(X)[INPUT_COLS]
  d$EDUCATION[d$EDUCATION %in% c(0, 5, 6)] <- 4
  d$MARRIAGE[d$MARRIAGE == 0] <- 3
  bills <- as.matrix(d[BILL_COLS])
  t <- as.numeric(5:0)                                # BILL_AMT1 (sep) = 5 ... BILL_AMT6 (abr) = 0
  tc <- t - mean(t)
  slope <- as.numeric(bills %*% tc) / sum(tc^2)
  out <- data.frame(
    SEX = factor(d$SEX, levels = c(1, 2)),
    EDUCATION = factor(d$EDUCATION, levels = 1:4),
    MARRIAGE = factor(d$MARRIAGE, levels = 1:3),
    AGE = d$AGE)
  for (c in PAY_COLS) out[[c]] <- d[[c]]
  out$BILL_AMT_MEAN_6M_LOG <- signed_log1p(rowMeans(bills))
  out$BILL_AMT_TREND_6M_LOG <- signed_log1p(slope)
  out$N_CREDIT_BALANCE_MONTHS <- rowSums(bills < 0)
  for (c in c("LIMIT_BAL", PAYAMT_COLS)) out[[paste0(c, "_LOG")]] <- signed_log1p(as.numeric(d[[c]]))
  out
}
