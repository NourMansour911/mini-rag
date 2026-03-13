from pydantic import BaseModel
from typing import List,Optional


class PushRequest(BaseModel):
    do_reset: Optional[int] = 0
    files_names: Optional[list[str]] = None
    
class SearchRequest(BaseModel):
    query: str
    limit: Optional[int] = 5
    
    
class PushResponse(BaseModel):
    no_of_inserted_chunks: int
    signal: str
    no_of_files: Optional[int] = None
    files_names: Optional[list[str]] = None