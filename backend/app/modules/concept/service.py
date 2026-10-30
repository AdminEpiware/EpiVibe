"""EpiVibe Stage 3A: one evidence-grounded concept, persisted in SQLite."""
import json
import os
import re
import threading
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from urllib import request, error, parse
from app.core.database import connect

_LOCK = threading.Lock()

def now():
    return datetime.now(timezone.utc).isoformat()

def ensure_table():
    with connect() as db:
        db.execute('''CREATE TABLE IF NOT EXISTS event_concepts (
            project_id TEXT PRIMARY KEY, status TEXT NOT NULL, concept_json TEXT,
            error TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
            FOREIGN KEY(project_id) REFERENCES projects(id))''')

def get(project_id):
    ensure_table()
    with connect() as db:
        row = db.execute('SELECT * FROM event_concepts WHERE project_id=?', (project_id,)).fetchone()
    if not row:
        return {'status':'not_started','concept':None,'error':None}
    return {'status':row['status'], 'concept':json.loads(row['concept_json']) if row['concept_json'] else None,
            'error':row['error'], 'updatedAt':row['updated_at']}

def store(project_id, status, concept=None, message=None):
    ensure_table()
    timestamp=now()
    with connect() as db:
        db.execute('''INSERT INTO event_concepts (project_id,status,concept_json,error,created_at,updated_at)
            VALUES (?,?,?,?,?,?) ON CONFLICT(project_id) DO UPDATE SET
            status=excluded.status,concept_json=COALESCE(excluded.concept_json,event_concepts.concept_json),
            error=excluded.error,updated_at=excluded.updated_at''',
            (project_id,status,json.dumps(concept,ensure_ascii=False) if concept is not None else None,message,timestamp,timestamp))

def budget_value(brief):
    raw=str(brief.get('budget','')).replace(',','').replace('₹','').strip()
    try:
        amount=Decimal(raw)
    except InvalidOperation as exc:
        raise ValueError('Event Brief budget must be a numeric amount') from exc
    if amount<=0: raise ValueError('Event Brief budget must be greater than zero')
    return amount

def validate(concept, brief):
    if not isinstance(concept,dict): raise ValueError('Gemini concept must be a JSON object')
    for key in ('name','tagline','overview','why_this_works','expected_outcomes','activities','cultural_insights','budget_allocations'):
        if key not in concept: raise ValueError('Concept missing field: '+key)
    for key in ('name','tagline','overview'):
        if not isinstance(concept[key],str) or not concept[key].strip(): raise ValueError('Invalid concept '+key)
    for key in ('why_this_works','expected_outcomes','activities','cultural_insights','budget_allocations'):
        if not isinstance(concept[key],list) or not concept[key]: raise ValueError('Concept requires nonempty '+key)
    if not 3<=len(concept['activities'])<=8: raise ValueError('Concept must contain 3–8 activities')
    for activity in concept['activities']:
        if not isinstance(activity,dict): raise ValueError('Each activity must be an object')
        for key in ('name','description','target_audience','cultural_rationale','priority','estimated_cost'):
            if key not in activity: raise ValueError('Activity missing '+key)
        if activity['priority'] not in ('Essential','Optional'): raise ValueError('Activity priority must be Essential or Optional')
        try: cost=Decimal(str(activity['estimated_cost']))
        except InvalidOperation as exc: raise ValueError('Invalid activity estimated_cost') from exc
        if cost<0: raise ValueError('Negative activity cost')
    for insight in concept['cultural_insights']:
        if not isinstance(insight,dict) or not all(isinstance(insight.get(k),str) and insight[k].strip() for k in ('evidence','interpretation','recommendation','evidence_reference')):
            raise ValueError('Cultural insights must identify evidence, interpretation, recommendation and evidence_reference')
    total=Decimal('0')
    for item in concept['budget_allocations']:
        if not isinstance(item,dict) or not isinstance(item.get('category'),str) or not item['category'].strip():
            raise ValueError('Invalid budget allocation category')
        try: amount=Decimal(str(item['amount']))
        except (InvalidOperation,KeyError) as exc: raise ValueError('Invalid budget allocation amount') from exc
        if amount<0: raise ValueError('Negative budget allocation')
        total+=amount
    budget=budget_value(brief)
    if abs(total-budget)>Decimal('1'): raise ValueError(f'Budget allocations total {total}, but Event Brief budget is {budget}')
    activity_cost=sum(Decimal(str(a['estimated_cost'])) for a in concept['activities'])
    if activity_cost>budget: raise ValueError('Activity costs exceed total budget')
    # Preserve authoritative brief fields: model may not change them.
    concept['event_details']={k:brief.get(k) for k in ('title','eventType','location','audiences','dateStart','dateEnd','goals','currency','budget')}
    concept['budget_total']=float(budget)
    concept['budget_allocated']=float(total)
    concept['budget_remaining']=float(budget-total)
    return concept

