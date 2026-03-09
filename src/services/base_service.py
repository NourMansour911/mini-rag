from helpers.config import get_settings
from helpers.logger import get_logger
import os

logger = get_logger(__name__)

class BaseService:
    def __init__(self):
        self.settings = get_settings()
        
        self.base_dir = os.path.dirname(os.path.dirname(__file__))
        self.files_dir = os.path.join(self.base_dir,"assets/files")
    
    def get_project_path(self, project_id: str):
        project_dir = os.path.join(self.files_dir, project_id)
        
        if not os.path.exists(project_dir):
            os.makedirs(project_dir)
            logger.info(f"Created project directory: {project_dir}")
        else:
            logger.debug(f"Project directory exists: {project_dir}")
        
        return project_dir   