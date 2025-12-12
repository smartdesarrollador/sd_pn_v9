"""
Constantes de espaciado y márgenes refinadas

Define espaciados consistentes para toda la vista completa,
siguiendo principios de diseño de 8px grid system.

Autor: Widget Sidebar Team
Versión: 1.0
"""


class Spacing:
    """
    Sistema de espaciado basado en grid de 8px

    Proporciona constantes para márgenes, padding y spacing
    consistentes en toda la aplicación.
    """

    # === UNIDAD BASE ===
    UNIT = 8  # 8px base unit

    # === ESPACIADOS PEQUEÑOS ===
    TINY = UNIT // 2  # 4px
    SMALL = UNIT  # 8px
    MEDIUM = UNIT * 2  # 16px

    # === ESPACIADOS GRANDES ===
    LARGE = UNIT * 3  # 24px
    XLARGE = UNIT * 4  # 32px
    XXLARGE = UNIT * 6  # 48px

    # === MÁRGENES DE PANEL ===
    PANEL_MARGIN = 0  # Sin margen en panel principal (full bleed)
    CONTENT_PADDING = MEDIUM  # 16px padding interno

    # === ESPACIADOS DE HEADERS ===
    HEADER_PADDING_VERTICAL = MEDIUM  # 16px arriba/abajo
    HEADER_PADDING_HORIZONTAL = LARGE  # 24px izquierda/derecha
    HEADER_SPACING = SMALL  # 8px entre headers

    # === ESPACIADOS DE ITEMS ===
    ITEM_PADDING_VERTICAL = MEDIUM  # 16px arriba/abajo
    ITEM_PADDING_HORIZONTAL = MEDIUM  # 16px izquierda/derecha
    ITEM_SPACING = SMALL  # 8px entre items
    ITEM_MARGIN_LEFT = XXLARGE + MEDIUM  # 56px margen izq (indentación)

    # === ESPACIADOS DE GRUPOS ===
    GROUP_SPACING = MEDIUM  # 16px entre grupos
    GROUP_MARGIN_LEFT = LARGE  # 24px margen izq

    # === ESPACIADOS DE TAGS ===
    TAG_SPACING = MEDIUM  # 16px entre tags de proyecto
    TAG_PADDING = MEDIUM  # 16px padding interno

    # === BOTONES ===
    BUTTON_PADDING_VERTICAL = SMALL  # 8px arriba/abajo
    BUTTON_PADDING_HORIZONTAL = MEDIUM  # 16px izquierda/derecha
    BUTTON_SPACING = SMALL  # 8px entre botones

    # === ICONOS ===
    ICON_MARGIN_RIGHT = SMALL  # 8px después de icono
    ICON_SIZE = LARGE  # 24px tamaño de icono

    # === BORDER RADIUS ===
    RADIUS_SMALL = 4  # 4px para elementos pequeños
    RADIUS_MEDIUM = 6  # 6px para elementos medianos
    RADIUS_LARGE = 8  # 8px para elementos grandes

    # === ANCHOS ESPECÍFICOS ===
    SCROLLBAR_WIDTH = SMALL  # 8px ancho del scrollbar


class FontSizes:
    """
    Tamaños de fuente consistentes

    Define la jerarquía tipográfica para la vista completa.
    """

    # === JERARQUÍA DE TÍTULOS ===
    TITLE_PROJECT = 24  # Título principal del proyecto
    TITLE_TAG = 18  # Título de tag de proyecto
    TITLE_GROUP = 14  # Título de grupo

    # === TEXTO DE CONTENIDO ===
    TEXT_NORMAL = 13  # Texto normal de items
    TEXT_SMALL = 12  # Texto secundario/metadatos
    TEXT_TINY = 11  # Texto muy pequeño (tooltips, etc.)

    # === TEXTO DE CÓDIGO ===
    CODE_NORMAL = 13  # Código normal
    CODE_SMALL = 12  # Código en inline

    # === BOTONES ===
    BUTTON_NORMAL = 12  # Texto de botones
    BUTTON_SMALL = 11  # Texto de botones pequeños


class LineHeights:
    """
    Alturas de línea para mejor legibilidad

    Define line-heights apropiados según el tamaño de fuente.
    """

    # === MULTIPLICADORES ===
    TIGHT = 1.2  # Para títulos
    NORMAL = 1.5  # Para texto normal
    LOOSE = 1.8  # Para párrafos largos

    # === VALORES ESPECÍFICOS ===
    TITLE_PROJECT = FontSizes.TITLE_PROJECT * TIGHT  # ~29px
    TITLE_TAG = FontSizes.TITLE_TAG * TIGHT  # ~22px
    TITLE_GROUP = FontSizes.TITLE_GROUP * TIGHT  # ~17px

    TEXT_NORMAL = FontSizes.TEXT_NORMAL * NORMAL  # ~20px
    TEXT_PARAGRAPH = FontSizes.TEXT_NORMAL * LOOSE  # ~23px


