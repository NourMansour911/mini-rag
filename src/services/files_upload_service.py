from .base_service import BaseService
from fastapi import UploadFile
import os
import uuid
import aiofiles
import re
from helpers.config import get_settings
from helpers.enums import Signals
from helpers.logger import get_logger  
from repos import  ProjectRepo, FileRepo
from models import  FileModel
from typing import List
from models.schemas import ChunkingRequest


logger = get_logger(__name__)  

class FilesUploadService(BaseService):
    
    def __init__(self):
        super().__init__()
        self.settings = get_settings()
        logger.info("File Upload Service initialized")


    async def upload_files(
        self,
        project_id: str,
        db_client,
        files: List[UploadFile]
    ):

        project_repo = await ProjectRepo.create_instance(db_client=db_client)
        file_repo = await FileRepo.create_instance(db_client=db_client)

        project = await project_repo.get_project_or_create_one(project_id=project_id)

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

                _, file_name = await self._write_file(
                    file=file,
                    project_id=project.project_id
                )

                file_model = FileModel(
                    file_name=file_name,
                    file_size=file.size,
                    file_project_iid=project.iid
                )

                saved_file = await file_repo.add_file(file_model)

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

 

    def _get_clean_filename(self, original_filename: str) -> str:
        cln_name = re.sub(r'[^\w.]', '', original_filename)
        cln_name = cln_name.replace(" ","_").lower()
        logger.debug(f"Cleaned filename: {original_filename} -> {cln_name}")
        return cln_name
    
    def _generate_file_path(self, original_filename: str, project_id: str):
        try:
            project_dir = self.get_project_path(project_id=project_id)
            file_name = self._get_clean_filename(original_filename=original_filename)
            random_name = str(uuid.uuid4()) + "_" + file_name
            file_path = os.path.join(project_dir, random_name)
            logger.debug(f"Generated file path: {file_path}")
        except Exception as e:
            logger.error(f"Error generating file path for {original_filename}: {e}", exc_info=True)
            return e.__str__()
        return file_path, random_name
    
    async def _write_file(self, file: UploadFile, project_id: str):
        file_path, file_name = self._generate_file_path(original_filename=file.filename, project_id=project_id)
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
    

        
