# Riesgo de Incumplimiento en Tarjetas de Crédito

**Dashboard interactivo de análisis exploratorio (EDA) del dataset Default of Credit Card Clients**



## Ver Dashboard en Vivo

[Ver Dashboard](https://dashcreditkv-production.up.railway.app/)



---

## Descripción del Proyecto

Las tarjetas de crédito son una de las líneas de la banca minorista con mayor exposición al riesgo: cada cliente recibe un cupo y se espera que lo pague en las fechas pactadas. Cuando no lo hace, la entidad enfrenta pérdidas, mayores costos de cobranza y la necesidad de provisionar capital. Entender qué perfiles y comportamientos anticipan el incumplimiento permite fijar límites, priorizar la cobranza y alimentar modelos de scoring.

Este proyecto presenta un tablero desarrollado con **Dash y Plotly** sobre el conjunto de datos *Default of Credit Card Clients* (UCI), con información de clientes de un banco de Taiwán entre abril y septiembre de 2005: límite de crédito, características demográficas, historial de pagos de seis meses, montos facturados, montos pagados y si el cliente incumplió el pago del mes siguiente. Cada gráfico incluye una interpretación básica (lenguaje cotidiano) y una técnica (estadísticos y recomendaciones de modelado).

El análisis incluye:
- Análisis Exploratorio de Datos (EDA) univariado y multivariado, con módulos interactivos de cruce de variables y matriz de dispersión
- Matriz de correlación de Spearman, robusta a valores extremos y adecuada para variables ordinales y binarias
- Pruebas estadísticas: χ² con V de Cramér, Mann-Whitney, t de Welch y Kruskal-Wallis
- Diagnóstico de multicolinealidad entre las variables de facturación (BILL_AMT)
- Análisis del desbalance de clases de la variable objetivo
- Sección **Predecir**: formulario visual (deslizadores y tarjetas con íconos) que devuelve en vivo el puntaje de riesgo de un cliente usando un Random Forest **serializado con `joblib`** (`dash/modelo/modelo_credito.pkl`), con indicador, votos de los árboles, historial del cliente, aporte de cada grupo de variables y simulador «¿Qué pasaría si…?»
- Modo claro y oscuro, y menú lateral plegable
- Sección **Modelos**: carrusel deslizable con los siete clasificadores del proyecto (mejor combinación de cada uno), el mejor modelo resaltado, F1 por técnica de balanceo, F1 frente a ROC-AUC de las 112 combinaciones, matriz de confusión del mejor modelo y resumen de SHAP

---

## Dataset

El dataset utilizado es [Default of Credit Card Clients](https://archive.ics.uci.edu/dataset/350/default+of+credit+card+clients) (UCI Machine Learning Repository), de Yeh & Lien (2009). Contiene 30 000 clientes y 24 variables (23 predictoras y una variable objetivo).

> **Nota:** El archivo `default_of_credit_card_clients.xls` está incluido en la carpeta `dash/`. Si la aplicación no lo encuentra, intenta descargarlo automáticamente desde UCI; si esa descarga falla, descárguelo manualmente desde la fuente y colóquelo junto a `app.py`.

---

## Estructura del Proyecto

```
dash_credit_kv/
├── README.md                                # Este archivo
├── .gitignore
├── assets/
│   └── imagen_presentacion.jpeg             # Captura del dashboard
└── dash/
    ├── app.py                               # Aplicación completa (datos, figuras, páginas y callbacks)
    ├── results/
    │   └── model_results.csv                # 112 combinaciones de modelos (del repositorio Credit_Card_Project)
    └── modelo/
        ├── features.py                      # Transformaciones de variables del proyecto (las usa el .pkl)
        ├── entrenar.py                      # Entrena y serializa el modelo (python -m modelo.entrenar)
        ├── modelo_credito.pkl               # Modelo serializado con joblib
        └── modelo_credito.json              # Métricas, hiperparámetros y versiones
    ├── requirements.txt                     # Dependencias del proyecto
    └── default_of_credit_card_clients.xls   # Dataset
```

La aplicación tiene estas secciones: Introducción, Problema y Objetivos, Marco Teórico, EDA Univariado, EDA Multivariado, Modelos, Predecir, Enlaces y Equipo.

### Modelo serializado (sección Predecir)

El modelo se entrena una sola vez y se guarda en disco con `joblib`; el tablero solo lo carga y predice:

```bash
cd dash
python -m modelo.entrenar        # entrena, guarda modelo/modelo_credito.pkl y verifica que cargue
```

```python
import joblib
joblib.dump(modelo, "modelo/modelo_credito.pkl", compress=3)   # serializar
modelo = joblib.load("modelo/modelo_credito.pkl")              # cargar en app.py
riesgo = modelo.predict_proba(cliente)[0, 1]                   # predecir
```

El `.pkl` guarda el pipeline completo (transformaciones del proyecto + one-hot + Random Forest con `class_weight="balanced"`), así que recibe las 23 variables originales del dataset. Debe cargarse con la misma versión de scikit-learn con la que se guardó (fijada en `requirements.txt`).

`results/model_results.csv` resume los resultados de [Credit_Card_Project](https://github.com/valeriaflorezs/Credit_Card_Project) (`results/experiments_posthoc_metrics.csv` para los 96 experimentos locales y `results/svm_gpu_results_colab.csv` para SVM): F1, precisión, recall, ROC-AUC y PR-AUC medios de cada combinación modelo × técnica de balanceo × método de optimización.

---

## Cómo ejecutar la aplicación

**1. Clonar el repositorio**

```bash
git clone https://github.com/KathBarrera/dash_credit_kv.git
cd dash_credit_kv
```

**2. (Opcional) Crear un entorno virtual**

```bash
conda create -n mi_env python=3.11
conda activate mi_env
```

**3. Instalar las dependencias**

```bash
cd dash
pip install -r requirements.txt
```

**4. Verificar el dataset**

Confirma que `default_of_credit_card_clients.xls` esté en la carpeta `dash/`. Si no está, descárgalo desde [UCI](https://archive.ics.uci.edu/dataset/350/default+of+credit+card+clients) y colócalo ahí.

**5. Ejecutar la aplicación**

```bash
python app.py
```

**6. Abrir en el navegador**

```
http://localhost:8050/
```

---

## Despliegue en Railway

El repositorio ya trae la configuración (`railway.json`, `requirements.txt` y `.python-version` en la raíz):

1. En [railway.com](https://railway.com) crea un proyecto con **New Project → Deploy from GitHub repo** y elige `KathBarrera/dash_credit_kv` (rama `main`).
2. No hace falta cambiar el *Root Directory*: Railway instala `dash/requirements.txt` y arranca con
   `gunicorn --chdir dash app:server --bind 0.0.0.0:$PORT --workers 2 --preload --timeout 120`.
3. En **Settings → Networking** pulsa **Generate Domain** para obtener la URL pública.

Si el dataset no está en `dash/`, la aplicación lo descarga de UCI al arrancar (una sola vez gracias a `--preload`).

Durante el build, si `dash/modelo/modelo_credito.pkl` no está en el repositorio, Railway lo entrena y lo serializa con `python -m modelo.entrenar 12` (descarga los datos de UCI). Para fijar un modelo concreto, entrénalo localmente y sube el `.pkl` y el `.json`.

---

## Equipo

Este proyecto fue desarrollado por:

- **Katherin Barrera** —  [GitHub](https://github.com/KathBarrera)
- **Valeria Flórez** —[GitHub](https://github.com/valeriaflorezs)
