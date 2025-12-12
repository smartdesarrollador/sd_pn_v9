"""
Widget base para items de vista completa

Clase abstracta que proporciona funcionalidad común para todos
los tipos de items (TEXT, CODE, URL, PATH).

Autor: Widget Sidebar Team
Versión: 1.0
"""

from PyQt6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout
from PyQt6.QtCore import Qt, pyqtSignal
from abc import abstractmethod
from ..common.copy_button import CopyButton
import pyperclip


class BaseItemWidget(QFrame):
    """
    Clase base abstracta para todos los widgets de items

    Proporciona:
    - Layout base con área de contenido y botón de copiar
    - Funcionalidad de copiado al portapapeles
    - Métodos helper para obtener datos del item
    - Método abstracto render_content() que debe ser implementado

    Señales:
        item_copied: Emitida cuando se copia el item al portapapeles
    """

    # Señales
    item_copied = pyqtSignal(dict)

    def __init__(self, item_data: dict, parent=None):
        """
        Inicializar widget base de item

        Args:
            item_data: Diccionario con datos del item
            parent: Widget padre
        """
        super().__init__(parent)

        self.item_data = item_data
        self.copy_button = None

        self.init_base_ui()
        self.render_content()  # Método abstracto - implementado por subclases

    def init_base_ui(self):
        """Inicializar UI base común a todos los items"""
        # Layout principal (horizontal)
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(12, 12, 12, 12)
        self.main_layout.setSpacing(10)

        # Layout de contenido (vertical, izquierda)
        self.content_layout = QVBoxLayout()
        self.content_layout.setSpacing(6)
        self.main_layout.addLayout(self.content_layout, 1)

        # Botón de copiar (derecha)
        self.copy_button = CopyButton()
        self.copy_button.copy_clicked.connect(self.copy_to_clipboard)
        self.main_layout.addWidget(
            self.copy_button,
            alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight
        )

        # Cursor
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    @abstractmethod
    def render_content(self):
        """
        Renderizar contenido específico del tipo de item

        Este método debe ser implementado por cada subclase
        para mostrar el contenido según el tipo de item.
        """
        pass

    def copy_to_clipboard(self):
        """
        Copiar contenido del item al portapapeles

        Copia el campo 'content' del item_data y emite
        la señal item_copied.
        """
        content = self.item_data.get('content', '')
        if content:
            try:
                pyperclip.copy(content)
                self.item_copied.emit(self.item_data)
            except Exception as e:
                print(f"Error al copiar al portapapeles: {e}")

    def get_item_label(self) -> str:
        """
        Obtener etiqueta/título del item

        Returns:
            Etiqueta del item o 'Sin título' si no existe
        """
        return self.item_data.get('label', 'Sin título')

    def get_item_content(self) -> str:
        """
        Obtener contenido del item

        Returns:
            Contenido del item o string vacío si no existe
        """
        return self.item_data.get('content', '')

    def get_item_description(self) -> str:
        """
        Obtener descripción del item

        Returns:
            Descripción del item o string vacío si no existe
        """
        return self.item_data.get('description', '')

    def get_item_type(self) -> str:
        """
        Obtener tipo del item

        Returns:
            Tipo del item (TEXT, CODE, URL, PATH)
        """
        return self.item_data.get('type', 'TEXT')

    def get_item_id(self) -> int:
        """
        Obtener ID del item

        Returns:
            ID del item o None si no existe
        """
        return self.item_data.get('id')

    def is_content_long(self, max_length: int = 800) -> bool:
        """
        Verificar si el contenido es extenso

        Args:
            max_length: Longitud máxima antes de considerar extenso

        Returns:
            True si el contenido excede max_length caracteres
        """
        content = self.get_item_content()
        return len(content) > max_length
