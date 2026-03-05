from ..BaseDataModel import BaseDataModel
from .file_entity import File
from helpers.enums import DBEnum
from bson import ObjectId


class FileModel(BaseDataModel):

    def __init__(self, db_client: object):
        super().__init__(db_client=db_client)
        self.collection = self.db_client[DBEnum.COLLECTION_FILE_NAME.value]
    
    @classmethod
    async def create_instance(cls, db_client: object):
        instance = cls(db_client)
        await instance.init_collection()
        return instance

    async def init_collection(self):
        all_collections = await self.db_client.list_collection_names()
        if DBEnum.COLLECTION_FILE_NAME.value not in all_collections:
            self.collection = self.db_client[DBEnum.COLLECTION_FILE_NAME.value]
            indexes = File.get_indexes()
            for index in indexes:
                await self.collection.create_index(
                    index["key"],
                    name=index["name"],
                    unique=index["unique"]
                )


    async def create_file(self, file: File):

        
        result = await self.collection.insert_one(file.model_dump(by_alias=True, exclude_unset=True))
        file.iid = result.inserted_id
       
        return file
    
    async def get_all_project_files(self, file_project_iid: str):
        result = await self.collection.find({
            "file_project_iid": ObjectId(file_project_iid) if isinstance(file_project_iid, str) else file_project_iid
        }).to_list(length=None)


        
        return result

    