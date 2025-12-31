from PyQt6.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QLabel, QPushButton, QHBoxLayout
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QShortcut, QKeySequence
from ..project_manager.styles.full_view_styles import FullViewStyles
from ..project_manager.widgets.headers import ProjectHeaderWidget, ProjectTagHeaderWidget
from ..project_manager.widgets.item_group_widget import ItemGroupWidget
from ..project_manager.widgets.common import SearchBarWidget
from .area_data_manager import AreaDataManager


class AreaFullViewPanel(QWidget):
    item_copied = pyqtSignal(dict)
    item_clicked = pyqtSignal(dict)

    def __init__(self, db_manager=None, parent=None):
        super().__init__(parent)

        # DB Manager (para pasar a ItemGroupWidget para imágenes)
        self.db_manager = db_manager

        self.data_manager = AreaDataManager(db_manager)
        self.area_data = None
        self.current_filters = []
        self.current_area_id = None
        self.tag_headers = []  # Lista para trackear los headers de tags
        self.all_collapsed = False  # Estado del botón de colapsar todo

        # Estado de búsqueda
        self.search_results = []  # Lista de widgets de items que coinciden
        self.current_result_index = -1  # Índice del resultado actual
        self.search_bar = None  # Widget de búsqueda

        self.init_ui()
        self.apply_styles()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Header con botón de colapsar todo y búsqueda
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(15, 10, 15, 10)
        header_layout.setSpacing(10)

        # Botón de colapsar/expandir todo
        self.toggle_all_btn = QPushButton("Colapsar Todo")
        self.toggle_all_btn.setFixedHeight(30)
        self.toggle_all_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggle_all_btn.clicked.connect(self._toggle_all_tags)
        self.toggle_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #2C2C2C;
                color: #32CD32;
                border: 1px solid #32CD32;
                border-radius: 4px;
                padding: 5px 15px;
                font-size: 12px;
                font-weight: 600;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QPushButton:hover {
                background-color: #3C3C3C;
                border-color: #7CFC00;
                color: #7CFC00;
            }
            QPushButton:pressed {
                background-color: #1C1C1C;
            }
        """)
        header_layout.addWidget(self.toggle_all_btn)

        # Botón para mostrar búsqueda
        self.show_search_btn = QPushButton("🔍 Buscar")
        self.show_search_btn.setFixedHeight(30)
        self.show_search_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.show_search_btn.clicked.connect(self.show_search)
        self.show_search_btn.setToolTip("Buscar en vista completa (Ctrl+F)")
        self.show_search_btn.setStyleSheet("""
            QPushButton {
                background-color: #2C2C2C;
                color: #00BFFF;
                border: 1px solid #00BFFF;
                border-radius: 4px;
                padding: 5px 15px;
                font-size: 12px;
                font-weight: 600;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QPushButton:hover {
                background-color: #3C3C3C;
                border-color: #1E90FF;
                color: #1E90FF;
            }
            QPushButton:pressed {
                background-color: #1C1C1C;
            }
        """)
        header_layout.addWidget(self.show_search_btn)

        header_layout.addStretch()

        main_layout.addWidget(header_widget)

        # Widget de búsqueda (inicialmente oculto)
        self.search_bar = SearchBarWidget()
        self.search_bar.setVisible(False)
        self.search_bar.search_text_changed.connect(self._on_search_text_changed)
        self.search_bar.next_result.connect(self._go_to_next_result)
        self.search_bar.previous_result.connect(self._go_to_previous_result)
        self.search_bar.search_closed.connect(self._on_search_closed)
        main_layout.addWidget(self.search_bar)

        # Atajo de teclado Ctrl+F
        self.search_shortcut = QShortcut(QKeySequence("Ctrl+F"), self)
        self.search_shortcut.activated.connect(self.show_search)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)
        self.content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.scroll_area.setWidget(self.content_widget)
        main_layout.addWidget(self.scroll_area)

        self.show_empty_state()

    def apply_styles(self):
        self.setStyleSheet(FullViewStyles.get_main_panel_style())

    def show_empty_state(self):
        self.clear_view()

        empty_label = QLabel("Selecciona un área para ver su contenido")
        empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_label.setStyleSheet(f"""
            color: #808080;
            font-size: 14px;
            padding: 50px;
            font-family: 'Segoe UI', Arial, sans-serif;
        """)

        self.content_layout.addWidget(empty_label)

    def load_area(self, area_id: int):
        self.current_area_id = area_id
        self.area_data = self.data_manager.get_area_full_data(area_id)

        if not self.area_data:
            self.show_empty_state()
            return

        self.render_view()

    def render_view(self):
        if not self.area_data:
            return

        self.clear_view()

        area_header = ProjectHeaderWidget()
        area_header.set_project_info(
            self.area_data['area_name'],
            self.area_data['area_icon']
        )
        self.content_layout.addWidget(area_header)

        for tag_data in self.area_data['tags']:
            self._render_tag_section(tag_data)

        if self.area_data.get('unclassified_elements'):
            self._render_unclassified_section(self.area_data['unclassified_elements'])

        if self.area_data['ungrouped_items']:
            self._render_ungrouped_section(self.area_data['ungrouped_items'])

        self.content_layout.addStretch()

    def _render_tag_section(self, tag_data: dict):
        total_items = sum(
            len(group['items'])
            for group in tag_data['groups']
        )

        tag_header = ProjectTagHeaderWidget()
        tag_header.set_tag_info(
            tag_data['tag_name'],
            tag_data['tag_color'],
            total_items
        )
        self.content_layout.addWidget(tag_header)

        # Agregar a la lista de headers para el botón de colapsar todo
        self.tag_headers.append(tag_header)

        tag_container = QWidget()
        tag_container_layout = QVBoxLayout(tag_container)
        tag_container_layout.setContentsMargins(0, 0, 0, 0)
        tag_container_layout.setSpacing(8)

        for group in tag_data['groups']:
            group_widget = ItemGroupWidget(
                group['name'],
                group['type'],
                db_manager=self.db_manager
            )

            for item_data in group['items']:
                group_widget.add_item(item_data)

            tag_container_layout.addWidget(group_widget)

        self.content_layout.addWidget(tag_container)

        tag_header.toggle_collapsed.connect(
            lambda collapsed: tag_container.setVisible(not collapsed)
        )

    def _render_unclassified_section(self, elements: list):
        tag_header = ProjectTagHeaderWidget()
        total_items = sum(len(elem['items']) for elem in elements)
        tag_header.set_tag_info("Sin Clasificar", "#808080", total_items)
        self.content_layout.addWidget(tag_header)

        # Agregar a la lista de headers para el botón de colapsar todo
        self.tag_headers.append(tag_header)

        tag_container = QWidget()
        tag_container_layout = QVBoxLayout(tag_container)
        tag_container_layout.setContentsMargins(0, 0, 0, 0)
        tag_container_layout.setSpacing(8)

        for elem in elements:
            group_widget = ItemGroupWidget(elem['name'], elem['type'], db_manager=self.db_manager)
            for item_data in elem['items']:
                group_widget.add_item(item_data)
            tag_container_layout.addWidget(group_widget)

        self.content_layout.addWidget(tag_container)

        tag_header.toggle_collapsed.connect(
            lambda collapsed: tag_container.setVisible(not collapsed)
        )

    def _render_ungrouped_section(self, items: list):
        tag_header = ProjectTagHeaderWidget()
        tag_header.set_tag_info("Otros Items", "#808080", len(items))
        self.content_layout.addWidget(tag_header)

        # Agregar a la lista de headers para el botón de colapsar todo
        self.tag_headers.append(tag_header)

        # Container para el grupo (para poder colapsar)
        tag_container = QWidget()
        tag_container_layout = QVBoxLayout(tag_container)
        tag_container_layout.setContentsMargins(0, 0, 0, 0)
        tag_container_layout.setSpacing(8)

        group_widget = ItemGroupWidget("Sin clasificar", "other", db_manager=self.db_manager)
        for item_data in items:
            group_widget.add_item(item_data)

        tag_container_layout.addWidget(group_widget)
        self.content_layout.addWidget(tag_container)

        # Conectar colapso/expansión
        tag_header.toggle_collapsed.connect(
            lambda collapsed: tag_container.setVisible(not collapsed)
        )

    def apply_filters(self, tag_filters: list[str], match_mode: str = 'OR'):
        self.current_filters = tag_filters

        if not self.area_data:
            return

        if not tag_filters:
            self.render_view()
            return

        filtered_data = self.data_manager.filter_by_area_tags(
            self.area_data,
            tag_filters,
            match_mode
        )

        original_data = self.area_data
        self.area_data = filtered_data
        self.render_view()
        self.area_data = original_data

        visible_tags = [tag['tag_name'] for tag in filtered_data['tags']]
        print(f"✓ Filtros aplicados ({match_mode}): {tag_filters}")
        print(f"  Tags visibles: {visible_tags}")

    def clear_filters(self):
        self.current_filters = []
        if self.area_data:
            self.render_view()
            print("✓ Filtros limpiados - Mostrando todos los tags")

    def refresh_view(self):
        if self.current_area_id:
            self.load_area(self.current_area_id)

    def _toggle_all_tags(self):
        """
        Colapsar o expandir todos los tags

        Alterna entre colapsar todos los tags y expandirlos todos.
        """
        # Alternar estado
        self.all_collapsed = not self.all_collapsed

        # Aplicar a todos los tag headers
        for tag_header in self.tag_headers:
            tag_header.set_collapsed(self.all_collapsed)

        # Actualizar texto del botón
        if self.all_collapsed:
            self.toggle_all_btn.setText("Expandir Todo")
        else:
            self.toggle_all_btn.setText("Colapsar Todo")

    def show_search(self):
        """
        Mostrar widget de búsqueda y dar foco al campo de texto

        Si la búsqueda ya está visible, da foco al campo.
        """
        self.search_bar.setVisible(True)
        self.search_bar.focus_search_input()

    def _on_search_text_changed(self, text: str):
        """
        Manejar cambio de texto de búsqueda

        Busca todos los items que coincidan y resalta el texto.

        Args:
            text: Texto de búsqueda
        """
        # Limpiar búsqueda anterior
        self._clear_search_highlights()
        self.search_results.clear()
        self.current_result_index = -1

        if not text:
            self.search_bar.update_results(0, 0)
            return

        # Buscar en todos los widgets de items
        from ..project_manager.widgets.items.base_item_widget import BaseItemWidget

        all_item_widgets = self.content_widget.findChildren(BaseItemWidget)

        for item_widget in all_item_widgets:
            if item_widget.has_match(text):
                self.search_results.append(item_widget)
                item_widget.highlight_text(text)

        # Actualizar contador
        total_results = len(self.search_results)
        if total_results > 0:
            self.current_result_index = 0
            self.search_bar.update_results(0, total_results)
            # Scroll al primer resultado
            self._scroll_to_item(self.search_results[0])
        else:
            self.search_bar.update_results(0, 0)

    def _go_to_next_result(self):
        """
        Ir al siguiente resultado de búsqueda

        Navega al siguiente item que coincide y hace scroll para mostrarlo.
        """
        if not self.search_results:
            return

        # Incrementar índice (con wrap-around)
        self.current_result_index = (self.current_result_index + 1) % len(self.search_results)

        # Actualizar contador y scroll
        self.search_bar.update_results(self.current_result_index, len(self.search_results))
        self._scroll_to_item(self.search_results[self.current_result_index])

    def _go_to_previous_result(self):
        """
        Ir al resultado anterior de búsqueda

        Navega al resultado anterior y hace scroll para mostrarlo.
        """
        if not self.search_results:
            return

        # Decrementar índice (con wrap-around)
        self.current_result_index = (self.current_result_index - 1) % len(self.search_results)

        # Actualizar contador y scroll
        self.search_bar.update_results(self.current_result_index, len(self.search_results))
        self._scroll_to_item(self.search_results[self.current_result_index])

    def _on_search_closed(self):
        """
        Cerrar búsqueda y limpiar resaltados

        Oculta el widget de búsqueda y limpia todos los resaltados.
        """
        self.search_bar.setVisible(False)
        self._clear_search_highlights()
        self.search_results.clear()
        self.current_result_index = -1

    def _clear_search_highlights(self):
        """
        Limpiar todos los resaltados de búsqueda

        Recorre todos los widgets de items y limpia sus resaltados.
        """
        from ..project_manager.widgets.items.base_item_widget import BaseItemWidget

        all_item_widgets = self.content_widget.findChildren(BaseItemWidget)
        for item_widget in all_item_widgets:
            item_widget.clear_highlight()

    def _scroll_to_item(self, item_widget):
        """
        Hacer scroll para mostrar un item específico

        Args:
            item_widget: Widget del item a mostrar
        """
        if not item_widget:
            return

        # Obtener la posición del widget en el scroll area
        item_pos = item_widget.mapTo(self.content_widget, item_widget.rect().topLeft())

        # Hacer scroll para mostrar el item (centrado si es posible)
        viewport_height = self.scroll_area.viewport().height()
        item_height = item_widget.height()

        # Calcular posición de scroll centrada
        scroll_value = item_pos.y() - (viewport_height // 2) + (item_height // 2)

        # Animar scroll suavemente
        self.scroll_area.verticalScrollBar().setValue(scroll_value)

    def clear_view(self):
        # Limpiar búsqueda
        if self.search_bar and self.search_bar.isVisible():
            self._on_search_closed()

        # Limpiar lista de headers
        self.tag_headers.clear()

        while self.content_layout.count():
            child = self.content_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def get_current_area_id(self) -> int:
        return self.current_area_id

    def has_active_filters(self) -> bool:
        return len(self.current_filters) > 0
