from fastapi import APIRouter,FastAPI,Depends
from helpers.config import get_settings,Settings


base_router = APIRouter()

@base_router.get("/",tags=["base"])
async def root(settings: Settings = Depends(get_settings)):
    
    app_name = settings.APP_NAME
    app_version = settings.APP_VERSION


    return {
            "message": "Welcome to MiniRAG!",
            "app_name": app_name,
            "app_version": app_version,
            }