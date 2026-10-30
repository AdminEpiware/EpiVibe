"""Proposal-first AI refinement. A proposal never overwrites the accepted concept."""
import json, os, threading
from urllib import request, error, parse
from app.core.database import connect
from app.modules.concept import service as concept_service

LOCK=threading.RLock()

def setup():
    with connect() as db:
        db.execute('''CREATE TABLE IF NOT EXISTS concept_versions(project_id TEXT NOT NULL, version INTEGER NOT NULL, concept_json TEXT NOT NULL, created_at TEXT NOT NULL, PRIMARY KEY(project_id,version))''')
        db.execute('''CREATE TABLE IF NOT EXISTS concept_refinement_sessions(project_id TEXT PRIMARY KEY, base_version INTEGER NOT NULL, proposal_json TEXT, messages_json TEXT NOT NULL DEFAULT '[]', updated_at TEXT NOT NULL)''')

def ensure_baseline(project_id):
    setup()
    current=concept_service.get(project_id)
    if current['status']!='completed' or not current['concept']:
        raise ValueError('Generate and complete the event concept first')
    with connect() as db:
        row=db.execute('SELECT MAX(version) AS v FROM concept_versions WHERE project_id=?',(project_id,)).fetchone()
        if row['v'] is None:
            db.execute('INSERT INTO concept_versions VALUES (?,?,?,?)',(project_id,1,json.dumps(current['concept'],ensure_ascii=False),concept_service.now()))
            return 1
        return row['v']

def state(project_id):
    version=ensure_baseline(project_id)
    with connect() as db:
        row=db.execute('SELECT * FROM concept_refinement_sessions WHERE project_id=?',(project_id,)).fetchone()
        versions=db.execute('SELECT version,created_at FROM concept_versions WHERE project_id=? ORDER BY version DESC',(project_id,)).fetchall()
    return {'version':version,'proposal':json.loads(row['proposal_json']) if row and row['proposal_json'] else None,'messages':json.loads(row['messages_json']) if row else [],'proposalBaseVersion':row['base_version'] if row else None,'versions':[dict(x) for x in versions]}

def _gemini(brief, evidence, current, prior, messages):
    key=os.getenv('GEMINI_API_KEY','').strip()
    if not key: raise RuntimeError('GEMINI_API_KEY is not configured in backend')
    model=os.getenv('GEMINI_MODEL','gemini-3.1-flash-lite').strip()
    instruction="""You are EpiVibe, a thoughtful, concise event-planning consultant chatting naturally with a user. Reply to the LATEST user message using the full conversation history, Event Brief, saved Qloo response, Gemini research synthesis and current approved concept. Never repeat questions already answered. The research includes original evidence and interpretations; preserve their distinction. Ask one focused question if an essential target is missing (e.g. 'reduce production costs' without amount or desired result); offer short practical suggestions. When enough information exists, you may propose changes immediately, unless the user is discussing options or asking a question rather than requesting a revision. Never claim a proposal exists unless you provide one. Do not force an extra confirmation when the request is already clear. Be conversational and brief, preferably 1-3 sentences.
Respond with a JSON OBJECT with keys: reply (string), action ('chat' or 'proposal'), concept (object or null), change_summary (array of strings). For chat, concept MUST be null. For proposal, return a COMPLETE concept object matching the existing concept schema (name, tagline, overview, why_this_works, expected_outcomes, activities, cultural_insights, budget_allocations, assumptions, risks), editing the WORKING PROPOSAL if present, otherwise CURRENT concept. Preserve every unrelated field and list item exactly. Preserve title/tagline unless explicitly asked to rename. Do not invent Qloo evidence, statistics or local inferences. Budget allocations must sum to the target total; activity costs cannot exceed total. A user can explicitly change the WORKING concept total budget; return concept.budget_total equal to the requested new total, and allocate accordingly. The original Event Brief is historical and must remain unchanged. Otherwise retain the CURRENT APPROVED CONCEPT total (not the historical Event Brief total). A category reduction does NOT necessarily mean a reduction in overall budget; ask where savings should go if unclear. Do not silently change event date, venue, target audience or overall budget. Only modify fields necessary to satisfy the request. Change summaries must describe ACTUAL modifications, not generic marketing claims. Return JSON only."""
    payload={'contents':[{'parts':[{'text':instruction+'\nCONTEXT: '+json.dumps({'brief':brief,'research':evidence,'current_concept':current,'working_proposal':prior,'conversation':messages},ensure_ascii=False,default=str)}]}],'generationConfig':{'responseMimeType':'application/json','temperature':0.25}}
    url='https://generativelanguage.googleapis.com/v1beta/models/'+parse.quote(model,safe='')+':generateContent'
    req=request.Request(url,data=json.dumps(payload).encode(),headers={'Content-Type':'application/json','x-goog-api-key':key},method='POST')
    try:
        with request.urlopen(req,timeout=100) as response: data=json.load(response)
    except error.HTTPError as exc: raise RuntimeError(f'Gemini HTTP {exc.code}: '+exc.read(350).decode(errors='replace')) from exc
    text=''.join(p.get('text','') for c in data.get('candidates',[]) for p in c.get('content',{}).get('parts',[]) if isinstance(p,dict))
    if not text: raise RuntimeError('Gemini returned an empty response')
    try: return json.loads(text)
    except json.JSONDecodeError as exc: raise RuntimeError('Gemini returned invalid JSON') from exc

