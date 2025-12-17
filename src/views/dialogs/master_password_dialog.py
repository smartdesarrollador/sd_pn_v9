"""
Master Password Verification Dialog
Dialog to verify master password for accessing sensitive items and exports
"""
import sys
from pathlib import Path
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton,
    QHBoxLayout
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
import logging

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from src.core.master_password_manager import MasterPasswordManager
from src.core.master_auth_cache import get_master_auth_cache

logger = logging.getLogger(__name__)


class MasterPasswordDialog(QDialog):
    """Dialog to verify master password for sensitive operations"""

    def __init__(self, title="Contraseña Maestra", message="Ingresa tu contraseña maestra para continuar:", parent=None):
        """
        Initialize master password verification dialog

        Args:
            title: Dialog title
            message: Message to display
            parent: Parent widget
        """
        super().__init__(parent)
        self.master_mgr = MasterPasswordManager()
        self.title_text = title
        self.message_text = message
        self.password_verified = False
        self.init_ui()

    def init_ui(self):
        """Initialize UI"""
        self.setWindowTitle(self.title_text)
        self.setFixedSize(450, 240)
        self.setModal(True)

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(25, 25, 25, 25)
        main_layout.setSpacing(15)

        # Title with icon
        title = QLabel(f"🔐 {self.title_text}")
        title_font = QFont()
        title_font.setPointSize(13)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title)

        # Message
        message = QLabel(self.message_text)
        message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        message.setWordWrap(True)
        main_layout.addWidget(message)

        main_layout.addSpacing(10)

        # Password input
        password_label = QLabel("Contraseña Maestra:")
        main_layout.addWidget(password_label)

        # Password container with show/hide button
        password_container = QHBoxLayout()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Ingresa tu contraseña maestra...")
        self.password_input.returnPressed.connect(self.verify_password)
        password_container.addWidget(self.password_input)

        # Show/hide button
        self.show_password_btn = QPushButton("👁")
        self.show_password_btn.setFixedSize(35, 35)
        self.show_password_btn.setToolTip("Mostrar/Ocultar contraseña")
        self.show_password_btn.clicked.connect(self.toggle_password_visibility)
        password_container.addWidget(self.show_password_btn)

        main_layout.addLayout(password_container)

        # Error label
        self.error_label = QLabel("")
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.error_label.setStyleSheet("color: #ff4444; font-weight: bold;")
        self.error_label.hide()
        main_layout.addWidget(self.error_label)

        main_layout.addStretch()

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_btn = QPushButton("Cancelar")
        cancel_btn.setFixedSize(100, 35)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        verify_btn = QPushButton("Verificar")
        verify_btn.setFixedSize(100, 35)
        verify_btn.clicked.connect(self.verify_password)
        verify_btn.setDefault(True)  # Make it default button
        button_layout.addWidget(verify_btn)

        main_layout.addLayout(button_layout)

        # Apply styles
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e1e;
            }
            QLabel {
                color: #cccccc;
            }
            QLineEdit {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 2px solid #3d3d3d;
                border-radius: 4px;
                padding: 8px;
                font-size: 10pt;
            }
            QLineEdit:focus {
                border: 2px solid #00aa55;
            }
            QPushButton {
                background-color: #00aa55;
                color: #ffffff;
                border: none;
                border-radius: 4px;
                font-size: 10pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #008844;
            }
            QPushButton:pressed {
                background-color: #006633;
            }
            QPushButton#cancel {
                background-color: #555555;
            }
            QPushButton#cancel:hover {
                background-color: #666666;
            }
        """)

        # Set object name for cancel button
        cancel_btn.setObjectName("cancel")

        # Focus on password input
        self.password_input.setFocus()

    def toggle_password_visibility(self):
        """Toggle password visibility"""
        if self.password_input.echoMode() == QLineEdit.EchoMode.Password:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self.show_password_btn.setText("🔒")
        else:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.show_password_btn.setText("👁")

    def verify_password(self):
        """Verify the entered master password"""
        password = self.password_input.text()

        if not password:
            self.show_error("Por favor ingresa tu contraseña maestra")
            return

        # Verify password with MasterPasswordManager
        if self.master_mgr.verify_master_password(password):
            self.password_verified = True
            logger.info("Master password verified in dialog")

            # Update cache
            cache = get_master_auth_cache()
            cache.authenticate()
            logger.debug("Master password cache authenticated")

            self.accept()
        else:
            self.show_error("Contraseña maestra incorrecta")
            self.password_input.clear()
            self.password_input.setFocus()
            logger.warning("Master password verification failed in dialog")

            # Shake animation for error feedback
            self.shake_dialog()

    def show_error(self, message):
        """Show error message"""
        self.error_label.setText(message)
        self.error_label.show()

    def shake_dialog(self):
        """Shake dialog for error feedback"""
        from PyQt6.QtCore import QPropertyAnimation, QRect

        # Get current geometry
        current_geom = self.geometry()

        # Create animation
        animation = QPropertyAnimation(self, b"geometry")
        animation.setDuration(500)
        animation.setLoopCount(1)

        # Shake left and right
        animation.setKeyValueAt(0, current_geom)
        animation.setKeyValueAt(0.1, QRect(current_geom.x() - 10, current_geom.y(), current_geom.width(), current_geom.height()))
        animation.setKeyValueAt(0.2, QRect(current_geom.x() + 10, current_geom.y(), current_geom.width(), current_geom.height()))
        animation.setKeyValueAt(0.3, QRect(current_geom.x() - 10, current_geom.y(), current_geom.width(), current_geom.height()))
        animation.setKeyValueAt(0.4, QRect(current_geom.x() + 10, current_geom.y(), current_geom.width(), current_geom.height()))
        animation.setKeyValueAt(0.5, QRect(current_geom.x() - 5, current_geom.y(), current_geom.width(), current_geom.height()))
        animation.setKeyValueAt(0.6, QRect(current_geom.x() + 5, current_geom.y(), current_geom.width(), current_geom.height()))
        animation.setKeyValueAt(1, current_geom)

        animation.start()

    @staticmethod
    def verify(title="Contraseña Maestra", message="Ingresa tu contraseña maestra para continuar:", parent=None):
        """
        Static method to show verification dialog and return result

        IMPORTANT: This method checks if master password is configured first.
        If no master password exists, returns True immediately (no verification needed).

        Args:
            title: Dialog title
            message: Message to display
            parent: Parent widget

        Returns:
            bool: True if password was verified OR no master password configured, False if cancelled

        Example:
            from views.dialogs.master_password_dialog import MasterPasswordDialog

            # Check before copying sensitive item
            if MasterPasswordDialog.verify(
                title="Item Sensible",
                message="Ingresa tu contraseña maestra para copiar este item:",
                parent=self
            ):
                # Password verified or not configured - proceed
                clipboard.copy(item.content)
            else:
                # User cancelled
                pass
        """
        # CRITICAL: Check if master password is configured
        master_mgr = MasterPasswordManager()
        if not master_mgr.has_master_password():
            logger.debug("No master password configured - allowing access without verification")
            return True

        # Master password exists - show dialog
        logger.debug("Master password configured - showing verification dialog")
        dialog = MasterPasswordDialog(title, message, parent)
        result = dialog.exec()
        return result == QDialog.DialogCode.Accepted and dialog.password_verified
