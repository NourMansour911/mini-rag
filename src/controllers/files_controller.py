from repos import ChunkRepo, ProjectRepo, FileRepo
from models import ChunkModel, FileModel, ProjectModel
from services import FileService
from fastapi.responses import JSONResponse
from fastapi import Request, UploadFile, File,status
from typing import List
from helpers.logger import get_logger

logger = get_logger("files_controller")

class FilesController:

    async def upload_files(self, project_id: str, app_request: Request, files: List[UploadFile] = File(...)):
      try:
             
        file_service = FileService()
        
     
        project_repo = await ProjectRepo.create_instance(db_client=app_request.app.db_client)
        file_repo = await FileRepo.create_instance(db_client=app_request.app.db_client)

      
        project = await project_repo.get_project_or_create_one(project_id=project_id)
        logger.info(f"Using project: {project.project_id} (DB ID: {str(project.iid)})")

        response_list = []

        for file in files:
            
            is_valid, signal = file_service.validate_file(file=file)
            if not is_valid:
                logger.warning(f"File validation failed: {file.filename} | Signal: {signal}")
                response_list.append({
                    "filename": file.filename,
                    "status": "error",
                    "signal": signal
                })
                continue

            try:
                _, file_name = await file_service.write_file(file=file, project_id=project.project_id)
                
                file_model = FileModel(
                    file_name=file.filename,
                    file_size=file.size,
                    file_project_iid=project.iid
                )

                saved_file = await file_repo.add_file(file_model)
                logger.info(f"File saved successfully: {file.filename} | File ID: {str(saved_file.file_iid)}")

                response_list.append({
                    "filename": file.filename,
                    "status": "success",
                    "file_id": str(saved_file.file_iid) 
                })

            except Exception as e:
                logger.error(f"Error saving file {file.filename}: {e}", exc_info=True)
                response_list.append({
                    "filename": file.filename,
                    "status": "error",
                    "message": str(e)
                })
         
        logger.info(f"Files uploaded successfully for project: {project.project_id} (DB ID: {str(project.iid)})")
         
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
            "project_db_id": str(project.iid), 
            "files": response_list
        })
      except Exception as e:
            logger.error(f"Error uploading files: {e}", exc_info=True)
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"message": f"Error uploading files: {e}"}
            )