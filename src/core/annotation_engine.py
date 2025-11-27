# -*- coding: utf-8 -*-
"""
Annotation Engine - Motor de anotaciones para screenshots

Proporciona herramientas de dibujo para anotar capturas de pantalla:
- Flechas
- Rectángulos
- Círculos
- Líneas
- Texto
- Resaltador
- Dibujo libre
"""

import logging
from abc import ABC, abstractmethod
from typing import Optional, List
from enum import Enum

from PyQt6.QtCore import QPoint, QRect, Qt
from PyQt6.QtGui import QPainter, QColor, QPen, QFont, QPolygon

logger = logging.getLogger(__name__)


class AnnotationToolType(Enum):
    """Tipos de herramientas de anotación"""
    ARROW = "arrow"
    RECTANGLE = "rectangle"
    CIRCLE = "circle"
    LINE = "line"
    TEXT = "text"
    HIGHLIGHTER = "highlighter"
    FREEDRAW = "freedraw"


class AnnotationTool(ABC):
    """
    Clase base abstracta para herramientas de anotación

    Todas las herramientas heredan de esta clase y deben implementar
    los métodos abstractos para dibujo y renderizado
    """

    def __init__(self, color: QColor = None, thickness: int = 2):
        """
        Inicializar herramienta de anotación

        Args:
            color: Color de la anotación
            thickness: Grosor del trazo
        """
        self.color = color or QColor(255, 0, 0)  # Rojo por defecto
        self.thickness = thickness
        self.start_point: Optional[QPoint] = None
        self.end_point: Optional[QPoint] = None
        self.is_drawing = False

    @abstractmethod
    def start_drawing(self, point: QPoint) -> None:
        """
        Inicia el dibujo de la anotación

        Args:
            point: Punto inicial
        """
        pass

    @abstractmethod
    def update_drawing(self, point: QPoint) -> None:
        """
        Actualiza el dibujo mientras se arrastra

        Args:
            point: Punto actual del mouse
        """
        pass

    @abstractmethod
    def finish_drawing(self, point: QPoint) -> None:
        """
        Finaliza el dibujo de la anotación

        Args:
            point: Punto final
        """
        pass

    @abstractmethod
    def render(self, painter: QPainter) -> None:
        """
        Renderiza la anotación en el painter

        Args:
            painter: QPainter donde dibujar
        """
        pass

    def set_color(self, color: QColor) -> None:
        """Establece el color de la anotación"""
        self.color = color

    def set_thickness(self, thickness: int) -> None:
        """Establece el grosor del trazo"""
        self.thickness = thickness


class ArrowTool(AnnotationTool):
    """Herramienta para dibujar flechas"""

    def __init__(self, color: QColor = None, thickness: int = 2):
        super().__init__(color, thickness)
        self.arrow_head_size = 10

    def start_drawing(self, point: QPoint) -> None:
        self.start_point = point
        self.end_point = point
        self.is_drawing = True

    def update_drawing(self, point: QPoint) -> None:
        self.end_point = point

    def finish_drawing(self, point: QPoint) -> None:
        self.end_point = point
        self.is_drawing = False

    def render(self, painter: QPainter) -> None:
        if not self.start_point or not self.end_point:
            return

        pen = QPen(self.color, self.thickness)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)

        # Dibujar línea principal
        painter.drawLine(self.start_point, self.end_point)

        # Calcular puntos de la punta de flecha
        dx = self.end_point.x() - self.start_point.x()
        dy = self.end_point.y() - self.start_point.y()

        # Evitar división por cero
        if dx == 0 and dy == 0:
            return

        # Calcular ángulo
        import math
        angle = math.atan2(dy, dx)

        # Puntos de la punta de flecha
        arrow_p1 = QPoint(
            int(self.end_point.x() - self.arrow_head_size * math.cos(angle - math.pi / 6)),
            int(self.end_point.y() - self.arrow_head_size * math.sin(angle - math.pi / 6))
        )
        arrow_p2 = QPoint(
            int(self.end_point.x() - self.arrow_head_size * math.cos(angle + math.pi / 6)),
            int(self.end_point.y() - self.arrow_head_size * math.sin(angle + math.pi / 6))
        )

        # Dibujar punta de flecha
        arrow_polygon = QPolygon([self.end_point, arrow_p1, arrow_p2])
        painter.setBrush(self.color)
        painter.drawPolygon(arrow_polygon)


