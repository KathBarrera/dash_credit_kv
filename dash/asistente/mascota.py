# -*- coding: utf-8 -*-
"""Kyo, la mascota del asistente: una estrella dorada de 5 puntas con ojos grandes, brazos y piernas.

`mascota_svg` devuelve el SVG como texto (para incrustarlo en la página y animarlo con CSS)
y `mascota_uri` lo devuelve como data URI (para usarlo en <img> dentro del chat).
Cada parte tiene una clase (a-leg-l, a-arm-r, a-eyes...) para poder animarla.
"""
import math
from urllib.parse import quote

# Dorados de la paleta del tablero (los mismos del chip de las tarjetas)
# Versión más luminosa: crema brillante -> oro vivo -> dorado cálido (siguen la paleta, con más brillo)
BODY_TOP, BODY_MID, BODY_BOT = "#FFF1C4", "#F4CC63", "#D49A2E"
LIMB = "#A57A2C"                            # brazos y piernas: dorado tostado (más vivo que BROWN)
INK = "#1A233D"                             # pupilas y boca: azul profundo del tablero
SPARK = "#E8B23F"                           # destello: oro vivo (se ve en claro y oscuro)


def _star(cx=50.0, cy=48.0, r_out=36.0, r_in=19.0, n=5, rot=-90.0):
    pts = []
    for i in range(2 * n):
        a = math.radians(rot + i * 180.0 / n)
        r = r_out if i % 2 == 0 else r_in
        pts.append(f"{cx + r * math.cos(a):.1f} {cy + r * math.sin(a):.1f}")
    return "M" + " L".join(pts) + " Z"


STAR_PATH = _star()

# Brazos según el ánimo: (izquierdo, derecho)
_ARMS = {
    "happy": ("M31 60 L21 76", "M69 60 L79 76"),
    "thinking": ("M31 60 L21 76", "M69 60 Q76 66 64 66"),
    "explaining": ("M31 60 L21 76", "M69 58 L88 40"),
    "proud": ("M31 58 L15 44", "M69 58 L85 44"),
    "alert": ("M31 58 L17 50", "M69 58 L83 50"),
}


def _eyes(mood):
    if mood == "proud":   # ojos felices ^ ^
        return ('<g class="a-eyes" fill="none" stroke="%s" stroke-width="2.6" stroke-linecap="round">'
                '<path d="M35 46 Q40 40 45 46"/><path d="M53 45 Q58 39 63 45"/></g>' % INK)
    dx, dy = {"thinking": (-1.4, -2.4), "alert": (0, 0), "explaining": (2.0, -1.0)}.get(mood, (1.8, -1.6))
    r = 4.6 if mood == "alert" else 3.7
    return ('<g class="a-eyes">'
            '<ellipse cx="40" cy="45" rx="6.2" ry="7" fill="#F4F1FF"/>'
            '<ellipse cx="58" cy="44" rx="6.2" ry="7" fill="#F4F1FF"/>'
            f'<circle cx="{40 + dx:.1f}" cy="{45 + dy:.1f}" r="{r}" fill="{INK}"/>'
            f'<circle cx="{58 + dx:.1f}" cy="{44 + dy:.1f}" r="{r}" fill="{INK}"/>'
            f'<circle cx="{41.2 + dx:.1f}" cy="{43.6 + dy:.1f}" r="1.2" fill="#FFFFFF"/>'
            f'<circle cx="{59.2 + dx:.1f}" cy="{42.6 + dy:.1f}" r="1.2" fill="#FFFFFF"/></g>')


def _mouth(mood):
    if mood == "alert":
        return f'<ellipse class="a-mouth" cx="49" cy="56.5" rx="2.6" ry="3.2" fill="{INK}"/>'
    if mood == "thinking":
        return f'<path class="a-mouth" d="M46 56.5 L52 55.5" stroke="{INK}" stroke-width="2" stroke-linecap="round"/>'
    if mood in ("proud", "explaining"):
        return f'<path class="a-mouth" d="M44.5 54 Q49 60.5 53.5 54 Z" fill="{INK}"/>'
    return (f'<path class="a-mouth" d="M45.5 54.5 Q49 58.5 52.5 54.5" fill="none" stroke="{INK}" '
            'stroke-width="2" stroke-linecap="round"/>')


def mascota_svg(mood="happy", cls="", uid="a"):
    """SVG de Kyo. mood: happy · thinking · explaining · proud · alert."""
    mood = mood if mood in _ARMS else "happy"
    arm_l, arm_r = _ARMS[mood]
    g = f"kyo-g-{uid}"
    spark = ""
    if mood in ("happy", "proud"):
        spark = (f'<path class="a-spark" d="M87 8 Q87 15 94 15 Q87 15 87 22 Q87 15 80 15 Q87 15 87 8 Z" '
                 f'fill="{SPARK}"/>')
    if mood == "thinking":
        spark = (f'<g class="a-spark" fill="{SPARK}"><circle cx="78" cy="16" r="2"/><circle cx="85" cy="11" r="2.6"/>'
                 '<circle cx="93" cy="6" r="3.2"/></g>')
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 120" class="{cls}" aria-hidden="true">'
        f'<defs><linearGradient id="{g}" x1="0" y1="0" x2="0.35" y2="1">'
        f'<stop offset="0" stop-color="{BODY_TOP}"/><stop offset=".45" stop-color="{BODY_MID}"/>'
        f'<stop offset="1" stop-color="{BODY_BOT}"/></linearGradient></defs>'
        '<ellipse class="a-shadow" cx="50" cy="114" rx="20" ry="3.4" fill="#000" opacity=".16"/>'
        f'<g stroke="{LIMB}" stroke-width="4.4" stroke-linecap="round" stroke-linejoin="round" fill="none">'
        '<path class="a-leg a-leg-l" d="M44 70 L43 106 L36 108"/>'
        '<path class="a-leg a-leg-r" d="M56 70 L57 106 L64 108"/>'
        f'<path class="a-arm a-arm-l" d="{arm_l}"/>'
        f'<path class="a-arm a-arm-r" d="{arm_r}"/></g>'
        f'<g class="a-body"><path d="{STAR_PATH}" fill="url(#{g})" stroke="url(#{g})" stroke-width="7" '
        'stroke-linejoin="round"/>'
        # brillo especular arriba a la izquierda: le da volumen y luz
        '<path d="M44 20 Q47 14 50 13 Q49 19 46 25 Z" fill="#FFFFFF" opacity=".55"/>'
        '<ellipse cx="30" cy="36" rx="5" ry="2.2" transform="rotate(-18 30 36)" fill="#FFFFFF" opacity=".35"/>'
        '<ellipse cx="32" cy="52" rx="3.6" ry="2.2" fill="#F2A7C9" opacity=".55"/>'
        '<ellipse cx="66" cy="51" rx="3.6" ry="2.2" fill="#F2A7C9" opacity=".55"/>'
        f'{_eyes(mood)}{_mouth(mood)}</g>{spark}</svg>')


def mascota_uri(mood="happy"):
    return "data:image/svg+xml;utf8," + quote(mascota_svg(mood, uid=mood))
