# -*- coding: utf-8 -*-
"""
Diálogo visor de imágenes con zoom

Muestra imágenes en tamaño grande con controles de zoom y navegación.

Características:
- Visualización de imagen en alta resolución
- Zoom in/out con botones o rueda del mouse
- Scroll para imágenes grandes
- Ajustar a ventana
- Vista 1:1 (tamaño real)

Autor: Widget Sidebar Team
Versión: 1.0
Fecha: 2025-12-31
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QScrollArea, QWidget, QSizePolicy
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPixmap, QWheelEvent, QCursor
import os
import logging

logger = logging.getLogger(__name__)


class ImageViewerDialog(QDialog):
    """
    Diálogo para visualizar imágenes en tamaño grande

    Características:
        - Zoom in/out (25% - 400%)
        - Scroll para imágenes grandes
        - Ajustar a ventana automáticamente
        - Vista 1:1 (tamaño real)
    """

    def __init__(self, image_path: str, title: str = "Visor de Imagen", parent=None):
        """
        Inicializar diálogo visor de imágenes

        Args:
            image_path: Ruta completa a la imagen
            title: Título del diálogo (default: nombre del archivo)
            parent: Widget padre
        """
        super().__init__(parent)

        self.image_path = image_path
        self.original_pixmap = None
        self.current_zoom = 1.0  # 100%

        # Usar nombre de archivo como título si no se proporciona otro
        if title == "Visor de Imagen" and image_path:
            title = f"Visor de Imagen - {os.path.basename(image_path)}"

        self.setWindowTitle(title)
        self.setModal(True)
        self.resize(900, 700)

        self._setup_ui()
        self._load_image()

    def _setup_ui(self):
        """Configurar interfaz de usuario"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # ==== BARRA DE HERRAMIENTAS ====
        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)

        # Información de imagen
        self.info_label = QLabel("Cargando...")
        self.info_label.setStyleSheet("""
            QLabel {
                color: #cccccc;
                font-size: 10pt;
                padding: 4px;
            }
        """)
        toolbar.addWidget(self.info_label)

        toolbar.addStretch()

        # Botón Zoom Out
        self.zoom_out_btn = QPushButton("🔍-")
        self.zoom_out_btn.setFixedSize(40, 32)
        self.zoom_out_btn.setToolTip("Reducir zoom (25% min)")
        self.zoom_out_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.zoom_out_btn.clicked.connect(self._zoom_out)
        toolbar.addWidget(self.zoom_out_btn)

        # Label de zoom
        self.zoom_label = QLabel("100%")
        self.zoom_label.setFixedWidth(60)
        self.zoom_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.zoom_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 10pt;
                font-weight: bold;
                padding: 4px;
            }
        """)
        toolbar.addWidget(self.zoom_label)

        # Botón Zoom In
        self.zoom_in_btn = QPushButton("🔍+")
        self.zoom_in_btn.setFixedSize(40, 32)
        self.zoom_in_btn.setToolTip("Aumentar zoom (400% max)")
        self.zoom_in_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.zoom_in_btn.clicked.connect(self._zoom_in)
        toolbar.addWidget(self.zoom_in_btn)

        # Botón Ajustar a ventana
        self.fit_btn = QPushButton("🖼️")
        self.fit_btn.setFixedSize(40, 32)
        self.fit_btn.setToolTip("Ajustar a ventana")
        self.fit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.fit_btn.clicked.connect(self._fit_to_window)
        toolbar.addWidget(self.fit_btn)

        # Botón Tamaño real
        self.actual_size_btn = QPushButton("1:1")
        self.actual_size_btn.setFixedSize(40, 32)
        self.actual_size_btn.setToolTip("Tamaño real (100%)")
        self.actual_size_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.actual_size_btn.clicked.connect(self._actual_size)
        toolbar.addWidget(self.actual_size_btn)

        layout.addLayout(toolbar)

        # ==== ÁREA DE IMAGEN CON SCROLL ====
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(False)
        self.scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: #1e1e1e;
                border: 1px solid #444;
            }
        """)

        # Label de imagen
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet("""
            QLabel {
                background-color: #2d2d2d;
                padding: 10px;
            }
        """)

        # Habilitar wheel event para zoom
        self.image_label.wheelEvent = self._wheel_event

        self.scroll_area.setWidget(self.image_label)
        layout.addWidget(self.scroll_area)

        # ==== BOTÓN CERRAR ====
        close_btn = QPushButton("Cerrar")
        close_btn.setFixedHeight(36)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #007acc;
                color: #ffffff;
                border: none;
                border-radius: 4px;
                font-size: 11pt;
                font-weight: bold;
                padding: 8px 20px;
            }
            QPushButton:hover {
                background-color: #005a9e;
            }
            QPushButton:pressed {
                background-color: #004578;
            }
        """)
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

        # Aplicar estilo general
        self.setStyleSheet("""
            QDialog {
                background-color: #2d2d2d;
            }
            QPushButton {
                background-color: #3d3d3d;
                color: #ffffff;
                border: 1px solid #555;
                border-radius: 4px;
                font-size: 10pt;
                padding: 4px;
            }
            QPushButton:hover {
                background-color: #4d4d4d;
                border-color: #007acc;
            }
            QPushButton:pressed {
                background-color: #2d2d2d;
            }
        """)

    def _load_image(self):
        """Cargar imagen desde archivo"""
        if not self.image_path or not os.path.exists(self.image_path):
            self.image_label.setText("❌ Imagen no encontrada")
            self.info_label.setText("Error: Archivo no existe")
            logger.error(f"Imagen no encontrada: {self.image_path}")
            return

        try:
            # Cargar imagen original
            self.original_pixmap = QPixmap(self.image_path)

            if self.original_pixmap.isNull():
                self.image_label.setText("❌ Error al cargar imagen")
                self.info_label.setText("Error: Formato no soportado")
                logger.error(f"Error al cargar pixmap: {self.image_path}")
                return

            # Actualizar información
            width = self.original_pixmap.width()
            height = self.original_pixmap.height()
            size_kb = os.path.getsize(self.image_path) / 1024

            self.info_label.setText(
                f"📐 {width}x{height}px | 💾 {size_kb:.1f} KB | 📁 {os.path.basename(self.image_path)}"
            )

            # Ajustar a ventana inicialmente
            self._fit_to_window()

            logger.info(f"Imagen cargada: {self.image_path} ({width}x{height})")

        except Exception as e:
            self.image_label.setText("❌ Error al cargar imagen")
            self.info_label.setText(f"Error: {str(e)}")
            logger.error(f"Excepción al cargar imagen: {e}")
            import traceback
            logger.error(traceback.format_exc())

    def _update_image(self):
        """Actualizar imagen mostrada según zoom actual"""
        if not self.original_pixmap or self.original_pixmap.isNull():
            return

        # Calcular nuevo tamaño
        new_width = int(self.original_pixmap.width() * self.current_zoom)
        new_height = int(self.original_pixmap.height() * self.current_zoom)

        # Escalar imagen
        scaled_pixmap = self.original_pixmap.scaled(
            new_width, new_height,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )

        self.image_label.setPixmap(scaled_pixmap)
        self.image_label.resize(scaled_pixmap.size())

        # Actualizar label de zoom
        self.zoom_label.setText(f"{int(self.current_zoom * 100)}%")

        logger.debug(f"Imagen actualizada a {int(self.current_zoom * 100)}% ({new_width}x{new_height})")

    def _zoom_in(self):
        """Aumentar zoom (máx 400%)"""
        if self.current_zoom < 4.0:
            self.current_zoom = min(4.0, self.current_zoom + 0.25)
            self._update_image()

    def _zoom_out(self):
        """Reducir zoom (mín 25%)"""
        if self.current_zoom > 0.25:
            self.current_zoom = max(0.25, self.current_zoom - 0.25)
            self._update_image()

    def _fit_to_window(self):
        """Ajustar imagen a tamaño de ventana"""
        if not self.original_pixmap or self.original_pixmap.isNull():
            return

        # Obtener tamaño disponible (con margen)
        available_width = self.scroll_area.width() - 40
        available_height = self.scroll_area.height() - 40

        # Calcular zoom para ajustar
        zoom_width = available_width / self.original_pixmap.width()
        zoom_height = available_height / self.original_pixmap.height()

        # Usar el menor para que quepa completamente
        self.current_zoom = min(zoom_width, zoom_height, 1.0)  # Max 100% al ajustar

        self._update_image()
        logger.debug("Imagen ajustada a ventana")

    def _actual_size(self):
        """Mostrar imagen en tamaño real (100%)"""
        self.current_zoom = 1.0
        self._update_image()
        logger.debug("Imagen a tamaño real (100%)")

    def _wheel_event(self, event: QWheelEvent):
        """Manejar evento de rueda del mouse para zoom"""
        # Ctrl + Wheel = Zoom
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            if event.angleDelta().y() > 0:
                self._zoom_in()
            else:
                self._zoom_out()
            event.accept()
        else:
            # Scroll normal
            event.ignore()

    def keyPressEvent(self, event):
        """Manejar eventos de teclado"""
        if event.key() == Qt.Key.Key_Escape:
            self.accept()
        elif event.key() == Qt.Key.Key_Plus or event.key() == Qt.Key.Key_Equal:
            self._zoom_in()
        elif event.key() == Qt.Key.Key_Minus:
            self._zoom_out()
        elif event.key() == Qt.Key.Key_0:
            self._actual_size()
        elif event.key() == Qt.Key.Key_F:
            self._fit_to_window()
        else:
            super().keyPressEvent(event)
