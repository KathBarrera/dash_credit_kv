# -*- coding: utf-8 -*-
"""Página Enlaces."""

from dash import html

from tablero.componentes import _ul, card, page_title
from tablero.config import tx
from tablero.paginas.conclusiones import book_summary, pipeline_card
from tablero.paginas.inicio import link_cards, video_card


def page_links():
    return html.Div([
        page_title(tx("Enlaces", "Links"), ""),
        video_card(),
        book_summary(),
        link_cards(),
        pipeline_card(),
        card(tx("Reproducir el análisis", "Reproduce the analysis"), _ul([
            [tx("Clona el repositorio del proyecto e instala las dependencias con ",
                "Clone the project repository and install the dependencies with "),
             html.Code("pip install -r requirements.txt"),
             tx(" (la guía del repositorio usa un entorno Conda con Python 3.12).",
                " (the repository guide uses a Conda environment with Python 3.12).")],
            [tx("Abre el notebook del EDA desde la carpeta ", "Open the EDA notebook from the "), html.Code("notebooks/"),
             tx(" y ejecútalo en VS Code.", " folder and run it in VS Code.")],
            [tx("Para correr este tablero: ", "To run this dashboard: "), html.Code("python app.py"),
             tx(" y abre ", " and open "), html.Code("http://127.0.0.1:8050"), "."],
        ], ordered=True)),
    ])
