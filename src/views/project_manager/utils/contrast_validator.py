"""
Validador de contraste de colores WCAG

Verifica que los colores cumplan con los estándares WCAG AAA
para accesibilidad visual.

Autor: Widget Sidebar Team
Versión: 1.0
"""

from PyQt6.QtGui import QColor
from typing import Tuple


class ContrastValidator:
    """
    Validador de contraste de colores según WCAG

    Implementa los cálculos de contraste y validación
    según las pautas WCAG 2.1.
    """

    # Ratios mínimos de contraste
    WCAG_AA_NORMAL = 4.5  # Texto normal AA
    WCAG_AA_LARGE = 3.0  # Texto grande AA
    WCAG_AAA_NORMAL = 7.0  # Texto normal AAA
    WCAG_AAA_LARGE = 4.5  # Texto grande AAA

    @staticmethod
    def get_relative_luminance(color: QColor) -> float:
        """
        Calcular luminancia relativa de un color

        Según la fórmula WCAG:
        L = 0.2126 * R + 0.7152 * G + 0.0722 * B

        Args:
            color: QColor

        Returns:
            Luminancia relativa (0.0 - 1.0)
        """

        def adjust_channel(channel_value: int) -> float:
            """Ajustar valor del canal según fórmula WCAG"""
            srgb = channel_value / 255.0
            if srgb <= 0.03928:
                return srgb / 12.92
            else:
                return ((srgb + 0.055) / 1.055) ** 2.4

        r = adjust_channel(color.red())
        g = adjust_channel(color.green())
        b = adjust_channel(color.blue())

        return 0.2126 * r + 0.7152 * g + 0.0722 * b

    @staticmethod
    def calculate_contrast_ratio(color1: QColor, color2: QColor) -> float:
        """
        Calcular ratio de contraste entre dos colores

        Según la fórmula WCAG:
        (L1 + 0.05) / (L2 + 0.05)

        Donde L1 es la luminancia del color más claro y
        L2 es la luminancia del color más oscuro.

        Args:
            color1: Primer color
            color2: Segundo color

        Returns:
            Ratio de contraste (1.0 - 21.0)
        """
        lum1 = ContrastValidator.get_relative_luminance(color1)
        lum2 = ContrastValidator.get_relative_luminance(color2)

        # Asegurar que lum1 es el más claro
        if lum1 < lum2:
            lum1, lum2 = lum2, lum1

        return (lum1 + 0.05) / (lum2 + 0.05)

    @staticmethod
    def validate_contrast(
        foreground: QColor,
        background: QColor,
        is_large_text: bool = False,
        level: str = "AAA"
    ) -> Tuple[bool, float]:
        """
        Validar si el contraste cumple con WCAG

        Args:
            foreground: Color del texto
            background: Color del fondo
            is_large_text: Si es texto grande (≥18pt o ≥14pt bold)
            level: Nivel WCAG ("AA" o "AAA")

        Returns:
            Tupla (cumple: bool, ratio: float)
        """
        ratio = ContrastValidator.calculate_contrast_ratio(foreground, background)

        # Determinar ratio mínimo requerido
        if level == "AAA":
            min_ratio = (
                ContrastValidator.WCAG_AAA_LARGE
                if is_large_text
                else ContrastValidator.WCAG_AAA_NORMAL
            )
        else:  # AA
            min_ratio = (
                ContrastValidator.WCAG_AA_LARGE
                if is_large_text
                else ContrastValidator.WCAG_AA_NORMAL
            )

        return ratio >= min_ratio, ratio

    @staticmethod
    def get_contrast_grade(ratio: float) -> str:
        """
        Obtener calificación de contraste

        Args:
            ratio: Ratio de contraste

        Returns:
            Calificación ("Fail", "AA", "AA+", "AAA")
        """
        if ratio >= ContrastValidator.WCAG_AAA_NORMAL:
            return "AAA"
        elif ratio >= ContrastValidator.WCAG_AA_NORMAL:
            return "AA+"
        elif ratio >= ContrastValidator.WCAG_AA_LARGE:
            return "AA"
        else:
            return "Fail"

    @staticmethod
    def validate_color_palette(palette: dict) -> dict:
        """
        Validar paleta de colores completa

        Args:
            palette: Dict con {nombre: código_color}

        Returns:
            Dict con resultados de validación
        """
        results = {}

        # Convertir strings a QColor
        colors = {}
        for name, color_code in palette.items():
            colors[name] = QColor(color_code)

        # Validar cada combinación relevante
        # (esto debe ajustarse según la estructura de la paleta)

        return results


