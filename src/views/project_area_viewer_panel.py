"""
Visor Compacto de Proyectos y Áreas

Ventana flotante de SOLO LECTURA para visualizar y navegar elementos de Proyectos/Áreas.

Características:
- Solo lectura: NO permite crear ni editar proyectos, áreas, tags o items
- Dimensiones: 450px ancho × altura completa de pantalla
- Frameless window, siempre encima
- AppBar API de Windows para reservar espacio
- Posicionamiento junto al sidebar (igual que Creador Masivo)
- Proyecto y Área mutuamente excluyentes
- Scroll vertical para muchos elementos
- Filtrado por tags + búsqueda integrada (Ctrl+F)

IMPORTANTE:
- Solo se puede seleccionar Proyecto O Área, NUNCA ambos simultáneamente
- Al seleccionar uno, el otro se resetea automáticamente

Versión: 1.0
Fecha: 2025-12-21
"""

from typing import Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QScrollArea, QApplication, QInputDialog, QMessageBox, QLineEdit
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QPoint
from PyQt6.QtGui import QFont, QShortcut, QKeySequence
from src.views.widgets.context_selector_compact import ContextSelectorCompact
from src.views.widgets.tag_filter_chips import TagFilterChips
from src.views.project_manager.widgets.common.search_bar_widget import SearchBarWidget
from src.views.project_manager.widgets.headers import ProjectHeaderWidget, ProjectTagHeaderWidget
from src.views.project_manager.widgets.item_group_widget import ItemGroupWidget
from src.views.project_manager.project_data_manager import ProjectDataManager
from src.views.dialogs.add_item_dialog import AddItemDialog
from src.core.project_element_tag_manager import ProjectElementTagManager
from src.core.area_element_tag_manager import AreaElementTagManager
import logging
import sys
import ctypes
from ctypes import wintypes

logger = logging.getLogger(__name__)

# === CONSTANTES DE APPBAR API ===
ABM_NEW = 0x00000000
ABM_REMOVE = 0x00000001
ABM_QUERYPOS = 0x00000002
ABM_SETPOS = 0x00000003
ABE_RIGHT = 2  # Lado derecho de la pantalla


class APPBARDATA(ctypes.Structure):
    """Estructura para AppBar API de Windows"""
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("hWnd", wintypes.HWND),
        ("uCallbackMessage", wintypes.UINT),
        ("uEdge", wintypes.UINT),
        ("rc", wintypes.RECT),
        ("lParam", wintypes.LPARAM),
    ]


# === CONSTANTES DE DIMENSIONES ===
VIEWER_WIDTH = 450  # Mismo ancho que Creador Masivo
VIEWER_MIN_HEIGHT = 400
SIDEBAR_WIDTH = 70  # Ancho estándar del sidebar principal
TOTAL_RESERVED_WIDTH = VIEWER_WIDTH + SIDEBAR_WIDTH  # 520px total


