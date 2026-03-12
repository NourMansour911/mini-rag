from repos import BaseRepo
from models import ChunkModel
from helpers.enums import DBEnum
from bson.objectid import ObjectId
from pymongo import InsertOne
from fastapi import Depends

class ChunkRepo(BaseRepo):

    def __init__(self, db_client: object):
        super().__init__(db_client=db_client)
        self.collection = self.db_client[DBEnum.COLLECTION_CHUNK_NAME.value]
        
        
    @classmethod
    async def create_instance(cls, db_client: object):
        instance = cls(db_client)
        await instance.init_collection()
        return instance

    async def init_collection(self):
        all_collections = await self.db_client.list_collection_names()
        if DBEnum.COLLECTION_CHUNK_NAME.value not in all_collections:
            self.collection = self.db_client[DBEnum.COLLECTION_CHUNK_NAME.value]
            indexes = ChunkModel.get_indexes()
            for index in indexes:
                await self.collection.create_index(
                    index["key"],
                    name=index["name"],
                    unique=index["unique"]
                )

    async def create_chunk(self, chunk: ChunkModel):
        result = await self.collection.insert_one(chunk.model_dump(by_alias=True, exclude_none=True))
        chunk.iid = result.inserted_id
        return chunk

    async def get_chunk(self, chunk_id: str):
        
        result = await self.collection.find_one({
            "_id": ObjectId(chunk_id)
        })

        if result is None:
            return None
        
        return ChunkModel(**result)

    async def get_project_chunks(self, project_iid: ObjectId,page:int=1,page_size:int=50):

        result = await self.collection.find({
            "chunk_project_iid": project_iid
        }).skip((page-1) * page_size).limit(page_size).to_list(length=None)

        return [ChunkModel(**record) for record in result]
    
    async def get_file_chunks(self, file_iid:ObjectId,page:int=1,page_size:int=50):
        result = await self.collection.find({
            "chunk_file_iid": file_iid
        }).skip((page-1) * page_size).limit(page_size).to_list(length=None)
        
        return [ChunkModel(**record) for record in result]
    
    
    async def insert_many_chunks(self, chunks: list[ChunkModel], batch_size: int=100):

        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i+batch_size]

            operations = [
                InsertOne(chunk.model_dump(by_alias=True, exclude_none=True))
                for chunk in batch
            ]

            await self.collection.bulk_write(operations)
        
        return len(chunks)

    async def delete_chunks_by_project_id(self, project_iid: ObjectId):
        result = await self.collection.delete_many({
            "chunk_project_iid": project_iid
        })

        return result.deleted_count
    
    
async def  get_chunk_repo(db_client: object = Depends(BaseRepo.get_db_client)):
    return await ChunkRepo.create_instance(db_client=db_client)