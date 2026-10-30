import json, os, threading, urllib.request, urllib.parse, urllib.error
from datetime import datetime, timezone
from app.core.database import connect

STEPS = ['Understanding Your Event','Discovering Cultural Affinities with Qloo','Understanding Audience Preferences','Identifying Event Opportunities','Preparing Your Event Intelligence']
PERCENT = [15,45,65,85,100]
_lock = threading.Lock()

def stamp(): return datetime.now(timezone.utc).isoformat()
def get(project_id):
    with connect() as db:
        row=db.execute('SELECT * FROM research_runs WHERE project_id=?',(project_id,)).fetchone()
    if not row: return {'status':'not_started','percent':0,'step':0,'steps':STEPS,'error':None}
    return {'status':row['status'],'percent':row['percent'],'step':row['step'],'steps':STEPS,'error':row['error'],'updatedAt':row['updated_at']}

def save(project_id,status,step,error=None,evidence=None):
    percent=PERCENT[step-1] if step else 0
    with connect() as db:
        db.execute("INSERT INTO research_runs(project_id,status,step,percent,error,evidence_json,updated_at) VALUES(?,?,?,?,?,?,?) ON CONFLICT(project_id) DO UPDATE SET status=excluded.status,step=excluded.step,percent=excluded.percent,error=excluded.error,evidence_json=COALESCE(excluded.evidence_json,research_runs.evidence_json),updated_at=excluded.updated_at",(project_id,status,step,percent,error,json.dumps(evidence) if evidence is not None else None,stamp()))

def set_project_status(project_id,status):
    with connect() as db:
        row=db.execute('SELECT brief_json FROM projects WHERE id=?',(project_id,)).fetchone()
        if not row:return
        brief=json.loads(row['brief_json']);brief['status']=status;brief['updatedAt']=stamp()
        db.execute('UPDATE projects SET status=?,brief_json=?,updated_at=? WHERE id=?',(status,json.dumps(brief),brief['updatedAt'],project_id))

def request_json(url,headers=None,payload=None):
    body=json.dumps(payload).encode() if payload is not None else None
    req=urllib.request.Request(url,data=body,headers=headers or {},method='POST' if body else 'GET')
    try:
        with urllib.request.urlopen(req,timeout=35) as res:return json.loads(res.read().decode())
    except urllib.error.HTTPError as exc:
        detail=exc.read(400).decode(errors='replace');raise RuntimeError(f'External API returned HTTP {exc.code}: {detail}') from exc

def qloo_search(brief):
    key=os.getenv('QLOO_API_KEY','').strip()
    if not key:raise RuntimeError('QLOO_API_KEY is not configured in the backend environment')
    base=os.getenv('QLOO_API_BASE','https://hackathon.api.qloo.com').rstrip('/')
    terms=[brief.get('eventType',''),brief.get('title','')]+brief.get('audiences',[])
    query=' '.join(x for x in terms if x).strip()
    # The hackathon /search endpoint supports a query parameter; keep the original response as evidence.
    url=base+'/search?'+urllib.parse.urlencode({'query':query[:160]})
    result=request_json(url,{'X-Api-Key':key,'Accept':'application/json'})
    if not result:raise RuntimeError('Qloo returned no research evidence')
    return {'endpoint':'/search','query':query[:160],'response':result}

