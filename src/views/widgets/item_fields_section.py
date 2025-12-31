"""
Widget de sección de campos de items para el Creador Masivo - VERSIÓN 2.1

Características:
- Solo Item Especial (con label separado + checkbox sensible)
- Soporte para ordenamiento de items (flechas arriba/abajo)
- Gestión dinámica de items
- Validación de todos los items
- Toggle de flechas con checkbox "Crear como lista"
- Captura de pantallas integrada con preview

NOTA: El scroll es manejado por el contenedor padre (TabContentWidget)
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QMessageBox
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFont
from src.views.widgets.item_field_widget import ItemFieldWidget
from src.models.item_draft import ItemFieldData
import logging
import os

logger = logging.getLogger(__name__)


class ItemFieldsSection(QWidget):
    """
    Sección de campos de items para el Creador Masivo v2.0

    Permite agregar/eliminar múltiples items dinámicamente.
    Solo soporta Items Especiales (con label separado + checkbox sensible).

    Señales:
        data_changed: Emitida cuando cambian los datos de items
    """

    # Señales
    data_changed = pyqtSignal()

    def __init__(self, parent=None):
        """Inicializa la sección de campos de items"""
        super().__init__(parent)
        self.item_widgets: list[ItemFieldWidget] = []
        self.create_as_list_enabled = False  # Estado del checkbox "Crear como lista"

        # Screenshot management
        self.screenshot_controller = None
        self.screenshots = []  # Lista de dicts: {'filepath': str, 'label': str, 'widget': ScreenshotPreviewWidget}

        self._setup_ui()
        self._apply_styles()
        self._connect_signals()

    def _setup_ui(self):
        """Configura la interfaz del widget"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)

        # Título con contador y botones de creación
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)

        title = QLabel("📋 Items")
        title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        header_layout.addWidget(title)

        self.count_label = QLabel("(0)")
        self.count_label.setStyleSheet("color: #888; font-size: 11px;")
        header_layout.addWidget(self.count_label)

        header_layout.addStretch()

        layout.addLayout(header_layout)

        # Separador
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background-color: #444;")
        layout.addWidget(separator)

        # Layout directo para items (sin scroll - manejado por padre)
        self.items_layout = QVBoxLayout()
        self.items_layout.setContentsMargins(0, 0, 0, 0)
        self.items_layout.setSpacing(10)
        layout.addLayout(self.items_layout)

        # Botones: Item Especial + Screenshot (debajo de los items)
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 10, 0, 0)
        button_layout.addStretch()

        self.add_special_btn = QPushButton("Agregar Item")
        self.add_special_btn.setFixedHeight(35)
        self.add_special_btn.setMinimumWidth(140)
        self.add_special_btn.setToolTip("Agregar item especial con label separado y checkbox sensible")
        self.add_special_btn.setProperty("special_button", True)
        button_layout.addWidget(self.add_special_btn)

        # Botón de captura de pantalla
        self.screenshot_btn = QPushButton("📷 Captura")
        self.screenshot_btn.setFixedHeight(35)
        self.screenshot_btn.setMinimumWidth(120)
        self.screenshot_btn.setToolTip("Tomar captura de pantalla y agregar como item a la lista actual")
        self.screenshot_btn.setProperty("screenshot_button", True)
        button_layout.addWidget(self.screenshot_btn)

        layout.addLayout(button_layout)

        # === SECCIÓN DE SCREENSHOTS ===
        # Separador
        screenshots_separator = QFrame()
        screenshots_separator.setFrameShape(QFrame.Shape.HLine)
        screenshots_separator.setStyleSheet("background-color: #444;")
        layout.addWidget(screenshots_separator)

        # Título de screenshots
        screenshots_header_layout = QHBoxLayout()
        screenshots_title = QLabel("📷 Capturas de Pantalla")
        screenshots_title.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        screenshots_header_layout.addWidget(screenshots_title)

        self.screenshots_count_label = QLabel("(0)")
        self.screenshots_count_label.setStyleSheet("color: #888; font-size: 11px;")
        screenshots_header_layout.addWidget(self.screenshots_count_label)

        screenshots_header_layout.addStretch()
        layout.addLayout(screenshots_header_layout)

        # Contenedor con scroll para screenshots
        self.screenshots_scroll = QScrollArea()
        self.screenshots_scroll.setWidgetResizable(True)
        self.screenshots_scroll.setMaximumHeight(250)
        self.screenshots_scroll.setStyleSheet("""
            QScrollArea {
                border: 1px solid #444;
                border-radius: 4px;
                background-color: #2d2d2d;
            }
        """)

        # Widget contenedor de screenshots
        screenshots_container = QWidget()
        self.screenshots_layout = QVBoxLayout(screenshots_container)
        self.screenshots_layout.setContentsMargins(10, 10, 10, 10)
        self.screenshots_layout.setSpacing(10)

        # Mensaje "No hay capturas"
        self.no_screenshots_label = QLabel("No hay capturas de pantalla")
        self.no_screenshots_label.setStyleSheet("color: #666; font-style: italic; padding: 20px;")
        self.no_screenshots_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.screenshots_layout.addWidget(self.no_screenshots_label)

        self.screenshots_layout.addStretch()
        self.screenshots_scroll.setWidget(screenshots_container)
        layout.addWidget(self.screenshots_scroll)

    def _apply_styles(self):
        """Aplica estilos CSS al widget"""
        self.setStyleSheet("""
            QPushButton[special_button="true"] {
                background-color: #ff9800;
                color: #000;
                border: none;
                border-radius: 5px;
                font-weight: bold;
                font-size: 12px;
                padding: 8px 16px;
            }
            QPushButton[special_button="true"]:hover {
                background-color: #ffb74d;
            }
            QPushButton[special_button="true"]:pressed {
                background-color: #f57c00;
            }
            QPushButton[screenshot_button="true"] {
                background-color: #2196F3;
                color: #fff;
                border: none;
                border-radius: 5px;
                font-weight: bold;
                font-size: 12px;
                padding: 8px 16px;
            }
            QPushButton[screenshot_button="true"]:hover {
                background-color: #42A5F5;
            }
            QPushButton[screenshot_button="true"]:pressed {
                background-color: #1976D2;
            }
            QLabel {
                color: #ffffff;
            }
        """)

    def _connect_signals(self):
        """Conecta señales internas"""
        self.add_special_btn.clicked.connect(lambda: self.add_special_item())
        self.screenshot_btn.clicked.connect(self._on_screenshot_clicked)

    # === AGREGAR ITEMS ===

    def add_simple_item(self, content="", item_type="TEXT"):
        """
        Agrega un item en modo SIMPLE (compacto)

        Args:
            content: Contenido inicial
            item_type: Tipo inicial (TEXT, CODE, URL, PATH)
        """
        item_widget = ItemFieldWidget(
            item_type="simple",
            content=content,
            item_data_type=item_type,
            auto_detect=True,
            parent=self
        )
        self._add_item_widget(item_widget)
        logger.debug("Item simple agregado")

    def add_special_item(self, content="", label="", item_data_type="TEXT", is_sensitive=False):
        """
        Agrega un item en modo ESPECIAL (expandido)

        Args:
            content: Contenido inicial
            label: Label inicial
            item_data_type: Tipo inicial
            is_sensitive: Si es sensible
        """
        item_widget = ItemFieldWidget(
            item_type="especial",
            content=content,
            label=label,
            item_data_type=item_data_type,
            is_sensitive=is_sensitive,
            auto_detect=True,
            parent=self
        )
        self._add_item_widget(item_widget)
        logger.debug("Item especial agregado")

    def _add_item_widget(self, widget: ItemFieldWidget):
        """
        Agrega un widget de item a la sección

        Args:
            widget: ItemFieldWidget a agregar
        """
        # Conectar señales del widget
        widget.data_changed.connect(self.data_changed.emit)
        widget.delete_requested.connect(self.remove_item)
        widget.move_up_requested.connect(self.move_item_up)
        widget.move_down_requested.connect(self.move_item_down)

        # Aplicar estado de ordenamiento actual
        widget.set_ordering_visible(self.create_as_list_enabled)

        # Agregar a layout y lista
        self.items_layout.addWidget(widget)
        self.item_widgets.append(widget)

        # Actualizar contador
        self._update_count()

        # Focus en el nuevo campo
        widget.focus_content()

        self.data_changed.emit()

    # === ELIMINAR ITEMS ===

    def remove_item(self, widget: ItemFieldWidget):
        """
        Elimina un item

        Args:
            widget: Widget a eliminar
        """
        # Eliminar de lista y layout
        if widget in self.item_widgets:
            self.item_widgets.remove(widget)
            self.items_layout.removeWidget(widget)
            widget.deleteLater()

            # Actualizar contador
            self._update_count()

            logger.debug(f"Item eliminado (total: {len(self.item_widgets)})")
            self.data_changed.emit()

    # === ORDENAMIENTO ===

    def move_item_up(self, widget: ItemFieldWidget):
        """
        Mueve un item hacia arriba en la lista

        Args:
            widget: Widget a mover
        """
        try:
            index = self.item_widgets.index(widget)
        except ValueError:
            logger.error("Widget no encontrado en la lista")
            return

        if index > 0:
            # Swap en lista
            self.item_widgets[index], self.item_widgets[index - 1] = \
                self.item_widgets[index - 1], self.item_widgets[index]

            # Reconstruir layout
            self._rebuild_layout()

            logger.debug(f"Item movido arriba: {index} -> {index - 1}")
            self.data_changed.emit()

    def move_item_down(self, widget: ItemFieldWidget):
        """
        Mueve un item hacia abajo en la lista

        Args:
            widget: Widget a mover
        """
        try:
            index = self.item_widgets.index(widget)
        except ValueError:
            logger.error("Widget no encontrado en la lista")
            return

        if index < len(self.item_widgets) - 1:
            # Swap en lista
            self.item_widgets[index], self.item_widgets[index + 1] = \
                self.item_widgets[index + 1], self.item_widgets[index]

            # Reconstruir layout
            self._rebuild_layout()

            logger.debug(f"Item movido abajo: {index} -> {index + 1}")
            self.data_changed.emit()

    def _rebuild_layout(self):
        """Reconstruye el layout después de reordenar items"""
        # Remover todos los widgets del layout
        while self.items_layout.count() > 0:
            self.items_layout.takeAt(0)

        # Agregar en nuevo orden
        for widget in self.item_widgets:
            self.items_layout.addWidget(widget)

    # === TOGGLE DE ORDENAMIENTO ===

    def set_create_as_list(self, enabled: bool):
        """
        Callback cuando cambia el checkbox "Crear como lista"
        Muestra/oculta las flechas de ordenamiento en todos los items

        Args:
            enabled: True si está marcado "Crear como lista"
        """
        self.create_as_list_enabled = enabled

        for widget in self.item_widgets:
            widget.set_ordering_visible(enabled)

        logger.debug(f"Flechas de ordenamiento {'visibles' if enabled else 'ocultas'}")

    # === CONTADOR ===

    def _update_count(self):
        """Actualiza el contador de items"""
        count = self.get_items_count()
        self.count_label.setText(f"({count})")

    def get_items_count(self) -> int:
        """
        Obtiene la cantidad de items con contenido

        Returns:
            Cantidad de items no vacíos
        """
        return sum(1 for widget in self.item_widgets if not widget.is_empty())

    def get_total_fields(self) -> int:
        """
        Obtiene la cantidad total de campos (vacíos o no)

        Returns:
            Total de campos
        """
        return len(self.item_widgets)

    # === OBTENER/ESTABLECER DATOS ===

    def get_items_data(self) -> list[ItemFieldData]:
        """
        Obtiene los datos de todos los items

        Returns:
            Lista de ItemFieldData
        """
        return [widget.get_data() for widget in self.item_widgets]

    def get_non_empty_items(self) -> list[ItemFieldData]:
        """
        Obtiene solo los items con contenido

        Returns:
            Lista de ItemFieldData (solo no vacíos)
        """
        return [
            widget.get_data()
            for widget in self.item_widgets
            if not widget.is_empty()
        ]

    def set_items_data(self, items_data: list[ItemFieldData]):
        """
        Establece los items desde datos

        Args:
            items_data: Lista de ItemFieldData
        """
        # Limpiar items existentes
        for widget in self.item_widgets[:]:
            self.items_layout.removeWidget(widget)
            widget.deleteLater()

        self.item_widgets.clear()

        # Agregar items desde datos
        if items_data:
            for item_data in items_data:
                if item_data.is_special_mode:
                    # Crear item especial
                    self.add_special_item(
                        content=item_data.content,
                        label=item_data.label,
                        item_data_type=item_data.item_type,
                        is_sensitive=item_data.is_sensitive
                    )
                else:
                    # Crear item simple
                    self.add_simple_item(
                        content=item_data.content,
                        item_type=item_data.item_type
                    )

        self._update_count()

    # === LIMPIEZA ===

    def clear_all_items(self):
        """Limpia todos los items"""
        # Eliminar todos los widgets
        for widget in self.item_widgets[:]:
            self.items_layout.removeWidget(widget)
            widget.deleteLater()

        self.item_widgets.clear()
        self._update_count()

        logger.debug("Todos los items limpiados")

    # === VALIDACIÓN ===

    def validate_all(self) -> tuple[bool, list[tuple[int, str]]]:
        """
        Valida todos los items

        Returns:
            Tupla (all_valid, list of (index, error_message))
        """
        errors = []

        for index, widget in enumerate(self.item_widgets):
            if widget.is_empty():
                continue  # Items vacíos se ignoran

            is_valid, error_msg = widget.validate()
            if not is_valid:
                errors.append((index, error_msg))

        all_valid = len(errors) == 0

        if all_valid:
            logger.debug(f"Validación exitosa: {self.get_items_count()} items válidos")
        else:
            logger.warning(f"Validación fallida: {len(errors)} errores")

        return all_valid, errors

    # === FOCO ===

    def focus_first_item(self):
        """Pone foco en el primer campo de item"""
        if self.item_widgets:
            self.item_widgets[0].focus_content()

    def focus_item(self, index: int):
        """
        Pone foco en un item específico

        Args:
            index: Índice del item
        """
        if 0 <= index < len(self.item_widgets):
            self.item_widgets[index].focus_content()

    # === CONVERSIÓN ===

    def to_list(self) -> list[dict]:
        """
        Exporta a lista de diccionarios

        Returns:
            Lista de items con todos los campos
        """
        return [item.to_dict() for item in self.get_non_empty_items()]

    def from_list(self, items_data: list[dict]):
        """
        Importa desde lista de diccionarios

        Args:
            items_data: Lista de items con campos
        """
        items = [ItemFieldData.from_dict(data) for data in items_data]
        self.set_items_data(items)

    # === SCREENSHOT MANAGEMENT ===

    def set_screenshot_controller(self, controller):
        """
        Establece la referencia al ScreenshotController

        Args:
            controller: Instancia de ScreenshotController
        """
        self.screenshot_controller = controller

        # Conectar señal de captura completada
        if self.screenshot_controller:
            try:
                self.screenshot_controller.screenshot_completed.connect(
                    self._on_screenshot_captured
                )
                logger.debug("ScreenshotController connected to ItemFieldsSection")
            except Exception as e:
                logger.error(f"Error connecting screenshot controller: {e}")

    def _on_screenshot_clicked(self):
        """Callback cuando se hace clic en el botón de captura"""
        if not self.screenshot_controller:
            QMessageBox.warning(
                self,
                "Error",
                "No se ha configurado el controlador de capturas de pantalla."
            )
            logger.error("Screenshot controller not set")
            return

        # Validar que se esté creando como lista (opción seleccionada en el diálogo padre)
        # Esta validación la hace el padre, aquí solo iniciamos la captura
        logger.info("Starting screenshot capture from ItemFieldsSection")

        try:
            self.screenshot_controller.start_screenshot()
        except Exception as e:
            logger.error(f"Error starting screenshot: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"Error al iniciar captura: {str(e)}"
            )

    def _on_screenshot_captured(self, success: bool, filepath: str):
        """
        Callback cuando se completa una captura de pantalla

        Args:
            success: True si la captura fue exitosa
            filepath: Ruta completa al archivo de captura
        """
        if not success or not filepath:
            logger.warning("Screenshot capture failed or cancelled")
            return

        logger.info(f"Screenshot captured: {filepath}")

        try:
            # Importar widget de preview aquí para evitar dependencia circular
            import sys
            from pathlib import Path
            sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "util"))
            from screenshot_preview_widget import ScreenshotPreviewWidget

            # Generar label automático
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            default_label = f"Captura {timestamp}"

            # Crear widget de preview
            preview_widget = ScreenshotPreviewWidget(
                image_path=filepath,
                label=default_label,
                parent=self
            )

            # Conectar señales
            screenshot_index = len(self.screenshots)
            preview_widget.label_changed.connect(
                lambda text, idx=screenshot_index: self._on_screenshot_label_changed(idx, text)
            )
            preview_widget.remove_requested.connect(
                lambda idx=screenshot_index: self._on_screenshot_removed(idx)
            )

            # Agregar a lista
            self.screenshots.append({
                'filepath': filepath,
                'label': default_label,
                'widget': preview_widget
            })

            # Ocultar mensaje "No hay capturas"
            if self.no_screenshots_label.isVisible():
                self.no_screenshots_label.hide()

            # Agregar al layout (antes del stretch)
            self.screenshots_layout.insertWidget(
                self.screenshots_layout.count() - 1,  # Antes del stretch
                preview_widget
            )

            # Actualizar contador
            self._update_screenshots_count()

            # Emitir señal de cambio
            self.data_changed.emit()

            logger.info(f"Screenshot preview added: {default_label}")

        except Exception as e:
            logger.error(f"Error adding screenshot preview: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Error",
                f"Error al agregar preview de captura: {str(e)}"
            )

    def _on_screenshot_label_changed(self, index: int, new_label: str):
        """
        Callback cuando cambia el label de un screenshot

        Args:
            index: Índice del screenshot
            new_label: Nuevo label
        """
        if 0 <= index < len(self.screenshots):
            self.screenshots[index]['label'] = new_label
            logger.debug(f"Screenshot label updated: {index} -> {new_label}")
            self.data_changed.emit()

    def _on_screenshot_removed(self, index: int):
        """
        Callback cuando se elimina un screenshot

        Args:
            index: Índice del screenshot a eliminar
        """
        if 0 <= index < len(self.screenshots):
            screenshot = self.screenshots[index]

            # Remover widget del layout
            widget = screenshot['widget']
            self.screenshots_layout.removeWidget(widget)
            widget.deleteLater()

            # Remover de lista
            self.screenshots.pop(index)

            # Actualizar contador
            self._update_screenshots_count()

            # Mostrar mensaje si no hay screenshots
            if len(self.screenshots) == 0:
                self.no_screenshots_label.show()

            logger.info(f"Screenshot removed: {index}")
            self.data_changed.emit()

    def _update_screenshots_count(self):
        """Actualiza el contador de screenshots"""
        count = len(self.screenshots)
        self.screenshots_count_label.setText(f"({count})")

    def get_screenshots_data(self) -> list[dict]:
        """
        Obtiene los datos de todos los screenshots

        Returns:
            Lista de dicts con filepath y label
        """
        return [
            {
                'filepath': s['filepath'],
                'label': s['label']
            }
            for s in self.screenshots
        ]

    def set_screenshots_data(self, screenshots_data: list[dict]):
        """
        Establece screenshots desde datos (para restaurar drafts)

        Args:
            screenshots_data: Lista de dicts con filepath y label
        """
        # Limpiar screenshots existentes
        self.clear_all_screenshots()

        # Agregar screenshots desde datos
        if screenshots_data:
            try:
                import sys
                from pathlib import Path
                sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "util"))
                from screenshot_preview_widget import ScreenshotPreviewWidget

                for idx, screenshot_data in enumerate(screenshots_data):
                    filepath = screenshot_data.get('filepath', '')
                    label = screenshot_data.get('label', 'Captura')

                    if not filepath or not os.path.exists(filepath):
                        logger.warning(f"Screenshot file not found: {filepath}")
                        continue

                    # Crear widget de preview
                    preview_widget = ScreenshotPreviewWidget(
                        image_path=filepath,
                        label=label,
                        parent=self
                    )

                    # Conectar señales
                    screenshot_index = len(self.screenshots)
                    preview_widget.label_changed.connect(
                        lambda text, idx=screenshot_index: self._on_screenshot_label_changed(idx, text)
                    )
                    preview_widget.remove_requested.connect(
                        lambda idx=screenshot_index: self._on_screenshot_removed(idx)
                    )

                    # Agregar a lista
                    self.screenshots.append({
                        'filepath': filepath,
                        'label': label,
                        'widget': preview_widget
                    })

                    # Agregar al layout
                    self.screenshots_layout.insertWidget(
                        self.screenshots_layout.count() - 1,
                        preview_widget
                    )

                # Ocultar mensaje "No hay capturas" si hay screenshots
                if len(self.screenshots) > 0:
                    self.no_screenshots_label.hide()

                # Actualizar contador
                self._update_screenshots_count()

                logger.info(f"Restored {len(self.screenshots)} screenshots from data")

            except Exception as e:
                logger.error(f"Error setting screenshots data: {e}", exc_info=True)

    def clear_all_screenshots(self):
        """Limpia todos los screenshots"""
        for screenshot in self.screenshots[:]:
            widget = screenshot['widget']
            self.screenshots_layout.removeWidget(widget)
            widget.deleteLater()

        self.screenshots.clear()
        self._update_screenshots_count()
        self.no_screenshots_label.show()

        logger.debug("All screenshots cleared")

    def __repr__(self) -> str:
        """Representación del widget"""
        non_empty = self.get_items_count()
        total = self.get_total_fields()
        screenshots_count = len(self.screenshots)
        return f"ItemFieldsSection(items={non_empty}/{total}, screenshots={screenshots_count})"
