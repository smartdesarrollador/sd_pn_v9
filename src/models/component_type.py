"""
ComponentType Model - Representa un tipo de componente visual para procesos
"""
from typing import Dict, Any, Optional
from datetime import datetime


class ComponentType:
    """Model representing a visual component type"""

    def __init__(
        self,
        component_id: int,
        name: str,
        description: str,
        default_config: Dict[str, Any],
        is_active: bool = True,
        created_at: Optional[str] = None
    ):
        self.id = component_id
        self.name = name
        self.description = description
        self.default_config = default_config
        self.is_active = is_active
        self.created_at = created_at or datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convert component type to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "default_config": self.default_config,
            "is_active": self.is_active,
            "created_at": self.created_at
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ComponentType':
        """Create a ComponentType from a dictionary"""
        return cls(
            component_id=data.get("id", 0),
            name=data.get("name", ""),
            description=data.get("description", ""),
            default_config=data.get("default_config", {}),
            is_active=data.get("is_active", True),
            created_at=data.get("created_at")
        )

    def get_config_value(self, key: str, default: Any = None) -> Any:
        """
        Get a specific configuration value from default_config

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        return self.default_config.get(key, default)

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        Validate a configuration dictionary against this component type's schema

        Args:
            config: Configuration dictionary to validate

        Returns:
            True if valid, False otherwise
        """
        # Basic validation: ensure all keys in default_config are present
        for key in self.default_config.keys():
            if key not in config:
                return False

        return True

    def merge_with_custom_config(self, custom_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge default config with custom config (custom overrides default)

        Args:
            custom_config: Custom configuration values

        Returns:
            Merged configuration dictionary
        """
        merged = self.default_config.copy()
        merged.update(custom_config)
        return merged

    def __repr__(self) -> str:
        status = "active" if self.is_active else "inactive"
        return f"ComponentType(id={self.id}, name={self.name}, {status})"

    def __eq__(self, other) -> bool:
        if not isinstance(other, ComponentType):
            return False
        return self.id == other.id
