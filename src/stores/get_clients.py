from fastapi import Request


def get_vdb_client(request: Request):
    return request.app.vdb_client

def get_generation_client(request: Request):
    return request.app.generation_client

def get_embedding_client(request: Request):
    return request.app.embedding_client
