"""
Widget para campo individual de item en el Creador Masivo - VERSIÓN 2.0

Soporta 2 modos:
- SIMPLE: Campo compacto (label = content automático)
- ESPECIAL: Formulario expandido con label separado + checkbox sensible

Componentes:
- Modo Simple: [icon] [content] [type] [↑] [↓] [×]
- Modo Especial: Formulario vertical con label, content, type, sensitive checkbox
"""

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLineEdit, QComboBox,
    QPushButton, QLabel, QCheckBox, QFrame
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFont
from src.core.item_validation_service import ItemValidationService
from src.models.item_draft import ItemFieldData
import logging

logger = logging.getLogger(__name__)


class ItemFieldWidget(QWidget):
    """
    Widget para un campo individual de item con soporte para 2 modos

    Modos:
    - simple: Modo compacto (label = content automático)
    - especial: Modo expandido (label + content separados, checkbox sensible)

    Señales:
        data_changed: Emitida cuando cambian los datos
        delete_requested: Emitida cuando se solicita eliminar (self)
        move_up_requested: Emitida cuando se solicita mover arriba (self)
        move_down_requested: Emitida cuando se solicita mover abajo (self)
    """

    # Señales
    data_changed = pyqtSignal()
    delete_requested = pyqtSignal(object)  # self
    move_up_requested = pyqtSignal(object)  # self
    move_down_requested = pyqtSignal(object)  # self

    # Tipos de items disponibles
    ITEM_TYPES = ['TEXT', 'CODE', 'URL', 'PATH']

    def __init__(self, item_type="simple", content="", label="",
                 item_data_type="TEXT", is_sensitive=False,
                 auto_detect=True, parent=None):
        """
        Inicializa el widget de campo de item

        Args:
            item_type: "simple" o "especial"
            content: Contenido inicial
            label: Label inicial (solo modo especial)
            item_data_type: Tipo de dato (TEXT, CODE, URL, PATH)
            is_sensitive: Si es dato sensible (solo modo especial)
            auto_detect: Habilitar auto-detección de tipo
            parent: Widget padre
        """
        super().__init__(parent)
        self.item_mode = item_type  # "simple" o "especial"
        self.auto_detect_enabled = auto_detect

        # Widgets que varían según el modo
        self.label_input = None  # Solo en modo especial
        self.sensitive_checkbox = None  # Solo en modo especial

        # Widgets comunes
        self.content_input = None
        self.type_combo = None
        self.up_btn = None
        self.down_btn = None
        self.delete_btn = None
        self.type_indicator = None

        self._setup_ui()
        self._apply_styles()

        # Establecer valores iniciales
        self.set_content(content)
        if self.label_input:
            self.set_label(label)
        self.set_data_type(item_data_type)
        if self.sensitive_checkbox:
            self.set_sensitive(is_sensitive)

        self._connect_signals()

        logger.debug(f"ItemFieldWidget creado en modo '{item_type}'")

    def _setup_ui(self):
        """Configura la interfaz según el modo"""
        if self.item_mode == "simple":
            self._setup_simple_mode()
        else:
            self._setup_special_mode()

    def _setup_simple_mode(self):
        """
        Configura layout para modo SIMPLE (compacto)

        Layout: [icon] [content_input (stretch)] [type_combo] [↑] [↓] [×]
        """
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(8)

        # Indicador de tipo (emoji)
        self.type_indicator = QLabel("📄")
        self.type_indicator.setFixedWidth(25)
        self.type_indicator.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setPointSize(14)
        self.type_indicator.setFont(font)
        layout.addWidget(self.type_indicator)

        # Content input
        self.content_input = QLineEdit()
        self.content_input.setPlaceholderText("Ingrese el contenido del item...")
        self.content_input.setMinimumHeight(35)
        layout.addWidget(self.content_input, 1)  # Stretch

        # Type combo
        self.type_combo = QComboBox()
        self.type_combo.addItems(self.ITEM_TYPES)
        self.type_combo.setFixedWidth(90)
        self.type_combo.setMinimumHeight(35)
        layout.addWidget(self.type_combo)

        # Botones de ordenamiento (inicialmente ocultos)
        self.up_btn = QPushButton("🔺")
        self.up_btn.setFixedSize(30, 30)
        self.up_btn.setToolTip("Mover arriba")
        self.up_btn.setVisible(False)
        self.up_btn.setProperty("ordering_button", True)
        layout.addWidget(self.up_btn)

        self.down_btn = QPushButton("🔻")
        self.down_btn.setFixedSize(30, 30)
        self.down_btn.setToolTip("Mover abajo")
        self.down_btn.setVisible(False)
        self.down_btn.setProperty("ordering_button", True)
        layout.addWidget(self.down_btn)

        # Botón eliminar
        self.delete_btn = QPushButton("❌")
        self.delete_btn.setFixedSize(30, 30)
        self.delete_btn.setToolTip("Eliminar item")
        layout.addWidget(self.delete_btn)

    def _setup_special_mode(self):
        """
        Configura layout para modo ESPECIAL (expandido)

        Layout vertical con:
        - Label input
        - Content input
        - Type combo
        - Sensitive checkbox + botones de control
        """
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(10)

        # Label field
        label_label = QLabel("Label:")
        label_label.setStyleSheet("font-weight: bold; color: #ccc;")
        main_layout.addWidget(label_label)

        self.label_input = QLineEdit()
        self.label_input.setPlaceholderText("Nombre o título del item")
        self.label_input.setMinimumHeight(35)
        main_layout.addWidget(self.label_input)

        # Content field
        content_label = QLabel("Content:")
        content_label.setStyleSheet("font-weight: bold; color: #ccc;")
        main_layout.addWidget(content_label)

        self.content_input = QLineEdit()
        self.content_input.setPlaceholderText("Contenido o comando")
        self.content_input.setMinimumHeight(35)
        main_layout.addWidget(self.content_input)

        # Type combo
        type_layout = QHBoxLayout()
        type_label = QLabel("Tipo:")
        type_label.setStyleSheet("font-weight: bold; color: #ccc;")
        type_layout.addWidget(type_label)

        self.type_combo = QComboBox()
        self.type_combo.addItems(self.ITEM_TYPES)
        self.type_combo.setFixedWidth(100)
        self.type_combo.setMinimumHeight(35)
        type_layout.addWidget(self.type_combo)
        type_layout.addStretch()

        main_layout.addLayout(type_layout)

        # Bottom row: Sensitive checkbox + control buttons
        bottom_layout = QHBoxLayout()

        self.sensitive_checkbox = QCheckBox("🔒 Dato sensible (is_sensitive)")
        self.sensitive_checkbox.setStyleSheet("color: #ffeb3b; font-weight: bold;")
        self.sensitive_checkbox.setToolTip("Marca si este item contiene información sensible que debe cifrarse")
        bottom_layout.addWidget(self.sensitive_checkbox)

        bottom_layout.addStretch()

        # Botones de ordenamiento (inicialmente ocultos)
        self.up_btn = QPushButton("🔺")
        self.up_btn.setFixedSize(30, 30)
        self.up_btn.setToolTip("Mover arriba")
        self.up_btn.setVisible(False)
        self.up_btn.setProperty("ordering_button", True)
        bottom_layout.addWidget(self.up_btn)

        self.down_btn = QPushButton("🔻")
        self.down_btn.setFixedSize(30, 30)
        self.down_btn.setToolTip("Mover abajo")
        self.down_btn.setVisible(False)
        self.down_btn.setProperty("ordering_button", True)
        bottom_layout.addWidget(self.down_btn)

        # Botón eliminar
        self.delete_btn = QPushButton("❌")
        self.delete_btn.setFixedSize(30, 30)
        self.delete_btn.setToolTip("Eliminar item")
        bottom_layout.addWidget(self.delete_btn)

        main_layout.addLayout(bottom_layout)

    def _apply_styles(self):
        """Aplica estilos CSS según el modo"""
        if self.item_mode == "simple":
            self.setStyleSheet("""
                ItemFieldWidget {
                    background-color: #2d2d2d;
                    border: 1px solid #3d3d3d;
                    border-radius: 5px;
                    padding: 2px;
                }
                ItemFieldWidget:hover {
                    border-color: #2196F3;
                }
                QLineEdit {
                    background-color: #252525;
                    color: #ffffff;
                    border: 1px solid #444;
                    border-radius: 4px;
                    padding: 6px 10px;
                    font-size: 12px;
                }
                QLineEdit:focus {
                    border: 1px solid #2196F3;
                    background-color: #303030;
                }
                QLineEdit::placeholder {
                    color: #888;
                }
                QComboBox {
                    background-color: #3d3d3d;
                    color: #ffffff;
                    border: 1px solid #444;
                    border-radius: 4px;
                    padding: 6px;
                    font-size: 11px;
                }
                QComboBox:hover {
                    background-color: #4d4d4d;
                }
                QPushButton[ordering_button="true"] {
                    background-color: #555;
                    color: #fff;
                    border: 1px solid #666;
                    border-radius: 4px;
                    font-size: 12px;
                }
                QPushButton[ordering_button="true"]:hover {
                    background-color: #2196F3;
                    border-color: #2196F3;
                }
                QPushButton:not([ordering_button="true"]) {
                    background-color: #d32f2f;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    font-weight: bold;
                    font-size: 14px;
                }
                QPushButton:not([ordering_button="true"]):hover {
                    background-color: #b71c1c;
                }
            """)
        else:  # especial
            self.setStyleSheet("""
                ItemFieldWidget {
                    background-color: #2a2a2a;
                    border: 2px solid #ff9800;
                    border-radius: 8px;
                    padding: 5px;
                }
                ItemFieldWidget:hover {
                    border-color: #ffb74d;
                    background-color: #2d2d2d;
                }
                QLineEdit {
                    background-color: #252525;
                    color: #ffffff;
                    border: 1px solid #555;
                    border-radius: 4px;
                    padding: 8px 12px;
                    font-size: 12px;
                }
                QLineEdit:focus {
                    border: 2px solid #ff9800;
                    background-color: #303030;
                }
                QLineEdit::placeholder {
                    color: #888;
                }
                QComboBox {
                    background-color: #3d3d3d;
                    color: #ffffff;
                    border: 1px solid #555;
                    border-radius: 4px;
                    padding: 6px;
                    font-size: 11px;
                }
                QComboBox:hover {
                    background-color: #4d4d4d;
                }
                QCheckBox {
                    color: #ffeb3b;
                    spacing: 6px;
                }
                QCheckBox::indicator {
                    width: 18px;
                    height: 18px;
                    border: 2px solid #666;
                    border-radius: 3px;
                    background-color: #2d2d2d;
                }
                QCheckBox::indicator:hover {
                    border-color: #ffeb3b;
                }
                QCheckBox::indicator:checked {
                    background-color: #ffeb3b;
                    border-color: #ffeb3b;
                    image: none;
                }
                QPushButton[ordering_button="true"] {
                    background-color: #555;
                    color: #fff;
                    border: 1px solid #666;
                    border-radius: 4px;
                    font-size: 12px;
                }
                QPushButton[ordering_button="true"]:hover {
                    background-color: #ff9800;
                    border-color: #ff9800;
                }
                QPushButton:not([ordering_button="true"]) {
                    background-color: #d32f2f;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    font-weight: bold;
                    font-size: 14px;
                }
                QPushButton:not([ordering_button="true"]):hover {
                    background-color: #b71c1c;
                }
            """)

    def _connect_signals(self):
        """Conecta señales internas"""
        # Señales de cambio de datos
        self.content_input.textChanged.connect(self._on_content_changed)
        self.type_combo.currentTextChanged.connect(self._on_type_changed)

        if self.label_input:
            self.label_input.textChanged.connect(self.data_changed.emit)

        if self.sensitive_checkbox:
            self.sensitive_checkbox.stateChanged.connect(self.data_changed.emit)

        # Señales de botones
        self.delete_btn.clicked.connect(lambda: self.delete_requested.emit(self))
        self.up_btn.clicked.connect(lambda: self.move_up_requested.emit(self))
        self.down_btn.clicked.connect(lambda: self.move_down_requested.emit(self))

    def _on_content_changed(self, text: str):
        """Callback cuando cambia el contenido"""
        # Auto-detectar tipo si está habilitado
        if self.auto_detect_enabled and text.strip() and self.item_mode == "simple":
            detected_type = ItemValidationService.auto_detect_type(text)
            if detected_type != self.get_data_type():
                self.type_combo.blockSignals(True)
                self.set_data_type(detected_type)
                self.type_combo.blockSignals(False)
                logger.debug(f"Auto-detectado tipo {detected_type}")

        self.data_changed.emit()

    def _on_type_changed(self, item_type: str):
        """Callback cuando cambia el tipo"""
        if self.type_indicator:
            icon = ItemValidationService.get_type_icon(item_type)
            self.type_indicator.setText(icon)
            tooltip = ItemValidationService.get_type_description(item_type)
            self.type_indicator.setToolTip(tooltip)

        self.data_changed.emit()

    # === GETTERS Y SETTERS ===

    def get_content(self) -> str:
        """Obtiene el contenido"""
        return self.content_input.text().strip()

    def set_content(self, content: str):
        """Establece el contenido"""
        self.content_input.setText(content)

    def get_label(self) -> str:
        """Obtiene el label (solo modo especial)"""
        if self.label_input:
            return self.label_input.text().strip()
        return ""

    def set_label(self, label: str):
        """Establece el label (solo modo especial)"""
        if self.label_input:
            self.label_input.setText(label)

    def get_data_type(self) -> str:
        """Obtiene el tipo de dato"""
        return self.type_combo.currentText()

    def set_data_type(self, item_type: str):
        """Establece el tipo de dato"""
        if item_type in self.ITEM_TYPES:
            self.type_combo.setCurrentText(item_type)
        else:
            logger.warning(f"Tipo inválido: {item_type}, usando TEXT")
            self.type_combo.setCurrentText('TEXT')

    def get_sensitive(self) -> bool:
        """Obtiene el estado de dato sensible (solo modo especial)"""
        if self.sensitive_checkbox:
            return self.sensitive_checkbox.isChecked()
        return False

    def set_sensitive(self, is_sensitive: bool):
        """Establece el estado de dato sensible (solo modo especial)"""
        if self.sensitive_checkbox:
            self.sensitive_checkbox.setChecked(is_sensitive)

    def set_ordering_visible(self, visible: bool):
        """Muestra/oculta botones de ordenamiento"""
        self.up_btn.setVisible(visible)
        self.down_btn.setVisible(visible)

    # === CONVERSIÓN DE DATOS ===

    def get_data(self) -> ItemFieldData:
        """
        Obtiene los datos del widget como ItemFieldData

        Returns:
            ItemFieldData con todos los campos
        """
        return ItemFieldData(
            content=self.get_content(),
            item_type=self.get_data_type(),
            label=self.get_label() if self.item_mode == "especial" else "",
            is_sensitive=self.get_sensitive() if self.item_mode == "especial" else False,
            is_special_mode=(self.item_mode == "especial")
        )

    def set_data(self, data: ItemFieldData):
        """
        Establece los datos desde ItemFieldData

        Args:
            data: ItemFieldData con los datos
        """
        self.set_content(data.content)
        self.set_data_type(data.item_type)

        if self.item_mode == "especial":
            if self.label_input:
                self.set_label(data.label)
            if self.sensitive_checkbox:
                self.set_sensitive(data.is_sensitive)

    def to_dict(self) -> dict:
        """Exporta a diccionario"""
        return self.get_data().to_dict()

    def from_dict(self, data: dict):
        """Importa desde diccionario"""
        item_data = ItemFieldData.from_dict(data)
        self.set_data(item_data)

    # === VALIDACIÓN ===

    def is_empty(self) -> bool:
        """Verifica si el campo está vacío"""
        return not self.get_content()

    def validate(self) -> tuple[bool, str]:
        """
        Valida el contenido

        Returns:
            Tupla (is_valid, error_message)
        """
        content = self.get_content()

        if not content:
            return False, "El campo está vacío"

        # En modo especial, validar que label no esté vacío
        if self.item_mode == "especial":
            label = self.get_label()
            if not label:
                return False, "El label no puede estar vacío en items especiales"

        # Validar contenido según tipo
        item_type = self.get_data_type()
        return ItemValidationService.validate_item(content, item_type)

    # === UTILIDADES ===

    def focus_content(self):
        """Pone foco en el campo de contenido"""
        self.content_input.setFocus()

    def clear(self):
        """Limpia todos los campos"""
        self.content_input.clear()
        if self.label_input:
            self.label_input.clear()
        if self.sensitive_checkbox:
            self.sensitive_checkbox.setChecked(False)

    def __repr__(self) -> str:
        """Representación del widget"""
        mode_text = "SPECIAL" if self.item_mode == "especial" else "SIMPLE"
        content_preview = self.get_content()[:30] + '...' if len(self.get_content()) > 30 else self.get_content()
        return f"ItemFieldWidget[{mode_text}]({self.get_data_type()}): {content_preview}"
