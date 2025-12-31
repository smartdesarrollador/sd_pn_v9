# -*- coding: utf-8 -*-
"""
Widget especializado para items de imagen en el Visor de Proyectos/Áreas

Layout (similar a ItemButton):
- Botón de ojo 👁️ (32x32px) a la izquierda para ver imagen completa
- Título + Miniatura (150x150px) en el centro (layout vertical)
- Botones de acción a la derecha: 📋 ✏️ ℹ️ (estilo ItemButton)

Características:
- Miniatura clickeable para ver imagen en tamaño completo
- Diseño consistente con items normales (ItemButton)
- Resolución automática de rutas (files_base_path + IMAGENES + filename)
- Señales compatibles con ItemGroupWidget

Autor: Widget Sidebar Team
Versión: 2.0
Fecha: 2025-12-31
"""

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QPixmap, QFont, QCursor
import os
import logging

logger = logging.getLogger(__name__)

# Importar diálogo visor de imágenes
from src.views.dialogs.image_viewer_dialog import ImageViewerDialog


class ImageItemWidget(QFrame):
    """
    Widget para items de imagen con miniatura y botones de acción (similar a ItemButton)

    Layout:
        [👁️ Ver] [Título + Miniatura 150x150] → [📋 Copiar] [✏️ Editar] [ℹ️ Info]

    Señales:
        thumbnail_clicked: Usuario hizo clic en la miniatura o botón de ojo (abre ImageViewerDialog)
        item_copied: Item copiado al portapapeles (compatibilidad con ItemGroupWidget)
        edit_clicked: Editar item
        detail_clicked: Ver detalles del item

    Señales heredadas (compatibilidad):
        move_up_clicked: Mover item arriba (botón no visible en UI actual)
        move_down_clicked: Mover item abajo (botón no visible en UI actual)
        delete_clicked: Eliminar item (botón no visible en UI actual)
    """

    # Señales
    thumbnail_clicked = pyqtSignal()
    item_copied = pyqtSignal(dict)  # Compatibilidad con ItemGroupWidget
    move_up_clicked = pyqtSignal()
    move_down_clicked = pyqtSignal()
    edit_clicked = pyqtSignal()
    detail_clicked = pyqtSignal()
    delete_clicked = pyqtSignal()

    def __init__(self, item_data: dict, db_manager=None, parent=None):
        """
        Inicializar widget de item de imagen

        Args:
            item_data: Diccionario con datos del item
            db_manager: Instancia de DBManager para obtener rutas
            parent: Widget padre
        """
        super().__init__(parent)

        self.item_data = item_data
        self.db = db_manager
        self.original_pixmap = None  # Guardar pixmap original para re-escalar

        # Logging para debug
        logger.info(f"=== ImageItemWidget.__init__ ===")
        logger.info(f"  item_data: {item_data}")
        logger.info(f"  db_manager recibido: {db_manager is not None}")
        if db_manager:
            logger.info(f"  db_manager tipo: {type(db_manager)}")
            logger.info(f"  tiene config_manager: {hasattr(db_manager, 'config_manager')}")

        self.image_path = self._get_full_image_path()

        self._setup_ui()
        self._apply_styles()
        self._load_thumbnail()

    def _get_full_image_path(self) -> str:
        """
        Obtener ruta completa de la imagen

        Intenta encontrar la imagen en este orden:
        1. Si content es ruta absoluta, usarla directamente
        2. Si existe configuración, usar base_path + folder + filename
        3. Buscar en ubicaciones comunes relativas al proyecto
        4. Devolver content tal cual (última opción)

        Returns:
            Ruta completa al archivo de imagen
        """
        content = self.item_data.get('content', '')

        if not content:
            logger.warning("Item sin contenido (content vacío)")
            return ''

        # Opción 1: Si content es una ruta absoluta, usarla directamente
        if os.path.isabs(content):
            if os.path.exists(content):
                logger.debug(f"✓ Usando ruta absoluta desde content: {content}")
                return content
            else:
                logger.warning(f"Ruta absoluta en content pero archivo no existe: {content}")

        # Opción 2: Construir ruta desde configuración (files_base_path + IMAGENES + filename)
        if self.db and hasattr(self.db, 'get_setting'):
            base_path = self.db.get_setting('files_base_path', '')

            if base_path:
                # Concatenar: files_base_path + "IMAGENES" + filename
                # (igual que en image_gallery_controller.py)
                images_folder = "IMAGENES"
                full_path = os.path.join(base_path, images_folder, content)
                if os.path.exists(full_path):
                    logger.info(f"✓ Ruta desde config (files_base_path + IMAGENES + filename): {full_path}")
                    return full_path
                else:
                    logger.debug(f"Ruta desde config no existe: {full_path}")
                    logger.debug(f"  files_base_path: {base_path}")
                    logger.debug(f"  images_folder: {images_folder}")
                    logger.debug(f"  filename: {content}")

        # Opción 3: Buscar en ubicaciones comunes relativas al proyecto
        import sys
        from pathlib import Path

        # Obtener directorio base del proyecto
        if getattr(sys, 'frozen', False):
            app_dir = Path(sys.executable).parent
        else:
            app_dir = Path(__file__).parent.parent.parent.parent

        # Ubicaciones posibles donde buscar la imagen
        possible_locations = [
            app_dir / "util" / "capturas" / content,  # util/capturas/filename
            app_dir / "IMAGENES" / content,           # IMAGENES/filename
            app_dir / "screenshots" / content,        # screenshots/filename
            app_dir / content,                        # directorio raíz/filename
        ]

        # Intentar encontrar en ubicaciones posibles
        for location in possible_locations:
            if location.exists():
                logger.info(f"✓ Imagen encontrada en ubicación alternativa: {location}")
                return str(location)

        # Opción 4: Buscar recursivamente en subdirectorios de util/capturas
        capturas_dir = app_dir / "util" / "capturas"
        if capturas_dir.exists():
            for root, dirs, files in os.walk(capturas_dir):
                if content in files:
                    found_path = os.path.join(root, content)
                    logger.info(f"✓ Imagen encontrada recursivamente en: {found_path}")
                    return found_path

        # Última opción: devolver content tal cual
        logger.warning(f"⚠ No se encontró la imagen en ninguna ubicación. Content: {content}")
        logger.warning(f"  Ubicaciones intentadas: {[str(loc) for loc in possible_locations]}")
        return content

    def _setup_ui(self):
        """Configurar interfaz del widget - Diseño similar a ItemButton"""
        # Frame properties (altura dinámica y redimensionable)
        self.setMinimumHeight(180)  # Altura mínima
        self.setMinimumWidth(300)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        # Permitir redimensionamiento vertical
        from PyQt6.QtWidgets import QSizePolicy
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding  # Permite expansión vertical
        )

        # Layout principal horizontal
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(12)

        # ==== BOTÓN DE OJO (IZQUIERDA) ====
        self.view_btn = QPushButton("👁️")
        self.view_btn.setFixedSize(32, 32)
        self.view_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.view_btn.setToolTip("Ver imagen en tamaño completo")
        self.view_btn.setStyleSheet("""
            QPushButton {
                background-color: #007acc;
                color: #ffffff;
                border: none;
                border-radius: 4px;
                font-size: 14pt;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: #005a9e;
            }
            QPushButton:pressed {
                background-color: #004578;
            }
        """)
        self.view_btn.clicked.connect(self._on_thumbnail_clicked)
        main_layout.addWidget(self.view_btn, alignment=Qt.AlignmentFlag.AlignTop)

        # ==== CONTENIDO CENTRAL (TÍTULO + MINIATURA) ====
        content_layout = QVBoxLayout()
        content_layout.setSpacing(8)

        # Título del item
        label_text = self.item_data.get('label', 'Sin título')
        self.title_label = QLabel(label_text)
        self.title_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.title_label.setStyleSheet("color: #ffffff; background: transparent;")
        self.title_label.setWordWrap(True)
        content_layout.addWidget(self.title_label)

        # Miniatura clickeable (redimensionable, min 150x150, max 500x500)
        self.thumbnail_label = QLabel()
        self.thumbnail_label.setMinimumSize(150, 150)
        self.thumbnail_label.setMaximumSize(500, 500)
        self.thumbnail_label.setScaledContents(False)  # Mantener aspect ratio
        self.thumbnail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumbnail_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.thumbnail_label.setToolTip("Clic para ver imagen completa. Arrastra el borde del contenedor para redimensionar.")

        # Size policy para permitir crecimiento
        from PyQt6.QtWidgets import QSizePolicy
        self.thumbnail_label.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )

        self.thumbnail_label.setStyleSheet("""
            QLabel {
                border: 2px solid #555;
                border-radius: 4px;
                background-color: #1e1e1e;
            }
            QLabel:hover {
                border-color: #007acc;
            }
        """)
        # Hacer clickeable
        self.thumbnail_label.mousePressEvent = lambda event: self._on_thumbnail_clicked()

        # Centrar la miniatura horizontalmente
        content_layout.addWidget(self.thumbnail_label, alignment=Qt.AlignmentFlag.AlignHCenter)

        # Descripción (si existe)
        description = self.item_data.get('description', '')
        if description:
            desc_label = QLabel(description)
            desc_label.setFont(QFont("Segoe UI", 9))
            desc_label.setStyleSheet("color: #888; background: transparent;")
            desc_label.setWordWrap(True)
            content_layout.addWidget(desc_label)

        content_layout.addStretch()
        main_layout.addLayout(content_layout, stretch=1)

        # Spacer para empujar botones a la derecha
        main_layout.addStretch()

        # ==== BOTONES DE ACCIÓN (DERECHA ARRIBA) - Similar a ItemButton ====
        # Layout vertical para alinear botones arriba
        buttons_container = QVBoxLayout()
        buttons_container.setSpacing(0)

        # Fila horizontal de botones
        buttons_row = QHBoxLayout()
        buttons_row.setSpacing(4)

        # Copiar ruta
        self.copy_btn = self._create_action_button("📋", "Copiar ruta de imagen")
        self.copy_btn.clicked.connect(self._on_copy_clicked)
        buttons_row.addWidget(self.copy_btn)

        # Editar
        self.edit_btn = self._create_action_button("✏️", "Editar")
        self.edit_btn.clicked.connect(self.edit_clicked.emit)
        buttons_row.addWidget(self.edit_btn)

        # Detalles (info)
        self.detail_btn = self._create_action_button("ℹ️", "Ver detalles")
        self.detail_btn.clicked.connect(self.detail_clicked.emit)
        buttons_row.addWidget(self.detail_btn)

        # Agregar fila de botones al contenedor vertical
        buttons_container.addLayout(buttons_row)
        # Stretch para empujar botones hacia arriba
        buttons_container.addStretch()

        main_layout.addLayout(buttons_container)

    def _create_action_button(self, text: str, tooltip: str) -> QPushButton:
        """
        Crear botón de acción uniforme - Estilo similar a ItemButton

        Args:
            text: Texto/emoji del botón
            tooltip: Tooltip del botón

        Returns:
            QPushButton configurado
        """
        btn = QPushButton(text)
        btn.setFixedSize(28, 28)
        btn.setToolTip(tooltip)
        btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                font-size: 12pt;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: #3e3e42;
                border-radius: 3px;
            }
        """)
        return btn

    def _apply_styles(self):
        """Aplicar estilos CSS - Similar a ItemButton"""
        self.setStyleSheet("""
            QFrame {
                background-color: #2d2d2d;
                border: none;
                border-bottom: 1px solid #1e1e1e;
            }
            QFrame:hover {
                background-color: #3d3d3d;
            }
            QLabel {
                color: #cccccc;
                background-color: transparent;
                border: none;
            }
        """)

    def _load_thumbnail(self):
        """Cargar miniatura de la imagen"""
        logger.info(f"Intentando cargar thumbnail desde: {self.image_path}")

        if not self.image_path:
            self.thumbnail_label.setText("❌\nSin\nruta")
            self.thumbnail_label.setStyleSheet("""
                QLabel {
                    border: 2px solid #d32f2f;
                    color: #ff5555;
                    font-size: 9pt;
                }
            """)
            logger.error("Ruta de imagen vacía")
            return

        if not os.path.exists(self.image_path):
            self.thumbnail_label.setText("❌\nNo\nencontrada")
            self.thumbnail_label.setStyleSheet("""
                QLabel {
                    border: 2px solid #d32f2f;
                    color: #ff5555;
                    font-size: 9pt;
                }
            """)
            logger.warning(f"Imagen no encontrada en: {self.image_path}")
            logger.warning(f"  - Existe directorio padre: {os.path.exists(os.path.dirname(self.image_path))}")
            logger.warning(f"  - Content original: {self.item_data.get('content', '')}")
            return

        try:
            # Cargar imagen original
            logger.debug(f"Cargando QPixmap desde: {self.image_path}")
            pixmap = QPixmap(self.image_path)

            if pixmap.isNull():
                self.thumbnail_label.setText("❌\nError\ncargar")
                logger.error(f"QPixmap.isNull() - No se pudo cargar imagen: {self.image_path}")
                return

            # Guardar pixmap original para re-escalar después
            self.original_pixmap = pixmap

            # Escalar a tamaño del label manteniendo aspect ratio
            self._update_thumbnail_scale()

            logger.info(f"✓ Thumbnail cargado exitosamente (tamaño original: {pixmap.width()}x{pixmap.height()}): {self.image_path}")
            logger.info(f"  Miniatura redimensionable entre 150x150 y 500x500")

        except Exception as e:
            self.thumbnail_label.setText("❌\nError")
            logger.error(f"Excepción al cargar thumbnail: {e}")
            import traceback
            logger.error(traceback.format_exc())

    def _on_thumbnail_clicked(self):
        """Callback cuando se hace clic en la miniatura o botón de ojo"""
        # Emitir señal para compatibilidad
        self.thumbnail_clicked.emit()

        # Abrir diálogo visor de imágenes
        if self.image_path and os.path.exists(self.image_path):
            try:
                title = self.item_data.get('label', 'Imagen')
                dialog = ImageViewerDialog(
                    image_path=self.image_path,
                    title=title,
                    parent=self.window()
                )
                dialog.exec()
                logger.info(f"Diálogo visor de imagen abierto: {self.image_path}")
            except Exception as e:
                logger.error(f"Error al abrir diálogo visor de imagen: {e}")
                import traceback
                logger.error(traceback.format_exc())
        else:
            logger.warning(f"No se puede abrir visor: imagen no encontrada en {self.image_path}")

    def _on_copy_clicked(self):
        """Copiar ruta de imagen al portapapeles"""
        try:
            import pyperclip
            pyperclip.copy(self.image_path)
            logger.info(f"Ruta de imagen copiada: {self.image_path}")
            self.item_copied.emit(self.item_data)
        except Exception as e:
            logger.error(f"Error al copiar ruta de imagen: {e}")

    def has_match(self, search_text: str) -> bool:
        """
        Verificar si el item coincide con el texto de búsqueda

        Args:
            search_text: Texto a buscar (lowercase)

        Returns:
            True si coincide con label o descripción
        """
        label = self.item_data.get('label', '').lower()
        description = self.item_data.get('description', '').lower()

        return search_text in label or search_text in description

    def highlight_text(self, search_text: str):
        """
        Resaltar texto de búsqueda (cambiar borde - similar a ItemButton)

        Args:
            search_text: Texto buscado
        """
        self.setStyleSheet("""
            QFrame {
                background-color: #3d3d3d;
                border: none;
                border-left: 3px solid #FFD700;
                border-bottom: 1px solid #FFD700;
            }
            QLabel {
                color: #cccccc;
                background-color: transparent;
                border: none;
            }
        """)

    def clear_highlight(self):
        """Limpiar resaltado de búsqueda"""
        self._apply_styles()

    def _update_thumbnail_scale(self):
        """Actualizar escala de la miniatura según tamaño del label"""
        if not self.original_pixmap or self.original_pixmap.isNull():
            return

        # Obtener tamaño disponible del label
        label_size = self.thumbnail_label.size()

        # Escalar pixmap manteniendo aspect ratio
        scaled_pixmap = self.original_pixmap.scaled(
            label_size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )

        self.thumbnail_label.setPixmap(scaled_pixmap)
        logger.debug(f"Thumbnail re-escalado a: {scaled_pixmap.width()}x{scaled_pixmap.height()}")

    def resizeEvent(self, event):
        """Detectar cambios de tamaño y re-escalar miniatura"""
        super().resizeEvent(event)
        # Re-escalar miniatura cuando cambia el tamaño del widget
        if hasattr(self, 'original_pixmap') and self.original_pixmap:
            self._update_thumbnail_scale()
