"""Stage 4 execution-plan generation using approved Stage 3 concept and saved research."""
import json
import os
import threading
from datetime import datetime, timezone, date
from decimal import Decimal, InvalidOperation
from urllib import request, error, parse
from app.core.database import connect
from app.modules.concept import service as concept_service

_LOCK = threading.RLock()

def now(): return datetime.now(timezone.utc).isoformat()

def setup():
    with connect() as db:
        db.execute("""CREATE TABLE IF NOT EXISTS execution_plans (
            project_id TEXT PRIMARY KEY, status TEXT NOT NULL,
            source_version INTEGER, source_concept_json TEXT,
            plan_json TEXT, error TEXT, updated_at TEXT NOT NULL,
            FOREIGN KEY(project_id) REFERENCES projects(id))""")

def get(project_id):
    setup()
    with connect() as db:
        row=db.execute('SELECT * FROM execution_plans WHERE project_id=?',(project_id,)).fetchone()
    if not row: return {'status':'not_started','plan':None,'error':None,'source_version':None,'stale':False}
    stale=False
    if row['status']=='completed':
        try:
            current=concept_service.get(project_id).get('concept')
            stale=bool(current and json.dumps(current,sort_keys=True,ensure_ascii=False)!=row['source_concept_json'])
        except Exception: pass
    return {'status':row['status'],'plan':json.loads(row['plan_json']) if row['plan_json'] else None,
            'error':row['error'],'source_version':row['source_version'],'stale':stale,'updatedAt':row['updated_at']}

def save(project_id,status,version=None,concept=None,plan=None,error_message=None):
    if status == 'running':
        with connect() as db:
            if db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='project_approvals'").fetchone():
                db.execute('DELETE FROM project_approvals WHERE project_id=?', (project_id,))
    setup()
    with connect() as db:
        db.execute("""INSERT INTO execution_plans(project_id,status,source_version,source_concept_json,plan_json,error,updated_at)
            VALUES(?,?,?,?,?,?,?) ON CONFLICT(project_id) DO UPDATE SET
            status=excluded.status,source_version=COALESCE(excluded.source_version,execution_plans.source_version),
            source_concept_json=COALESCE(excluded.source_concept_json,execution_plans.source_concept_json),
            plan_json=excluded.plan_json,error=excluded.error,updated_at=excluded.updated_at""",
            (project_id,status,version,json.dumps(concept,sort_keys=True,ensure_ascii=False) if concept is not None else None,
             json.dumps(plan,ensure_ascii=False) if plan is not None else None,error_message,now()))

def source(project_id):
    with connect() as db:
        project=db.execute('SELECT brief_json FROM projects WHERE id=?',(project_id,)).fetchone()
        if not project: raise LookupError('Project not found')
        research=db.execute('SELECT status,evidence_json FROM research_runs WHERE project_id=?',(project_id,)).fetchone()
    if not research or research['status']!='completed' or not research['evidence_json']:
        raise ValueError('Complete AI Research before generating an execution plan')
    state=concept_service.get(project_id)
    if state['status']!='completed' or not state['concept']:
        raise ValueError('Complete Event Concept before generating an execution plan')
    concept=state['concept']
    try: budget=Decimal(str(concept['budget_total']))
    except (KeyError,InvalidOperation,TypeError) as exc: raise ValueError('Approved concept has no valid budget_total') from exc
    if budget<=0: raise ValueError('Approved concept budget must be positive')
    allocations=concept.get('budget_allocations',[])
    if abs(sum(Decimal(str(x['amount'])) for x in allocations)-budget)>Decimal('1'):
        raise ValueError('Approved concept allocations do not match its working budget')
    version=None
    try:
        with connect() as db:
            r=db.execute('SELECT MAX(version) AS v FROM concept_versions WHERE project_id=?',(project_id,)).fetchone()
            version=r['v'] if r else None
    except Exception: pass
    return json.loads(project['brief_json']),json.loads(research['evidence_json']),concept,version

def require_list(plan,key):
    if not isinstance(plan.get(key),list) or not plan[key]: raise ValueError('Execution plan requires nonempty '+key)

def validate(plan,brief,concept):
    if not isinstance(plan,dict): raise ValueError('Execution plan must be a JSON object')
    for k in ('executive_summary','objectives'):
        if not isinstance(plan.get(k),str) or not plan[k].strip(): raise ValueError('Execution plan requires '+k)
    for k in ('timeline','tasks','activities','resources','budget_breakdown','marketing','operations','risks','event_day_runbook','post_event'):
        require_list(plan,k)
    names={str(a.get('name','')).strip() for a in concept['activities']}
    actual={str(a.get('name','')).strip() for a in plan['activities'] if isinstance(a,dict)}
    if not names.issubset(actual): raise ValueError('Execution plan does not cover every approved activity: '+', '.join(sorted(names-actual)))
    for task in plan['tasks']:
        if not isinstance(task,dict) or not all(str(task.get(k,'')).strip() for k in ('task','owner_role','due_date','priority','status')):
            raise ValueError('Every task needs task, owner_role, due_date, priority, status')
        try: date.fromisoformat(str(task['due_date']))
        except ValueError as exc: raise ValueError('Task due_date must be YYYY-MM-DD') from exc
    for item in plan['timeline']:
        if not isinstance(item,dict) or not all(str(item.get(k,'')).strip() for k in ('date','milestone','description')):
            raise ValueError('Timeline items need date, milestone, description')
        try: date.fromisoformat(str(item['date']))
        except ValueError as exc: raise ValueError('Timeline date must be YYYY-MM-DD') from exc
    # The approved Stage 3 allocations are authoritative. Gemini may supply
    # procurement notes, but it must not rename or redistribute budget lines.
    # Normalize the presentation deterministically rather than spending tokens
    # repeatedly asking the model to reproduce fixed financial data.
    expected_items = concept['budget_allocations']
    notes = {}
    for item in plan['budget_breakdown']:
        if isinstance(item, dict) and isinstance(item.get('category'), str):
            category = item['category'].strip()
            if category and category not in notes:
                notes[category] = str(item.get('procurement_notes') or '').strip()
    plan['budget_breakdown'] = [
        {
            'category': item['category'],
            'amount': float(Decimal(str(item['amount']))),
            'procurement_notes': notes.get(item['category'],
                'Confirm itemized procurement and vendor quotations within this approved allocation.'),
        }
        for item in expected_items
    ]
    total = Decimal(str(concept['budget_total']))
    if abs(sum(Decimal(str(item['amount'])) for item in expected_items) - total) > Decimal('1'):
        raise ValueError('Approved concept budget allocations do not match approved total')
    plan['budget_total']=float(total)
    plan['event_name']=concept['name']
    plan['event_dates']={'start':brief.get('dateStart'),'end':brief.get('dateEnd')}
    plan['venue']=brief.get('location')
    plan['source']='approved_event_concept'
    return plan

