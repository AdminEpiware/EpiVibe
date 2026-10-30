import { useCallback, useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { ArrowLeft, ArrowRight, Check, RefreshCw, Sparkles } from 'lucide-react';
import './concept.css';

type Item = Record<string, unknown>;
type Concept = {
  name?: string; tagline?: string; overview?: string;
  why_this_works?: string[]; expected_outcomes?: string[];
  activities?: Item[]; cultural_insights?: Item[];
  budget_allocations?: Item[]; assumptions?: string[]; risks?: string[];
  event_details?: Item; budget_total?: number; budget_allocated?: number; budget_remaining?: number;
};
type Result = { status?: string; concept?: Concept | null; error?: string | null };
type Tab = 'overview' | 'activities' | 'insights' | 'budget';
const API = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '');
const asText = (v: unknown): string => typeof v === 'string' ? v : typeof v === 'number' ? String(v) : '';
const money = (v: unknown, currency: string) => typeof v === 'number' && Number.isFinite(v) ? new Intl.NumberFormat('en-IN', {style:'currency',currency:currency || 'INR', maximumFractionDigits:0}).format(v) : 'Not provided';
const textArray = (v: unknown) => Array.isArray(v) ? v.filter((x): x is string => typeof x === 'string') : [];
const items = (v: unknown): Item[] => Array.isArray(v) ? v.filter((x): x is Item => !!x && typeof x === 'object' && !Array.isArray(x)) : [];
const textField = (o: Item, ...keys: string[]) => keys.map(k => asText(o[k])).find(Boolean) || '';