def _save_session(project_id,version,proposal,messages):
    with connect() as db:
        db.execute("INSERT INTO concept_refinement_sessions(project_id,base_version,proposal_json,messages_json,updated_at) VALUES (?,?,?,?,?) ON CONFLICT(project_id) DO UPDATE SET base_version=excluded.base_version,proposal_json=excluded.proposal_json,messages_json=excluded.messages_json,updated_at=excluded.updated_at",(project_id,version,json.dumps(proposal,ensure_ascii=False) if proposal is not None else None,json.dumps(messages,ensure_ascii=False),concept_service.now()))

def propose(project_id,message):
    if not message or not message.strip(): raise ValueError('Enter a message')
    if len(message)>2500: raise ValueError('Message is too long (maximum 2500 characters)')
    with LOCK:
        version=ensure_baseline(project_id)
        with connect() as db:
            session=db.execute('SELECT * FROM concept_refinement_sessions WHERE project_id=?',(project_id,)).fetchone()
            briefrow=db.execute('SELECT brief_json FROM projects WHERE id=?',(project_id,)).fetchone()
            research=db.execute('SELECT evidence_json FROM research_runs WHERE project_id=?',(project_id,)).fetchone()
        if not briefrow or not research or not research['evidence_json']: raise ValueError('Event Brief or research evidence is missing')
        brief=json.loads(briefrow['brief_json']);evidence=json.loads(research['evidence_json'])
        messages=json.loads(session['messages_json']) if session and session['base_version']==version else []
        prior=json.loads(session['proposal_json']) if session and session['base_version']==version and session['proposal_json'] else None
        current=concept_service.get(project_id)['concept']
        new_messages=messages+[{'role':'user','text':message.strip()}]
        response=_gemini(brief,evidence,current,prior,new_messages)
        if not isinstance(response,dict): raise RuntimeError('Gemini returned an invalid response')
        reply=response.get('reply')
        if not isinstance(reply,str) or not reply.strip(): raise RuntimeError('Gemini response is missing reply')
        proposal=prior
        if response.get('action')=='proposal':
            candidate=response.get('concept')
            if not isinstance(candidate,dict): raise RuntimeError('Gemini did not provide a concept proposal')
            # The model may propose a new total only when the conversation explicitly requests it.
            # A working-budget change is staged; the original Event Brief remains unchanged.
            target=candidate.get('budget_total',current.get('budget_total'))
            try: target=float(target)
            except (ValueError,TypeError): raise ValueError('Invalid proposed budget')
            old=float(current.get('budget_total') or concept_service.budget_value(brief))
            budget_change=abs(target-old)>1
            latest=message.lower()
            # Scope intent to the current request, not unrelated historical refinements.
            total_terms=('total budget','overall budget','event budget','entire budget','total cost','overall cost','total expense','total spending')
            explicit_total=any(x in latest for x in total_terms)
            # A numeric answer to Gemini's immediately preceding budget question is also valid.
            previous=messages[-1] if messages else {}
            if not explicit_total and previous.get('role')=='assistant' and any(x in previous.get('text','').lower() for x in total_terms):
                explicit_total=any(ch.isdigit() for ch in latest)
            conversation_text=latest
            if budget_change and not explicit_total:
                new_messages.append({'role':'assistant','text':'Do you want to change the overall event budget, or only redistribute costs between categories?'})
                _save_session(project_id,version,prior,new_messages)
                return state(project_id)
            if target<=0: raise ValueError('Budget must be greater than zero')
            # Validate every revision against the proposed WORKING concept budget,
            # not the historical Event Brief budget. The brief is never modified.
            draft_brief=dict(brief)
            draft_brief['budget']=target
            candidate=concept_service.validate(candidate,draft_brief)
            identity_change=any(term in conversation_text for term in ('rename','change the name','change title','new name','new title','change the tagline','new tagline','completely new concept','entirely new concept','different concept'))
            if not identity_change:
                candidate['name']=current['name'];candidate['tagline']=current['tagline']
            research_change=any(term in conversation_text for term in ('change cultural insight','update cultural insight','revise cultural insight','update qloo evidence'))
            if not research_change: candidate['cultural_insights']=current['cultural_insights']
            proposal=candidate
            changes=response.get('change_summary',[])
            changes=[str(x)[:240] for x in changes if isinstance(x,str)][:5] if isinstance(changes,list) else []
            new_messages.append({'role':'assistant','text':reply.strip(),'changes':changes})
        elif response.get('action')=='chat':
            new_messages.append({'role':'assistant','text':reply.strip()})
        else: raise RuntimeError('Gemini returned an unknown action')
        _save_session(project_id,version,proposal,new_messages)
        return state(project_id)