class RectangleTool(AnnotationTool):
    """Herramienta para dibujar rectángulos"""

    def __init__(self, color: QColor = None, thickness: int = 2, filled: bool = False):
        super().__init__(color, thickness)
        self.filled = filled

    def start_drawing(self, point: QPoint) -> None:
        self.start_point = point
        self.end_point = point
        self.is_drawing = True

    def update_drawing(self, point: QPoint) -> None:
        self.end_point = point

    def finish_drawing(self, point: QPoint) -> None:
        self.end_point = point
        self.is_drawing = False

    def render(self, painter: QPainter) -> None:
        if not self.start_point or not self.end_point:
            return

        pen = QPen(self.color, self.thickness)
        painter.setPen(pen)

        # Crear rectángulo normalizado
        rect = QRect(self.start_point, self.end_point).normalized()

        if self.filled:
            # Rectángulo relleno semi-transparente
            fill_color = QColor(self.color)
            fill_color.setAlpha(100)
            painter.setBrush(fill_color)
            painter.drawRect(rect)
        else:
            # Solo borde
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(rect)


class CircleTool(AnnotationTool):
    """Herramienta para dibujar círculos/elipses"""

    def __init__(self, color: QColor = None, thickness: int = 2, filled: bool = False):
        super().__init__(color, thickness)
        self.filled = filled

    def start_drawing(self, point: QPoint) -> None:
        self.start_point = point
        self.end_point = point
        self.is_drawing = True

    def update_drawing(self, point: QPoint) -> None:
        self.end_point = point

    def finish_drawing(self, point: QPoint) -> None:
        self.end_point = point
        self.is_drawing = False

    def render(self, painter: QPainter) -> None:
        if not self.start_point or not self.end_point:
            return

        pen = QPen(self.color, self.thickness)
        painter.setPen(pen)

        # Crear rectángulo que define la elipse
        rect = QRect(self.start_point, self.end_point).normalized()

        if self.filled:
            # Círculo relleno semi-transparente
            fill_color = QColor(self.color)
            fill_color.setAlpha(100)
            painter.setBrush(fill_color)
            painter.drawEllipse(rect)
        else:
            # Solo borde
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(rect)


class LineTool(AnnotationTool):
    """Herramienta para dibujar líneas rectas"""

    def start_drawing(self, point: QPoint) -> None:
        self.start_point = point
        self.end_point = point
        self.is_drawing = True

    def update_drawing(self, point: QPoint) -> None:
        self.end_point = point

    def finish_drawing(self, point: QPoint) -> None:
        self.end_point = point
        self.is_drawing = False

    def render(self, painter: QPainter) -> None:
        if not self.start_point or not self.end_point:
            return

        pen = QPen(self.color, self.thickness)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.drawLine(self.start_point, self.end_point)


class TextTool(AnnotationTool):
    """Herramienta para agregar texto"""

    def __init__(self, color: QColor = None, thickness: int = 2, text: str = ""):
        super().__init__(color, thickness)
        self.text = text
        self.font_size = 16

    def start_drawing(self, point: QPoint) -> None:
        self.start_point = point
        self.is_drawing = True

    def update_drawing(self, point: QPoint) -> None:
        pass  # El texto no cambia al arrastrar

    def finish_drawing(self, point: QPoint) -> None:
        self.is_drawing = False

    def set_text(self, text: str) -> None:
        """Establece el texto a mostrar"""
        self.text = text

    def set_font_size(self, size: int) -> None:
        """Establece el tamaño de fuente"""
        self.font_size = size

    def render(self, painter: QPainter) -> None:
        if not self.start_point or not self.text:
            return

        font = QFont("Arial", self.font_size, QFont.Weight.Bold)
        painter.setFont(font)
        painter.setPen(self.color)

        # Dibujar texto
        painter.drawText(self.start_point, self.text)


