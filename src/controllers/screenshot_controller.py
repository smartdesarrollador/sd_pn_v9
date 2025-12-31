# -*- coding: utf-8 -*-
"""
Screenshot Controller - Controlador de capturas de pantalla

Orquesta el flujo completo de capturas de pantalla:
1. Mostrar overlay de selección
2. Capturar área seleccionada
3. Guardar imagen en disco
4. Crear item en base de datos
5. Copiar a portapapeles
6. Mostrar notificación
"""

import logging
from datetime import datetime
from typing import Optional
from pathlib import Path

from PyQt6.QtCore import QObject, QTimer, QRect, pyqtSignal
from PyQt6.QtGui import QPixmap

from src.core.screenshot_manager import ScreenshotManager
from src.core.config_manager import ConfigManager
from src.views.screenshot_overlay import ScreenshotOverlay

logger = logging.getLogger(__name__)


class ScreenshotController(QObject):
    """
    Controlador para gestionar capturas de pantalla

    Coordina entre:
    - ScreenshotOverlay (UI de selección)
    - ScreenshotManager (captura y guardado)
    - DBManager (creación de items)
    - NotificationManager (feedback al usuario)

    Señales:
        screenshot_completed(bool, str): Emitida cuando la captura se completa
            - bool: True si fue exitosa, False si falló o se canceló
            - str: Ruta completa al archivo de captura (vacío si falló)
    """

    # Señales
    screenshot_completed = pyqtSignal(bool, str)  # (success, filepath)

    def __init__(self, main_controller):
        """
        Inicializar Screenshot Controller

        Args:
            main_controller: Referencia al MainController
        """
        super().__init__()

        self.main_controller = main_controller
        self.config_manager = main_controller.config_manager
        self.db_manager = main_controller.config_manager.db
        self.db = main_controller.config_manager.db  # Alias para db

        # Managers
        self.screenshot_manager = ScreenshotManager(self.config_manager)

        # UI
        self.overlay: Optional[ScreenshotOverlay] = None

        # Estado
        self.captured_pixmap: Optional[QPixmap] = None
        self.selected_rect: Optional[QRect] = None

        logger.info("ScreenshotController initialized")

    @property
    def main_window(self):
        """Obtener referencia a main_window"""
        if hasattr(self.main_controller, 'main_window'):
            return self.main_controller.main_window
        return None

    def start_screenshot(self) -> None:
        """
        Inicia el proceso de captura de pantalla

        Flujo:
        1. Ocultar ventanas de la aplicación
        2. Esperar 200ms para que se oculten
        3. Mostrar overlay de selección
        """
        logger.info("Starting screenshot process")

        # Ocultar ventanas de la aplicación
        self._hide_app_windows()

        # Esperar un momento para que se oculten las ventanas
        QTimer.singleShot(200, self._show_overlay)

    def _hide_app_windows(self) -> None:
        """Oculta todas las ventanas de la aplicación"""
        try:
            # Ocultar ventana principal (sidebar)
            if hasattr(self.main_controller, 'main_window'):
                self.main_controller.main_window.hide()

            # Ocultar floating panels
            if hasattr(self.main_controller, 'floating_panel'):
                if self.main_controller.floating_panel:
                    self.main_controller.floating_panel.hide()

            logger.debug("App windows hidden")

        except Exception as e:
            logger.error(f"Error hiding app windows: {e}")

    def _show_app_windows(self) -> None:
        """Restaura las ventanas de la aplicación"""
        try:
            # Restaurar ventana principal
            if hasattr(self.main_controller, 'main_window'):
                self.main_controller.main_window.show()

            # Restaurar floating panels si estaban visibles
            if hasattr(self.main_controller, 'floating_panel'):
                if self.main_controller.floating_panel:
                    # Solo mostrar si tenía contenido antes
                    if hasattr(self.main_controller.floating_panel, '_was_visible'):
                        if self.main_controller.floating_panel._was_visible:
                            self.main_controller.floating_panel.show()

            logger.debug("App windows restored")

        except Exception as e:
            logger.error(f"Error restoring app windows: {e}")

    def _show_overlay(self) -> None:
        """Muestra el overlay de selección"""
        try:
            # Crear overlay si no existe
            if not self.overlay:
                self.overlay = ScreenshotOverlay()

                # Conectar señales
                self.overlay.area_selected.connect(self._handle_area_selected)
                self.overlay.capture_cancelled.connect(self._handle_screenshot_cancelled)

            # Mostrar overlay
            self.overlay.show()
            logger.debug("Screenshot overlay shown")

        except Exception as e:
            logger.error(f"Error showing overlay: {e}")
            self._handle_screenshot_cancelled()

    def _handle_area_selected(self, rect: QRect) -> None:
        """
        Handler cuando se selecciona un área

        Args:
            rect: Rectángulo seleccionado
        """
        logger.info(f"Area selected: ({rect.x()}, {rect.y()}) - {rect.width()}x{rect.height()}")

        self.selected_rect = rect

        # Cerrar overlay
        if self.overlay:
            self.overlay.close()

        # Esperar un momento para que el overlay se cierre completamente
        QTimer.singleShot(100, self._capture_and_process)

    def _capture_and_process(self) -> None:
        """Captura la región seleccionada y procesa"""
        if not self.selected_rect:
            logger.error("No selected rect available")
            self._handle_screenshot_cancelled()
            return

        try:
            # Capturar región
            logger.debug("Capturing selected region...")
            pixmap = self.screenshot_manager.capture_region(
                self.selected_rect.x(),
                self.selected_rect.y(),
                self.selected_rect.width(),
                self.selected_rect.height()
            )

            if not pixmap:
                logger.error("Failed to capture screenshot")
                self._show_error_notification("Error al capturar pantalla")
                self._handle_screenshot_cancelled()
                return

            self.captured_pixmap = pixmap
            logger.info(f"Screenshot captured: {pixmap.width()}x{pixmap.height()}")

            # Procesar captura
            self._process_screenshot()

        except Exception as e:
            logger.error(f"Error capturing screenshot: {e}")
            self._show_error_notification(f"Error: {str(e)}")
            self._handle_screenshot_cancelled()

    def _process_screenshot(self) -> None:
        """Procesa la captura: guardar, crear item, copiar, notificar"""
        if not self.captured_pixmap:
            # Emitir señal de fallo
            self.screenshot_completed.emit(False, "")
            return

        try:
            # Obtener configuración
            auto_copy = self.config_manager.get_setting('screenshot_auto_copy', '1') == '1'
            show_notification = self.config_manager.get_setting('screenshot_show_notification', '1') == '1'
            create_item = self.config_manager.get_setting('screenshot_create_item', '1') == '1'

            # 1. Guardar en disco
            filepath = self.screenshot_manager.save_screenshot(self.captured_pixmap)

            if not filepath:
                logger.error("Failed to save screenshot")
                self._show_error_notification("Error al guardar captura")
                self._handle_screenshot_cancelled()
                # Emitir señal de fallo
                self.screenshot_completed.emit(False, "")
                return

            logger.info(f"Screenshot saved: {filepath}")

            # 2. Copiar a portapapeles si está habilitado
            if auto_copy:
                success = self.screenshot_manager.copy_to_clipboard(self.captured_pixmap)
                if success:
                    logger.debug("Screenshot copied to clipboard")

            # 3. Mostrar diálogo para guardar como item (si está habilitado)
            item_id = None
            if create_item:
                # Mostrar diálogo de guardado
                item_id = self._show_save_dialog(filepath)
                if item_id:
                    logger.info(f"Screenshot item created: ID {item_id}")

            # 4. Mostrar notificación si está habilitado
            if show_notification:
                self._show_success_notification(filepath, item_id)

            # Limpiar y restaurar
            self._cleanup_after_screenshot()

            # Emitir señal de éxito con la ruta del archivo
            self.screenshot_completed.emit(True, filepath)

        except Exception as e:
            logger.error(f"Error processing screenshot: {e}")
            self._show_error_notification(f"Error procesando captura: {str(e)}")
            self._cleanup_after_screenshot()
            # Emitir señal de fallo
            self.screenshot_completed.emit(False, "")

    def _show_save_dialog(self, filepath: str) -> Optional[int]:
        """
        Muestra diálogo para guardar screenshot como item

        Args:
            filepath: Ruta al archivo de screenshot

        Returns:
            int: ID del item creado o None si se omitió
        """
        from src.views.dialogs.save_screenshot_dialog import SaveScreenshotDialog

        try:
            # Obtener categorías
            categories = self.db.get_categories()

            # Obtener ID de categoría Screenshots
            screenshots_category_id = self._get_or_create_screenshots_category()

            # Crear y mostrar diálogo
            dialog = SaveScreenshotDialog(
                screenshot_path=filepath,
                categories=categories,
                default_category_id=screenshots_category_id,
                db=self.config_manager.db,
                parent=self.main_window
            )

            # Ejecutar diálogo (modal)
            result = dialog.exec()

            if result == SaveScreenshotDialog.DialogCode.Accepted:
                item_data = dialog.get_item_data()

                if item_data:
                    # Usuario quiere guardar el item
                    return self._create_screenshot_item_from_dialog(item_data)
                else:
                    # Usuario eligió "No guardar item"
                    logger.info("User skipped creating item for screenshot")
                    return None
            else:
                # Usuario canceló
                logger.info("User cancelled save screenshot dialog")
                return None

        except Exception as e:
            logger.error(f"Error showing save dialog: {e}", exc_info=True)
            # Si falla el diálogo, crear item automáticamente
            return self._create_screenshot_item(filepath)

    def _create_screenshot_item_from_dialog(self, item_data: dict) -> Optional[int]:
        """
        Crea item con datos del diálogo

        Args:
            item_data: Datos del item desde el diálogo

        Returns:
            int: ID del item creado o None si falla
        """
        try:
            # El filepath está en original_filename o content
            filepath = item_data.get('original_filename') or item_data.get('content')

            # Extraer metadatos del archivo
            metadata = self.screenshot_manager.get_screenshot_metadata(filepath)

            if not metadata:
                logger.error("Failed to extract file metadata")
                return None

            # Obtener solo el nombre del archivo (relativo)
            import os
            filename = os.path.basename(filepath)

            # Extraer created_at de los metadatos si existe
            created_at_str = None
            if metadata.get('file_created_at'):
                # Convertir datetime a string en formato SQLite
                created_at_str = metadata['file_created_at'].strftime('%Y-%m-%d %H:%M:%S')

            # Crear item con datos del diálogo
            item_id = self.db.add_item(
                category_id=item_data['category_id'],
                label=item_data['label'],
                content=filename,  # Solo nombre de archivo relativo
                item_type='PATH',
                description=item_data.get('description'),
                tags=item_data.get('tags', []),
                is_favorite=item_data.get('is_favorite', False),
                file_size=metadata.get('file_size'),
                file_type=metadata.get('file_type'),
                file_extension=metadata.get('file_extension'),
                original_filename=filename,  # Solo nombre de archivo relativo
                file_hash=metadata.get('file_hash'),
                preview_url=item_data.get('preview_url'),  # URL opcional
                created_at=created_at_str  # Fecha extraída del nombre del archivo
            )

            logger.info(f"Screenshot item created from dialog: ID {item_id}")
            return item_id

        except Exception as e:
            logger.error(f"Error creating screenshot item from dialog: {e}", exc_info=True)
            return None

    def _create_screenshot_item(self, filepath: str) -> Optional[int]:
        """
        Crea un item en la base de datos para la captura (método automático)

        Args:
            filepath: Ruta al archivo de captura

        Returns:
            int: ID del item creado o None si falla
        """
        try:
            # Obtener o crear categoría Screenshots
            category_id = self._get_or_create_screenshots_category()

            if not category_id:
                logger.error("Failed to get/create screenshots category")
                return None

            # Extraer metadatos del archivo
            metadata = self.screenshot_manager.get_screenshot_metadata(filepath)

            if not metadata:
                logger.error("Failed to extract file metadata")
                return None

            # Generar label automático
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            label = f"Captura {timestamp}"

            # Crear item
            item_id = self.db_manager.add_item(
                category_id=category_id,
                label=label,
                content=filepath,
                item_type='PATH',
                file_size=metadata['file_size'],
                file_type=metadata['file_type'],
                file_extension=metadata['file_extension'],
                original_filename=metadata['original_filename'],
                file_hash=metadata['file_hash'],
                tags=['screenshot', 'captura'],
                description=f"Captura de pantalla {self.selected_rect.width()}x{self.selected_rect.height()}"
            )

            return item_id

        except Exception as e:
            logger.error(f"Error creating screenshot item: {e}")
            return None

    def _get_or_create_screenshots_category(self) -> Optional[int]:
        """
        Obtiene o crea la categoría Screenshots

        Returns:
            int: ID de la categoría o None si falla
        """
        try:
            # Verificar si hay una categoría configurada
            config_category_id = self.config_manager.get_setting('screenshot_category_id', '')

            if config_category_id and config_category_id.strip():
                # Verificar que la categoría exista
                category = self.db_manager.get_category(int(config_category_id))
                if category:
                    return int(config_category_id)

            # Buscar categoría por nombre
            categories = self.db_manager.get_all_categories()
            for category in categories:
                if category['name'].lower() in ['screenshots', 'capturas', 'capturas de pantalla']:
                    # Guardar en config para próxima vez
                    self.config_manager.set_setting('screenshot_category_id', str(category['id']))
                    return category['id']

            # Crear nueva categoría
            logger.info("Creating new Screenshots category")
            category_id = self.db_manager.add_category(
                name='Screenshots',
                icon='📸',
                is_predefined=False,
                order_index=999
            )

            # Guardar en config
            self.config_manager.set_setting('screenshot_category_id', str(category_id))

            return category_id

        except Exception as e:
            logger.error(f"Error getting/creating screenshots category: {e}")
            return None

    def _show_success_notification(self, filepath: str, item_id: Optional[int] = None) -> None:
        """
        Muestra notificación de éxito

        Args:
            filepath: Ruta al archivo guardado
            item_id: ID del item creado (opcional)
        """
        try:
            # Por ahora solo log, en el futuro integrar con NotificationManager
            message = f"Captura guardada: {Path(filepath).name}"
            if item_id:
                message += f" (Item #{item_id})"

            logger.info(f"SUCCESS: {message}")

            # TODO: Integrar con NotificationManager cuando esté disponible
            # self.main_controller.notification_manager.show_notification(
            #     title="Captura Exitosa",
            #     message=message,
            #     notification_type="success"
            # )

        except Exception as e:
            logger.error(f"Error showing success notification: {e}")

    def _show_error_notification(self, message: str) -> None:
        """
        Muestra notificación de error

        Args:
            message: Mensaje de error
        """
        try:
            logger.error(f"ERROR: {message}")

            # TODO: Integrar con NotificationManager cuando esté disponible
            # self.main_controller.notification_manager.show_notification(
            #     title="Error en Captura",
            #     message=message,
            #     notification_type="error"
            # )

        except Exception as e:
            logger.error(f"Error showing error notification: {e}")

    def _handle_screenshot_cancelled(self) -> None:
        """Handler cuando se cancela la captura"""
        logger.info("Screenshot cancelled")
        self._cleanup_after_screenshot()
        # Emitir señal de cancelación
        self.screenshot_completed.emit(False, "")

    def _cleanup_after_screenshot(self) -> None:
        """Limpieza después de completar o cancelar captura"""
        # Limpiar estado
        self.captured_pixmap = None
        self.selected_rect = None

        # Restaurar ventanas de la aplicación
        self._show_app_windows()

        logger.debug("Screenshot process cleanup completed")