def gemini_synthesis(brief,qloo):
    key=os.getenv('GEMINI_API_KEY','').strip()
    if not key:raise RuntimeError('GEMINI_API_KEY is not configured in the backend environment')
    model=os.getenv('GEMINI_MODEL','gemini-3.1-flash-lite').strip()
    prompt=('You are EpiVibe research analyst. Use ONLY the supplied Qloo response as externally supported cultural evidence. '
            'Audience descriptions are hypotheses, not measured audience facts. No unverified geographic or trend claims. '
            'Return a JSON object with keys audience_insights (array), opportunities (array), research_summary (string), '
            'evidence_notes (array). Each opportunity should cite which Qloo evidence supports it; distinguish inference. '
            'Do not create the final event concept. Input: '+json.dumps({'brief':brief,'qloo':qloo},ensure_ascii=False)[:24000])
    url='https://generativelanguage.googleapis.com/v1beta/models/'+urllib.parse.quote(model,safe='')+':generateContent'
    data=request_json(url,{'Content-Type':'application/json','x-goog-api-key':key},{'contents':[{'parts':[{'text':prompt}]}],'generationConfig':{'responseMimeType':'application/json','responseSchema':{'type':'OBJECT','properties':{'audience_insights':{'type':'ARRAY','items':{'type':'STRING'}},'opportunities':{'type':'ARRAY','items':{'type':'OBJECT','properties':{'opportunity':{'type':'STRING'},'qloo_evidence':{'type':'STRING'},'inference':{'type':'STRING'}},'required':['opportunity','qloo_evidence','inference']}},'research_summary':{'type':'STRING'},'evidence_notes':{'type':'ARRAY','items':{'type':'STRING'}}},'required':['audience_insights','opportunities','research_summary','evidence_notes']}}})
    if not isinstance(data, dict):
        raise RuntimeError('Gemini API returned an unexpected response format')
    text_parts = []
    for candidate in data.get('candidates', []):
        if not isinstance(candidate, dict):
            continue
        content = candidate.get('content')
        if not isinstance(content, dict):
            continue
        for part in content.get('parts', []):
            if isinstance(part, dict) and isinstance(part.get('text'), str):
                text_parts.append(part['text'])
    text = ''.join(text_parts)
    if not text:raise RuntimeError('Gemini returned no research synthesis')
    try:
        synthesis = json.loads(text)
    except json.JSONDecodeError as exc:
        raise RuntimeError('Gemini did not return valid JSON') from exc
    if not isinstance(synthesis, dict):
        raise RuntimeError(f'Gemini research synthesis must be a JSON object; received {type(synthesis).__name__}')
    required = {'audience_insights': list, 'opportunities': list,
                'research_summary': str, 'evidence_notes': list}
    for field, expected_type in required.items():
        if not isinstance(synthesis.get(field), expected_type):
            raise RuntimeError(f'Gemini research synthesis field {field!r} must be {expected_type.__name__}')
    if not synthesis['opportunities']:
        raise RuntimeError('Gemini research synthesis returned no event opportunities')
    return synthesis

def run(project_id,brief):
    step=0
    try:
        if not brief.get('title') or not brief.get('eventType') or not brief.get('audiences') or not brief.get('goals') or not brief.get('budget'):
            raise RuntimeError('Event Brief is incomplete; complete mandatory fields before research')
        step=1;save(project_id,'running',step)
        step=2;qloo=qloo_search(brief);save(project_id,'running',step)
        step=3;synthesis=gemini_synthesis(brief,qloo);save(project_id,'running',step)
        step=4
        if not isinstance(synthesis.get('opportunities'),list):raise RuntimeError('Research synthesis lacks event opportunities')
        save(project_id,'running',step)
        step=5;save(project_id,'completed',step,evidence={'qloo':qloo,'synthesis':synthesis,'brief_snapshot':brief});set_project_status(project_id,'Research Completed')
    except Exception as exc:
        save(project_id,'failed',max(0,step-1),str(exc)[:600]);set_project_status(project_id,'Action Required')

def start(project_id,background_tasks):
    with _lock:
        with connect() as db:
            row=db.execute('SELECT brief_json FROM projects WHERE id=?',(project_id,)).fetchone()
            if not row:raise LookupError('Project not found')
            state=db.execute('SELECT status FROM research_runs WHERE project_id=?',(project_id,)).fetchone()
            if state and state['status']=='running':return get(project_id)
            brief=json.loads(row['brief_json'])
            save(project_id,'running',0);set_project_status(project_id,'Researching')
    background_tasks.add_task(run,project_id,brief)
    return get(project_id)
