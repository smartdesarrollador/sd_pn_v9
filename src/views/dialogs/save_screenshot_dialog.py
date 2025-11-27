# -*- coding: utf-8 -*-
"""
Save Screenshot Dialog

Diálogo para guardar screenshot como item inmediatamente después de capturar
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QTextEdit, QCheckBox, QGroupBox,
    QFormLayout, QWidget
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QFont
from typing import Optional


class SaveScreenshotDialog(QDialog):
    """
    Diálogo para guardar screenshot como item

    Permite configurar:
    - Nombre del item
    - Categoría (Screenshots por defecto)
    - Descripción
    - Tags
    - Si es favorito
    """

    # Señal emitida cuando se confirma guardar
    item_saved = pyqtSignal(dict)  # item_data

    def __init__(self,
                 screenshot_path: str,
                 categories: list,
                 default_category_id: Optional[int] = None,
                 parent=None):
        """
        Inicializar diálogo

        Args:
            screenshot_path: Ruta al archivo de screenshot guardado
            categories: Lista de categorías disponibles
            default_category_id: ID de categoría por defecto (Screenshots)
            parent: Widget padre
        """
        super().__init__(parent)

        self.screenshot_path = screenshot_path
        self.categories = categories
        self.default_category_id = default_category_id
        self.item_data = None

        self.init_ui()
        self.load_default_values()

    def init_ui(self):
        """Inicializar interfaz de usuario"""
        self.setWindowTitle("Guardar Captura como Item")
        self.setModal(True)
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)

        # Aplicar estilos
        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
            }
            QLabel {
                color: #cccccc;
                font-size: 10pt;
            }
            QLineEdit, QTextEdit {
                background-color: #1e1e1e;
                color: #cccccc;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                padding: 6px;
                font-size: 10pt;
            }
            QLineEdit:focus, QTextEdit:focus {
                border: 1px solid #007acc;
            }
            QComboBox {
                background-color: #1e1e1e;
                color: #cccccc;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                padding: 6px;
                font-size: 10pt;
            }
            QComboBox:focus {
                border: 1px solid #007acc;
            }
            QComboBox::drop-down {
                border: none;
                padding-right: 10px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 6px solid #cccccc;
                margin-right: 5px;
            }
            QComboBox QAbstractItemView {
                background-color: #2d2d2d;
                color: #cccccc;
                selection-background-color: #007acc;
                border: 1px solid #3d3d3d;
            }
            QCheckBox {
                color: #cccccc;
                font-size: 10pt;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 1px solid #3d3d3d;
                border-radius: 3px;
                background-color: #1e1e1e;
            }
            QCheckBox::indicator:checked {
                background-color: #007acc;
                border: 1px solid #007acc;
            }
            QGroupBox {
                color: #cccccc;
                font-weight: bold;
                font-size: 11pt;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QPushButton {
                background-color: #007acc;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 10pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #005a9e;
            }
            QPushButton:pressed {
                background-color: #004578;
            }
            QPushButton#cancelButton {
                background-color: #3d3d3d;
            }
            QPushButton#cancelButton:hover {
                background-color: #4d4d4d;
            }
        """)

        # Layout principal
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Título
        title_label = QLabel("📸 Nueva Captura de Pantalla")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # Ruta del archivo (info)
        info_label = QLabel(f"Archivo: {self.screenshot_path}")
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #888888; font-size: 9pt;")
        layout.addWidget(info_label)

        # GroupBox: Datos del Item
        item_group = QGroupBox("Información del Item")
        item_layout = QFormLayout()
        item_layout.setSpacing(10)

        # Campo: Nombre del item
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Ej: Captura de error en login")
        self.name_input.setFocus()
        item_layout.addRow("Nombre:", self.name_input)

        # Campo: Categoría
        self.category_combo = QComboBox()
        self.category_combo.addItem("-- Seleccionar Categoría --", None)
        for category in self.categories:
            cat_id = category.get('id') or category.get('category_id')
            cat_name = category.get('name', 'Sin nombre')
            cat_icon = category.get('icon', '📁')
            self.category_combo.addItem(f"{cat_icon} {cat_name}", cat_id)
        item_layout.addRow("Categoría:", self.category_combo)

        # Campo: Descripción
        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("Descripción opcional del screenshot...")
        self.description_input.setMaximumHeight(80)
        item_layout.addRow("Descripción:", self.description_input)

        # Campo: Tags
        self.tags_input = QLineEdit()
        self.tags_input.setPlaceholderText("Separados por comas: bug, login, error")
        item_layout.addRow("Tags:", self.tags_input)

        item_group.setLayout(item_layout)
        layout.addWidget(item_group)

        # Checkbox: Marcar como favorito
        self.favorite_checkbox = QCheckBox("Marcar como favorito")
        layout.addWidget(self.favorite_checkbox)

        # Spacer
        layout.addStretch()

        # Botones
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)

        # Botón Cancelar
        self.cancel_button = QPushButton("Cancelar")
        self.cancel_button.setObjectName("cancelButton")
        self.cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(self.cancel_button)

        buttons_layout.addStretch()

        # Botón No guardar
        self.skip_button = QPushButton("No Guardar Item")
        self.skip_button.setObjectName("cancelButton")
        self.skip_button.setToolTip("El screenshot ya está guardado en disco, solo omitir crear item")
        self.skip_button.clicked.connect(self.skip_item)
        buttons_layout.addWidget(self.skip_button)

        # Botón Guardar
        self.save_button = QPushButton("Guardar Item")
        self.save_button.clicked.connect(self.save_item)
        self.save_button.setDefault(True)
        buttons_layout.addWidget(self.save_button)

        layout.addLayout(buttons_layout)

    def load_default_values(self):
        """Cargar valores por defecto"""
        # Generar nombre por defecto
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.name_input.setText(f"Captura {timestamp}")

        # Seleccionar texto para que el usuario pueda escribir directamente
        self.name_input.selectAll()

        # Seleccionar categoría Screenshots por defecto
        if self.default_category_id:
            for i in range(self.category_combo.count()):
                if self.category_combo.itemData(i) == self.default_category_id:
                    self.category_combo.setCurrentIndex(i)
                    break

        # Tags por defecto
        self.tags_input.setText("screenshot, captura")

    def save_item(self):
        """Guardar item con datos ingresados"""
        # Validar nombre
        name = self.name_input.text().strip()
        if not name:
            self.name_input.setFocus()
            self.name_input.setStyleSheet("""
                QLineEdit {
                    border: 2px solid #ff0000;
                    background-color: #1e1e1e;
                    color: #cccccc;
                }
            """)
            return

        # Validar categoría
        category_id = self.category_combo.currentData()
        if not category_id:
            self.category_combo.setStyleSheet("""
                QComboBox {
                    border: 2px solid #ff0000;
                }
            """)
            return

        # Obtener datos
        description = self.description_input.toPlainText().strip()
        tags_text = self.tags_input.text().strip()
        tags = [tag.strip() for tag in tags_text.split(',') if tag.strip()]
        is_favorite = self.favorite_checkbox.isChecked()

        # Construir datos del item
        self.item_data = {
            'label': name,
            'content': self.screenshot_path,
            'item_type': 'PATH',
            'category_id': category_id,
            'description': description if description else None,
            'tags': tags,
            'is_favorite': is_favorite
        }

        # Emitir señal y cerrar
        self.item_saved.emit(self.item_data)
        self.accept()

    def skip_item(self):
        """Omitir guardado de item (screenshot ya guardado en disco)"""
        self.item_data = None
        self.accept()

    def get_item_data(self) -> Optional[dict]:
        """
        Obtener datos del item

        Returns:
            dict con datos del item o None si se omitió
        """
        return self.item_data