def call_gemini(brief, evidence, feedback=None):
    key=os.getenv('GEMINI_API_KEY','').strip()
    if not key: raise RuntimeError('GEMINI_API_KEY is not configured')
    model=os.getenv('GEMINI_MODEL','gemini-3.1-flash-lite').strip()
    prompt='''You are EpiVibe, an expert shopping-mall event strategist. Generate EXACTLY ONE original, coherent event concept.
    Use the supplied Event Brief as immutable constraints and the supplied Qloo evidence and Gemini research synthesis as the sole external cultural evidence.
    Distinguish Qloo observations from your own inferences. Never invent Qloo statistics, visitor numbers, geographic facts, or supplier quotations.
    Return a JSON OBJECT with:
    name (string), tagline (string), overview (string), why_this_works (array of strings), expected_outcomes (array of strings),
    activities (3–8 objects with name, description, target_audience, cultural_rationale, priority [Essential or Optional], estimated_cost [number], operational_consideration),
    cultural_insights (array of objects with evidence, evidence_reference, interpretation, recommendation; reference identifiable Qloo source details),
    budget_allocations (array of objects with category and amount [number]), assumptions (array of strings), risks (array of strings).
    Budget allocations must sum EXACTLY to the Event Brief budget. Include production, marketing, operations and contingency where appropriate.
    Activity estimated costs are included within budget allocations, NOT additional spending. No hardcoded example activities.
    No Markdown. Return only JSON.'''
    if feedback: prompt+='\nThe previous response failed validation. Correct it: '+feedback
    payload={'contents':[{'parts':[{'text':prompt+'\nINPUT: '+json.dumps({'brief':brief,'research':evidence},ensure_ascii=False,default=str)[:65000]}]}],
             'generationConfig':{'responseMimeType':'application/json','temperature':0.5}}
    url='https://generativelanguage.googleapis.com/v1beta/models/'+parse.quote(model,safe='')+':generateContent'
    req=request.Request(url,data=json.dumps(payload).encode('utf-8'),headers={'Content-Type':'application/json','x-goog-api-key':key},method='POST')
    try:
        with request.urlopen(req,timeout=90) as response: data=json.load(response)
    except error.HTTPError as exc:
        detail=exc.read(500).decode(errors='replace')
        raise RuntimeError(f'Gemini HTTP {exc.code}: {detail}') from exc
    if not isinstance(data,dict): raise RuntimeError('Gemini API returned invalid response')
    parts=[]
    for candidate in data.get('candidates',[]):
        if isinstance(candidate,dict) and isinstance(candidate.get('content'),dict):
            parts.extend(p.get('text','') for p in candidate['content'].get('parts',[]) if isinstance(p,dict))
    text=''.join(parts).strip()
    if not text: raise RuntimeError('Gemini returned no concept text')
    try: result=json.loads(text)
    except json.JSONDecodeError as exc: raise RuntimeError('Gemini concept is not valid JSON') from exc
    return result

def run(project_id, brief, evidence):
    try:
        feedback=None
        for attempt in range(2):
            generated=call_gemini(brief,evidence,feedback)
            try:
                concept=validate(generated,brief)
                store(project_id,'completed',concept)
                return
            except (ValueError,TypeError) as exc:
                feedback=str(exc)
        raise RuntimeError('Gemini concept failed validation after one correction attempt: '+str(feedback))
    except Exception as exc:
        store(project_id,'failed',message=str(exc)[:700])

def start(project_id, background_tasks):
    with _LOCK:
        ensure_table()
        with connect() as db:
            row=db.execute('SELECT brief_json FROM projects WHERE id=?',(project_id,)).fetchone()
            if not row: raise LookupError('Project not found')
            research=db.execute('SELECT status,evidence_json FROM research_runs WHERE project_id=?',(project_id,)).fetchone()
        if not research or research['status']!='completed' or not research['evidence_json']:
            raise ValueError('Complete Stage 2 AI Research before generating a concept')
        existing=get(project_id)
        if existing['status'] in ('running','completed'): return existing
        brief=json.loads(row['brief_json'])
        budget_value(brief)
        evidence=json.loads(research['evidence_json'])
        if not isinstance(evidence,dict) or not evidence.get('qloo') or not evidence.get('synthesis'):
            raise ValueError('Saved research evidence is incomplete')
        store(project_id,'running')
        background_tasks.add_task(run,project_id,brief,evidence)
        return get(project_id)
