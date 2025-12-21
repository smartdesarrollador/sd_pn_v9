"""
Widget base para items de vista completa

Clase abstracta que proporciona funcionalidad común para todos
los tipos de items (TEXT, CODE, URL, PATH).

Autor: Widget Sidebar Team
Versión: 1.0
"""

from PyQt6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QMenu
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QCursor
from abc import abstractmethod
from ..common.copy_button import CopyButton
import pyperclip
import re
import logging

logger = logging.getLogger(__name__)


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
        # Establecer ancho fijo para el contenedor del item
        self.setFixedWidth(800)  # ANCHO FIJO: 800px

        # Layout principal (horizontal)
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(12, 12, 12, 12)
        self.main_layout.setSpacing(10)

        # Layout de contenido (vertical, izquierda)
        self.content_layout = QVBoxLayout()
        self.content_layout.setSpacing(6)
        self.main_layout.addLayout(self.content_layout, 1)  # stretch=1 para ocupar espacio disponible

        # Contenedor de botones de acción (derecha)
        self.buttons_layout = QHBoxLayout()
        self.buttons_layout.setSpacing(4)
        self.buttons_layout.setContentsMargins(0, 0, 0, 0)

        # Crear botones de acción (llamar método que puede ser sobrescrito)
        self._create_action_buttons()

        # Agregar botones comunes (editar, info, más)
        self._create_common_buttons()

        self.main_layout.addLayout(self.buttons_layout, 0)

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
        # Si el item es sensible, verificar contraseña maestra
        if self.item_data.get('is_sensitive', False):
            from src.views.dialogs.master_password_dialog import MasterPasswordDialog

            item_label = self.item_data.get('label', 'item sensible')
            verified = MasterPasswordDialog.verify(
                title="Item Sensible",
                message=f"Ingresa tu contraseña maestra para copiar:\n'{item_label}'",
                parent=self.window()
            )

            if not verified:
                print(f"Master password verification cancelled for copying item: {item_label}")
                return  # Usuario canceló o contraseña incorrecta

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

        Si el item es sensible (is_sensitive=True) y NO está revelado,
        retorna el contenido enmascarado para proteger la información.

        Returns:
            Contenido del item o string vacío si no existe.
            Si es sensible y no revelado, retorna contenido enmascarado.
        """
        content = self.item_data.get('content', '')
        is_sensitive = self.item_data.get('is_sensitive', False)

        # Si el item es sensible Y no está revelado, enmascarar el contenido
        if is_sensitive and content and not getattr(self, '_is_revealed', False):
            # Calcular longitud aproximada para el enmascaramiento
            # Usar puntos circulares (bullets) para enmascarar
            mask_length = min(len(content), 20)  # Máximo 20 bullets
            return '•' * mask_length + (' ...' if len(content) > 20 else '')

        return content

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

    def has_match(self, search_text: str) -> bool:
        """
        Verificar si el item coincide con el texto de búsqueda

        Busca en: label, content (sin enmascarar), y description

        Args:
            search_text: Texto a buscar (case-insensitive)

        Returns:
            True si hay coincidencia en algún campo
        """
        if not search_text:
            return False

        search_lower = search_text.lower()

        # Buscar en label
        label = self.get_item_label()
        if label and search_lower in label.lower():
            return True

        # Buscar en content (sin enmascarar)
        content = self.item_data.get('content', '')
        if content and search_lower in content.lower():
            return True

        # Buscar en description
        description = self.get_item_description()
        if description and search_lower in description.lower():
            return True

        return False

    def highlight_text(self, search_text: str):
        """
        Resaltar texto de búsqueda en el widget

        Recorre todos los QLabel hijos y resalta el texto encontrado
        usando HTML con color de fondo amarillo.

        Args:
            search_text: Texto a resaltar (case-insensitive)
        """
        if not search_text:
            return

        # Recorrer todos los widgets hijos que sean QLabel
        for child in self.findChildren(QLabel):
            self._highlight_label(child, search_text)

    def clear_highlight(self):
        """
        Limpiar resaltado de texto en el widget

        Restaura el texto original sin HTML de resaltado.
        """
        # Recorrer todos los QLabel hijos y limpiar HTML
        for child in self.findChildren(QLabel):
            self._clear_label_highlight(child)

    def _highlight_label(self, label: QLabel, search_text: str):
        """
        Resaltar texto en un QLabel específico

        Args:
            label: QLabel a modificar
            search_text: Texto a resaltar
        """
        original_text = label.text()

        # Si el texto ya tiene HTML (indicado por tags), extraer texto plano
        if '<' in original_text and '>' in original_text:
            # Intentar extraer texto sin HTML
            import html
            plain_text = re.sub(r'<[^>]+>', '', original_text)
            plain_text = html.unescape(plain_text)
        else:
            plain_text = original_text

        # Guardar texto original en una propiedad dinámica si no existe
        if not label.property("original_text"):
            label.setProperty("original_text", plain_text)

        # Crear patrón regex case-insensitive
        pattern = re.compile(re.escape(search_text), re.IGNORECASE)

        # Función de reemplazo que preserva el caso original
        def replace_match(match):
            matched_text = match.group(0)
            return f'<span style="background-color: #FFD700; color: #000000; font-weight: bold;">{matched_text}</span>'

        # Aplicar resaltado
        highlighted_text = pattern.sub(replace_match, plain_text)

        # Si hubo cambios, aplicar HTML
        if highlighted_text != plain_text:
            # Preservar saltos de línea y espacios en HTML
            highlighted_text = highlighted_text.replace('\n', '<br>')
            label.setTextFormat(Qt.TextFormat.RichText)
            label.setText(highlighted_text)

    def _clear_label_highlight(self, label: QLabel):
        """
        Limpiar resaltado en un QLabel específico

        Args:
            label: QLabel a limpiar
        """
        # Restaurar texto original si existe
        original_text = label.property("original_text")
        if original_text:
            label.setTextFormat(Qt.TextFormat.PlainText)
            label.setText(original_text)
            label.setProperty("original_text", None)

    def _create_action_buttons(self):
        """
        Crear botones de acción específicos del tipo de item

        Este método puede ser sobrescrito por las subclases para
        agregar botones específicos según el tipo de item.

        Por defecto, solo agrega el botón de copiar.
        """
        # Botón de copiar (siempre presente)
        self.copy_button = CopyButton()
        self.copy_button.copy_clicked.connect(self.copy_to_clipboard)
        self.copy_button.setFixedSize(28, 28)
        self.copy_button.setToolTip("Copiar contenido")
        self.buttons_layout.addWidget(self.copy_button)

    def _create_common_buttons(self):
        """
        Crear botones comunes a todos los tipos de items

        Botones:
        - Revelar/Ocultar (solo para items sensibles)
        - Detalles (info)
        """
        # Botón revelar/ocultar (solo para items sensibles)
        if self.item_data.get('is_sensitive', False):
            self.reveal_button = QPushButton("👁")
            self.reveal_button.setFixedSize(28, 28)
            self.reveal_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            self.reveal_button.setStyleSheet("""
                QPushButton {
                    background-color: #cc0000;
                    color: #ffffff;
                    border: none;
                    border-radius: 3px;
                    font-size: 12pt;
                    padding: 0px;
                }
                QPushButton:hover {
                    background-color: #9e0000;
                }
                QPushButton:pressed {
                    background-color: #780000;
                }
            """)
            self.reveal_button.setToolTip("Revelar/Ocultar contenido sensible")
            self.reveal_button.clicked.connect(self._toggle_reveal)
            self.buttons_layout.addWidget(self.reveal_button)
            self._is_revealed = False

        # Botón detalles (info)
        self.info_btn = QPushButton("ℹ️")
        self.info_btn.setFixedSize(28, 28)
        self.info_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.info_btn.setStyleSheet("""
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
        self.info_btn.setToolTip("Ver detalles del item")
        self.info_btn.clicked.connect(self._show_details)
        self.buttons_layout.addWidget(self.info_btn)

    def _toggle_reveal(self):
        """Revelar/ocultar contenido sensible"""
        if not hasattr(self, '_is_revealed'):
            self._is_revealed = False

        # Si no está revelado, verificar contraseña maestra
        if not self._is_revealed:
            from src.views.dialogs.master_password_dialog import MasterPasswordDialog

            item_label = self.item_data.get('label', 'item sensible')
            verified = MasterPasswordDialog.verify(
                title="Item Sensible",
                message=f"Ingresa tu contraseña maestra para revelar:\n'{item_label}'",
                parent=self.window()
            )

            if not verified:
                logger.info(f"Master password verification cancelled for revealing item: {item_label}")
                return

        # Alternar estado
        self._is_revealed = not self._is_revealed

        # Actualizar icono del botón
        if self._is_revealed:
            self.reveal_button.setText("🙈")
            self.reveal_button.setToolTip("Ocultar contenido sensible")
        else:
            self.reveal_button.setText("👁")
            self.reveal_button.setToolTip("Revelar contenido sensible")

        # Renderizar de nuevo el contenido (las subclases deben manejar esto)
        self._update_content_visibility()

    def _update_content_visibility(self):
        """
        Actualizar visibilidad del contenido sensible

        Re-renderiza el contenido del item para mostrar/ocultar
        información sensible según el estado de revelado.
        """
        # Limpiar el layout de contenido
        while self.content_layout.count():
            child = self.content_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
            elif child.layout():
                # Si es un layout, eliminar sus widgets también
                while child.layout().count():
                    subchild = child.layout().takeAt(0)
                    if subchild.widget():
                        subchild.widget().deleteLater()

        # Volver a renderizar el contenido
        self.render_content()

    def _edit_item(self):
        """Editar el item"""
        # Si el item es sensible, verificar contraseña maestra
        if self.item_data.get('is_sensitive', False):
            from src.views.dialogs.master_password_dialog import MasterPasswordDialog

            item_label = self.item_data.get('label', 'item sensible')
            verified = MasterPasswordDialog.verify(
                title="Item Sensible",
                message=f"Ingresa tu contraseña maestra para editar:\n'{item_label}'",
                parent=self.window()
            )

            if not verified:
                logger.info(f"Master password verification cancelled for editing item: {item_label}")
                return

        # Abrir diálogo de edición
        from src.views.item_editor_dialog import ItemEditorDialog
        from src.models.item import Item

        try:
            # Convertir dict a objeto Item
            item = Item.from_dict(self.item_data)

            # Crear diálogo de edición
            dialog = ItemEditorDialog(item=item, parent=self.window())
            result = dialog.exec()

            if result:
                logger.info(f"Item edited: {item.label}")
                # Recargar la vista del área
                self._reload_area_view()

        except Exception as e:
            logger.error(f"Error editing item: {e}")

    def _show_details(self):
        """Mostrar detalles del item"""
        # Si el item es sensible, verificar contraseña maestra
        if self.item_data.get('is_sensitive', False):
            from src.views.dialogs.master_password_dialog import MasterPasswordDialog

            item_label = self.item_data.get('label', 'item sensible')
            verified = MasterPasswordDialog.verify(
                title="Item Sensible",
                message=f"Ingresa tu contraseña maestra para ver detalles de:\n'{item_label}'",
                parent=self.window()
            )

            if not verified:
                logger.info(f"Master password verification cancelled for viewing details: {item_label}")
                return

        # Abrir diálogo de detalles
        from src.views.dialogs.item_details_dialog import ItemDetailsDialog
        from src.models.item import Item

        try:
            # Convertir dict a objeto Item
            item = Item.from_dict(self.item_data)

            # Crear diálogo de detalles
            dialog = ItemDetailsDialog(item, parent=self.window())
            dialog.exec()

        except Exception as e:
            logger.error(f"Error showing item details: {e}")

    def _reload_area_view(self):
        """
        Recargar la vista del área completa

        Busca el AreaFullViewPanel padre y recarga la vista.
        """
        from src.views.area_manager.area_full_view_panel import AreaFullViewPanel

        # Buscar el panel padre
        parent_widget = self.parent()
        while parent_widget:
            if isinstance(parent_widget, AreaFullViewPanel):
                parent_widget.refresh_view()
                break
            parent_widget = parent_widget.parent()
