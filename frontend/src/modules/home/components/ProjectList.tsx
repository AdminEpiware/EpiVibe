import {useEffect,useState} from 'react';
import {Link} from 'react-router-dom';
import {FolderOpen,ArrowRight} from 'lucide-react';
import {listProjects,migrateLocalDrafts} from '../../event-brief/eventBrief.api';
import type {EventBrief} from '../../event-brief/eventBrief.types';
import {sortedProjects,eventDate,statusLabel,continuePath} from './projectDisplay';
import './projects.css';
export default function ProjectList(){
 const [items,setItems]=useState<EventBrief[]>([]);const [error,setError]=useState('');
 useEffect(()=>{let active=true;migrateLocalDrafts().then(listProjects).then(rows=>{if(active)setItems(sortedProjects(rows))}).catch(e=>{if(active)setError(String(e.message||e))});return()=>{active=false}},[]);
 return <section className="epi-home-projects" aria-labelledby="epi-projects-heading"><div className="epi-home-projects-header"><h2 id="epi-projects-heading">Your Event Projects</h2><Link to="/projects">View all <ArrowRight size={17}/></Link></div>
 {error?<div className="epi-home-empty">Unable to load projects: {error}. Please start the backend.</div>:items.length?<div className="epi-home-project-cards">{items.slice(0,5).map(item=><div key={item.id} className="epi-project-entry"><Link className="epi-project-name" to={`/projects/${item.id}`}>{item.title||'Untitled Event'}</Link><span className="epi-project-date">{eventDate(item)}</span><span className="epi-project-state">{statusLabel(item.status)}</span><Link className="epi-project-continue" to={continuePath(item)} aria-label={`Continue ${item.title||'Untitled Event'}`}>Continue <ArrowRight size={16}/></Link></div>)}</div>:<div className="epi-home-empty"><FolderOpen size={30}/><div><h3>Your event projects will appear here</h3><p>Create your first event to start building a culturally informed plan.</p></div><Link to="/events/new">Create an event <ArrowRight size={16}/></Link></div>}</section>
}