def discard(project_id):
    with LOCK:
        ensure_baseline(project_id)
        with connect() as db: db.execute('DELETE FROM concept_refinement_sessions WHERE project_id=?',(project_id,))
        return state(project_id)

def apply(project_id):
    with LOCK:
        version=ensure_baseline(project_id)
        with connect() as db:
            session=db.execute('SELECT * FROM concept_refinement_sessions WHERE project_id=?',(project_id,)).fetchone()
            if not session or not session['proposal_json']: raise ValueError('There is no proposed concept to apply')
            if session['base_version']!=version: raise ValueError('Concept changed. Discard and start a new refinement')
            briefrow=db.execute('SELECT brief_json FROM projects WHERE id=?',(project_id,)).fetchone()
        brief=json.loads(briefrow['brief_json'])
        candidate=json.loads(session['proposal_json'])
        target=candidate.get('budget_total')
        validation_brief=dict(brief)
        if target is None:
            target=concept_service.get(project_id)['concept'].get('budget_total')
        if target is None:
            target=concept_service.budget_value(brief)
        validation_brief['budget']=float(target)
        proposal=concept_service.validate(candidate,validation_brief)
        with connect() as db:
            db.execute('INSERT INTO concept_versions VALUES (?,?,?,?)',(project_id,version+1,json.dumps(proposal,ensure_ascii=False),concept_service.now()))
            db.execute('UPDATE event_concepts SET concept_json=?,status=?,error=NULL,updated_at=? WHERE project_id=?',(json.dumps(proposal,ensure_ascii=False),'completed',concept_service.now(),project_id))
            db.execute('DELETE FROM concept_refinement_sessions WHERE project_id=?',(project_id,))
        return state(project_id)
