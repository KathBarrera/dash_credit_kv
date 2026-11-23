# -*- coding: utf-8 -*-
"""
===============================================================================
 DASHBOARD EDA — DEFAULT OF CREDIT CARD CLIENTS (UCI, Taiwán 2005)
 Python · Dash · Plotly
===============================================================================
 Ejecución local (Visual Studio Code):
     1) pip install -r requirements.txt
     2) Deja este archivo junto a `default_of_credit_card_clients.xls`
        (o dentro de una carpeta `data/`). Si no lo encuentra, lo descarga
        automáticamente desde el repositorio UCI.
     3) python app.py   ->   http://127.0.0.1:8050

 Este archivo solo arma la aplicación; el código vive en el paquete tablero/:

     tablero/config.py         Configuración: AUTORES, EQUIPO, ENLACES, rutas, paleta e idioma  <- editar aquí
     tablero/datos.py          Carga y limpieza de datos (igual que el notebook 00_eda.ipynb) y filtro del EDA
     tablero/utilidades.py     Formato, estadísticos y estilo de las figuras
     tablero/eda_uni.py        Figuras e interpretaciones del EDA univariado
     tablero/eda_multi.py      Figuras e interpretaciones del EDA multivariado
     tablero/resultados.py     Resultados de los modelos (results/*.csv del proyecto)
     tablero/prediccion.py     Modelos serializados (modelo/*.pkl) y lo que usa la página Predecir
     tablero/iconos.py         Íconos SVG
     tablero/componentes.py    Tarjetas, KPIs, interpretaciones y controles compartidos
     tablero/paginas/          Una página (o grupo de páginas) por archivo
     tablero/servidor.py       La aplicación Dash y las rutas /ping y /health
     tablero/estilos.py        CSS y JavaScript
     tablero/tema.py           Tema claro / oscuro de las figuras y el decorador graph_cb
     tablero/kyo.py            Entrenamiento y panel del asistente Kyo (su lógica está en asistente/)
     tablero/layout.py         Barra lateral, barra superior y layout final
     tablero/callbacks/        Callbacks por sección (navegación, EDA, modelos, Predecir, Kyo)
===============================================================================
"""
from tablero.servidor import app, server  # noqa: F401  (gunicorn usa app:server)
from tablero import layout  # noqa: F401,E402  (define app.layout)
from tablero.callbacks import eda, kyo, modelos, navegacion, predecir  # noqa: F401,E402  (registran los callbacks)

if __name__ == "__main__":
    app.run(debug=True, port=8050)
