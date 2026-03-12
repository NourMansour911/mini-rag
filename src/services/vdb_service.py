from helpers.logger import get_logger  

from repos import  ProjectRepo, FileRepo, ChunkRepo
from models import  ProjectModel
from schemas import PushRequest

from fastapi import HTTPException, status,Depends

from stores import get_vdb_client,get_generation_client,get_embedding_client
from stores.llm import LLMInterface,DocumentTypeEnum
from stores.vector_db import VectorDBInterface


from models import ChunkModel,FileModel
from typing import List
from helpers.enums import Signals



from repos import  ProjectRepo, FileRepo, ChunkRepo,get_chunk_repo,get_file_repo,get_project_repo

logger = get_logger(__name__)  

class VDBService():
    
    def __init__(self,project_repo: ProjectRepo,file_repo: FileRepo,chunk_repo: ChunkRepo, vdb_client: VectorDBInterface,generation_client: LLMInterface,embedding_client: LLMInterface):
        super().__init__()
        self.project_repo = project_repo
        self.file_repo = file_repo
        self.chunk_repo = chunk_repo
        self.vdb_client = vdb_client
        self.generation_client = generation_client
        self.embedding_client = embedding_client

        logger.info("Vector DB Push Service initialized")


    async def vdb_push(self,project_id: str,request_schema: PushRequest):

        if await self.project_repo.project_exists(project_id=project_id) == False:
            raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Project [{project_id}] does not exist"
            )
        
        project = await self.project_repo.get_project_or_create_one(project_id=project_id)
        
        
        if request_schema.do_reset == 1:
            await self.chunk_repo.delete_chunks_by_project_id(project_iid=project.iid) 
        
        files_names = request_schema.files_names
        
        response_list = []
        files: List[FileModel] = []
        errors = []
        
        if files_names is None:
            try:
                files = await self.file_repo.get_all_project_files(project_iid=project.iid)
            except Exception as e:
                logger.error(f"Error fetching project files for ID {project_id}: {e}", exc_info=True)
                raise  
        else:        
                for file_name in files_names:
                    try:
                        file = await self.file_repo.get_file(file_name=file_name, project_iid=project.iid)
                        if file is None:
                            errors.append(f"File [{file_name}] does not exist")
                            continue  
                        files.append(file)
                    except Exception as e:
                        logger.error(f"Error fetching file {file_name} for project {project_id}: {e}", exc_info=True)
                        errors.append(f"File [{file_name}] error: {str(e)}")

                if errors:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=errors
                    )
                    
                    

        if len(files) == 0 and request_schema.do_reset == 0:
            logger.error("No files found for chunking")
            response_list.append({
                    "filename": None,
                    "status": "error",
                    "signal": Signals.NO_FILES_FETCHED.value
                })
            return
        
    
    
    def _index_into_vdb(self,project_id: str,chunks: list[ChunkModel],do_reset: bool = False):
        collection_name = self._create_collection_name(project_id=project_id)
        
        texts = [chunk.chunk_text for chunk in chunks]
        metadata = [chunk.chunk_metadata for chunk in chunks]
        vectors = [self.embedding_client.embed_text(text=text,document_type=DocumentTypeEnum.DOCUMENT.value) for text in texts]
        
        
        _ = self.vdb_client.create_collection(collection_name=collection_name,embedding_size=self.embedding_client.embedding_size,do_reset=do_reset)
        
        _ = self.vdb_client.insert_many(collection_name=collection_name, texts=texts, vectors=vectors, metadata=metadata)
        
        
        return True

    
    def _create_collection_name(self,project_id: str):
        return f"collection_{project_id}".strip()

    def _reset_vdb_collection(self,project_id: str):
        collection_name = self._create_collection_name(project_id=project_id)
        return self.vdb_client.delete_collection(collection_name)
    
    def _get_vdb_collection_info(self,project_id: str):
        collection_name = self._create_collection_name(project_id=project_id)
        return self.vdb_client.get_collection_info(collection_name)


        

def get_vdb_service(project_repo: ProjectRepo = Depends(get_project_repo),file_repo: FileRepo = Depends(get_file_repo),chunk_repo: ChunkRepo = Depends(get_chunk_repo),
                    vdb_client = Depends(get_vdb_client)  ,generation_client = Depends(get_generation_client,),embedding_client = Depends(get_embedding_client)):
    return VDBService(project_repo=project_repo,file_repo=file_repo,chunk_repo=chunk_repo,vdb_client=vdb_client,generation_client=generation_client,embedding_client=embedding_client)