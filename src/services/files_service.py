from base_service import BaseService
from fastapi import UploadFile,status
from fastapi.responses import JSONResponse
import os
import uuid
import aiofiles
import re
from helpers.config import get_settings,Settings
from helpers.enums import Signals
from helpers.logger import get_logger  

logger = get_logger("file_service")  # Logger for this layer

class FileService(BaseService):
    
    def __init__(self):
        super().__init__()
        self.settings = get_settings()
        logger.info("FileService initialized")

    def validate_file(self, file: UploadFile):
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

    def get_project_path(self, project_id: str):
        project_dir = os.path.join(self.files_dir, project_id)
        
        if not os.path.exists(project_dir):
            os.makedirs(project_dir)
            logger.info(f"Created project directory: {project_dir}")
        else:
            logger.debug(f"Project directory exists: {project_dir}")
        
        return project_dir    

    def get_clean_filename(self, original_filename: str) -> str:
        cln_name = re.sub(r'[^\w.]', '', original_filename)
        cln_name = cln_name.replace(" ","_").lower()
        logger.debug(f"Cleaned filename: {original_filename} -> {cln_name}")
        return cln_name
    
    def generate_file_path(self, original_filename: str, project_id: str):
        try:
            project_dir = self.get_project_path(project_id=project_id)
            file_name = self.get_clean_filename(original_filename=original_filename)
            random_name = str(uuid.uuid4()) + "_" + file_name
            file_path = os.path.join(project_dir, random_name)
            logger.debug(f"Generated file path: {file_path}")
        except Exception as e:
            logger.error(f"Error generating file path for {original_filename}: {e}", exc_info=True)
            return e.__str__()
        return file_path, random_name
    
    async def write_file(self, file: UploadFile, project_id: str):
        file_path, file_id = self.generate_file_path(original_filename=file.filename, project_id=project_id)
        logger.info(f"Writing file to path: {file_path}")

        try:
            async with aiofiles.open(file_path, 'wb') as f:
                while chunk := await file.read(self.settings.FILE_DEFAULT_CHUNK_SIZE):
                    await f.write(chunk)
            logger.info(f"File written successfully: {file.filename} -> {file_path}")
        except Exception as e:
            logger.error(f"Error writing file {file.filename}: {e}", exc_info=True)
            raise

        return file_path, file_id