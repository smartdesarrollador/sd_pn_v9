# -*- coding: utf-8 -*-
"""
Screenshot Settings Tab - Configuración de capturas de pantalla
"""
import os
from pathlib import Path
from typing import Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QCheckBox, QFileDialog, QMessageBox,
    QGroupBox, QFormLayout, QComboBox, QSlider, QSpinBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from core.config_manager import ConfigManager
from views.widgets.hotkey_input import HotkeyInput


class ScreenshotSettings(QWidget):
    """Widget de configuración de capturas de pantalla"""

    settings_changed = pyqtSignal()  # Emitido cuando cambia configuración

    def __init__(self, config_manager: ConfigManager, controller=None, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.controller = controller  # MainController para recargar hotkey

        self.init_ui()
        self.load_settings()

    def init_ui(self):
        """Inicializar interfaz de usuario"""
        # Apply dark theme styles
        self.setStyleSheet("""
            ScreenshotSettings {
                background-color: #2b2b2b;
            }
            QLabel {
                color: #cccccc;
                background-color: transparent;
            }
            QGroupBox {
                background-color: #2b2b2b;
                color: #cccccc;
                font-weight: bold;
                font-size: 11pt;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #cccccc;
            }
            QLineEdit {
                background-color: #2d2d2d;
                color: #cccccc;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                padding: 5px;
            }
            QLineEdit:focus {
                border: 1px solid #007acc;
            }
            QLineEdit:disabled {
                background-color: #1e1e1e;
                color: #666666;
            }
            QComboBox {
                background-color: #2d2d2d;
                color: #cccccc;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                padding: 5px;
                min-height: 25px;
            }
            QComboBox:focus {
                border: 1px solid #007acc;
            }
            QComboBox::drop-down {
                border: none;
                padding-right: 10px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 6px solid #cccccc;
                margin-right: 5px;
            }
            QComboBox QAbstractItemView {
                background-color: #2d2d2d;
                color: #cccccc;
                selection-background-color: #007acc;
                border: 1px solid #3d3d3d;
            }
            QCheckBox {
                color: #cccccc;
                spacing: 5px;
                background-color: transparent;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 1px solid #3d3d3d;
                border-radius: 3px;
                background-color: #2d2d2d;
            }
            QCheckBox::indicator:checked {
                background-color: #007acc;
                border-color: #007acc;
            }
            QCheckBox::indicator:hover {
                border-color: #007acc;
            }
            QPushButton {
                background-color: #2d2d2d;
                color: #cccccc;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #3d3d3d;
                border: 1px solid #007acc;
            }
            QPushButton:pressed {
                background-color: #1e1e1e;
            }
            QPushButton:disabled {
                background-color: #1e1e1e;
                color: #666666;
                border: 1px solid #2d2d2d;
            }
            QSlider::groove:horizontal {
                background: #2d2d2d;
                height: 8px;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #007acc;
                border: 1px solid #005a9e;
                width: 18px;
                margin: -5px 0;
                border-radius: 9px;
            }
            QSlider::handle:horizontal:hover {
                background: #005a9e;
            }
            QSpinBox {
                background-color: #2d2d2d;
                color: #cccccc;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                padding: 5px;
            }
            QSpinBox:focus {
                border: 1px solid #007acc;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                background-color: #3d3d3d;
                border: none;
                width: 16px;
            }
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                background-color: #007acc;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Título
        title = QLabel("📸 Configuración de Capturas de Pantalla")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        # Sección 1: Almacenamiento
        storage_group = self._create_storage_section()
        layout.addWidget(storage_group)

        # Sección 2: Formato
        format_group = self._create_format_section()
        layout.addWidget(format_group)

        # Sección 3: Hotkey
        hotkey_group = self._create_hotkey_section()
        layout.addWidget(hotkey_group)

        # Sección 4: Comportamiento
        behavior_group = self._create_behavior_section()
        layout.addWidget(behavior_group)

        # Botones de acción
        buttons_layout = self._create_buttons_section()
        layout.addLayout(buttons_layout)

        # Stretch al final para empujar todo hacia arriba
        layout.addStretch()

    def _create_storage_section(self) -> QGroupBox:
        """Crear sección de almacenamiento"""
        group = QGroupBox("📁 Almacenamiento")
        layout = QVBoxLayout(group)

        # Descripción
        desc = QLabel(
            "Configura dónde se guardarán las capturas de pantalla.\n"
            "Las imágenes se guardarán en: [Ruta Base] / [Nombre de Carpeta]"
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #888; font-size: 11px; padding: 5px;")
        layout.addWidget(desc)

        # Nombre de carpeta
        folder_layout = QFormLayout()

        self.folder_name_input = QLineEdit()
        self.folder_name_input.setPlaceholderText("Ejemplo: IMAGENES")
        self.folder_name_input.setMinimumHeight(30)
        folder_layout.addRow("Nombre de carpeta:", self.folder_name_input)

        # Prefijo de archivo
        self.prefix_input = QLineEdit()
        self.prefix_input.setPlaceholderText("Ejemplo: screenshot")
        self.prefix_input.setMinimumHeight(30)
        folder_layout.addRow("Prefijo de archivo:", self.prefix_input)

        layout.addLayout(folder_layout)

        # Preview de ruta completa
        self.path_preview_label = QLabel("")
        self.path_preview_label.setStyleSheet("color: #888; font-size: 10px; padding: 10px; background-color: #1e1e1e; border-radius: 4px;")
        self.path_preview_label.setWordWrap(True)
        layout.addWidget(self.path_preview_label)

        # Conectar señales para actualizar preview
        self.folder_name_input.textChanged.connect(self._update_path_preview)
        self.prefix_input.textChanged.connect(self._update_path_preview)

        return group

    def _create_format_section(self) -> QGroupBox:
        """Crear sección de formato"""
        group = QGroupBox("🖼️ Formato de Imagen")
        layout = QFormLayout(group)

        # Formato
        self.format_combo = QComboBox()
        self.format_combo.addItems(["PNG", "JPG", "BMP"])
        self.format_combo.setCurrentText("PNG")
        self.format_combo.currentTextChanged.connect(self._on_format_changed)
        layout.addRow("Formato:", self.format_combo)

        # Calidad (solo para JPG)
        quality_layout = QHBoxLayout()

        self.quality_slider = QSlider(Qt.Orientation.Horizontal)
        self.quality_slider.setMinimum(1)
        self.quality_slider.setMaximum(100)
        self.quality_slider.setValue(95)
        self.quality_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.quality_slider.setTickInterval(10)
        self.quality_slider.valueChanged.connect(self._on_quality_changed)
        quality_layout.addWidget(self.quality_slider)

        self.quality_label = QLabel("95%")
        self.quality_label.setMinimumWidth(40)
        self.quality_label.setStyleSheet("color: #007acc; font-weight: bold;")
        quality_layout.addWidget(self.quality_label)

        self.quality_row_label = QLabel("Calidad JPG:")
        layout.addRow(self.quality_row_label, quality_layout)

        # Inicialmente ocultar calidad (solo visible para JPG)
        self.quality_row_label.setVisible(False)
        self.quality_slider.setVisible(False)
        self.quality_label.setVisible(False)

        return group

    def _create_hotkey_section(self) -> QGroupBox:
        """Crear sección de hotkey"""
        group = QGroupBox("Atajo de Teclado")
        layout = QVBoxLayout(group)

        # Descripción
        desc = QLabel(
            "Haz clic en el campo y presiona la combinacion de teclas que deseas usar.\n"
            "Ejemplo: Ctrl+Shift+S, Ctrl+Alt+C, etc."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #888; font-size: 11px; padding: 5px;")
        layout.addWidget(desc)

        # Input de hotkey con widget personalizado
        hotkey_layout = QHBoxLayout()

        self.hotkey_input = HotkeyInput()
        self.hotkey_input.setMinimumHeight(40)
        self.hotkey_input.hotkey_changed.connect(self._on_hotkey_changed)
        hotkey_layout.addWidget(self.hotkey_input)

        # Botón para limpiar
        self.hotkey_clear_btn = QPushButton("Limpiar")
        self.hotkey_clear_btn.setMinimumHeight(40)
        self.hotkey_clear_btn.setMaximumWidth(100)
        self.hotkey_clear_btn.clicked.connect(self._clear_hotkey)
        hotkey_layout.addWidget(self.hotkey_clear_btn)

        layout.addLayout(hotkey_layout)

        # Nota informativa
        note = QLabel("El atajo se aplicara al guardar y reiniciar la aplicacion")
        note.setStyleSheet("color: #888; font-size: 10px; padding: 5px;")
        layout.addWidget(note)

        return group

    def _create_behavior_section(self) -> QGroupBox:
        """Crear sección de comportamiento"""
        group = QGroupBox("⚙️ Comportamiento")
        layout = QVBoxLayout(group)

        # Copiar automáticamente
        self.auto_copy_checkbox = QCheckBox(
            "Copiar automáticamente al portapapeles"
        )
        self.auto_copy_checkbox.setChecked(True)
        layout.addWidget(self.auto_copy_checkbox)

        # Mostrar notificación
        self.show_notification_checkbox = QCheckBox(
            "Mostrar notificación al capturar"
        )
        self.show_notification_checkbox.setChecked(True)
        layout.addWidget(self.show_notification_checkbox)

        # Crear item automáticamente
        self.create_item_checkbox = QCheckBox(
            "Crear item automáticamente en categoría (TYPE=PATH)"
        )
        self.create_item_checkbox.setChecked(True)
        layout.addWidget(self.create_item_checkbox)

        # Habilitar anotaciones
        self.enable_annotations_checkbox = QCheckBox(
            "Habilitar herramientas de anotación (flechas, texto, figuras)"
        )
        self.enable_annotations_checkbox.setChecked(True)
        layout.addWidget(self.enable_annotations_checkbox)

        return group

    def _create_buttons_section(self) -> QHBoxLayout:
        """Crear sección de botones de acción"""
        layout = QHBoxLayout()

        self.open_folder_btn = QPushButton("📂 Abrir Carpeta de Capturas")
        self.open_folder_btn.setMinimumHeight(35)
        self.open_folder_btn.clicked.connect(self._open_screenshots_folder)
        layout.addWidget(self.open_folder_btn)

        layout.addStretch()

        self.save_btn = QPushButton("💾 Guardar Cambios")
        self.save_btn.setMinimumHeight(35)
        self.save_btn.setMinimumWidth(150)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        self.save_btn.clicked.connect(self._save_settings)
        layout.addWidget(self.save_btn)

        return layout

    def load_settings(self):
        """Cargar configuración actual"""
        # Cargar configuración de almacenamiento
        folder_name = self.config_manager.get_setting('screenshots_folder_name', 'IMAGENES')
        self.folder_name_input.setText(folder_name)

        prefix = self.config_manager.get_setting('screenshot_prefix', 'screenshot')
        self.prefix_input.setText(prefix)

        # Cargar formato
        format_value = self.config_manager.get_setting('screenshot_format', 'png').upper()
        index = self.format_combo.findText(format_value)
        if index >= 0:
            self.format_combo.setCurrentIndex(index)

        # Cargar calidad
        quality = int(self.config_manager.get_setting('screenshot_quality', '95'))
        self.quality_slider.setValue(quality)

        # Cargar hotkey
        hotkey = self.config_manager.get_setting('screenshot_hotkey', 'ctrl+shift+s')
        self.hotkey_input.set_hotkey(hotkey)

        # Cargar comportamiento
        auto_copy = self.config_manager.get_setting('screenshot_auto_copy', '1') == '1'
        self.auto_copy_checkbox.setChecked(auto_copy)

        show_notification = self.config_manager.get_setting('screenshot_show_notification', '1') == '1'
        self.show_notification_checkbox.setChecked(show_notification)

        create_item = self.config_manager.get_setting('screenshot_create_item', '1') == '1'
        self.create_item_checkbox.setChecked(create_item)

        enable_annotations = self.config_manager.get_setting('screenshot_enable_annotations', '1') == '1'
        self.enable_annotations_checkbox.setChecked(enable_annotations)

        # Actualizar preview
        self._update_path_preview()

    def _update_path_preview(self):
        """Actualizar preview de ruta completa"""
        # Obtener ruta base de archivos (usar files_base_path que es el que está en Settings > Archivos)
        base_path = self.config_manager.get_setting('files_base_path', '')
        folder_name = self.folder_name_input.text().strip()
        prefix = self.prefix_input.text().strip()

        if not folder_name:
            folder_name = "[Nombre de Carpeta]"

        if not prefix:
            prefix = "[Prefijo]"

        if base_path:
            full_path = os.path.join(base_path, folder_name)
            example_file = f"{prefix}_2025-11-27_14-30-45.{self.format_combo.currentText().lower()}"
            preview_text = f"📍 Ruta completa: {full_path}\n📄 Ejemplo archivo: {example_file}"
        else:
            preview_text = "⚠️ Ruta base no configurada. Configura la ruta base en la pestaña 'Archivos' primero."

        self.path_preview_label.setText(preview_text)

    def _on_format_changed(self, format_text: str):
        """Handler cuando cambia el formato"""
        # Mostrar/ocultar calidad según formato
        is_jpg = format_text.upper() == "JPG"
        self.quality_row_label.setVisible(is_jpg)
        self.quality_slider.setVisible(is_jpg)
        self.quality_label.setVisible(is_jpg)

        # Actualizar preview
        self._update_path_preview()

    def _on_quality_changed(self, value: int):
        """Handler cuando cambia la calidad"""
        self.quality_label.setText(f"{value}%")

    def _on_hotkey_changed(self, hotkey: str):
        """Handler cuando se captura un nuevo hotkey"""
        print(f"Nuevo hotkey capturado: {hotkey}")

    def _clear_hotkey(self):
        """Limpiar el hotkey actual"""
        self.hotkey_input.set_hotkey("")
        self.hotkey_input.setFocus()

    def _open_screenshots_folder(self):
        """Abrir carpeta de capturas en explorador de archivos"""
        # Usar files_base_path que es el configurado en Settings > Archivos
        base_path = self.config_manager.get_setting('files_base_path', '')
        folder_name = self.folder_name_input.text().strip()

        if not base_path:
            QMessageBox.warning(
                self,
                "Ruta Base No Configurada",
                "Debes configurar la ruta base en la pestaña 'Archivos' primero."
            )
            return

        if not folder_name:
            QMessageBox.warning(
                self,
                "Nombre de Carpeta Vacío",
                "Debes especificar un nombre para la carpeta de capturas."
            )
            return

        full_path = os.path.join(base_path, folder_name)

        # Crear carpeta si no existe
        if not os.path.exists(full_path):
            try:
                os.makedirs(full_path, exist_ok=True)
                QMessageBox.information(
                    self,
                    "Carpeta Creada",
                    f"La carpeta de capturas se ha creado en:\n{full_path}"
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error al Crear Carpeta",
                    f"No se pudo crear la carpeta:\n{str(e)}"
                )
                return

        # Abrir en explorador de archivos
        os.startfile(full_path)

    def _save_settings(self):
        """Guardar configuración"""
        # Validar nombre de carpeta
        folder_name = self.folder_name_input.text().strip()
        if not folder_name:
            QMessageBox.warning(
                self,
                "Nombre de Carpeta Vacío",
                "Debes especificar un nombre para la carpeta de capturas."
            )
            return

        # Validar prefijo
        prefix = self.prefix_input.text().strip()
        if not prefix:
            QMessageBox.warning(
                self,
                "Prefijo Vacío",
                "Debes especificar un prefijo para los archivos de captura."
            )
            return

        try:
            # Guardar configuración de almacenamiento
            self.config_manager.set_setting('screenshots_folder_name', folder_name)
            self.config_manager.set_setting('screenshot_prefix', prefix)

            # Guardar formato
            format_value = self.format_combo.currentText().lower()
            self.config_manager.set_setting('screenshot_format', format_value)

            # Guardar calidad
            quality = str(self.quality_slider.value())
            self.config_manager.set_setting('screenshot_quality', quality)

            # Guardar hotkey
            hotkey = self.hotkey_input.get_hotkey()
            if hotkey:
                self.config_manager.set_setting('screenshot_hotkey', hotkey)
            else:
                # Si está vacío, usar default
                self.config_manager.set_setting('screenshot_hotkey', 'ctrl+shift+s')

            # Guardar comportamiento
            auto_copy = '1' if self.auto_copy_checkbox.isChecked() else '0'
            self.config_manager.set_setting('screenshot_auto_copy', auto_copy)

            show_notification = '1' if self.show_notification_checkbox.isChecked() else '0'
            self.config_manager.set_setting('screenshot_show_notification', show_notification)

            create_item = '1' if self.create_item_checkbox.isChecked() else '0'
            self.config_manager.set_setting('screenshot_create_item', create_item)

            enable_annotations = '1' if self.enable_annotations_checkbox.isChecked() else '0'
            self.config_manager.set_setting('screenshot_enable_annotations', enable_annotations)

            # Emitir señal de cambio
            self.settings_changed.emit()

            # Recargar hotkey dinámicamente si el controller está disponible
            if self.controller and hasattr(self.controller, 'reload_screenshot_hotkey'):
                try:
                    self.controller.reload_screenshot_hotkey()
                    message = (
                        "La configuración de capturas de pantalla se ha guardado correctamente.\n\n"
                        "El atajo de teclado se ha actualizado y ya está listo para usar."
                    )
                except Exception as e:
                    print(f"Error al recargar hotkey: {e}")
                    message = (
                        "La configuración se ha guardado correctamente.\n\n"
                        "IMPORTANTE: Para que el nuevo atajo de teclado funcione, "
                        "debes reiniciar la aplicación."
                    )
            else:
                message = (
                    "La configuración de capturas de pantalla se ha guardado correctamente.\n\n"
                    "IMPORTANTE: Para que el nuevo atajo de teclado funcione, "
                    "debes reiniciar la aplicación."
                )

            QMessageBox.information(
                self,
                "Configuración Guardada",
                message
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error al Guardar",
                f"No se pudo guardar la configuración:\n{str(e)}"
            )
