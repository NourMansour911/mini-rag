from fastapi import APIRouter, UploadFile, Request,File,Depends

from typing import List
from models.schemas import UploadResponse,FileChunkingResponse
from helpers.logger import get_logger
from models.schemas import ChunkingRequest
from services import FilesService,get_files_service



logger = get_logger(__name__)

files_router = APIRouter(
    prefix="/api/files",
    tags=["api_v1", "files"],
)



@files_router.post("/upload/{project_id}",response_model=UploadResponse)
async def upload_files(project_id: str,files: List[UploadFile]= File(...),service: FilesService = Depends(get_files_service)):
    return await service.upload_files(project_id=project_id,files=files)


@files_router.post("/chunking/{project_id}",response_model=FileChunkingResponse)
async def chunking(project_id: str,request_schema: ChunkingRequest ,service: FilesService = Depends(get_files_service)):
    
    return await service.chunking(project_id=project_id,request_schema=request_schema)




   