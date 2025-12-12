"""
Utilidades de animaciones para vista completa

Proporciona animaciones suaves y efectos visuales para mejorar
la experiencia de usuario:
- Fade in/out
- Smooth expand/collapse
- Hover effects
- Transiciones suaves

Autor: Widget Sidebar Team
Versión: 1.0
"""

from PyQt6.QtCore import (
    QPropertyAnimation, QEasingCurve, QParallelAnimationGroup,
    QSequentialAnimationGroup, QTimer, QRect, QSize, pyqtProperty
)
from PyQt6.QtWidgets import QWidget, QGraphicsOpacityEffect
from PyQt6.QtGui import QColor


class AnimationManager:
    """
    Gestor centralizado de animaciones

    Proporciona métodos estáticos para crear animaciones
    comunes de forma consistente.
    """

    # Duraciones estándar (en ms)
    DURATION_FAST = 150
    DURATION_NORMAL = 250
    DURATION_SLOW = 350

    @staticmethod
    def fade_in(widget: QWidget, duration: int = None, on_finished=None):
        """
        Animar fade in de un widget

        Args:
            widget: Widget a animar
            duration: Duración en ms (default: DURATION_NORMAL)
            on_finished: Callback al finalizar
        """
        if duration is None:
            duration = AnimationManager.DURATION_NORMAL

        # Crear efecto de opacidad si no existe
        if not widget.graphicsEffect():
            effect = QGraphicsOpacityEffect(widget)
            widget.setGraphicsEffect(effect)
            effect.setOpacity(0.0)

        effect = widget.graphicsEffect()

        # Animación de opacidad
        animation = QPropertyAnimation(effect, b"opacity")
        animation.setDuration(duration)
        animation.setStartValue(0.0)
        animation.setEndValue(1.0)
        animation.setEasingCurve(QEasingCurve.Type.InOutQuad)

        if on_finished:
            animation.finished.connect(on_finished)

        animation.start()

        # Guardar referencia para que no sea garbage collected
        widget._fade_animation = animation

        return animation

    @staticmethod
    def fade_out(widget: QWidget, duration: int = None, on_finished=None):
        """
        Animar fade out de un widget

        Args:
            widget: Widget a animar
            duration: Duración en ms (default: DURATION_NORMAL)
            on_finished: Callback al finalizar
        """
        if duration is None:
            duration = AnimationManager.DURATION_NORMAL

        # Crear efecto de opacidad si no existe
        if not widget.graphicsEffect():
            effect = QGraphicsOpacityEffect(widget)
            widget.setGraphicsEffect(effect)
            effect.setOpacity(1.0)

        effect = widget.graphicsEffect()

        # Animación de opacidad
        animation = QPropertyAnimation(effect, b"opacity")
        animation.setDuration(duration)
        animation.setStartValue(1.0)
        animation.setEndValue(0.0)
        animation.setEasingCurve(QEasingCurve.Type.InOutQuad)

        if on_finished:
            animation.finished.connect(on_finished)

        animation.start()

        # Guardar referencia
        widget._fade_animation = animation

        return animation

    @staticmethod
    def smooth_collapse(widget: QWidget, duration: int = None, on_finished=None):
        """
        Colapsar widget con animación suave

        Args:
            widget: Widget a colapsar
            duration: Duración en ms (default: DURATION_NORMAL)
            on_finished: Callback al finalizar
        """
        if duration is None:
            duration = AnimationManager.DURATION_NORMAL

        # Obtener altura actual
        current_height = widget.height()

        # Animación de altura
        animation = QPropertyAnimation(widget, b"maximumHeight")
        animation.setDuration(duration)
        animation.setStartValue(current_height)
        animation.setEndValue(0)
        animation.setEasingCurve(QEasingCurve.Type.InOutCubic)

        def finish_collapse():
            widget.setVisible(False)
            widget.setMaximumHeight(16777215)  # Resetear a max
            if on_finished:
                on_finished()

        animation.finished.connect(finish_collapse)
        animation.start()

        # Guardar referencia
        widget._collapse_animation = animation

        return animation

    @staticmethod
    def smooth_expand(widget: QWidget, target_height: int = None, duration: int = None, on_finished=None):
        """
        Expandir widget con animación suave

        Args:
            widget: Widget a expandir
            target_height: Altura objetivo (None = sizeHint)
            duration: Duración en ms (default: DURATION_NORMAL)
            on_finished: Callback al finalizar
        """
        if duration is None:
            duration = AnimationManager.DURATION_NORMAL

        # Hacer visible primero
        widget.setVisible(True)

        # Obtener altura objetivo
        if target_height is None:
            widget.adjustSize()
            target_height = widget.sizeHint().height()

        # Animación de altura
        animation = QPropertyAnimation(widget, b"maximumHeight")
        animation.setDuration(duration)
        animation.setStartValue(0)
        animation.setEndValue(target_height)
        animation.setEasingCurve(QEasingCurve.Type.InOutCubic)

        def finish_expand():
            widget.setMaximumHeight(16777215)  # Resetear a max
            if on_finished:
                on_finished()

        animation.finished.connect(finish_expand)
        animation.start()

        # Guardar referencia
        widget._expand_animation = animation

        return animation

    @staticmethod
    def pulse_effect(widget: QWidget, scale: float = 1.05, duration: int = None):
        """
        Efecto de pulso (escala arriba y abajo)

        Args:
            widget: Widget a animar
            scale: Factor de escala (default: 1.05 = 5% más grande)
            duration: Duración en ms (default: DURATION_FAST)
        """
        if duration is None:
            duration = AnimationManager.DURATION_FAST

        # Crear efecto de opacidad para poder animar
        if not widget.graphicsEffect():
            effect = QGraphicsOpacityEffect(widget)
            widget.setGraphicsEffect(effect)

        effect = widget.graphicsEffect()

        # Animación de opacidad (sutil)
        opacity_up = QPropertyAnimation(effect, b"opacity")
        opacity_up.setDuration(duration)
        opacity_up.setStartValue(1.0)
        opacity_up.setEndValue(0.9)
        opacity_up.setEasingCurve(QEasingCurve.Type.OutQuad)

        opacity_down = QPropertyAnimation(effect, b"opacity")
        opacity_down.setDuration(duration)
        opacity_down.setStartValue(0.9)
        opacity_down.setEndValue(1.0)
        opacity_down.setEasingCurve(QEasingCurve.Type.InQuad)

        # Secuencia
        sequence = QSequentialAnimationGroup()
        sequence.addAnimation(opacity_up)
        sequence.addAnimation(opacity_down)

        sequence.start()

        # Guardar referencia
        widget._pulse_animation = sequence

        return sequence

    @staticmethod
    def slide_in(widget: QWidget, direction: str = "down", duration: int = None, on_finished=None):
        """
        Deslizar widget desde una dirección

        Args:
            widget: Widget a animar
            direction: "up", "down", "left", "right"
            duration: Duración en ms (default: DURATION_NORMAL)
            on_finished: Callback al finalizar
        """
        if duration is None:
            duration = AnimationManager.DURATION_NORMAL

        # Hacer visible
        widget.setVisible(True)

        # Obtener posición actual y calcular offset
        current_pos = widget.pos()

        if direction == "down":
            start_pos = current_pos - QRect(0, -20, 0, 0).topLeft()
        elif direction == "up":
            start_pos = current_pos + QRect(0, 20, 0, 0).topLeft()
        elif direction == "right":
            start_pos = current_pos - QRect(-20, 0, 0, 0).topLeft()
        else:  # left
            start_pos = current_pos + QRect(20, 0, 0, 0).topLeft()

        # Animación de posición
        animation = QPropertyAnimation(widget, b"pos")
        animation.setDuration(duration)
        animation.setStartValue(start_pos)
        animation.setEndValue(current_pos)
        animation.setEasingCurve(QEasingCurve.Type.OutCubic)

        if on_finished:
            animation.finished.connect(on_finished)

        animation.start()

        # Guardar referencia
        widget._slide_animation = animation

        return animation

    @staticmethod
    def highlight_flash(widget: QWidget, color: QColor = None, count: int = 2, duration: int = None):
        """
        Efecto de flash/highlight

        Args:
            widget: Widget a animar
            color: Color del flash (default: amarillo)
            count: Número de flashes
            duration: Duración de cada flash en ms
        """
        if duration is None:
            duration = AnimationManager.DURATION_FAST

        if color is None:
            color = QColor("#FFD700")  # Amarillo dorado

        # Guardar estilo original
        original_style = widget.styleSheet()

        flash_style = f"""
            {widget.__class__.__name__} {{
                background-color: {color.name()};
            }}
        """

        def flash_on():
            widget.setStyleSheet(original_style + flash_style)

        def flash_off():
            widget.setStyleSheet(original_style)

        # Secuencia de flashes
        for i in range(count):
            QTimer.singleShot(i * duration * 2, flash_on)
            QTimer.singleShot(i * duration * 2 + duration, flash_off)

    @staticmethod
    def smooth_scroll_to(scroll_area, target_value: int, duration: int = None):
        """
        Scroll suave a una posición

        Args:
            scroll_area: QScrollArea
            target_value: Valor objetivo del scroll
            duration: Duración en ms (default: DURATION_NORMAL)
        """
        if duration is None:
            duration = AnimationManager.DURATION_NORMAL

        scrollbar = scroll_area.verticalScrollBar()

        # Animación de valor del scrollbar
        animation = QPropertyAnimation(scrollbar, b"value")
        animation.setDuration(duration)
        animation.setStartValue(scrollbar.value())
        animation.setEndValue(target_value)
        animation.setEasingCurve(QEasingCurve.Type.InOutQuad)

        animation.start()

        # Guardar referencia
        scroll_area._scroll_animation = animation

        return animation


