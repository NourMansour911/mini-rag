from fastapi import APIRouter, UploadFile, Request,File,Depends

from typing import List
import logging
from models.schemas import UploadResponse

from services import FilesUploadService,FilesChunkingService
from models.schemas import ChunkingRequest



logger = logging.getLogger('uvicorn.error')

files_router = APIRouter(
    prefix="/api/files",
    tags=["api_v1", "files"],
)


def get_db_client(request: Request):
    return request.app.db_client

@files_router.post("/upload/{project_id}",response_model=UploadResponse)
async def upload_files(project_id: str,files: List[UploadFile]= File(...),db_client = Depends(get_db_client)):
    service = FilesUploadService()
    return await service.upload_files(db_client=db_client,project_id=project_id,files=files)


@files_router.post("/chunking/{project_id}")
async def chunking(project_id: str,request_schema: ChunkingRequest ,db_client = Depends(get_db_client)):
    service = FilesChunkingService(project_id=project_id)
    return await service.chunking(db_client=db_client,project_id=project_id,request_schema=request_schema)




   