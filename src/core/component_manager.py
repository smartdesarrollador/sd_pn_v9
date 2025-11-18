"""
ComponentManager - Gestiona tipos de componentes visuales y creación de items-componente
"""
import json
import logging
from typing import List, Dict, Any, Optional
from functools import lru_cache

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.component_type import ComponentType
from models.item import Item, ItemType

logger = logging.getLogger(__name__)


class ComponentManager:
    """Manager for visual components in processes"""

    # ID de categoría especial para componentes (se crea automáticamente)
    COMPONENTS_CATEGORY_ID = None

    # Esquemas de validación para cada tipo de componente
    COMPONENT_SCHEMAS = {
        'separador': {
            'color': str,
            'thickness': int,
            'style': str  # 'solid', 'dashed', 'dotted', 'double'
        },
        'nota': {
            'background': str,
            'icon': str,
            'dismissible': bool
        },
        'alerta': {
            'type': str,  # 'info', 'warning', 'error', 'success'
            'title': str,
            'dismissible': bool
        },
        'grupo': {
            'color': str,
            'collapsible': bool,
            'expanded': bool
        }
    }

    def __init__(self, db_manager):
        """
        Initialize ComponentManager

        Args:
            db_manager: Database manager instance
        """
        self.db = db_manager
        self._cache_invalidated = True
        self._cached_types = []

        # Ensure components category exists
        self._ensure_components_category()

    @lru_cache(maxsize=128)
    def get_all_component_types(self, active_only: bool = True) -> List[ComponentType]:
        """
        Get all component types from database

        Args:
            active_only: If True, return only active component types

        Returns:
            List of ComponentType objects
        """
        try:
            rows = self.db.get_component_types(active_only=active_only)
            component_types = []

            for row in rows:
                # Deserializar default_config de JSON
                default_config = row.get('default_config', '{}')
                if isinstance(default_config, str):
                    default_config = json.loads(default_config)

                component_type = ComponentType(
                    component_id=row['id'],
                    name=row['name'],
                    description=row['description'],
                    default_config=default_config,
                    is_active=row['is_active'],
                    created_at=row.get('created_at')
                )
                component_types.append(component_type)

            return component_types

        except Exception as e:
            logger.error(f"Error getting component types: {e}")
            return []

    def get_component_type_by_name(self, name: str) -> Optional[ComponentType]:
        """
        Get a specific component type by name

        Args:
            name: Component type name (e.g., 'separador', 'nota')

        Returns:
            ComponentType object or None if not found
        """
        try:
            row = self.db.get_component_type_by_name(name)
            if not row:
                return None

            # Deserializar default_config de JSON
            default_config = row.get('default_config', '{}')
            if isinstance(default_config, str):
                default_config = json.loads(default_config)

            return ComponentType(
                component_id=row['id'],
                name=row['name'],
                description=row['description'],
                default_config=default_config,
                is_active=row['is_active'],
                created_at=row.get('created_at')
            )

        except Exception as e:
            logger.error(f"Error getting component type '{name}': {e}")
            return None

    def create_component_item(
        self,
        component_name: str,
        label: str = None,
        content: str = "",
        custom_config: Dict[str, Any] = None
    ) -> Optional[Item]:
        """
        Create an Item configured as a visual component

        Args:
            component_name: Type of component ('separador', 'nota', 'alerta', 'grupo')
            label: Label for the item (defaults to component description)
            content: Content of the component (optional, for nota/alerta)
            custom_config: Custom configuration (overrides defaults)

        Returns:
            Item object configured as component, or None if component type not found
        """
        try:
            # Obtener tipo de componente
            component_type = self.get_component_type_by_name(component_name)
            if not component_type:
                logger.error(f"Component type '{component_name}' not found")
                return None

            # Validar configuración personalizada
            if custom_config:
                if not self.validate_component_config(component_name, custom_config):
                    logger.error(f"Invalid custom config for component '{component_name}'")
                    return None
                config = component_type.merge_with_custom_config(custom_config)
            else:
                config = component_type.default_config

            # Generar label si no se provee
            if not label:
                label = f"{component_type.description}"

            # Crear item
            item = Item(
                item_id=f"component_{component_name}_{id(config)}",
                label=label,
                content=content,
                item_type=ItemType.TEXT,  # Los componentes son tipo TEXT
                is_component=True,
                name_component=component_name,
                component_config=config
            )

            return item

        except Exception as e:
            logger.error(f"Error creating component item: {e}")
            return None

    def validate_component_config(self, component_name: str, config: Dict[str, Any]) -> bool:
        """
        Validate a component configuration against its schema

        Args:
            component_name: Name of the component type
            config: Configuration dictionary to validate

        Returns:
            True if valid, False otherwise
        """
        try:
            schema = self.COMPONENT_SCHEMAS.get(component_name)
            if not schema:
                logger.warning(f"No schema defined for component '{component_name}'")
                return True  # Allow unknown component types

            # Validar que todos los campos requeridos estén presentes
            for key, expected_type in schema.items():
                if key not in config:
                    logger.error(f"Missing required field '{key}' in component config")
                    return False

                # Validar tipo de dato
                if expected_type == str:
                    if not isinstance(config[key], str):
                        logger.error(f"Field '{key}' must be string")
                        return False
                elif expected_type == int:
                    if not isinstance(config[key], int):
                        logger.error(f"Field '{key}' must be integer")
                        return False
                elif expected_type == bool:
                    if not isinstance(config[key], bool):
                        logger.error(f"Field '{key}' must be boolean")
                        return False

            # Validaciones específicas por tipo de componente
            if component_name == 'separador':
                valid_styles = ['solid', 'dashed', 'dotted', 'double']
                if config.get('style') not in valid_styles:
                    logger.error(f"Invalid separator style: {config.get('style')}")
                    return False

                if config.get('thickness', 0) < 1 or config.get('thickness', 0) > 20:
                    logger.error(f"Invalid separator thickness: {config.get('thickness')}")
                    return False

            elif component_name == 'alerta':
                valid_types = ['info', 'warning', 'error', 'success']
                if config.get('type') not in valid_types:
                    logger.error(f"Invalid alert type: {config.get('type')}")
                    return False

            return True

        except Exception as e:
            logger.error(f"Error validating component config: {e}")
            return False

    def update_component_type(
        self,
        component_type_id: int,
        name: str = None,
        description: str = None,
        default_config: Dict[str, Any] = None,
        is_active: bool = None
    ) -> bool:
        """
        Update a component type in database

        Args:
            component_type_id: ID of component type to update
            name: New name (optional)
            description: New description (optional)
            default_config: New default configuration (optional)
            is_active: New active status (optional)

        Returns:
            True if successful, False otherwise
        """
        try:
            updates = {}
            if name is not None:
                updates['name'] = name
            if description is not None:
                updates['description'] = description
            if default_config is not None:
                # Validar configuración antes de actualizar
                if name:  # Si se cambia el nombre, validar con el nuevo
                    if not self.validate_component_config(name, default_config):
                        return False
                updates['default_config'] = json.dumps(default_config)
            if is_active is not None:
                updates['is_active'] = is_active

            if not updates:
                logger.warning("No updates provided for component type")
                return False

            success = self.db.update_component_type(component_type_id, **updates)
            if success:
                # Invalidar caché
                self.get_all_component_types.cache_clear()
            return success

        except Exception as e:
            logger.error(f"Error updating component type: {e}")
            return False

    def add_component_type(
        self,
        name: str,
        description: str,
        default_config: Dict[str, Any],
        is_active: bool = True
    ) -> Optional[int]:
        """
        Add a new component type to database

        Args:
            name: Component type name
            description: Description of the component
            default_config: Default configuration dictionary
            is_active: Whether the component is active

        Returns:
            ID of created component type, or None if failed
        """
        try:
            # Validar configuración
            if not self.validate_component_config(name, default_config):
                return None

            # Serializar config a JSON
            config_json = json.dumps(default_config)

            component_id = self.db.add_component_type(
                name=name,
                description=description,
                default_config=config_json,
                is_active=is_active
            )

            if component_id:
                # Invalidar caché
                self.get_all_component_types.cache_clear()

            return component_id

        except Exception as e:
            logger.error(f"Error adding component type: {e}")
            return None

    def delete_component_type(self, component_type_id: int) -> bool:
        """
        Delete a component type from database

        Args:
            component_type_id: ID of component type to delete

        Returns:
            True if successful, False otherwise
        """
        try:
            success = self.db.delete_component_type(component_type_id)
            if success:
                # Invalidar caché
                self.get_all_component_types.cache_clear()
            return success

        except Exception as e:
            logger.error(f"Error deleting component type: {e}")
            return False

    def get_component_icon(self, component_name: str) -> str:
        """
        Get the emoji icon for a component type

        Args:
            component_name: Name of component type

        Returns:
            Emoji icon string
        """
        icons = {
            'separador': '➖',
            'nota': '📝',
            'alerta': '⚠️',
            'grupo': '📁'
        }
        return icons.get(component_name, '🔷')

    def invalidate_cache(self) -> None:
        """Invalidate the component types cache"""
        self.get_all_component_types.cache_clear()

    def _ensure_components_category(self) -> int:
        """
        Ensure a special category for components exists in the database

        Returns:
            Category ID for components
        """
        try:
            # Check if category already exists
            categories = self.db.get_categories()
            for category in categories:
                if category.get('name') == '🧩 Componentes':
                    ComponentManager.COMPONENTS_CATEGORY_ID = category.get('id')
                    logger.debug(f"Components category already exists: ID {ComponentManager.COMPONENTS_CATEGORY_ID}")
                    return ComponentManager.COMPONENTS_CATEGORY_ID

            # Create the category
            category_id = self.db.add_category(
                name='🧩 Componentes',
                icon='🧩',
                is_predefined=True  # Mark as system category
            )
            ComponentManager.COMPONENTS_CATEGORY_ID = category_id
            logger.info(f"Created components category: ID {category_id}")
            return category_id

        except Exception as e:
            logger.error(f"Error ensuring components category: {e}")
            # Fallback: return 1 (usually the first category exists)
            return 1

    def get_components_category_id(self) -> int:
        """
        Get the category ID for components

        Returns:
            Category ID
        """
        if ComponentManager.COMPONENTS_CATEGORY_ID is None:
            return self._ensure_components_category()
        return ComponentManager.COMPONENTS_CATEGORY_ID
