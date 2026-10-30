from fastapi import APIRouter, BackgroundTasks, HTTPException
from app.core.database import connect
from datetime import datetime, timezone
from fastapi.responses import Response
from app.modules.execution_plan.pdf_export import build_execution_pdf
from app.modules.execution_plan import service
router=APIRouter(prefix='/api/projects/{project_id}/execution',tags=['execution-plan'])
@router.get('')
def get_plan(project_id:str):
    return service.get(project_id)
@router.post('/generate')
def generate_plan(project_id:str,background_tasks:BackgroundTasks):
    try: return service.start(project_id,background_tasks)
    except LookupError as exc: raise HTTPException(status_code=404,detail=str(exc)) from exc
    except ValueError as exc: raise HTTPException(status_code=409,detail=str(exc)) from exc

@router.get('/pdf')
def export_pdf(project_id: str):
    state = service.get(project_id)
    if state.get('status') != 'completed' or not state.get('plan'):
        raise HTTPException(status_code=409, detail='Generate a completed execution plan before exporting PDF')
    try:
        pdf = build_execution_pdf(state['plan'])
    except Exception as exc:
        raise HTTPException(status_code=500, detail='PDF generation failed: ' + str(exc)[:250]) from exc
    return Response(content=pdf, media_type='application/pdf', headers={
        'Content-Disposition': 'attachment; filename="EpiVibe_Complete_Execution_Plan.pdf"',
        'Cache-Control': 'no-store',
    })

@router.post('/complete')
def complete_planning(project_id: str):
    state = service.get(project_id)
    if state.get('status') != 'completed' or not state.get('plan') or state.get('stale'):
        raise HTTPException(409, 'Generate an up-to-date execution plan before confirming completion')
    with connect() as db:
        row = db.execute('SELECT concept_json FROM event_concepts WHERE project_id=? AND status=?', (project_id, 'completed')).fetchone()
        if not row or not row['concept_json']:
            raise HTTPException(409, 'Approved concept is missing')
        db.execute("""CREATE TABLE IF NOT EXISTS project_approvals (
            project_id TEXT PRIMARY KEY, source_concept_json TEXT NOT NULL,
            approved_at TEXT NOT NULL)""")
        db.execute("""INSERT INTO project_approvals(project_id,source_concept_json,approved_at)
            VALUES(?,?,?) ON CONFLICT(project_id) DO UPDATE SET
            source_concept_json=excluded.source_concept_json,approved_at=excluded.approved_at""",
            (project_id,row['concept_json'],datetime.now(timezone.utc).isoformat()))
    return {'planningCompleted':True}
