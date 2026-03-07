from fastapi import FastAPI, APIRouter, Depends, UploadFile, status, Request,File
from fastapi.responses import JSONResponse
from typing import List
import logging
from repos import ChunkRepo,ProjectRepo,FileRepo
from models import ChunkModel,FileModel, ProjectModel


logger = logging.getLogger('uvicorn.error')

data_router = APIRouter(
    prefix="/api/files",
    tags=["api_v1", "files"],
)


@data_router.post("/upload/{project_id}")
async def upload_file(project_id: str,app_request: Request,files: List[UploadFile]= File(...)):
    pass
    