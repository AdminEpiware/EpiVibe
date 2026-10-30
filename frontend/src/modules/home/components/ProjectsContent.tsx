import {useEffect,useMemo,useState} from 'react';
import {Link} from 'react-router-dom';
import {deleteProject,listProjects,migrateLocalDrafts} from '../../event-brief/eventBrief.api';
import type {EventBrief} from '../../event-brief/eventBrief.types';
import {sortedProjects,eventDate,formatDate,statusLabel,continuePath,statusRank} from './projectDisplay';
import './projects.css';
type Filter='All'|'In Progress'|'Draft'|'Planning Completed';
export default function ProjectsContent(){
 const [deleting,setDeleting]=useState<string|null>(null);const [items,setItems]=useState<EventBrief[]>([]);const [loading,setLoading]=useState(true);const [error,setError]=useState('');const [filter,setFilter]=useState<Filter>('All');
 useEffect(()=>{let active=true;migrateLocalDrafts().then(listProjects).then(rows=>{if(active)setItems(sortedProjects(rows))}).catch(e=>{if(active)setError(String(e.message||e))}).finally(()=>{if(active)setLoading(false)});return()=>{active=false}},[]);
 const remove=async(item:EventBrief)=>{if(!window.confirm(`Permanently delete "${item.title||'Untitled Event'}" and all its planning data? This cannot be undone.`))return;setDeleting(item.id);setError('');try{await deleteProject(item.id);setItems(old=>old.filter(x=>x.id!==item.id));}catch(e){setError(e instanceof Error?e.message:String(e));}finally{setDeleting(null)}};
 const filtered=useMemo(()=>items.filter(x=>filter==='All'||(filter==='Draft'?statusRank(x.status)===2:filter==='Planning Completed'?statusRank(x.status)===3:statusRank(x.status)<2)),[items,filter]);
 return <main className="epi-projects-page"><header><h1>Your Event Projects</h1><p>Continue planning your saved events.</p><Link to="/events/new" className="epi-projects-new">+ New Event</Link></header>
 <div className="epi-project-filters" role="group" aria-label="Filter projects">{(['All','In Progress','Draft','Planning Completed'] as Filter[]).map(f=><button key={f} type="button" className={filter===f?'is-selected':''} onClick={()=>setFilter(f)}>{f}</button>)}</div>
 {loading?<p>Loading projects…</p>:error?<p role="alert">Could not load projects: {error}. Check that FastAPI is running.</p>:filtered.length===0?<div className="epi-projects-empty">{items.length?'No projects match this filter.':<>No saved projects yet. <Link to="/events/new">Create your first event</Link>.</>}</div>:<div className="epi-projects-grid">{filtered.map(item=><article key={item.id} className="epi-projects-card"><Link className="epi-projects-title" to={`/projects/${item.id}`}>{item.title||'Untitled Event'}</Link><div className="epi-projects-meta"><div><span>Event Date</span><strong>{eventDate(item)}</strong></div><div><span>Planning Status</span><strong className="epi-projects-status">{statusLabel(item.status)}</strong>{statusRank(item.status)!==3&&<small>Updated {formatDate(item.updatedAt)}</small>}</div></div><button className="epi-projects-delete" type="button" disabled={deleting===item.id} onClick={()=>void remove(item)}>{deleting===item.id?'Deleting…':'Delete Project'}</button><Link className="epi-projects-open" to={continuePath(item)}>{statusRank(item.status)===2?'Edit Event Brief':statusRank(item.status)===3?'View Project':'Continue Planning'} →</Link></article>)}</div>}
 </main>
}
