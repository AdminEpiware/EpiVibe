import {useEffect,useState,useCallback} from 'react';
import {useParams,useNavigate,Link} from 'react-router-dom';
import {Check,ArrowRight,RotateCcw} from 'lucide-react';
import './research.css';
type Research={status:string;percent:number;step:number;steps:string[];error?:string|null};
const API=(import.meta.env.VITE_API_BASE_URL||'').replace(/\/$/,'');
const activities=['Understanding Your Event','Discovering Cultural Affinities with Qloo','Understanding Audience Preferences','Identifying Event Opportunities','Preparing Your Event Intelligence'];
export default function ResearchPage(){
 const {id}=useParams();const navigate=useNavigate();const [state,setState]=useState<Research>({status:'not_started',percent:0,step:0,steps:activities});const [busy,setBusy]=useState(false);const [message,setMessage]=useState('');
 const load=useCallback(async()=>{if(!id)return;try{const r=await fetch(`${API}/api/projects/${id}/research`);if(!r.ok)throw Error(`HTTP ${r.status}`);setState(await r.json());setMessage('')}catch(e){setMessage(String(e))}},[id]);
 const begin=useCallback(async()=>{if(!id)return;setBusy(true);try{const r=await fetch(`${API}/api/projects/${id}/research/start`,{method:'POST'});if(!r.ok)throw Error(await r.text());setState(await r.json());setMessage('')}catch(e){setMessage(String(e))}finally{setBusy(false)}},[id]);
 useEffect(()=>{void load()},[load]);
 useEffect(()=>{if(state.status!=='running')return;const t=setInterval(()=>void load(),1200);return()=>clearInterval(t)},[state.status,load]);
 // Research begins on arrival from a validated Event Brief. Revisiting a completed run does not restart it.
 useEffect(()=>{if(state.status==='not_started'&&!busy&&!message)void begin()},[state.status,busy,message,begin]);
 const done=state.status==='completed';const failed=state.status==='failed';const running=state.status==='running';
 return <div className="epi-research"><div className="epi-research-steps">{['Event Brief','AI Research','Event Concept','Execution Plan'].map((name,i)=><div className={'epi-research-step '+(i===1?'active':i===0?'done':'')} key={name}><span>{i===0?<Check size={18}/>:i+1}</span><b>{name}</b></div>)}</div>
 <h1>{done?'AI Research Completed':failed?'AI Research Needs Attention':'AI Research in Progress'}</h1><p className="epi-research-sub">{done?'Your cultural and audience intelligence is ready for event concept generation.':failed?'Research stopped. Review the error and retry when ready.':'Analyzing cultural insights, audience interests, and relevant opportunities for your event.'}</p>
 <div className="epi-research-grid"><div className="epi-research-visual"><div className={'epi-research-orb '+(running?'pulse':'')}><div className="epi-research-bars"><i/><i/><i/></div><strong>{done?'Research Complete':failed?'Research Paused':'Researching Event Insights...'}</strong></div><div className="epi-research-meter"><div className="epi-research-track"><div style={{width:`${state.percent}%`}}/></div><strong>{state.percent}%</strong></div></div>
 <section className="epi-research-panel"><h2>What's Happening Now</h2>{activities.map((name,i)=>{const complete=done||state.step>i+1||(running&&state.step===i+1);const active=running&&state.step===i;return <div className="epi-research-activity" key={name}><span className={complete?'complete':active?'processing':'pending'}>{complete?<Check size={18}/>:null}</span><p>{name}</p></div>})}{failed&&<p className="epi-research-error" role="alert">{state.error||'Research failed'}</p>}</section></div>
 <div className="epi-research-actions"><Link to={`/projects/${id}`}>← Project Overview</Link>{failed?<button onClick={()=>void begin()} disabled={busy}><RotateCcw size={18}/> Retry Research</button>:<button disabled={!done} onClick={()=>navigate(`/projects/${id}/concept`)}>Generate Event Concept <ArrowRight size={18}/></button>}</div>{message&&<p className="epi-research-error" role="alert">{message}</p>}</div>
}
