
import sys
import os
import logging

# Add src to path
sys.path.insert(0, os.path.join(os.getcwd(), 'src'))

from database.db_manager import DBManager
from core.global_tag_manager import GlobalTagManager

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_tag_creation():
    print("Initializing DBManager...")
    db = DBManager("test_db.sqlite")
    
    # Ensure tables exist
    db.initialize_db()
    
    print("Initializing GlobalTagManager...")
    manager = GlobalTagManager(db)
    
    tag_name = "test_tag_creation_123"
    
    print(f"Attempting to create tag: {tag_name}")
    tag = manager.create_tag(tag_name, color="#ff0000")
    
    if tag:
        print(f"SUCCESS: Tag created: {tag}")
        print(f"ID: {tag.id}, Name: {tag.name}, Color: {tag.color}")
        
        # Verify in DB
        db_tag = db.get_tag_by_id(tag.id)
        print(f"DB Verification: {db_tag}")
    else:
        print("FAILURE: Tag creation returned None")

if __name__ == "__main__":
    test_tag_creation()
