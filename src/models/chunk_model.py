from pydantic import BaseModel, Field
from typing import Optional
from bson.objectid import ObjectId

class ChunkModel(BaseModel):
    iid: Optional[ObjectId] = Field(None, alias="_id")
    chunk_text: str = Field(..., min_length=1)
    chunk_metadata: dict
    chunk_order: int = Field(..., gt=0)
    chunk_project_iid: ObjectId
    chunk_asset_iid: Optional[ObjectId]


    model_config = {  
        "arbitrary_types_allowed": True, 
        "populate_by_name": True,
        "json_encoders": {ObjectId: str}   
    }
    
    @classmethod
    def get_indexes(cls):
        return [
            {
                "key": [
                    ("chunk_project_id", 1)
                ],
                "name": "chunk_project_id_index_1",
                "unique": False
            }
        ]