# -*- coding: utf-8 -*-
"""
Screenshot Manager - Gestor de capturas de pantalla

Maneja toda la funcionalidad de captura de pantalla:
- Captura de pantalla completa y regiones específicas
- Guardado de imágenes en diferentes formatos
- Generación de metadatos
- Copia al portapapeles
- Integración con mss para capturas rápidas
"""

import os
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple
from io import BytesIO

import mss
from PIL import Image
from PyQt6.QtGui import QPixmap, QImage, QClipboard
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QBuffer

from core.config_manager import ConfigManager
from utils.file_utils import (
    extract_file_metadata,
    ensure_directory_exists,
    sanitize_filename,
    get_unique_filepath
)

logger = logging.getLogger(__name__)


class ScreenshotManager:
    """
    Manager para capturas de pantalla con soporte para:
    - Captura de regiones personalizadas
    - Múltiples formatos de imagen
    - Metadatos automáticos
    - Copia a portapapeles
    """

    def __init__(self, config_manager: ConfigManager):
        """
        Inicializar Screenshot Manager

        Args:
            config_manager: Gestor de configuración
        """
        self.config_manager = config_manager
        self.mss_instance = None

    def capture_full_screen(self, monitor_number: int = 1) -> Optional[QPixmap]:
        """
        Captura la pantalla completa de un monitor específico

        Args:
            monitor_number: Número de monitor (1 = primario, 2 = secundario, etc.)

        Returns:
            QPixmap: Imagen capturada o None si falla
        """
        try:
            with mss.mss() as sct:
                # Validar número de monitor
                if monitor_number < 1 or monitor_number > len(sct.monitors) - 1:
                    logger.warning(f"Monitor {monitor_number} no válido, usando monitor primario")
                    monitor_number = 1

                # Capturar monitor específico
                monitor = sct.monitors[monitor_number]
                screenshot = sct.grab(monitor)

                # Convertir a PIL Image
                img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")

                # Convertir a QPixmap
                return self._pil_to_qpixmap(img)

        except Exception as e:
            logger.error(f"Error capturando pantalla completa: {e}")
            return None

    def capture_region(self, x: int, y: int, width: int, height: int) -> Optional[QPixmap]:
        """
        Captura una región específica de la pantalla

        Args:
            x: Coordenada X inicial
            y: Coordenada Y inicial
            width: Ancho de la región
            height: Alto de la región

        Returns:
            QPixmap: Imagen capturada o None si falla
        """
        try:
            # Validar dimensiones
            if width <= 0 or height <= 0:
                logger.error(f"Dimensiones inválidas: {width}x{height}")
                return None

            with mss.mss() as sct:
                # Definir región a capturar
                monitor = {
                    "top": y,
                    "left": x,
                    "width": width,
                    "height": height
                }

                # Capturar región
                screenshot = sct.grab(monitor)

                # Convertir a PIL Image
                img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")

                # Convertir a QPixmap
                return self._pil_to_qpixmap(img)

        except Exception as e:
            logger.error(f"Error capturando región ({x},{y},{width},{height}): {e}")
            return None

    def save_screenshot(
        self,
        pixmap: QPixmap,
        directory: Optional[str] = None,
        filename: Optional[str] = None,
        format: Optional[str] = None,
        quality: Optional[int] = None
    ) -> Optional[str]:
        """
        Guarda una captura de pantalla en disco

        Args:
            pixmap: Imagen a guardar
            directory: Directorio donde guardar (usa config si es None)
            filename: Nombre del archivo (genera automático si es None)
            format: Formato de imagen (usa config si es None)
            quality: Calidad de compresión para JPG (usa config si es None)

        Returns:
            str: Ruta completa al archivo guardado o None si falla
        """
        try:
            # Obtener configuración
            if directory is None:
                # Usar files_base_path que es el configurado en Settings > Archivos
                base_path = self.config_manager.get_setting('files_base_path', '')
                folder_name = self.config_manager.get_setting('screenshots_folder_name', 'IMAGENES')

                if not base_path:
                    logger.error("Ruta base no configurada (files_base_path)")
                    return None

                directory = os.path.join(base_path, folder_name)

            if format is None:
                format = self.config_manager.get_setting('screenshot_format', 'png').lower()

            if quality is None:
                quality = int(self.config_manager.get_setting('screenshot_quality', '95'))

            # Crear directorio si no existe
            ensure_directory_exists(directory)

            # Generar nombre de archivo si no se proporciona
            if filename is None:
                filename = self.generate_filename(format)

            # Sanitizar nombre de archivo
            filename = sanitize_filename(filename)

            # Obtener ruta única (evitar sobrescribir)
            filepath = get_unique_filepath(directory, filename)

            # Convertir QPixmap a PIL Image para guardar con más control
            pil_image = self._qpixmap_to_pil(pixmap)

            # Guardar según formato
            if format.lower() in ['jpg', 'jpeg']:
                # Convertir a RGB si es necesario (JPG no soporta transparencia)
                if pil_image.mode in ('RGBA', 'LA', 'P'):
                    rgb_image = Image.new('RGB', pil_image.size, (255, 255, 255))
                    if pil_image.mode == 'P':
                        pil_image = pil_image.convert('RGBA')
                    rgb_image.paste(pil_image, mask=pil_image.split()[-1] if pil_image.mode == 'RGBA' else None)
                    pil_image = rgb_image

                pil_image.save(filepath, 'JPEG', quality=quality, optimize=True)

            elif format.lower() == 'png':
                pil_image.save(filepath, 'PNG', optimize=True)

            elif format.lower() == 'bmp':
                pil_image.save(filepath, 'BMP')

            else:
                logger.error(f"Formato no soportado: {format}")
                return None

            logger.info(f"Screenshot guardado: {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"Error guardando screenshot: {e}")
            return None

    def generate_filename(self, extension: str = 'png') -> str:
        """
        Genera un nombre de archivo único para captura

        Args:
            extension: Extensión del archivo (sin punto)

        Returns:
            str: Nombre de archivo generado

        Examples:
            "screenshot_20251127_143045.png"
        """
        prefix = self.config_manager.get_setting('screenshot_prefix', 'screenshot')
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Asegurar que extensión no tenga punto
        if extension.startswith('.'):
            extension = extension[1:]

        return f"{prefix}_{timestamp}.{extension}"

    def copy_to_clipboard(self, pixmap: QPixmap) -> bool:
        """
        Copia una imagen al portapapeles del sistema

        Args:
            pixmap: Imagen a copiar

        Returns:
            bool: True si se copió exitosamente
        """
        try:
            clipboard = QApplication.clipboard()
            clipboard.setPixmap(pixmap)
            logger.info("Screenshot copiado al portapapeles")
            return True

        except Exception as e:
            logger.error(f"Error copiando al portapapeles: {e}")
            return False

    def get_screenshot_metadata(self, filepath: str) -> Optional[dict]:
        """
        Obtiene metadatos de un archivo de screenshot guardado

        Args:
            filepath: Ruta al archivo de screenshot

        Returns:
            dict: Metadatos del archivo o None si falla
        """
        try:
            metadata = extract_file_metadata(filepath)
            logger.info(f"Metadatos extraídos de {filepath}")
            return metadata

        except Exception as e:
            logger.error(f"Error extrayendo metadatos: {e}")
            return None

    def _pil_to_qpixmap(self, pil_image: Image.Image) -> QPixmap:
        """
        Convierte una imagen PIL a QPixmap

        Args:
            pil_image: Imagen PIL

        Returns:
            QPixmap: Imagen convertida
        """
        # Convertir PIL Image a bytes
        if pil_image.mode != 'RGB':
            pil_image = pil_image.convert('RGB')

        data = pil_image.tobytes("raw", "RGB")
        qimage = QImage(
            data,
            pil_image.width,
            pil_image.height,
            pil_image.width * 3,
            QImage.Format.Format_RGB888
        )

        return QPixmap.fromImage(qimage)

    def _qpixmap_to_pil(self, qpixmap: QPixmap) -> Image.Image:
        """
        Convierte un QPixmap a imagen PIL

        Args:
            qpixmap: QPixmap a convertir

        Returns:
            Image: Imagen PIL
        """
        # Convertir QPixmap a QImage
        qimage = qpixmap.toImage()

        # Convertir a formato compatible
        qimage = qimage.convertToFormat(QImage.Format.Format_RGBA8888)

        # Obtener datos de bytes
        width = qimage.width()
        height = qimage.height()
        ptr = qimage.bits()
        ptr.setsize(height * width * 4)

        # Crear imagen PIL desde bytes
        pil_image = Image.frombytes('RGBA', (width, height), ptr.asarray())

        return pil_image

    def get_all_monitors(self) -> list:
        """
        Obtiene información de todos los monitores disponibles

        Returns:
            list: Lista de diccionarios con info de monitores
        """
        try:
            with mss.mss() as sct:
                monitors = []
                for i, monitor in enumerate(sct.monitors[1:], start=1):  # Skip monitor 0 (all monitors)
                    monitors.append({
                        'number': i,
                        'left': monitor['left'],
                        'top': monitor['top'],
                        'width': monitor['width'],
                        'height': monitor['height']
                    })
                return monitors

        except Exception as e:
            logger.error(f"Error obteniendo monitores: {e}")
            return []

    def validate_region(self, x: int, y: int, width: int, height: int) -> bool:
        """
        Valida que una región sea válida para captura

        Args:
            x: Coordenada X
            y: Coordenada Y
            width: Ancho
            height: Alto

        Returns:
            bool: True si la región es válida
        """
        # Verificar dimensiones positivas
        if width <= 0 or height <= 0:
            return False

        # Verificar que la región esté dentro de algún monitor
        monitors = self.get_all_monitors()

        for monitor in monitors:
            # Verificar si la región está completamente dentro del monitor
            if (x >= monitor['left'] and
                y >= monitor['top'] and
                x + width <= monitor['left'] + monitor['width'] and
                y + height <= monitor['top'] + monitor['height']):
                return True

        # Región fuera de todos los monitores
        return False

    def __del__(self):
        """Cleanup al destruir el manager"""
        if self.mss_instance:
            try:
                self.mss_instance.close()
            except:
                pass
