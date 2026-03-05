from pydantic import BaseModel, Field
from typing import Optional
from bson.objectid import ObjectId
from datetime import datetime

class File(BaseModel):
    iid: Optional[ObjectId] = Field(None, alias="_id")
    file_project_iid: ObjectId
    file_type: str = Field(default="file", min_length=1)
    file_name: str = Field(..., min_length=1)
    file_size: int = Field(ge=0, default=None)
    file_config: dict = Field(default=None)
    file_pushed_at: datetime = Field(default=datetime.now())

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
                    ("file_project_id", 1)
                ],
                "name": "file_project_id_index_1",
                "unique": False
            },
            {
                "key": [
                    ("file_project_id", 1),
                    ("file_name", 1)
                ],
                "name": "file_project_id_name_index_1",
                "unique": True
            },
        ]