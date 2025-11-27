# -*- coding: utf-8 -*-
"""
Screenshot Overlay - Overlay de selección de área para capturas

Ventana fullscreen semi-transparente que permite al usuario:
- Seleccionar un área rectangular mediante drag & drop
- Visualizar el área seleccionada en tiempo real
- Ver las dimensiones del área
- Cancelar la operación con Esc o click derecho
"""

import logging
from typing import Optional
from PyQt6.QtWidgets import QWidget, QApplication, QLabel
from PyQt6.QtCore import Qt, QRect, QPoint, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QPen, QFont, QCursor, QPalette

logger = logging.getLogger(__name__)


class ScreenshotOverlay(QWidget):
    """
    Overlay fullscreen para selección de área de captura

    Señales:
        area_selected(QRect): Emitida cuando se completa la selección
        capture_cancelled(): Emitida cuando se cancela la operación
    """

    # Señales
    area_selected = pyqtSignal(QRect)
    capture_cancelled = pyqtSignal()

    def __init__(self, parent=None):
        """
        Inicializar overlay de screenshot

        Args:
            parent: Widget padre (opcional)
        """
        super().__init__(parent)

        # Estado de selección
        self.selection_start: Optional[QPoint] = None
        self.selection_end: Optional[QPoint] = None
        self.is_selecting = False

        # Configuración visual
        self.overlay_color = QColor(0, 0, 0, 100)  # Negro semi-transparente
        self.selection_border_color = QColor(0, 122, 204)  # Azul accent
        self.selection_border_width = 2
        self.handle_size = 8  # Tamaño de cuadrados en esquinas

        self.init_ui()

    def init_ui(self):
        """Inicializar interfaz de usuario"""
        # Ventana fullscreen sin bordes, always on top
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )

        # Fondo semi-transparente
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Cursor de cruz
        self.setCursor(QCursor(Qt.CursorShape.CrossCursor))

        # Capturar todos los eventos de mouse y teclado
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        # Hacer la ventana fullscreen
        screen = QApplication.primaryScreen()
        screen_geometry = screen.geometry()
        self.setGeometry(screen_geometry)

        logger.info("Screenshot overlay initialized")

    def showEvent(self, event):
        """Override showEvent para asegurar fullscreen"""
        super().showEvent(event)
        self.showFullScreen()
        self.activateWindow()
        self.raise_()
        self.setFocus()

    def paintEvent(self, event):
        """
        Dibuja el overlay y el área de selección

        Args:
            event: QPaintEvent
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Dibujar overlay semi-transparente sobre toda la pantalla
        painter.fillRect(self.rect(), self.overlay_color)

        # Si hay selección activa, dibujar
        if self.selection_start and self.selection_end:
            selection_rect = self._get_selection_rect()

            # Limpiar área seleccionada (hacerla transparente)
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
            painter.fillRect(selection_rect, Qt.GlobalColor.transparent)

            # Restaurar modo de composición normal
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)

            # Dibujar borde del rectángulo de selección
            pen = QPen(self.selection_border_color, self.selection_border_width)
            painter.setPen(pen)
            painter.drawRect(selection_rect)

            # Dibujar esquinas (cuadrados pequeños)
            self._draw_handles(painter, selection_rect)

            # Dibujar dimensiones
            self._draw_dimensions(painter, selection_rect)

    def _draw_handles(self, painter: QPainter, rect: QRect):
        """
        Dibuja cuadrados en las esquinas del rectángulo de selección

        Args:
            painter: QPainter
            rect: Rectángulo de selección
        """
        handle_color = self.selection_border_color
        painter.fillRect(
            rect.left() - self.handle_size // 2,
            rect.top() - self.handle_size // 2,
            self.handle_size,
            self.handle_size,
            handle_color
        )
        painter.fillRect(
            rect.right() - self.handle_size // 2,
            rect.top() - self.handle_size // 2,
            self.handle_size,
            self.handle_size,
            handle_color
        )
        painter.fillRect(
            rect.left() - self.handle_size // 2,
            rect.bottom() - self.handle_size // 2,
            self.handle_size,
            self.handle_size,
            handle_color
        )
        painter.fillRect(
            rect.right() - self.handle_size // 2,
            rect.bottom() - self.handle_size // 2,
            self.handle_size,
            self.handle_size,
            handle_color
        )

    def _draw_dimensions(self, painter: QPainter, rect: QRect):
        """
        Dibuja las dimensiones del área seleccionada

        Args:
            painter: QPainter
            rect: Rectángulo de selección
        """
        width = rect.width()
        height = rect.height()

        # Texto de dimensiones
        dimensions_text = f"{width} x {height}"

        # Configurar fuente
        font = QFont("Segoe UI", 12, QFont.Weight.Bold)
        painter.setFont(font)

        # Calcular tamaño del texto
        fm = painter.fontMetrics()
        text_width = fm.horizontalAdvance(dimensions_text)
        text_height = fm.height()

        # Posición del texto (arriba del rectángulo, centrado)
        text_x = rect.left() + (rect.width() - text_width) // 2
        text_y = rect.top() - 10

        # Si el texto quedaría fuera de la pantalla arriba, ponerlo abajo
        if text_y < text_height:
            text_y = rect.bottom() + text_height + 5

        # Fondo para el texto
        padding = 4
        text_bg_rect = QRect(
            text_x - padding,
            text_y - text_height,
            text_width + padding * 2,
            text_height + padding
        )

        painter.fillRect(text_bg_rect, QColor(0, 0, 0, 180))

        # Dibujar texto
        painter.setPen(QColor(255, 255, 255))
        painter.drawText(text_x, text_y, dimensions_text)

    def mousePressEvent(self, event):
        """
        Maneja el evento de presionar el mouse

        Args:
            event: QMouseEvent
        """
        if event.button() == Qt.MouseButton.LeftButton:
            # Iniciar selección
            self.selection_start = event.pos()
            self.selection_end = event.pos()
            self.is_selecting = True
            self.update()
            logger.debug(f"Selection started at {self.selection_start}")

        elif event.button() == Qt.MouseButton.RightButton:
            # Cancelar con click derecho
            logger.info("Screenshot cancelled by right click")
            self.capture_cancelled.emit()
            self.close()

    def mouseMoveEvent(self, event):
        """
        Maneja el movimiento del mouse

        Args:
            event: QMouseEvent
        """
        if self.is_selecting and self.selection_start:
            # Actualizar punto final de selección
            self.selection_end = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        """
        Maneja el evento de soltar el mouse

        Args:
            event: QMouseEvent
        """
        if event.button() == Qt.MouseButton.LeftButton and self.is_selecting:
            self.selection_end = event.pos()
            self.is_selecting = False

            # Obtener rectángulo de selección
            selection_rect = self._get_selection_rect()

            # Validar que tenga área
            if selection_rect.width() > 0 and selection_rect.height() > 0:
                logger.info(f"Area selected: {selection_rect}")
                self.area_selected.emit(selection_rect)
                # No cerrar aquí, el controller decidirá cuándo cerrar
            else:
                logger.warning("Invalid selection area (zero size)")
                self.selection_start = None
                self.selection_end = None
                self.update()

    def keyPressEvent(self, event):
        """
        Maneja eventos de teclado

        Args:
            event: QKeyEvent
        """
        if event.key() == Qt.Key.Key_Escape:
            # Cancelar con Esc
            logger.info("Screenshot cancelled by Esc key")
            self.capture_cancelled.emit()
            self.close()

    def _get_selection_rect(self) -> QRect:
        """
        Obtiene el rectángulo de selección normalizado

        Returns:
            QRect: Rectángulo de selección (normalizado)
        """
        if not self.selection_start or not self.selection_end:
            return QRect()

        # Crear rectángulo desde los dos puntos
        rect = QRect(self.selection_start, self.selection_end)

        # Normalizar (asegurar que left < right y top < bottom)
        return rect.normalized()

    def reset_selection(self):
        """Resetea la selección actual"""
        self.selection_start = None
        self.selection_end = None
        self.is_selecting = False
        self.update()
        logger.debug("Selection reset")

    def get_selection_rect(self) -> Optional[QRect]:
        """
        Obtiene el rectángulo de selección actual

        Returns:
            QRect: Rectángulo de selección o None si no hay selección
        """
        if not self.selection_start or not self.selection_end:
            return None

        rect = self._get_selection_rect()

        # Validar que tenga área
        if rect.width() > 0 and rect.height() > 0:
            return rect

        return None
