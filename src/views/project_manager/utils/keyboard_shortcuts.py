"""
Gestor de atajos de teclado para vista completa

Proporciona shortcuts de teclado para mejorar la productividad:
- Navegación rápida
- Copiado de items
- Control de vista
- Búsqueda

Autor: Widget Sidebar Team
Versión: 1.0
"""

from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtCore import Qt, QObject, pyqtSignal


class KeyboardShortcutManager(QObject):
    """
    Gestor centralizado de atajos de teclado

    Maneja todos los shortcuts para la vista completa,
    proporcionando una interfaz consistente.
    """

    # Señales
    copy_current_item = pyqtSignal()  # Copiar item actual
    search_requested = pyqtSignal()  # Abrir búsqueda
    next_item = pyqtSignal()  # Navegar al siguiente item
    previous_item = pyqtSignal()  # Navegar al item anterior
    expand_all = pyqtSignal()  # Expandir todas las secciones
    collapse_all = pyqtSignal()  # Colapsar todas las secciones
    scroll_to_top = pyqtSignal()  # Scroll al inicio
    scroll_to_bottom = pyqtSignal()  # Scroll al final
    refresh_requested = pyqtSignal()  # Refrescar vista

    def __init__(self, parent_widget):
        """
        Inicializar gestor de shortcuts

        Args:
            parent_widget: Widget padre (típicamente ProjectFullViewPanel)
        """
        super().__init__(parent_widget)
        self.parent_widget = parent_widget
        self.shortcuts = []
        self.enabled = True

    def setup_shortcuts(self):
        """
        Configurar todos los atajos de teclado

        IMPORTANTE: Llamar este método después de que el widget
        padre esté completamente inicializado.
        """
        self.shortcuts.clear()

        # === COPIADO ===
        # Ctrl+C: Copiar item seleccionado/enfocado
        copy_shortcut = QShortcut(QKeySequence.StandardKey.Copy, self.parent_widget)
        copy_shortcut.activated.connect(self._on_copy)
        self.shortcuts.append(copy_shortcut)

        # === BÚSQUEDA ===
        # Ctrl+F: Abrir búsqueda en vista
        search_shortcut = QShortcut(QKeySequence.StandardKey.Find, self.parent_widget)
        search_shortcut.activated.connect(self._on_search)
        self.shortcuts.append(search_shortcut)

        # === NAVEGACIÓN ===
        # Ctrl+Down: Siguiente item
        next_shortcut = QShortcut(QKeySequence("Ctrl+Down"), self.parent_widget)
        next_shortcut.activated.connect(self._on_next_item)
        self.shortcuts.append(next_shortcut)

        # Ctrl+Up: Item anterior
        prev_shortcut = QShortcut(QKeySequence("Ctrl+Up"), self.parent_widget)
        prev_shortcut.activated.connect(self._on_previous_item)
        self.shortcuts.append(prev_shortcut)

        # Home: Scroll al inicio
        home_shortcut = QShortcut(QKeySequence("Home"), self.parent_widget)
        home_shortcut.activated.connect(self._on_scroll_to_top)
        self.shortcuts.append(home_shortcut)

        # End: Scroll al final
        end_shortcut = QShortcut(QKeySequence("End"), self.parent_widget)
        end_shortcut.activated.connect(self._on_scroll_to_bottom)
        self.shortcuts.append(end_shortcut)

        # === EXPANSIÓN/COLAPSO ===
        # Ctrl+E: Expandir todas las secciones
        expand_shortcut = QShortcut(QKeySequence("Ctrl+E"), self.parent_widget)
        expand_shortcut.activated.connect(self._on_expand_all)
        self.shortcuts.append(expand_shortcut)

        # Ctrl+Shift+E: Colapsar todas las secciones
        collapse_shortcut = QShortcut(QKeySequence("Ctrl+Shift+E"), self.parent_widget)
        collapse_shortcut.activated.connect(self._on_collapse_all)
        self.shortcuts.append(collapse_shortcut)

        # === REFRESCAR ===
        # F5: Refrescar vista
        refresh_shortcut = QShortcut(QKeySequence.StandardKey.Refresh, self.parent_widget)
        refresh_shortcut.activated.connect(self._on_refresh)
        self.shortcuts.append(refresh_shortcut)

        # Ctrl+R: Refrescar vista (alternativo)
        refresh_alt_shortcut = QShortcut(QKeySequence("Ctrl+R"), self.parent_widget)
        refresh_alt_shortcut.activated.connect(self._on_refresh)
        self.shortcuts.append(refresh_alt_shortcut)

    def _on_copy(self):
        """Handler para copiar item"""
        if self.enabled:
            self.copy_current_item.emit()

    def _on_search(self):
        """Handler para búsqueda"""
        if self.enabled:
            self.search_requested.emit()

    def _on_next_item(self):
        """Handler para siguiente item"""
        if self.enabled:
            self.next_item.emit()

    def _on_previous_item(self):
        """Handler para item anterior"""
        if self.enabled:
            self.previous_item.emit()

    def _on_expand_all(self):
        """Handler para expandir todo"""
        if self.enabled:
            self.expand_all.emit()

    def _on_collapse_all(self):
        """Handler para colapsar todo"""
        if self.enabled:
            self.collapse_all.emit()

    def _on_scroll_to_top(self):
        """Handler para scroll al inicio"""
        if self.enabled:
            self.scroll_to_top.emit()

    def _on_scroll_to_bottom(self):
        """Handler para scroll al final"""
        if self.enabled:
            self.scroll_to_bottom.emit()

    def _on_refresh(self):
        """Handler para refrescar"""
        if self.enabled:
            self.refresh_requested.emit()

    def enable(self):
        """Habilitar todos los shortcuts"""
        self.enabled = True
        for shortcut in self.shortcuts:
            shortcut.setEnabled(True)

    def disable(self):
        """Deshabilitar todos los shortcuts"""
        self.enabled = False
        for shortcut in self.shortcuts:
            shortcut.setEnabled(False)

    def get_shortcuts_help(self) -> dict:
        """
        Obtener diccionario con ayuda de shortcuts

        Returns:
            Dict con categoría -> lista de (shortcut, descripción)
        """
        return {
            "Copiado": [
                ("Ctrl+C", "Copiar item seleccionado")
            ],
            "Búsqueda": [
                ("Ctrl+F", "Buscar en vista")
            ],
            "Navegación": [
                ("Ctrl+↓", "Siguiente item"),
                ("Ctrl+↑", "Item anterior"),
                ("Home", "Ir al inicio"),
                ("End", "Ir al final")
            ],
            "Vista": [
                ("Ctrl+E", "Expandir todas las secciones"),
                ("Ctrl+Shift+E", "Colapsar todas las secciones"),
                ("F5 / Ctrl+R", "Refrescar vista")
            ]
        }

    def print_shortcuts_help(self):
        """Imprimir ayuda de shortcuts en consola"""
        print("\n" + "=" * 70)
        print("ATAJOS DE TECLADO - VISTA COMPLETA")
        print("=" * 70)

        help_dict = self.get_shortcuts_help()

        for category, shortcuts in help_dict.items():
            print(f"\n{category}:")
            for shortcut, description in shortcuts:
                print(f"  {shortcut:<20} - {description}")

        print("\n" + "=" * 70 + "\n")


