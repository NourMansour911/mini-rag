from pydantic import BaseModel, Field
from typing import Optional
from bson.objectid import ObjectId
from datetime import datetime
class ChunkModel(BaseModel):
    iid: Optional[ObjectId] = Field(None, alias="_id")
    chunk_text: str = Field(..., min_length=1)
    chunk_metadata: Optional[dict] = None 
    chunk_order: int = Field(..., gt=0)
    chunk_id: Optional[str] = None
    chunk_type: Optional[str] = None
    chunk_file_name: Optional[str]
    chunk_file_iid: Optional[ObjectId]
    chunk_project_iid: ObjectId
    chunk_pushed_at: datetime = Field(default=datetime.now())

    model_config = {  
        "arbitrary_types_allowed": True, 
        "populate_by_name": True,
        "json_encoders": {ObjectId: str}   
    }
    
    @classmethod
    def get_indexes(cls):
        return [
            {
                "key": [("chunk_project_iid", 1)],
                "name": "chunk_project_iid_index_1",
                "unique": False
            }
        ]