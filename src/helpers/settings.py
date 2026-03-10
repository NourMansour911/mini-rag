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
    class Config:
        env_file = ".env"
        
        
def get_settings():
    return Settings()