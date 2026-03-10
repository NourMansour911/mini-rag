from repos import BaseRepo
from models import FileModel
from helpers.enums import DBEnum

from helpers.logger import get_logger  # << Added logger
import logging

from bson import ObjectId

from fastapi import Depends

logger = get_logger("file_repo", level=logging.DEBUG)  # Logger for this layer

class FileRepo(BaseRepo):

    def __init__(self, db_client: object):
        super().__init__(db_client=db_client)
        self.collection = self.db_client[DBEnum.COLLECTION_FILE_NAME.value]
        logger.info(f"FileRepo initialized with collection: {DBEnum.COLLECTION_FILE_NAME.value}")
    
    @classmethod
    async def create_instance(cls, db_client: object):
        logger.debug("Creating FileRepo instance")
        try:
            instance = cls(db_client)
            await instance.init_collection()
            logger.info("FileRepo instance created successfully")
            return instance
        except Exception as e:
            logger.error(f"Error creating FileRepo instance: {e}", exc_info=True)
            raise

    async def init_collection(self):
        try:
            all_collections = await self.db_client.list_collection_names()
            if DBEnum.COLLECTION_FILE_NAME.value not in all_collections:
                self.collection = self.db_client[DBEnum.COLLECTION_FILE_NAME.value]
                indexes = FileModel.get_indexes()
                for index in indexes:
                    await self.collection.create_index(
                        index["key"],
                        name=index["name"],
                        unique=index["unique"]
                    )
                logger.info(f"Collection {DBEnum.COLLECTION_FILE_NAME.value} initialized with indexes")
            else:
                logger.debug(f"Collection {DBEnum.COLLECTION_FILE_NAME.value} already exists")
        except Exception as e:
            logger.error(f"Error initializing collection {DBEnum.COLLECTION_FILE_NAME.value}: {e}", exc_info=True)
            raise
        
    async def add_file(self, file: FileModel):
        try:
            result = await self.collection.insert_one(file.model_dump(by_alias=True, exclude_none=True))
            file.file_iid = result.inserted_id
            logger.info(f"File added successfully with ID: {file.file_iid}")
            return file
        except Exception as e:
            logger.error(f"Error adding file: {e}", exc_info=True)
            raise
        
    async def get_file(self, project_iid: str, file_name: str) -> FileModel | None:

        record = await self.collection.find_one({
            "file_project_iid": ObjectId(project_iid) if isinstance(project_iid, str) else project_iid,
            "file_name": file_name,
        })

        if record:
            return FileModel(**record)
        
        return None

    async def get_all_project_files(self, project_iid: str) -> list[FileModel] | None:
        try:
            query = {
                "file_project_iid": ObjectId(project_iid) if isinstance(project_iid, str) else project_iid
            }
            logger.debug(f"Fetching all files for project ID: {project_iid} with query: {query}")
            result = await self.collection.find(query).to_list(length=None)
            logger.info(f"Fetched {len(result)} files for project ID: {project_iid}")
            return [
            FileModel(**record)
            for record in result
        ]
        except Exception as e:
            logger.error(f"Error fetching project files for ID {project_iid}: {e}", exc_info=True)
            return None

async def get_file_repo(db_client: object = Depends(BaseRepo.get_db_client)):
    return await FileRepo.create_instance(db_client=db_client)
