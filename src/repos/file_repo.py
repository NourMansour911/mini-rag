from repos import BaseRepo
from models import FileModel
from helpers.enums import DBEnum

from helpers.logger import get_logger  # << Added logger
import logging

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
    
