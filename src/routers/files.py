from fastapi import FastAPI, APIRouter, Depends, UploadFile, status, Request,File
from fastapi.responses import JSONResponse
from typing import List
import logging
from repos import ChunkRepo,ProjectRepo,FileRepo
from models import ChunkModel,FileModel, ProjectModel
from helpers.config import get_settings,Settings

from controllers import FilesController

logger = logging.getLogger('uvicorn.error')

files_router = APIRouter(
    prefix="/api/files",
    tags=["api_v1", "files"],
)


@files_router.post("/upload/{project_id}")
async def upload_file(project_id: str,app_request: Request,files: List[UploadFile]= File(...)):
    return await FilesController.upload_files(app_request=app_request,project_id=project_id,files=files)
    