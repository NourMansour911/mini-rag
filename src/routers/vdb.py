from fastapi import APIRouter, UploadFile, Request,File,Depends

from typing import List
from schemas import PushRequest,PushResponse
from helpers.logger import get_logger
from services import VDBService,get_vdb_service

logger = get_logger(__name__)

vdb_router = APIRouter(
    prefix="/api/nlp",
    tags=["api_v1", "nlp"],
)



def get_db_client(request: Request):
    return request.app.db_client

@vdb_router.post("/vdb/push/{project_id}",response_model=PushResponse)
async def vdb_push(project_id: str,request_schema: PushRequest ,service: VDBService = Depends(get_files_service)):

    return await service.vdb_push(project_id=project_id,request_schema=request_schema) 