export default function ConceptContent() {
  const { id } = useParams();
  const [result, setResult] = useState<Result | null>(null);
  const [tab, setTab] = useState<Tab>('overview');
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState('');
  const load = useCallback(async () => {
    if (!id) return;
    try {
      const response = await fetch(`${API}/api/projects/${encodeURIComponent(id)}/concept`);
      if (!response.ok) throw new Error(`Could not load concept (HTTP ${response.status})`);
      const data: Result = await response.json();
      setResult(data); setError('');
    } catch (e) { setError(e instanceof Error ? e.message : String(e)); }
    finally { setLoading(false); }
  }, [id]);
  useEffect(() => { void load(); }, [load]);
  useEffect(() => {
    if (result?.status !== 'running') return;
    const timer = window.setInterval(() => void load(), 1800);
    return () => window.clearInterval(timer);
  }, [result?.status, load]);
  const generate = async () => {
    if (!id || generating) return;
    setGenerating(true); setError('');
    try {
      const response = await fetch(`${API}/api/projects/${encodeURIComponent(id)}/concept/generate`, {method:'POST'});
      if (!response.ok) throw new Error(await response.text());
      setResult(await response.json());
    } catch (e) { setError(e instanceof Error ? e.message : String(e)); }
    finally { setGenerating(false); }
  };
  const concept = result?.concept;
  const details = concept?.event_details || {};
  const currency = textField(details, 'currency') || 'INR';
  const allocations = items(concept?.budget_allocations);
  const budgetTotal = concept?.budget_total;
  const allocated = concept?.budget_allocated;
  const remaining = concept?.budget_remaining;
  const tabs: {id: Tab; label: string}[] = [
    {id:'overview',label:'Overview'}, {id:'activities',label:'Activities'},
    {id:'insights',label:'Cultural Insights'}, {id:'budget',label:'Budget'}
  ];
  return <main className="epi-concept">
    <nav className="epi-concept-progress" aria-label="Event creation progress">
      {['Event Brief','AI Research','Event Concept','Execution Plan'].map((label,i) =>
        <div key={label} className={'epi-concept-progress-item '+(i<2?'completed':i===2?'current':'future')}>
          <span className="epi-concept-step-number">{i<2?<Check size={17}/>:i+1}</span><span>{label}</span>
        </div>)}
    </nav>
    <div className="epi-concept-back"><Link to={`/projects/${id}/research`}><ArrowLeft size={16}/> Back to AI Research</Link></div>
    {loading ? <section className="epi-concept-state">Loading saved AI concept…</section> : error ?
      <section className="epi-concept-state"><h2>Unable to load concept</h2><p role="alert">{error}</p><button onClick={()=>void load()}><RefreshCw size={16}/> Retry</button></section> :
      result?.status === 'running' ? <section className="epi-concept-state"><Sparkles/> <h2>AI is generating your event concept</h2><p>Using saved Qloo research and your Event Brief. This page updates automatically.</p></section> :
      !concept ? <section className="epi-concept-state"><h2>{result?.status === 'failed' ? 'Concept generation needs attention' : 'Your concept is ready to generate'}</h2><p>{result?.error || 'Generate one tailored event concept using the completed research.'}</p><button onClick={()=>void generate()} disabled={generating}>{generating?'Starting…':'Generate Event Concept'} <ArrowRight size={16}/></button></section> : <>
        <header className="epi-concept-heading"><div><div className="epi-concept-kicker"><Sparkles size={15}/> AI Recommended Concept</div><h1>{concept.name || 'Untitled Event Concept'}</h1><p>{concept.tagline || concept.overview || 'AI-generated event concept'}</p></div></header>
        <div className="epi-concept-layout"><div className="epi-concept-primary">
          <div className="epi-concept-tabs" role="tablist" aria-label="Concept details">{tabs.map(t=><button key={t.id} role="tab" aria-selected={tab===t.id} className={tab===t.id?'selected':''} onClick={()=>setTab(t.id)}>{t.label}</button>)}</div>
          <section className="epi-concept-card" role="tabpanel">
            {tab==='overview' && <>
              <div className="epi-concept-overview-top"><div><h2>Concept Overview</h2><p>{concept.overview || 'No overview was returned by the AI.'}</p></div><aside className="epi-concept-facts">
                {['title','location','dateStart','dateEnd'].map(k=>textField(details,k)&&<div key={k}><span>{k==='dateStart'?'Start Date':k==='dateEnd'?'End Date':k==='location'?'Venue':'Event'}</span><strong>{textField(details,k)}</strong></div>)}
                {Array.isArray(details.audiences)&&<div><span>Audience</span><strong>{details.audiences.map(asText).filter(Boolean).join(', ')}</strong></div>}
                <div><span>Total Budget</span><strong>{money(budgetTotal ?? details.budget,currency)}</strong></div>
              </aside></div>
              <div className="epi-concept-columns"><div className="epi-concept-subcard"><h3>Why This Works</h3>{textArray(concept.why_this_works).length ? <ul>{textArray(concept.why_this_works).map((x,i)=><li key={i}><Check size={17}/>{x}</li>)}</ul> : <p>No rationale provided.</p>}</div><div className="epi-concept-subcard"><h3>Expected Outcomes</h3>{textArray(concept.expected_outcomes).length ? <ul>{textArray(concept.expected_outcomes).map((x,i)=><li key={i}><Check size={17}/>{x}</li>)}</ul> : <p>No expected outcomes provided.</p>}</div></div>
            </>}
            {tab==='activities' && <><h2>AI-Recommended Activities</h2><p className="epi-concept-muted">Experiences designed around the Event Brief and cultural research.</p>{items(concept.activities).length ? <div className="epi-concept-list">{items(concept.activities).map((a,i)=><article key={i} className="epi-concept-list-card"><div className="epi-concept-row"><h3>{textField(a,'name','title')||`Activity ${i+1}`}</h3>{textField(a,'priority')&&<span className="epi-concept-pill">{textField(a,'priority')}</span>}</div><p>{textField(a,'description')}</p>{textField(a,'target_audience')&&<p><b>Audience:</b> {textField(a,'target_audience')}</p>}{textField(a,'cultural_rationale')&&<p><b>Cultural rationale:</b> {textField(a,'cultural_rationale')}</p>}{typeof a.estimated_cost==='number'&&<p><b>Estimated cost:</b> {money(a.estimated_cost,currency)}</p>}{textField(a,'operational_consideration')&&<p><b>Operations:</b> {textField(a,'operational_consideration')}</p>}</article>)}</div>:<p>No activities were returned.</p>}</>}
            {tab==='insights' && <><h2>Cultural Intelligence</h2><p className="epi-concept-muted">AI interpretation of the saved Qloo research. Evidence references should be validated against source data.</p>{items(concept.cultural_insights).length ? <div className="epi-concept-list">{items(concept.cultural_insights).map((insight,i)=><article className="epi-concept-list-card" key={i}><h3>Insight {i+1}</h3><p><b>Evidence:</b> {textField(insight,'evidence')||'Not provided'}</p><p><b>Interpretation:</b> {textField(insight,'interpretation')||'Not provided'}</p>{textField(insight,'evidence_reference')&&<small>Qloo reference: {textField(insight,'evidence_reference')}</small>}</article>)}</div>:<p>No cultural insights were returned.</p>}</>}
            {tab==='budget' && <><h2>Budget Allocation</h2><div className="epi-concept-budget-stats"><div><span>Total</span><strong>{money(budgetTotal,currency)}</strong></div><div><span>Allocated</span><strong>{money(allocated,currency)}</strong></div><div><span>Remaining</span><strong>{money(remaining,currency)}</strong></div></div>{allocations.length ? <div className="epi-concept-list">{allocations.map((a,i)=><div className="epi-concept-budget-row" key={i}><span>{textField(a,'category','name')||`Category ${i+1}`}</span><strong>{money(a.amount,currency)}</strong></div>)}</div>:<p>No budget breakdown was returned.</p>}{textArray(concept.assumptions).length>0&&<div className="epi-concept-note"><h3>Assumptions</h3><ul>{textArray(concept.assumptions).map((x,i)=><li key={i}>{x}</li>)}</ul></div>}{textArray(concept.risks).length>0&&<div className="epi-concept-note"><h3>Risks</h3><ul>{textArray(concept.risks).map((x,i)=><li key={i}>{x}</li>)}</ul></div>}</>}
          </section>
        </div><aside className="epi-concept-side"><section className="epi-concept-sidecard"><h2>Next Steps</h2><p>Move from strategy to practical event execution.</p><button disabled title="Available when Stage 4 is implemented">Generate Execution Plan <ArrowRight size={18}/></button><Link className="epi-refine-entry" to={`/projects/${id}/refine`}>Refine with AI <ArrowRight size={18}/></Link><small>Execution planning is coming in Stage 4.</small></section><section className="epi-concept-sidecard"><h3>Concept Status</h3><p><Check size={17}/> Saved AI-generated concept</p><p><Check size={17}/> Based on completed AI Research</p></section></aside></div>
      </>}
  </main>;
}
