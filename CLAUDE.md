# CLAUDE.md

Este archivo proporciona guía a Claude Code (claude.ai/code) al trabajar con código en este repositorio.

## Descripción del Proyecto

**SidePanel** es una aplicación de escritorio empresarial para Windows diseñada como un gestor avanzado de productividad, portapapeles y biblioteca de snippets. Construida con PyQt6 y SQLite, proporciona un sidebar persistente siempre visible en el borde derecho de la pantalla para acceso instantáneo a comandos, URLs, fragmentos de código, procesos automatizados, proyectos y gestión organizacional completa.

### Propósito
Maximizar la productividad mediante un hub centralizado que integra:
- Acceso inmediato a comandos y snippets sin cambiar de aplicación
- Organización multi-nivel: Items → Listas/Tablas → Categorías → Proyectos/Áreas
- Automatización de flujos de trabajo mediante procesos configurables
- Gestión de proyectos y áreas con relaciones entre entidades
- Búsqueda universal con FTS5 a través de todo el contenido
- Protección de información sensible con cifrado y autenticación
- Screenshots, galería de imágenes y navegador embebido
- Estadísticas avanzadas y tracking de uso

### Características Principales

#### Gestión de Contenido
- **Items avanzados**: TEXT, URL, CODE, PATH con cifrado, tags, favoritos, descripción
- **Listas**: Agrupamiento secuencial de items con orden y tracking
- **Tablas**: Estructura matricial para organización de items
- **Componentes**: Elementos visuales (dividers, comments, alerts, notes)
- **Procesos**: Flujos de ejecución con pasos configurables (secuencial/paralelo/manual)

#### Organización Multi-Nivel
- **Categorías**: Organización base con iconos emoji, colores, badges, pinning
- **Proyectos**: Agrupamiento de entidades (tags, procesos, listas, tablas, categorías, items)
- **Áreas**: Organización por área funcional (Frontend, Backend, DevOps, Database, etc.)
- **Tags globales**: Sistema de etiquetado multi-nivel con grupos de tags

#### Búsqueda y Filtrado
- **Búsqueda Universal (FTS5)**: Full-text search a través de TODA la aplicación
- **Búsqueda Avanzada**: Múltiples criterios, vistas (lista/tabla/árbol), filtros dinámicos
- **Filtrado Multi-Criterio**: Por texto, rangos numéricos, fechas, métricas, estados
- **Búsqueda Global**: Panel dedicado para búsqueda en tiempo real

#### Productividad
- **Procesos Automatizados**: Ejecución secuencial/paralela de pasos con tracking
- **Screenshots**: Captura completa/región con anotaciones y metadatos
- **Galería de Imágenes**: Grid, búsqueda, preview y edición de metadatos
- **Navegador Embebido**: Captura de snippets desde web, sesiones guardadas, bookmarks
- **Speed Dial**: Accesos rápidos visuales
- **Notebooks**: Cuadernos con pestañas para organización

#### Seguridad
- **Autenticación**: Contraseña maestra con hash bcrypt
- **Sesiones**: Gestión con expiración automática (24h)
- **Cifrado**: Fernet (simétrico) para items sensibles, transparente en BD
- **Validación**: Sistema de validación de items y contenido

#### UI y Paneles
- **Sidebar persistente**: Frameless, always-on-top (70px ancho, 100% altura)
- **Paneles flotantes**: Categorías, procesos, favoritos, estadísticas, búsqueda
- **Paneles fijados**: Persistencia de posición y configuración con shortcuts
- **Dashboard**: Visualización de métricas, sugerencias, items populares/olvidados
- **System Tray**: Minimiza a bandeja con menú contextual

#### Estadísticas y Tracking
- **Usage Tracking**: Contador de uso, última fecha, patrones temporales
- **Analytics**: Agregación y visualización de métricas
- **Sugerencias**: Items recomendados basados en uso
- **Reporting**: Items populares, olvidados, estadísticas detalladas

#### Características Técnicas
- **Hotkey global**: `Ctrl+Shift+V` muestra/oculta desde cualquier aplicación
- **Exportación/Importación**: JSON/CSV para proyectos, áreas y datos
- **Wizards con IA**: Creación masiva de items y tablas
- **Caché LRU**: Optimización de rendimiento en filtros y búsquedas
- **Migrations**: Sistema completo de migraciones de BD

**Versión:** 3.0.0 (SQLite Edition)
**Plataforma:** Windows 10/11
**Python:** 3.10+
**Complejidad:** 43+ managers, 150+ vistas, 16 modelos de datos, 19+ migraciones

## Comandos de Desarrollo

### Ejecutar la Aplicación
```bash
# Desde el código fuente (requiere Python 3.10+)
python main.py

# Desde entorno virtual
.\venv\Scripts\activate
python main.py
```

### Construir Ejecutable
```bash
# Construir .exe standalone con PyInstaller
build.bat

# Ubicación salida: dist\WidgetSidebar.exe
# Paquete distribución: WidgetSidebar_v2.0\
```

### Dependencias
```bash
# Instalar todas las dependencias
pip install -r requirements.txt

# Dependencias principales:
# - PyQt6 (6.7.0) - Framework GUI
# - PyQt6-WebEngine (6.7.0) - Navegador embebido
# - pyperclip (1.9.0) - Gestión del portapapeles
# - pynput (1.7.7) - Captura de hotkeys globales
# - cryptography (41.0.7) - Cifrado para items sensibles
# - python-dotenv (1.0.0) - Gestión de variables de entorno
# - matplotlib (3.8.0) - Gráficos y visualización de estadísticas
# - jsonschema (4.17.0) - Validación de esquemas JSON
# - mss (9.0.1) - Captura de screenshots
# - Pillow (10.1.0) - Procesamiento de imágenes
```

## Arquitectura

### Patrón MVC
La aplicación sigue la arquitectura Model-View-Controller:

- **Models** (`src/models/`): Estructuras de datos (Category, Item, Lista, Table, Process, Project, Area, Tags, Drafts)
- **Views** (`src/views/`): 150+ componentes UI PyQt6 organizados en:
  - Paneles principales (MainWindow, Sidebar, ContentPanel, FloatingPanel)
  - Diálogos especializados (dialogs/)
  - Widgets reutilizables (widgets/)
  - Dashboard y búsqueda avanzada (dashboard/, advanced_search/)
  - Galería de imágenes (image_gallery/)
  - Ventanas de configuración (SettingsWindow, 6 categorías de settings)
