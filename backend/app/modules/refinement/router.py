from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.modules.refinement import service
router=APIRouter(prefix='/api/projects/{project_id}/refinement',tags=['refinement'])
class Request(BaseModel):
    message:str

def respond(action,*args):
    try: return action(*args)
    except LookupError as exc: raise HTTPException(status_code=404,detail=str(exc)) from exc
    except ValueError as exc: raise HTTPException(status_code=409,detail=str(exc)) from exc
    except RuntimeError as exc: raise HTTPException(status_code=502,detail=str(exc)) from exc

@router.get('')
def get_refinement(project_id:str): return respond(service.state,project_id)
@router.post('/propose')
def propose(project_id:str,body:Request): return respond(service.propose,project_id,body.message)
@router.post('/apply')
def apply(project_id:str): return respond(service.apply,project_id)
@router.post('/discard')
def discard(project_id:str): return respond(service.discard,project_id)
