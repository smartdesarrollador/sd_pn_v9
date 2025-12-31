"""
Ventana del Creador Masivo de Items

Características:
- Sistema de tabs con QTabWidget
- Auto-guardado de borradores con debounce
- Recuperación de borradores al abrir
- Gestión de tabs (agregar, eliminar, renombrar)
- Guardado final de items en BD
- AppBar API para reservar espacio en pantalla
- Posicionamiento junto al sidebar
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTabWidget,
    QMessageBox, QInputDialog, QLabel, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QPoint
from PyQt6.QtGui import QFont, QScreen
from src.views.widgets.tab_content_widget import TabContentWidget
from src.core.draft_persistence_manager import DraftPersistenceManager
from src.core.project_element_tag_manager import ProjectElementTagManager
from src.core.area_element_tag_manager import AreaElementTagManager
from src.models.item_draft import ItemDraft
import uuid
import logging
import sys
import ctypes
from ctypes import wintypes

logger = logging.getLogger(__name__)

# Constantes para AppBar API de Windows
ABM_NEW = 0x00000000
ABM_REMOVE = 0x00000001
ABM_QUERYPOS = 0x00000002
ABM_SETPOS = 0x00000003
ABE_RIGHT = 2  # Lado derecho de la pantalla


class APPBARDATA(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("hWnd", wintypes.HWND),
        ("uCallbackMessage", wintypes.UINT),
        ("uEdge", wintypes.UINT),
        ("rc", wintypes.RECT),
        ("lParam", wintypes.LPARAM),
    ]


# Constantes de dimensiones
CREATOR_WIDTH = 450
CREATOR_MIN_HEIGHT = 400


class BulkItemCreatorDialog(QWidget):
    """
    Ventana para creación masiva de items

    Gestiona múltiples tabs, cada uno con un TabContentWidget.
    Implementa auto-guardado, recuperación de borradores y guardado final.
    Usa AppBar API para reservar espacio en pantalla.

    Señales:
        items_saved: Emitida cuando se guardan items exitosamente (int count)
        closed: Emitida cuando se cierra la ventana
    """

    # Señales
    items_saved = pyqtSignal(int)  # Cantidad de items guardados
    closed = pyqtSignal()  # Cuando se cierra la ventana

    def __init__(self, db_manager, config_manager, main_controller=None, parent=None):
        """
        Inicializa la ventana del Creador Masivo

        Args:
            db_manager: Instancia de DBManager
            config_manager: Instancia de ConfigManager
            main_controller: Instancia de MainController (para screenshot_controller)
            parent: Widget padre
        """
        super().__init__(parent)
        self.db = db_manager
        self.config = config_manager
        self.main_controller = main_controller
        self.appbar_registered = False  # Estado del AppBar
        self.drag_position = QPoint()  # Para dragging de ventana

        # Screenshot controller (obtenido del main_controller)
        self.screenshot_controller = None
        if main_controller and hasattr(main_controller, 'screenshot_controller'):
            self.screenshot_controller = main_controller.screenshot_controller

        # Draft persistence manager
        self.draft_manager = DraftPersistenceManager(
            db_manager=db_manager,
            debounce_ms=1000,  # 1 segundo de debounce
            parent=self
        )

        # Timer para debounce de auto-guardado
        self.save_timer = QTimer(self)
        self.save_timer.setSingleShot(True)
        self.save_timer.timeout.connect(self._save_current_tab)

        # Tag Managers
        self.project_tag_manager = ProjectElementTagManager(self.db)
        self.area_tag_manager = AreaElementTagManager(self.db)

        # Configuración de ventana
        self.setWindowTitle("⚡ Creador Masivo de Items")
        self.setMinimumSize(CREATOR_WIDTH, CREATOR_MIN_HEIGHT)

        # Frameless window (Tool para no aparecer en barra de tareas)
        self.setWindowFlags(
            Qt.WindowType.Tool |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )

        self._setup_ui()
        self._apply_styles()
        self._connect_signals()
        self._load_available_data()
        self._recover_drafts()

        logger.info("BulkItemCreatorDialog inicializado")

    def _setup_ui(self):
        """Configura la interfaz del diálogo"""
        # Layout principal
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header con barra de título personalizada
        header = self._create_header()
        layout.addWidget(header)

        # Tab widget principal
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.setMovable(True)
        self.tab_widget.setDocumentMode(True)
        layout.addWidget(self.tab_widget)

        # Botón "+" para agregar tabs
        add_tab_btn = QPushButton("+")
        add_tab_btn.setFixedSize(20, 20)
        add_tab_btn.setToolTip("Agregar nueva pestaña")
        add_tab_btn.clicked.connect(self.add_new_tab)
        self.tab_widget.setCornerWidget(add_tab_btn, Qt.Corner.TopRightCorner)

        # Footer con botones de acción
        footer = self._create_footer()
        layout.addWidget(footer)

    def _create_header(self) -> QWidget:
        """Crea el header compacto con barra de título arrastrable"""
        header = QWidget()
        header.setFixedHeight(35)
        header.setStyleSheet("background-color: #2d2d2d; border-bottom: 1px solid #444;")

        layout = QHBoxLayout(header)
        layout.setContentsMargins(10, 0, 10, 0)
        layout.setSpacing(8)

        # Título (arrastrable)
        title = QLabel("⚡ Creador Masivo")
        title.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        title.setStyleSheet("color: #ffffff;")
        layout.addWidget(title)

        layout.addStretch()

        # Botón Actualizar (refrescar datos de BD)
        refresh_btn = QPushButton("⟳")
        refresh_btn.setFixedSize(20, 20)
        refresh_btn.setToolTip("Actualizar datos desde la base de datos")
        refresh_btn.clicked.connect(self._on_refresh_clicked)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #00BCD4;
                color: #fff;
                border: none;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #00ACC1;
            }
            QPushButton:pressed {
                background-color: #0097A7;
            }
        """)
        layout.addWidget(refresh_btn)

        # Info label
        self.info_label = QLabel("0 tabs")
        self.info_label.setStyleSheet("color: #888; font-size: 9px;")
        layout.addWidget(self.info_label)

        # Botón minimizar
        minimize_btn = QPushButton("━")
        minimize_btn.setFixedSize(20, 20)
        minimize_btn.setToolTip("Ocultar ventana")
        minimize_btn.clicked.connect(self.hide)
        minimize_btn.setStyleSheet("""
            QPushButton {
                background-color: #555;
                color: #fff;
                border: none;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #666;
            }
        """)
        layout.addWidget(minimize_btn)

        # Botón cerrar
        close_btn = QPushButton("✖")
        close_btn.setFixedSize(20, 20)
        close_btn.setToolTip("Cerrar")
        close_btn.clicked.connect(self._on_close_clicked)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #d32f2f;
                color: #fff;
                border: none;
                font-size: 16px;
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

    def _create_footer(self) -> QWidget:
        """Crea el footer compacto con botones de acción"""
        footer = QWidget()
        footer.setFixedHeight(45)
        footer.setStyleSheet("background-color: #2d2d2d; border-top: 1px solid #444;")

        layout = QHBoxLayout(footer)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(6)

        layout.addStretch()

        # Botón Cancelar
        self.cancel_btn = QPushButton("Cancelar")
        self.cancel_btn.setFixedHeight(28)
        self.cancel_btn.setMinimumWidth(80)
        self.cancel_btn.clicked.connect(self.hide)
        layout.addWidget(self.cancel_btn)

        # Botón Guardar Todas las Pestañas
        self.save_all_btn = QPushButton("💾 Guardar Todas")
        self.save_all_btn.setFixedHeight(28)
        self.save_all_btn.setMinimumWidth(120)
        self.save_all_btn.clicked.connect(self._on_save_all_tabs)
        layout.addWidget(self.save_all_btn)

        # Botón Guardar Pestaña Actual
        self.save_current_btn = QPushButton("✓ Guardar Actual")
        self.save_current_btn.setFixedHeight(28)
        self.save_current_btn.setMinimumWidth(110)
        self.save_current_btn.setDefault(True)
        self.save_current_btn.clicked.connect(self._on_save_current_tab)
        layout.addWidget(self.save_current_btn)

        return footer

    def _apply_styles(self):
        """Aplica estilos CSS compactos"""
        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e1e;
            }
            QTabWidget::pane {
                border: none;
                background-color: #1e1e1e;
            }
            QTabWidget::tab-bar {
                alignment: left;
            }
            QTabBar::tab {
                background-color: #2d2d2d;
                color: #aaaaaa;
                padding: 6px 12px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                min-width: 80px;
                font-size: 10px;
            }
            QTabBar::tab:selected {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            QTabBar::tab:hover {
                background-color: #3d3d3d;
            }
            QTabBar::close-button {
                image: none;
                background-color: #d32f2f;
                border-radius: 2px;
                width: 12px;
                height: 12px;
            }
            QTabBar::close-button:hover {
                background-color: #b71c1c;
            }
            QPushButton {
                background-color: #3d3d3d;
                color: #ffffff;
                border: 1px solid #555;
                border-radius: 4px;
                font-size: 10px;
                font-weight: bold;
                padding: 4px 10px;
            }
            QPushButton:hover {
                background-color: #4d4d4d;
                border: 1px solid #666;
            }
            QPushButton:pressed {
                background-color: #2d2d2d;
            }
            QPushButton:default {
                background-color: #2196F3;
                border: 1px solid #1976D2;
            }
            QPushButton:default:hover {
                background-color: #1976D2;
            }
            QPushButton#add_tab_btn {
                background-color: #2196F3;
                font-size: 14px;
            }
        """)

    def _connect_signals(self):
        """Conecta señales del diálogo"""
        # Señales del tab widget
        self.tab_widget.tabCloseRequested.connect(self._on_tab_close_requested)
        self.tab_widget.currentChanged.connect(self._on_tab_changed)

        # Señales del draft manager
        self.draft_manager.draft_saved.connect(self._on_draft_saved)
        self.draft_manager.save_failed.connect(self._on_save_failed)

    def _load_available_data(self):
        """Carga datos disponibles para los selectores"""
        # Se hará en cada tab cuando se cree
        pass

    def _recover_drafts(self):
        """Recupera borradores existentes al abrir el diálogo"""
        logger.info("Recuperando borradores...")

        drafts = self.draft_manager.load_all_drafts()

        if drafts:
            logger.info(f"Recuperados {len(drafts)} borradores")
            for draft in drafts:
                self._add_tab_from_draft(draft)
        else:
            logger.info("No hay borradores, creando tab vacío")
            self.add_new_tab()

        self._update_info_label()

    def add_new_tab(self, name: str = None):
        """
        Agrega un nuevo tab vacío

        Args:
            name: Nombre del tab (opcional)
        """
        tab_id = str(uuid.uuid4())
        tab_name = name or f"Tab {self.tab_widget.count() + 1}"

        # Crear widget de contenido
        tab_content = TabContentWidget(
            tab_id,
            tab_name,
            db_manager=self.db,
            project_tag_manager=self.project_tag_manager,
            area_tag_manager=self.area_tag_manager,
            parent=self
        )

        # Establecer screenshot controller si está disponible
        if self.screenshot_controller:
            tab_content.set_screenshot_controller(self.screenshot_controller)

        # Cargar datos disponibles
        self._load_tab_available_data(tab_content)

        # Conectar señales
        self._connect_tab_signals(tab_content)

        # Agregar al tab widget
        index = self.tab_widget.addTab(tab_content, tab_name)
        self.tab_widget.setCurrentIndex(index)

        self._update_info_label()

        logger.info(f"Tab agregado: {tab_name} ({tab_id})")

    def _add_tab_from_draft(self, draft: ItemDraft):
        """
        Agrega un tab desde un borrador recuperado

        Args:
            draft: Borrador a cargar
        """
        # Crear widget de contenido
        tab_content = TabContentWidget(
            draft.tab_id,
            draft.tab_name,
            db_manager=self.db,
            project_tag_manager=self.project_tag_manager,
            area_tag_manager=self.area_tag_manager,
            parent=self
        )

        # Establecer screenshot controller si está disponible
        if self.screenshot_controller:
            tab_content.set_screenshot_controller(self.screenshot_controller)

        # Cargar datos disponibles
        self._load_tab_available_data(tab_content)

        # Cargar datos del draft
        tab_content.load_data(draft)

        # Conectar señales
        self._connect_tab_signals(tab_content)

        # Agregar al tab widget
        index = self.tab_widget.addTab(tab_content, draft.tab_name)

        logger.info(f"Tab recuperado: {draft.tab_name} ({draft.tab_id})")

    def _load_tab_available_data(self, tab_content: TabContentWidget):
        """
        Carga datos disponibles en un tab

        Args:
            tab_content: Widget del tab
        """
        # Cargar proyectos
        try:
            projects = self.db.get_all_projects() if hasattr(self.db, 'get_all_projects') else []
            if projects:
                tab_content.load_available_projects([(p['id'], p['name']) for p in projects])
        except Exception as e:
            logger.warning(f"No se pudieron cargar proyectos: {e}")

        # Cargar áreas
        try:
            areas = self.db.get_all_areas() if hasattr(self.db, 'get_all_areas') else []
            if areas:
                tab_content.load_available_areas([(a['id'], a['name']) for a in areas])
        except Exception as e:
            logger.warning(f"No se pudieron cargar áreas: {e}")

        # Cargar categorías
        try:
            categories = self.config.get_categories()
            if categories:
                tab_content.load_available_categories([(c.id, c.name) for c in categories])
        except Exception as e:
            logger.error(f"Error cargando categorías: {e}")

        # Cargar tags
        try:
            # TODO: Implementar get_all_tags en DBManager
            # tags = self.db.get_all_tags()
            # tab_content.load_available_item_tags(tags)
            pass
        except Exception as e:
            logger.warning(f"No se pudieron cargar tags: {e}")

    def _connect_tab_signals(self, tab_content: TabContentWidget):
        """
        Conecta señales de un tab

        Args:
            tab_content: Widget del tab
        """
        # Señal de cambio de datos (auto-save)
        tab_content.data_changed.connect(lambda: self._schedule_save(tab_content))

        # Señales de creación
        tab_content.create_project_clicked.connect(self._on_create_project)
        tab_content.create_area_clicked.connect(self._on_create_area)
        tab_content.create_category_clicked.connect(self._on_create_category)
        tab_content.create_project_tag_clicked.connect(self._on_create_project_tag)
        tab_content.create_item_tag_clicked.connect(self._on_create_item_tag)
        tab_content.create_list_clicked.connect(self._on_create_list)

    def _schedule_save(self, tab_content: TabContentWidget):
        """
        Programa el auto-guardado de un tab

        Args:
            tab_content: Widget del tab
        """
        # Cancelar timer anterior
        self.save_timer.stop()

        # Guardar referencia al tab actual
        self.current_tab_to_save = tab_content

        # Iniciar timer (1 segundo de debounce)
        self.save_timer.start(1000)

        logger.debug(f"Auto-guardado programado para tab {tab_content.get_tab_id()}")

    def _save_current_tab(self):
        """Ejecuta el auto-guardado del tab actual"""
        if not hasattr(self, 'current_tab_to_save'):
            return

        tab_content = self.current_tab_to_save

        try:
            # Obtener datos del tab
            draft = tab_content.get_data()

            # Programar guardado con draft manager
            self.draft_manager.schedule_save(draft)

            logger.debug(f"Auto-guardado ejecutado para tab {draft.tab_id}")

        except Exception as e:
            logger.error(f"Error en auto-guardado: {e}")

    def _on_tab_close_requested(self, index: int):
        """
        Callback cuando se solicita cerrar un tab

        Args:
            index: Índice del tab a cerrar
        """
        if self.tab_widget.count() <= 1:
            QMessageBox.warning(
                self,
                "No se puede cerrar",
                "Debe haber al menos un tab abierto."
            )
            return

        # Obtener tab content
        tab_content = self.tab_widget.widget(index)
        if not isinstance(tab_content, TabContentWidget):
            return

        # Confirmar si hay datos
        if tab_content.get_items_count() > 0:
            reply = QMessageBox.question(
                self,
                "Confirmar cierre",
                f"¿Cerrar el tab '{tab_content.get_tab_name()}'?\n\n"
                "El borrador se eliminará permanentemente.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.No:
                return

        # Eliminar borrador de BD
        self.draft_manager.delete_draft(tab_content.get_tab_id())

        # Eliminar tab
        self.tab_widget.removeTab(index)
        tab_content.deleteLater()

        self._update_info_label()

        logger.info(f"Tab cerrado: {tab_content.get_tab_name()}")

    def _on_tab_changed(self, index: int):
        """
        Callback cuando cambia el tab activo

        Args:
            index: Índice del nuevo tab activo
        """
        if index >= 0:
            tab_content = self.tab_widget.widget(index)
            if isinstance(tab_content, TabContentWidget):
                logger.debug(f"Tab activo: {tab_content.get_tab_name()}")

    def _on_draft_saved(self, tab_id: str):
        """
        Callback cuando se guarda un borrador exitosamente

        Args:
            tab_id: ID del tab guardado
        """
        logger.debug(f"✅ Borrador guardado: {tab_id}")

    def _on_save_failed(self, tab_id: str, error_msg: str):
        """
        Callback cuando falla el guardado de un borrador

        Args:
            tab_id: ID del tab
            error_msg: Mensaje de error
        """
        logger.error(f"❌ Error guardando borrador {tab_id}: {error_msg}")

    def _update_info_label(self):
        """Actualiza el label de información"""
        count = self.tab_widget.count()
        total_items = sum(
            self.tab_widget.widget(i).get_items_count()
            for i in range(count)
            if isinstance(self.tab_widget.widget(i), TabContentWidget)
        )
        self.info_label.setText(f"{count} tabs, {total_items} items")

    def _on_save_current_tab(self):
        """Callback del botón Guardar Pestaña Actual"""
        # Obtener tab actual
        current_tab = self._get_current_tab_content()
        if not current_tab:
            QMessageBox.warning(self, "Error", "No hay pestaña activa")
            return

        # Validar solo campos obligatorios
        valid, errors = current_tab.validate()
        if not valid:
            # Filtrar solo errores de campos obligatorios
            obligatory_errors = self._filter_obligatory_errors(errors)
            if obligatory_errors:
                QMessageBox.warning(
                    self,
                    "Campos obligatorios incompletos",
                    "Complete los siguientes campos obligatorios:\n\n" + "\n".join([f"• {err}" for err in obligatory_errors])
                )
                return

        # Guardar items
        try:
            draft = current_tab.get_data()
            count = self._save_items_from_draft(draft)

            # Generar mensaje de resumen
            summary_msg = self._generate_save_summary(draft, count)

            # Preguntar si desea limpiar la pestaña
            reply = QMessageBox.question(
                self,
                "✅ Guardado exitoso",
                f"{summary_msg}\n\n¿Desea limpiar la pestaña actual?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )

            # Eliminar borrador
            self.draft_manager.delete_draft(draft.tab_id)

            # Limpiar si el usuario lo solicita
            if reply == QMessageBox.StandardButton.Yes:
                current_tab.clear_all()
                logger.info("Pestaña actual limpiada después de guardar")

            # Emitir señal
            self.items_saved.emit(count)

        except Exception as e:
            logger.error(f"Error guardando pestaña actual: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"Error al guardar items:\n{str(e)}"
            )

    def _on_save_all_tabs(self):
        """Callback del botón Guardar Todas las Pestañas"""
        # Validar todos los tabs
        errors_by_tab = {}
        valid_tabs = []

        for i in range(self.tab_widget.count()):
            tab_content = self.tab_widget.widget(i)
            if not isinstance(tab_content, TabContentWidget):
                continue

            valid, tab_errors = tab_content.validate()
            if not valid:
                # Filtrar solo errores obligatorios
                obligatory_errors = self._filter_obligatory_errors(tab_errors)
                if obligatory_errors:
                    errors_by_tab[tab_content.get_tab_name()] = obligatory_errors
            else:
                valid_tabs.append(tab_content)

        # Si hay errores, mostrar y abortar
        if errors_by_tab:
            error_msg = "Complete los campos obligatorios en las siguientes pestañas:\n\n"
            for tab_name, tab_errors in errors_by_tab.items():
                error_msg += f"📑 {tab_name}:\n"
                error_msg += "\n".join([f"  • {err}" for err in tab_errors])
                error_msg += "\n\n"

            QMessageBox.warning(
                self,
                "Campos obligatorios incompletos",
                error_msg.strip()
            )
            return

        # Guardar items de todos los tabs
        total_saved = 0
        saved_tabs = []

        try:
            for tab_content in valid_tabs:
                draft = tab_content.get_data()
                count = self._save_items_from_draft(draft)
                total_saved += count
                saved_tabs.append((tab_content.get_tab_name(), count))

                # Eliminar borrador después de guardar
                self.draft_manager.delete_draft(draft.tab_id)

            # Generar mensaje de resumen de todas las pestañas
            summary_msg = f"✅ Se guardaron {total_saved} items correctamente desde {len(saved_tabs)} pestaña(s):\n\n"
            for tab_name, count in saved_tabs:
                summary_msg += f"📑 {tab_name}: {count} items\n"

            # Mostrar mensaje de éxito
            QMessageBox.information(
                self,
                "Guardado exitoso",
                summary_msg.strip()
            )

            # Emitir señal
            self.items_saved.emit(total_saved)

            # Limpiar todos los tabs
            for tab_content in valid_tabs:
                tab_content.clear_all()

            logger.info(f"Guardadas {len(saved_tabs)} pestañas con {total_saved} items en total")

        except Exception as e:
            logger.error(f"Error guardando todas las pestañas: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"Error al guardar items:\n{str(e)}"
            )

    def _filter_obligatory_errors(self, errors: list[str]) -> list[str]:
        """
        Filtra solo los errores de campos obligatorios

        Args:
            errors: Lista de errores de validación

        Returns:
            Lista con solo errores de campos obligatorios
        """
        obligatory_keywords = [
            "obligatorio", "debe", "requerido", "necesario",
            "seleccionar", "ingresar", "al menos"
        ]

        filtered = []
        for error in errors:
            error_lower = error.lower()
            if any(keyword in error_lower for keyword in obligatory_keywords):
                filtered.append(error)

        return filtered

    def _generate_save_summary(self, draft: ItemDraft, count: int) -> str:
        """
        Genera un mensaje de resumen personalizado según el tipo de guardado

        Args:
            draft: Borrador guardado
            count: Cantidad de items guardados

        Returns:
            Mensaje de resumen
        """
        # Determinar tipo de guardado
        has_project_or_area = draft.has_project_or_area()

        # Calcular desglose de items
        regular_items = len([item for item in draft.items if not item.is_empty()])
        screenshots_count = len(draft.screenshots) if draft.screenshots else 0

        # Base del mensaje
        msg = f"✅ Se guardaron {count} items correctamente"

        # Agregar desglose si hay screenshots
        if screenshots_count > 0:
            msg += f" ({regular_items} regulares + {screenshots_count} capturas)"

        # Si tiene proyecto/área, siempre es lista
        if has_project_or_area and draft.list_name:
            # Diferenciar entre lista existente y nueva
            if draft.list_id:
                msg += f" a la lista '{draft.list_name}'"
            else:
                msg += f" en la lista '{draft.list_name}'"

            # Agregar relación con proyecto/área
            if draft.project_id:
                msg += f"\n📁 Relacionada con el proyecto"
            elif draft.area_id:
                msg += f"\n📁 Relacionada con el área"

            # Agregar tags de proyecto/área
            if draft.project_element_tags:
                tags_str = ", ".join(draft.project_element_tags)
                msg += f"\n🏷️ Tags: {tags_str}"

        # Modo simple (sin proyecto/área)
        else:
            if draft.item_tags:
                tags_str = ", ".join(draft.item_tags)
                msg += f"\n🏷️ Tags: {tags_str}"

        return msg

    def _save_items_from_draft(self, draft: ItemDraft) -> int:
        """
        Guarda los items de un draft en la BD usando 2 estrategias

        Estrategias de guardado:
        1. MODO SIMPLE: Sin proyecto/área
           → Guarda items con tags opcionales

        2. MODO LISTA: Con proyecto/área (siempre como lista)
           → Crea lista → guarda items con list_id → crea relación proyecto-lista

        Args:
            draft: Borrador con los items y metadatos

        Returns:
            Cantidad de items guardados

        Raises:
            Exception: Si hay error en el guardado
        """
        # Determinar estrategia de guardado
        has_project_or_area = draft.has_project_or_area()

        logger.info("=" * 60)
        logger.info("GUARDANDO ITEMS DESDE DRAFT")
        logger.info(f"  Proyecto: {draft.project_id}")
        logger.info(f"  Área: {draft.area_id}")
        logger.info(f"  Nombre lista: '{draft.list_name}'")
        logger.info(f"  Items: {len(draft.items)}")
        logger.info(f"  Tags proyecto: {draft.project_element_tags}")
        logger.info(f"  Tags items: {draft.item_tags}")
        logger.info("=" * 60)

        # ESTRATEGIA 1: Modo Simple (sin proyecto/área)
        if not has_project_or_area:
            logger.info("→ Estrategia: MODO SIMPLE")
            return self._save_simple_items(draft)

        # ESTRATEGIA 2: Modo Lista (con proyecto/área - siempre como lista)
        logger.info("→ Estrategia: MODO LISTA")
        return self._save_as_list(draft)

    def _save_simple_items(self, draft: ItemDraft) -> int:
        """
        Guarda items sin proyecto/área (modo simple)

        Este método se usa cuando NO hay proyecto ni área seleccionados.
        Solo guarda los items con sus tags opcionales.

        Args:
            draft: Borrador con items y tags

        Returns:
            Cantidad de items guardados
        """
        saved_count = 0

        logger.info(f"Guardando {len(draft.items)} items en modo SIMPLE (sin proyecto/área)")

        # Guardar cada item con sus tags
        for item_field in draft.items:
            if item_field.is_empty():
                continue

            try:
                item_id = self.db.add_item(
                    category_id=draft.category_id,
                    label=item_field.get_final_label(),
                    content=item_field.content,
                    item_type=item_field.item_type,
                    is_sensitive=item_field.is_sensitive,
                    tags=draft.item_tags  # Solo tags de items (opcionales)
                )

                if item_id:
                    saved_count += 1
                    logger.debug(f"Item guardado (simple): {item_field.content[:30]}...")

            except Exception as e:
                logger.error(f"Error guardando item simple: {e}")

        # Guardar screenshots (si existen)
        screenshots_count = self._save_screenshots(
            draft=draft,
            category_id=draft.category_id,
            tags=draft.item_tags
        )
        saved_count += screenshots_count

        logger.info(f"✓ Modo SIMPLE: {saved_count} items guardados ({len(draft.items)} regulares + {screenshots_count} screenshots)")
        return saved_count

    def _save_as_list(self, draft: ItemDraft) -> int:
        """
        Guarda items como lista vinculada a proyecto/área

        Dos modos de operación:
        A) Si draft.list_id existe: Agregar items a lista existente
        B) Si no existe: Crear nueva lista (flujo original)

        Args:
            draft: Borrador con items, list_id/list_name y project_element_tags

        Returns:
            Cantidad de items guardados
        """
        saved_count = 0

        # Determinar si es proyecto o área
        is_project = draft.project_id is not None
        entity_id = draft.project_id if is_project else draft.area_id
        entity_name = "Proyecto" if is_project else "Área"

        try:
            # MODO A: Agregar a lista existente
            if draft.list_id:
                logger.info(f"Agregando items a LISTA EXISTENTE: '{draft.list_name}' (ID: {draft.list_id})")
                lista_id = draft.list_id

                # Paso 1.5: Preparar tags (lista existente)
                item_tags_with_list_name = draft.item_tags.copy() if draft.item_tags else []
                if draft.list_name and draft.list_name not in item_tags_with_list_name:
                    item_tags_with_list_name.append(draft.list_name)

                # Paso 2: Guardar items con list_id
                for item_field in draft.items:
                    if item_field.is_empty():
                        continue

                    try:
                        item_id = self.db.add_item(
                            category_id=draft.category_id,
                            label=item_field.get_final_label(),
                            content=item_field.content,
                            item_type=item_field.item_type,
                            is_sensitive=item_field.is_sensitive,
                            list_id=lista_id,
                            tags=item_tags_with_list_name
                        )

                        if item_id:
                            saved_count += 1
                            logger.debug(f"Item guardado en lista existente: {item_field.content[:30]}...")

                    except Exception as e:
                        logger.error(f"Error guardando item en lista existente: {e}")

                # Guardar screenshots (si existen)
                screenshots_count = self._save_screenshots(
                    draft=draft,
                    category_id=draft.category_id,
                    list_id=lista_id,
                    tags=item_tags_with_list_name
                )
                saved_count += screenshots_count

                logger.info(f"✓ {saved_count} items agregados a lista existente ({len(draft.items)} regulares + {screenshots_count} screenshots)")
                return saved_count

            # MODO B: Crear nueva lista (flujo original)
            logger.info(f"Creando NUEVA LISTA: '{draft.list_name}' → {entity_name} #{entity_id}")

            # Paso 1: Crear lista
            lista_id = self.db.create_lista(
                category_id=draft.category_id,
                name=draft.list_name,
                description=f"Lista creada desde {entity_name} #{entity_id}"
            )
            logger.debug(f"Lista creada: lista_id={lista_id}")

            # Paso 1.5: Preparar tags para los items
            # Combinar tags del usuario + tag automático con nombre de la lista
            item_tags_with_list_name = draft.item_tags.copy() if draft.item_tags else []
            if draft.list_name and draft.list_name not in item_tags_with_list_name:
                item_tags_with_list_name.append(draft.list_name)

            logger.info(f"Tags para items de lista: {item_tags_with_list_name}")

            # Paso 2: Guardar items con list_id
            for item_field in draft.items:
                if item_field.is_empty():
                    continue

                try:
                    item_id = self.db.add_item(
                        category_id=draft.category_id,
                        label=item_field.get_final_label(),
                        content=item_field.content,
                        item_type=item_field.item_type,
                        is_sensitive=item_field.is_sensitive,
                        list_id=lista_id,
                        tags=item_tags_with_list_name  # Tags opcionales + tag automático del nombre de la lista
                    )

                    if item_id:
                        saved_count += 1
                        logger.debug(f"Item guardado (lista): {item_field.content[:30]}...")

                except Exception as e:
                    logger.error(f"Error guardando item de lista: {e}")

            # Paso 3: Crear relación proyecto/área → lista
            if is_project:
                relation_id = self.db.add_project_relation(
                    project_id=draft.project_id,
                    entity_type='list',
                    entity_id=lista_id,
                    description=f"Lista: {draft.list_name}"
                )
                logger.debug(f"Relación proyecto-lista creada: relation_id={relation_id}")
            else:
                relation_id = self.db.add_area_relation(
                    area_id=draft.area_id,
                    entity_type='list',
                    entity_id=lista_id,
                    description=f"Lista: {draft.list_name}"
                )
                logger.debug(f"Relación área-lista creada: relation_id={relation_id}")

            # Paso 4: Asociar tags de proyecto/área a la relación
            for project_tag_name in draft.project_element_tags:
                # Obtener tag de proyecto (NO de tags global)
                if is_project:
                    project_tag = self.db.get_project_element_tag_by_name(project_tag_name)
                    if not project_tag:
                        # Si no existe, crearlo
                        project_tag_id = self.db.add_project_element_tag(project_tag_name)
                    else:
                        project_tag_id = project_tag['id']

                    self.db.add_tag_to_project_relation(relation_id, project_tag_id)
                else:
                    # Para áreas, usar tabla area_element_tags
                    area_tag = self.db.get_area_element_tag_by_name(project_tag_name)
                    if not area_tag:
                        area_tag_id = self.db.add_area_element_tag(project_tag_name)
                    else:
                        area_tag_id = area_tag['id']

                    self.db.assign_tag_to_area_relation(relation_id, area_tag_id)

                logger.debug(f"Tag '{project_tag_name}' asociado a lista")

            # Paso 5: Guardar orden en filtered_order para cada tag
            for project_tag_name in draft.project_element_tags:
                if is_project:
                    project_tag = self.db.get_project_element_tag_by_name(project_tag_name)
                    project_tag_id = project_tag['id'] if project_tag else None

                    if project_tag_id:
                        # Obtener el max order_index actual
                        filtered_orders = self.db.get_filtered_order(draft.project_id, project_tag_id)
                        max_order = max(filtered_orders.values()) if filtered_orders else -1
                        next_order = max_order + 1

                        # Guardar el orden
                        self.db.update_filtered_order(
                            draft.project_id,
                            project_tag_id,
                            'relation',
                            relation_id,
                            next_order
                        )
                        logger.debug(f"Orden guardado para tag '{project_tag_name}': {next_order}")
                else:
                    area_tag = self.db.get_area_element_tag_by_name(project_tag_name)
                    area_tag_id = area_tag['id'] if area_tag else None

                    if area_tag_id:
                        # Obtener el max order_index actual
                        filtered_orders = self.db.get_area_filtered_order(draft.area_id, area_tag_id)
                        max_order = max(filtered_orders.values()) if filtered_orders else -1
                        next_order = max_order + 1

                        # Guardar el orden
                        self.db.update_area_filtered_order(
                            draft.area_id,
                            area_tag_id,
                            'relation',
                            relation_id,
                            next_order
                        )
                        logger.debug(f"Orden guardado para tag '{project_tag_name}': {next_order}")

            # Paso 6: Guardar screenshots (si existen)
            screenshots_count = self._save_screenshots(
                draft=draft,
                category_id=draft.category_id,
                list_id=lista_id,
                tags=item_tags_with_list_name
            )
            saved_count += screenshots_count

            logger.info(f"✓ Modo LISTA: {saved_count} items + relación {entity_name.lower()} ({len(draft.items)} regulares + {screenshots_count} screenshots)")

        except Exception as e:
            logger.error(f"Error en guardado como lista: {e}")
            raise

        return saved_count

    def _save_screenshots(self, draft: ItemDraft, category_id: int, list_id: int = None, tags: list = None) -> int:
        """
        Guarda screenshots como items PATH en la base de datos

        Args:
            draft: Borrador con screenshots
            category_id: ID de la categoría
            list_id: ID de lista (opcional)
            tags: Tags a aplicar (opcional)

        Returns:
            Cantidad de screenshots guardados
        """
        if not draft.screenshots:
            return 0

        saved_count = 0

        logger.info(f"Guardando {len(draft.screenshots)} screenshots como items PATH")

        for screenshot_data in draft.screenshots:
            filepath = screenshot_data.get('filepath', '')
            label = screenshot_data.get('label', 'Captura')

            if not filepath:
                logger.warning("Screenshot sin filepath, omitiendo")
                continue

            try:
                # Obtener solo el nombre del archivo (relativo)
                import os
                filename = os.path.basename(filepath)

                # Extraer metadatos del archivo
                metadata = None
                if self.main_controller and hasattr(self.main_controller, 'screenshot_controller'):
                    screenshot_manager = self.main_controller.screenshot_controller.screenshot_manager
                    metadata = screenshot_manager.get_screenshot_metadata(filepath)

                if not metadata:
                    logger.warning(f"No se pudieron extraer metadatos de {filepath}")
                    # Continuar sin metadatos
                    metadata = {}

                # Extraer created_at de los metadatos si existe
                created_at_str = None
                if metadata.get('file_created_at'):
                    # Convertir datetime a string en formato SQLite
                    created_at_str = metadata['file_created_at'].strftime('%Y-%m-%d %H:%M:%S')

                # Crear item PATH con metadatos
                item_id = self.db.add_item(
                    category_id=category_id,
                    label=label,
                    content=filename,  # Solo nombre de archivo relativo
                    item_type='PATH',
                    list_id=list_id,
                    tags=tags or [],
                    file_size=metadata.get('file_size'),
                    file_type=metadata.get('file_type'),
                    file_extension=metadata.get('file_extension'),
                    original_filename=filename,  # Solo nombre de archivo relativo
                    file_hash=metadata.get('file_hash'),
                    created_at=created_at_str  # Fecha extraída del nombre del archivo
                )

                if item_id:
                    saved_count += 1
                    logger.debug(f"Screenshot guardado como item PATH: {label} ({filename})")

            except Exception as e:
                logger.error(f"Error guardando screenshot {filepath}: {e}", exc_info=True)

        logger.info(f"✓ {saved_count} screenshots guardados como items PATH")
        return saved_count

    def _on_create_project(self):
        """Callback para crear nuevo proyecto"""
        # Diálogo simple para nombre
        name, ok = QInputDialog.getText(
            self,
            "Crear Proyecto",
            "Nombre del proyecto:",
            text=""
        )

        if not ok or not name.strip():
            logger.info("Creación de proyecto cancelada")
            return

        try:
            # Crear proyecto en BD
            project_id = self.db.add_project(name=name.strip())

            if not project_id:
                QMessageBox.critical(self, "Error", "No se pudo crear el proyecto")
                return

            logger.info(f"Proyecto creado: {name} (ID: {project_id})")

            # Actualizar todos los tabs con el nuevo proyecto
            self._reload_projects_in_all_tabs()

            # Seleccionar el proyecto recién creado en el tab actual
            current_tab = self._get_current_tab_content()
            if current_tab:
                current_tab.context_section.set_project_id(project_id)

            QMessageBox.information(
                self,
                "Éxito",
                f"Proyecto '{name}' creado correctamente."
            )

        except Exception as e:
            logger.error(f"Error creando proyecto: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"Error al crear proyecto:\n{str(e)}"
            )

    def _on_create_area(self):
        """Callback para crear nueva área"""
        name, ok = QInputDialog.getText(
            self,
            "Crear Área",
            "Nombre del área:",
            text=""
        )

        if not ok or not name.strip():
            logger.info("Creación de área cancelada")
            return

        try:
            # Crear área en BD
            area_id = self.db.add_area(name=name.strip())

            if not area_id:
                QMessageBox.critical(self, "Error", "No se pudo crear el área")
                return

            logger.info(f"Área creada: {name} (ID: {area_id})")

            # Actualizar todos los tabs
            self._reload_areas_in_all_tabs()

            # Seleccionar área recién creada
            current_tab = self._get_current_tab_content()
            if current_tab:
                current_tab.context_section.set_area_id(area_id)

            QMessageBox.information(
                self,
                "Éxito",
                f"Área '{name}' creada correctamente."
            )

        except Exception as e:
            logger.error(f"Error creando área: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"Error al crear área:\n{str(e)}"
            )

    def _on_create_category(self):
        """Callback para crear nueva categoría"""
        name, ok = QInputDialog.getText(
            self,
            "Crear Categoría",
            "Nombre de la categoría:",
            text=""
        )

        if not ok or not name.strip():
            logger.info("Creación de categoría cancelada")
            return

        try:
            # Crear categoría en BD
            category_id = self.db.add_category(
                name=name.strip(),
                icon="📁",  # Icono por defecto
                is_predefined=False
            )

            if not category_id:
                QMessageBox.critical(self, "Error", "No se pudo crear la categoría")
                return

            logger.info(f"Categoría creada: {name} (ID: {category_id})")

            # IMPORTANTE: Invalidar caché del ConfigManager para que se recargue desde BD
            self.config._categories_cache = None

            # Actualizar todos los tabs
            self._reload_categories_in_all_tabs()

            # Seleccionar categoría recién creada
            current_tab = self._get_current_tab_content()
            if current_tab:
                current_tab.category_section.set_category_id(category_id)

            QMessageBox.information(
                self,
                "Éxito",
                f"Categoría '{name}' creada correctamente."
            )

        except Exception as e:
            logger.error(f"Error creando categoría: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"Error al crear categoría:\n{str(e)}"
            )

    def _on_create_project_tag(self):
        """Callback para crear nuevo tag de proyecto/área"""
        # Obtener tab actual
        current_tab = self._get_current_tab_content()
        if not current_tab:
            return

        # Verificar que haya proyecto o área seleccionado
        has_project_or_area = current_tab.context_section.has_project_or_area()
        if not has_project_or_area:
            QMessageBox.warning(
                self,
                "Proyecto/Área requerido",
                "Primero debe seleccionar un Proyecto o Área para crear tags asociados."
            )
            return

        # Solicitar nombre del tag
        name, ok = QInputDialog.getText(
            self,
            "Crear Tag de Proyecto/Área",
            "Nombre del tag:",
            text=""
        )

        if not ok or not name.strip():
            logger.info("Creación de tag de proyecto/área cancelada")
            return

        try:
            # Determinar si es proyecto o área
            project_id = current_tab.context_section.get_project_id()
            area_id = current_tab.context_section.get_area_id()

            # Usar el TagManager correcto según el tipo de entidad
            if project_id:
                tag_manager = self.project_tag_manager
                entity_type = "proyecto"
            elif area_id:
                tag_manager = self.area_tag_manager
                entity_type = "área"
            else:
                QMessageBox.warning(
                    self,
                    "Error",
                    "No se detectó proyecto ni área seleccionado."
                )
                return

            # Crear tag usando el TagManager correcto
            tag = tag_manager.create_tag(
                name=name.strip(),
                color="#2196F3",  # Color por defecto (azul)
                description=f"Tag creado desde Creador Masivo"
            )

            if not tag:
                QMessageBox.critical(
                    self,
                    "Error",
                    "No se pudo crear el tag. Puede que ya exista un tag con ese nombre."
                )
                return

            logger.info(f"Tag de {entity_type} creado: {name} (ID: {tag.id})")

            # Recargar tags en el tab actual
            if project_id:
                # Cargar tags del proyecto
                tags = tag_manager.get_tags_for_project(project_id)
                tag_names = [t.name for t in tags]

                # Agregar el tag recién creado si no está en la lista
                if name.strip() not in tag_names:
                    tag_names.append(name.strip())

                current_tab.project_tags_section.load_tags(tag_names)
                # Auto-seleccionar el tag recién creado
                current_tab.project_tags_section.add_tag(name.strip(), select=True)

            elif area_id:
                # Cargar tags del área
                tags = tag_manager.get_tags_for_area(area_id)
                tag_names = [t.name for t in tags]

                # Agregar el tag recién creado si no está en la lista
                if name.strip() not in tag_names:
                    tag_names.append(name.strip())

                current_tab.project_tags_section.load_tags(tag_names)
                # Auto-seleccionar el tag recién creado
                current_tab.project_tags_section.add_tag(name.strip(), select=True)

            QMessageBox.information(
                self,
                "Éxito",
                f"Tag '{name}' creado y seleccionado correctamente."
            )

        except Exception as e:
            logger.error(f"Error creando tag de proyecto/área: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"Error al crear tag:\n{str(e)}"
            )

    def _on_create_item_tag(self):
        """Callback para crear nuevo tag de item"""
        # Solicitar nombre del tag
        name, ok = QInputDialog.getText(
            self,
            "Crear Tag de Item",
            "Nombre del tag:",
            text=""
        )

        if not ok or not name.strip():
            logger.info("Creación de tag de item cancelada")
            return

        try:
            # Crear tag en la tabla general de tags (para items)
            tag_id = self.db.get_or_create_tag(name.strip())

            if not tag_id:
                QMessageBox.critical(self, "Error", "No se pudo crear el tag")
                return

            logger.info(f"Tag de item creado: {name} (ID: {tag_id})")

            # Obtener tab actual para auto-seleccionar el tag
            current_tab = self._get_current_tab_content()
            if current_tab:
                # Auto-seleccionar el tag recién creado
                current_tab.item_tags_section.add_tag(name.strip())

            QMessageBox.information(
                self,
                "Éxito",
                f"Tag '{name}' creado y agregado correctamente."
            )

        except Exception as e:
            logger.error(f"Error creando tag de item: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"Error al crear tag:\n{str(e)}"
            )

    def _on_create_list(self):
        """Callback para crear nueva lista"""
        # Obtener tab actual
        current_tab = self._get_current_tab_content()
        if not current_tab:
            return

        # Verificar que haya proyecto o área seleccionado
        project_id = current_tab.context_section.get_project_id()
        area_id = current_tab.context_section.get_area_id()

        if not project_id and not area_id:
            QMessageBox.warning(
                self,
                "Proyecto/Área requerido",
                "Primero debe seleccionar un Proyecto o Área para crear una lista asociada."
            )
            return

        # Verificar que haya tags de proyecto/área seleccionados
        selected_tags = current_tab.project_tags_section.get_selected_tags()
        if not selected_tags:
            QMessageBox.warning(
                self,
                "Tags requeridos",
                "Debe seleccionar al menos un tag de proyecto/área para crear la lista."
            )
            return

        # Verificar categoría seleccionada
        category_id = current_tab.category_section.get_category_id()
        if not category_id:
            QMessageBox.warning(
                self,
                "Categoría requerida",
                "Debe seleccionar una categoría antes de crear la lista."
            )
            return

        # Solicitar nombre de la lista
        name, ok = QInputDialog.getText(
            self,
            "Crear Lista",
            "Nombre de la lista:",
            text=""
        )

        if not ok or not name.strip():
            logger.info("Creación de lista cancelada")
            return

        try:
            # 1. Verificar si la lista ya existe (get_or_create)
            existing_lista = self.db.get_lista_by_name(category_id, name.strip())

            if existing_lista:
                lista_id = existing_lista['id']
                logger.info(f"Lista '{name}' ya existe en categoría {category_id}, reutilizando (ID: {lista_id})")
                was_created = False
            else:
                # Crear nueva lista
                lista_id = self.db.create_lista(
                    category_id=category_id,
                    name=name.strip(),
                    description=f"Lista creada desde Creador Masivo"
                )

                if not lista_id:
                    QMessageBox.critical(self, "Error", "No se pudo crear la lista")
                    return

                logger.info(f"Lista creada: {name} (ID: {lista_id})")
                was_created = True

            # 2. Crear relación proyecto/área → lista (si no existe ya)
            relation_id = None

            if project_id:
                # Verificar si ya existe la relación
                existing_relations = self.db.get_project_relations(project_id)
                existing_relation = next(
                    (r for r in existing_relations if r['entity_type'] == 'list' and r['entity_id'] == lista_id),
                    None
                )

                if existing_relation:
                    relation_id = existing_relation['id']
                    logger.debug(f"Relación proyecto-lista ya existe: {relation_id}")
                else:
                    relation_id = self.db.add_project_relation(
                        project_id=project_id,
                        entity_type='list',
                        entity_id=lista_id,
                        description=f"Lista: {name.strip()}"
                    )
                    logger.debug(f"Nueva relación proyecto-lista creada: {relation_id}")
            else:
                # Verificar si ya existe la relación con área
                existing_relations = self.db.get_area_relations(area_id)
                existing_relation = next(
                    (r for r in existing_relations if r['entity_type'] == 'list' and r['entity_id'] == lista_id),
                    None
                )

                if existing_relation:
                    relation_id = existing_relation['id']
                    logger.debug(f"Relación área-lista ya existe: {relation_id}")
                else:
                    relation_id = self.db.add_area_relation(
                        area_id=area_id,
                        entity_type='list',
                        entity_id=lista_id,
                        description=f"Lista: {name.strip()}"
                    )
                    logger.debug(f"Nueva relación área-lista creada: {relation_id}")

            # 3. Asociar tags de proyecto/área a la relación (evitar duplicados)
            logger.info(f"=== Asociando {len(selected_tags)} tags a relación {relation_id} ===")
            for tag_name in selected_tags:
                if project_id:
                    tag = self.db.get_project_element_tag_by_name(tag_name)
                    if tag:
                        logger.debug(f"Tag '{tag_name}' encontrado con ID: {tag['id']}")
                        # Verificar si el tag ya está asociado
                        existing_tags = self.db.get_tags_for_project_relation(relation_id)
                        logger.debug(f"Tags existentes en relación: {[t['id'] for t in existing_tags]}")
                        if tag['id'] not in [t['id'] for t in existing_tags]:
                            self.db.add_tag_to_project_relation(relation_id, tag['id'])
                            logger.info(f"✅ Tag '{tag_name}' (ID: {tag['id']}) asociado a relación proyecto-lista {relation_id}")
                        else:
                            logger.info(f"Tag '{tag_name}' (ID: {tag['id']}) ya estaba asociado a relación proyecto-lista {relation_id}")
                    else:
                        logger.warning(f"Tag '{tag_name}' no encontrado en BD")
                else:
                    tag = self.db.get_area_element_tag_by_name(tag_name)
                    if tag:
                        logger.debug(f"Tag '{tag_name}' encontrado con ID: {tag['id']}")
                        # Verificar si el tag ya está asociado
                        existing_tags = self.db.get_tags_for_area_relation(relation_id)
                        logger.debug(f"Tags existentes en relación: {[t['id'] for t in existing_tags]}")
                        if tag['id'] not in [t['id'] for t in existing_tags]:
                            self.db.assign_tag_to_area_relation(relation_id, tag['id'])
                            logger.info(f"✅ Tag '{tag_name}' (ID: {tag['id']}) asociado a relación área-lista {relation_id}")
                        else:
                            logger.info(f"Tag '{tag_name}' (ID: {tag['id']}) ya estaba asociado a relación área-lista {relation_id}")
                    else:
                        logger.warning(f"Tag '{tag_name}' no encontrado en BD")

            logger.info(f"=== Asociación de tags completada ===")

            # 4. Recargar listas desde BD (incluye la recién creada con todos sus tags)
            current_tab._reload_lists_by_tags()

            # 5. Seleccionar la lista recién creada/reutilizada
            current_tab.list_name_section.select_list_by_id(lista_id)

            # Mensaje de éxito diferente según si se creó o reutilizó
            action = "creada" if was_created else "reutilizada"
            entity_type = "proyecto" if project_id else "área"
            QMessageBox.information(
                self,
                "Éxito",
                f"Lista '{name}' {action} y relacionada con {entity_type} correctamente.\n"
                f"Tags asociados: {', '.join(selected_tags)}"
            )

        except Exception as e:
            logger.error(f"Error creando lista: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"Error al crear lista:\n{str(e)}"
            )

    def _on_close_clicked(self):
        """Callback del botón cerrar del header"""
        self.hide()

    # === MÉTODOS AUXILIARES ===

    def _get_current_tab_content(self) -> TabContentWidget | None:
        """Obtiene el TabContentWidget del tab actual"""
        index = self.tab_widget.currentIndex()
        if index < 0:
            return None

        widget = self.tab_widget.widget(index)
        if isinstance(widget, TabContentWidget):
            return widget
        return None

    def _reload_projects_in_all_tabs(self):
        """Recarga lista de proyectos en todos los tabs"""
        try:
            projects = self.db.get_all_projects() if hasattr(self.db, 'get_all_projects') else []
            projects_data = [(p['id'], p['name']) for p in projects]

            for i in range(self.tab_widget.count()):
                tab_content = self.tab_widget.widget(i)
                if isinstance(tab_content, TabContentWidget):
                    tab_content.load_available_projects(projects_data)

            logger.debug(f"Proyectos recargados en {self.tab_widget.count()} tabs")
        except Exception as e:
            logger.error(f"Error recargando proyectos: {e}")

    def _reload_areas_in_all_tabs(self):
        """Recarga lista de áreas en todos los tabs"""
        try:
            areas = self.db.get_all_areas() if hasattr(self.db, 'get_all_areas') else []
            areas_data = [(a['id'], a['name']) for a in areas]

            for i in range(self.tab_widget.count()):
                tab_content = self.tab_widget.widget(i)
                if isinstance(tab_content, TabContentWidget):
                    tab_content.load_available_areas(areas_data)

            logger.debug(f"Áreas recargadas en {self.tab_widget.count()} tabs")
        except Exception as e:
            logger.error(f"Error recargando áreas: {e}")

    def _reload_categories_in_all_tabs(self):
        """Recarga lista de categorías en todos los tabs"""
        try:
            categories = self.config.get_categories()
            categories_data = [(c.id, c.name) for c in categories]

            for i in range(self.tab_widget.count()):
                tab_content = self.tab_widget.widget(i)
                if isinstance(tab_content, TabContentWidget):
                    tab_content.load_available_categories(categories_data)

            logger.debug(f"Categorías recargadas en {self.tab_widget.count()} tabs")
        except Exception as e:
            logger.error(f"Error recargando categorías: {e}")

    def _on_refresh_clicked(self):
        """
        Callback del botón Actualizar

        Recarga todos los datos desde la base de datos:
        - Proyectos
        - Áreas
        - Categorías
        """
        try:
            logger.info("Actualizando datos desde la base de datos...")

            # Invalidar caché de categorías
            self.config._categories_cache = None

            # Recargar todos los datos en todos los tabs
            self._reload_projects_in_all_tabs()
            self._reload_areas_in_all_tabs()
            self._reload_categories_in_all_tabs()

            # Feedback visual temporal (cambiar ícono brevemente)
            current_tab = self._get_current_tab_content()
            if current_tab:
                # Mostrar mensaje breve en el info label
                original_text = self.info_label.text()
                self.info_label.setText("✓ Datos actualizados")
                self.info_label.setStyleSheet("color: #4CAF50; font-size: 9px; font-weight: bold;")

                # Restaurar después de 2 segundos
                QTimer.singleShot(2000, lambda: self._restore_info_label(original_text))

            logger.info("Datos actualizados correctamente")

        except Exception as e:
            logger.error(f"Error actualizando datos: {e}")
            self.info_label.setText("❌ Error al actualizar")
            self.info_label.setStyleSheet("color: #d32f2f; font-size: 9px;")
            QTimer.singleShot(3000, lambda: self._restore_info_label(f"{self.tab_widget.count()} tabs"))

    def _restore_info_label(self, original_text: str):
        """Restaura el info_label a su estado original"""
        self.info_label.setText(original_text)
        self.info_label.setStyleSheet("color: #888; font-size: 9px;")

    # === DRAGGING ===

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
        """Posicionar ventana a la izquierda del sidebar, completamente pegada"""
        try:
            if sidebar_window:
                # Método 1: Usar posición real del sidebar (como FloatingPanel)
                sidebar_x = sidebar_window.x()
                sidebar_y = sidebar_window.y()

                # Posicionar justo a la izquierda del sidebar, sin gap
                x = sidebar_x - CREATOR_WIDTH
                y = sidebar_y
            else:
                # Método 2: Fallback - calcular basado en geometría de pantalla
                screen = QApplication.primaryScreen()
                if not screen:
                    logger.warning("No se pudo obtener pantalla")
                    return

                screen_geometry = screen.availableGeometry()
                sidebar_width = 70
                x = screen_geometry.width() - CREATOR_WIDTH - sidebar_width
                y = screen_geometry.y()

            # Obtener altura de pantalla
            screen = QApplication.primaryScreen()
            if screen:
                height = screen.availableGeometry().height()
            else:
                height = CREATOR_MIN_HEIGHT

            self.setGeometry(x, y, CREATOR_WIDTH, height)
            logger.info(f"Ventana posicionada (pegada al sidebar): x={x}, y={y}, w={CREATOR_WIDTH}, h={height}")

        except Exception as e:
            logger.error(f"Error posicionando ventana: {e}")

    # === APPBAR API ===

    def register_appbar(self):
        """
        Registra la ventana como AppBar de Windows para reservar espacio permanentemente.
        Esto empuja las ventanas maximizadas para que no cubran el creador + sidebar.
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
            # Reservar espacio para: Creador Masivo (450px) + Sidebar (70px) = 520px desde el borde derecho
            abd.rc.left = self.x()  # Desde donde empieza el creador
            abd.rc.top = screen_geometry.y()
            abd.rc.right = screen_geometry.x() + screen_geometry.width()  # Hasta el borde derecho
            abd.rc.bottom = screen_geometry.y() + screen_geometry.height()

            # Registrar el AppBar
            result = ctypes.windll.shell32.SHAppBarMessage(ABM_NEW, ctypes.byref(abd))
            if result:
                logger.info(f"Creador Masivo registrado como AppBar - reservando {CREATOR_WIDTH + 70}px desde borde derecho")
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
            logger.info("Creador Masivo desregistrado como AppBar - espacio liberado")

        except Exception as e:
            logger.error(f"Error al desregistrar AppBar: {e}")

    # === EVENTOS ===

    def showEvent(self, event):
        """Cuando la ventana se muestra"""
        super().showEvent(event)
        # Posicionar y registrar AppBar con delay
        # Pasar referencia al sidebar (parent) para posicionamiento correcto
        QTimer.singleShot(100, lambda: self.position_window(self.parent()))
        QTimer.singleShot(200, self.register_appbar)
        logger.debug("BulkItemCreatorDialog shown - registering AppBar")

    def hideEvent(self, event):
        """Cuando la ventana se oculta"""
        self.unregister_appbar()
        super().hideEvent(event)
        self.closed.emit()
        logger.debug("BulkItemCreatorDialog hidden - unregistering AppBar")

    def closeEvent(self, event):
        """Al cerrar, ocultar ventana en lugar de destruirla"""
        logger.info("BulkItemCreatorDialog close requested - hiding instead")

        # Forzar guardado de todos los borradores pendientes
        self.draft_manager.force_save_all()

        # Desregistrar AppBar antes de ocultar
        self.unregister_appbar()

        # Emitir señal
        self.closed.emit()

        # Ocultar ventana en lugar de cerrarla (no destruir la instancia)
        event.ignore()
        self.hide()

        logger.info("BulkItemCreatorDialog hidden (not destroyed)")