- **Controllers** (`src/controllers/`): Orquestación de lógica de negocio (MainController, ClipboardController, NavigationController, ProcessController, TableController, ListController, ScreenshotController, ImageGalleryController)

### Core Managers (`src/core/`) - 43+ Managers Especializados

#### Gestión de Contenido
- `config_manager.py`: Persistencia de configuración vía SQLite, CRUD de categorías/items
- `table_manager.py`: Gestión de tablas (estructura matricial), caché LRU
- `item_validation_service.py`: Validación de contenido de items
- `draft_persistence_manager.py`: Persistencia de borradores de items
- `component_manager.py`: Gestión de componentes visuales (dividers, notes, alerts)

#### Organización y Proyectos
- `project_manager.py`: CRUD de proyectos, relaciones entidad, componentes, caché LRU
- `area_manager.py`: CRUD de áreas, relaciones entidad, componentes, caché LRU
- `project_filter_engine.py`: Filtrado específico de proyectos
- `area_filter_engine.py`: Filtrado específico de áreas
- `project_export_manager.py`: Exportación/importación de proyectos
- `area_export_manager.py`: Exportación/importación de áreas
- `project_element_tag_manager.py`: Tags de elementos de proyecto
- `area_element_tag_manager.py`: Tags de elementos de área
- `global_tag_manager.py`: Tags globales reutilizables
- `category_tag_manager.py`: Tags de categorías
- `tag_groups_manager.py`: Grupos jerárquicos de tags
- `smart_collections_manager.py`: Colecciones dinámicas basadas en criterios

#### Búsqueda y Filtrado
- `universal_search_engine.py`: Búsqueda universal FTS5 en toda la aplicación
- `search_engine.py`: Búsqueda en tiempo real con debouncing (300ms)
- `category_filter_engine.py`: Filtrado de categorías con caché LRU
- `advanced_filter_engine.py`: Filtrado multi-criterio complejo

#### Seguridad y Autenticación
- `auth_manager.py`: Autenticación con hash bcrypt
- `session_manager.py`: Gestión de sesiones con expiración (24h)
- `encryption_manager.py`: Cifrado Fernet para contenido sensible
- `master_password_manager.py`: Gestión de contraseña maestra
- `master_auth_cache.py`: Caché de autenticación

#### Productividad
- `process_manager.py`: CRUD de procesos, validación, búsqueda
- `process_executor.py`: Ejecución secuencial/paralela de procesos
- `screenshot_manager.py`: Captura de pantalla (completa/región) con metadatos
- `annotation_engine.py`: Anotaciones sobre screenshots
- `file_manager.py`: Gestión de archivos
- `notebook_manager.py`: Cuadernos con pestañas
- `workarea_manager.py`: Gestión de espacios de trabajo

#### Navegador
- `simple_browser_manager.py`: Navegador simple embebido
- `browser_session_manager.py`: Gestión de sesiones de navegador
- `browser_profile_manager.py`: Gestión de perfiles de navegador
- `speed_dial_generator.py`: Generación de accesos rápidos

#### Estadísticas y Tracking
- `usage_tracker.py`: Tracking de uso de items (contador, última fecha, patrones)
- `stats_manager.py`: Agregación de estadísticas para dashboard
- `dashboard_manager.py`: Gestión del dashboard estadístico
- `favorites_manager.py`: Seguimiento y gestión de favoritos

#### UI y Paneles
- `floating_panels_manager.py`: Gestión de paneles flotantes
- `pinned_panels_manager.py`: Gestión de paneles fijados con persistencia
- `left_sidebar_manager.py`: Gestión del sidebar izquierdo
- `notification_manager.py`: Sistema de notificaciones in-app
- `advanced_taskbar_manager.py`: Integración avanzada con taskbar de Windows
- `taskbar_minimizable_mixin.py`: Mixin para minimización en taskbar

#### Sistema
- `clipboard_manager.py`: Operaciones de portapapeles usando pyperclip
- `hotkey_manager.py`: Manejo de hotkeys globales con pynput
- `tray_manager.py`: Integración con bandeja del sistema (system tray)
- `state_manager.py`: Gestión del estado de la aplicación
- `alert_service.py`: Sistema de alertas

#### IA y Automatización
- `ai_bulk_manager.py`: Creación masiva de items con IA
- `ai_table_manager.py`: Creación de tablas con asistencia de IA

#### Exportación y Validación
- `table_exporter.py`: Exportación de tablas a diferentes formatos
- `table_validator.py`: Validación de estructura de tablas

### Capa de Base de Datos (`src/database/`)
La aplicación utiliza SQLite con FTS5 para persistencia y búsqueda de texto completo:

- `db_manager.py`: Operaciones de BD con context managers, FTS5, auto-cifrado de items sensibles
- `migrations/`: 19+ migraciones de esquema (ver directorio `src/database/migrations/`)
- Archivo de BD: `widget_sidebar.db` (se crea automáticamente en primera ejecución)

#### Tablas Principales (40+ tablas)

**Configuración y Sistema:**
- `settings` - Configuración general
- `sessions` - Sesiones de usuario con expiración
- `panel_settings` - Dimensiones y posición de paneles

**Gestión de Contenido:**
- `categories` - Categorías con iconos, colores, badges, pinning, métricas
- `items` - Items avanzados con soporte para listas/tablas/componentes/archivos
- `listas` - Listas de items (v3.1.0 refactorización)
- `tables` - Tablas (estructura matricial)
- `clipboard_history` - Historial de portapapeles
- `item_usage_history` - Tracking detallado de uso de items
- `item_drafts` - Borradores de items

**Organización Multi-Nivel:**
- `projects` - Proyectos
- `project_relations` - Relaciones proyecto ↔ entidad
- `project_components` - Componentes visuales de proyecto
- `project_element_tags` - Tags de elementos de proyecto
- `project_drafts` - Borradores de proyectos
- `project_filtered_order` - Orden filtrado de proyectos
- `areas` - Áreas funcionales
- `area_relations` - Relaciones área ↔ entidad
- `area_components` - Componentes visuales de área
- `area_element_tags` - Tags de elementos de área
- `area_filtered_order` - Orden filtrado de áreas

