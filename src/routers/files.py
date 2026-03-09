from fastapi import APIRouter, UploadFile, Request,File,Depends

from typing import List
import logging
from models.schemas import UploadResponse

from services import FilesService

logger = logging.getLogger('uvicorn.error')

files_router = APIRouter(
    prefix="/api/files",
    tags=["api_v1", "files"],
)

def get_files_service():
    return FilesService()

def get_db_client(request: Request):
    return request.app.db_client

@files_router.post("/upload/{project_id}",response_model=UploadResponse)
async def upload_files(project_id: str,files: List[UploadFile]= File(...),service: FilesService = Depends(get_files_service),db_client = Depends(get_db_client)):
    return await service.upload_files(db_client=db_client,project_id=project_id,files=files)







   