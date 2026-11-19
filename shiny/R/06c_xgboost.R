# =============================================================================
# 6c. XGBOOST EN R: predicción con los árboles exportados del modelo entrenado en Python
# =============================================================================
# shiny/herramientas/exportar_xgboost.py escribe en modelo/ los 147 árboles del XGBoost del Dash
# (dash/modelo/modelo_xgboost.pkl), con sus umbrales float32 exactos. Aquí se recorren como lo hace XGBoost:
# en cada nodo interno el cliente va a la izquierda si  x[col] < umbral,  comparando en float32, y el puntaje
# es  sigmoide(margen base + suma de las hojas de los 147 árboles). Así Shiny y el Dash usan el MISMO modelo.
# modelo/xgboost_verificacion.csv trae 300 clientes de prueba con la probabilidad de Python para comprobarlo.
XGB <- tryCatch(local({
  meta <- jsonlite::fromJSON("modelo/xgboost_meta.json", simplifyVector = TRUE)
  con <- gzfile("modelo/xgboost_arboles.bin.gz", "rb"); on.exit(close(con))
  n <- meta$n_nodos
  leer_i <- function() readBin(con, "integer", n, size = 4, endian = "little")
  izq <- leer_i(); der <- leer_i(); col <- leer_i(); defecto_izq <- leer_i()
  umbral <- readBin(con, "double", n, size = 4, endian = "little")   # float32 leído como double (exacto)
  stopifnot(length(umbral) == n)
  list(meta = meta, izq = izq, der = der, col = col, defecto_izq = defecto_izq == 1L, umbral = umbral,
       inicio = c(0L, cumsum(meta$nodos_por_arbol))[seq_along(meta$nodos_por_arbol)])
}), error = function(e) { message("[xgboost] no se pudo cargar: ", conditionMessage(e)); NULL })

# XGBoost convierte las variables a float32 antes de compararlas con los umbrales
.f32 <- function(x) readBin(writeBin(as.double(x), raw(), size = 4), "double", n = length(x), size = 4)

# Valor de hoja de cada árbol (filas = clientes, columnas = árboles)
xgb_hojas <- function(d) {
  B <- XGB; X <- pipeline_matriz(d, B$meta$columnas)
  X[] <- .f32(X)
  n <- nrow(X); nt <- length(B$inicio)
  out <- matrix(0, n, nt)
  for (t in seq_len(nt)) {
    o <- B$inicio[t]; nodo <- rep(o + 1L, n); activos <- seq_len(n)
    repeat {
      nd <- nodo[activos]
      interno <- B$izq[nd] >= 0
      activos <- activos[interno]; nd <- nd[interno]
      if (!length(activos)) break
      x <- X[cbind(activos, B$col[nd] + 1L)]
      a_izq <- ifelse(is.na(x), B$defecto_izq[nd], x < B$umbral[nd])
      nodo[activos] <- o + 1L + ifelse(a_izq, B$izq[nd], B$der[nd])
    }
    out[, t] <- B$umbral[nodo]                       # en las hojas, «umbral» guarda el valor de la hoja
  }
  out
}

xgb_proba <- function(d) {
  m <- XGB$meta$margen_base + rowSums(xgb_hojas(d))
  1 / (1 + exp(-m))
}