class AnimatedWidget(QWidget):
    """
    Widget base con soporte para animaciones

    Hereda de esta clase para tener métodos de animación
    integrados directamente.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._animations = []

    def fadeIn(self, duration: int = None, on_finished=None):
        """Fade in del widget"""
        return AnimationManager.fade_in(self, duration, on_finished)

    def fadeOut(self, duration: int = None, on_finished=None):
        """Fade out del widget"""
        return AnimationManager.fade_out(self, duration, on_finished)

    def collapse(self, duration: int = None, on_finished=None):
        """Colapsar con animación"""
        return AnimationManager.smooth_collapse(self, duration, on_finished)

    def expand(self, target_height: int = None, duration: int = None, on_finished=None):
        """Expandir con animación"""
        return AnimationManager.smooth_expand(self, target_height, duration, on_finished)

    def pulse(self, scale: float = 1.05, duration: int = None):
        """Efecto de pulso"""
        return AnimationManager.pulse_effect(self, scale, duration)

    def flash(self, color: QColor = None, count: int = 2, duration: int = None):
        """Efecto de flash"""
        return AnimationManager.highlight_flash(self, color, count, duration)


# Singleton para uso global
_animation_manager = AnimationManager()


def get_animation_manager() -> AnimationManager:
    """Obtener instancia global del animation manager"""
    return _animation_manager
