from helpers.enums import Signals
from helpers.logger import get_logger
from helpers.settings import get_settings
from helpers.disk_helper import get_project_path, generate_file_path

import os
import aiofiles

from typing import List

from fastapi import HTTPException, status, UploadFile, Depends

from repos import (
    ProjectRepo,
    FileRepo,
    ChunkRepo,
    get_chunk_repo,
    get_file_repo,
    get_project_repo
)

from models import ChunkModel, FileModel,ProjectModel
from schemas import ChunkingRequest

from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter


logger = get_logger(__name__)


class FilesService:

    def __init__(
        self,
        project_repo: ProjectRepo,
        file_repo: FileRepo,
        chunk_repo: ChunkRepo
    ):
        self.project_repo = project_repo
        self.file_repo = file_repo
        self.chunk_repo = chunk_repo
        self.settings = get_settings()


    async def upload_files(
        self,
        project_id: str,
        files: List[UploadFile]
    ):

        project = await self.project_repo.get_project_or_create_one(project_id)

        logger.info(
            f"Using project: {project.project_id} (DB ID: {str(project.iid)})"
        )

        response_list = []

        for file in files:

            is_valid, signal = self._validate_file(file)

            if not is_valid:
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
                    file_size=file.size if file.size else 0,
                    file_project_iid=project.iid,
                    file_original_name=file.filename
                )

                saved_file = await self.file_repo.add_file(file_model)

                response_list.append({
                    "filename": file.filename,
                    "status": "success",
                    "database_filename": file_name,
                    "file_db_id": str(saved_file.file_iid),
                    "signal": signal
                })

                logger.info(f"File uploaded successfully: {file.filename}")

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

        return {
            "project_db_id": str(project.iid),
            "files": response_list
        }


    async def chunking(
        self,
        request_schema: ChunkingRequest,
        project_id: str
    ):

        if not await self.project_repo.project_exists(project_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Project [{project_id}] does not exist"
            )

        project = await self.project_repo.get_project_or_create_one(project_id)

        if request_schema.do_reset == 1:
            await self.chunk_repo.delete_chunks_by_project_id(project.iid)
        
        files: List[FileModel] = await self._get_files(project, request_schema) 

        if not files:
            return {
                "project_db_id": str(project.iid),
                "no_of_files": 0,
                "no_of_inserted_chunks": 0,
                "files": []
            }

        response_list = []
        inserted_chunks = 0
        processed_files = 0

        for file in files:

            try:

                file_chunks = self._create_chunks(
                    project_id=project_id,
                    file_name=file.file_name,
                    chunk_size=request_schema.chunk_size,
                    chunk_overlap=request_schema.chunk_overlap
                )

                chunk_records = [
                    ChunkModel(
                        chunk_project_iid=file.file_project_iid,
                        chunk_file_iid=file.file_iid,
                        chunk_file_name=file.file_name,
                        chunk_order=i + 1,
                        chunk_id=chunk.id,
                        chunk_metadata=chunk.metadata,
                        chunk_text=chunk.page_content,
                        chunk_type=chunk.type
                    )
                    for i, chunk in enumerate(file_chunks)
                ]

                inserted_chunks += await self.chunk_repo.insert_many_chunks(
                    chunk_records
                )

                processed_files += 1

                response_list.append({
                    "filename": file.file_name,
                    "status": "success",
                    "signal": Signals.CHUNKING_SUCCESS.value
                })

                logger.info(f"File chunked successfully: {file.file_name}")

            except Exception as e:

                logger.error(
                    f"Error chunking file {file.file_name}: {e}",
                    exc_info=True
                )

                response_list.append({
                    "filename": file.file_name,
                    "status": "error",
                    "signal": Signals.CHUNKING_FAILED.value
                })

        return {
            "project_db_id": str(project.iid),
            "no_of_files": processed_files,
            "no_of_inserted_chunks": inserted_chunks,
            "files": response_list
        }


    def _validate_file(self, file: UploadFile):

        if not file or not file.filename:
            return False, Signals.FILE_NOT_FOUND.value

        if file.size and file.size > (
            self.settings.FILE_MAX_SIZE * self.settings.FILE_SCALE_VALUE
        ):
            return False, Signals.FILE_SIZE_EXCEEDED.value

        if file.content_type not in self.settings.FILE_ALLOWED_EXT:
            return False, Signals.FILE_TYPE_NOT_ALLOWED.value

        return True, Signals.FILE_VALID.value


    async def _disk_write_file(self, file: UploadFile, project_id: str):

        file_path, file_name = generate_file_path(
            original_filename=file.filename,
            project_id=project_id
        )

        try:

            async with aiofiles.open(file_path, "wb") as f:

                while chunk := await file.read(
                    self.settings.FILE_DEFAULT_CHUNK_SIZE
                ):
                    await f.write(chunk)

        except Exception as e:
            logger.error(
                f"Error writing file {file.filename}: {e}",
                exc_info=True
            )
            raise

        return file_path, file_name


    async def _get_files(self, project: ProjectModel, request_schema: ChunkingRequest):

        if request_schema.files_names is None:
            return await self.file_repo.get_all_project_files(project.iid)

        files = []
        errors = []

        for file_name in request_schema.files_names:

            file = await self.file_repo.get_file(
                file_name=file_name,
                project_iid=project.iid
            )

            if not file:
                errors.append(f"File [{file_name}] does not exist")
            else:
                files.append(file)

        if errors:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=errors
            )

        return files

 
    def _create_chunks(
        self,
        project_id: str,
        file_name: str,
        chunk_size: int,
        chunk_overlap: int
    ):

        file_loader = self.get_file_loader(project_id, file_name)

        if not file_loader:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=Signals.FILE_TYPE_NOT_ALLOWED.value
            )

        documents = file_loader.load()

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len
        )

        return splitter.split_documents(documents)


    def get_file_loader(self, project_id: str, file_name: str):

        file_ext = os.path.splitext(file_name)[-1].lower()

        file_path = os.path.join(
            get_project_path(project_id),
            file_name
        )

        if file_ext == ".pdf":
            return PyPDFLoader(file_path)

        if file_ext == ".txt":
            return TextLoader(file_path, encoding="utf-8")

        return None



def get_files_service(
    project_repo: ProjectRepo = Depends(get_project_repo),
    file_repo: FileRepo = Depends(get_file_repo),
    chunk_repo: ChunkRepo = Depends(get_chunk_repo)
) -> FilesService:

    return FilesService(
        project_repo=project_repo,
        file_repo=file_repo,
        chunk_repo=chunk_repo
    )