from pydantic import BaseModel,field_validator,Field
from typing import Optional
from bson.objectid import ObjectId

class ProjectModel(BaseModel):
    iid: Optional[ObjectId] = Field(None, alias="_id")
    project_id: str = Field(...,min_length=1)
    
    
    @field_validator("project_id")
    def validate_project_id(cls,value):
        if not value.isalnum():
            raise ValueError("project_id must be alphanumeric")
        return value
    
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
                    ("project_id", 1)
                ],
                "name": "project_id_index_1",
                "unique": True
            }
        ]