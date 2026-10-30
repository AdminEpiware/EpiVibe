from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4
import json
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from app.core.database import connect

router = APIRouter(prefix='/api/projects', tags=['projects'])

def now():
    return datetime.now(timezone.utc).isoformat()

class ProjectInput(BaseModel):
    id: str | None = None
    eventType: str = ''
    eventTypeOther: str = ''
    title: str = ''
    location: str = ''
    audiences: list[str] = Field(default_factory=list)
    audienceOther: str = ''
    dateStart: str = ''
    dateEnd: str = ''
    goals: list[str] = Field(default_factory=list)
    goalOther: str = ''
    currency: str = 'INR'
    budget: str = ''
    context: str = ''
    status: str = 'Draft'
    updatedAt: str = ''

def parse(row):
    brief = json.loads(row['brief_json'])
    with connect() as db:
        research = db.execute("SELECT status FROM research_runs WHERE project_id=?", (brief['id'],)).fetchone() if _has_table(db, 'research_runs') else None
        concept = db.execute("SELECT status FROM event_concepts WHERE project_id=?", (brief['id'],)).fetchone() if _has_table(db, 'event_concepts') else None
        execution = db.execute("SELECT status FROM execution_plans WHERE project_id=?", (brief['id'],)).fetchone() if _has_table(db, 'execution_plans') else None
        approval = db.execute("SELECT source_concept_json FROM project_approvals WHERE project_id=?", (brief['id'],)).fetchone() if _has_table(db, 'project_approvals') else None
        concept_json = db.execute("SELECT concept_json FROM event_concepts WHERE project_id=?", (brief['id'],)).fetchone() if concept and _has_table(db, 'event_concepts') else None
    from app.modules.execution_plan import service as execution_service
    stage1 = brief.get('status') != 'Draft' or bool(research or concept or execution)
    stage2 = bool(research and research['status'] == 'completed')
    stage3 = bool(concept and concept['status'] == 'completed' and concept_json and concept_json['concept_json'])
    stage4 = bool(stage3 and execution and execution['status'] == 'completed' and approval and
                  approval['source_concept_json'] == concept_json['concept_json'] and
                  not execution_service.get(brief['id']).get('stale'))
    brief['completedStages'] = [i for i, ok in enumerate((stage1,stage2,stage3,stage4),1) if ok]
    brief['status'] = 'Planning Completed' if stage4 else ('Draft' if not stage1 else 'In Progress')
    return brief

def _has_table(db, name):
    return bool(db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)).fetchone())

@router.get('')
def list_projects():
    with connect() as db:
        rows = db.execute('SELECT brief_json FROM projects ORDER BY updated_at DESC').fetchall()
    return [parse(r) for r in rows]

@router.get('/{project_id}')
def get_project(project_id: str):
    with connect() as db:
        row = db.execute('SELECT brief_json FROM projects WHERE id=?', (project_id,)).fetchone()
    if not row:
        raise HTTPException(404, 'Project not found')
    return parse(row)

@router.put('/{project_id}')
def save_project(project_id: str, data: ProjectInput):
    try:
        UUID(project_id)
    except ValueError:
        raise HTTPException(422, 'Invalid project ID')
    if data.status not in ('Draft','Researching','Research Completed','Action Required','In Progress','Planning Completed'):
        raise HTTPException(422, 'Unsupported project status')
    stamp = now()
    with connect() as db:
        old = db.execute('SELECT created_at FROM projects WHERE id=?',(project_id,)).fetchone()
        brief = data.model_dump()
        brief.update(id=project_id, updatedAt=stamp)
        db.execute('''INSERT INTO projects (id,title,status,brief_json,created_at,updated_at)
            VALUES (?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET
            title=excluded.title,status=excluded.status,brief_json=excluded.brief_json,updated_at=excluded.updated_at''',
            (project_id, data.title, data.status, json.dumps(brief), old['created_at'] if old else stamp, stamp))
    return brief

@router.delete('/{project_id}', status_code=204)
def delete_project(project_id: str):
    with connect() as db:
        if not db.execute('SELECT 1 FROM projects WHERE id=?',(project_id,)).fetchone():
            raise HTTPException(404, 'Project not found')
        # Delete all project-scoped records, including revision history.
        tables = db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        for row in tables:
            table = row['name']
            if table == 'projects' or not table.replace('_','').isalnum():
                continue
            columns = {col['name'] for col in db.execute(f'PRAGMA table_info("{table}")')}
            if 'project_id' in columns:
                db.execute(f'DELETE FROM "{table}" WHERE project_id=?', (project_id,))
        db.execute('DELETE FROM projects WHERE id=?', (project_id,))
