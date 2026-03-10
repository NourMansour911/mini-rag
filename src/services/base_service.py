from helpers.settings import get_settings
from helpers.logger import get_logger
import os

logger = get_logger(__name__)

class BaseService:
    def __init__(self):
        self.settings = get_settings()
        
        self.base_dir = os.path.dirname(os.path.dirname(__file__))
        self.files_dir = os.path.join(self.base_dir,"assets/files")
    
  