**Tags y Colecciones:**
- `tag_groups` - Grupos jerárquicos de tags
- `item_tags` - Asociaciones tag-item
- `category_tags` - Tags de categorías
- `smart_collections` - Colecciones dinámicas

**Procesos:**
- `processes` - Procesos (flujos de trabajo)
- `process_items` - Pasos de proceso (process_steps)
- `process_execution_history` - Historial de ejecución de procesos

**Paneles:**
- `pinned_panels` - Paneles fijados (categorías, búsqueda global)
- `pinned_process_panels` - Paneles de procesos fijados

**Navegador:**
- `browser_config` - Configuración del navegador embebido
- `browser_profiles` - Perfiles de navegador
- `browser_sessions` - Sesiones de navegación guardadas
- `session_tabs` - Pestañas de sesiones
- `bookmarks` - Marcadores del navegador
- `speed_dials` - Speed dials (accesos rápidos visuales)

**Componentes:**
- `component_types` - Tipos de componentes disponibles

**Búsqueda FTS5:**
- `fts_items` - Índice FTS5 para búsqueda de texto completo
- `search_history` - Historial de búsquedas

**Notebooks:**
- `notebook_tabs` - Pestañas de notebooks
- (Configuraciones adicionales en settings)

**Importante:** La conexión a BD usa `check_same_thread=False` para compatibilidad con PyQt6. Siempre usar el context manager de transacciones para operaciones de escritura:
```python
with db.transaction() as conn:
    conn.execute(...)
```

**Cifrado de Items Sensibles:** Items marcados con `is_sensitive=True` tienen su campo `content` automáticamente cifrado en la capa de BD usando cifrado Fernet. El cifrado/descifrado ocurre transparentemente en `DBManager.add_item()`, `DBManager.update_item()`, y `DBManager.get_items_by_category()`.

### Flujo de Punto de Entrada
1. `main.py` inicializa logging y maneja rutas de ejecución frozen/script
2. Crea instancia de QApplication
3. **Flujo de autenticación:**
   - `SessionManager` verifica sesión válida
   - Si es primera vez: `FirstTimeWizard` para creación de contraseña
   - Si es usuario recurrente: `LoginDialog` para ingreso de contraseña
   - En fallo: sale de la aplicación
4. Crea `MainController` que inicializa `ConfigManager` con SQLite
5. `ConfigManager` carga categorías/items desde BD (auto-descifra items sensibles)
6. `MainWindow` se crea con referencia al controller
7. Se inicializan hotkey manager y tray manager
8. Categorías se cargan en UI del sidebar

### Arquitectura de Ventanas (150+ Vistas)

#### Ventanas Principales
- **MainWindow** (`main_window.py`): Sidebar frameless, always-on-top (70px ancho, 100% altura disponible)
- **SettingsWindow** (`settings_window.py`): Ventana de configuración con 6 categorías de settings

#### Paneles Flotantes
- **FloatingPanel** (`floating_panel.py`): Panel flotante para items de categoría
- **FavoritesFloatingPanel** (`favorites_floating_panel.py`): Panel de favoritos
- **StatsFloatingPanel** (`stats_floating_panel.py`): Dashboard estadístico
- **ProcessesFloatingPanel** (`processes_floating_panel.py`): Panel de procesos
- **PinnedPanelsWindow** (`pinned_panels_window.py`): Gestión de paneles fijados
- **PinnedPanelsManagerWindow** (`pinned_panels_manager_window.py`): Manager de paneles

#### Búsqueda
- **GlobalSearchPanel** (`global_search_panel.py`): Búsqueda global en tiempo real
- **AdvancedSearchWindow** (`advanced_search/`): Búsqueda avanzada con vistas lista/tabla/árbol
- **UniversalSearchDialog** (`dialogs/universal_search_dialog.py`): Búsqueda universal FTS5
- **CategoryFilterWindow** (`category_filter_window.py`): Filtrado de categorías
- **AdvancedFiltersWindow** (`advanced_filters_window.py`): Filtrado multi-criterio

#### Gestión de Proyectos y Áreas
- **ProjectsWindow** (`projects_window.py`): Gestión de proyectos
- **AreasWindow** (`areas_window.py`): Gestión de áreas
- **ProjectEditorDialog** (`dialogs/project_editor_dialog.py`): Editor CRUD de proyectos
- **ProjectExportDialog** (`dialogs/project_export_dialog.py`): Exportación de proyectos
- **ProjectImportDialog** (`dialogs/project_import_dialog.py`): Importación de proyectos

#### Gestión de Contenido
- **CategoryEditor** (`category_editor.py`): Editor CRUD de categorías
- **ItemEditorDialog** (`item_editor_dialog.py`): Editor CRUD de items con validación
- **TablesManagerWindow** (`tables_manager_window.py`): Gestión de tablas
- **TableEditorDialog** (`dialogs/table_editor_dialog.py`): Editor de tablas
- **TableViewDialog** (`dialogs/table_view_dialog.py`): Vista de tabla
- **ListCreatorDialog** (`dialogs/list_creator_dialog.py`): Creación de listas
- **ListEditorDialog** (`dialogs/list_editor_dialog.py`): Edición de listas

#### Productividad
- **ProcessBuilderWindow** (`process_builder_window.py`): Constructor de procesos
- **ProcessStepConfigDialog** (`dialogs/process_step_config_dialog.py`): Configuración de pasos
- **ScreenshotOverlay** (`screenshot_overlay.py`): Overlay para captura de screenshots
- **NotebookWindow** (`notebook_window.py`): Cuadernos con pestañas
- **CalendarWindow** (`calendar_window.py`): Vista de calendario

#### Navegador
- **SimpleBrowserWindow** (`simple_browser_window.py`): Navegador simple embebido
- **EmbeddedBrowserDialog** (`dialogs/embedded_browser_dialog.py`): Navegador para captura de snippets
- **SessionDialog** (`session_dialog.py`): Gestión de sesiones de navegador
- **SaveSessionDialog** (`save_session_dialog.py`): Guardar sesión de navegador
- **BookmarksPanel** (`bookmarks_panel.py`): Panel de marcadores
- **SpeedDialDialog** (`speed_dial_dialog.py`): Diálogo de speed dial

