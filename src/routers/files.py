from fastapi import APIRouter, UploadFile, Request,File

from typing import List
import logging
from models.schemas import UploadResponse

from services import FilesService

logger = logging.getLogger('uvicorn.error')

files_router = APIRouter(
    prefix="/api/files",
    tags=["api_v1", "files"],
)

service = FilesService()

@files_router.post("/upload/{project_id}",response_model=UploadResponse)
async def upload_files(project_id: str,app_request: Request,files: List[UploadFile]= File(...)):
    return await service.upload_files(db_client=app_request.app.db_client,project_id=project_id,files=files)




   