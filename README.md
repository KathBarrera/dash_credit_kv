# Riesgo de Incumplimiento en Tarjetas de Crédito

**Dashboard interactivo de análisis exploratorio (EDA) del dataset Default of Credit Card Clients**



## Ver Dashboard en Vivo

[![Ver Dashboard](https://dash-credit-kv.onrender.com/)



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
- Modo claro y oscuro, y menú lateral plegable
- *(Próximamente)* Modelo predictivo de incumplimiento integrado al tablero

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
    ├── requirements.txt                     # Dependencias del proyecto
    └── default_of_credit_card_clients.xls   # Dataset
```

La aplicación tiene cinco secciones: Introducción, Problema y Objetivos, Marco Teórico, EDA Univariado y EDA Multivariado.

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

## Equipo

Este proyecto fue desarrollado por:

- **Katherin Barrera** —  [GitHub](https://github.com/KathBarrera)
- **Valeria Flórez** —[GitHub](https://github.com/valeriaflorezs)