class HighlighterTool(AnnotationTool):
    """Herramienta de resaltador (rectángulo semi-transparente amarillo)"""

    def __init__(self, color: QColor = None, thickness: int = 2):
        # Color amarillo semi-transparente por defecto
        default_color = QColor(255, 255, 0, 80)
        super().__init__(color or default_color, thickness)

    def start_drawing(self, point: QPoint) -> None:
        self.start_point = point
        self.end_point = point
        self.is_drawing = True

    def update_drawing(self, point: QPoint) -> None:
        self.end_point = point

    def finish_drawing(self, point: QPoint) -> None:
        self.end_point = point
        self.is_drawing = False

    def render(self, painter: QPainter) -> None:
        if not self.start_point or not self.end_point:
            return

        # Rectángulo relleno sin borde
        rect = QRect(self.start_point, self.end_point).normalized()
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(self.color)
        painter.drawRect(rect)


class FreeDrawTool(AnnotationTool):
    """Herramienta de dibujo libre (path)"""

    def __init__(self, color: QColor = None, thickness: int = 2):
        super().__init__(color, thickness)
        self.points: List[QPoint] = []

    def start_drawing(self, point: QPoint) -> None:
        self.points = [point]
        self.is_drawing = True

    def update_drawing(self, point: QPoint) -> None:
        self.points.append(point)

    def finish_drawing(self, point: QPoint) -> None:
        self.points.append(point)
        self.is_drawing = False

    def render(self, painter: QPainter) -> None:
        if len(self.points) < 2:
            return

        pen = QPen(self.color, self.thickness)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)

        # Dibujar líneas entre puntos consecutivos
        for i in range(len(self.points) - 1):
            painter.drawLine(self.points[i], self.points[i + 1])


class AnnotationManager:
    """
    Gestor de anotaciones

    Maneja la lista de anotaciones aplicadas y proporciona
    operaciones como agregar, deshacer, limpiar y renderizar
    """

    def __init__(self):
        """Inicializar gestor de anotaciones"""
        self.annotations: List[AnnotationTool] = []
        self.current_tool: Optional[AnnotationTool] = None

    def add_annotation(self, tool: AnnotationTool) -> None:
        """
        Agrega una anotación a la lista

        Args:
            tool: Herramienta de anotación completada
        """
        self.annotations.append(tool)
        logger.debug(f"Annotation added: {type(tool).__name__}")

    def undo(self) -> bool:
        """
        Deshace la última anotación

        Returns:
            bool: True si se deshizo una anotación
        """
        if self.annotations:
            removed = self.annotations.pop()
            logger.debug(f"Annotation undone: {type(removed).__name__}")
            return True
        return False

    def clear_all(self) -> None:
        """Limpia todas las anotaciones"""
        count = len(self.annotations)
        self.annotations.clear()
        logger.debug(f"All annotations cleared: {count} removed")

    def render_all(self, painter: QPainter) -> None:
        """
        Renderiza todas las anotaciones

        Args:
            painter: QPainter donde dibujar
        """
        for annotation in self.annotations:
            annotation.render(painter)

        # Renderizar también la herramienta actual si está en uso
        if self.current_tool and self.current_tool.is_drawing:
            self.current_tool.render(painter)

    def set_current_tool(self, tool: AnnotationTool) -> None:
        """
        Establece la herramienta actual

        Args:
            tool: Herramienta activa
        """
        self.current_tool = tool

    def get_annotation_count(self) -> int:
        """
        Obtiene el número de anotaciones aplicadas

        Returns:
            int: Cantidad de anotaciones
        """
        return len(self.annotations)

    def has_annotations(self) -> bool:
        """
        Verifica si hay anotaciones aplicadas

        Returns:
            bool: True si hay al menos una anotación
        """
        return len(self.annotations) > 0
