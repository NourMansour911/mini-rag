from helpers.settings import get_settings, Settings
from fastapi import  Request
class BaseRepo:

    def __init__(self, db_client: object):
        self.db_client = db_client
        self.app_settings = get_settings()
    
    def get_db_client(request: Request):
        return request.app.db_client