class ProjectAreaViewerPanel(QWidget):
    """
    Visor Compacto de Proyectos y Áreas (SOLO LECTURA)

    Ventana flotante para visualizar elementos de Proyectos/Áreas con:
    - Selectores de Proyecto/Área (mutuamente excluyentes)
    - Tags filtrables (click para filtrar)
    - Vista jerárquica similar a Vista Completa de Proyectos
    - Búsqueda integrada (Ctrl+F)
    - Scroll vertical para muchos elementos

    NO permite crear ni editar proyectos, áreas, tags o items.

    Señales:
        item_copied(dict): Emitida cuando se copia un item
        closed: Emitida cuando se cierra la ventana
    """

    # Señales
    item_copied = pyqtSignal(dict)  # Item copiado
    closed = pyqtSignal()  # Ventana cerrada

    def __init__(self, db_manager, parent=None):
        """
        Inicializa el Visor de Proyectos/Áreas

        Args:
            db_manager: Instancia de DBManager
            parent: Widget padre (generalmente el sidebar principal)
        """
        super().__init__(parent)
        self.db = db_manager
        self.appbar_registered = False  # Estado del AppBar
        self.drag_position = QPoint()  # Para dragging de ventana

        # Data manager ✅ FASE 6
        self.data_manager = ProjectDataManager(db_manager)

        # Tag managers (✨ NUEVO - para creación de tags)
        self.project_tag_manager = ProjectElementTagManager(db_manager) if db_manager else None
        self.area_tag_manager = AreaElementTagManager(db_manager) if db_manager else None

        # Diálogo de agregar item (✨ NUEVO)
        self.add_item_dialog = None
        self.current_lista_id = None  # Lista actualmente seleccionada para agregar items

        # Estado interno
        self.current_project_id = None
        self.current_area_id = None
        self.current_filters = []  # Tags de filtrado activos
        self.search_results = []  # Resultados de búsqueda
        self.current_result_index = -1
        self.project_data = None  # Datos del proyecto/área actual
        self.tag_headers = []  # Lista de headers de tags (para colapsar todo)

        # Configuración de ventana
        self.setWindowTitle("📋 Listar Proyectos/Áreas")
        self.setMinimumSize(VIEWER_WIDTH, VIEWER_MIN_HEIGHT)

        # Frameless window (Tool para no aparecer en barra de tareas)
        self.setWindowFlags(
            Qt.WindowType.Tool |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )

        self._setup_ui()
        self._apply_styles()
        self._setup_shortcuts()  # ✅ FASE 4: Atajos de teclado
        self._connect_signals()
        self._load_available_data()

        logger.info("ProjectAreaViewerPanel inicializado")

    def _setup_ui(self):
        """Configura la interfaz del visor"""
        # Layout principal
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header con barra de título personalizada
        header = self._create_header()
        layout.addWidget(header)

        # Sección Contexto (Proyecto/Área dropdowns) ✅ FASE 2
        self.context_selector = ContextSelectorCompact()
        layout.addWidget(self.context_selector)

        # Sección Tags de Proyecto/Área (chips clickeables) ✅ FASE 3
        self.tag_filter_chips = TagFilterChips()
        layout.addWidget(self.tag_filter_chips)

        # Controles de Vista (Colapsar Todo, Buscar) ✅ FASE 4
        view_controls = self._create_view_controls()
        layout.addWidget(view_controls)

        # Barra de Búsqueda (oculta por defecto) ✅ FASE 5
        self.search_bar = SearchBarWidget()
        self.search_bar.setVisible(False)  # Oculta por defecto
        layout.addWidget(self.search_bar)

        # Área de Contenido con Scroll ✅ FASE 6
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #1e1e1e;
            }
            QScrollBar:vertical {
                background-color: #2d2d2d;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #555;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #666;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

        # Contenedor de contenido (dentro del scroll area)
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)
        self.content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Establecer widget de contenido en scroll area
        self.scroll_area.setWidget(self.content_widget)
        layout.addWidget(self.scroll_area)

        # Mostrar estado vacío inicial
        self._show_empty_state()

    def _create_header(self) -> QWidget:
        """
        Crea el header compacto con barra de título arrastrable

        Returns:
            QWidget con el header completo
        """
        header = QWidget()
        header.setFixedHeight(35)
        header.setStyleSheet("background-color: #2d2d2d; border-bottom: 1px solid #444;")

        layout = QHBoxLayout(header)
        layout.setContentsMargins(10, 0, 10, 0)
        layout.setSpacing(8)

        # Título (arrastrable)
        title = QLabel("📋 Listar Proyectos/Áreas")
        title.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        title.setStyleSheet("color: #ffffff;")
        layout.addWidget(title)

        layout.addStretch()

        # Botón actualizar/refrescar
        self.refresh_btn = QPushButton("🔄")
        self.refresh_btn.setFixedSize(20, 20)
        self.refresh_btn.setToolTip("Actualizar datos")
        self.refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.refresh_btn.clicked.connect(self._on_refresh_clicked)
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #2d5d2e;
                color: #00ff88;
                border: none;
                font-size: 12px;
                font-weight: bold;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #3a7a3c;
            }
            QPushButton:pressed {
                background-color: #1a4d2e;
            }
        """)
        layout.addWidget(self.refresh_btn)

        # Botón minimizar
        minimize_btn = QPushButton("−")
        minimize_btn.setFixedSize(20, 20)
        minimize_btn.setToolTip("Ocultar ventana")
        minimize_btn.clicked.connect(self.hide)
        minimize_btn.setStyleSheet("""
            QPushButton {
                background-color: #555;
                color: #fff;
                border: none;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #666;
            }
        """)
        layout.addWidget(minimize_btn)

        # Botón cerrar
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(20, 20)
        close_btn.setToolTip("Cerrar")
        close_btn.clicked.connect(self._on_close_clicked)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #d32f2f;
                color: #fff;
                border: none;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #b71c1c;
            }
        """)
        layout.addWidget(close_btn)

        # Hacer header arrastrable
        header.mousePressEvent = self._start_drag
        header.mouseMoveEvent = self._do_drag
        title.mousePressEvent = self._start_drag
        title.mouseMoveEvent = self._do_drag

        return header

    def _create_view_controls(self) -> QWidget:
        """
        Crea la sección de controles de vista (Colapsar Todo, Buscar)

        Returns:
            QWidget con los controles
        """
        controls_widget = QWidget()
        controls_widget.setFixedHeight(60)

        layout = QHBoxLayout(controls_widget)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(10)

        # Botón "Colapsar Todo"
        self.collapse_all_btn = QPushButton("📁 Colapsar Todo")
        self.collapse_all_btn.setFixedHeight(35)
        self.collapse_all_btn.setMinimumWidth(150)
        self.collapse_all_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.collapse_all_btn.setToolTip("Colapsar todos los elementos del proyecto/área")
        self.collapse_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #2d5d2e;
                color: #00ff88;
                border: 1px solid #00ff88;
                border-radius: 6px;
                font-size: 11px;
                font-weight: 600;
                padding: 8px 12px;
            }
            QPushButton:hover {
                background-color: #3a7a3c;
                border-color: #7CFC00;
            }
            QPushButton:pressed {
                background-color: #1a4d2e;
            }
            QPushButton:disabled {
                background-color: #3d3d3d;
                color: #666;
                border-color: #555;
            }
        """)
        layout.addWidget(self.collapse_all_btn)

        # Botón "Buscar"
        self.search_btn = QPushButton("🔍 Buscar")
        self.search_btn.setFixedHeight(35)
        self.search_btn.setMinimumWidth(120)
        self.search_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.search_btn.setToolTip("Buscar elementos (Ctrl+F)")
        self.search_btn.setStyleSheet("""
            QPushButton {
                background-color: #1a4d7a;
                color: #00BFFF;
                border: 1px solid #00BFFF;
                border-radius: 6px;
                font-size: 11px;
                font-weight: 600;
                padding: 8px 12px;
            }
            QPushButton:hover {
                background-color: #2a5d8a;
                border-color: #87CEEB;
            }
            QPushButton:pressed {
                background-color: #0a3d6a;
            }
            QPushButton:disabled {
                background-color: #3d3d3d;
                color: #666;
                border-color: #555;
            }
        """)
        layout.addWidget(self.search_btn)

        layout.addStretch()

        return controls_widget

    def _apply_styles(self):
        """Aplica estilos CSS oscuros al visor"""
        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e1e;
                color: #ffffff;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
        """)

    def _setup_shortcuts(self):
        """Configura atajos de teclado"""
        # Ctrl+F: Mostrar búsqueda
        search_shortcut = QShortcut(QKeySequence("Ctrl+F"), self)
        search_shortcut.activated.connect(self._on_search_shortcut)
        logger.debug("Atajo Ctrl+F configurado para búsqueda")

    def _connect_signals(self):
        """Conecta señales internas"""
        # Señales del context selector
        self.context_selector.project_changed.connect(self._on_project_selected)
        self.context_selector.area_changed.connect(self._on_area_selected)

        # Señales de creación del context selector (✨ NUEVO)
        self.context_selector.create_project_clicked.connect(self._on_create_project)
        self.context_selector.create_area_clicked.connect(self._on_create_area)

        # Señales de tag filter chips
        self.tag_filter_chips.tags_changed.connect(self._on_tags_changed)

        # Señal de creación de tag (✨ NUEVO)
        self.tag_filter_chips.create_tag_clicked.connect(self._on_create_project_tag)

        # Señales de controles de vista ✅ FASE 4
        self.collapse_all_btn.clicked.connect(self._on_collapse_all_clicked)
        self.search_btn.clicked.connect(self._on_search_clicked)

        # Señales de búsqueda ✅ FASE 5
        self.search_bar.search_text_changed.connect(self._on_search_text_changed)
        self.search_bar.next_result.connect(self._on_next_result)
        self.search_bar.previous_result.connect(self._on_previous_result)
        self.search_bar.search_closed.connect(self._on_search_closed)

    def _load_available_data(self):
        """Carga datos disponibles (proyectos y áreas) desde la BD"""
        if not self.db:
            logger.warning("No hay DBManager - no se pueden cargar datos")
            return

        try:
            # Cargar proyectos
            logger.debug("🔍 Llamando a db.get_all_projects()...")
            projects = self.db.get_all_projects()
            logger.debug(f"📦 get_all_projects() retornó: {projects}")
            logger.debug(f"📦 Tipo: {type(projects)}, Longitud: {len(projects) if projects else 0}")

            if projects:
                logger.debug(f"📦 Primer proyecto (muestra): {projects[0]}")

            projects_data = [(p['id'], p['name']) for p in projects]
            logger.debug(f"📦 projects_data procesada: {projects_data}")

            self.context_selector.load_projects(projects_data)
            logger.info(f"✅ Cargados {len(projects_data)} proyectos en dropdown")

            # Cargar áreas
            logger.debug("🔍 Llamando a db.get_all_areas()...")
            areas = self.db.get_all_areas()
            logger.debug(f"📦 get_all_areas() retornó: {areas}")
            logger.debug(f"📦 Tipo: {type(areas)}, Longitud: {len(areas) if areas else 0}")

            if areas:
                logger.debug(f"📦 Primera área (muestra): {areas[0]}")

            areas_data = [(a['id'], a['name']) for a in areas]
            logger.debug(f"📦 areas_data procesada: {areas_data}")

            self.context_selector.load_areas(areas_data)
            logger.info(f"✅ Cargadas {len(areas_data)} áreas en dropdown")

        except Exception as e:
            logger.error(f"❌ Error cargando datos disponibles: {e}", exc_info=True)

    def _on_close_clicked(self):
        """Callback cuando se hace click en botón cerrar"""
        logger.info("Visor close requested - hiding")
        self.hide()

    # === MÉTODOS DE RENDERIZADO (FASE 6) ===

    def _show_empty_state(self):
        """Mostrar estado vacío cuando no hay proyecto/área seleccionado"""
        self._clear_view()

        empty_label = QLabel("Selecciona un Proyecto o Área para ver su contenido")
        empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_label.setStyleSheet("""
            color: #808080;
            font-size: 14px;
            padding: 50px;
            font-family: 'Segoe UI', Arial, sans-serif;
        """)
        self.content_layout.addWidget(empty_label)

    def _clear_view(self):
        """Limpiar todos los widgets del área de contenido"""
        # Limpiar lista de headers de tags
        self.tag_headers.clear()

        # Eliminar todos los widgets del layout
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        logger.debug("Vista limpiada")

    # === CALLBACKS DE SELECCIÓN ===

    def _on_project_selected(self, project_id):
        """
        Callback cuando se selecciona un proyecto

        CRÍTICO: El área ya fue reseteada automáticamente por ContextSelectorCompact

        Args:
            project_id: ID del proyecto seleccionado (o None si se deseleccionó)
        """
        if project_id:
            logger.info(f"Proyecto seleccionado: {project_id}")
            self.current_project_id = project_id
            self.current_area_id = None  # Asegurar que área está en None

            # Limpiar selección de tags anteriores
            self.tag_filter_chips.clear_selection()
            self.current_filters = []

            # Cargar tags del proyecto ✅ FASE 3
            self._load_project_tags(project_id)

            # Cargar y renderizar proyecto ✅ FASE 6
            self.load_project(project_id)

        else:
            logger.debug("Proyecto deseleccionado")
            self.current_project_id = None
            self.tag_filter_chips.clear()  # Limpiar tags
            self._show_empty_state()

    def _on_area_selected(self, area_id):
        """
        Callback cuando se selecciona un área

        CRÍTICO: El proyecto ya fue reseteado automáticamente por ContextSelectorCompact

        Args:
            area_id: ID del área seleccionada (o None si se deseleccionó)
        """
        if area_id:
            logger.info(f"Área seleccionada: {area_id}")
            self.current_area_id = area_id
            self.current_project_id = None  # Asegurar que proyecto está en None

            # Limpiar selección de tags anteriores
            self.tag_filter_chips.clear_selection()
            self.current_filters = []

            # Cargar tags del área ✅ FASE 3
            self._load_area_tags(area_id)

            # Cargar y renderizar área ✅ FASE 6
            self.load_area(area_id)

        else:
            logger.debug("Área deseleccionada")
            self.current_area_id = None
            self.tag_filter_chips.clear()  # Limpiar tags
            self._show_empty_state()

    def _on_tags_changed(self, tag_names: list):
        """
        Callback cuando cambian los tags seleccionados

        Aplica filtrado por tags y re-renderiza la vista.

        Args:
            tag_names: Lista de nombres de tags seleccionados
        """
        self.current_filters = tag_names
        logger.info(f"Tags de filtro actualizados: {tag_names}")

        # Aplicar filtros y re-renderizar
        self.apply_tag_filters(tag_names)

    def _load_project_tags(self, project_id: int):
        """
        Cargar tags reales específicos del proyecto desde BD

        Args:
            project_id: ID del proyecto
        """
        if not self.db:
            logger.warning("No hay DBManager - no se pueden cargar tags")
            return

        try:
            logger.info(f"Cargando tags del proyecto {project_id}")

            # Obtener tags reales que tienen elementos asociados al proyecto
            conn = self.db.connect()
            cursor = conn.execute("""
                SELECT DISTINCT pet.id, pet.name, pet.color
                FROM project_element_tag_associations ta
                JOIN project_element_tags pet ON ta.tag_id = pet.id
                JOIN project_relations pr ON ta.project_relation_id = pr.id
                WHERE pr.project_id = ?
                ORDER BY pet.name ASC
            """, (project_id,))

            tags_data = []
            for row in cursor.fetchall():
                tags_data.append({
                    'name': row['name'],
                    'color': row['color'] if row['color'] else '#808080'
                })

            if tags_data:
                self.tag_filter_chips.load_tags(tags_data)
                logger.info(f"Cargados {len(tags_data)} tags del proyecto")
            else:
                self.tag_filter_chips.clear()
                logger.info("Proyecto sin tags")

        except Exception as e:
            logger.error(f"Error cargando tags del proyecto: {e}")
            self.tag_filter_chips.clear()

    def _load_area_tags(self, area_id: int):
        """
        Cargar tags reales específicos del área desde BD

        Args:
            area_id: ID del área
        """
        if not self.db:
            logger.warning("No hay DBManager - no se pueden cargar tags")
            return

        try:
            logger.info(f"Cargando tags del área {area_id}")

            # Obtener tags reales que tienen elementos asociados al área
            conn = self.db.connect()
            cursor = conn.execute("""
                SELECT DISTINCT aet.id, aet.name, aet.color
                FROM area_element_tag_associations ta
                JOIN area_element_tags aet ON ta.tag_id = aet.id
                JOIN area_relations ar ON ta.area_relation_id = ar.id
                WHERE ar.area_id = ?
                ORDER BY aet.name ASC
            """, (area_id,))

            tags_data = []
            for row in cursor.fetchall():
                tags_data.append({
                    'name': row['name'],
                    'color': row['color'] if row['color'] else '#808080'
                })

            if tags_data:
                self.tag_filter_chips.load_tags(tags_data)
                logger.info(f"Cargados {len(tags_data)} tags del área")
            else:
                self.tag_filter_chips.clear()
                logger.info("Área sin tags")

        except Exception as e:
            logger.error(f"Error cargando tags del área: {e}")
            self.tag_filter_chips.clear()

    # === CALLBACKS DE CONTROLES DE VISTA (FASE 4) ===

    def _on_collapse_all_clicked(self):
        """
        Callback cuando se hace click en "Colapsar Todo"

        Alterna entre colapsar y expandir todos los headers de elementos.
        """
        self.toggle_all_headers()
        logger.debug("Colapsar Todo clicked")

    def _on_search_clicked(self):
        """
        Callback cuando se hace click en botón "🔍 Buscar"

        Muestra/oculta la barra de búsqueda.
        """
        self.show_search()
        logger.debug("Búsqueda clicked")

    def _on_search_shortcut(self):
        """
        Callback cuando se presiona Ctrl+F

        Muestra la barra de búsqueda.
        """
        self.show_search()
        logger.debug("Ctrl+F pressed - mostrando búsqueda")

    def toggle_all_headers(self):
        """
        Alternar entre colapsar y expandir todos los headers de elementos
        """
        if not self.tag_headers:
            logger.debug("No hay headers para colapsar/expandir")
            return

        # Determinar nuevo estado (opuesto al texto actual del botón)
        current_text = self.collapse_all_btn.text()
        should_collapse = "Colapsar" in current_text

        # Aplicar a todos los headers
        for header in self.tag_headers:
            if should_collapse:
                # Colapsar si no está colapsado
                if not header.is_tag_collapsed():
                    header.toggle_collapse()
            else:
                # Expandir si está colapsado
                if header.is_tag_collapsed():
                    header.toggle_collapse()

        # Actualizar texto del botón
        if should_collapse:
            self.collapse_all_btn.setText("📂 Expandir Todo")
            logger.debug(f"Todos los headers colapsados ({len(self.tag_headers)} headers)")
        else:
            self.collapse_all_btn.setText("📁 Colapsar Todo")
            logger.debug(f"Todos los headers expandidos ({len(self.tag_headers)} headers)")

    # === CALLBACKS DE BÚSQUEDA (FASE 5) ===

    def _on_search_text_changed(self, search_text: str):
        """
        Callback cuando cambia el texto de búsqueda

        Busca el texto en el área de contenido y resalta los resultados.

        Args:
            search_text: Texto a buscar
        """
        if not search_text:
            # Limpiar búsqueda
            self.search_results = []
            self.current_result_index = -1
            self.search_bar.update_results(0, 0)
            self._clear_search_highlights()
            logger.debug("Búsqueda limpiada")
            return

        # Buscar en todos los widgets de items del contenido
        logger.info(f"Buscando: '{search_text}'")
        self.search_results = []
        search_lower = search_text.lower()

        # Recorrer todos los widgets buscando ItemGroupWidget
        self._search_in_layout(self.content_layout, search_lower)

        # Actualizar contador
        if self.search_results:
            self.current_result_index = 0
            self.search_bar.update_results(0, len(self.search_results))
            self._scroll_to_result(0)
            logger.info(f"Encontrados {len(self.search_results)} resultados")
        else:
            self.current_result_index = -1
            self.search_bar.update_results(0, 0)
            logger.info("No se encontraron resultados")

    def _search_in_layout(self, layout, search_text: str):
        """
        Buscar recursivamente en un layout

        Args:
            layout: Layout donde buscar
            search_text: Texto a buscar
        """
        # Validar que el layout no sea None
        if layout is None:
            return

        for i in range(layout.count()):
            item = layout.itemAt(i)
            if not item:
                continue

            widget = item.widget()
            if not widget:
                continue

            # Si es un ItemGroupWidget, buscar en sus items
            if hasattr(widget, 'items'):
                for item_widget in widget.items:
                    # Usar el método has_match del widget si existe
                    if hasattr(item_widget, 'has_match') and item_widget.has_match(search_text):
                        self.search_results.append(item_widget)
                        # Resaltar texto si el widget lo soporta
                        if hasattr(item_widget, 'highlight_text'):
                            item_widget.highlight_text(search_text)
                    else:
                        # Asegurar que se limpie si no coincide (por si acaso)
                        if hasattr(item_widget, 'clear_highlight'):
                            item_widget.clear_highlight()

            # Si tiene layout, buscar recursivamente
            # Verificar si layout es un método o un atributo
            try:
                child_layout = widget.layout() if callable(widget.layout) else widget.layout
                if child_layout:
                    self._search_in_layout(child_layout, search_text)
            except (AttributeError, TypeError):
                pass  # Widget no tiene layout o no es accesible

    def _clear_search_highlights(self):
        """Limpiar resaltado de búsqueda en todos los items"""
        # Recorrer todo el layout para limpiar
        self._clear_highlights_recursive(self.content_layout)

    def _clear_highlights_recursive(self, layout):
        """Helper recursivo para limpiar resaltados"""
        # Validar que el layout no sea None
        if layout is None:
            return

        for i in range(layout.count()):
            item = layout.itemAt(i)
            if not item:
                continue

            widget = item.widget()
            if not widget:
                continue

            # Si es un ItemGroupWidget, limpiar sus items
            if hasattr(widget, 'items'):
                for item_widget in widget.items:
                    if hasattr(item_widget, 'clear_highlight'):
                        item_widget.clear_highlight()

            # Recursión
            # Verificar si layout es un método o un atributo
            try:
                child_layout = widget.layout() if callable(widget.layout) else widget.layout
                if child_layout:
                    self._clear_highlights_recursive(child_layout)
            except (AttributeError, TypeError):
                pass  # Widget no tiene layout o no es accesible

    def _scroll_to_result(self, index: int):
        """
        Hacer scroll al resultado especificado

        Args:
            index: Índice del resultado (0-based)
        """
        if not self.search_results or index < 0 or index >= len(self.search_results):
            return

        # Obtener widget del resultado
        result_widget = self.search_results[index]

        # Hacer scroll para que sea visible
        self.scroll_area.ensureWidgetVisible(result_widget, 0, 100)
        logger.debug(f"Scroll a resultado {index + 1}/{len(self.search_results)}")

    def _on_next_result(self):
        """
        Navegar al siguiente resultado de búsqueda

        Actualiza el índice actual y hace scroll al elemento.
        """
        if not self.search_results:
            logger.debug("No hay resultados para navegar")
            return

        # Avanzar al siguiente resultado (con wrap)
        self.current_result_index = (self.current_result_index + 1) % len(self.search_results)

        # Actualizar contador
        self.search_bar.update_results(self.current_result_index, len(self.search_results))

        # Hacer scroll al resultado
        self._scroll_to_result(self.current_result_index)
        logger.debug(f"Siguiente resultado: {self.current_result_index + 1}/{len(self.search_results)}")

    def _on_previous_result(self):
        """
        Navegar al resultado anterior de búsqueda

        Actualiza el índice actual y hace scroll al elemento.
        """
        if not self.search_results:
            logger.debug("No hay resultados para navegar")
            return

        # Retroceder al resultado anterior (con wrap)
        self.current_result_index = (self.current_result_index - 1) % len(self.search_results)

        # Actualizar contador
        self.search_bar.update_results(self.current_result_index, len(self.search_results))

        # Hacer scroll al resultado
        self._scroll_to_result(self.current_result_index)
        logger.debug(f"Resultado anterior: {self.current_result_index + 1}/{len(self.search_results)}")

    def _on_search_closed(self):
        """
        Callback cuando se cierra la búsqueda

        Oculta la barra de búsqueda y limpia los resultados.
        """
        self.hide_search()
        logger.debug("Búsqueda cerrada por usuario")

    def _on_refresh_clicked(self):
        """
        Callback cuando se hace click en el botón "Actualizar"

        Refresca todos los datos:
        1. Recarga lista de proyectos y áreas en dropdowns
        2. Si hay proyecto/área seleccionado, recarga sus datos y tags
        3. Re-renderiza la vista
        """
        logger.info("🔄 Actualizando datos del visor...")

        try:
            # 1. Recargar lista de proyectos y áreas disponibles
            self._load_available_data()

            # 2. Refrescar contenido actual si hay algo seleccionado
            if self.current_project_id:
                # Recargar tags del proyecto
                self._load_project_tags(self.current_project_id)
                # Recargar datos y re-renderizar
                self.load_project(self.current_project_id)
                logger.info(f"✅ Proyecto {self.current_project_id} actualizado")

            elif self.current_area_id:
                # Recargar tags del área
                self._load_area_tags(self.current_area_id)
                # Recargar datos y re-renderizar
                self.load_area(self.current_area_id)
                logger.info(f"✅ Área {self.current_area_id} actualizada")

            else:
                # No hay nada seleccionado, solo se actualizaron los dropdowns
                logger.info("✅ Dropdowns actualizados (no hay proyecto/área seleccionado)")

            logger.info("🔄 Actualización completada")

        except Exception as e:
            logger.error(f"❌ Error al actualizar datos: {e}", exc_info=True)

    # === DRAGGING DE VENTANA ===

    def _start_drag(self, event):
        """Iniciar arrastre de ventana"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def _do_drag(self, event):
        """Realizar arrastre de ventana"""
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    # === POSICIONAMIENTO ===

    def position_window(self, sidebar_window=None):
        """
        Posicionar ventana a la izquierda del sidebar, completamente pegada

        Args:
            sidebar_window: Referencia al widget del sidebar principal (opcional)
        """
        try:
            if sidebar_window:
                # Método 1: Usar posición real del sidebar
                sidebar_x = sidebar_window.x()
                sidebar_y = sidebar_window.y()

                # Posicionar justo a la izquierda del sidebar, SIN GAP
                x = sidebar_x - VIEWER_WIDTH
                y = sidebar_y
            else:
                # Método 2: Fallback - calcular basado en geometría de pantalla
                screen = QApplication.primaryScreen()
                if not screen:
                    logger.warning("No se pudo obtener pantalla")
                    return

                screen_geometry = screen.availableGeometry()
                x = screen_geometry.width() - VIEWER_WIDTH - SIDEBAR_WIDTH
                y = screen_geometry.y()

            # Obtener altura de pantalla
            screen = QApplication.primaryScreen()
            if screen:
                height = screen.availableGeometry().height()
            else:
                height = VIEWER_MIN_HEIGHT

            self.setGeometry(x, y, VIEWER_WIDTH, height)
            logger.info(f"Visor posicionado (pegado al sidebar): x={x}, y={y}, w={VIEWER_WIDTH}, h={height}")

        except Exception as e:
            logger.error(f"Error posicionando ventana: {e}")

    # === APPBAR API ===

    def register_appbar(self):
        """
        Registra la ventana como AppBar de Windows para reservar espacio permanentemente.

        Esto empuja las ventanas maximizadas para que no cubran el visor + sidebar.
        Reserva 520px desde el borde derecho (450px visor + 70px sidebar).
        """
        try:
            if sys.platform != 'win32':
                logger.warning("AppBar solo funciona en Windows")
                return

            if self.appbar_registered:
                logger.debug("AppBar ya está registrada")
                return

            # Obtener handle de la ventana
            hwnd = int(self.winId())

            # Obtener geometría de la pantalla
            screen = QApplication.primaryScreen()
            screen_geometry = screen.availableGeometry()

            # Crear estructura APPBARDATA
            abd = APPBARDATA()
            abd.cbSize = ctypes.sizeof(APPBARDATA)
            abd.hWnd = hwnd
            abd.uCallbackMessage = 0
            abd.uEdge = ABE_RIGHT  # Lado derecho de la pantalla

            # Definir el rectángulo del AppBar
            # Reservar espacio para: Visor (450px) + Sidebar (70px) = 520px desde el borde derecho
            abd.rc.left = self.x()  # Desde donde empieza el visor
            abd.rc.top = screen_geometry.y()
            abd.rc.right = screen_geometry.x() + screen_geometry.width()  # Hasta el borde derecho
            abd.rc.bottom = screen_geometry.y() + screen_geometry.height()

            # Registrar el AppBar
            result = ctypes.windll.shell32.SHAppBarMessage(ABM_NEW, ctypes.byref(abd))
            if result:
                logger.info(f"Visor registrado como AppBar - reservando {TOTAL_RESERVED_WIDTH}px desde borde derecho")
                self.appbar_registered = True

                # Consultar y establecer posición para reservar espacio
                ctypes.windll.shell32.SHAppBarMessage(ABM_QUERYPOS, ctypes.byref(abd))
                ctypes.windll.shell32.SHAppBarMessage(ABM_SETPOS, ctypes.byref(abd))
            else:
                logger.warning("No se pudo registrar como AppBar")

        except Exception as e:
            logger.error(f"Error al registrar como AppBar: {e}")

    def unregister_appbar(self):
        """
        Desregistra la ventana como AppBar al cerrar u ocultar.

        Esto libera el espacio reservado en el escritorio.
        """
        try:
            if not self.appbar_registered:
                return

            # Obtener handle de la ventana
            hwnd = int(self.winId())

            # Crear estructura APPBARDATA
            abd = APPBARDATA()
            abd.cbSize = ctypes.sizeof(APPBARDATA)
            abd.hWnd = hwnd

            # Desregistrar el AppBar
            ctypes.windll.shell32.SHAppBarMessage(ABM_REMOVE, ctypes.byref(abd))
            self.appbar_registered = False
            logger.info("Visor desregistrado como AppBar - espacio liberado")

        except Exception as e:
            logger.error(f"Error al desregistrar AppBar: {e}")

    # === EVENTOS ===

    def showEvent(self, event):
        """
        Cuando la ventana se muestra

        Posiciona la ventana y registra AppBar para reservar espacio en pantalla.
        """
        super().showEvent(event)
        # Posicionar y registrar AppBar con delay
        # Pasar referencia al sidebar (parent) para posicionamiento correcto
        QTimer.singleShot(100, lambda: self.position_window(self.parent()))
        QTimer.singleShot(200, self.register_appbar)
        logger.debug("Visor mostrado - registrando AppBar")

    def hideEvent(self, event):
        """
        Cuando la ventana se oculta

        Desregistra AppBar para liberar espacio reservado.
        """
        self.unregister_appbar()
        super().hideEvent(event)
        self.closed.emit()
        logger.debug("Visor oculto - desregistrando AppBar")

    def closeEvent(self, event):
        """
        Al cerrar, ocultar ventana en lugar de destruirla

        Mantiene el estado del visor (proyecto/área/filtros seleccionados).
        """
        logger.info("Visor close requested - hiding instead")

        # Desregistrar AppBar antes de ocultar
        self.unregister_appbar()

        # Ocultar en lugar de cerrar (mantener estado)
        event.ignore()
        self.hide()

    # === MÉTODOS PÚBLICOS (STUB - Implementar en fases posteriores) ===

    def load_project(self, project_id: int):
        """
        Cargar proyecto en el visor

        Args:
            project_id: ID del proyecto a cargar
        """
        logger.info(f"Cargando proyecto {project_id}")
        self.current_project_id = project_id

        # Obtener datos del proyecto
        self.project_data = self.data_manager.get_project_full_data(project_id)

        if not self.project_data:
            logger.warning(f"No se pudieron obtener datos del proyecto {project_id}")
            self._show_empty_state()
            return

        # Renderizar vista
        self.render_view()

    def load_area(self, area_id: int):
        """
        Cargar área en el visor

        Args:
            area_id: ID del área a cargar
        """
        logger.info(f"Cargando área {area_id}")
        self.current_area_id = area_id

        # Obtener datos del área (usar el mismo método por ahora)
        # TODO: Crear método específico para áreas si la estructura es diferente
        self.project_data = self.data_manager.get_area_full_data(area_id)

        if not self.project_data:
            logger.warning(f"No se pudieron obtener datos del área {area_id}")
            self._show_empty_state()
            return

        # Renderizar vista
        self.render_view()

    def render_view(self):
        """Renderizar vista completa con todos los componentes"""
        if not self.project_data:
            logger.warning("No hay datos para renderizar")
            return

        logger.info(f"Renderizando vista - Tags: {len(self.project_data.get('tags', []))}")
        self._clear_view()

        # Header del proyecto/área
        header = ProjectHeaderWidget()
        header.set_project_info(
            self.project_data['project_name'],
            self.project_data.get('project_icon', '📁')
        )
        self.content_layout.addWidget(header)

        # Determinar qué tags mostrar basado en filtros actuales
        tags_to_render = self._get_filtered_tags()

        # Secciones por tag
        for tag_data in tags_to_render:
            self._render_tag_section(tag_data)

        # Items sin tag (solo si no hay filtros activos)
        if not self.current_filters and self.project_data.get('ungrouped_items'):
            self._render_ungrouped_section(self.project_data['ungrouped_items'])

        # Spacer al final
        self.content_layout.addStretch()

        logger.info(f"Vista renderizada - Headers de tags: {len(self.tag_headers)}")

    def _get_filtered_tags(self) -> list:
        """
        Obtener tags filtrados según selección actual

        Returns:
            Lista de tags a renderizar (todos o solo los filtrados)
        """
        all_tags = self.project_data.get('tags', [])

        # Si no hay filtros, mostrar todos los tags
        if not self.current_filters:
            return all_tags

        # Filtrar solo los tags seleccionados (modo OR)
        filtered_tags = []
        for tag_data in all_tags:
            if tag_data['tag_name'] in self.current_filters:
                filtered_tags.append(tag_data)

        return filtered_tags

    def apply_tag_filters(self, tag_names: list):
        """
        Aplicar filtros de tags y re-renderizar vista

        Args:
            tag_names: Lista de nombres de tags para filtrar (modo OR)
        """
        if not self.project_data:
            logger.debug("No hay datos cargados - ignorando filtros")
            return

        logger.info(f"Aplicando filtros por tags: {tag_names if tag_names else 'ninguno (mostrar todo)'}")

        # Actualizar filtros actuales
        self.current_filters = tag_names

        # Re-renderizar vista con filtros aplicados
        self.render_view()

    def _render_tag_section(self, tag_data: dict):
        """
        Renderizar sección de tag

        Args:
            tag_data: Datos del tag con sus grupos e items
        """
        # Contar items totales en este tag
        total_items = sum(
            len(group['items'])
            for group in tag_data.get('groups', [])
        )

        # Header del tag
        tag_header = ProjectTagHeaderWidget()
        tag_header.set_tag_info(
            tag_data['tag_name'],
            tag_data.get('tag_color', '#32CD32'),
            total_items
        )
        self.content_layout.addWidget(tag_header)

        # Agregar a la lista de headers para el botón de colapsar todo
        self.tag_headers.append(tag_header)

        # Container para grupos (para poder colapsar)
        tag_container = QWidget()
        tag_container_layout = QVBoxLayout(tag_container)
        tag_container_layout.setContentsMargins(0, 0, 0, 0)
        tag_container_layout.setSpacing(8)

        # Capturar tag_name y tag_id del tag actual para pasar al callback de crear lista
        tag_name = tag_data['tag_name']
        tag_id = tag_data.get('tag_id', None)  # tag_id puede no estar disponible

        # Grupos de items
        for group in tag_data.get('groups', []):
            group_widget = ItemGroupWidget(
                group['name'],
                group['type']
            )

            # Conectar señales del grupo (✨ NUEVO)
            # Pasar tag_name y tag_id al callback usando lambda
            create_list_callback = lambda checked=False, tn=tag_name, tid=tag_id: self._on_create_list(tn, tid)
            group_widget.create_list_clicked.connect(create_list_callback)

            # Si es lista, conectar señal de agregar item
            if group['type'] == 'list':
                # Necesitamos pasar el ID de la lista al callback
                # Por ahora, asumimos que group['name'] es el nombre de la lista
                # y buscamos su ID (TODO: mejorar esto con ID directo en los datos)
                lista_name = group['name']
                # Crear lambda con valores capturados
                add_item_callback = lambda checked=False, ln=lista_name, gw=group_widget: self._on_add_item_from_group(ln, gw)
                group_widget.add_item_clicked.connect(add_item_callback)

            # Agregar items al grupo
            for item_data in group['items']:
                group_widget.add_item(item_data)

            tag_container_layout.addWidget(group_widget)

        self.content_layout.addWidget(tag_container)

        # Conectar colapso/expansión
        tag_header.toggle_collapsed.connect(
            lambda collapsed: tag_container.setVisible(not collapsed)
        )

    def _render_ungrouped_section(self, items: list):
        """
        Renderizar sección de items sin tag

        Args:
            items: Lista de items sin tag
        """
        # Header
        tag_header = ProjectTagHeaderWidget()
        tag_header.set_tag_info("Otros Items", "#808080", len(items))
        self.content_layout.addWidget(tag_header)

        # Agregar a la lista de headers
        self.tag_headers.append(tag_header)

        # Container para el grupo
        tag_container = QWidget()
        tag_container_layout = QVBoxLayout(tag_container)
        tag_container_layout.setContentsMargins(0, 0, 0, 0)
        tag_container_layout.setSpacing(8)

        # Grupo de items
        group_widget = ItemGroupWidget("Sin clasificar", "other")
        for item_data in items:
            group_widget.add_item(item_data)

        tag_container_layout.addWidget(group_widget)
        self.content_layout.addWidget(tag_container)

        # Conectar colapso/expansión
        tag_header.toggle_collapsed.connect(
            lambda collapsed: tag_container.setVisible(not collapsed)
        )

    def show_search(self):
        """
        Mostrar/ocultar barra de búsqueda (Ctrl+F)

        Alterna visibilidad de la barra de búsqueda y da foco al campo.
        """
        if self.search_bar.isVisible():
            # Si ya está visible, solo dar foco
            self.search_bar.focus_search_input()
            logger.debug("SearchBar ya visible - dando foco")
        else:
            # Mostrar y dar foco
            self.search_bar.setVisible(True)
            self.search_bar.focus_search_input()
            logger.info("SearchBar mostrada")

    def hide_search(self):
        """Ocultar barra de búsqueda"""
        self.search_bar.setVisible(False)
        self.search_bar.clear_search()
        logger.debug("SearchBar ocultada")

    # === MÉTODOS DE CREACIÓN (✨ NUEVO) ===

    def _on_create_project(self):
        """Callback para crear nuevo proyecto"""
        if not self.db:
            QMessageBox.warning(self, "Error", "No hay conexión a la base de datos")
            return

        # Pedir nombre del proyecto
        name, ok = QInputDialog.getText(
            self,
            "Crear Proyecto",
            "Nombre del proyecto:",
            QLineEdit.EchoMode.Normal
        )

        if not ok or not name.strip():
            return

        name = name.strip()

        try:
            # Crear proyecto en BD
            project_id = self.db.add_project(name=name)
            logger.info(f"✅ Proyecto creado: ID={project_id}, nombre='{name}'")

            # Recargar proyectos en dropdown
            self._reload_projects_and_areas()

            # Auto-seleccionar el proyecto recién creado
            self.context_selector.project_combo.setCurrentText(name)

            QMessageBox.information(
                self,
                "Proyecto Creado",
                f"Proyecto '{name}' creado exitosamente."
            )

        except Exception as e:
            logger.error(f"Error creando proyecto: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"No se pudo crear el proyecto:\n{str(e)}"
            )

    def _on_create_area(self):
        """Callback para crear nueva área"""
        if not self.db:
            QMessageBox.warning(self, "Error", "No hay conexión a la base de datos")
            return

        # Pedir nombre del área
        name, ok = QInputDialog.getText(
            self,
            "Crear Área",
            "Nombre del área:",
            QLineEdit.EchoMode.Normal
        )

        if not ok or not name.strip():
            return

        name = name.strip()

        try:
            # Crear área en BD
            area_id = self.db.add_area(name=name)
            logger.info(f"✅ Área creada: ID={area_id}, nombre='{name}'")

            # Recargar áreas en dropdown
            self._reload_projects_and_areas()

            # Auto-seleccionar el área recién creada
            self.context_selector.area_combo.setCurrentText(name)

            QMessageBox.information(
                self,
                "Área Creada",
                f"Área '{name}' creada exitosamente."
            )

        except Exception as e:
            logger.error(f"Error creando área: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"No se pudo crear el área:\n{str(e)}"
            )

    def _on_create_project_tag(self):
        """Callback para crear nuevo tag de proyecto/área"""
        if not self.db:
            QMessageBox.warning(self, "Error", "No hay conexión a la base de datos")
            return

        # Verificar que haya proyecto o área seleccionado
        if not self.current_project_id and not self.current_area_id:
            QMessageBox.warning(
                self,
                "Proyecto/Área Requerido",
                "Debe seleccionar un Proyecto o Área antes de crear un tag."
            )
            return

        # Pedir nombre del tag
        name, ok = QInputDialog.getText(
            self,
            "Crear Tag",
            "Nombre del tag:",
            QLineEdit.EchoMode.Normal
        )

        if not ok or not name.strip():
            return

        name = name.strip()

        try:
            # Crear tag usando el manager apropiado
            if self.current_project_id:
                tag = self.project_tag_manager.create_tag(
                    name=name,
                    color="#2196F3",
                    description=f"Tag creado desde Visor de Proyectos/Áreas"
                )
                logger.info(f"✅ Tag de proyecto creado: ID={tag['id']}, nombre='{name}'")

            else:  # Área
                tag = self.area_tag_manager.create_tag(
                    name=name,
                    color="#2196F3",
                    description=f"Tag creado desde Visor de Proyectos/Áreas"
                )
                logger.info(f"✅ Tag de área creado: ID={tag['id']}, nombre='{name}'")

            # Recargar tags en chips
            self._reload_current_tags()

            QMessageBox.information(
                self,
                "Tag Creado",
                f"Tag '{name}' creado exitosamente."
            )

        except Exception as e:
            logger.error(f"Error creando tag: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"No se pudo crear el tag:\n{str(e)}"
            )

    def _on_create_list(self, tag_name: str = None, tag_id: int = None):
        """
        Callback para crear nueva lista

        Crea una lista y automáticamente:
        1. Crea un tag de item con el mismo nombre (si no existe)
        2. Asocia la lista al tag de proyecto/área actual

        Args:
            tag_name: Nombre del tag de proyecto/área (capturado de lambda)
            tag_id: ID del tag de proyecto/área (capturado de lambda)
        """
        if not self.db:
            QMessageBox.warning(self, "Error", "No hay conexión a la base de datos")
            return

        # Verificar que hay proyecto o área seleccionado
        if not self.current_project_id and not self.current_area_id:
            QMessageBox.warning(
                self,
                "Proyecto/Área Requerido",
                "Debe seleccionar un Proyecto o Área antes de crear una lista."
            )
            return

        # Usar categoría "sin categoria" (primer registro, ID = 1)
        try:
            category_id = 1  # Primera categoría "sin categoria"

            # Pedir nombre de la lista
            name, ok = QInputDialog.getText(
                self,
                "Crear Lista",
                "Nombre de la lista:",
                QLineEdit.EchoMode.Normal
            )

            if not ok or not name.strip():
                return

            name = name.strip()

            # Crear lista en BD
            lista_id = self.db.create_lista(
                category_id=category_id,
                name=name,
                description=f"Lista creada desde Visor de Proyectos/Áreas"
            )

            logger.info(f"✅ Lista creada: ID={lista_id}, nombre='{name}', category={category_id}")

            # ✨ NUEVO: Crear tag de item con el mismo nombre de la lista
            try:
                # get_or_create_tag ya normaliza el nombre (lowercase, strip)
                tag_item_id = self.db.get_or_create_tag(name)
                logger.info(f"✅ Tag de item creado/obtenido: ID={tag_item_id}, nombre='{name}'")
            except Exception as e:
                logger.warning(f"⚠️ No se pudo crear tag de item: {e}")
                # No es crítico, continuar

            # Asociar lista al tag de proyecto/área si corresponde
            if tag_name and (self.current_project_id or self.current_area_id):
                try:
                    # Si no tenemos tag_id, buscarlo por nombre
                    if not tag_id:
                        if self.current_project_id:
                            # Buscar tag de proyecto por nombre
                            conn = self.db.connect()
                            cursor = conn.execute(
                                "SELECT id FROM project_element_tags WHERE name = ?",
                                (tag_name,)
                            )
                            row = cursor.fetchone()
                            if row:
                                tag_id = row['id']
                                logger.debug(f"Tag de proyecto '{tag_name}' encontrado: ID={tag_id}")

                        elif self.current_area_id:
                            # Buscar tag de área por nombre
                            conn = self.db.connect()
                            cursor = conn.execute(
                                "SELECT id FROM area_element_tags WHERE name = ?",
                                (tag_name,)
                            )
                            row = cursor.fetchone()
                            if row:
                                tag_id = row['id']
                                logger.debug(f"Tag de área '{tag_name}' encontrado: ID={tag_id}")

                    # Crear relación y asociar al tag si tenemos tag_id
                    if tag_id:
                        if self.current_project_id:
                            # Crear relación de proyecto para la lista
                            relation_id = self._create_project_relation_for_list(lista_id, category_id)

                            if relation_id:
                                # Asociar al tag de proyecto
                                self._associate_to_project_tag(relation_id, tag_id)
                                logger.info(f"✅ Lista asociada al tag de proyecto '{tag_name}'")

                        elif self.current_area_id:
                            # Crear relación de área para la lista
                            relation_id = self._create_area_relation_for_list(lista_id, category_id)

                            if relation_id:
                                # Asociar al tag de área
                                self._associate_to_area_tag(relation_id, tag_id)
                                logger.info(f"✅ Lista asociada al tag de área '{tag_name}'")
                    else:
                        logger.warning(f"⚠️ No se encontró tag '{tag_name}' - lista no asociada")

                except Exception as e:
                    logger.warning(f"⚠️ No se pudo asociar lista al tag: {e}")
                    # No es crítico, continuar

            # Recargar vista completa
            if self.current_project_id:
                self.load_project(self.current_project_id)
            elif self.current_area_id:
                self.load_area(self.current_area_id)

            QMessageBox.information(
                self,
                "Lista Creada",
                f"Lista '{name}' creada exitosamente.\n"
                f"Tag de item '{name}' creado/actualizado automáticamente."
            )

        except ValueError as e:
            QMessageBox.warning(self, "Error de Validación", str(e))
        except Exception as e:
            logger.error(f"Error creando lista: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Error",
                f"No se pudo crear la lista:\n{str(e)}"
            )

    def _on_add_item_from_group(self, lista_name: str, group_widget):
        """
        Callback para agregar item desde un grupo de lista (busca ID por nombre)

        Args:
            lista_name: Nombre de la lista
            group_widget: Widget del grupo
        """
        if not self.db:
            QMessageBox.warning(self, "Error", "No hay conexión a la base de datos")
            return

        try:
            # Buscar lista por nombre
            # Obtener el ID del primer item del grupo para saber la categoría
            if group_widget.items:
                first_item_id = group_widget.items[0].item_data.get('id')
                if first_item_id:
                    item = self.db.get_item(first_item_id)
                    if item and item.get('list_id'):
                        lista_id = item['list_id']
                        self._on_add_item_to_list(lista_id, lista_name)
                        return

            # Si no se pudo obtener el ID de los items, buscar en todas las listas
            conn = self.db.connect()
            cursor = conn.execute("SELECT id FROM listas WHERE name = ?", (lista_name,))
            row = cursor.fetchone()

            if row:
                lista_id = row['id']
                self._on_add_item_to_list(lista_id, lista_name)
            else:
                QMessageBox.warning(
                    self,
                    "Lista no encontrada",
                    f"No se encontró la lista '{lista_name}' en la base de datos."
                )

        except Exception as e:
            logger.error(f"Error buscando lista '{lista_name}': {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"No se pudo encontrar la lista:\n{str(e)}"
            )

    def _on_add_item_to_list(self, lista_id: int, lista_name: str):
        """
        Callback para agregar item a una lista específica

        Args:
            lista_id: ID de la lista
            lista_name: Nombre de la lista
        """
        if not self.db:
            QMessageBox.warning(self, "Error", "No hay conexión a la base de datos")
            return

        # Guardar lista actual
        self.current_lista_id = lista_id

        # Crear o mostrar diálogo de agregar item
        if not self.add_item_dialog:
            self.add_item_dialog = AddItemDialog(self)
            self.add_item_dialog.item_created.connect(self._on_item_created)

        # Posicionar diálogo cerca del visor
        dialog_x = self.x() + (self.width() - self.add_item_dialog.width()) // 2
        dialog_y = self.y() + 100
        self.add_item_dialog.move(dialog_x, dialog_y)

        self.add_item_dialog.show()
        self.add_item_dialog.raise_()
        self.add_item_dialog.activateWindow()

        logger.info(f"Diálogo de agregar item mostrado para lista '{lista_name}' (ID={lista_id})")

    def _on_item_created(self, item_data: dict):
        """
        Callback cuando se crea un item desde el diálogo

        Args:
            item_data: Datos del item {label, content, type, is_sensitive}
        """
        if not self.db or not self.current_lista_id:
            logger.error("No hay lista seleccionada para agregar item")
            return

        try:
            # Obtener ID de categoría de la lista
            lista = self.db.get_lista(self.current_lista_id)
            if not lista:
                raise Exception(f"Lista {self.current_lista_id} no encontrada")

            category_id = lista['category_id']

            # ✨ NUEVO: Obtener nombre de la lista para crear tag automático
            lista_name = lista['name']

            # Crear item en BD con la lista
            # El tag con el nombre de la lista se agregará automáticamente después
            item_id = self.db.add_item(
                category_id=category_id,
                label=item_data['label'],
                content=item_data['content'],
                item_type=item_data['type'],
                is_sensitive=item_data['is_sensitive'],
                list_id=self.current_lista_id,
                tags=[]  # Tags se agregarán después
            )

            logger.info(f"✅ Item creado: ID={item_id}, label='{item_data['label']}' en lista {self.current_lista_id}")

            # ✨ NUEVO: Agregar automáticamente el tag de item con el mismo nombre de la lista
            try:
                self.db.add_tag_to_item(item_id, lista_name)
                logger.info(f"✅ Tag '{lista_name}' agregado automáticamente al item {item_id}")
            except Exception as e:
                logger.warning(f"⚠️ No se pudo agregar tag automático al item: {e}")
                # No es crítico, continuar

            # Recargar vista completa
            if self.current_project_id:
                self.load_project(self.current_project_id)
            elif self.current_area_id:
                self.load_area(self.current_area_id)

            QMessageBox.information(
                self,
                "Item Creado",
                f"Item '{item_data['label']}' agregado exitosamente a la lista."
            )

        except Exception as e:
            logger.error(f"Error creando item: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"No se pudo crear el item:\n{str(e)}"
            )

    def _reload_projects_and_areas(self):
        """Recargar proyectos y áreas en los dropdowns"""
        try:
            # Recargar proyectos
            projects = self.db.get_all_projects()
            projects_data = [(p['id'], p['name']) for p in projects]
            self.context_selector.load_projects(projects_data)

            # Recargar áreas
            areas = self.db.get_all_areas()
            areas_data = [(a['id'], a['name']) for a in areas]
            self.context_selector.load_areas(areas_data)

            logger.info("✅ Proyectos y áreas recargados en dropdowns")

        except Exception as e:
            logger.error(f"Error recargando proyectos/áreas: {e}")

    def _reload_current_tags(self):
        """Recargar tags del proyecto/área actual"""
        if not self.db:
            return

        try:
            if self.current_project_id:
                # Recargar tags de proyecto
                tags = self.project_tag_manager.get_tags_for_project(self.current_project_id)
                tags_data = [{'name': t['name'], 'color': t.get('color', '#808080')} for t in tags]
                self.tag_filter_chips.load_tags(tags_data)
                logger.info(f"✅ Recargados {len(tags_data)} tags de proyecto")

            elif self.current_area_id:
                # Recargar tags de área
                tags = self.area_tag_manager.get_tags_for_area(self.current_area_id)
                tags_data = [{'name': t['name'], 'color': t.get('color', '#808080')} for t in tags]
                self.tag_filter_chips.load_tags(tags_data)
                logger.info(f"✅ Recargados {len(tags_data)} tags de área")

        except Exception as e:
            logger.error(f"Error recargando tags: {e}")

    # === MÉTODOS AUXILIARES PARA ASOCIACIÓN DE LISTAS A TAGS ===

    def _create_project_relation_for_list(self, lista_id: int, category_id: int) -> Optional[int]:
        """
        Crea una relación de proyecto para una lista

        Args:
            lista_id: ID de la lista
            category_id: ID de la categoría

        Returns:
            ID de la relación creada o None si falló
        """
        try:
            relation_id = self.db.add_project_relation(
                project_id=self.current_project_id,
                entity_type='list',
                entity_id=lista_id,
                description=f"Lista creada desde Visor",
                order_index=0
            )
            logger.info(f"✅ Relación de proyecto creada: ID={relation_id} para lista {lista_id}")
            return relation_id
        except Exception as e:
            logger.error(f"Error creando relación de proyecto: {e}")
            return None

    def _associate_to_project_tag(self, relation_id: int, tag_id: int) -> bool:
        """
        Asocia una relación de proyecto a un tag

        Args:
            relation_id: ID de la relación
            tag_id: ID del tag de proyecto

        Returns:
            True si se asoció correctamente
        """
        try:
            success = self.db.add_tag_to_project_relation(relation_id, tag_id)
            if success:
                logger.info(f"✅ Relación {relation_id} asociada al tag de proyecto {tag_id}")
            return success
        except Exception as e:
            logger.error(f"Error asociando relación a tag de proyecto: {e}")
            return False

    def _create_area_relation_for_list(self, lista_id: int, category_id: int) -> Optional[int]:
        """
        Crea una relación de área para una lista

        Args:
            lista_id: ID de la lista
            category_id: ID de la categoría

        Returns:
            ID de la relación creada o None si falló
        """
        try:
            relation_id = self.db.add_area_relation(
                area_id=self.current_area_id,
                entity_type='list',
                entity_id=lista_id,
                description=f"Lista creada desde Visor",
                order_index=0
            )
            logger.info(f"✅ Relación de área creada: ID={relation_id} para lista {lista_id}")
            return relation_id
        except Exception as e:
            logger.error(f"Error creando relación de área: {e}")
            return None

    def _associate_to_area_tag(self, relation_id: int, tag_id: int) -> bool:
        """
        Asocia una relación de área a un tag

        Args:
            relation_id: ID de la relación
            tag_id: ID del tag de área

        Returns:
            True si se asoció correctamente
        """
        try:
            success = self.db.assign_tag_to_area_relation(relation_id, tag_id)
            if success:
                logger.info(f"✅ Relación {relation_id} asociada al tag de área {tag_id}")
            return success
        except Exception as e:
            logger.error(f"Error asociando relación a tag de área: {e}")
            return False


# === TEST ===
if __name__ == '__main__':
    """Test independiente del visor"""
    import sys
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    # Crear visor sin DBManager para testing
    viewer = ProjectAreaViewerPanel(db_manager=None)
    viewer.setWindowTitle("Vista de Proyectos/Áreas - Test")
    viewer.show()

    sys.exit(app.exec())
