import os
import uuid
import re

from helpers.logger import get_logger  
from helpers.settings import get_settings

import os

from langchain_community.document_loaders import PyPDFLoader,TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = get_logger(__name__)  



settings = get_settings()

base_dir = os.path.dirname(os.path.dirname(__file__))
files_dir = os.path.join(base_dir,"assets/files")

def _get_project_path(project_id: str):
        project_dir = os.path.join(files_dir, project_id)
        
        if not os.path.exists(project_dir):
            os.makedirs(project_dir)
            logger.info(f"Created project directory: {project_dir}")
        else:
            logger.debug(f"Project directory exists: {project_dir}")
        
        return project_dir   
 

def _get_clean_filename(original_filename: str) -> str:
    cln_name = re.sub(r'[^\w.]', '', original_filename)
    cln_name = cln_name.replace(" ","_").lower()
    logger.debug(f"Cleaned filename: {original_filename} -> {cln_name}")
    return cln_name

def generate_file_path(original_filename: str, project_id: str):
    try:
        project_path = _get_project_path(project_id=project_id)
        file_name = _get_clean_filename(original_filename=original_filename)
        random_name = str(uuid.uuid4()) + "_" + file_name
        file_path = os.path.join(project_path, random_name)
        logger.debug(f"Generated file path: {file_path}")
    except Exception as e:
        logger.error(f"Error generating file path for {original_filename}: {e}", exc_info=True)
        return e.__str__()
    return file_path, random_name


    
def get_file_loader(project_id: str,file_name:str):
    file_ext = os.path.splitext(file_name)[-1]
    file_path = os.path.join(
        _get_project_path(project_id=project_id),
        file_name
    )
    if file_ext == ".pdf":
        return PyPDFLoader(file_path)
    
    if file_ext == ".txt":
        return TextLoader(file_path,encoding="utf-8")
    
    return None


def process_file_content(content:list,chunk_size: int,chunk_overlap: int):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size,chunk_overlap=chunk_overlap,length_function=len)
    
    
    chunks = text_splitter.split_documents(content)
    
    return chunks
