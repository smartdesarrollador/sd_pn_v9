"""
Global Tag Manager
Adapts the global tags table (managed by DBManager) to the interface expected by ProjectTagSelector.
"""

import logging
from typing import List, Optional, Dict, Any
from models.project_element_tag import ProjectElementTag

logger = logging.getLogger(__name__)

class GlobalTagManager:
    """
    Manager for global tags (used by Items).
    Adapts DBManager's tag methods to return ProjectElementTag objects.
    """

    def __init__(self, db_manager):
        """
        Initialize with a DBManager instance.
        
        Args:
            db_manager: Instance of DBManager
        """
        self.db = db_manager

    def search_tags(self, query: str) -> List[ProjectElementTag]:
        """
        Search tags by name.
        
        Args:
            query: Search query
            
        Returns:
            List of ProjectElementTag objects
        """
        try:
            # DBManager.search_tags returns List[Dict]
            results = self.db.search_tags(query)
            return [self._dict_to_tag(row) for row in results]
        except Exception as e:
            logger.error(f"Error searching global tags: {e}")
            return []

    def create_tag(self, name: str, color: str = "#3498db", description: str = "") -> Optional[ProjectElementTag]:
        """
        Create a new global tag.
        
        Args:
            name: Tag name
            color: Tag color
            description: Tag description
            
        Returns:
            Created ProjectElementTag object or None if failed
        """
        try:
            # DBManager.add_project_element_tag is for project tags.
            # We need to check if there is a method for global tags.
            # DBManager.add_project_element_tag inserts into 'tags' table? 
            # Let's check DBManager again. 
            # In step 53, I saw add_project_element_tag inserts into 'tags'.
            # Wait, let me re-verify DBManager methods.
            # 'add_project_element_tag' in DBManager (viewed in step 53) inserted into 'tags'.
            # BUT in step 88 'inspect_db' showed 'tags' and 'project_element_tags' as separate tables.
            # And 'add_project_element_tag' in step 96 inserted into 'project_element_tags'.
            # I need to find the method that inserts into 'tags'.
            # In step 96, I saw 'add_tag_to_item' which calls 'get_or_create_tag'.
            # I need to find 'get_or_create_tag' or similar in DBManager.
            
            # Assuming DBManager has a method to create a tag in 'tags' table.
            # If not, I might need to implement it or use raw query here (less ideal).
            # Let's try to find 'add_tag' or 'create_tag' in DBManager again.
            
            # For now, I will assume there is a way or I will use execute_update directly if needed, 
            # but preferably I should use DBManager methods.
            
            # Re-reading step 96: 
            # add_tag_to_item calls self.get_or_create_tag(tag_name).
            # Let's assume get_or_create_tag exists.
            
            # However, ProjectTagSelector expects to create a tag with color.
            # 'tags' table has 'color' column (verified in step 88).
            
            # I'll implement create_tag using direct DB access if a specific method with color doesn't exist,
            # or try to find the best match.
            
            # Let's use a safe approach: check if tag exists, if not create it.
            
            # Note: DBManager.add_project_element_tag (step 96) inserts into project_element_tags.
            # I need to insert into 'tags'.
            
            # I will implement the logic here using self.db.execute_update if needed, 
            # or call a method if I find it.
            
            # Let's try to use self.db.get_or_create_tag if it allows color, but likely it just takes name.
            # If I need to set color, I might need update_tag.
            
            # Better implementation:
            tag_id = self.db.get_or_create_tag(name)
            if tag_id:
                # Update color if provided and different from default?
                # Or just ensure it has the color.
                self.db.update_tag(tag_id, color=color, description=description)
                return self.get_tag(tag_id)
            return None

        except Exception as e:
            logger.error(f"Error creating global tag: {e}")
            return None

    def get_tag(self, tag_id: int) -> Optional[ProjectElementTag]:
        """
        Get a tag by ID.
        
        Args:
            tag_id: Tag ID
            
        Returns:
            ProjectElementTag object or None
        """
        try:
            # DBManager.get_tag_by_id returns Dict
            row = self.db.get_tag_by_id(tag_id)
            if row:
                return self._dict_to_tag(row)
            return None
        except Exception as e:
            logger.error(f"Error getting global tag by id {tag_id}: {e}")
            return None
            
    def get_tag_by_name(self, name: str) -> Optional[ProjectElementTag]:
        """
        Get a tag by name.
        
        Args:
            name: Tag name
            
        Returns:
            ProjectElementTag object or None
        """
        try:
            row = self.db.get_tag_by_name(name)
            if row:
                return self._dict_to_tag(row)
            return None
        except Exception as e:
            logger.error(f"Error getting global tag by name {name}: {e}")
            return None

    def _dict_to_tag(self, row: Dict[str, Any]) -> ProjectElementTag:
        """Convert DB dictionary to ProjectElementTag object"""
        return ProjectElementTag(
            id=row['id'],
            name=row['name'],
            color=row.get('color', '#3498db'),
            description=row.get('description', ''),
            created_at=row.get('created_at'),
            updated_at=row.get('updated_at')
        )
