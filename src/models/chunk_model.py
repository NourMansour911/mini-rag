from pydantic import BaseModel, Field
from typing import Optional
from bson.objectid import ObjectId

class ChunkModel(BaseModel):
    iid: ObjectId = Field(..., alias="_id")
    chunk_text: str = Field(..., min_length=1)
    chunk_metadata: Optional[dict] = None 
    chunk_order: int = Field(..., gt=0)
    chunk_project_iid: ObjectId
    chunk_file_iid: Optional[ObjectId] = None 

    model_config = {  
        "arbitrary_types_allowed": True, 
        "populate_by_name": True,
        "json_encoders": {ObjectId: str}   
    }
    
    @classmethod
    def get_indexes(cls):
        return [
            {
                "key": [("chunk_project_id", 1)],
                "name": "chunk_project_id_index_1",
                "unique": False
            }
        ]