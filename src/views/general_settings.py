"""
General Settings
Widget for general application settings
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox,
    QSpinBox, QPushButton, QGroupBox, QFormLayout, QFileDialog,
    QMessageBox, QLineEdit
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
import json
import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from views.dialogs.password_verify_dialog import PasswordVerifyDialog
from core.auth_manager import AuthManager
from core.master_password_manager import MasterPasswordManager

logger = logging.getLogger(__name__)


class GeneralSettings(QWidget):
    """
    General settings widget
    Configure misc application options
    """

    # Signal emitted when settings change
    settings_changed = pyqtSignal()

    def __init__(self, config_manager=None, parent=None):
        """
        Initialize general settings

        Args:
            config_manager: ConfigManager instance
            parent: Parent widget
        """
        super().__init__(parent)
        self.config_manager = config_manager

        self.init_ui()
        self.load_settings()

    def init_ui(self):
        """Initialize the UI"""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # Behavior group
        behavior_group = QGroupBox("Comportamiento")
        behavior_layout = QVBoxLayout()
        behavior_layout.setSpacing(10)

        # Minimize to tray checkbox
        self.minimize_tray_check = QCheckBox("Minimizar a tray al cerrar ventana")
        self.minimize_tray_check.setChecked(True)
        self.minimize_tray_check.stateChanged.connect(self.settings_changed)
        behavior_layout.addWidget(self.minimize_tray_check)

        # Always on top checkbox
        self.always_on_top_check = QCheckBox("Mantener ventana siempre visible")
        self.always_on_top_check.setChecked(True)
        self.always_on_top_check.stateChanged.connect(self.settings_changed)
        behavior_layout.addWidget(self.always_on_top_check)

        # Start with Windows checkbox
        self.start_windows_check = QCheckBox("Iniciar con Windows (próximamente)")
        self.start_windows_check.setChecked(False)
        self.start_windows_check.setEnabled(False)
        behavior_layout.addWidget(self.start_windows_check)

        behavior_group.setLayout(behavior_layout)
        main_layout.addWidget(behavior_group)

        # Clipboard group
        clipboard_group = QGroupBox("Portapapeles")
        clipboard_layout = QFormLayout()
        clipboard_layout.setSpacing(10)

        # Max history items
        self.max_history_spin = QSpinBox()
        self.max_history_spin.setMinimum(10)
        self.max_history_spin.setMaximum(50)
        self.max_history_spin.setValue(20)
        self.max_history_spin.setSuffix(" items")
        self.max_history_spin.valueChanged.connect(self.settings_changed)
        clipboard_layout.addRow("Máximo items historial:", self.max_history_spin)

        clipboard_group.setLayout(clipboard_layout)
        main_layout.addWidget(clipboard_group)

        # Security group
        security_group = QGroupBox("Seguridad")
        security_layout = QFormLayout()
        security_layout.setSpacing(10)

        # Current password
        self.current_password_input = QLineEdit()
        self.current_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.current_password_input.setPlaceholderText("Ingresa tu contraseña actual")
        security_layout.addRow("Contraseña actual:", self.current_password_input)

        # New password
        self.new_password_input = QLineEdit()
        self.new_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.new_password_input.setPlaceholderText("Ingresa tu nueva contraseña")
        security_layout.addRow("Nueva contraseña:", self.new_password_input)

        # Confirm password
        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_password_input.setPlaceholderText("Confirma tu nueva contraseña")
        security_layout.addRow("Confirmar contraseña:", self.confirm_password_input)

        # Change password button
        change_password_btn_layout = QHBoxLayout()
        change_password_btn_layout.addStretch()
        self.change_password_btn = QPushButton("Cambiar Contraseña")
        self.change_password_btn.clicked.connect(self.change_password)
        self.change_password_btn.setStyleSheet("""
            QPushButton {
                background-color: #007acc;
                color: #ffffff;
                border: none;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #005a9e;
            }
            QPushButton:pressed {
                background-color: #004578;
            }
        """)
        change_password_btn_layout.addWidget(self.change_password_btn)
        security_layout.addRow("", change_password_btn_layout)

        security_group.setLayout(security_layout)
        main_layout.addWidget(security_group)

        # Master Password group
        master_password_group = QGroupBox("🔐 Contraseña Maestra")
        master_password_layout = QVBoxLayout()
        master_password_layout.setSpacing(10)

        # Description
        master_desc = QLabel(
            "La contraseña maestra protege items sensibles y exportaciones (opcional).\n"
            "Si no la configuras, los items sensibles serán accesibles sin protección adicional."
        )
        master_desc.setWordWrap(True)
        master_desc.setStyleSheet("color: #aaaaaa; font-size: 9pt; padding: 5px;")
        master_password_layout.addWidget(master_desc)

        # Status indicator
        self.master_status_label = QLabel()
        self.master_status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.master_status_label.setStyleSheet("padding: 5px; font-weight: bold;")
        master_password_layout.addWidget(self.master_status_label)

        # Form layout for inputs
        master_form_layout = QFormLayout()
        master_form_layout.setSpacing(10)

        # Current master password
        self.master_current_input = QLineEdit()
        self.master_current_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.master_current_input.setPlaceholderText("Ingresa tu contraseña maestra actual")
        master_form_layout.addRow("Contraseña actual:", self.master_current_input)

        # New master password
        self.master_new_input = QLineEdit()
        self.master_new_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.master_new_input.setPlaceholderText("Ingresa una nueva contraseña maestra")
        master_form_layout.addRow("Nueva contraseña:", self.master_new_input)

        # Confirm master password
        self.master_confirm_input = QLineEdit()
        self.master_confirm_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.master_confirm_input.setPlaceholderText("Confirma tu nueva contraseña maestra")
        master_form_layout.addRow("Confirmar contraseña:", self.master_confirm_input)

        master_password_layout.addLayout(master_form_layout)

        # Master password button (dynamic text)
        master_btn_layout = QHBoxLayout()
        master_btn_layout.addStretch()
        self.master_password_btn = QPushButton()
        self.master_password_btn.clicked.connect(self.create_or_change_master_password)
        self.master_password_btn.setStyleSheet("""
            QPushButton {
                background-color: #00aa55;
                color: #ffffff;
                border: none;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #008844;
            }
            QPushButton:pressed {
                background-color: #006633;
            }
        """)
        master_btn_layout.addWidget(self.master_password_btn)
        master_password_layout.addLayout(master_btn_layout)

        master_password_group.setLayout(master_password_layout)
        main_layout.addWidget(master_password_group)

        # Update master password UI state
        self.update_master_password_ui()

        # Import/Export group
        io_group = QGroupBox("Importar/Exportar")
        io_layout = QVBoxLayout()
        io_layout.setSpacing(10)

        # Export button
        export_layout = QHBoxLayout()
        export_label = QLabel("Exportar configuración:")
        self.export_button = QPushButton("Exportar...")
        self.export_button.clicked.connect(self.export_config)
        export_layout.addWidget(export_label)
        export_layout.addStretch()
        export_layout.addWidget(self.export_button)
        io_layout.addLayout(export_layout)

        # Import button
        import_layout = QHBoxLayout()
        import_label = QLabel("Importar configuración:")
        self.import_button = QPushButton("Importar...")
        self.import_button.clicked.connect(self.import_config)
        import_layout.addWidget(import_label)
        import_layout.addStretch()
        import_layout.addWidget(self.import_button)
        io_layout.addLayout(import_layout)

        io_group.setLayout(io_layout)
        main_layout.addWidget(io_group)

        # About group
        about_group = QGroupBox("Acerca de")
        about_layout = QVBoxLayout()
        about_layout.setSpacing(5)

        about_text = QLabel(
            "<b>Widget Sidebar</b><br>"
            "Version: 2.0.0<br>"
            "Framework: PyQt6<br>"
            "Architecture: MVC<br><br>"
            "Gestor avanzado de portapapeles para Windows"
        )
        about_text.setStyleSheet("font-size: 10pt;")
        about_layout.addWidget(about_text)

        about_group.setLayout(about_layout)
        main_layout.addWidget(about_group)

        # Spacer
        main_layout.addStretch()

        # Apply widget styles
        self.setStyleSheet("""
            GeneralSettings {
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
            QSpinBox {
                background-color: #2d2d2d;
                color: #cccccc;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                padding: 5px;
                min-width: 100px;
            }
            QSpinBox:focus {
                border: 1px solid #007acc;
            }
            QLineEdit {
                background-color: #2d2d2d;
                color: #cccccc;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                padding: 8px;
                min-width: 200px;
            }
            QLineEdit:focus {
                border: 1px solid #007acc;
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
        """)

    def load_settings(self):
        """Load settings from config manager"""
        if not self.config_manager:
            return

        # Load minimize to tray (default True)
        minimize_tray = self.config_manager.get_setting("minimize_to_tray", True)
        self.minimize_tray_check.setChecked(minimize_tray)

        # Load always on top
        always_on_top = self.config_manager.get_setting("always_on_top", True)
        self.always_on_top_check.setChecked(always_on_top)

        # Load start with windows
        start_windows = self.config_manager.get_setting("start_with_windows", False)
        self.start_windows_check.setChecked(start_windows)

        # Load max history
        max_history = self.config_manager.get_setting("max_history", 20)
        self.max_history_spin.setValue(max_history)

    def _has_sensitive_items(self) -> bool:
        """
        Check if configuration contains sensitive items

        Returns:
            True if any item has is_sensitive=True, False otherwise
        """
        if not self.config_manager or not self.config_manager.db:
            return False

        try:
            # Query database for any sensitive items
            db = self.config_manager.db
            with db.transaction() as conn:
                cursor = conn.execute(
                    "SELECT COUNT(*) FROM items WHERE is_sensitive = 1"
                )
                count = cursor.fetchone()[0]
                has_sensitive = count > 0

                if has_sensitive:
                    logger.info(f"Found {count} sensitive items in configuration")
                else:
                    logger.debug("No sensitive items found in configuration")

                return has_sensitive
        except Exception as e:
            logger.error(f"Error checking for sensitive items: {e}")
            return False

    def export_config(self):
        """Export configuration to JSON file"""
        if not self.config_manager:
            QMessageBox.warning(
                self,
                "Error",
                "ConfigManager no disponible"
            )
            return

        # Verify password before exporting (security measure)
        password_verified = PasswordVerifyDialog.verify(
            title="Exportar Configuración",
            message="Por razones de seguridad, ingresa tu contraseña para exportar la configuración:",
            parent=self.window()
        )

        if not password_verified:
            # User cancelled or password incorrect
            return

        # ⚠️ PROTECTION: Verify master password if configuration has sensitive items
        if self._has_sensitive_items():
            logger.info("Configuration contains sensitive items - verifying master password")

            # Check if master password is configured
            master_mgr = MasterPasswordManager()
            if master_mgr.has_master_password():
                # Master password exists - verify it
                from views.dialogs.master_password_dialog import MasterPasswordDialog

                master_verified = MasterPasswordDialog.verify(
                    title="Exportar Configuración",
                    message="Tu configuración incluye items sensibles.\nIngresa tu contraseña maestra para continuar:",
                    parent=self.window()
                )

                if not master_verified:
                    logger.warning("Export cancelled - master password verification failed")
                    return
            else:
                # No master password configured - allow export (optional behavior)
                logger.debug("No master password configured - exporting without additional verification")

        # Open file dialog
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Exportar Configuración",
            str(Path.home() / "widget_sidebar_config.json"),
            "JSON Files (*.json)"
        )

        if not file_path:
            return

        try:
            # Export config
            success = self.config_manager.export_config(file_path)
            if success:
                QMessageBox.information(
                    self,
                    "Exportar",
                    f"Configuración exportada exitosamente a:\n{file_path}"
                )
            else:
                QMessageBox.warning(
                    self,
                    "Error",
                    "No se pudo exportar la configuración"
                )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Error al exportar configuración:\n{str(e)}"
            )

    def import_config(self):
        """Import configuration from JSON file"""
        if not self.config_manager:
            QMessageBox.warning(
                self,
                "Error",
                "ConfigManager no disponible"
            )
            return

        # Open file dialog
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Importar Configuración",
            str(Path.home()),
            "JSON Files (*.json)"
        )

        if not file_path:
            return

        try:
            # Import config
            success = self.config_manager.import_config(file_path)
            if success:
                QMessageBox.information(
                    self,
                    "Importar",
                    "Configuración importada exitosamente.\n"
                    "Reinicie la aplicación para aplicar los cambios."
                )
                # Reload settings
                self.load_settings()
            else:
                QMessageBox.warning(
                    self,
                    "Error",
                    "No se pudo importar la configuración"
                )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Error al importar configuración:\n{str(e)}"
            )

    def change_password(self):
        """Change user password"""
        # Get values
        current_password = self.current_password_input.text()
        new_password = self.new_password_input.text()
        confirm_password = self.confirm_password_input.text()

        # Validate inputs
        if not current_password:
            QMessageBox.warning(
                self,
                "Error",
                "Por favor ingresa tu contraseña actual"
            )
            self.current_password_input.setFocus()
            return

        if not new_password:
            QMessageBox.warning(
                self,
                "Error",
                "Por favor ingresa una nueva contraseña"
            )
            self.new_password_input.setFocus()
            return

        if len(new_password) < 4:
            QMessageBox.warning(
                self,
                "Error",
                "La nueva contraseña debe tener al menos 4 caracteres"
            )
            self.new_password_input.setFocus()
            return

        if not confirm_password:
            QMessageBox.warning(
                self,
                "Error",
                "Por favor confirma tu nueva contraseña"
            )
            self.confirm_password_input.setFocus()
            return

        # Validate passwords match
        if new_password != confirm_password:
            QMessageBox.warning(
                self,
                "Error",
                "Las contraseñas no coinciden"
            )
            self.confirm_password_input.clear()
            self.confirm_password_input.setFocus()
            return

        # Validate current password is different from new
        if current_password == new_password:
            QMessageBox.warning(
                self,
                "Error",
                "La nueva contraseña debe ser diferente a la actual"
            )
            self.new_password_input.clear()
            self.confirm_password_input.clear()
            self.new_password_input.setFocus()
            return

        # Change password using AuthManager
        auth_manager = AuthManager()
        success = auth_manager.change_password(current_password, new_password)

        if success:
            # Success
            QMessageBox.information(
                self,
                "Contraseña Cambiada",
                "Tu contraseña ha sido cambiada exitosamente"
            )
            logger.info("Password changed successfully")

            # Clear fields
            self.current_password_input.clear()
            self.new_password_input.clear()
            self.confirm_password_input.clear()
        else:
            # Failed - incorrect current password
            QMessageBox.warning(
                self,
                "Error",
                "La contraseña actual es incorrecta"
            )
            self.current_password_input.clear()
            self.current_password_input.setFocus()
            logger.warning("Failed to change password: incorrect current password")

    def update_master_password_ui(self):
        """Update master password UI state (button text and status)"""
        master_mgr = MasterPasswordManager()

        if master_mgr.is_first_time():
            # No master password configured
            self.master_password_btn.setText("Crear Contraseña Maestra")
            self.master_status_label.setText("⚠ No configurada")
            self.master_status_label.setStyleSheet(
                "color: #ff9900; background-color: #2d2d00; "
                "padding: 5px; font-weight: bold; border-radius: 3px;"
            )
            # Make current password field optional (show hint)
            self.master_current_input.setPlaceholderText("Déjalo vacío (primera vez)")
        else:
            # Master password already configured
            self.master_password_btn.setText("Cambiar Contraseña Maestra")
            self.master_status_label.setText("✓ Configurada")
            self.master_status_label.setStyleSheet(
                "color: #00ff88; background-color: #002d1a; "
                "padding: 5px; font-weight: bold; border-radius: 3px;"
            )
            # Current password is required
            self.master_current_input.setPlaceholderText("Ingresa tu contraseña maestra actual")

    def create_or_change_master_password(self):
        """Create or change master password"""
        master_mgr = MasterPasswordManager()

        current_password = self.master_current_input.text()
        new_password = self.master_new_input.text()
        confirm_password = self.master_confirm_input.text()

        # Validate new password
        if not new_password:
            QMessageBox.warning(
                self,
                "Error",
                "Por favor ingresa una nueva contraseña maestra"
            )
            self.master_new_input.setFocus()
            return

        if len(new_password) < 4:
            QMessageBox.warning(
                self,
                "Error",
                "La contraseña maestra debe tener al menos 4 caracteres"
            )
            self.master_new_input.setFocus()
            return

        # Validate confirmation
        if not confirm_password:
            QMessageBox.warning(
                self,
                "Error",
                "Por favor confirma tu nueva contraseña maestra"
            )
            self.master_confirm_input.setFocus()
            return

        if new_password != confirm_password:
            QMessageBox.warning(
                self,
                "Error",
                "Las contraseñas no coinciden"
            )
            self.master_confirm_input.clear()
            self.master_confirm_input.setFocus()
            return

        # First time - Create master password
        if master_mgr.is_first_time():
            # Current password can be empty
            master_mgr.set_master_password(new_password)

            QMessageBox.information(
                self,
                "Contraseña Maestra Creada",
                "Tu contraseña maestra ha sido creada exitosamente.\n\n"
                "Ahora los items sensibles y las exportaciones requerirán "
                "esta contraseña para ser accedidos."
            )
            logger.info("Master password created successfully")

            # Clear fields
            self.master_current_input.clear()
            self.master_new_input.clear()
            self.master_confirm_input.clear()

            # Update UI
            self.update_master_password_ui()

        # Already exists - Change master password
        else:
            # Validate current password is provided
            if not current_password:
                QMessageBox.warning(
                    self,
                    "Error",
                    "Por favor ingresa tu contraseña maestra actual"
                )
                self.master_current_input.setFocus()
                return

            # Validate current password is different from new
            if current_password == new_password:
                QMessageBox.warning(
                    self,
                    "Error",
                    "La nueva contraseña debe ser diferente a la actual"
                )
                self.master_new_input.clear()
                self.master_confirm_input.clear()
                self.master_new_input.setFocus()
                return

            # Change password
            success = master_mgr.change_master_password(current_password, new_password)

            if success:
                QMessageBox.information(
                    self,
                    "Contraseña Maestra Cambiada",
                    "Tu contraseña maestra ha sido cambiada exitosamente."
                )
                logger.info("Master password changed successfully")

                # Clear fields
                self.master_current_input.clear()
                self.master_new_input.clear()
                self.master_confirm_input.clear()
            else:
                QMessageBox.warning(
                    self,
                    "Error",
                    "La contraseña maestra actual es incorrecta"
                )
                self.master_current_input.clear()
                self.master_current_input.setFocus()
                logger.warning("Failed to change master password - incorrect current password")

    def get_settings(self) -> dict:
        """
        Get current general settings

        Returns:
            Dictionary with general settings
        """
        return {
            "minimize_to_tray": self.minimize_tray_check.isChecked(),
            "always_on_top": self.always_on_top_check.isChecked(),
            "start_with_windows": self.start_windows_check.isChecked(),
            "max_history": self.max_history_spin.value()
        }
