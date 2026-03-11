from helpers.logger import get_logger  

from repos import  ProjectRepo, FileRepo, ChunkRepo
from models import  ProjectModel
from schemas import PushRequest

from fastapi import HTTPException, status,Depends


from repos import  ProjectRepo, FileRepo, ChunkRepo,get_chunk_repo,get_file_repo,get_project_repo

logger = get_logger(__name__)  

class VDBService():
    
    def __init__(self,project_repo: ProjectRepo,file_repo: FileRepo,chunk_repo: ChunkRepo, vdb_client,generation_client,embedding_client):
        super().__init__()
        self.project_repo = project_repo
        self.file_repo = file_repo
        self.chunk_repo = chunk_repo
        self.vdb_client = vdb_client
        self.generation_client = generation_client
        self.embedding_client = embedding_client
        self.collection_name = None

        logger.info("NLP Push Service initialized")


    async def vdb_push(self,project_id: str,request_schema: PushRequest):
        self.collection_name = f"collection_{project_id}".strip()
        
        if await self.project_repo.project_exists(project_id=self.project_id) == False:
            raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Project [{self.project_id}] does not exist"
            )
        
        project = await self.project_repo.get_project_or_create_one(project_id=self.project_id)
    
    
    def _reset_vdb_collection(self):
        return self.vdb_client.delete_collection(self.collection_name)
    
    def _get_vdb_collection_info(self):
        return self.vdb_client.get_collection_info(self.collection_name)

             
def get_vdb_service(project_repo: ProjectRepo = Depends(get_project_repo),file_repo: FileRepo = Depends(get_file_repo),chunk_repo: ChunkRepo = Depends(get_chunk_repo)):
    return VDBService(project_repo=project_repo,file_repo=file_repo,chunk_repo=chunk_repo)