class Transitions:
    """
    Duraciones de transiciones y animaciones

    Define tiempos consistentes para animaciones.
    """

    # === DURACIONES (en ms) ===
    INSTANT = 0  # Sin animación
    FAST = 150  # Animaciones rápidas (hover, etc.)
    NORMAL = 250  # Animaciones normales
    SLOW = 350  # Animaciones lentas (colapso/expansión)

    # === EASING ===
    # Usar QEasingCurve en código PyQt6
    EASE_IN_OUT = "ease-in-out"  # Para CSS
    EASE_OUT = "ease-out"  # Para CSS
    EASE_IN = "ease-in"  # Para CSS


class Shadows:
    """
    Sombras para dar profundidad

    Define box-shadows consistentes para elementos.
    """

    # === SOMBRAS SUTILES ===
    SUBTLE = "0 1px 3px rgba(0, 0, 0, 0.3)"
    NORMAL = "0 2px 6px rgba(0, 0, 0, 0.4)"
    STRONG = "0 4px 12px rgba(0, 0, 0, 0.5)"

    # === SOMBRAS DE HOVER ===
    HOVER = "0 3px 8px rgba(0, 0, 0, 0.45)"


class ZIndex:
    """
    Niveles Z para stacking context

    Define el orden de apilamiento de elementos.
    """

    BASE = 0  # Nivel base
    ITEM = 1  # Items normales
    HEADER = 10  # Headers de secciones
    STICKY = 100  # Elementos sticky
    OVERLAY = 1000  # Overlays y modales
    TOOLTIP = 2000  # Tooltips


def get_spacing_css() -> str:
    """
    Obtener variables CSS de espaciado

    Returns:
        String con variables CSS
    """
    return f"""
        :root {{
            --spacing-tiny: {Spacing.TINY}px;
            --spacing-small: {Spacing.SMALL}px;
            --spacing-medium: {Spacing.MEDIUM}px;
            --spacing-large: {Spacing.LARGE}px;
            --spacing-xlarge: {Spacing.XLARGE}px;
            --spacing-xxlarge: {Spacing.XXLARGE}px;

            --font-size-title-project: {FontSizes.TITLE_PROJECT}px;
            --font-size-title-tag: {FontSizes.TITLE_TAG}px;
            --font-size-title-group: {FontSizes.TITLE_GROUP}px;
            --font-size-text: {FontSizes.TEXT_NORMAL}px;

            --radius-small: {Spacing.RADIUS_SMALL}px;
            --radius-medium: {Spacing.RADIUS_MEDIUM}px;
            --radius-large: {Spacing.RADIUS_LARGE}px;

            --transition-fast: {Transitions.FAST}ms;
            --transition-normal: {Transitions.NORMAL}ms;
            --transition-slow: {Transitions.SLOW}ms;
        }}
    """


# Test de valores
if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("SISTEMA DE ESPACIADO - 8PX GRID")
    print("=" * 70)
    print()

    print("Espaciados:")
    print(f"  TINY:    {Spacing.TINY}px")
    print(f"  SMALL:   {Spacing.SMALL}px")
    print(f"  MEDIUM:  {Spacing.MEDIUM}px")
    print(f"  LARGE:   {Spacing.LARGE}px")
    print(f"  XLARGE:  {Spacing.XLARGE}px")
    print(f"  XXLARGE: {Spacing.XXLARGE}px")
    print()

    print("Tamaños de Fuente:")
    print(f"  Título Proyecto: {FontSizes.TITLE_PROJECT}px")
    print(f"  Título Tag:      {FontSizes.TITLE_TAG}px")
    print(f"  Título Group:    {FontSizes.TITLE_GROUP}px")
    print(f"  Texto Normal:    {FontSizes.TEXT_NORMAL}px")
    print()

    print("Line Heights:")
    print(f"  Título Proyecto: {LineHeights.TITLE_PROJECT:.1f}px")
    print(f"  Texto Normal:    {LineHeights.TEXT_NORMAL:.1f}px")
    print(f"  Párrafo:         {LineHeights.TEXT_PARAGRAPH:.1f}px")
    print()

    print("Transiciones:")
    print(f"  FAST:   {Transitions.FAST}ms")
    print(f"  NORMAL: {Transitions.NORMAL}ms")
    print(f"  SLOW:   {Transitions.SLOW}ms")
    print()

    print("=" * 70 + "\n")
