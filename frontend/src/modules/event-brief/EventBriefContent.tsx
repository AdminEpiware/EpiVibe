import {useEffect,useLayoutEffect,useRef,useState} from 'react';
import {createPortal} from 'react-dom';
import {useNavigate,useParams} from 'react-router-dom';
import {ArrowRight,Save,ChevronDown} from 'lucide-react';
import EventProgress from '../../shared/workflow/EventProgress';
import {eventTypes,audiences,goals,currencies} from './eventBrief.config';
import {emptyBrief,type EventBrief} from './eventBrief.types';
import {validateBrief} from './eventBrief.validation';
import {getProject,saveProject,migrateLocalDrafts,getLocalBrief} from './eventBrief.api';
import './eventBrief.css';

function MultiDropdown({label, value, options, onToggle}: {label:string;value:string[];options:string[];onToggle:(option:string)=>void}) {
 const [open,setOpen]=useState(false);
 const trigger=useRef<HTMLButtonElement>(null);
 const menu=useRef<HTMLDivElement>(null);
 const [placement,setPlacement]=useState({top:0,left:0,width:0,maxHeight:220});
 useLayoutEffect(()=>{
  if(!open)return;
  const position=()=>{
   const rect=trigger.current?.getBoundingClientRect();if(!rect)return;
   const spaceBelow=window.innerHeight-rect.bottom-12;
   const spaceAbove=rect.top-12;
   const height=Math.min(options.length*38+14,240);
   const above=spaceBelow<height && spaceAbove>spaceBelow;
   const available=Math.max(90,(above?spaceAbove:spaceBelow)-8);
   const maxHeight=Math.min(height,available);
   setPlacement({top:above?rect.top-maxHeight-5:rect.bottom+5,left:rect.left,width:rect.width,maxHeight});
  };
  position();window.addEventListener('resize',position);window.addEventListener('scroll',position,true);
  return()=>{window.removeEventListener('resize',position);window.removeEventListener('scroll',position,true)};
 },[open,options.length]);
 useEffect(()=>{
  if(!open)return;
  const close=(event:PointerEvent)=>{const target=event.target as Node;if(!trigger.current?.contains(target)&&!menu.current?.contains(target))setOpen(false)};
  const escape=(event:KeyboardEvent)=>{if(event.key==='Escape'){setOpen(false);trigger.current?.focus()}};
  document.addEventListener('pointerdown',close);document.addEventListener('keydown',escape);
  return()=>{document.removeEventListener('pointerdown',close);document.removeEventListener('keydown',escape)};
 },[open]);
 return <div className="epi-brief-multiselect">
  <button ref={trigger} type="button" className="epi-brief-multi-trigger" aria-haspopup="listbox" aria-expanded={open} onClick={()=>setOpen(v=>!v)}>
   <span className={value.length?'epi-brief-selected':'epi-brief-placeholder'}>{value.length?value.join(', '):`Select ${label.toLowerCase()}`}</span><ChevronDown size={17} className={open?'epi-brief-chevron-open':''}/>
  </button>
  {open&&createPortal(<div ref={menu} className="epi-brief-floating-menu" role="group" aria-label={label} style={{position:'fixed',top:placement.top,left:placement.left,width:placement.width,maxHeight:placement.maxHeight,zIndex:99999}}>
   {options.map(option=><label key={option} className={value.includes(option)?'selected':''}><input type="checkbox" checked={value.includes(option)} onChange={()=>onToggle(option)}/><span>{option}</span></label>)}
  </div>,document.body)}
 </div>;
}
type Field = keyof EventBrief;
export default function EventBriefContent(){
 const {id}=useParams();const navigate=useNavigate();
 const [brief,setBrief]=useState<EventBrief>(()=>id?getLocalBrief(id)||emptyBrief():emptyBrief());
 const [errors,setErrors]=useState<Record<string,string>>({});const [notice,setNotice]=useState('');const [dirty,setDirty]=useState(false);
 useEffect(()=>{let active=true;setErrors({});setNotice('');setDirty(false);
  migrateLocalDrafts().then(()=>id?getProject(id):undefined).then(saved=>{if(active)setBrief(saved||emptyBrief())}).catch(error=>{if(active){setNotice('Unable to load projects: '+String(error.message||error));if(id)setBrief(getLocalBrief(id)||emptyBrief())}});
  return()=>{active=false};},[id]);
 useEffect(()=>{const onBeforeUnload=(e:BeforeUnloadEvent)=>{if(dirty){e.preventDefault();e.returnValue='';}};window.addEventListener('beforeunload',onBeforeUnload);return()=>window.removeEventListener('beforeunload',onBeforeUnload)},[dirty]);
 const set=(field:Field,value:string|string[])=>{setBrief(prev=>({...prev,[field]:value}));setDirty(true);setNotice('');setErrors(prev=>({...prev,[field]:''}));};
 const toggle=(field:'audiences'|'goals',option:string)=>{const next=brief[field].includes(option)?brief[field].filter(x=>x!==option):[...brief[field],option];set(field,next);};
 const [saving,setSaving]=useState(false);
 const persist=async(status:'Draft'|'Researching')=>{
  setSaving(true);
  try{const saved=await saveProject({...brief,status});setBrief(saved);setDirty(false);
   if(!id)navigate(`/events/${saved.id}/edit`,{replace:true});return saved;
  }finally{setSaving(false)}
 };
 const draft=async()=>{try{await persist('Draft');setNotice('Draft saved to EpiVibe database. View it under Projects.')}catch(error){setNotice('Save failed: '+String(error instanceof Error?error.message:error))}};
 const start=async()=>{const e=validateBrief(brief);setErrors(e);if(Object.keys(e).length){setNotice('Please correct the highlighted fields before continuing.');return;}
  try{const saved=await persist('Draft');navigate(`/projects/${saved.id}/research`)}catch(error){setNotice('Save failed: '+String(error instanceof Error?error.message:error))}};
 const cancel=()=>{if(!dirty||window.confirm('Discard your unsaved changes?'))navigate('/home');};
 const select=(label:string,field:'eventType',options:string[])=> <label className="epi-brief-field"><span>{label} <b>*</b></span><div className="epi-brief-select"><select value={brief[field]} onChange={e=>set(field,e.target.value)}><option value="">Select event type</option>{options.map(x=><option key={x}>{x}</option>)}</select><ChevronDown size={17}/></div>{errors[field]&&<small role="alert">{errors[field]}</small>}</label>;
 const multi=(label:string,field:'audiences'|'goals',options:string[])=> {
  const selected=brief[field];
  const otherField=field==='audiences'?'audienceOther':'goalOther';
  const error=errors[field]||errors[otherField];
  return <div className="epi-brief-field epi-brief-multi"><span>{label} <b>*</b></span>
   <MultiDropdown label={label} value={selected} options={options} onToggle={option=>toggle(field,option)}/>
   {selected.includes('Other')&&<input aria-label={`Specify ${label}`} placeholder="Please specify" value={brief[otherField]} onChange={e=>set(otherField,e.target.value)}/>}
   {error&&<small role="alert">{error}</small>}
  </div>;
 };
 return <section className="epi-brief-page"><EventProgress currentStage={1}/><header className="epi-brief-heading"><h1>Create Your Event Brief</h1><p>Enter your event requirements and get a tailored event plan.</p></header>
 <form onSubmit={e=>{e.preventDefault();start();}} noValidate><div className="epi-brief-grid">
  <div className="epi-brief-card">{select('Event Type','eventType',eventTypes)}{brief.eventType==='Other'&&<label className="epi-brief-field"><span>Specify Event Type <b>*</b></span><input value={brief.eventTypeOther} onChange={e=>set('eventTypeOther',e.target.value)} placeholder="Describe your event type"/>{errors.eventTypeOther&&<small role="alert">{errors.eventTypeOther}</small>}</label>}</div>
  <div className="epi-brief-card"><label className="epi-brief-field"><span>Event Title <b>*</b></span><input value={brief.title} onChange={e=>set('title',e.target.value)} placeholder="e.g. Family Entertainment Festival"/>{errors.title&&<small role="alert">{errors.title}</small>}</label></div>
  <div className="epi-brief-card"><label className="epi-brief-field"><span>Venue / Location <em>(Optional)</em></span><input value={brief.location} onChange={e=>set('location',e.target.value)} placeholder="e.g. Phoenix Marketcity, Chennai"/></label></div>
  <div className="epi-brief-card">{multi('Target Audience','audiences',audiences)}</div>
  <div className="epi-brief-card"><div className="epi-brief-field"><span>Event Date <em>(Optional)</em></span><div className="epi-brief-dates"><label>Start<input type="date" value={brief.dateStart} onChange={e=>set('dateStart',e.target.value)}/></label><label>End<input type="date" min={brief.dateStart||undefined} value={brief.dateEnd} onChange={e=>set('dateEnd',e.target.value)}/></label></div>{errors.dateEnd&&<small role="alert">{errors.dateEnd}</small>}</div></div>
  <div className="epi-brief-card">{multi('Event Goal','goals',goals)}</div>
  <div className="epi-brief-card"><div className="epi-brief-field"><span>Event Budget <b>*</b></span><div className="epi-brief-budget"><select aria-label="Currency" value={brief.currency} onChange={e=>set('currency',e.target.value)}>{currencies.map(c=><option key={c.code} value={c.code}>{c.symbol} {c.code}</option>)}</select><input aria-label="Total event budget" type="number" min="0" step="any" value={brief.budget} onChange={e=>set('budget',e.target.value)} placeholder="Enter total budget"/></div>{errors.budget&&<small role="alert">{errors.budget}</small>}<p className="epi-brief-hint">Enter one total amount. EpiVibe will propose the allocation later.</p></div></div>
  <div className="epi-brief-card epi-brief-context"><label className="epi-brief-field"><span>Additional Context <em>(Optional)</em></span><textarea maxLength={2000} value={brief.context} onChange={e=>set('context',e.target.value)} placeholder="Tell us about the event vision, theme, constraints, or any special requirements..." rows={2}/><span className="epi-brief-counter">{brief.context.length}/2000 characters</span></label></div>
 </div><div className="epi-brief-actions"><button type="button" className="epi-brief-cancel" onClick={cancel}>Cancel</button><button type="button" className="epi-brief-save" onClick={draft} disabled={saving}><Save size={18}/>Save Draft</button><button type="submit" className="epi-brief-primary" disabled={saving}>Start AI Research <ArrowRight size={19}/></button></div>{notice&&<p className="epi-brief-notice" role="status">{notice}</p>}</form></section>;
}
