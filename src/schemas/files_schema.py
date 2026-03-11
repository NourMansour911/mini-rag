from pydantic import BaseModel
from typing import List,Optional



class FileUploadResult(BaseModel):
    filename: str
    status: str
    database_filename: str
    file_db_id: Optional[str] = None
    signal: Optional[str] = None


class UploadResponse(BaseModel):
    project_db_id: str
    files: List[FileUploadResult]
    
class ChunkingRequest(BaseModel):
    files_names: list[str] = None
    chunk_size: Optional[int] = 400
    chunk_overlap: Optional[int] = 20
    do_reset: Optional[int] = 0


class FileChunkingResult(BaseModel):
    file_name: str
    status: str
    signal: Optional[str] = None


class FileChunkingResponse(BaseModel):
    project_db_id: str
    no_of_files: int
    no_of_inserted_chunks: int
    files: List[FileChunkingResult]
