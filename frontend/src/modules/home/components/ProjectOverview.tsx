import {useEffect,useState} from 'react';
import {Link,useParams} from 'react-router-dom';
import {getProject} from '../../event-brief/eventBrief.api';
import type {EventBrief} from '../../event-brief/eventBrief.types';
import {eventDate,formatDate,statusLabel,continuePath,statusRank} from './projectDisplay';
import './projects.css';
export default function ProjectOverview(){
 const {id}=useParams();const [item,setItem]=useState<EventBrief|null>(null);const [error,setError]=useState('');
 useEffect(()=>{if(!id)return;let active=true;getProject(id).then(x=>{if(active)setItem(x)}).catch(e=>{if(active)setError(String(e.message||e))});return()=>{active=false}},[id]);
 if(error)return <main className="epi-project-overview"><Link to="/projects">← Projects</Link><p role="alert">Could not open project: {error}</p></main>;
 if(!item)return <main className="epi-project-overview">Loading project…</main>;
 const rank=statusRank(item.status);const completed=item.completedStages||[];const stage=[1,2,3,4].find(x=>!completed.includes(x))||4;
 return <main className="epi-project-overview"><Link className="epi-overview-back" to="/projects">← All Projects</Link><div className="epi-overview-heading"><div><p className="epi-overview-eyebrow">PROJECT OVERVIEW</p><h1>{item.title||'Untitled Event'}</h1><p>{item.eventType||'Event type not set'}{item.location?' · '+item.location:''}</p></div><span className="epi-overview-badge">{statusLabel(item.status)}</span></div>
 <section className="epi-overview-panel"><h2>Planning Progress</h2><div className="epi-overview-stages">{['Event Brief','AI Research','Event Concept','Execution Plan'].map((name,i)=><div key={name} className={`epi-overview-stage ${completed.includes(i+1)?'is-complete':i+1===stage?'is-active':''}`}><span>{completed.includes(i+1)?'✓':i+1}</span><strong>{name}</strong><small>{completed.includes(i+1)?'Completed':i+1===stage?'Current stage':'Upcoming'}</small></div>)}</div><div className="epi-overview-actions"><Link className="epi-overview-primary" to={continuePath(item)}>{rank===2?'Continue Event Brief':rank===3?'View Project':'Continue Planning'} →</Link><Link className="epi-overview-secondary" to={`/events/${item.id}/edit`}>View / Edit Event Brief</Link></div>{rank!==2&&<p className="epi-overview-note">Research progress is available from Continue Planning. Later stages will be connected after research.</p>}</section>
 <section className="epi-overview-panel"><h2>Event Information</h2><dl className="epi-overview-details"><div><dt>Event Type</dt><dd>{item.eventType||'Not set'}</dd></div><div><dt>Event Date</dt><dd>{eventDate(item)}</dd></div><div><dt>Location</dt><dd>{item.location||'Not specified'}</dd></div><div><dt>Target Audience</dt><dd>{[...item.audiences,item.audienceOther].filter(Boolean).join(', ')||'Not specified'}</dd></div><div><dt>Event Goal</dt><dd>{[...item.goals,item.goalOther].filter(Boolean).join(', ')||'Not specified'}</dd></div><div><dt>Total Budget</dt><dd>{item.budget?`${item.currency} ${Number(item.budget).toLocaleString('en-IN')}`:'Not set'}</dd></div>{item.context&&<div className="epi-overview-context"><dt>Additional Context</dt><dd>{item.context}</dd></div>}</dl></section>
 <section className="epi-overview-panel"><h2>Planning Outputs</h2><p className="epi-overview-muted">Research findings, event concepts, and execution plans will become available as their stages are implemented and completed.</p></section>
 <section className="epi-overview-panel"><h2>Project Information</h2><dl className="epi-overview-details"><div><dt>Last Updated</dt><dd>{formatDate(item.updatedAt)}</dd></div><div><dt>Planning Status</dt><dd>{statusLabel(item.status)}</dd></div></dl></section>
 </main>;
}