#### Galería y Multimedia
- **ImageGalleryWindow** (`image_gallery/`): Galería de imágenes con:
  - `image_grid_widget.py` - Grid de imágenes
  - `image_search_panel.py` - Búsqueda de imágenes
  - `image_card_widget.py` - Tarjeta de imagen
  - `image_preview_dialog.py` - Preview de imagen
  - `edit_metadata_dialog.py` - Edición de metadatos

#### Autenticación
- **FirstTimeWizard** (`first_time_wizard.py`): Configuración inicial de contraseña
- **LoginDialog** (`login_dialog.py`): Autenticación en ejecuciones subsecuentes
- **PasswordVerifyDialog** (`dialogs/password_verify_dialog.py`): Verificación de contraseña

#### Wizards con IA
- **AIBulkWizard** (`dialogs/ai_bulk_wizard.py`): Creación masiva de items con IA
- **AITableWizard** (`dialogs/ai_table_wizard.py`): Creación de tablas con IA
- **BulkItemDialog** (`dialogs/bulk_item_dialog.py`): Creación masiva manual
- **TableCreatorWizard** (`dialogs/table_creator_wizard.py`): Wizard de creación de tablas

#### Diálogos Especializados
- **StatsDashboard** (`dialogs/stats_dashboard.py`): Dashboard de estadísticas
- **PopularItemsDialog** (`dialogs/popular_items_dialog.py`): Items populares
- **ForgottenItemsDialog** (`dialogs/forgotten_items_dialog.py`): Items olvidados
- **FavoriteSuggestionsDialog** (`dialogs/suggestions_dialog.py`): Sugerencias de favoritos
- **ItemDetailsDialog** (`dialogs/item_details_dialog.py`): Detalles completos de item
- **QuickCreateDialog** (`dialogs/quick_create_dialog.py`): Creación rápida
- **PanelConfigDialog** (`dialogs/panel_config_dialog.py`): Configuración de panel
- **PanelCustomizationDialog** (`dialogs/panel_customization_dialog.py`): Personalización
- **TagGroupsDialog** (`dialogs/tag_groups_dialog.py`): Gestión de grupos de tags
- **SmartCollectionsDialog** (`dialogs/smart_collections_dialog.py`): Colecciones inteligentes
- **ComponentManagerDialog** (`dialogs/component_manager_dialog.py`): Gestión de componentes
- **CommandOutputDialog** (`command_output_dialog.py`): Salida de comandos

#### Configuraciones Especializadas (6 Categorías)
- **GeneralSettings** (`general_settings.py`): Configuración general
- **AppearanceSettings** (`appearance_settings.py`): Personalización visual
- **HotkeySettings** (`hotkey_settings.py`): Configuración de hotkeys
- **OrganizationSettings** (`organization_settings.py`): Organización
- **BrowserSettings** (`browser_settings.py`): Configuración del navegador
- **FilesSettings** (`files_settings.py`): Gestión de archivos
- **ScreenshotSettings** (`screenshot_settings.py`): Configuración de screenshots

### Comunicación Signal/Slot
Las señales PyQt6 conectan componentes a través de toda la aplicación:

**Señales Principales:**
- `category_selected(str)`: Categoría seleccionada en sidebar
- `item_selected(Item)`: Item seleccionado en panel de contenido
- `item_copied(Item)`: Item copiado exitosamente al portapapeles
- `filters_applied()`: Filtros aplicados a categorías
- `tag_group_selected()`: Grupo de tags seleccionado
- `process_state_changed()`: Estado de proceso cambiado
- `search_query_changed(str)`: Query de búsqueda modificada
- `panel_toggled(bool)`: Panel mostrado/ocultado
- `item_usage_tracked(int)`: Uso de item registrado
- `favorites_updated()`: Lista de favoritos actualizada
- `project_modified()`: Proyecto modificado
- `area_modified()`: Área modificada

## Detalles Clave de Implementación

### Autenticación y Seguridad
- **Protección con Contraseña**: Primera ejecución muestra `FirstTimeWizard` para establecer contraseña maestra
- **Gestión de Sesiones**: Las sesiones expiran automáticamente (24h por defecto), almacenadas en BD
- **Hash de Contraseñas**: Usa bcrypt vía `AuthManager` para almacenamiento seguro
- **Cifrado**: Items sensibles cifrados con Fernet (cifrado simétrico)
  - Clave de cifrado almacenada en archivo `.env` (auto-generada en primera ejecución)
  - Derivación de clave: PBKDF2 desde contraseña maestra
  - Cifrado/descifrado transparente en capa de BD

### Sistema de Hotkeys
- Hotkey global `Ctrl+Shift+V` alterna visibilidad del widget desde cualquier aplicación
- Gestionado por `HotkeyManager` usando listener de teclado pynput
- Ejecuta en thread de fondo, comunica vía señales PyQt6

### Bandeja del Sistema
- Minimiza a system tray en lugar de cerrar
- Menú contextual: Mostrar/Ocultar, Configuración, Salir
- Doble clic en ícono del tray restaura la ventana

### Sistema de Búsqueda Multi-Nivel

#### Búsqueda Universal (FTS5)
**Archivo:** `src/core/universal_search_engine.py`
- Full-text search a través de TODA la aplicación usando FTS5
- Índice automático de items con reconstrucción y optimización
- Búsqueda de tipos: ITEM, TAG, CATEGORY_TAG, PROJECT_TAG, AREA_TAG
- Filtrado por entidades (proyectos, áreas, categorías, tablas, procesos, listas)
- Resultados con relaciones completas (ItemRelationships)
- Diálogo: `UniversalSearchDialog` con interfaz avanzada

#### Búsqueda Avanzada
**Directorio:** `src/views/advanced_search/`
- Múltiples vistas de resultados:
  - Lista (`results_list_view.py`)
  - Tabla (`results_table_view.py`)
  - Árbol jerárquico (`results_tree_view.py`)
- Panel izquierdo de filtros (`left_panel.py`)
- Búsqueda multi-criterio compleja
- Exportación de resultados

#### Búsqueda Global (Tiempo Real)
**Archivo:** `src/views/global_search_panel.py`
- Búsqueda en tiempo real con debouncing (300ms)
- Busca a través de TODOS los items en TODAS las categorías
- Muestra contexto de categoría para cada resultado
- Clic en resultado copia al portapapeles
- Puede fijarse como panel persistente

