from routers import base,files
from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient
from helpers.settings import get_settings
from contextlib import asynccontextmanager
from stores.llm.llm_factory import LLMFactory
from routers import vdb
from stores.vector_db.vdb_factory import VectorDBFactory



@asynccontextmanager
async def lifespan(app: FastAPI):
  settings = get_settings()
  
  # MongoDB client
  app.client = AsyncIOMotorClient(settings.MONGODB_URL)
  app.db_client = app.client[settings.MONGODB_DATABASE]

  # Vector DB client
  vdb_provider_factory = VectorDBFactory(settings)
  app.vdb_client = vdb_provider_factory.create(provider=settings.VECTOR_DB_BACKEND)
  app.vdb_client.connect()
  
  
  # Generation client
  llm_provider_factory = LLMFactory(settings)
  
  app.generation_client = llm_provider_factory.create(provider=settings.GENERATION_BACKEND)
  app.generation_client.set_generation_model(model_id = settings.GENERATION_MODEL_ID)

  # Embedding client
  app.embedding_client = llm_provider_factory.create(provider=settings.EMBEDDING_BACKEND)
  app.embedding_client.set_embedding_model(model_id=settings.EMBEDDING_MODEL_ID,
                                           embedding_size=settings.EMBEDDING_MODEL_SIZE)
  
  
  
  yield
  
  app.client.close()
  
  

app = FastAPI(lifespan=lifespan)

app.include_router(base.base_router)
app.include_router(files.files_router)
app.include_router(vdb.vdb_router)