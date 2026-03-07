from routers import base,files
from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient
from helpers.config import get_settings
from contextlib import asynccontextmanager



@asynccontextmanager
async def lifespan(app: FastAPI):
  settings = get_settings()
  app.client = AsyncIOMotorClient(settings.MONGODB_URL)
  app.db_client = app.client[settings.MONGODB_DATABASE]
  
  yield
  
  app.client.close()
  
  

app = FastAPI(lifespan=lifespan)


app.include_router(base.base_router)
app.include_router(files.files_router)