#### Búsqueda por Categoría
**Archivo:** `src/views/widgets/search_bar.py`
- Filtrado en tiempo real dentro de categoría activa
- Debounce de 300ms
- Coincidencia fuzzy en nombres y contenido

### Sistema de Filtrado

#### Filtrado de Categorías
**Archivo:** `src/core/category_filter_engine.py`
- Caché LRU para rendimiento
- Filtrado por estado activo/fijado
- Ventana: `CategoryFilterWindow`

#### Filtrado Avanzado Multi-Criterio
**Archivo:** `src/core/advanced_filter_engine.py`
- Búsqueda de texto (nombre, tags, contenido)
- Rangos numéricos (conteo de items)
- Métricas de uso (conteo de accesos, rangos de fechas)
- Lógica AND entre múltiples criterios
- Ventana: `AdvancedFiltersWindow`
- Widget: `AdvancedFilterPanel`

#### Filtrado de Proyectos y Áreas
- `project_filter_engine.py`: Filtrado específico de proyectos
- `area_filter_engine.py`: Filtrado específico de áreas

### Sistema de Favoritos y Tracking

#### Favoritos
**Manager:** `src/core/favorites_manager.py`
- Items marcados con `is_favorite` y `favorite_order`
- Panel dedicado: `FavoritesFloatingPanel`
- Widget: `favorites_panel.py`

#### Tracking de Uso
**Manager:** `src/core/usage_tracker.py`
- Tabla: `item_usage_history` con tracking detallado
- Métricas capturadas:
  - Timestamp de uso (`used_at`)
  - Tiempo de ejecución (`execution_time_ms`)
  - Estado de éxito/fallo (`success`, `error_message`)
  - Contador acumulativo en item (`use_count`)
  - Última fecha de uso (`last_used`)
- Analytics basados en tiempo (patrones de uso)

#### Estadísticas
**Manager:** `src/core/stats_manager.py`
- Agregación de métricas de uso
- Computación de estadísticas avanzadas
- Identificación de:
  - Items populares (`PopularItemsDialog`)
  - Items olvidados (`ForgottenItemsDialog`)
  - Sugerencias de favoritos (`FavoriteSuggestionsDialog`)
- Dashboard: `StatsFloatingPanel` y `StatsDashboard`
- Widgets de visualización con matplotlib

### Sistema de Tags Multi-Nivel

#### Tags Globales
**Manager:** `src/core/global_tag_manager.py`
- Tags reutilizables en toda la aplicación
- Asociación flexible a items, categorías, proyectos, áreas

#### Tags de Items
- Campo `tags` (TEXT) en tabla `items`
- Tabla `item_tags` para asociaciones
- Múltiples tags por item

#### Tags de Categorías
**Manager:** `src/core/category_tag_manager.py`
- Campo `tags` en tabla `categories`
- Tabla `category_tags` para gestión

#### Tags de Elementos de Proyecto/Área
**Managers:**
- `project_element_tag_manager.py`: Tags de elementos en proyectos
- `area_element_tag_manager.py`: Tags de elementos en áreas
- Tablas: `project_element_tags`, `area_element_tags`
- Permite etiquetar relaciones específicas dentro de proyectos/áreas

#### Grupos de Tags
**Manager:** `src/core/tag_groups_manager.py`
- Agrupamiento jerárquico de tags
- Tabla: `tag_groups`
- Diálogos: `TagGroupsDialog`, `TagGroupEditorDialog`
- Widget: `tag_group_selector.py`

#### Colecciones Inteligentes
**Manager:** `src/core/smart_collections_manager.py`
- Colecciones dinámicas basadas en criterios
- Auto-actualización según reglas
- Tabla: `smart_collections`
- Diálogos: `SmartCollectionsDialog`, `SmartCollectionEditorDialog`

### Persistencia de Configuración
**Migración de JSON a SQLite:** La aplicación originalmente usaba archivos JSON (`config.json`, `default_categories.json`). Ahora usa SQLite exclusivamente. El script `build.bat` incluye paso de migración de JSON a BD.

### Build con PyInstaller
- Archivo spec: `widget_sidebar.spec`
- Incluye base de datos SQLite, recursos, e imports ocultos para pynput
- Modo consola deshabilitado (`console=False`)
- Compresión UPX habilitada