def generate(brief,research,concept,feedback=None):
    key=os.getenv('GEMINI_API_KEY','').strip()
    if not key: raise RuntimeError('GEMINI_API_KEY is not configured')
    model=os.getenv('GEMINI_MODEL','gemini-3.1-flash-lite').strip()
    instruction="""You are EpiVibe's professional shopping-mall event execution planner.
    Build a realistic actionable execution plan based on the APPROVED CONCEPT, Event Brief and saved Qloo/Gemini research.
    The APPROVED CONCEPT is authoritative for the event name, activities and budget. The original brief budget may differ.
    Never invent confirmed vendors, named staff, quotations, permissions or research statistics. Mark unknowns as unconfirmed.
    Output ONLY a JSON object with: executive_summary (string), objectives (string),
    timeline (array of {date: YYYY-MM-DD, milestone, description}),
    tasks (array of {task, owner_role, due_date: YYYY-MM-DD, priority, status, dependencies: array of strings}),
    activities (array of {name, execution_steps: array of strings, staffing, equipment: array of strings, vendor_needs: array of strings, schedule, safety_notes}; EXACT approved activity names, cover all),
    resources (array of {resource, quantity_or_scope, responsible_role, confirmation_status}),
    budget_breakdown (array of {category, amount, procurement_notes}; use EXACT category names and amounts from approved budget_allocations),
    marketing (array of {action, channel, timing, owner_role}),
    operations (array of {area, action, owner_role}),
    risks (array of {risk, mitigation, contingency, owner_role}),
    event_day_runbook (array of {date, time, action, owner_role}),
    post_event (array of {action, due_date, owner_role}).
    Include setup, safety, venue coordination, procurement, marketing, operations, breakdown and vendor settlement.
    No KPI dashboard. Dates must be consistent with event dates; do not silently pretend past deadlines are achievable.
    The budget breakdown is the approved category allocation, NOT additional spending. No markdown."""
    if feedback: instruction+='\nPREVIOUS OUTPUT FAILED VALIDATION; FIX: '+feedback
    context={'event_brief':brief,'ai_research':research,'approved_concept':concept,'current_date':date.today().isoformat()}
    payload={'contents':[{'parts':[{'text':instruction+'\nCONTEXT_JSON: '+json.dumps(context,ensure_ascii=False,default=str)[:100000]}]}],
             'generationConfig':{'responseMimeType':'application/json','temperature':0.3}}
    url='https://generativelanguage.googleapis.com/v1beta/models/'+parse.quote(model,safe='')+':generateContent'
    req=request.Request(url,data=json.dumps(payload).encode(),headers={'Content-Type':'application/json','x-goog-api-key':key},method='POST')
    try:
        with request.urlopen(req,timeout=120) as response: data=json.load(response)
    except error.HTTPError as exc: raise RuntimeError('Gemini HTTP '+str(exc.code)+': '+exc.read(500).decode(errors='replace')) from exc
    text=''.join(p.get('text','') for c in data.get('candidates',[]) for p in c.get('content',{}).get('parts',[]) if isinstance(p,dict)).strip()
    if not text: raise RuntimeError('Gemini returned no execution plan')
    try: return json.loads(text)
    except json.JSONDecodeError as exc: raise RuntimeError('Gemini execution plan is not valid JSON') from exc

def run(project_id,brief,research,concept,version):
    try:
        feedback=None
        for _ in range(2):
            result=generate(brief,research,concept,feedback)
            try:
                result=validate(result,brief,concept)
                save(project_id,'completed',version,concept,result)
                return
            except (ValueError,TypeError,KeyError) as exc: feedback=str(exc)
        raise RuntimeError('Execution plan failed validation: '+str(feedback))
    except Exception as exc:
        save(project_id,'failed',version,concept,error_message=str(exc)[:700])

def start(project_id,background_tasks):
    with _LOCK:
        brief,research,concept,version=source(project_id)
        current=get(project_id)
        if current['status']=='running': return current
        if current['status']=='completed' and not current['stale']: return current
        save(project_id,'running',version,concept)
        background_tasks.add_task(run,project_id,brief,research,concept,version)
        return get(project_id)
