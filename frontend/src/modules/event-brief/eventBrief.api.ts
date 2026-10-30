import type {EventBrief} from './eventBrief.types';
const BASE = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '');
const KEY='epivibe.eventBriefs.v1';
export function listLocalBriefs():EventBrief[]{try{return JSON.parse(localStorage.getItem(KEY)||'[]') as EventBrief[]}catch{return []}}
export function getLocalBrief(id:string):EventBrief|undefined{return listLocalBriefs().find(x=>x.id===id)}
export function saveLocalBrief(brief:EventBrief):EventBrief{
 const next={...brief,id:brief.id||crypto.randomUUID(),updatedAt:new Date().toISOString()};
 localStorage.setItem(KEY,JSON.stringify([next,...listLocalBriefs().filter(x=>x.id!==next.id)]));return next;
}
async function request<T>(url:string, init?:RequestInit):Promise<T>{
 const response=await fetch(BASE+url,init);
 if(!response.ok){let msg='API request failed ('+response.status+')';try{const data=await response.json();if(typeof data.detail==='string')msg=data.detail}catch{}throw new Error(msg)}
 return response.json() as Promise<T>;
}
export async function deleteProject(id:string):Promise<void>{const response=await fetch(BASE+'/api/projects/'+encodeURIComponent(id),{method:'DELETE'});if(!response.ok)throw Error('Delete failed (HTTP '+response.status+')')}
export function listProjects():Promise<EventBrief[]>{return request('/api/projects')}
export function getProject(id:string):Promise<EventBrief>{return request('/api/projects/'+encodeURIComponent(id))}
export function saveProject(brief:EventBrief):Promise<EventBrief>{
 const id=brief.id||crypto.randomUUID();return request('/api/projects/'+encodeURIComponent(id),{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({...brief,id})});
}
let migrationPromise:Promise<void>|undefined;
export function migrateLocalDrafts():Promise<void>{
 if(!migrationPromise)migrationPromise=(async()=>{
  const local=listLocalBriefs();if(!local.length)return;
  const remote=await listProjects();const ids=new Set(remote.map(x=>x.id));
  for(const draft of local){if(!ids.has(draft.id))await saveProject(draft)}
  localStorage.removeItem(KEY);
 })().catch(e=>{migrationPromise=undefined;throw e});
 return migrationPromise;
}
