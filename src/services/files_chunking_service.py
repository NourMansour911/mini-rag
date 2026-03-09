from .base_service import BaseService
from helpers.config import get_settings
from helpers.enums import Signals
from helpers.logger import get_logger  
from repos import  ProjectRepo, FileRepo, ChunkRepo
from typing import List
from models.schemas import ChunkingRequest
from models import  ChunkModel,FileModel

from fastapi import HTTPException, status

import os

from langchain_community.document_loaders import PyPDFLoader,TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = get_logger(__name__)  

class FilesChunkingService(BaseService):
    
    def __init__(self,project_id: str):
        super().__init__()
        self.settings = get_settings()
        self.project_path = self.get_project_path(project_id=project_id)
        logger.info("File Chunking Service initialized")


    async def chunking(self,project_id: str,db_client,request_schema: ChunkingRequest):
        project_repo = await ProjectRepo.create_instance(db_client=db_client)
        file_repo = await FileRepo.create_instance(db_client=db_client)
        chunk_repo = await ChunkRepo.create_instance(db_client=db_client)
        
        if await project_repo.project_exists(project_id=project_id) == False:
            raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Project [{project_id}] does not exist"
            )
        
        project = await project_repo.get_project_or_create_one(project_id=project_id)
        
        
        if request_schema.do_reset == 1:
            await chunk_repo.delete_chunks_by_project_id(project_iid=project.iid) 
        
        files_names = request_schema.files_names
        
        response_list = []
        files: List[FileModel] = []
        errors = []
        
        if files_names is None:
            try:
                files = await file_repo.get_all_project_files(project_iid=project.iid)
            except Exception as e:
                logger.error(f"Error fetching project files for ID {project_id}: {e}", exc_info=True)
                raise  
        else:        
                for file_name in files_names:
                    try:
                        file = await file_repo.get_file(file_name=file_name, project_iid=project.iid)
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
         
        no_of_files = 0
        no_of_inserted_chunks = 0

        for file in files:
            
            try:

               file_chunks = self._create_chunks(file_name=file.file_name,chunk_size=request_schema.chunk_size,chunk_overlap=request_schema.chunk_overlap)
               
               file_chunks_records = [
               ChunkModel(
                chunk_project_iid=file.file_project_iid,
                chunk_file_iid=file.file_iid,
                chunk_file_name=file.file_name,
                chunk_order=i+1,
                chunk_id=chunk.id,
                chunk_metadata=chunk.metadata,
                chunk_text=chunk.page_content,
                chunk_type=chunk.type,
                )
               for i,chunk in enumerate(file_chunks)]
               no_of_inserted_chunks += await chunk_repo.insert_many_chunks(chunks=file_chunks_records)
               no_of_files += 1
                
               
               logger.info(f"File {file.file_name} chunked successfully")
               response_list.append({
                   "file_name": file.file_name,
                   "status": "success",
                   "signal": Signals.CHUNKING_SUCCESS.value
               })
            except Exception as e:
                logger.error(f"Error chunking file {file.file_name}: {e}", exc_info=True)
                response_list.append({
                    "filename": file.file_name,
                    "status": "error",
                    "signal": Signals.CHUNKING_FAILED.value
                })
        
        return {
            "project_db_id": str(project.iid),
            "no_of_files": no_of_files,
            "no_of_inserted_chunks": no_of_inserted_chunks,
            "files": response_list
        }




    def _create_chunks(self,file_name: str,chunk_size: int,chunk_overlap: int):
        
        if not file_name:
            return False, Signals.FILE_NOT_FOUND.value
        
        file_content = self._load_file_content(file_name=file_name)
    
        file_chunks = self._process_file_content(
        content=file_content,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap)
        
        if file_chunks is None :
          return False, Signals.PROCESS_FAILED.value
  
        
        
        return file_chunks
    


    
    def _get_file_extension(self, file_name: str) -> str:
        file_ext = os.path.splitext(file_name)[-1]
        
        return file_ext
    
    def _get_file_loader(self,file_name:str):
        file_ext = self._get_file_extension(file_name=file_name)
        file_path = os.path.join(
            self.project_path,
            file_name
        )
        if file_ext == ".pdf":
            return PyPDFLoader(file_path)
        
        if file_ext == ".txt":
            return TextLoader(file_path,encoding="utf-8")
        
        return None

    def _load_file_content(self,file_name:str):
        file_loader = self._get_file_loader(file_name=file_name)
        content = file_loader.load()
        return content
    
    def _process_file_content(self ,content:list,chunk_size: int,chunk_overlap: int):
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size,chunk_overlap=chunk_overlap,length_function=len)
        
        
        chunks = text_splitter.split_documents(content)
        
        return chunks
