"""
Project Card Widget - Card moderna para Modo Limpio

Diseño en card estilo Material Design para mostrar elementos del proyecto
en un grid responsive. Incluye:
- Hover effects con sombras elevadas
- Preview de contenido
- Metadata visible (tipo, fecha)
- Badge de tipo de elemento
- Bordes de color según tipo
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QFrame, QPushButton, QGraphicsDropShadowEffect,
                             QGraphicsOpacityEffect)
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve, QSize, QTimer, QRect
from PyQt6.QtGui import QCursor, QColor, QPainter, QPen, QFont
import logging

logger = logging.getLogger(__name__)


class ProjectCardWidget(QWidget):
    """Card moderna para mostrar elementos del proyecto en modo limpio"""

    # Señales
    clicked = pyqtSignal(str)  # Emite el contenido a copiar

    # Colores por tipo de elemento
    TYPE_COLORS = {
        'tag': '#00ff88',      # Verde
        'item': '#00ccff',     # Azul
        'category': '#ff8800', # Naranja
        'list': '#aa88ff',     # Púrpura
        'table': '#ff0088',    # Rosa
        'process': '#88ff00',  # Lima
        'comment': '#00ccff',  # Azul claro
        'alert': '#ffaa00',    # Amarillo/Naranja
        'note': '#00ff88',     # Verde
        'divider': '#555555'   # Gris
    }

    # Iconos por tipo
    TYPE_ICONS = {
        'tag': '🏷️',
        'item': '📄',
        'category': '📂',
        'list': '📋',
        'table': '📊',
        'process': '⚙️',
        'comment': '💬',
        'alert': '⚠️',
        'note': '📌',
        'divider': '─'
    }

    def __init__(self, item_data: dict, item_type: str, parent=None):
        """
        Args:
            item_data: Datos del elemento (puede ser relation o component)
            item_type: Tipo de elemento ('tag', 'item', 'category', etc.)
        """
        super().__init__(parent)

        self.item_data = item_data
        self.item_type = item_type
        self.is_hovered = False
        self.show_copied_indicator = False  # Para mostrar checkmark al copiar

        # Guardar el nombre original completo para copiar
        self.original_name = item_data.get('name', item_data.get('content', ''))

        # Configurar tamaño fijo de la card
        self.setFixedSize(280, 160)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.init_ui()
        self.setup_shadow_effect()

        # Timer para ocultar el indicador de copiado
        self.copied_timer = QTimer()
        self.copied_timer.setSingleShot(True)
        self.copied_timer.timeout.connect(self.hide_copied_indicator)

    def init_ui(self):
        """Inicializa la interfaz de la card"""
        # Layout principal
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Frame contenedor
        self.card_frame = QFrame()
        self.card_frame.setObjectName("cardFrame")

        # Color del borde según tipo
        border_color = self.TYPE_COLORS.get(self.item_type, '#555555')

        self.card_frame.setStyleSheet(f"""
            QFrame#cardFrame {{
                background-color: #2d2d2d;
                border: 2px solid {border_color};
                border-radius: 8px;
                padding: 12px;
            }}
            QFrame#cardFrame:hover {{
                background-color: #353535;
                border-color: #ffffff;
            }}
        """)

        card_layout = QVBoxLayout(self.card_frame)
        card_layout.setContentsMargins(12, 12, 12, 12)
        card_layout.setSpacing(8)

        # Header: Icono + Nombre + Badge
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)

        # Icono del elemento
        icon = self.item_data.get('icon', self.TYPE_ICONS.get(self.item_type, '📄'))
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 20pt;")
        icon_label.setFixedSize(32, 32)
        header_layout.addWidget(icon_label)

        # Nombre del elemento
        name = self.item_data.get('name', self.item_data.get('content', 'Sin nombre'))
        # Truncar nombre largo
        if len(name) > 25:
            name = name[:22] + '...'

        name_label = QLabel(name)
        name_label.setWordWrap(True)
        name_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 11pt;
                font-weight: bold;
            }
        """)
        header_layout.addWidget(name_label, 1)

        # Badge de tipo
        type_badge = QLabel(self.item_type.upper())
        type_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        type_badge.setFixedSize(48, 20)
        type_badge.setStyleSheet(f"""
            QLabel {{
                background-color: {border_color};
                color: #000000;
                font-size: 7pt;
                font-weight: bold;
                border-radius: 3px;
                padding: 2px 4px;
            }}
        """)
        header_layout.addWidget(type_badge)

        card_layout.addLayout(header_layout)

        # Separador
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet(f"background-color: {border_color}; max-height: 1px;")
        card_layout.addWidget(separator)

        # Descripción / Preview
        description = self.item_data.get('description', '')
        content = self.item_data.get('content', '')

        preview_text = description if description else content

        # Truncar preview
        if preview_text and len(preview_text) > 100:
            preview_text = preview_text[:97] + '...'

        preview_label = QLabel(preview_text or "Sin descripción")
        preview_label.setWordWrap(True)
        preview_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        preview_label.setStyleSheet("""
            QLabel {
                color: #aaaaaa;
                font-size: 9pt;
                font-style: italic;
            }
        """)
        preview_label.setMinimumHeight(40)
        card_layout.addWidget(preview_label, 1)

        # Footer: Metadata
        footer_layout = QHBoxLayout()
        footer_layout.setSpacing(8)

        # Tipo de contenido (para items)
        if 'type' in self.item_data and self.item_data['type']:
            content_type_label = QLabel(f"📋 {self.item_data['type']}")
            content_type_label.setStyleSheet("""
                QLabel {
                    color: #888888;
                    font-size: 8pt;
                }
            """)
            footer_layout.addWidget(content_type_label)

        footer_layout.addStretch()

        # Fecha de última modificación (si existe)
        if 'updated_at' in self.item_data or 'created_at' in self.item_data:
            date = self.item_data.get('updated_at', self.item_data.get('created_at', ''))
            if date:
                # Extraer solo la fecha (primeros 10 caracteres)
                date_str = str(date)[:10]
                date_label = QLabel(f"⏰ {date_str}")
                date_label.setStyleSheet("""
                    QLabel {
                        color: #888888;
                        font-size: 8pt;
                    }
                """)
                footer_layout.addWidget(date_label)

        card_layout.addLayout(footer_layout)

        main_layout.addWidget(self.card_frame)

    def setup_shadow_effect(self):
        """Configura el efecto de sombra"""
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(10)
        self.shadow.setXOffset(0)
        self.shadow.setYOffset(2)
        self.shadow.setColor(QColor(0, 0, 0, 60))
        self.card_frame.setGraphicsEffect(self.shadow)

    def enterEvent(self, event):
        """Al pasar el mouse sobre la card"""
        self.is_hovered = True

        # Animar sombra - aumentar blur y offset
        self.shadow.setBlurRadius(20)
        self.shadow.setYOffset(6)
        self.shadow.setColor(QColor(0, 0, 0, 100))

        super().enterEvent(event)

    def leaveEvent(self, event):
        """Al quitar el mouse de la card"""
        self.is_hovered = False

        # Restaurar sombra
        self.shadow.setBlurRadius(10)
        self.shadow.setYOffset(2)
        self.shadow.setColor(QColor(0, 0, 0, 60))

        super().leaveEvent(event)

    def mousePressEvent(self, event):
        """Al hacer clic en la card"""
        if event.button() == Qt.MouseButton.LeftButton:
            # Emitir señal con el nombre original (sin truncar, sin icono)
            self.clicked.emit(self.original_name)
            logger.info(f"Card clicked - Copying to clipboard: {self.original_name}")

            # Mostrar indicador de copiado
            self.show_copy_feedback()

        super().mousePressEvent(event)

    def show_copy_feedback(self):
        """Muestra feedback visual de que se copió al portapapeles"""
        # Activar indicador
        self.show_copied_indicator = True
        self.update()  # Forzar repaint

        # Cambiar color del borde Y FONDO temporalmente
        border_color = self.TYPE_COLORS.get(self.item_type, '#555555')
        self.card_frame.setStyleSheet(f"""
            QFrame#cardFrame {{
                background-color: #1a3d2e;
                border: 3px solid #00ff88;
                border-radius: 8px;
                padding: 12px;
            }}
        """)

        # Iniciar animación de sombra
        self.shadow.setBlurRadius(25)
        self.shadow.setYOffset(8)
        self.shadow.setColor(QColor(0, 255, 136, 150))

        # Ocultar indicador después de 1 segundo
        self.copied_timer.start(1000)

    def hide_copied_indicator(self):
        """Oculta el indicador de copiado"""
        self.show_copied_indicator = False
        self.update()

        # Restaurar estilo original
        border_color = self.TYPE_COLORS.get(self.item_type, '#555555')
        self.card_frame.setStyleSheet(f"""
            QFrame#cardFrame {{
                background-color: #2d2d2d;
                border: 2px solid {border_color};
                border-radius: 8px;
                padding: 12px;
            }}
            QFrame#cardFrame:hover {{
                background-color: #353535;
                border-color: #ffffff;
            }}
        """)

        # Restaurar sombra
        self.shadow.setBlurRadius(10)
        self.shadow.setYOffset(2)
        self.shadow.setColor(QColor(0, 0, 0, 60))

    def paintEvent(self, event):
        """Dibuja el indicador de copiado si está activo"""
        super().paintEvent(event)

        if self.show_copied_indicator:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)

            # Dibujar círculo de fondo
            center_x = self.width() - 30
            center_y = 30
            radius = 20

            # Círculo verde con borde
            painter.setBrush(QColor(0, 255, 136))
            painter.setPen(QPen(QColor(0, 200, 100), 2))
            painter.drawEllipse(center_x - radius, center_y - radius, radius * 2, radius * 2)

            # Dibujar checkmark
            painter.setPen(QPen(QColor(0, 0, 0), 3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))

            # Línea 1 del check (parte corta)
            painter.drawLine(center_x - 8, center_y, center_x - 3, center_y + 6)

            # Línea 2 del check (parte larga)
            painter.drawLine(center_x - 3, center_y + 6, center_x + 8, center_y - 6)

            # Texto "Copiado!"
            painter.setPen(QColor(0, 255, 136))
            font = QFont()
            font.setPointSize(8)
            font.setBold(True)
            painter.setFont(font)
            painter.drawText(center_x - 30, center_y + 35, "Copiado!")