class ShortcutHelpWidget:
    """
    Helper para mostrar ayuda de shortcuts en UI

    Proporciona métodos para generar texto de ayuda
    formateado para mostrar en tooltips o diálogos.
    """

    @staticmethod
    def get_help_text(manager: KeyboardShortcutManager) -> str:
        """
        Obtener texto de ayuda formateado para UI

        Args:
            manager: KeyboardShortcutManager

        Returns:
            Texto HTML formateado
        """
        help_dict = manager.get_shortcuts_help()

        html = "<html><body style='font-family: Segoe UI; font-size: 12px;'>"
        html += "<h3 style='color: #FFD700; margin-bottom: 10px;'>Atajos de Teclado</h3>"

        for category, shortcuts in help_dict.items():
            html += f"<p style='margin-top: 15px; margin-bottom: 5px;'><b style='color: #00BFFF;'>{category}:</b></p>"
            html += "<table cellpadding='3'>"

            for shortcut, description in shortcuts:
                html += f"""
                <tr>
                    <td style='color: #32CD32; font-family: Consolas; padding-right: 15px;'>{shortcut}</td>
                    <td style='color: #E0E0E0;'>{description}</td>
                </tr>
                """

            html += "</table>"

        html += "</body></html>"

        return html

    @staticmethod
    def get_tooltip_text(manager: KeyboardShortcutManager, max_shortcuts: int = 5) -> str:
        """
        Obtener texto de ayuda breve para tooltip

        Args:
            manager: KeyboardShortcutManager
            max_shortcuts: Máximo de shortcuts a mostrar

        Returns:
            Texto formateado para tooltip
        """
        help_dict = manager.get_shortcuts_help()
        shortcuts = []

        # Recopilar todos los shortcuts
        for category_shortcuts in help_dict.values():
            shortcuts.extend(category_shortcuts)

        # Limitar cantidad
        shortcuts = shortcuts[:max_shortcuts]

        # Formatear
        text = "Atajos de teclado:\n"
        for shortcut, description in shortcuts:
            text += f"\n{shortcut}: {description}"

        if len(shortcuts) < sum(len(s) for s in help_dict.values()):
            text += f"\n\n... y más (presiona ? para ver todos)"

        return text
