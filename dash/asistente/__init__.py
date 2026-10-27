"""Astra: asistente del tablero (bot entrenado con el contenido del dash)."""
from .motor import Asistente, Intencion, normalizar
from .mascota import mascota_svg, mascota_uri
from .conocimiento import construir_conocimiento

__all__ = ["Asistente", "Intencion", "normalizar", "mascota_svg", "mascota_uri", "construir_conocimiento"]
