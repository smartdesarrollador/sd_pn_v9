# -*- coding: utf-8 -*-
"""
Hotkey Input Widget - Widget para capturar atajos de teclado

Permite al usuario presionar una combinación de teclas y la captura automáticamente.
"""

from PyQt6.QtWidgets import QLineEdit
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QKeyEvent


class HotkeyInput(QLineEdit):
    """
    Widget de input para capturar combinaciones de teclas

    Señales:
        hotkey_changed(str): Emitida cuando se captura una nueva combinación
    """

    hotkey_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        # Estado
        self.current_keys = set()
        self.is_capturing = False

        # Configuración
        self.setPlaceholderText("Presiona las teclas del atajo...")
        self.setReadOnly(True)  # No editable directamente, solo por captura

        # Estilo
        self.setStyleSheet("""
            QLineEdit {
                background-color: #2d2d2d;
                color: #cccccc;
                border: 2px solid #3d3d3d;
                border-radius: 4px;
                padding: 8px;
                font-size: 11pt;
            }
            QLineEdit:focus {
                border: 2px solid #007acc;
                background-color: #1e1e1e;
            }
        """)

    def mousePressEvent(self, event):
        """Activar modo captura al hacer click"""
        self.is_capturing = True
        self.current_keys.clear()
        self.setText("Presionando...")
        self.setFocus()
        super().mousePressEvent(event)

    def keyPressEvent(self, event: QKeyEvent):
        """Capturar teclas presionadas"""
        if not self.is_capturing:
            super().keyPressEvent(event)
            return

        # Ignorar eventos de auto-repeat
        if event.isAutoRepeat():
            return

        # Obtener nombre de la tecla
        key_name = self._get_key_name(event.key())

        if key_name:
            self.current_keys.add(key_name)
            self._update_display()

        # No propagar el evento
        event.accept()

    def keyReleaseEvent(self, event: QKeyEvent):
        """Detectar cuando se sueltan todas las teclas"""
        if not self.is_capturing:
            super().keyReleaseEvent(event)
            return

        # Ignorar eventos de auto-repeat
        if event.isAutoRepeat():
            return

        # Si se suelta cualquier tecla, completar la captura
        if self.current_keys:
            self._complete_capture()

        event.accept()

    def focusOutEvent(self, event):
        """Completar captura si se pierde el foco"""
        if self.is_capturing and self.current_keys:
            self._complete_capture()
        super().focusOutEvent(event)

    def _get_key_name(self, key_code: int) -> str:
        """
        Convierte código de tecla a nombre legible

        Args:
            key_code: Código de tecla Qt

        Returns:
            Nombre de la tecla o None
        """
        # Teclas modificadoras
        modifiers = {
            Qt.Key.Key_Control: 'Ctrl',
            Qt.Key.Key_Shift: 'Shift',
            Qt.Key.Key_Alt: 'Alt',
            Qt.Key.Key_Meta: 'Win',
        }

        if key_code in modifiers:
            return modifiers[key_code]

        # Teclas especiales
        special_keys = {
            Qt.Key.Key_Space: 'Space',
            Qt.Key.Key_Return: 'Enter',
            Qt.Key.Key_Enter: 'Enter',
            Qt.Key.Key_Escape: 'Esc',
            Qt.Key.Key_Tab: 'Tab',
            Qt.Key.Key_Backspace: 'Backspace',
            Qt.Key.Key_Delete: 'Delete',
            Qt.Key.Key_Insert: 'Insert',
            Qt.Key.Key_Home: 'Home',
            Qt.Key.Key_End: 'End',
            Qt.Key.Key_PageUp: 'PageUp',
            Qt.Key.Key_PageDown: 'PageDown',
            Qt.Key.Key_Up: 'Up',
            Qt.Key.Key_Down: 'Down',
            Qt.Key.Key_Left: 'Left',
            Qt.Key.Key_Right: 'Right',
        }

        if key_code in special_keys:
            return special_keys[key_code]

        # Teclas de función
        if Qt.Key.Key_F1 <= key_code <= Qt.Key.Key_F12:
            f_num = key_code - Qt.Key.Key_F1 + 1
            return f'F{f_num}'

        # Teclas alfanuméricas
        if 32 <= key_code <= 126:
            return chr(key_code).upper()

        return None

    def _update_display(self):
        """Actualiza el texto mostrado con las teclas actuales"""
        if not self.current_keys:
            self.setText("Presionando...")
            return

        # Ordenar las teclas: modificadores primero, luego otras
        modifier_order = ['Ctrl', 'Alt', 'Shift', 'Win']
        modifiers = [k for k in modifier_order if k in self.current_keys]
        others = sorted([k for k in self.current_keys if k not in modifier_order])

        all_keys = modifiers + others
        display_text = '+'.join(all_keys)

        self.setText(display_text)

    def _complete_capture(self):
        """Completa la captura del hotkey"""
        self.is_capturing = False

        if not self.current_keys:
            self.setText("")
            return

        # Generar combinación final
        modifier_order = ['Ctrl', 'Alt', 'Shift', 'Win']
        modifiers = [k for k in modifier_order if k in self.current_keys]
        others = sorted([k for k in self.current_keys if k not in modifier_order])

        all_keys = modifiers + others

        # Validar que haya al menos una tecla
        if not all_keys:
            self.setText("")
            self.current_keys.clear()
            return

        # Convertir a formato para HotkeyManager (lowercase con +)
        hotkey_str = '+'.join(all_keys)
        display_str = '+'.join(all_keys)

        # Formato para guardar (lowercase)
        save_format = '+'.join([k.lower() for k in all_keys])

        self.setText(display_str)

        # Emitir señal con formato de guardado
        self.hotkey_changed.emit(save_format)

        # Limpiar estado
        self.current_keys.clear()

    def set_hotkey(self, hotkey_str: str):
        """
        Establece el hotkey desde un string

        Args:
            hotkey_str: String del hotkey (ej: "ctrl+shift+s")
        """
        if not hotkey_str:
            self.setText("")
            return

        # Convertir a formato de display
        parts = hotkey_str.split('+')
        display_parts = []

        for part in parts:
            part = part.strip().lower()
            if part == 'ctrl':
                display_parts.append('Ctrl')
            elif part == 'shift':
                display_parts.append('Shift')
            elif part == 'alt':
                display_parts.append('Alt')
            elif part == 'win' or part == 'meta':
                display_parts.append('Win')
            else:
                display_parts.append(part.upper())

        display_str = '+'.join(display_parts)
        self.setText(display_str)

    def get_hotkey(self) -> str:
        """
        Obtiene el hotkey actual en formato de guardado

        Returns:
            String del hotkey en formato lowercase (ej: "ctrl+shift+s")
        """
        text = self.text()
        if not text:
            return ""

        # Convertir de display a formato guardado
        parts = text.split('+')
        save_parts = [p.strip().lower() for p in parts]

        return '+'.join(save_parts)
