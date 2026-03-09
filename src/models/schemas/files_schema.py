from pydantic import BaseModel
from typing import List,Optional

class ChunkingRequest(BaseModel):
    file_ids: list[str] = None
    chunk_size: Optional[int] = 400
    overlap_size: Optional[int] = 20
    do_reset: Optional[int] = 0


class FileUploadResult(BaseModel):
    filename: str
    status: str
    database_filename: str
    file_db_id: Optional[str] = None
    signal: Optional[str] = None


class UploadResponse(BaseModel):
    project_db_id: str
    files: List[FileUploadResult]