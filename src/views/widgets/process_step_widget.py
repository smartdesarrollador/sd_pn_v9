"""
ProcessStepWidget - Widget para visualizar y editar un step en el constructor de procesos

Muestra:
- Orden del step
- Label del item
- Tipo de item
- Botones de accion (editar, eliminar, mover)
"""

from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QLabel,
                             QPushButton, QFrame)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QCursor
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from models.process import ProcessStep


class ProcessStepWidget(QWidget):
    """Widget para un step individual en el constructor de procesos"""

    # Signals
    step_edited = pyqtSignal(object)  # ProcessStep
    step_deleted = pyqtSignal(object)  # ProcessStep
    step_moved_up = pyqtSignal(object)  # ProcessStep
    step_moved_down = pyqtSignal(object)  # ProcessStep

    def __init__(self, step: ProcessStep, is_first: bool = False, is_last: bool = False, parent=None):
        """
        Initialize ProcessStepWidget

        Args:
            step: ProcessStep object
            is_first: Whether this is the first step
            is_last: Whether this is the last step
            parent: Parent widget
        """
        super().__init__(parent)
        self.step = step
        self.is_first = is_first
        self.is_last = is_last
        self.init_ui()

    def init_ui(self):
        """Initialize UI"""
        # Check if this step is a component
        if hasattr(self.step, 'is_component') and self.step.is_component:
            self._render_component()
        else:
            self._render_regular_step()

    def _render_regular_step(self):
        """Render a regular (non-component) step"""
        # Main layout
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(10)

        # Container frame for better visual separation
        container = QFrame()
        container.setFrameShape(QFrame.Shape.StyledPanel)
        container.setStyleSheet("""
            QFrame {
                background-color: #2d2d2d;
                border: 1px solid #3d3d3d;
                border-radius: 6px;
                padding: 5px;
            }
            QFrame:hover {
                background-color: #3d3d3d;
                border-color: #007acc;
            }
        """)

        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(8, 8, 8, 8)
        container_layout.setSpacing(10)

        # Order number
        self.order_label = QLabel(f"{self.step.step_order}.")
        self.order_label.setStyleSheet("""
            QLabel {
                color: #007acc;
                font-size: 14pt;
                font-weight: bold;
                min-width: 30px;
            }
        """)
        container_layout.addWidget(self.order_label)

        # Content area
        content_layout = QVBoxLayout()
        content_layout.setSpacing(3)

        # Step label
        label_text = self.step.get_display_label()
        self.label_widget = QLabel(label_text)
        self.label_widget.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 10pt;
                font-weight: bold;
            }
        """)
        content_layout.addWidget(self.label_widget)

        # Item info (type + content preview)
        info_text = f"{self.step.item_type}"
        if self.step.item_content:
            preview = self.step.item_content[:40]
            if len(self.step.item_content) > 40:
                preview += "..."
            info_text += f" | {preview}"

        self.info_label = QLabel(info_text)
        self.info_label.setStyleSheet("""
            QLabel {
                color: #888888;
                font-size: 8pt;
            }
        """)
        content_layout.addWidget(self.info_label)

        container_layout.addLayout(content_layout, stretch=1)

        # Badges (optional, confirmation, etc.)
        badges_layout = QHBoxLayout()
        badges_layout.setSpacing(5)

        if self.step.is_optional:
            optional_badge = QLabel("OPCIONAL")
            optional_badge.setStyleSheet("""
                QLabel {
                    background-color: #ff6b00;
                    color: white;
                    padding: 2px 6px;
                    border-radius: 3px;
                    font-size: 7pt;
                    font-weight: bold;
                }
            """)
            badges_layout.addWidget(optional_badge)

        if self.step.wait_for_confirmation:
            confirm_badge = QLabel("ESPERAR")
            confirm_badge.setStyleSheet("""
                QLabel {
                    background-color: #ffa500;
                    color: white;
                    padding: 2px 6px;
                    border-radius: 3px;
                    font-size: 7pt;
                    font-weight: bold;
                }
            """)
            badges_layout.addWidget(confirm_badge)

        if not self.step.is_enabled:
            disabled_badge = QLabel("DESHABILITADO")
            disabled_badge.setStyleSheet("""
                QLabel {
                    background-color: #888888;
                    color: white;
                    padding: 2px 6px;
                    border-radius: 3px;
                    font-size: 7pt;
                    font-weight: bold;
                }
            """)
            badges_layout.addWidget(disabled_badge)

        container_layout.addLayout(badges_layout)

        # Action buttons
        buttons_layout = QVBoxLayout()
        buttons_layout.setSpacing(3)

        # Move up button
        self.up_button = QPushButton("↑")
        self.up_button.setFixedSize(24, 24)
        self.up_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.up_button.setStyleSheet("""
            QPushButton {
                background-color: #3d3d3d;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 4px;
                font-weight: bold;
                font-size: 10pt;
            }
            QPushButton:hover {
                background-color: #007acc;
                border-color: #007acc;
            }
            QPushButton:disabled {
                background-color: #2d2d2d;
                color: #555555;
                border-color: #333333;
            }
        """)
        self.up_button.setEnabled(not self.is_first)
        self.up_button.setToolTip("Mover arriba")
        self.up_button.clicked.connect(self.on_move_up)
        buttons_layout.addWidget(self.up_button)

        # Move down button
        self.down_button = QPushButton("↓")
        self.down_button.setFixedSize(24, 24)
        self.down_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.down_button.setStyleSheet("""
            QPushButton {
                background-color: #3d3d3d;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 4px;
                font-weight: bold;
                font-size: 10pt;
            }
            QPushButton:hover {
                background-color: #007acc;
                border-color: #007acc;
            }
            QPushButton:disabled {
                background-color: #2d2d2d;
                color: #555555;
                border-color: #333333;
            }
        """)
        self.down_button.setEnabled(not self.is_last)
        self.down_button.setToolTip("Mover abajo")
        self.down_button.clicked.connect(self.on_move_down)
        buttons_layout.addWidget(self.down_button)

        container_layout.addLayout(buttons_layout)

        # Edit and Delete buttons
        action_buttons_layout = QVBoxLayout()
        action_buttons_layout.setSpacing(3)

        # Edit button
        edit_button = QPushButton("✏")
        edit_button.setFixedSize(24, 24)
        edit_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        edit_button.setStyleSheet("""
            QPushButton {
                background-color: #3d3d3d;
                color: #00ff88;
                border: 1px solid #555555;
                border-radius: 4px;
                font-size: 10pt;
            }
            QPushButton:hover {
                background-color: #00ff88;
                color: #000000;
                border-color: #00ff88;
            }
        """)
        edit_button.setToolTip("Editar configuracion")
        edit_button.clicked.connect(self.on_edit)
        action_buttons_layout.addWidget(edit_button)

        # Delete button
        delete_button = QPushButton("✕")
        delete_button.setFixedSize(24, 24)
        delete_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        delete_button.setStyleSheet("""
            QPushButton {
                background-color: #3d3d3d;
                color: #e4475b;
                border: 1px solid #555555;
                border-radius: 4px;
                font-size: 12pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e4475b;
                color: #ffffff;
                border-color: #e4475b;
            }
        """)
        delete_button.setToolTip("Eliminar step")
        delete_button.clicked.connect(self.on_delete)
        action_buttons_layout.addWidget(delete_button)

        container_layout.addLayout(action_buttons_layout)

        main_layout.addWidget(container)

    def update_order(self, new_order: int, is_first: bool, is_last: bool):
        """
        Update step order and button states

        Args:
            new_order: New order number
            is_first: Whether this is now the first step
            is_last: Whether this is now the last step
        """
        self.step.step_order = new_order
        self.is_first = is_first
        self.is_last = is_last

        # Update label
        self.order_label.setText(f"{new_order}.")

        # Update button states
        self.up_button.setEnabled(not is_first)
        self.down_button.setEnabled(not is_last)

    def on_edit(self):
        """Handle edit button click"""
        self.step_edited.emit(self.step)

    def on_delete(self):
        """Handle delete button click"""
        self.step_deleted.emit(self.step)

    def on_move_up(self):
        """Handle move up button click"""
        if not self.is_first:
            self.step_moved_up.emit(self.step)

    def on_move_down(self):
        """Handle move down button click"""
        if not self.is_last:
            self.step_moved_down.emit(self.step)

    def get_step(self) -> ProcessStep:
        """Get the ProcessStep object"""
        return self.step

    def update_step_data(self, step: ProcessStep):
        """
        Update widget with new step data

        Args:
            step: Updated ProcessStep object
        """
        self.step = step

        # Update labels
        self.label_widget.setText(step.get_display_label())

        info_text = f"{step.item_type}"
        if step.item_content:
            preview = step.item_content[:40]
            if len(step.item_content) > 40:
                preview += "..."
            info_text += f" | {preview}"
        self.info_label.setText(info_text)

        # Rebuild the entire widget to reflect changes in badges
        # This is simpler than trying to update badges dynamically
        # Store current state
        current_order = self.step.step_order
        current_is_first = self.is_first
        current_is_last = self.is_last

        # Clear layout
        while self.layout().count():
            item = self.layout().takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Reinitialize UI with updated data
        self.init_ui()

        # Restore order state
        self.update_order(current_order, current_is_first, current_is_last)

    # ==================== Component Rendering ====================

    def _render_component(self):
        """Render a component step in the constructor (simplified view)"""
        component_type = getattr(self.step, 'name_component', None)

        # Render as a regular step but with component indicator
        # Main container
        container_layout = QHBoxLayout(self)
        container_layout.setContentsMargins(5, 5, 5, 5)
        container_layout.setSpacing(10)

        # Order number
        self.order_label = QLabel(f"{self.step.step_order}.")
        self.order_label.setStyleSheet("""
            QLabel {
                color: #007acc;
                font-size: 14pt;
                font-weight: bold;
                min-width: 30px;
            }
        """)
        container_layout.addWidget(self.order_label)

        # Content area
        content_layout = QVBoxLayout()
        content_layout.setSpacing(5)

        # Component indicator with icon
        component_icons = {
            'separador': '━',
            'nota': '💡',
            'alerta': '⚠',
            'grupo': '📁'
        }
        icon = component_icons.get(component_type, '🧩')

        component_label = QLabel(f"{icon} COMPONENTE: {component_type or 'Desconocido'}")
        component_label.setStyleSheet("""
            QLabel {
                color: #9370DB;
                font-size: 11pt;
                font-weight: bold;
                padding: 8px;
                background-color: #2d2d3d;
                border-left: 4px solid #9370DB;
                border-radius: 4px;
            }
        """)
        content_layout.addWidget(component_label)

        # Description
        description = self.step.item_label or f"Componente visual: {component_type}"
        desc_label = QLabel(description)
        desc_label.setStyleSheet("""
            QLabel {
                color: #b0b0b0;
                font-size: 9pt;
                padding-left: 12px;
            }
        """)
        desc_label.setWordWrap(True)
        content_layout.addWidget(desc_label)

        container_layout.addLayout(content_layout, stretch=1)

        # Control buttons (move up/down, delete)
        # Action buttons for ordering
        buttons_layout = QVBoxLayout()
        buttons_layout.setSpacing(3)

        # Move up button
        self.up_button = QPushButton("↑")
        self.up_button.setFixedSize(24, 24)
        self.up_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.up_button.setStyleSheet("""
            QPushButton {
                background-color: #3d3d3d;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 4px;
                font-weight: bold;
                font-size: 10pt;
            }
            QPushButton:hover {
                background-color: #9370DB;
                border-color: #9370DB;
            }
            QPushButton:disabled {
                background-color: #2d2d2d;
                color: #555555;
                border-color: #333333;
            }
        """)
        self.up_button.setEnabled(not self.is_first)
        self.up_button.setToolTip("Mover arriba")
        self.up_button.clicked.connect(self.on_move_up)
        buttons_layout.addWidget(self.up_button)

        # Move down button
        self.down_button = QPushButton("↓")
        self.down_button.setFixedSize(24, 24)
        self.down_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.down_button.setStyleSheet("""
            QPushButton {
                background-color: #3d3d3d;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 4px;
                font-weight: bold;
                font-size: 10pt;
            }
            QPushButton:hover {
                background-color: #9370DB;
                border-color: #9370DB;
            }
            QPushButton:disabled {
                background-color: #2d2d2d;
                color: #555555;
                border-color: #333333;
            }
        """)
        self.down_button.setEnabled(not self.is_last)
        self.down_button.setToolTip("Mover abajo")
        self.down_button.clicked.connect(self.on_move_down)
        buttons_layout.addWidget(self.down_button)

        container_layout.addLayout(buttons_layout)

        # Delete button
        delete_buttons_layout = QVBoxLayout()
        delete_buttons_layout.setSpacing(3)

        delete_button = QPushButton("✕")
        delete_button.setFixedSize(24, 24)
        delete_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        delete_button.setStyleSheet("""
            QPushButton {
                background-color: #3d3d3d;
                color: #e4475b;
                border: 1px solid #555555;
                border-radius: 4px;
                font-size: 12pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e4475b;
                color: #ffffff;
                border-color: #e4475b;
            }
        """)
        delete_button.setToolTip("Eliminar componente")
        delete_button.clicked.connect(self.on_delete)
        delete_buttons_layout.addWidget(delete_button)

        container_layout.addLayout(delete_buttons_layout)

    def _render_separator(self, config):
        """Render a separator component"""
        # Main layout
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(5, 10, 5, 10)

        # Get configuration
        color = config.get('color', '#ff6b6b')
        thickness = config.get('thickness', 2)
        style = config.get('style', 'solid')

        # Create separator line
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFixedHeight(thickness)

        # Map style to Qt style
        border_style = 'solid'
        if style == 'dashed':
            border_style = 'dashed'
        elif style == 'dotted':
            border_style = 'dotted'
        elif style == 'double':
            thickness = max(4, thickness)  # Double needs more space

        separator.setStyleSheet(f"""
            QFrame {{
                background-color: {color};
                border: none;
                border-top: {thickness}px {border_style} {color};
            }}
        """)

        main_layout.addWidget(separator, stretch=1)

        # Add delete button on the right
        delete_button = QPushButton("✕")
        delete_button.setFixedSize(20, 20)
        delete_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        delete_button.setStyleSheet("""
            QPushButton {
                background-color: #3d3d3d;
                color: #e4475b;
                border: 1px solid #555555;
                border-radius: 4px;
                font-size: 10pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e4475b;
                color: #ffffff;
            }
        """)
        delete_button.setToolTip("Eliminar separador")
        delete_button.clicked.connect(self.on_delete)
        main_layout.addWidget(delete_button)

    def _render_note(self, config):
        """Render a note component"""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)

        # Get configuration
        background = config.get('background', '#fff3cd')
        icon = config.get('icon', '💡')
        dismissible = config.get('dismissible', False)

        # Create note container
        note_widget = QFrame()
        note_widget.setStyleSheet(f"""
            QFrame {{
                background-color: {background};
                border-left: 4px solid #f39c12;
                border-radius: 4px;
                padding: 10px;
            }}
        """)

        note_layout = QHBoxLayout(note_widget)

        # Icon
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 20pt;")
        note_layout.addWidget(icon_label)

        # Content
        content_label = QLabel(self.step.item_label or "Nota informativa")
        content_label.setStyleSheet("color: #333333; font-size: 10pt;")
        content_label.setWordWrap(True)
        note_layout.addWidget(content_label, stretch=1)

        # Delete button
        delete_btn = QPushButton("✕")
        delete_btn.setFixedSize(20, 20)
        delete_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #888888;
                border: none;
                font-size: 14pt;
                font-weight: bold;
            }
            QPushButton:hover {
                color: #e4475b;
            }
        """)
        delete_btn.setToolTip("Eliminar nota")
        delete_btn.clicked.connect(self.on_delete)
        note_layout.addWidget(delete_btn)

        main_layout.addWidget(note_widget)

    def _render_alert(self, config):
        """Render an alert component"""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)

        # Get configuration
        alert_type = config.get('type', 'warning')
        title = config.get('title', 'Atención')
        dismissible = config.get('dismissible', True)

        # Colors by type
        colors = {
            'info': '#3498db',
            'warning': '#f39c12',
            'error': '#e74c3c',
            'success': '#2ecc71'
        }
        color = colors.get(alert_type, '#f39c12')

        # Icons by type
        icons = {
            'info': 'ℹ️',
            'warning': '⚠️',
            'error': '❌',
            'success': '✅'
        }
        icon = icons.get(alert_type, '⚠️')

        # Create alert container
        alert_widget = QFrame()
        alert_widget.setStyleSheet(f"""
            QFrame {{
                background-color: {color}22;
                border-left: 4px solid {color};
                border-radius: 4px;
                padding: 10px;
            }}
        """)

        alert_layout = QVBoxLayout(alert_widget)

        # Header with icon and title
        header_layout = QHBoxLayout()

        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 18pt;")
        header_layout.addWidget(icon_label)

        title_label = QLabel(title)
        title_label.setStyleSheet(f"color: {color}; font-size: 11pt; font-weight: bold;")
        header_layout.addWidget(title_label, stretch=1)

        # Delete button
        delete_btn = QPushButton("✕")
        delete_btn.setFixedSize(20, 20)
        delete_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #888888;
                border: none;
                font-size: 14pt;
                font-weight: bold;
            }
            QPushButton:hover {
                color: #e4475b;
            }
        """)
        delete_btn.setToolTip("Eliminar alerta")
        delete_btn.clicked.connect(self.on_delete)
        header_layout.addWidget(delete_btn)

        alert_layout.addLayout(header_layout)

        # Content
        if self.step.item_label:
            content_label = QLabel(self.step.item_label)
            content_label.setStyleSheet("color: #333333; font-size: 9pt; padding-left: 30px;")
            content_label.setWordWrap(True)
            alert_layout.addWidget(content_label)

        main_layout.addWidget(alert_widget)

    def _render_group(self, config):
        """Render a group component"""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)

        # Get configuration
        color = config.get('color', '#007acc')
        collapsible = config.get('collapsible', True)
        expanded = config.get('expanded', True)

        # Create group container
        group_widget = QFrame()
        group_widget.setStyleSheet(f"""
            QFrame {{
                background-color: #2d2d2d;
                border: 2px solid {color};
                border-radius: 6px;
            }}
        """)

        group_layout = QVBoxLayout(group_widget)
        group_layout.setContentsMargins(0, 0, 0, 0)
        group_layout.setSpacing(0)

        # Header
        header = QPushButton(f"📁 {self.step.item_label or 'Grupo'}")
        header.setCheckable(collapsible)
        header.setChecked(expanded)
        header.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        header.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: white;
                text-align: left;
                padding: 8px;
                border: none;
                font-weight: bold;
                font-size: 10pt;
                border-radius: 4px 4px 0 0;
            }}
            QPushButton:hover {{
                background-color: {color}dd;
            }}
        """)
        group_layout.addWidget(header)

        # Info label (placeholder for grouped items)
        info_label = QLabel("   Los items del grupo aparecerán aquí durante la ejecución")
        info_label.setStyleSheet("""
            QLabel {
                color: #888888;
                font-size: 8pt;
                font-style: italic;
                padding: 8px;
            }
        """)
        group_layout.addWidget(info_label)

        # Delete button at bottom right
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        delete_btn = QPushButton("✕ Eliminar")
        delete_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #3d3d3d;
                color: #e4475b;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 8pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e4475b;
                color: #ffffff;
            }
        """)
        delete_btn.setToolTip("Eliminar grupo")
        delete_btn.clicked.connect(self.on_delete)
        button_layout.addWidget(delete_btn)

        group_layout.addLayout(button_layout)

        main_layout.addWidget(group_widget)
