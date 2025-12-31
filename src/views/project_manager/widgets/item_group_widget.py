"""
Widget contenedor de grupo de items

Agrupa items bajo un encabezado de grupo (categoría, lista o tag).
Para listas, incluye botones de "+ Agregar Item".

Autor: Widget Sidebar Team
Versión: 1.1
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame
from PyQt6.QtCore import Qt, pyqtSignal
from .headers.group_header import GroupHeaderWidget
from .items import TextItemWidget, CodeItemWidget, URLItemWidget, PathItemWidget, WebStaticItemWidget
import sys
from pathlib import Path

# Importar ImageItemWidget desde util (temporalmente)
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "util"))
from image_item_widget import ImageItemWidget


class ItemGroupWidget(QWidget):
    """
    Widget contenedor de grupo de items

    Agrupa items bajo un encabezado de grupo.
    Renderiza cada item con el widget apropiado según su tipo.
    Para listas, incluye botones "+ Agregar Item".

    Nivel de jerarquía: Grupos (categorías, listas, tags de items)

    Señales:
        create_list_clicked: Emitida cuando se hace click en "+" del header (solo listas)
        add_item_clicked: Emitida cuando se hace click en "+ Agregar Item" (solo listas)
    """

    # Señales
    create_list_clicked = pyqtSignal()
    add_item_clicked = pyqtSignal()

    def __init__(self, group_name: str, group_type: str = "category", db_manager=None, parent=None):
        """
        Inicializar widget de grupo de items

        Args:
            group_name: Nombre del grupo
            group_type: Tipo de grupo ('category', 'list', 'tag')
            db_manager: Instancia de DBManager (para ImageItemWidget)
            parent: Widget padre
        """
        super().__init__(parent)

        self.group_name = group_name
        self.group_type = group_type
        self.db_manager = db_manager
        self.items = []

        self.init_ui()

    def init_ui(self):
        """Inicializar interfaz de usuario"""
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # Header del grupo
        self.header = GroupHeaderWidget()
        self.header.set_group_info(self.group_name, self.group_type)
        self.header.create_list_clicked.connect(self.create_list_clicked.emit)
        self.main_layout.addWidget(self.header)

        # Si es lista, agregar barra de "Items" con botones
        if self.group_type == "list":
            self._add_items_toolbar()

        # Layout de items
        self.items_layout = QVBoxLayout()
        self.items_layout.setSpacing(0)
        self.main_layout.addLayout(self.items_layout)

    def _add_items_toolbar(self):
        """Agregar barra de herramientas de items (solo para listas)"""
        toolbar = QFrame()
        toolbar.setObjectName("itemsToolbar")
        toolbar.setStyleSheet("""
            QFrame#itemsToolbar {
                background-color: #252525;
                border-top: 1px solid #333;
                border-bottom: 1px solid #333;
            }
        """)
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(40, 8, 15, 8)
        toolbar_layout.setSpacing(10)

        # Label "Items"
        items_label = QLabel("📦 Items")
        items_label.setStyleSheet("""
            color: #ffffff;
            font-size: 10px;
            font-weight: bold;
        """)
        toolbar_layout.addWidget(items_label)

        toolbar_layout.addStretch()

        # Botón "+ Agregar Item"
        add_item_btn = QPushButton("+ Agregar Item")
        add_item_btn.setFixedHeight(28)
        add_item_btn.setMinimumWidth(110)
        add_item_btn.setToolTip("Agregar nuevo item a esta lista")
        add_item_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_item_btn.setStyleSheet("""
            QPushButton {
                background-color: #1565C0;
                color: #ffffff;
                border: 1px solid #1976D2;
                border-radius: 4px;
                font-size: 10px;
                font-weight: bold;
                padding: 4px 10px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #0d47a1;
            }
        """)
        add_item_btn.clicked.connect(self.add_item_clicked.emit)
        toolbar_layout.addWidget(add_item_btn)

        self.main_layout.addWidget(toolbar)

    def _is_image_item(self, item_data: dict) -> bool:
        """
        Detectar si un item PATH es una imagen

        Args:
            item_data: Diccionario con datos del item

        Returns:
            True si es un item de imagen
        """
        if item_data.get('type') != 'PATH':
            return False

        # Extensiones de imagen soportadas
        image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp', '.ico', '.svg'}

        # Verificar file_extension si existe
        file_extension = item_data.get('file_extension', '')
        if file_extension:
            return file_extension.lower() in image_extensions

        # Fallback: verificar por content (nombre de archivo)
        content = item_data.get('content', '')
        if content:
            import os
            _, ext = os.path.splitext(content)
            return ext.lower() in image_extensions

        return False

    def add_item(self, item_data: dict):
        """
        Agregar item al grupo

        Crea el widget apropiado según el tipo de item
        y lo agrega al layout de items.

        Args:
            item_data: Diccionario con datos del item
        """
        item_type = item_data.get('type', 'TEXT')

        # Crear widget según tipo
        if item_type == 'CODE':
            item_widget = CodeItemWidget(item_data)
        elif item_type == 'URL':
            item_widget = URLItemWidget(item_data)
        elif item_type == 'PATH':
            # Detectar si es imagen para usar widget especializado
            if self._is_image_item(item_data):
                item_widget = ImageItemWidget(item_data, db_manager=self.db_manager)
                # Conectar señales específicas de imagen
                item_widget.thumbnail_clicked.connect(lambda: self._on_image_thumbnail_clicked(item_data))
                item_widget.move_up_clicked.connect(lambda: print(f"TODO: Move up {item_data.get('label')}"))
                item_widget.move_down_clicked.connect(lambda: print(f"TODO: Move down {item_data.get('label')}"))
                item_widget.edit_clicked.connect(lambda: print(f"TODO: Edit {item_data.get('label')}"))
                item_widget.detail_clicked.connect(lambda: print(f"TODO: Detail {item_data.get('label')}"))
                item_widget.delete_clicked.connect(lambda: print(f"TODO: Delete {item_data.get('label')}"))
            else:
                item_widget = PathItemWidget(item_data)
        elif item_type == 'WEB_STATIC':
            item_widget = WebStaticItemWidget(item_data)
        else:  # TEXT o por defecto
            item_widget = TextItemWidget(item_data)

        # Conectar señal de copiado
        item_widget.item_copied.connect(self.on_item_copied)

        self.items.append(item_widget)
        self.items_layout.addWidget(item_widget)

    def on_item_copied(self, item_data: dict):
        """
        Manejar evento de item copiado

        Args:
            item_data: Datos del item copiado
        """
        label = item_data.get('label', 'Sin título')
        print(f"✓ Item copiado del grupo '{self.group_name}': {label}")

    def _on_image_thumbnail_clicked(self, item_data: dict):
        """
        Manejar clic en miniatura de imagen - abrir visor completo

        Args:
            item_data: Datos del item de imagen
        """
        try:
            # Importar ImageViewerDialog
            from image_viewer_dialog import ImageViewerDialog

            # Obtener ruta completa de la imagen
            filename = item_data.get('content', '')
            if not filename:
                print(f"⚠️ Item sin filename: {item_data.get('label')}")
                return

            # Construir ruta completa
            import os
            if self.db_manager and hasattr(self.db_manager, 'config_manager'):
                base_path = self.db_manager.config_manager.get_setting('files_base_path', '')
                folder = self.db_manager.config_manager.get_setting('screenshots_folder_name', 'IMAGENES')
                full_path = os.path.join(base_path, folder, filename)
            else:
                full_path = filename

            # Verificar que el archivo existe
            if not os.path.exists(full_path):
                print(f"⚠️ Imagen no encontrada: {full_path}")
                return

            # Abrir visor de imagen
            print(f"🖼️ Abriendo visor para: {item_data.get('label')}")
            viewer = ImageViewerDialog(full_path, parent=self)
            viewer.exec()

        except Exception as e:
            print(f"❌ Error abriendo visor de imagen: {e}")
            import traceback
            traceback.print_exc()

    def clear_items(self):
        """Limpiar todos los items del grupo"""
        for item in self.items:
            item.deleteLater()
        self.items.clear()

    def get_item_count(self) -> int:
        """
        Obtener cantidad de items en el grupo

        Returns:
            Número de items
        """
        return len(self.items)

    def get_group_name(self) -> str:
        """
        Obtener nombre del grupo

        Returns:
            Nombre del grupo
        """
        return self.group_name

    def get_group_type(self) -> str:
        """
        Obtener tipo del grupo

        Returns:
            Tipo del grupo
        """
        return self.group_type
