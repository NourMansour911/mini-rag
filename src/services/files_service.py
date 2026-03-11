from helpers.enums import Signals
from helpers.logger import get_logger  
from helpers.settings import get_settings
from helpers.disk_helper import get_project_path,generate_file_path
import os

from repos import  ProjectRepo, FileRepo, ChunkRepo,get_chunk_repo,get_file_repo,get_project_repo
from models import  ChunkModel,FileModel
from typing import List

from schemas import ChunkingRequest

from fastapi import HTTPException, status, UploadFile,Depends

import aiofiles

from langchain_community.document_loaders import PyPDFLoader,TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = get_logger(__name__)  



class FilesService():
    def __init__(self,project_repo: ProjectRepo,file_repo: FileRepo,chunk_repo: ChunkRepo):
        super().__init__()
        self.project_repo = project_repo
        self.file_repo = file_repo
        self.chunk_repo = chunk_repo
        self.settings = get_settings()

    async def upload_files(
        self,
        project_id: str,
        files: List[UploadFile]
    ):


        project = await self.project_repo.get_project_or_create_one(project_id=project_id)

        logger.info(
            f"Using project: {project.project_id} (DB ID: {str(project.iid)})"
        )

        response_list = []

        for file in files:

            is_valid, signal = self._validate_file(file=file)

            if not is_valid:
                logger.warning(
                    f"File validation failed: {file.filename} | Signal: {signal}"
                )

                response_list.append({
                    "filename": file.filename,
                    "status": "error",
                    "signal": signal
                })

                continue

            try:

                _, file_name = await self._disk_write_file(
                    file=file,
                    project_id=project.project_id
                )

                file_model = FileModel(
                    file_name=file_name,
                    file_size=file.size,
                    file_project_iid=project.iid
                )

                saved_file = await self.file_repo.add_file(file_model)

                logger.info(
                    f"File saved successfully: {file.filename} as {file_name} | "
                    f"File ID: {str(saved_file.file_iid)}"
                )

                response_list.append({
                    "filename": file.filename,
                    "status": "success",
                    "database_filename": file_name,
                    "file_db_id": str(saved_file.file_iid),
                    "signal": signal
                })

            except Exception as e:

                logger.error(
                    f"Error saving file {file.filename}: {e}",
                    exc_info=True
                )

                response_list.append({
                    "filename": file.filename,
                    "status": "error",
                    "signal": str(e)
                })

        logger.info(
            f"Files uploaded successfully for project: {project.project_id} "
            f"(DB ID: {str(project.iid)})"
        )

        return {
            "project_db_id": str(project.iid),
            "files": response_list
        }   
    async def chunking(self,request_schema: ChunkingRequest,project_id: str):
        

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
         
        no_of_files = 0
        no_of_inserted_chunks = 0

        for file in files:
            
            try:

               file_chunks = self._create_chunks(file_name=file.file_name,chunk_size=request_schema.chunk_size,chunk_overlap=request_schema.chunk_overlap,project_id=project_id)
               
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
               no_of_inserted_chunks += await self.chunk_repo.insert_many_chunks(chunks=file_chunks_records)
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

    def _validate_file(self, file: UploadFile):
        logger.debug(f"Validating file: {file.filename if file else 'None'}")

        if file is None or file.filename == "":
            logger.error("File not found or empty")
            return False, Signals.FILE_NOT_FOUND.value

        if file.size > self.settings.FILE_MAX_SIZE * self.settings.FILE_SCALE_VALUE:
            logger.error(f"File size exceeded: {file.size} bytes")
            return False, Signals.FILE_SIZE_EXCEEDED.value

        if file.content_type not in self.settings.FILE_ALLOWED_EXT:
            logger.error(f"File type not allowed: {file.content_type}")
            return False, Signals.FILE_TYPE_NOT_ALLOWED.value   

        logger.info(f"File validated successfully: {file.filename}")
        return True, Signals.FILE_VALID.value
    
    async def _disk_write_file(self, file: UploadFile, project_id: str):
        file_path, file_name = generate_file_path(original_filename=file.filename, project_id=project_id)
        logger.info(f"Writing file to path: {file_path}")

        try:
            async with aiofiles.open(file_path, 'wb') as f:
                while chunk := await file.read(self.settings.FILE_DEFAULT_CHUNK_SIZE):
                    await f.write(chunk)
            logger.info(f"File written successfully: {file.filename} -> {file_path}")
        except Exception as e:
            logger.error(f"Error writing file {file.filename}: {e}", exc_info=True)
            raise
        
        return file_path, file_name

  
    def _create_chunks(self,project_id: str,file_name: str,chunk_size: int,chunk_overlap: int):
        
        if not file_name:
            return False, Signals.FILE_NOT_FOUND.value
        
        file_loader = self.get_file_loader(project_id=project_id,file_name=file_name)
        file_content = file_loader.load()
    
        file_chunks = self.process_file_content(
        content=file_content,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap)
        
        if file_chunks is None :
          return False, Signals.PROCESS_FAILED.value
  
        
        
        return file_chunks
    
    def get_file_loader(project_id: str,file_name:str):
        file_ext = os.path.splitext(file_name)[-1]
        file_path = os.path.join(
            get_project_path(project_id=project_id),
            file_name
        )
        if file_ext == ".pdf":
            return PyPDFLoader(file_path)
        
        if file_ext == ".txt":
            return TextLoader(file_path,encoding="utf-8")
        
        return None


    def process_file_content(content:list,chunk_size: int,chunk_overlap: int):
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size,chunk_overlap=chunk_overlap,length_function=len)
        
        
        chunks = text_splitter.split_documents(content)
        
        return chunks   


def get_files_service(project_repo: ProjectRepo = Depends(get_project_repo),file_repo: FileRepo = Depends(get_file_repo),chunk_repo: ChunkRepo = Depends(get_chunk_repo)) -> FilesService:
    return FilesService(project_repo=project_repo,file_repo=file_repo,chunk_repo=chunk_repo)
