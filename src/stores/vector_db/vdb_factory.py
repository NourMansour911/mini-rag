from .providers import QdrantDBProvider
from helpers import get_database_path,Settings,get_logger

logger = get_logger(__name__)




class VectorDBFactory:
    def __init__(self,settings: Settings):
        self.settings = settings
    
    def create(self, provider: str):
        if provider == "QDRANT":
            db_path = get_database_path(self.settings.VECTOR_DB_PATH)
            return QdrantDBProvider(
                db_path=db_path,
                distance_method=self.settings.VECTOR_DB_DISTANCE_METHOD,
            )
        
        return None
