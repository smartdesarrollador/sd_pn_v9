"""
Widget de sección de campos de items para el Creador Masivo - VERSIÓN 2.0

Características:
- Solo Item Especial (con label separado + checkbox sensible)
- Soporte para ordenamiento de items (flechas arriba/abajo)
- Gestión dinámica de items
- Validación de todos los items
- Toggle de flechas con checkbox "Crear como lista"

NOTA: El scroll es manejado por el contenedor padre (TabContentWidget)
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFont
from src.views.widgets.item_field_widget import ItemFieldWidget
from src.models.item_draft import ItemFieldData
import logging

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

        # Botón: Item Especial (debajo de los items)
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 10, 0, 0)
        button_layout.addStretch()

        self.add_special_btn = QPushButton("⚙️ Item Especial")
        self.add_special_btn.setFixedHeight(35)
        self.add_special_btn.setMinimumWidth(140)
        self.add_special_btn.setToolTip("Agregar item especial con label separado y checkbox sensible")
        self.add_special_btn.setProperty("special_button", True)
        button_layout.addWidget(self.add_special_btn)

        layout.addLayout(button_layout)

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
            QLabel {
                color: #ffffff;
            }
        """)

    def _connect_signals(self):
        """Conecta señales internas"""
        self.add_special_btn.clicked.connect(lambda: self.add_special_item())

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

    def __repr__(self) -> str:
        """Representación del widget"""
        non_empty = self.get_items_count()
        total = self.get_total_fields()
        return f"ItemFieldsSection(items={non_empty}/{total})"
