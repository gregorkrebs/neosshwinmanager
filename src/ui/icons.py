"""
icons.py – Zentrale SVG-Icon-Loader (lucide-Stil).

Ermöglicht einheitliche, theme-farbige Icons für QPushButton/QLabel.
SVGs liegen in assets/icons/ und verwenden stroke="currentColor";
diese Funktion ersetzt das beim Laden durch die gewünschte Farbe.
"""

from __future__ import annotations

import os
import sys
from functools import lru_cache

from PyQt6.QtCore import QByteArray, QSize, Qt
from PyQt6.QtGui import QIcon, QPixmap, QPainter
from PyQt6.QtSvg import QSvgRenderer


def _icons_root() -> str:
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, "assets", "icons")
    return os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "assets", "icons"
    )


@lru_cache(maxsize=256)
def _svg_bytes(name: str, color: str) -> bytes:
    path = os.path.join(_icons_root(), f"{name}.svg")
    with open(path, "r", encoding="utf-8") as f:
        svg = f.read()
    # currentColor → konkrete Farbe
    svg = svg.replace("currentColor", color)
    return svg.encode("utf-8")


def icon(name: str, color: str = "#aab4c4", size: int = 18) -> QIcon:
    """SVG-Icon als QIcon in gewünschter Farbe/Größe."""
    data = _svg_bytes(name, color)
    renderer = QSvgRenderer(QByteArray(data))
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pm)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
    renderer.render(painter)
    painter.end()
    return QIcon(pm)


def pixmap(name: str, color: str = "#aab4c4", size: int = 18) -> QPixmap:
    """SVG als QPixmap (für QLabel)."""
    data = _svg_bytes(name, color)
    renderer = QSvgRenderer(QByteArray(data))
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pm)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
    renderer.render(painter)
    painter.end()
    return pm
