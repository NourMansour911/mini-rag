from fastapi import APIRouter, UploadFile, Request,File,Depends

from typing import List
from schemas import PushRequest,ChunkingRequest
from helpers.logger import get_logger
from services import VDBService

logger = get_logger(__name__)

vdb_router = APIRouter(
    prefix="/api/nlp",
    tags=["api_v1", "nlp"],
)



def get_db_client(request: Request):
    return request.app.db_client

@vdb_router.post("/vdb/push/{project_id}")
async def vdb_push(app_request: Request,project_id: str,request_schema: PushRequest ,db_client = Depends(get_db_client)):
    service = VDBService(project_id=project_id,request_schema=request_schema,db_client=db_client)
    return await service.vdb_push() 