## Estructura del Proyecto
```
widget_sidebar/
├── main.py                         # Punto de entrada de la aplicación
├── widget_sidebar.db               # Base de datos SQLite (40+ tablas, auto-creada)
├── widget_sidebar_error.log        # Log de errores y debug
├── requirements.txt                # Dependencias Python (10 paquetes principales)
├── widget_sidebar.spec             # Configuración PyInstaller
├── build.bat                       # Script de build para exe de Windows
├── .env                            # Variables de entorno (clave cifrado, auto-generada)
├── .gitignore                      # Exclusiones de git
├── CLAUDE.md                       # Guía para Claude Code (este archivo)
├── README.md                       # Documentación principal
├── LICENSE                         # Licencia MIT
│
└── src/
    ├── __init__.py
    │
    ├── models/                     # 16 Modelos de Datos
    │   ├── category.py             # Categoría con métricas y pinning
    │   ├── item.py                 # Item multi-tipo con cifrado
    │   ├── lista.py                # Lista de items (v3.1.0)
    │   ├── table.py                # Tabla matricial
    │   ├── process.py              # Proceso y ProcessStep
    │   ├── project.py              # Project, ProjectRelation, ProjectComponent
    │   ├── area.py                 # Area, AreaRelation, AreaComponent
    │   ├── config.py               # Configuración general
    │   ├── bulk_item_data.py       # Datos de creación masiva
    │   ├── ai_table_data.py        # Datos de tabla con IA
    │   ├── component_type.py       # Tipos de componentes
    │   ├── project_element_tag.py  # Tags de elementos de proyecto
    │   ├── area_element_tag.py     # Tags de elementos de área
    │   ├── category_tag.py         # Tags de categorías
    │   ├── item_draft.py           # Borradores de items
    │   └── __init__.py
    │
    ├── views/                      # 150+ Vistas y Componentes UI
    │   ├── main_window.py          # Ventana principal frameless
    │   ├── sidebar.py              # Sidebar de categorías
    │   ├── content_panel.py        # Panel de contenido
    │   ├── floating_panel.py       # Panel flotante de categoría
    │   ├── settings_window.py      # Ventana de configuración (6 tabs)
    │   ├── first_time_wizard.py    # Wizard de configuración inicial
    │   ├── login_dialog.py         # Diálogo de login
    │   ├── item_editor_dialog.py   # Editor de items
    │   ├── category_editor.py      # Editor de categorías
    │   │
    │   ├── dialogs/                # 30+ Diálogos Especializados
    │   │   ├── project_editor_dialog.py
    │   │   ├── ai_bulk_wizard.py
    │   │   ├── ai_table_wizard.py
    │   │   ├── stats_dashboard.py
    │   │   ├── universal_search_dialog.py
    │   │   ├── table_creator_wizard.py
    │   │   └── ... (más diálogos)
    │   │
    │   ├── widgets/                # 40+ Widgets Reutilizables
    │   │   ├── search_bar.py
    │   │   ├── item_widget.py
    │   │   ├── process_widget.py
    │   │   ├── favorites_panel.py
    │   │   ├── responsive_card_grid.py
    │   │   └── ... (más widgets)
    │   │
    │   ├── dashboard/              # Dashboard de Estructura
    │   │   ├── search_bar_widget.py
    │   │   ├── action_bar_widget.py
    │   │   ├── tags_filter_sidebar.py
    │   │   └── selection_utils_widget.py
    │   │
    │   ├── advanced_search/        # Búsqueda Avanzada Multi-Vista
    │   │   ├── left_panel.py
    │   │   ├── results_list_view.py
    │   │   ├── results_table_view.py
    │   │   └── results_tree_view.py
    │   │
    │   ├── image_gallery/          # Galería de Imágenes
    │   │   ├── image_grid_widget.py
    │   │   ├── image_search_panel.py
    │   │   ├── image_card_widget.py
    │   │   ├── image_preview_dialog.py
    │   │   └── edit_metadata_dialog.py
    │   │
    │   ├── projects_window.py      # Gestión de proyectos
    │   ├── areas_window.py         # Gestión de áreas
    │   ├── tables_manager_window.py
    │   ├── processes_floating_panel.py
    │   ├── simple_browser_window.py
    │   ├── notebook_window.py
    │   ├── calendar_window.py
    │   ├── screenshot_overlay.py
    │   └── ... (40+ vistas más)
    │
    ├── controllers/                # 9 Controladores
    │   ├── main_controller.py      # Controlador principal (orquestación)
    │   ├── clipboard_controller.py # Lógica de portapapeles
    │   ├── navigation_controller.py
    │   ├── process_controller.py
    │   ├── table_controller.py
    │   ├── list_controller.py
    │   ├── screenshot_controller.py
    │   ├── image_gallery_controller.py
    │   └── __init__.py
    │
    ├── core/                       # 43+ Managers Especializados
    │   ├── config_manager.py       # Persistencia SQLite
    │   ├── universal_search_engine.py  # Búsqueda FTS5
    │   ├── project_manager.py      # Gestión de proyectos
    │   ├── area_manager.py         # Gestión de áreas
    │   ├── process_manager.py      # Gestión de procesos
    │   ├── process_executor.py     # Ejecución de procesos
    │   ├── table_manager.py        # Gestión de tablas
    │   ├── auth_manager.py         # Autenticación
    │   ├── encryption_manager.py   # Cifrado Fernet
    │   ├── session_manager.py      # Sesiones de usuario
    │   ├── screenshot_manager.py   # Capturas de pantalla
    │   ├── usage_tracker.py        # Tracking de uso
    │   ├── stats_manager.py        # Estadísticas
    │   ├── favorites_manager.py    # Favoritos
    │   ├── hotkey_manager.py       # Hotkeys globales
    │   ├── tray_manager.py         # System tray
    │   ├── clipboard_manager.py    # Portapapeles
    │   ├── notification_manager.py # Notificaciones
    │   ├── pinned_panels_manager.py
    │   ├── ai_bulk_manager.py      # IA para creación masiva
    │   ├── ai_table_manager.py     # IA para tablas
    │   └── ... (30+ managers más)
    │
    ├── database/                   # Gestión de Base de Datos
    │   ├── db_manager.py           # Manager principal SQLite+FTS5
    │   ├── migrations.py           # Sistema de migraciones
    │   └── migrations/             # 19+ Migraciones
    │       ├── add_projects_tables.py
    │       ├── add_areas_tables.py
    │       ├── add_fts5_search_tables.py
    │       ├── add_item_drafts_table.py
    │       └── ... (15+ migraciones más)
    │
    ├── utils/                      # Utilidades
    │   ├── animations.py           # Animaciones PyQt6
    │   ├── validators.py           # Validadores de datos
    │   ├── constants.py            # Constantes globales
    │   ├── logger.py               # Configuración de logging
    │   └── __init__.py
    │
    ├── styles/                     # Estilos y Temas
    │   ├── animations.py
    │   ├── effects.py
    │   └── __init__.py
    │
    ├── resources/                  # Recursos Estáticos
    │   └── ... (iconos, imágenes, etc.)
    │
    └── assets/                     # Assets adicionales
        └── ... (recursos multimedia)
│
└── util/                           # Archivos Temporales (NO en git)
    ├── test_*.py                   # Scripts de prueba
    ├── debug_*.py                  # Scripts de debug
    ├── migrate_*.py                # Migraciones one-time
    ├── complete_schema.sql         # Esquema SQL completo
    └── FASE*.md                    # Documentación temporal
```

**Nota sobre `util/`:** Esta carpeta está excluida del repositorio git y contiene archivos temporales de desarrollo local.

## Convenciones Importantes

### Organización de Archivos Temporales y de Desarrollo

**IMPORTANTE:** Para mantener el repositorio limpio, TODOS los archivos temporales, de prueba y documentación local deben crearse dentro de la carpeta `util/`:

#### Archivos que SIEMPRE deben ir en `util/`:
- **Scripts de prueba**: `test_*.py` - Scripts de desarrollo/pruebas temporales
- **Scripts de debug**: `debug_*.py` - Scripts de debugging y diagnóstico
- **Scripts de demostración**: `demo_*.py` - Ejemplos y demos
- **Scripts de migración**: `migrate_*.py` - Migraciones de BD one-time
- **Scripts de población de datos**: `populate_*.py`, `add_*.py` - Scripts para agregar datos de prueba
- **Scripts de verificación**: `check_*.py`, `fix_*.py` - Utilidades de verificación y corrección
- **Scripts run**: `run_*.py` - Scripts para ejecutar migraciones u operaciones únicas
- **Documentación temporal**: `FASE*.md`, `GUIA_*.md` - Documentación de desarrollo local
- **Ejemplos JSON**: Datos de ejemplo y plantillas
- **Capturas de pantalla**: Screenshots y documentación visual

#### Archivos en la raíz del proyecto:
Solo estos archivos Python deben estar en la raíz:
- `main.py` - Punto de entrada de la aplicación
- Archivos de configuración: `requirements.txt`, `build.bat`, `.gitignore`, etc.
- Documentación oficial: `README.md`, `CLAUDE.md`, `LICENSE`

#### Ejemplo de uso:
```python
# ❌ MAL - No crear en la raíz
# test_nueva_feature.py (en raíz del proyecto)

# ✅ BIEN - Crear en util/
# util/test_nueva_feature.py
```

**Nota:** La carpeta `util/` completa está excluida del repositorio git. Los archivos ahí son solo para desarrollo local.

### Manejo de Rutas
La aplicación soporta ejecución como script y frozen (exe):
```python
if getattr(sys, 'frozen', False):
    base_dir = Path(sys.executable).parent  # Ejecutando como exe
else:
    base_dir = Path(__file__).parent        # Ejecutando como script
```
Siempre usar este patrón al referenciar archivos de la aplicación.

### Variables de Entorno
- Archivo `.env` almacena clave de cifrado (auto-generada)
- Nunca hacer commit de `.env` al control de versiones
- `EncryptionManager` maneja generación y carga de claves

### Logging
Logging comprehensivo configurado en `main.py`:
- Archivo log: `widget_sidebar_error.log` (sobrescrito cada sesión)
- Nivel log: DEBUG
- Manejador de excepciones global captura excepciones no atrapadas
- Usar `logger = logging.getLogger(__name__)` en cada módulo

### Posicionamiento de Ventanas
MainWindow se posiciona en borde derecho de pantalla con márgenes 10%:
```python
screen_height = screen.availableGeometry().height()
window_height = int(screen_height * 0.8)  # 80% altura
```

### Acceso a Base de Datos
- ConfigManager posee la instancia de DBManager
- Siempre cerrar BD al salir de aplicación (manejado en MainController.__del__)
- Usar transacciones para integridad de datos
- **Invalidación de Caché**: Llamar `controller.invalidate_filter_cache()` después de cualquier modificación en BD para asegurar coherencia de caché de filtros

## Tareas Comunes

### Agregar Nueva Categoría Programáticamente
```python
# Vía DBManager directamente
category_id = db.add_category(
    name='Nueva Categoría',
    icon='🆕',
    is_predefined=False
)
```

### Agregar Items a Categoría
```python
# Item regular
item_id = db.add_item(
    category_id=category_id,
    label='Mi Comando',
    content='git status',
    item_type='CODE'
)

# Item sensible (auto-cifrado)
item_id = db.add_item(
    category_id=category_id,
    label='API Key',
    content='sk-1234567890',
    item_type='TEXT',
    is_sensitive=True  # El contenido será cifrado
)
```

### Trabajar con Contenido Cifrado
```python
# El cifrado ocurre automáticamente en DBManager
# Al agregar/actualizar items:
db.add_item(..., is_sensitive=True)  # Contenido cifrado antes de almacenar

# Al recuperar items:
items = db.get_items_by_category(cat_id)  # Contenido auto-descifrado si es sensible
```

### Gestionar Sesiones
```python
from core.session_manager import SessionManager

session_mgr = SessionManager()
# Verificar si sesión es válida
if session_mgr.validate_session():
    print("Sesión válida")
else:
    # Mostrar diálogo de login
    pass
```

### Trabajar con Tags
```python
# Los tags se pasan directamente al crear el item
item_id = db.add_item(
    category_id=category_id,
    label='Mi Script Python',
    content='import asyncio...',
    item_type='CODE',
    tags=['python', 'async', 'backend']  # Tags como lista
)

# Los tags también se pueden actualizar
db.update_item(
    item_id=item_id,
    tags=['python', 'async', 'backend', 'nuevo-tag']
)
```

### Modificar Hotkey Global
Editar `src/core/hotkey_manager.py` y actualizar la combinación de teclas en el método `setup_hotkeys()`.

## Historial de Versiones

### **3.0.0** (SQLite Edition - ACTUAL)
**Arquitectura Empresarial Completa**

**Gestión de Contenido Avanzada:**
- Items multi-tipo (TEXT, URL, CODE, PATH) con cifrado automático
- Listas (v3.1.0): Agrupamiento secuencial de items
- Tablas: Estructura matricial para organización
- Componentes visuales: dividers, comments, alerts, notes
- Procesos: Flujos de trabajo con ejecución secuencial/paralela/manual

**Organización Multi-Nivel:**
- Proyectos: Agrupamiento de entidades (tags, procesos, listas, tablas, categorías, items)
- Áreas: Organización por área funcional (Frontend, Backend, DevOps, etc.)
- Sistema de tags multi-nivel con grupos jerárquicos
- Colecciones inteligentes dinámicas

**Búsqueda y Filtrado:**
- Búsqueda Universal con FTS5 en toda la aplicación
- Búsqueda avanzada con vistas múltiples (lista/tabla/árbol)
- Filtrado multi-criterio complejo
- Búsqueda global en tiempo real con debouncing

**Productividad:**
- Procesos automatizados con tracking de ejecución
- Screenshots con captura completa/región y anotaciones
- Galería de imágenes con búsqueda y metadatos
- Navegador embebido con sesiones y bookmarks
- Notebooks con pestañas
- Speed dial y accesos rápidos

**Seguridad:**
- Autenticación con contraseña maestra (bcrypt)
- Sesiones con expiración automática (24h)
- Cifrado Fernet para items sensibles
- Derivación de clave con PBKDF2

