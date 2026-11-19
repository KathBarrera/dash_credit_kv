# =============================================================================
# 6b. CS-FOF EN R: predicción con los árboles exportados del modelo entrenado en Python
# =============================================================================
# shiny/herramientas/exportar_cs_fof.py escribe en modelo/ los nodos de los 359 árboles del CS-FOF del Dash
# (dash/modelo/modelo_cs_fof.pkl). Aquí se recorren igual que `_ArbolCSFOF.proba1` de original_model.py:
# en cada nodo interno el cliente va a la izquierda si  sum_j coef_j · z_{col_j} <= umbral  (un corte por eje
# es el caso con una sola columna y coeficiente 1), y la probabilidad es el promedio de las hojas.
# modelo/cs_fof_verificacion.csv trae 300 clientes de prueba con la probabilidad de Python para comprobarlo.
CSFOF <- tryCatch(local({
  meta <- jsonlite::fromJSON("modelo/cs_fof_meta.json", simplifyVector = TRUE)
  con <- gzfile("modelo/cs_fof_bosque.bin.gz", "rb"); on.exit(close(con))
  n <- meta$n_nodos; w <- meta$ancho
  leer_i <- function(k) readBin(con, "integer", k, size = 4, endian = "little")
  leer_d <- function(k) readBin(con, "double", k, size = 8, endian = "little")
  feat <- matrix(leer_i(n * w), ncol = w, byrow = TRUE)
  izq <- leer_i(n); der <- leer_i(n)
  coef <- matrix(leer_d(n * w), ncol = w, byrow = TRUE)
  thr <- leer_d(n); valor <- leer_d(n)
  stopifnot(length(valor) == n)
  list(meta = meta, feat = feat, coef = coef, thr = thr, izq = izq, der = der, valor = valor,
       inicio = c(0L, cumsum(meta$nodos_por_arbol))[seq_along(meta$nodos_por_arbol)])
}), error = function(e) { message("[cs_fof] no se pudo cargar: ", conditionMessage(e)); NULL })

# Suma en double, de izquierda a derecha, como numpy en filas cortas. rowSums y rowMeans de R acumulan en
# precisión extendida y pueden diferir en el último bit; eso basta para cambiar de rama cuando un cliente cae
# justo en el umbral de un corte (pasa con perfiles repetidos del entrenamiento).
.suma_np <- function(M) Reduce(`+`, lapply(seq_len(ncol(M)), function(j) M[, j]))

# 23 variables originales -> matriz con las 25 columnas del pipeline de Python (one-hot + resto), en su orden.
# La usan CS-FOF (que además la estandariza) y XGBoost (R/06c_xgboost.R): los dos pipelines del Dash son iguales.
pipeline_matriz <- function(d, columnas) {
  v <- preparar_variables(d)
  bills <- as.matrix(as.data.frame(d)[BILL_COLS]); storage.mode(bills) <- "double"
  tc <- as.numeric(5:0) - 2.5
  v$BILL_AMT_MEAN_6M_LOG <- signed_log1p(.suma_np(bills) / 6)
  v$BILL_AMT_TREND_6M_LOG <- signed_log1p(.suma_np(sweep(bills, 2, tc, "*")) / sum(tc^2))
  cols <- lapply(columnas, function(cn) {
    for (c in c("SEX", "EDUCATION", "MARRIAGE")) if (startsWith(cn, paste0(c, "_")))
      return(as.numeric(as.character(v[[c]]) == sub(paste0(c, "_"), "", cn)))
    as.numeric(v[[cn]])
  })
  X <- matrix(unlist(cols), ncol = length(cols))
  X[is.na(X)] <- 0                                   # categoría desconocida: todas las columnas en 0 (handle_unknown)
  X
}

# Matriz estandarizada de CS-FOF (la estandarización es parte del bosque en original_model.py)
cs_fof_matriz <- function(d) {
  m <- CSFOF$meta
  sweep(sweep(pipeline_matriz(d, m$columnas), 2, m$media, "-"), 2, m$escala, "/")
}

# Probabilidad de cada árbol (filas = clientes, columnas = árboles)
cs_fof_hojas <- function(Z) {
  B <- CSFOF; n <- nrow(Z); w <- ncol(B$feat); nt <- length(B$inicio)
  out <- matrix(0, n, nt)
  for (t in seq_len(nt)) {
    o <- B$inicio[t]; nodo <- rep(o + 1L, n)
    activos <- seq_len(n)
    repeat {
      nd <- nodo[activos]
      interno <- B$izq[nd] >= 0
      activos <- activos[interno]; nd <- nd[interno]
      if (!length(activos)) break
      f <- B$feat[nd, , drop = FALSE]
      zv <- matrix(Z[cbind(rep(activos, w), as.vector(pmax(f, 0)) + 1L)], ncol = w)
      proy <- .suma_np(ifelse(f >= 0, zv, 0) * B$coef[nd, , drop = FALSE])
      nodo[activos] <- o + 1L + ifelse(proy <= B$thr[nd], B$izq[nd], B$der[nd])
    }
    out[, t] <- B$valor[nodo]
  }
  out
}

cs_fof_proba <- function(d) rowMeans(cs_fof_hojas(cs_fof_matriz(d)))
