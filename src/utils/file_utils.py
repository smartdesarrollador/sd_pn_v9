# -*- coding: utf-8 -*-
"""
File Utilities - Utilidades para manejo de archivos y metadatos

Proporciona funciones para:
- Extracción de metadatos de archivos
- Cálculo de hash SHA-256
- Formateo de tamaños de archivo
- Detección de tipos MIME
"""

import os
import hashlib
import mimetypes
from typing import Dict, Optional
from pathlib import Path


def calculate_sha256(file_path: str) -> str:
    """
    Calcula el hash SHA-256 de un archivo

    Args:
        file_path: Ruta al archivo

    Returns:
        str: Hash SHA-256 en formato hexadecimal
    """
    sha256_hash = hashlib.sha256()

    try:
        with open(file_path, "rb") as f:
            # Leer archivo en chunks de 4KB para eficiencia
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)

        return sha256_hash.hexdigest()

    except Exception as e:
        raise IOError(f"Error calculando hash del archivo: {e}")


def extract_file_metadata(file_path: str) -> Dict[str, any]:
    """
    Extrae metadatos completos de un archivo

    Args:
        file_path: Ruta al archivo

    Returns:
        dict: Diccionario con metadatos:
            - file_size: Tamaño en bytes
            - file_type: Tipo MIME
            - file_extension: Extensión con punto
            - original_filename: Nombre del archivo
            - file_hash: Hash SHA-256
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Archivo no encontrado: {file_path}")

    if not os.path.isfile(file_path):
        raise ValueError(f"La ruta no es un archivo: {file_path}")

    # Obtener información básica
    stat = os.stat(file_path)
    path_obj = Path(file_path)

    # Detectar tipo MIME
    mime_type, _ = mimetypes.guess_type(file_path)

    # Clasificar tipo de archivo para categorización
    file_type_category = _classify_file_type(path_obj.suffix.lower(), mime_type)

    # Calcular hash
    file_hash = calculate_sha256(file_path)

    return {
        'file_size': stat.st_size,
        'file_type': file_type_category,
        'file_extension': path_obj.suffix,
        'original_filename': path_obj.name,
        'file_hash': file_hash
    }


def _classify_file_type(extension: str, mime_type: Optional[str]) -> str:
    """
    Clasifica el tipo de archivo en categorías

    Args:
        extension: Extensión del archivo (con punto)
        mime_type: Tipo MIME detectado

    Returns:
        str: Categoría del archivo (IMAGEN, VIDEO, PDF, WORD, EXCEL, TEXT, OTROS)
    """
    # Mapeo de extensiones a categorías
    extension_map = {
        # Imágenes
        '.jpg': 'IMAGEN',
        '.jpeg': 'IMAGEN',
        '.png': 'IMAGEN',
        '.gif': 'IMAGEN',
        '.bmp': 'IMAGEN',
        '.svg': 'IMAGEN',
        '.webp': 'IMAGEN',
        '.ico': 'IMAGEN',
        '.tiff': 'IMAGEN',
        '.tif': 'IMAGEN',

        # Videos
        '.mp4': 'VIDEO',
        '.avi': 'VIDEO',
        '.mkv': 'VIDEO',
        '.mov': 'VIDEO',
        '.wmv': 'VIDEO',
        '.flv': 'VIDEO',
        '.webm': 'VIDEO',
        '.m4v': 'VIDEO',

        # PDFs
        '.pdf': 'PDF',

        # Documentos Word
        '.doc': 'WORD',
        '.docx': 'WORD',
        '.odt': 'WORD',

        # Hojas de cálculo Excel
        '.xls': 'EXCEL',
        '.xlsx': 'EXCEL',
        '.csv': 'EXCEL',
        '.ods': 'EXCEL',

        # Archivos de texto
        '.txt': 'TEXT',
        '.md': 'TEXT',
        '.log': 'TEXT',
        '.json': 'TEXT',
        '.xml': 'TEXT',
        '.yaml': 'TEXT',
        '.yml': 'TEXT',
        '.ini': 'TEXT',
        '.cfg': 'TEXT',
        '.conf': 'TEXT',
    }

    # Primero intentar por extensión
    if extension in extension_map:
        return extension_map[extension]

    # Si no hay match por extensión, intentar por MIME type
    if mime_type:
        if mime_type.startswith('image/'):
            return 'IMAGEN'
        elif mime_type.startswith('video/'):
            return 'VIDEO'
        elif mime_type == 'application/pdf':
            return 'PDF'
        elif 'word' in mime_type or 'document' in mime_type:
            return 'WORD'
        elif 'excel' in mime_type or 'spreadsheet' in mime_type:
            return 'EXCEL'
        elif mime_type.startswith('text/'):
            return 'TEXT'

    # Default
    return 'OTROS'


def format_file_size(bytes_size: int) -> str:
    """
    Formatea un tamaño de archivo en bytes a formato legible

    Args:
        bytes_size: Tamaño en bytes

    Returns:
        str: Tamaño formateado (ej: "2.5 MB", "1.2 GB")

    Examples:
        >>> format_file_size(1024)
        '1.00 KB'
        >>> format_file_size(1536)
        '1.50 KB'
        >>> format_file_size(1048576)
        '1.00 MB'
    """
    if bytes_size < 0:
        return "0 B"

    size = float(bytes_size)
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    unit_index = 0

    while size >= 1024.0 and unit_index < len(units) - 1:
        size /= 1024.0
        unit_index += 1

    # Formatear con decimales apropiados
    if unit_index == 0:  # Bytes
        return f"{int(size)} {units[unit_index]}"
    else:
        return f"{size:.2f} {units[unit_index]}"


def ensure_directory_exists(directory_path: str) -> bool:
    """
    Asegura que un directorio exista, creándolo si es necesario

    Args:
        directory_path: Ruta al directorio

    Returns:
        bool: True si el directorio existe o fue creado exitosamente

    Raises:
        OSError: Si no se puede crear el directorio
    """
    if not directory_path:
        return False

    try:
        os.makedirs(directory_path, exist_ok=True)
        return True
    except OSError as e:
        raise OSError(f"No se pudo crear el directorio {directory_path}: {e}")


def is_valid_filename(filename: str) -> bool:
    """
    Valida si un nombre de archivo es válido para Windows

    Args:
        filename: Nombre del archivo a validar

    Returns:
        bool: True si el nombre es válido
    """
    if not filename:
        return False

    # Caracteres inválidos en Windows
    invalid_chars = '<>:"|?*\\/\0'

    for char in invalid_chars:
        if char in filename:
            return False

    # Nombres reservados en Windows
    reserved_names = [
        'CON', 'PRN', 'AUX', 'NUL',
        'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
        'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
    ]

    name_without_ext = os.path.splitext(filename)[0].upper()
    if name_without_ext in reserved_names:
        return False

    return True


def sanitize_filename(filename: str, replacement: str = '_') -> str:
    """
    Sanitiza un nombre de archivo reemplazando caracteres inválidos

    Args:
        filename: Nombre del archivo
        replacement: Carácter de reemplazo para caracteres inválidos

    Returns:
        str: Nombre de archivo sanitizado
    """
    if not filename:
        return "unnamed"

    # Caracteres inválidos en Windows
    invalid_chars = '<>:"|?*\\/\0'

    sanitized = filename
    for char in invalid_chars:
        sanitized = sanitized.replace(char, replacement)

    # Validar nombres reservados
    name_without_ext = os.path.splitext(sanitized)[0].upper()
    reserved_names = [
        'CON', 'PRN', 'AUX', 'NUL',
        'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
        'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
    ]

    if name_without_ext in reserved_names:
        sanitized = f"file_{sanitized}"

    return sanitized


def get_unique_filepath(directory: str, filename: str) -> str:
    """
    Genera una ruta de archivo única, agregando contador si existe

    Args:
        directory: Directorio donde se guardará el archivo
        filename: Nombre del archivo deseado

    Returns:
        str: Ruta completa al archivo único

    Examples:
        Si "screenshot.png" existe, retorna "screenshot_1.png"
        Si "screenshot_1.png" existe, retorna "screenshot_2.png"
    """
    base_path = os.path.join(directory, filename)

    # Si no existe, retornar tal cual
    if not os.path.exists(base_path):
        return base_path

    # Separar nombre y extensión
    name, extension = os.path.splitext(filename)

    # Buscar nombre único
    counter = 1
    while True:
        new_filename = f"{name}_{counter}{extension}"
        new_path = os.path.join(directory, new_filename)

        if not os.path.exists(new_path):
            return new_path

        counter += 1

        # Prevenir bucle infinito
        if counter > 9999:
            raise ValueError("No se pudo generar nombre de archivo único")
