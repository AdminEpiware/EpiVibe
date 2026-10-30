from fastapi import APIRouter, BackgroundTasks, HTTPException
from app.modules.research import service
router=APIRouter(prefix='/api/projects/{project_id}/research',tags=['research'])
@router.get('')
def status(project_id:str):return service.get(project_id)
@router.post('/start')
def start(project_id:str, background_tasks:BackgroundTasks):
    try:return service.start(project_id,background_tasks)
    except LookupError:raise HTTPException(404,'Project not found')