def validate_full_view_palette():
    """
    Validar paleta de colores de vista completa

    Verifica todos los pares de colores relevantes
    (texto sobre fondo).
    """
    from ..styles.color_palette import FullViewColorPalette

    print("\n" + "=" * 70)
    print("VALIDACIÓN DE CONTRASTE - WCAG AAA")
    print("=" * 70)
    print()

    # Pares a validar: (nombre, foreground, background, is_large)
    pairs = [
        ("Texto Principal sobre Fondo Principal",
         FullViewColorPalette.TEXT_PRIMARY,
         FullViewColorPalette.BG_MAIN,
         False),

        ("Texto Secundario sobre Fondo Principal",
         FullViewColorPalette.TEXT_SECONDARY,
         FullViewColorPalette.BG_MAIN,
         False),

        ("Título Proyecto sobre Fondo Header",
         FullViewColorPalette.TITLE_PROJECT,
         FullViewColorPalette.BG_HEADER,
         True),

        ("Título Tag sobre Fondo Header",
         FullViewColorPalette.TITLE_TAG,
         FullViewColorPalette.BG_HEADER,
         True),

        ("Título Group sobre Fondo Header",
         FullViewColorPalette.TITLE_GROUP,
         FullViewColorPalette.BG_HEADER,
         True),

        ("Texto Code sobre Fondo Item Code",
         FullViewColorPalette.TEXT_CODE,
         FullViewColorPalette.BG_ITEM_CODE,
         False),

        ("Texto URL sobre Fondo Item URL",
         FullViewColorPalette.TEXT_URL,
         FullViewColorPalette.BG_ITEM_URL,
         False),

        ("Texto Path sobre Fondo Item Path",
         FullViewColorPalette.TEXT_PATH,
         FullViewColorPalette.BG_ITEM_PATH,
         False),

        ("Accent sobre Fondo Principal",
         FullViewColorPalette.ACCENT,
         FullViewColorPalette.BG_MAIN,
         False),
    ]

    all_pass = True
    results = []

    for name, fg_code, bg_code, is_large in pairs:
        fg = QColor(fg_code)
        bg = QColor(bg_code)

        passes, ratio = ContrastValidator.validate_contrast(
            fg, bg, is_large, level="AAA"
        )

        grade = ContrastValidator.get_contrast_grade(ratio)
        status = "✓ PASS" if passes else "✗ FAIL"

        if not passes:
            all_pass = False

        results.append({
            'name': name,
            'ratio': ratio,
            'grade': grade,
            'passes': passes,
            'status': status
        })

        # Imprimir resultado
        text_type = "Texto grande" if is_large else "Texto normal"
        print(f"{status} | {name}")
        print(f"       {fg_code} sobre {bg_code}")
        print(f"       Ratio: {ratio:.2f}:1 | Grade: {grade} | {text_type}")
        print()

    print("=" * 70)
    if all_pass:
        print("✓ TODAS LAS COMBINACIONES CUMPLEN WCAG AAA")
    else:
        print("⚠ ALGUNAS COMBINACIONES NO CUMPLEN WCAG AAA")
    print("=" * 70 + "\n")

    return all_pass, results


# Test rápido
if __name__ == '__main__':
    # Test de contraste
    white = QColor("#FFFFFF")
    black = QColor("#000000")

    ratio = ContrastValidator.calculate_contrast_ratio(white, black)
    print(f"Contraste Blanco/Negro: {ratio:.2f}:1")
    print(f"Grade: {ContrastValidator.get_contrast_grade(ratio)}")

    # Validar paleta completa
    validate_full_view_palette()
