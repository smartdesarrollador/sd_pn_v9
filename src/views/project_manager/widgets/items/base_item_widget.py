"""
Widget base para items de vista completa

Clase abstracta que proporciona funcionalidad común para todos
los tipos de items (TEXT, CODE, URL, PATH).

Autor: Widget Sidebar Team
Versión: 1.0
"""

from PyQt6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QMenu, QScrollArea, QWidget
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QCursor
from abc import abstractmethod
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

        # Variables para resize manual
        self._is_resizing = False
        self._resize_start_y = 0
        self._resize_start_height = 0
        self._custom_height = None  # Altura personalizada por el usuario

        self.init_base_ui()
        self.render_content()  # Método abstracto - implementado por subclases
        self._adjust_height_for_content()  # Ajustar altura según contenido

        # Habilitar tracking del mouse para resize
        self.setMouseTracking(True)

    def init_base_ui(self):
        """Inicializar UI base común a todos los items"""
        # Hacer el contenedor responsivo (sin ancho fijo)
        # Establecer ancho mínimo pero permitir expansión
        self.setMinimumWidth(400)
        self.setMaximumWidth(16777215)  # Sin límite máximo (QWIDGETSIZE_MAX)

        # IMPORTANTE: Limitar altura máxima para evitar que crezca demasiado
        self.setMaximumHeight(300)  # Altura máxima de 300px

        # Política de tamaño: expandir horizontalmente, máximo verticalmente
        from PyQt6.QtWidgets import QSizePolicy
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)

        # ✨ NUEVO: Layout principal VERTICAL
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # ✨ NUEVO: Barra de acciones superior (esquina derecha)
        action_bar = QWidget()
        action_bar.setFixedHeight(32)
        action_bar.setStyleSheet("background-color: transparent;")
        action_bar_layout = QHBoxLayout(action_bar)
        action_bar_layout.setContentsMargins(8, 4, 8, 4)
        action_bar_layout.setSpacing(6)

        # Spacer para empujar botones a la derecha
        action_bar_layout.addStretch()

        # Contenedor de botones de acción (derecha)
        self.buttons_layout = QHBoxLayout()
        self.buttons_layout.setSpacing(6)
        self.buttons_layout.setContentsMargins(0, 0, 0, 0)

        # Crear botones de acción (copiar e info)
        self._create_action_buttons()
        self._create_common_buttons()

        action_bar_layout.addLayout(self.buttons_layout)

        # Agregar barra de acciones al layout principal
        self.main_layout.addWidget(action_bar)

        # ✨ MODIFICADO: Área de contenido (debajo de la barra)
        content_container_widget = QWidget()
        content_container_widget.setStyleSheet("background: transparent;")
        content_container_layout = QVBoxLayout(content_container_widget)
        content_container_layout.setContentsMargins(8, 0, 8, 6)
        content_container_layout.setSpacing(0)

        # Scroll area para el contenido (permite scroll vertical interno)
        self.content_scroll = QScrollArea()
        self.content_scroll.setWidgetResizable(True)
        self.content_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.content_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.content_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.content_scroll.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background: #2d2d2d;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #555555;
                border-radius: 4px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: #00ff88;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

        # Widget contenedor del contenido (dentro del scroll)
        self.content_container = QWidget()
        self.content_container.setStyleSheet("background: transparent;")

        # Layout de contenido (vertical, dentro del contenedor)
        self.content_layout = QVBoxLayout(self.content_container)
        self.content_layout.setSpacing(4)
        self.content_layout.setContentsMargins(0, 0, 0, 0)

        # Establecer el contenedor en el scroll area
        self.content_scroll.setWidget(self.content_container)

        # Agregar scroll area al contenedor de contenido
        content_container_layout.addWidget(self.content_scroll)

        # Agregar contenedor de contenido al layout principal
        self.main_layout.addWidget(content_container_widget, 1)

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
        la señal item_copied. Muestra feedback visual verde en el botón.
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

                # Feedback visual: cambiar botón a verde temporalmente
                self._show_copy_success_feedback()

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

        ✨ NUEVO DISEÑO: Botones de ordenamiento + editar + copiar
        """
        # Botón mover arriba (gris con flecha ▲)
        self.move_up_button = QPushButton("▲")
        self.move_up_button.setFixedSize(32, 24)
        self.move_up_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.move_up_button.setStyleSheet("""
            QPushButton {
                background-color: #4d4d4d;
                color: #ff5555;
                border: 1px solid #555;
                border-radius: 4px;
                font-size: 12px;
                font-weight: bold;
                padding: 2px;
            }
            QPushButton:hover {
                background-color: #5d5d5d;
                border-color: #ff5555;
                color: #ff7777;
            }
            QPushButton:pressed {
                background-color: #3d3d3d;
            }
            QPushButton:disabled {
                background-color: #2d2d2d;
                color: #555;
                border-color: #444;
            }
        """)
        self.move_up_button.setToolTip("Mover item hacia arriba")
        self.move_up_button.clicked.connect(self._move_item_up)
        self.buttons_layout.addWidget(self.move_up_button)

        # Botón mover abajo (gris con flecha ▼)
        self.move_down_button = QPushButton("▼")
        self.move_down_button.setFixedSize(32, 24)
        self.move_down_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.move_down_button.setStyleSheet("""
            QPushButton {
                background-color: #4d4d4d;
                color: #ff5555;
                border: 1px solid #555;
                border-radius: 4px;
                font-size: 12px;
                font-weight: bold;
                padding: 2px;
            }
            QPushButton:hover {
                background-color: #5d5d5d;
                border-color: #ff5555;
                color: #ff7777;
            }
            QPushButton:pressed {
                background-color: #3d3d3d;
            }
            QPushButton:disabled {
                background-color: #2d2d2d;
                color: #555;
                border-color: #444;
            }
        """)
        self.move_down_button.setToolTip("Mover item hacia abajo")
        self.move_down_button.clicked.connect(self._move_item_down)
        self.buttons_layout.addWidget(self.move_down_button)

        # Botón de editar (naranja/ámbar)
        self.edit_button = QPushButton("🖊️")
        self.edit_button.setFixedSize(32, 24)
        self.edit_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.edit_button.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: #ffffff;
                border: 1px solid #F57C00;
                border-radius: 4px;
                font-size: 14px;
                padding: 2px;
            }
            QPushButton:hover {
                background-color: #FB8C00;
                border-color: #E65100;
            }
            QPushButton:pressed {
                background-color: #E65100;
            }
        """)
        self.edit_button.setToolTip("Editar item")
        self.edit_button.clicked.connect(self._edit_item)
        self.buttons_layout.addWidget(self.edit_button)

        # Botón de copiar (gris oscuro)
        self.copy_button = QPushButton("📋")
        self.copy_button.setFixedSize(32, 24)
        self.copy_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.copy_button.setStyleSheet("""
            QPushButton {
                background-color: #3d3d3d;
                color: #ffffff;
                border: 1px solid #555;
                border-radius: 4px;
                font-size: 14px;
                padding: 2px;
            }
            QPushButton:hover {
                background-color: #4d4d4d;
                border-color: #666;
            }
            QPushButton:pressed {
                background-color: #2d2d2d;
            }
        """)
        self.copy_button.setToolTip("Copiar contenido")
        self.copy_button.clicked.connect(self.copy_to_clipboard)
        self.buttons_layout.addWidget(self.copy_button)

    def _create_common_buttons(self):
        """
        Crear botones comunes a todos los tipos de items

        ✨ NUEVO DISEÑO: Solo botón de info (azul)
        """
        # Botón detalles/info (azul)
        self.info_btn = QPushButton("ℹ️")
        self.info_btn.setFixedSize(32, 24)
        self.info_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.info_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: #ffffff;
                border: 1px solid #1976D2;
                border-radius: 4px;
                font-size: 14px;
                padding: 2px;
            }
            QPushButton:hover {
                background-color: #1976D2;
                border-color: #0d47a1;
            }
            QPushButton:pressed {
                background-color: #0d47a1;
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

        # Ajustar altura según contenido actualizado
        self._adjust_height_for_content()

        # Asegurar que el scroll se actualice correctamente
        self.content_container.adjustSize()
        self.content_scroll.updateGeometry()

    def _edit_item(self):
        """Editar el item usando el nuevo EditItemDialog"""
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

        # Abrir nuevo diálogo de edición
        from src.views.dialogs.edit_item_dialog import EditItemDialog

        try:
            # Obtener db_manager desde el padre (visor o área completa)
            db_manager = self._get_db_manager()

            if not db_manager:
                logger.error("No se pudo obtener db_manager para editar item")
                return

            # Obtener datos completos del item desde BD (incluye tags actualizados)
            item_id = self.item_data.get('id')
            if not item_id:
                logger.error("Item sin ID - no se puede editar")
                return

            logger.info(f"📋 Obteniendo datos completos del item {item_id} desde BD...")
            fresh_item_data = db_manager.get_item(item_id)

            if not fresh_item_data:
                logger.error(f"No se pudo obtener item {item_id} desde BD")
                return

            logger.info(f"✅ Item obtenido: tags={fresh_item_data.get('tags', [])}")

            # Crear y mostrar diálogo de edición con datos frescos
            dialog = EditItemDialog(item_data=fresh_item_data, db_manager=db_manager, parent=self.window())
            dialog.item_updated.connect(self._on_item_updated)
            result = dialog.exec()

            if result:
                logger.info(f"Item {item_id} editado exitosamente")
                # Recargar la vista
                self._reload_view()

        except Exception as e:
            logger.error(f"Error editing item: {e}", exc_info=True)

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

    def _adjust_height_for_content(self):
        """
        Ajustar altura del widget según la cantidad de contenido

        Si el contenido es muy extenso (>400 caracteres), amplía la altura
        máxima al doble (600px) para mostrar más texto sin scroll inicial.

        Si el usuario ya estableció una altura personalizada (resize manual),
        respeta esa altura.
        """
        # Si el usuario ya personalizó la altura, no ajustar automáticamente
        if self._custom_height is not None:
            logger.debug(f"Respetando altura personalizada: {self._custom_height}px")
            return

        # Obtener contenido del item (manejar valores None)
        content = self.item_data.get('content', '') or ''
        label = self.item_data.get('label', '') or ''
        description = self.item_data.get('description', '') or ''

        # Calcular longitud total
        total_length = len(content) + len(label) + len(description)

        # Si el contenido es muy extenso, ampliar altura al doble
        if total_length > 400:  # Reducido de 800 a 400 para mejor detección
            self.setMaximumHeight(1000)  # Ampliar a 1000px
            logger.debug(f"Item con contenido extenso ({total_length} chars): altura ampliada a 1000px")
        else:
            self.setMaximumHeight(300)  # Mantener altura estándar
            logger.debug(f"Item con contenido normal ({total_length} chars): altura estándar 300px")

        # Actualizar geometría
        self.updateGeometry()

    def mouseMoveEvent(self, event):
        """
        Manejar movimiento del mouse para resize manual

        Detecta cuando el mouse está cerca del borde inferior
        y cambia el cursor a SizeVerCursor.
        """
        # Zona de resize: 10px desde el borde inferior
        resize_margin = 10
        mouse_y = event.pos().y()
        widget_height = self.height()

        # Si estamos en modo resize, actualizar altura
        if self._is_resizing:
            # Calcular nueva altura
            delta_y = event.globalPosition().y() - self._resize_start_y
            new_height = max(100, self._resize_start_height + int(delta_y))  # Mínimo 100px

            # Aplicar nueva altura
            self.setMaximumHeight(new_height)
            self.setMinimumHeight(new_height)
            self._custom_height = new_height

            logger.debug(f"Resizing item: new height = {new_height}px")
            return

        # Detectar si el mouse está cerca del borde inferior
        if widget_height - mouse_y <= resize_margin:
            self.setCursor(Qt.CursorShape.SizeVerCursor)
        else:
            self.setCursor(Qt.CursorShape.PointingHandCursor)

        super().mouseMoveEvent(event)

    def mousePressEvent(self, event):
        """
        Iniciar resize cuando se hace click en el borde inferior
        """
        # Zona de resize: 10px desde el borde inferior
        resize_margin = 10
        mouse_y = event.pos().y()
        widget_height = self.height()

        # Si el click es en la zona de resize
        if widget_height - mouse_y <= resize_margin and event.button() == Qt.MouseButton.LeftButton:
            self._is_resizing = True
            self._resize_start_y = event.globalPosition().y()
            self._resize_start_height = self.height()
            logger.debug(f"Starting resize from height: {self._resize_start_height}px")
            event.accept()
            return

        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        """
        Finalizar resize
        """
        if self._is_resizing:
            self._is_resizing = False
            logger.info(f"Resize completed: final height = {self.height()}px")
            event.accept()
            return

        super().mouseReleaseEvent(event)

    def _get_db_manager(self):
        """
        Obtener db_manager desde el widget padre

        Busca en la jerarquía de widgets hasta encontrar uno que tenga 'db' o 'db_manager'.

        Returns:
            DBManager o None si no se encuentra
        """
        # Buscar el db_manager en la jerarquía de padres
        parent_widget = self.parent()
        while parent_widget:
            # Intentar obtener db_manager o db
            if hasattr(parent_widget, 'db'):
                return parent_widget.db
            if hasattr(parent_widget, 'db_manager'):
                return parent_widget.db_manager

            parent_widget = parent_widget.parent()

        logger.warning("No se pudo encontrar db_manager en la jerarquía de widgets")
        return None

    def _on_item_updated(self, updated_item_data: dict):
        """
        Callback cuando se actualiza el item

        Args:
            updated_item_data: Datos actualizados del item
        """
        # Actualizar datos locales
        self.item_data.update(updated_item_data)
        logger.info(f"Item {self.item_data.get('id')} actualizado en widget")

        # Re-renderizar contenido con los nuevos datos
        self._update_content_visibility()

    def _reload_view(self):
        """
        Recargar la vista completa del panel padre

        Busca el ProjectAreaViewerPanel o AreaFullViewPanel padre y recarga.
        """
        from src.views.project_area_viewer_panel import ProjectAreaViewerPanel

        # Buscar el panel padre
        parent_widget = self.parent()
        while parent_widget:
            # ProjectAreaViewerPanel
            if isinstance(parent_widget, ProjectAreaViewerPanel):
                # Recargar proyecto o área actual
                if hasattr(parent_widget, 'current_project_id') and parent_widget.current_project_id:
                    parent_widget.load_project(parent_widget.current_project_id)
                    logger.info(f"Vista de proyecto {parent_widget.current_project_id} recargada")
                elif hasattr(parent_widget, 'current_area_id') and parent_widget.current_area_id:
                    parent_widget.load_area(parent_widget.current_area_id)
                    logger.info(f"Vista de área {parent_widget.current_area_id} recargada")
                break

            # AreaFullViewPanel (legacy)
            try:
                from src.views.area_manager.area_full_view_panel import AreaFullViewPanel
                if isinstance(parent_widget, AreaFullViewPanel):
                    parent_widget.refresh_view()
                    logger.info("Vista de área completa recargada")
                    break
            except ImportError:
                pass  # AreaFullViewPanel no existe

            parent_widget = parent_widget.parent()

    def _reload_area_view(self):
        """
        Recargar la vista del área completa (legacy, llama a _reload_view)

        Busca el AreaFullViewPanel padre y recarga la vista.
        """
        self._reload_view()

    def _move_item_up(self):
        """
        Mover item hacia arriba en la lista

        Intercambia el orden_lista con el item anterior en la misma lista.
        """
        try:
            # Obtener db_manager
            db_manager = self._get_db_manager()
            if not db_manager:
                logger.error("No se pudo obtener db_manager para reordenar")
                return

            # Obtener datos del item actual
            item_id = self.item_data.get('id')
            list_id = self.item_data.get('list_id')
            current_order = self.item_data.get('orden_lista')

            # DEBUG: Ver qué campos tiene item_data
            logger.debug(f"🔍 item_data keys: {list(self.item_data.keys())}")
            logger.debug(f"🔍 item_id={item_id}, list_id={list_id}, orden_lista={current_order}")

            if not list_id:
                logger.warning(f"Item {item_id} no pertenece a una lista, no se puede reordenar")
                return

            logger.info(f"⬆️ Moviendo item {item_id} hacia arriba (orden actual: {current_order})")

            # Obtener todos los items de la misma lista ordenados
            query = """
                SELECT id, orden_lista
                FROM items
                WHERE list_id = ?
                ORDER BY CAST(orden_lista AS INTEGER) ASC
            """
            items = db_manager.execute_query(query, (list_id,))

            if not items or len(items) < 2:
                logger.debug("No hay suficientes items para reordenar")
                return

            # Encontrar posición actual y anterior
            current_index = None
            for i, item in enumerate(items):
                if item['id'] == item_id:
                    current_index = i
                    break

            if current_index is None or current_index == 0:
                logger.debug("Item ya está en la primera posición")
                return

            # Intercambiar con el item anterior
            prev_item = items[current_index - 1]
            current_item = items[current_index]

            logger.debug(f"Intercambiando orden: Item {prev_item['id']} (orden {prev_item['orden_lista']}) ↔ Item {current_item['id']} (orden {current_item['orden_lista']})")

            # Actualizar orden en BD
            db_manager.execute_update(
                "UPDATE items SET orden_lista = ? WHERE id = ?",
                (current_item['orden_lista'], prev_item['id'])
            )
            db_manager.execute_update(
                "UPDATE items SET orden_lista = ? WHERE id = ?",
                (prev_item['orden_lista'], current_item['id'])
            )

            logger.info(f"✅ Item {item_id} movido hacia arriba exitosamente")

            # Recargar vista
            self._reload_view()

        except Exception as e:
            logger.error(f"❌ Error moviendo item hacia arriba: {e}", exc_info=True)

    def _move_item_down(self):
        """
        Mover item hacia abajo en la lista

        Intercambia el orden_lista con el item siguiente en la misma lista.
        """
        try:
            # Obtener db_manager
            db_manager = self._get_db_manager()
            if not db_manager:
                logger.error("No se pudo obtener db_manager para reordenar")
                return

            # Obtener datos del item actual
            item_id = self.item_data.get('id')
            list_id = self.item_data.get('list_id')
            current_order = self.item_data.get('orden_lista')

            if not list_id:
                logger.warning(f"Item {item_id} no pertenece a una lista, no se puede reordenar")
                return

            logger.info(f"⬇️ Moviendo item {item_id} hacia abajo (orden actual: {current_order})")

            # Obtener todos los items de la misma lista ordenados
            query = """
                SELECT id, orden_lista
                FROM items
                WHERE list_id = ?
                ORDER BY CAST(orden_lista AS INTEGER) ASC
            """
            items = db_manager.execute_query(query, (list_id,))

            if not items or len(items) < 2:
                logger.debug("No hay suficientes items para reordenar")
                return

            # Encontrar posición actual y siguiente
            current_index = None
            for i, item in enumerate(items):
                if item['id'] == item_id:
                    current_index = i
                    break

            if current_index is None or current_index >= len(items) - 1:
                logger.debug("Item ya está en la última posición")
                return

            # Intercambiar con el item siguiente
            current_item = items[current_index]
            next_item = items[current_index + 1]

            logger.debug(f"Intercambiando orden: Item {current_item['id']} (orden {current_item['orden_lista']}) ↔ Item {next_item['id']} (orden {next_item['orden_lista']})")

            # Actualizar orden en BD
            db_manager.execute_update(
                "UPDATE items SET orden_lista = ? WHERE id = ?",
                (next_item['orden_lista'], current_item['id'])
            )
            db_manager.execute_update(
                "UPDATE items SET orden_lista = ? WHERE id = ?",
                (current_item['orden_lista'], next_item['id'])
            )

            logger.info(f"✅ Item {item_id} movido hacia abajo exitosamente")

            # Recargar vista
            self._reload_view()

        except Exception as e:
            logger.error(f"❌ Error moviendo item hacia abajo: {e}", exc_info=True)

    def _show_copy_success_feedback(self):
        """
        Mostrar feedback visual verde cuando se copia exitosamente

        Cambia el botón de copiar a verde por 1.5 segundos.
        """
        # Guardar estilo original
        original_style = """
            QPushButton {
                background-color: #3d3d3d;
                color: #ffffff;
                border: 1px solid #555;
                border-radius: 4px;
                font-size: 14px;
                padding: 2px;
            }
            QPushButton:hover {
                background-color: #4d4d4d;
                border-color: #666;
            }
            QPushButton:pressed {
                background-color: #2d2d2d;
            }
        """

        # Estilo de éxito (verde)
        success_style = """
            QPushButton {
                background-color: #4CAF50;
                color: #ffffff;
                border: 1px solid #45a049;
                border-radius: 4px;
                font-size: 14px;
                padding: 2px;
            }
            QPushButton:hover {
                background-color: #45a049;
                border-color: #3d8b40;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """

        # Cambiar a verde
        self.copy_button.setStyleSheet(success_style)
        self.copy_button.setText("✓")  # Cambiar icono temporalmente

        # Restaurar después de 1.5 segundos
        QTimer.singleShot(1500, lambda: self._restore_copy_button_style(original_style))

    def _restore_copy_button_style(self, original_style: str):
        """
        Restaurar estilo original del botón de copiar

        Args:
            original_style: Estilo CSS original del botón
        """
        self.copy_button.setStyleSheet(original_style)
        self.copy_button.setText("📋")  # Restaurar icono original
