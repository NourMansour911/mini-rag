from helpers.logger import get_logger
from repos import ProjectRepo, FileRepo, ChunkRepo
from models import ChunkModel, FileModel
from schemas import PushRequest,SearchRequest
from fastapi import HTTPException, status, Depends
from stores import get_vdb_client, get_generation_client, get_embedding_client
from stores.llm import LLMInterface, DocumentTypeEnum
from stores.vector_db import VectorDBInterface
from typing import List
from helpers.enums import Signals
from repos import get_chunk_repo, get_file_repo, get_project_repo
import json

logger = get_logger(__name__)


class VDBService:

    def __init__(
        self,
        vdb_client: VectorDBInterface,
        project_repo: ProjectRepo | None = None,
        file_repo: FileRepo | None = None,
        chunk_repo: ChunkRepo | None = None,
        generation_client: LLMInterface | None = None,
        embedding_client: LLMInterface | None = None
    ):
        self.project_repo = project_repo
        self.file_repo = file_repo
        self.chunk_repo = chunk_repo
        self.vdb_client = vdb_client
        self.generation_client = generation_client
        self.embedding_client = embedding_client

        logger.info("Vector DB Push Service initialized")

    async def vdb_push(self, project_id: str, request_schema: PushRequest):

        if not await self.project_repo.project_exists(project_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Project [{project_id}] does not exist"
            )

        project = await self.project_repo.get_project_or_create_one(project_id)

        collection_name = self._create_collection_name(project_id)

        self.vdb_client.create_collection(
            collection_name=collection_name,
            embedding_size=self.embedding_client.embedding_size,
            do_reset=request_schema.do_reset
        )

        idx = 0
        inserted_chunks = 0
        files: List[FileModel] = []
        errors = []

        logger.info(request_schema.files_names)
        if not request_schema.files_names:

            page = 1
            while True:

                chunks = await self.chunk_repo.get_project_chunks(
                    project_iid=project.iid,
                    page=page
                )

                has_records, idx, inserted = await self._process_chunks_batch(
                    collection_name=collection_name,
                    chunks=chunks,
                    idx=idx
                )

                if not has_records:
                    break

                inserted_chunks += inserted
                page += 1

            return {
                "no_of_inserted_chunks": inserted_chunks,
                "signal": Signals.CHUNK_VECTORIZE_SUCCESS.value
            }
        else:
            for file_name in request_schema.files_names:

                file = await self.file_repo.get_file(
                    file_name=file_name,
                    project_iid=project.iid
                )

                if not file:
                    errors.append(f"File [{file_name}] does not exist")
                else:
                    files.append(file)

            if errors:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=errors
                )

            files_processed = 0

            for file in files:

                page = 1

                while True:

                    chunks = await self.chunk_repo.get_file_chunks(
                        file_iid=file.file_iid,
                        page=page
                    )

                    has_records, idx, inserted = await self._process_chunks_batch(
                        collection_name=collection_name,
                        chunks=chunks,
                        idx=idx
                    )

                    if not has_records:
                        break

                    inserted_chunks += inserted
                    page += 1

                files_processed += 1

            return {
                "no_of_inserted_chunks": inserted_chunks,
                "signal": Signals.CHUNK_VECTORIZE_SUCCESS.value,
                "files_names": [f.file_name for f in files],
                "no_of_files": files_processed
            }
    
    def vdb_info(self, project_id: str):
        collection_name = self._create_collection_name(project_id)
        info = self.vdb_client.get_collection_info(collection_name=collection_name)
        return json.loads(
            json.dumps(info,default=lambda x: x.__dict__)
        )
    
    async def vdb_search(self, project_id: str, request_schema: SearchRequest):
        if not await self.project_repo.project_exists(project_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Project [{project_id}] does not exist"
            )

        collection_name = self._create_collection_name(project_id)
        vector = self.embedding_client.embed_text(
                text=request_schema.query,
                document_type=DocumentTypeEnum.QUERY.value
            )
        
        if vector is None or len(vector) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=Signals.QUERY_VECTORIZE_FAILED.value
                )
            
        search_results = self.vdb_client.search_by_vector(
            collection_name=collection_name,
            vector=vector.tolist(),
            limit=request_schema.limit
        )
        return search_results

        
    async def _process_chunks_batch(
        self,
        collection_name: str,
        chunks: List[ChunkModel],
        idx: int
    ):

        if not chunks:
            return False, idx, 0

        record_ids = list(range(idx, idx + len(chunks)))
        idx += len(chunks)

        texts = [c.chunk_text for c in chunks]
        metadata = []

        for chunk in chunks:  
            
            metadata.append({
                "chunk_order": chunk.chunk_order,
                "chunk_type": chunk.chunk_type,
                "chunk_file_name": chunk.chunk_file_name,
                "chunk_file_iid": str(chunk.chunk_file_iid),
                "chunk_project_iid": str(chunk.chunk_project_iid),
                "chunk_pushed_at": chunk.chunk_pushed_at
            })        

        vectors = [
            self.embedding_client.embed_text(
                text=text,
                document_type=DocumentTypeEnum.DOCUMENT.value
            )
            for text in texts
        ]

        self.vdb_client.insert_many(
            collection_name=collection_name,
            texts=texts,
            vectors=vectors,
            metadata=metadata,
            record_ids=record_ids
        )

        return True, idx, len(chunks)

    def _create_collection_name(self, project_id: str):
        return f"collection_{project_id}".strip()


def get_vdb_service(
    project_repo: ProjectRepo = Depends(get_project_repo),
    file_repo: FileRepo = Depends(get_file_repo),
    chunk_repo: ChunkRepo = Depends(get_chunk_repo),
    vdb_client: VectorDBInterface = Depends(get_vdb_client),
    generation_client: LLMInterface = Depends(get_generation_client),
    embedding_client: LLMInterface = Depends(get_embedding_client)
):
    return VDBService(
        project_repo=project_repo,
        file_repo=file_repo,
        chunk_repo=chunk_repo,
        vdb_client=vdb_client,
        generation_client=generation_client,
        embedding_client=embedding_client
    )


def get_vdb_service_light(
    vdb_client: VectorDBInterface = Depends(get_vdb_client),
    embedding_client: LLMInterface = Depends(get_embedding_client),
    project_repo: ProjectRepo = Depends(get_project_repo),
):
    return VDBService(
        vdb_client=vdb_client,
        embedding_client=embedding_client,
        project_repo=project_repo,
    )
    

def get_vdb_service_only(
    vdb_client: VectorDBInterface = Depends(get_vdb_client),

):
    return VDBService(
        vdb_client=vdb_client,

    )