# =============================================================================
# Entrena y SERIALIZA el modelo de la página «Predecir» (versión R / Shiny)
# =============================================================================
# Uso (desde la carpeta shiny/):
#     Rscript modelo/entrenar_modelo.R
#
# Modelo: Random Forest (paquete ranger) con pesos de clase balanceados, la técnica con la
# que ganó en el proyecto Credit_Card_Project. Usa los mismos hiperparámetros que eligió la
# búsqueda del tablero Dash (dash/modelo/modelo_credito.json) y las mismas variables
# transformadas. Usa la MISMA partición del Dash (modelo/particion_dash.csv.gz, que exporta
# herramientas/exportar_cs_fof.py): 80 % para entrenar y 20 % de prueba que no participa en el ajuste. Así sus
# métricas se comparan con las de CS-FOF sobre los mismos 5,993 clientes.
# La prueba se divide en dos mitades, igual que en el Dash:
#   - calibración: elige el umbral recomendado (máximo F1) y calibra la predicción conforme (90 %);
#   - verificación: mide el efecto de cada umbral y la cobertura real del conjunto conforme.
#
# Salidas (en esta carpeta):
#     modelo_credito.rds    bosque entrenado (saveRDS)  -> la app lo carga con readRDS
#     modelo_credito.json   métricas, hiperparámetros, umbral ajustable, predicción conforme y versiones

suppressPackageStartupMessages({ library(ranger); library(jsonlite) })
source("R/00_config.R"); source("R/01_datos.R"); source("R/06_variables.R")

SEMILLA <- 42
HP <- list(num.trees = 291, max.depth = 14, mtry = 4,   # max_features = log2(25 columnas one-hot) -> 4
           min.bucket = 10, min.node.size = 20)          # hojas con ≥ 10 clientes (min_samples_leaf = 10)

P <- utils::read.csv("modelo/particion_dash.csv.gz")
X <- preparar_variables(P[INPUT_COLS])
y <- factor(P[[TARGET]], levels = c(0, 1))
tr <- which(P$conjunto == "entrenamiento")
idx_te <- which(P$conjunto != "entrenamiento")
cal <- which(P$conjunto == "calibracion"); ver <- which(P$conjunto == "verificacion")

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

# ---------- Umbral ajustable y predicción conforme (mitades de calibración y verificación) ----------
p_cal <- predict(modelo, X[cal, ])$predictions[, "1"]; y_cal <- as.integer(as.character(y[cal]))
p_ver <- predict(modelo, X[ver, ])$predictions[, "1"]; y_ver <- as.integer(as.character(y[ver]))
f1_de <- function(yy, pp, u) { pr <- as.integer(pp >= u); tp <- sum(pr == 1 & yy == 1)
  if (tp == 0) return(0); 2 * tp / (2 * tp + sum(pr == 1 & yy == 0) + sum(pr == 0 & yy == 1)) }
metricas <- function(yy, pp, u) {
  pr <- as.integer(pp >= u); tp <- sum(pr == 1 & yy == 1); fp <- sum(pr == 1 & yy == 0); fn <- sum(pr == 0 & yy == 1)
  list(umbral = u, recall = round(if (tp + fn) tp / (tp + fn) else 0, 4), precision = round(if (tp + fp) tp / (tp + fp) else 0, 4),
       f1 = round(f1_de(yy, pp, u), 4), marcados = round(mean(pr), 4), falsas_alarmas_por_100 = round(fp / length(yy) * 100, 2))
}
GRILLA <- round(seq(0.05, 0.95, by = 0.01), 2)
u_rec <- GRILLA[which.max(vapply(GRILLA, function(u) f1_de(y_cal, p_cal, u), 0))]
umbral_ajustable <- list(recomendado = u_rec, criterio = "máximo F1 en la mitad de calibración de la prueba",
                         n_calibracion = length(cal), n_verificacion = length(ver),
                         en_recomendado = metricas(y_ver, p_ver, u_rec), en_0_5 = metricas(y_ver, p_ver, 0.5),
                         curva = lapply(GRILLA, function(u) metricas(y_ver, p_ver, u)))
# Conforme Mondrian (por clase), alfa = 0.10: cuantil «higher» de numpy
ALFA <- 0.10
cuantil <- function(s, a) { s <- sort(s); n <- length(s); k <- min(1, ceiling((n + 1) * (1 - a)) / n)
  s[min(n, ceiling(k * (n - 1)) + 1)] }
q0 <- cuantil(p_cal[y_cal == 0], ALFA); q1 <- cuantil(1 - p_cal[y_cal == 1], ALFA)
incl0 <- p_ver <= q0; incl1 <- 1 - p_ver <= q1
cubre <- ifelse(y_ver == 1, incl1, incl0); tam <- incl0 + incl1
conformal <- list(alfa = ALFA, cobertura_nominal = 1 - ALFA, q0 = round(q0, 6), q1 = round(q1, 6),
                  solo_no_incumple_si_p_menor_que = round(1 - q1, 4), solo_incumple_si_p_mayor_que = round(q0, 4),
                  n_calibracion = length(cal), n_verificacion = length(ver),
                  cobertura_empirica = round(mean(cubre), 4), cobertura_no_incumple = round(mean(cubre[y_ver == 0]), 4),
                  cobertura_incumple = round(mean(cubre[y_ver == 1]), 4), tamano_medio = round(mean(tam), 4),
                  fraccion_un_solo_valor = round(mean(tam == 1), 4), fraccion_vacio = round(mean(tam == 0), 4))

meta <- list(
  modelo = "Random Forest", balanceo = "pesos de clase balanceados (case.weights)",
  busqueda = "hiperparámetros elegidos por RandomizedSearchCV (25 combinaciones, F1, 3 folds) en el tablero Dash",
  hiperparametros = HP, umbral = 0.5, umbral_ajustable = umbral_ajustable, conformal = conformal,
  particion = "la misma del Dash (modelo/particion_dash.csv.gz): 80/20 estratificada, semilla 42",
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
cat(sprintf("Umbral recomendado %.2f · cobertura conforme %.3f\n", u_rec, conformal$cobertura_empirica))
