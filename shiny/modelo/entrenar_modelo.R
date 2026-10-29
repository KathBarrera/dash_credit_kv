# =============================================================================
# Entrena y SERIALIZA el modelo de la página «Predecir» (versión R / Shiny)
# =============================================================================
# Uso (desde la carpeta shiny/):
#     Rscript modelo/entrenar_modelo.R
#
# Modelo: Random Forest (paquete ranger) con pesos de clase balanceados, la técnica con la
# que ganó en el proyecto Credit_Card_Project. Usa los mismos hiperparámetros que eligió la
# búsqueda del tablero Dash (dash/modelo/modelo_credito.json) y las mismas variables
# transformadas. Se evalúa en un 20 % de prueba estratificado que no participa en el ajuste.
#
# Salidas (en esta carpeta):
#     modelo_credito.rds    bosque entrenado (saveRDS)  -> la app lo carga con readRDS
#     modelo_credito.json   métricas, hiperparámetros y versiones

suppressPackageStartupMessages({ library(ranger); library(jsonlite) })
source("R/00_config.R"); source("R/01_datos.R"); source("R/06_variables.R")

SEMILLA <- 42
HP <- list(num.trees = 291, max.depth = 14, mtry = 4,   # max_features = log2(25 columnas one-hot) -> 4
           min.bucket = 10, min.node.size = 20)          # hojas con ≥ 10 clientes (min_samples_leaf = 10)

X <- preparar_variables(df[INPUT_COLS])
y <- factor(df[[TARGET]], levels = c(0, 1))

# Partición estratificada 80 / 20
set.seed(SEMILLA)
idx_te <- unlist(lapply(split(seq_along(y), y), function(i) sample(i, round(length(i) * 0.2))))
tr <- setdiff(seq_along(y), idx_te)

# Pesos de clase balanceados (= class_weight="balanced"): n / (2 · n_clase)
w_clase <- length(tr) / (2 * table(y[tr]))
pesos <- as.numeric(w_clase[as.character(y[tr])])

t0 <- Sys.time()
modelo <- ranger(x = X[tr, ], y = y[tr], probability = TRUE, case.weights = pesos,
                 num.trees = HP$num.trees, max.depth = HP$max.depth, mtry = HP$mtry,
                 min.bucket = HP$min.bucket, min.node.size = HP$min.node.size,
                 importance = "impurity", seed = SEMILLA, num.threads = 2)
seg <- as.numeric(difftime(Sys.time(), t0, units = "secs"))

# Evaluación en prueba (umbral 0.5)
proba <- predict(modelo, X[idx_te, ])$predictions[, "1"]
real <- as.integer(as.character(y[idx_te]))
pred <- as.integer(proba >= 0.5)
tp <- sum(pred == 1 & real == 1); fp <- sum(pred == 1 & real == 0)
fn <- sum(pred == 0 & real == 1); tn <- sum(pred == 0 & real == 0)
prec <- tp / (tp + fp); rec <- tp / (tp + fn); f1 <- 2 * prec * rec / (prec + rec)
auc <- function(s, r) {           # ROC-AUC por rangos (Mann-Whitney)
  rk <- rank(s); n1 <- sum(r == 1); n0 <- sum(r == 0)
  (sum(rk[r == 1]) - n1 * (n1 + 1) / 2) / (n1 * n0)
}
ap <- function(s, r) {            # PR-AUC (average precision)
  o <- order(s, decreasing = TRUE); r <- r[o]
  sum(cumsum(r)[r == 1] / which(r == 1)) / sum(r)
}

saveRDS(modelo, "modelo/modelo_credito.rds", compress = "xz")

meta <- list(
  modelo = "Random Forest", balanceo = "pesos de clase balanceados (case.weights)",
  busqueda = "hiperparámetros elegidos por RandomizedSearchCV (25 combinaciones, F1, 3 folds) en el tablero Dash",
  hiperparametros = HP, umbral = 0.5,
  prueba = list(n = length(idx_te), f1 = round(f1, 4), precision = round(prec, 4), recall = round(rec, 4),
                roc_auc = round(auc(proba, real), 4), pr_auc = round(ap(proba, real), 4),
                matriz_confusion = list(tn = tn, fp = fp, fn = fn, tp = tp)),
  n_entrenamiento = length(tr), tasa_default_entrenamiento = round(mean(y[tr] == 1), 4),
  entradas = INPUT_COLS,
  versiones = list(R = paste(R.version$major, R.version$minor, sep = "."),
                   ranger = as.character(packageVersion("ranger"))),
  fecha = as.character(Sys.Date()), segundos_entrenamiento = round(seg, 1))
write_json(meta, "modelo/modelo_credito.json", auto_unbox = TRUE, pretty = TRUE)
cat(sprintf("Listo: F1 %.3f · recall %.3f · precisión %.3f · ROC-AUC %.3f · %.1f s · %.1f MB\n",
            f1, rec, prec, auc(proba, real), seg, file.size("modelo/modelo_credito.rds") / 1e6))
