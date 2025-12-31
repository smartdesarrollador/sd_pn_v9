"""
Modelos de datos para borradores de items del Creador Masivo

Clases:
- ItemFieldData: Datos de un campo individual de item
- ItemDraft: Modelo completo de borrador de items
"""

from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime
import uuid


@dataclass
class ItemFieldData:
    """
    Representa los datos de un campo individual de item en el borrador

    Attributes:
        content: Contenido del item (texto, URL, código, path)
        item_type: Tipo de item (TEXT, CODE, URL, PATH)
        label: Label/título del item (si vacío, se usa content)
        is_sensitive: Si el item contiene datos sensibles (será cifrado)
        is_special_mode: Si fue creado como item especial (con label separado)
    """
    content: str
    item_type: str = 'TEXT'  # Tipo por defecto
    label: str = ''  # Si vacío, label = content
    is_sensitive: bool = False
    is_special_mode: bool = False

    def get_final_label(self) -> str:
        """
        Obtiene el label final a usar (si está vacío, retorna content)

        Returns:
            Label final del item
        """
        return self.label.strip() if self.label.strip() else self.content.strip()

    def to_dict(self) -> dict:
        """
        Convierte el campo a diccionario para serialización

        Returns:
            Dict con todos los campos
        """
        return {
            'content': self.content,
            'type': self.item_type,
            'label': self.label,
            'is_sensitive': self.is_sensitive,
            'is_special_mode': self.is_special_mode
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'ItemFieldData':
        """
        Crea una instancia desde un diccionario

        Args:
            data: Dict con los campos del item

        Returns:
            ItemFieldData instance
        """
        return cls(
            content=data.get('content', ''),
            item_type=data.get('type', 'TEXT'),
            label=data.get('label', ''),
            is_sensitive=data.get('is_sensitive', False),
            is_special_mode=data.get('is_special_mode', False)
        )

    def is_empty(self) -> bool:
        """
        Verifica si el campo está vacío

        Returns:
            True si el contenido está vacío
        """
        return not self.content.strip()

    def __str__(self) -> str:
        """Representación en string"""
        label_text = self.get_final_label()
        preview = label_text[:50] + '...' if len(label_text) > 50 else label_text
        sensitive_mark = " [SENSITIVE]" if self.is_sensitive else ""
        return f"ItemField({self.item_type}): {preview}{sensitive_mark}"


@dataclass
class ItemDraft:
    """
    Modelo de borrador de items para el Creador Masivo

    Representa el estado completo de una pestaña en el creador,
    incluyendo todos los items a crear y sus propiedades compartidas.

    Attributes:
        tab_id: UUID único de la pestaña
        tab_name: Nombre editable de la pestaña
        project_id: ID del proyecto (opcional)
        area_id: ID del área (opcional)
        category_id: ID de la categoría (OBLIGATORIO para guardar)
        create_as_list: Flag para crear items como lista
        list_name: Nombre de la lista (si create_as_list=True)
        special_tag: Tag especial que se relaciona con proyecto/área
        item_tags: Tags generales de items
        project_element_tags: Tags específicos del proyecto/área
        items: Lista de campos de items
        screenshots: Lista de capturas de pantalla (filepath y label)
        created_at: Timestamp de creación
        updated_at: Timestamp de última actualización
    """
    tab_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    tab_name: str = 'Sin título'
    project_id: Optional[int] = None
    area_id: Optional[int] = None
    category_id: Optional[int] = None
    create_as_list: bool = False
    list_id: Optional[int] = None  # ID de lista existente (si se seleccionó una)
    list_name: Optional[str] = None
    special_tag: str = ''  # Tag especial relacionado con proyecto/área
    item_tags: List[str] = field(default_factory=list)
    project_element_tags: List[str] = field(default_factory=list)
    items: List[ItemFieldData] = field(default_factory=list)
    screenshots: List[dict] = field(default_factory=list)  # [{'filepath': str, 'label': str}, ...]
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        """
        Convierte el borrador a diccionario para persistencia en BD

        Returns:
            Dict con todos los campos serializados
        """
        return {
            'tab_id': self.tab_id,
            'tab_name': self.tab_name,
            'project_id': self.project_id,
            'area_id': self.area_id,
            'category_id': self.category_id,
            'create_as_list': self.create_as_list,
            'list_id': self.list_id,  # NUEVO
            'list_name': self.list_name,
            'special_tag': self.special_tag,
            'item_tags': self.item_tags,
            'project_element_tags': self.project_element_tags,
            'items': [item.to_dict() for item in self.items],
            'screenshots': self.screenshots  # Lista de dicts ya serializados
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'ItemDraft':
        """
        Crea una instancia desde diccionario de BD

        Args:
            data: Dict con campos del borrador

        Returns:
            ItemDraft instance
        """
        # Convertir items de dict a ItemFieldData
        items_data = data.get('items', [])
        items = [ItemFieldData.from_dict(item) for item in items_data]

        # Screenshots ya vienen como lista de dicts
        screenshots = data.get('screenshots', [])

        return cls(
            tab_id=data.get('tab_id', str(uuid.uuid4())),
            tab_name=data.get('tab_name', 'Sin título'),
            project_id=data.get('project_id'),
            area_id=data.get('area_id'),
            category_id=data.get('category_id'),
            create_as_list=data.get('create_as_list', False),
            list_id=data.get('list_id'),  # NUEVO
            list_name=data.get('list_name'),
            special_tag=data.get('special_tag', ''),
            item_tags=data.get('item_tags', []),
            project_element_tags=data.get('project_element_tags', []),
            items=items,
            screenshots=screenshots,
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )

    def is_valid_for_save(self) -> tuple[bool, str]:
        """
        Valida si el borrador puede guardarse como items reales

        Validaciones:
        1. Al menos un item con contenido
        2. Categoría obligatoria
        3. Nombre de lista si create_as_list está marcado

        Returns:
            Tupla (is_valid, error_message)
        """
        # Validación 1: Al menos un item con contenido
        items_with_content = [item for item in self.items if not item.is_empty()]
        if not items_with_content:
            return False, "Debe ingresar al menos un item con contenido"

        # Validación 2: Categoría obligatoria
        if not self.category_id:
            return False, "Debe seleccionar una categoría"

        # Validación 3: Nombre de lista si checkbox marcado
        if self.create_as_list and not self.list_name:
            return False, "Debe ingresar un nombre para la lista"

        # Si todo está bien
        return True, ""

    def get_items_count(self) -> int:
        """
        Retorna cantidad de items con contenido

        Returns:
            Número de items no vacíos
        """
        return sum(1 for item in self.items if not item.is_empty())

    def get_all_tags(self) -> List[str]:
        """
        Retorna todos los tags (item_tags + project_element_tags)

        Returns:
            Lista combinada de tags sin duplicados
        """
        all_tags = set(self.item_tags + self.project_element_tags)
        return list(all_tags)

    def has_project_or_area(self) -> bool:
        """
        Verifica si el borrador tiene proyecto o área asignada

        Returns:
            True si tiene proyecto_id o area_id
        """
        return self.project_id is not None or self.area_id is not None

    def add_item(self, content: str, item_type: str = 'TEXT'):
        """
        Agrega un nuevo item al borrador

        Args:
            content: Contenido del item
            item_type: Tipo de item (por defecto TEXT)
        """
        item = ItemFieldData(content=content, item_type=item_type)
        self.items.append(item)

    def remove_item(self, index: int) -> bool:
        """
        Elimina un item por índice

        Args:
            index: Índice del item a eliminar

        Returns:
            True si se eliminó correctamente
        """
        try:
            if 0 <= index < len(self.items):
                self.items.pop(index)
                return True
            return False
        except Exception:
            return False

    def clear_items(self):
        """Elimina todos los items del borrador"""
        self.items.clear()

    def get_summary(self) -> str:
        """
        Retorna un resumen del borrador

        Returns:
            String con resumen
        """
        items_count = self.get_items_count()
        category = f"Categoría: {self.category_id}" if self.category_id else "Sin categoría"
        lista = f"Lista: {self.list_name}" if self.create_as_list else "Sin lista"

        return f"{self.tab_name} - {items_count} items - {category} - {lista}"

    def __str__(self) -> str:
        """Representación en string"""
        return self.get_summary()

    def __repr__(self) -> str:
        """Representación técnica"""
        return f"ItemDraft(tab_id='{self.tab_id}', items={len(self.items)})"