**UI Avanzada:**
- 150+ vistas y componentes
- Paneles flotantes y fijados con persistencia
- Dashboard de estadísticas con matplotlib
- 6 categorías de configuración especializada
- Integración taskbar de Windows

**IA y Automatización:**
- Wizards de creación masiva de items con IA
- Generación de tablas con asistencia de IA
- Validación automática de contenido

**Estadísticas y Analytics:**
- Tracking detallado de uso (timestamps, tiempo de ejecución, éxito/fallo)
- Items populares, olvidados, sugerencias
- Visualización de métricas y patrones

**Exportación e Integración:**
- Exportación/importación de proyectos y áreas (JSON/CSV)
- Exportación de tablas en múltiples formatos
- Sistema completo de migraciones (19+)

**Base de Datos:**
- 40+ tablas SQLite con FTS5
- 43+ managers especializados
- 16 modelos de datos
- Caché LRU para rendimiento

### **2.0.1** (Versión de Transición)
- Estabilización de funcionalidades
- Mejoras de rendimiento
- Corrección de bugs

### **2.0.0** (Inicio de Expansión)
- Hotkeys globales (`Ctrl+Shift+V`)
- Integración system tray con menú contextual
- Funcionalidad de búsqueda básica
- Inicio de migración a SQLite
- Panel flotante separado del sidebar

### **1.0.0** (Release Inicial)
- Sidebar frameless always-on-top
- Content panel para visualización de items
- Gestión básica de categorías e items
- Tema oscuro
- Animaciones de transición
- Gestión de portapapeles con pyperclip
- Configuración con archivos JSON

---

## Resumen Técnico para Claude Code

### Complejidad del Proyecto
Este es un **proyecto empresarial extremadamente complejo** con:
- **16 modelos de datos** diferentes
- **43+ managers especializados** en `src/core/`
- **150+ vistas y componentes UI** en `src/views/`
- **9 controladores** de lógica de negocio
- **40+ tablas SQLite** con soporte FTS5
- **19+ migraciones de base de datos** aplicadas
- **10 dependencias principales** de Python

### Jerarquía de Organización (5 Niveles)
```
1. Items (Elementos base: TEXT, URL, CODE, PATH)
   ↓
2. Listas/Tablas (Agrupamiento de items)
   ↓
3. Categorías (Organización con iconos, colores, tags)
   ↓
4. Proyectos/Áreas (Agrupamiento de entidades)
   ↓
5. Búsqueda Universal (FTS5 a través de todo)
```

### Sistemas Principales

**1. Gestión de Contenido:**
- Items con cifrado, tags, favoritos, tracking de uso
- Listas (secuenciales) y Tablas (matriciales)
- Procesos (flujos de trabajo automatizados)
- Componentes visuales (dividers, notes, alerts)

**2. Búsqueda (3 Niveles):**
- Universal (FTS5): Búsqueda de texto completo en toda la aplicación
- Avanzada: Múltiples vistas (lista/tabla/árbol), criterios complejos
- Global: Tiempo real con debouncing (300ms)

**3. Organización:**
- Proyectos: Agrupamiento de entidades relacionadas
- Áreas: Organización funcional (Frontend, Backend, DevOps, etc.)
- Tags multi-nivel con grupos jerárquicos

**4. Seguridad:**
- Autenticación con bcrypt
- Cifrado Fernet para items sensibles (transparente)
- Sesiones con expiración (24h)
- Derivación de clave PBKDF2

**5. Productividad:**
- Procesos con ejecución secuencial/paralela
- Screenshots con anotaciones
- Galería de imágenes
- Navegador embebido

### Características Técnicas Clave

**Base de Datos:**
- SQLite con `check_same_thread=False`
- FTS5 para búsqueda de texto completo
- Transacciones con context managers
- Auto-cifrado de items sensibles en capa BD

**UI:**
- PyQt6 con 150+ componentes
- Paneles flotantes y fijados con persistencia
- Always-on-top sidebar (70px × 100% altura)
- System tray integration

**Rendimiento:**
- Caché LRU en filtros y búsquedas
- Debouncing (300ms) en búsquedas en tiempo real
- Índices FTS5 optimizados

**Integración del Sistema:**
- Hotkey global (`Ctrl+Shift+V`)
- Windows AppBar API para reservar espacio
- System tray con menú contextual
- Integración taskbar avanzada

### Archivos Clave para Modificaciones

**Para agregar nuevas características:**
- `src/controllers/main_controller.py` - Punto de orquestación
- `src/views/main_window.py` - UI principal
- `src/database/db_manager.py` - Operaciones de BD
- `src/core/config_manager.py` - Configuración

**Para búsqueda:**
- `src/core/universal_search_engine.py` - Búsqueda FTS5
- `src/views/advanced_search/` - UI de búsqueda avanzada

**Para proyectos/áreas:**
- `src/core/project_manager.py` - Lógica de proyectos
- `src/core/area_manager.py` - Lógica de áreas
- `src/views/projects_window.py` - UI de proyectos
- `src/views/areas_window.py` - UI de áreas

**Para procesos:**
- `src/core/process_manager.py` - Gestión de procesos
- `src/core/process_executor.py` - Ejecución
- `src/views/processes_floating_panel.py` - UI

### Convenciones Importantes

1. **Archivos temporales:** TODO en `util/` (excluido de git)
2. **Transacciones BD:** Siempre usar `with db.transaction() as conn:`
3. **Caché:** Llamar `controller.invalidate_filter_cache()` después de modificaciones
4. **Cifrado:** Automático con `is_sensitive=True` en items
5. **Logging:** Usar `logger = logging.getLogger(__name__)` en cada módulo
6. **Migraciones:** Crear en `src/database/migrations/` para cambios de esquema

### Señales PyQt6 Comunes
- `category_selected(str)`, `item_selected(Item)`, `item_copied(Item)`
- `process_state_changed()`, `filters_applied()`, `favorites_updated()`
- `project_modified()`, `area_modified()`

### Puntos de Atención
- La aplicación es **muy compleja** - modificaciones requieren entender dependencias
- **Siempre leer código existente** antes de hacer cambios
- **Validar con managers existentes** antes de crear nuevos
- **Respetar arquitectura MVC** - no mezclar lógica en vistas
- **Usar caché LRU** para operaciones costosas
- **Documentar cambios** en migraciones de BD
