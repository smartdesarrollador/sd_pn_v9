"""
ComponentManagerDialog - Ventana para gestionar tipos de componentes visuales
"""
import json
import logging
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QTextEdit, QMessageBox,
    QWidget, QSplitter, QGroupBox, QLineEdit
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.component_manager import ComponentManager
from models.component_type import ComponentType

logger = logging.getLogger(__name__)


class ComponentManagerDialog(QDialog):
    """Dialog for managing visual component types"""

    # Signals
    component_types_changed = pyqtSignal()  # Emitted when components are modified

    def __init__(self, component_manager: ComponentManager, parent=None):
        """
        Initialize ComponentManagerDialog

        Args:
            component_manager: ComponentManager instance
            parent: Parent widget
        """
        super().__init__(parent)
        self.component_manager = component_manager
        self.current_component_type = None
        self.init_ui()
        self.load_component_types()

    def init_ui(self):
        """Initialize user interface"""
        self.setWindowTitle("Gestor de Componentes")
        self.setMinimumSize(900, 600)

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # Title
        title_label = QLabel("Gestor de Componentes Visuales")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 16pt;
                font-weight: bold;
                color: #007acc;
                padding: 10px;
            }
        """)
        main_layout.addWidget(title_label)

        # Splitter for two-panel layout
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # ===== Left Panel: Component Types List =====
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)

        # Left panel title
        list_title = QLabel("Tipos de Componentes")
        list_title.setStyleSheet("""
            QLabel {
                font-size: 11pt;
                font-weight: bold;
                color: #ffffff;
                background-color: #3d3d3d;
                padding: 8px;
                border-radius: 4px;
            }
        """)
        left_layout.addWidget(list_title)

        # Component types list
        self.components_list = QListWidget()
        self.components_list.setStyleSheet("""
            QListWidget {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                padding: 5px;
                font-size: 10pt;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #3d3d3d;
            }
            QListWidget::item:selected {
                background-color: #007acc;
                color: #ffffff;
            }
            QListWidget::item:hover {
                background-color: #3d3d3d;
            }
        """)
        self.components_list.currentItemChanged.connect(self.on_component_selected)
        left_layout.addWidget(self.components_list)

        # Buttons below list
        list_buttons_layout = QHBoxLayout()

        self.new_btn = QPushButton("Nuevo Tipo")
        self.new_btn.setStyleSheet(self._get_button_style("#00ff88"))
        self.new_btn.clicked.connect(self.on_new_component)
        list_buttons_layout.addWidget(self.new_btn)

        self.delete_btn = QPushButton("Eliminar")
        self.delete_btn.setStyleSheet(self._get_button_style("#e4475b"))
        self.delete_btn.setEnabled(False)
        self.delete_btn.clicked.connect(self.on_delete_component)
        list_buttons_layout.addWidget(self.delete_btn)

        left_layout.addLayout(list_buttons_layout)

        # ===== Right Panel: Component Details =====
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)

        # Right panel title
        details_title = QLabel("Configuración Detallada")
        details_title.setStyleSheet("""
            QLabel {
                font-size: 11pt;
                font-weight: bold;
                color: #ffffff;
                background-color: #3d3d3d;
                padding: 8px;
                border-radius: 4px;
            }
        """)
        right_layout.addWidget(details_title)

        # Details container
        details_container = QWidget()
        details_container.setStyleSheet("""
            QWidget {
                background-color: #2d2d2d;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
            }
        """)
        details_layout = QVBoxLayout(details_container)
        details_layout.setSpacing(15)
        details_layout.setContentsMargins(15, 15, 15, 15)

        # Name field
        name_group = QGroupBox("Nombre del Componente")
        name_group.setStyleSheet(self._get_groupbox_style())
        name_layout = QVBoxLayout(name_group)

        self.name_input = QLineEdit()
        self.name_input.setStyleSheet(self._get_input_style())
        self.name_input.setPlaceholderText("ej: separador, nota, alerta...")
        self.name_input.textChanged.connect(self.on_field_changed)
        name_layout.addWidget(self.name_input)

        details_layout.addWidget(name_group)

        # Description field
        desc_group = QGroupBox("Descripción")
        desc_group.setStyleSheet(self._get_groupbox_style())
        desc_layout = QVBoxLayout(desc_group)

        self.description_input = QLineEdit()
        self.description_input.setStyleSheet(self._get_input_style())
        self.description_input.setPlaceholderText("Descripción breve del componente...")
        self.description_input.textChanged.connect(self.on_field_changed)
        desc_layout.addWidget(self.description_input)

        details_layout.addWidget(desc_group)

        # Default config field (JSON editor)
        config_group = QGroupBox("Configuración por Defecto (JSON)")
        config_group.setStyleSheet(self._get_groupbox_style())
        config_layout = QVBoxLayout(config_group)

        self.config_editor = QTextEdit()
        self.config_editor.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                padding: 8px;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 10pt;
            }
        """)
        self.config_editor.setPlaceholderText('{\n  "key": "value"\n}')
        self.config_editor.textChanged.connect(self.on_field_changed)
        config_layout.addWidget(self.config_editor)

        # JSON validation label
        self.json_validation_label = QLabel("")
        self.json_validation_label.setStyleSheet("""
            QLabel {
                font-size: 9pt;
                padding: 5px;
            }
        """)
        config_layout.addWidget(self.json_validation_label)

        details_layout.addWidget(config_group)

        # Action buttons
        action_buttons_layout = QHBoxLayout()
        action_buttons_layout.addStretch()

        self.save_btn = QPushButton("Guardar Cambios")
        self.save_btn.setStyleSheet(self._get_button_style("#007acc"))
        self.save_btn.setEnabled(False)
        self.save_btn.clicked.connect(self.on_save_component)
        action_buttons_layout.addWidget(self.save_btn)

        self.cancel_btn = QPushButton("Cancelar")
        self.cancel_btn.setStyleSheet(self._get_button_style("#888888"))
        self.cancel_btn.clicked.connect(self.on_cancel_edit)
        action_buttons_layout.addWidget(self.cancel_btn)

        details_layout.addLayout(action_buttons_layout)

        right_layout.addWidget(details_container)

        # Add panels to splitter
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)

        main_layout.addWidget(splitter)

        # Bottom buttons
        bottom_buttons_layout = QHBoxLayout()
        bottom_buttons_layout.addStretch()

        close_btn = QPushButton("Cerrar")
        close_btn.setStyleSheet(self._get_button_style("#3d3d3d"))
        close_btn.clicked.connect(self.accept)
        bottom_buttons_layout.addWidget(close_btn)

        main_layout.addLayout(bottom_buttons_layout)

        # Apply dark theme
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e1e;
                color: #ffffff;
            }
        """)

    def _get_button_style(self, color: str) -> str:
        """Get button stylesheet with specified color"""
        return f"""
            QPushButton {{
                background-color: {color};
                color: #ffffff;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 10pt;
                font-weight: bold;
                min-width: 100px;
            }}
            QPushButton:hover {{
                background-color: {color}dd;
            }}
            QPushButton:pressed {{
                background-color: {color}aa;
            }}
            QPushButton:disabled {{
                background-color: #3d3d3d;
                color: #888888;
            }}
        """

    def _get_groupbox_style(self) -> str:
        """Get groupbox stylesheet"""
        return """
            QGroupBox {
                color: #ffffff;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                margin-top: 10px;
                font-weight: bold;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 5px;
                color: #007acc;
            }
        """

    def _get_input_style(self) -> str:
        """Get input field stylesheet"""
        return """
            QLineEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                padding: 8px;
                font-size: 10pt;
            }
            QLineEdit:focus {
                border-color: #007acc;
            }
        """

    def load_component_types(self):
        """Load component types into list"""
        self.components_list.clear()

        try:
            component_types = self.component_manager.get_all_component_types(active_only=False)

            for comp_type in component_types:
                icon = self.component_manager.get_component_icon(comp_type.name)
                status = "" if comp_type.is_active else " [INACTIVO]"
                item_text = f"{icon} {comp_type.name}{status}"

                item = QListWidgetItem(item_text)
                item.setData(Qt.ItemDataRole.UserRole, comp_type)
                self.components_list.addItem(item)

        except Exception as e:
            logger.error(f"Error loading component types: {e}")
            QMessageBox.critical(self, "Error", f"Error al cargar componentes:\n{e}")

    def on_component_selected(self, current: QListWidgetItem, previous: QListWidgetItem):
        """Handle component selection"""
        if not current:
            self.current_component_type = None
            self.clear_details()
            self.delete_btn.setEnabled(False)
            return

        component_type = current.data(Qt.ItemDataRole.UserRole)
        self.current_component_type = component_type
        self.delete_btn.setEnabled(True)

        # Load component details
        self.name_input.setText(component_type.name)
        self.description_input.setText(component_type.description)

        # Format JSON config
        try:
            config_json = json.dumps(component_type.default_config, indent=2, ensure_ascii=False)
            self.config_editor.setText(config_json)
            self.validate_json()
        except Exception as e:
            logger.error(f"Error formatting config JSON: {e}")
            self.config_editor.setText(str(component_type.default_config))

        # Disable save button initially
        self.save_btn.setEnabled(False)

    def clear_details(self):
        """Clear detail fields"""
        self.name_input.clear()
        self.description_input.clear()
        self.config_editor.clear()
        self.json_validation_label.clear()
        self.save_btn.setEnabled(False)

    def on_field_changed(self):
        """Handle field changes"""
        self.save_btn.setEnabled(True)
        if self.sender() == self.config_editor:
            self.validate_json()

    def validate_json(self):
        """Validate JSON in config editor"""
        try:
            json_text = self.config_editor.toPlainText().strip()
            if not json_text:
                self.json_validation_label.setText("")
                return True

            json.loads(json_text)
            self.json_validation_label.setText("✓ JSON válido")
            self.json_validation_label.setStyleSheet("QLabel { color: #00ff88; }")
            return True

        except json.JSONDecodeError as e:
            self.json_validation_label.setText(f"✗ Error JSON: {e.msg} (línea {e.lineno})")
            self.json_validation_label.setStyleSheet("QLabel { color: #e4475b; }")
            return False

    def on_new_component(self):
        """Handle new component creation"""
        self.components_list.clearSelection()
        self.current_component_type = None
        self.clear_details()
        self.name_input.setFocus()
        self.save_btn.setEnabled(True)

    def on_save_component(self):
        """Handle save component"""
        try:
            # Validate fields
            name = self.name_input.text().strip()
            description = self.description_input.text().strip()
            config_text = self.config_editor.toPlainText().strip()

            if not name:
                QMessageBox.warning(self, "Validación", "El nombre es requerido")
                return

            if not description:
                QMessageBox.warning(self, "Validación", "La descripción es requerida")
                return

            if not config_text:
                QMessageBox.warning(self, "Validación", "La configuración es requerida")
                return

            # Validate JSON
            if not self.validate_json():
                QMessageBox.warning(self, "Validación", "El JSON de configuración no es válido")
                return

            config_dict = json.loads(config_text)

            # Create or update component type
            if self.current_component_type:
                # Update existing
                success = self.component_manager.update_component_type(
                    component_type_id=self.current_component_type.id,
                    name=name,
                    description=description,
                    default_config=config_dict
                )

                if success:
                    QMessageBox.information(self, "Éxito", "Componente actualizado exitosamente")
                    self.component_types_changed.emit()
                    self.load_component_types()
                else:
                    QMessageBox.critical(self, "Error", "Error al actualizar el componente")

            else:
                # Create new
                component_id = self.component_manager.add_component_type(
                    name=name,
                    description=description,
                    default_config=config_dict
                )

                if component_id:
                    QMessageBox.information(self, "Éxito", "Componente creado exitosamente")
                    self.component_types_changed.emit()
                    self.load_component_types()
                    self.clear_details()
                else:
                    QMessageBox.critical(self, "Error", "Error al crear el componente")

            self.save_btn.setEnabled(False)

        except Exception as e:
            logger.error(f"Error saving component: {e}")
            QMessageBox.critical(self, "Error", f"Error al guardar:\n{e}")

    def on_cancel_edit(self):
        """Handle cancel edit"""
        if self.current_component_type:
            # Reload current component
            current_item = self.components_list.currentItem()
            if current_item:
                self.on_component_selected(current_item, None)
        else:
            self.clear_details()

    def on_delete_component(self):
        """Handle delete component"""
        if not self.current_component_type:
            return

        reply = QMessageBox.question(
            self,
            "Confirmar Eliminación",
            f"¿Estás seguro de eliminar el componente '{self.current_component_type.name}'?\n\n"
            "Esta acción no se puede deshacer.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                success = self.component_manager.delete_component_type(
                    self.current_component_type.id
                )

                if success:
                    QMessageBox.information(self, "Éxito", "Componente eliminado exitosamente")
                    self.component_types_changed.emit()
                    self.load_component_types()
                    self.clear_details()
                    self.current_component_type = None
                else:
                    QMessageBox.critical(self, "Error", "Error al eliminar el componente")

            except Exception as e:
                logger.error(f"Error deleting component: {e}")
                QMessageBox.critical(self, "Error", f"Error al eliminar:\n{e}")
