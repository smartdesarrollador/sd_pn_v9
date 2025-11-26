"""
Category List Item Widget
Widget para mostrar cada categoría en la ventana de gestión
FASE 4: Item con checkbox, icono, nombre, badge y menú contextual
"""
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QCheckBox, QPushButton, QMenu
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QCursor
import logging

# Get logger
logger = logging.getLogger(__name__)


class CategoryListItem(QWidget):
    """
    Widget for displaying a category in the management list.

    Layout: [Checkbox] [Icon] [Name] [Badge] [MenuButton]

    Features:
    - Checkbox to toggle active/inactive state
    - Icon with emoji
    - Name label
    - Badge showing item count
    - Menu button with context menu (Edit, Duplicate, Pin, Delete)
    """

    # Signals
    active_toggled = pyqtSignal(int, bool)  # category_id, is_active
    edit_requested = pyqtSignal(int)  # category_id
    delete_requested = pyqtSignal(int)  # category_id
    duplicate_requested = pyqtSignal(int)  # category_id
    pin_toggled = pyqtSignal(int)  # category_id

    def __init__(self, category: dict, db=None, parent=None):
        """
        Initialize category list item

        Args:
            category: Category dictionary from database
            db: DBManager instance
            parent: Parent widget
        """
        super().__init__(parent)
        self.category = category
        self.db = db
        self.category_id = category['id']
        self.is_active = category.get('is_active', 1)
        self.is_pinned = category.get('is_pinned', 0)
        self.is_predefined = category.get('is_predefined', 0)

        # State
        self._is_hovered = False

        self.init_ui()
        self.update_visual_state()

    def init_ui(self):
        """Initialize the UI"""
        # Widget properties
        self.setFixedHeight(60)
        self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))

        # Enable hover events
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self.setMouseTracking(True)

        # Main layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 8, 16, 8)
        layout.setSpacing(12)

        # Checkbox for active/inactive
        self.checkbox = QCheckBox()
        self.checkbox.setChecked(bool(self.is_active))
        self.checkbox.setStyleSheet("""
            QCheckBox {
                spacing: 0px;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
                border-radius: 4px;
                border: 2px solid #3d3d3d;
                background-color: #1e1e1e;
            }
            QCheckBox::indicator:hover {
                border: 2px solid #007acc;
            }
            QCheckBox::indicator:checked {
                background-color: #007acc;
                border: 2px solid #005a9e;
                image: url(none);
            }
            QCheckBox::indicator:checked:after {
                content: "✓";
                color: white;
            }
        """)
        self.checkbox.stateChanged.connect(self._on_checkbox_changed)
        self.checkbox.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        layout.addWidget(self.checkbox)

        # Icon label
        icon = self.category.get('icon', '📁')
        self.icon_label = QLabel(icon)
        self.icon_label.setStyleSheet("""
            QLabel {
                font-size: 28px;
                padding: 0px;
            }
        """)
        self.icon_label.setFixedSize(40, 40)
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.icon_label)

        # Name label
        self.name_label = QLabel(self.category['name'])
        self.name_label.setStyleSheet("""
            QLabel {
                font-size: 13pt;
                font-weight: 500;
                color: #ffffff;
            }
        """)
        self.name_label.setMinimumWidth(200)
        layout.addWidget(self.name_label)

        # Spacer
        layout.addStretch()

        # Pinned indicator (if category is pinned)
        if self.is_pinned:
            pin_label = QLabel("📌")
            pin_label.setStyleSheet("""
                QLabel {
                    font-size: 16px;
                    color: #888888;
                }
            """)
            pin_label.setToolTip("Categoría anclada")
            layout.addWidget(pin_label)

        # Predefined indicator (if category is predefined)
        if self.is_predefined:
            predefined_label = QLabel("🔒")
            predefined_label.setStyleSheet("""
                QLabel {
                    font-size: 14px;
                    color: #888888;
                }
            """)
            predefined_label.setToolTip("Categoría predefinida del sistema")
            layout.addWidget(predefined_label)

        # Badge with item count
        item_count = self.category.get('item_count', 0)
        self.badge_label = QLabel(f"{item_count} items")
        self.badge_label.setStyleSheet("""
            QLabel {
                background-color: rgba(255, 255, 255, 0.1);
                color: #cccccc;
                border-radius: 10px;
                padding: 4px 10px;
                font-size: 10pt;
            }
        """)
        self.badge_label.setFixedHeight(24)
        layout.addWidget(self.badge_label)

        # Menu button
        self.menu_btn = QPushButton("⋮")
        self.menu_btn.setFixedSize(35, 35)
        self.menu_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #888888;
                border: none;
                border-radius: 17px;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3d3d3d;
                color: #cccccc;
            }
            QPushButton:pressed {
                background-color: #4d4d4d;
            }
        """)
        self.menu_btn.clicked.connect(self._show_context_menu)
        self.menu_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        layout.addWidget(self.menu_btn)

        # Apply base style
        self._apply_base_style()

    def _apply_base_style(self):
        """Apply base stylesheet"""
        self.setStyleSheet("""
            CategoryListItem {
                background-color: #252525;
                border-radius: 8px;
                border: 1px solid transparent;
            }
            CategoryListItem:hover {
                background-color: #2d2d2d;
                border: 1px solid #3d3d3d;
            }
        """)

    def _on_checkbox_changed(self, state):
        """Handle checkbox state change"""
        new_active_state = (state == Qt.CheckState.Checked.value)

        # Update in database
        if self.db:
            try:
                success = self.db.set_category_active(self.category_id, new_active_state)
                if success:
                    self.is_active = new_active_state
                    self.update_visual_state()
                    self.active_toggled.emit(self.category_id, new_active_state)
                    logger.info(f"Category {self.category_id} active state changed to: {new_active_state}")
                else:
                    # Revert checkbox if update failed
                    self.checkbox.blockSignals(True)
                    self.checkbox.setChecked(not new_active_state)
                    self.checkbox.blockSignals(False)
                    logger.error(f"Failed to update category {self.category_id} active state")
            except Exception as e:
                logger.error(f"Error updating category active state: {e}")
                # Revert checkbox
                self.checkbox.blockSignals(True)
                self.checkbox.setChecked(not new_active_state)
                self.checkbox.blockSignals(False)

    def _show_context_menu(self):
        """Show context menu with actions"""
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #2b2b2b;
                color: #cccccc;
                border: 1px solid #3d3d3d;
                border-radius: 6px;
                padding: 5px;
            }
            QMenu::item {
                padding: 8px 30px 8px 30px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #007acc;
                color: #ffffff;
            }
            QMenu::separator {
                height: 1px;
                background-color: #3d3d3d;
                margin: 5px 10px;
            }
        """)

        # Edit action
        edit_action = menu.addAction("✏️ Editar categoría")
        edit_action.triggered.connect(lambda: self.edit_requested.emit(self.category_id))

        # Duplicate action
        duplicate_action = menu.addAction("📋 Duplicar categoría")
        duplicate_action.triggered.connect(lambda: self.duplicate_requested.emit(self.category_id))

        menu.addSeparator()

        # Pin/Unpin action
        if self.is_pinned:
            pin_action = menu.addAction("📌 Desanclar")
        else:
            pin_action = menu.addAction("📌 Anclar")
        pin_action.triggered.connect(lambda: self.pin_toggled.emit(self.category_id))

        menu.addSeparator()

        # Delete action
        delete_action = menu.addAction("🗑️ Eliminar categoría")
        delete_action.triggered.connect(lambda: self.delete_requested.emit(self.category_id))

        # Disable delete for predefined categories
        if self.is_predefined:
            delete_action.setEnabled(False)
            delete_action.setText("🗑️ Eliminar categoría (No permitido para categorías predefinidas)")

        # Show menu at button position
        menu.exec(self.menu_btn.mapToGlobal(self.menu_btn.rect().bottomLeft()))

    def update_visual_state(self):
        """Update visual state based on active status"""
        if not self.is_active:
            # Inactive state: reduced opacity
            self.setStyleSheet("""
                CategoryListItem {
                    background-color: #1e1e1e;
                    border-radius: 8px;
                    border: 1px solid transparent;
                    opacity: 0.6;
                }
                CategoryListItem:hover {
                    background-color: #252525;
                    border: 1px solid #3d3d3d;
                }
            """)
            self.name_label.setStyleSheet("""
                QLabel {
                    font-size: 13pt;
                    font-weight: 500;
                    color: #888888;
                }
            """)
        else:
            # Active state: normal appearance
            self._apply_base_style()
            self.name_label.setStyleSheet("""
                QLabel {
                    font-size: 13pt;
                    font-weight: 500;
                    color: #ffffff;
                }
            """)

    def enterEvent(self, event):
        """Handle mouse enter event"""
        self._is_hovered = True
        super().enterEvent(event)

    def leaveEvent(self, event):
        """Handle mouse leave event"""
        self._is_hovered = False
        super().leaveEvent(event)

    def get_category_data(self):
        """Get current category data"""
        return {
            'id': self.category_id,
            'name': self.category['name'],
            'icon': self.category.get('icon', '📁'),
            'is_active': self.is_active,
            'is_pinned': self.is_pinned,
            'is_predefined': self.is_predefined,
            'item_count': self.category.get('item_count', 0)
        }
