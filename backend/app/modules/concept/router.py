from fastapi import APIRouter, BackgroundTasks, HTTPException
from app.modules.concept import service

router = APIRouter(prefix='/api/projects/{project_id}/concept',tags=['concept'])

@router.get('')
def get_concept(project_id:str):
    return service.get(project_id)

@router.post('/generate')
def generate_concept(project_id:str,background_tasks:BackgroundTasks):
    try:
        return service.start(project_id,background_tasks)
    except LookupError as exc:
        raise HTTPException(status_code=404,detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409,detail=str(exc)) from exc
