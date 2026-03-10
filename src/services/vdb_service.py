from .base_service import BaseService
from helpers.logger import get_logger  

from repos import  ProjectRepo, FileRepo, ChunkRepo
from models import  ProjectModel
from models.schemas import PushRequest

from fastapi import HTTPException, status

import os

from langchain_community.document_loaders import PyPDFLoader,TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = get_logger(__name__)  

class VDBService(BaseService):
    
    def __init__(self,project_id: str,request_schema: PushRequest,db_client,vdb_client,generation_client,embedding_client):
        super().__init__()
        self.project_id = project_id
        self.request_schema = request_schema
        self.db_client = db_client
        self.vdb_client = vdb_client
        self.generation_client = generation_client
        self.embedding_client = embedding_client
        self.collection_name = f"collection_{self.project_id}".strip()
        logger.info("NLP Push Service initialized")

    async def vdb_push(self):
        project_repo = await ProjectRepo.create_instance(db_client=self.db_client)
        file_repo = await FileRepo.create_instance(db_client=self.db_client)
        chunk_repo = await ChunkRepo.create_instance(db_client=self.db_client)
        
        if await project_repo.project_exists(project_id=self.project_id) == False:
            raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Project [{self.project_id}] does not exist"
            )
        
        project = await project_repo.get_project_or_create_one(project_id=self.project_id)
    
    
    def _reset_vdb_collection(self):
        return self.vdb_client.delete_collection(self.collection_name)
    
    def _get_vdb_collection_info(self):
        return self.vdb_client.get_collection_info(self.collection_name)

             
