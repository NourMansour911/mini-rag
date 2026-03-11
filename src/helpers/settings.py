from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    
    APP_NAME: str
    APP_VERSION: str 
    GITHUB_TOKEN: str
    OPENROUTER_API_KEY: str
    
    FILE_MAX_SIZE: int
    FILE_ALLOWED_EXT:list
    FILE_DEFAULT_CHUNK_SIZE: int
    FILE_SCALE_VALUE: int
    
    MONGODB_URL:str
    MONGODB_DATABASE:str
    
    GENERATION_BACKEND: str
    EMBEDDING_BACKEND: str

    OPENAI_API_KEY: str = None
    OPENAI_API_URL: str = None
    COHERE_API_KEY: str = None
    
    GENERATION_MODEL_ID: str = None
    EMBEDDING_MODEL_ID: str = None
    EMBEDDING_MODEL_SIZE: int = None

    VECTOR_DB_BACKEND : str
    VECTOR_DB_PATH : str
    VECTOR_DB_DISTANCE_METHOD: str = None

    class Config:
        env_file = ".env"
        
        
def get_settings():
    return Settings()