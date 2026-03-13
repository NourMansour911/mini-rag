from fastapi import APIRouter, UploadFile, Request,File,Depends

from typing import List
from schemas import PushRequest,PushResponse,SearchRequest
from helpers.logger import get_logger
from services import VDBService,get_vdb_service,get_vdb_service_only,get_vdb_service_light

logger = get_logger(__name__)

vdb_router = APIRouter(
    prefix="/api/vdb",
    tags=["api_v1", "vdb"],
)



@vdb_router.post("/push/{project_id}",response_model=PushResponse)
async def vdb_push(project_id: str,request_schema: PushRequest ,service: VDBService = Depends(get_vdb_service)):

    return await service.vdb_push(project_id=project_id,request_schema=request_schema) 

@vdb_router.get("/info/{project_id}")
async def vdb_info(project_id: str,service: VDBService = Depends(get_vdb_service_only)):

    return service.vdb_info(project_id=project_id) 

@vdb_router.post("/search/{project_id}")
async def vdb_push(project_id: str,request_schema: SearchRequest ,service: VDBService = Depends(get_vdb_service_light)):

    return await service.vdb_search(project_id=project_id,request_schema=request_schema) 
