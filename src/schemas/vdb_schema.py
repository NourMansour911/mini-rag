from pydantic import BaseModel
from typing import List,Optional


class PushRequest(BaseModel):
    do_reset: Optional[int] = 0
    files_names: list[str] = None
    
    
class PushResponse(BaseModel):
    no_of_inserted_chunks: int
    signal: str
    no_of_files: Optional[int] 
    files_names: Optional[list[str]] = None