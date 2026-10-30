import { useCallback, useEffect, useRef, useState } from 'react';
import { Check, ChevronRight, Send, Sparkles, X } from 'lucide-react';
import { createPortal } from 'react-dom';
import './refinement-panel.css';

type Obj = Record<string, unknown>;
type Message = { role: string; text: string; changes?: string[] };
type RefinementState = { version: number; proposal: Obj | null; messages: Message[]; proposalBaseVersion: number | null };
const API = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '');
const label = (s: string) => s.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
const money = (n: number) => `₹${Math.round(n).toLocaleString('en-IN')}`;
const human = (value: unknown): string => {
  if (value === null || value === undefined) return 'Not specified';
  if (typeof value === 'boolean') return value ? 'Yes' : 'No';
  if (typeof value === 'number') return value.toLocaleString('en-IN');
  if (typeof value === 'string') return value || 'Empty';
  if (Array.isArray(value)) return value.length ? value.map((v, i) => `${i + 1}. ${human(v)}`).join('\n') : 'None';
  if (typeof value === 'object') return Object.entries(value as Obj).map(([k, v]) => `${label(k)}: ${human(v)}`).join('\n');
  return String(value);
};
type Difference = { path: string; before: unknown; after: unknown };
const isRecord = (v: unknown): v is Obj => !!v && typeof v === 'object' && !Array.isArray(v);
const diffs = (before: unknown, after: unknown, path = '', depth = 0): Difference[] => {
  if (JSON.stringify(before) === JSON.stringify(after)) return [];
  if (depth > 6) return [{ path, before, after }];
  if (isRecord(before) && isRecord(after)) {
    const keys = new Set([...Object.keys(before), ...Object.keys(after)]);
    return [...keys].flatMap(key => diffs(before[key], after[key], path ? `${path} / ${label(key)}` : label(key), depth + 1));
  }
  if (Array.isArray(before) && Array.isArray(after)) {
    const result: Difference[] = [];
    for (let i = 0; i < Math.max(before.length, after.length); i++) {
      const item = isRecord(after[i]) ? after[i] : isRecord(before[i]) ? before[i] : null;
      const title = item && (item.name || item.title || item.category || item.activity || item.label);
      result.push(...diffs(before[i], after[i], `${path} / ${typeof title === 'string' ? title : `Item ${i + 1}`}`, depth + 1));
    }
    return result;
  }
  return [{ path: path || 'Concept', before, after }];
};
const display = (path: string, value: unknown) => typeof value === 'number' && /budget|amount|cost|price|allocation/i.test(path) ? money(value) : human(value);
function ReviewModal({ mode, changes, busy, onClose, onApply, onDiscard }: {
  mode: 'summary' | 'compare'; changes: Difference[]; busy: boolean; onClose: () => void; onApply: () => void; onDiscard: () => void;
}) {
  const [tab, setTab] = useState<'summary' | 'compare'>(mode);
  useEffect(() => setTab(mode), [mode]);
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose(); };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [onClose]);
  return createPortal(<div className="epi-review-backdrop" onMouseDown={e => { if (e.target === e.currentTarget) onClose(); }}>
    <section className="epi-review-modal" role="dialog" aria-modal="true" aria-label="Review proposed changes">
      <header className="epi-review-header"><div><strong>Review AI Proposed Changes</strong><span>{changes.length} individual changes detected</span></div><button type="button" onClick={onClose} aria-label="Close review"><X size={22}/></button></header>
      <div className="epi-review-tabs"><button className={tab === 'summary' ? 'active' : ''} onClick={() => setTab('summary')}>View Changes</button><button className={tab === 'compare' ? 'active' : ''} onClick={() => setTab('compare')}>Compare Side by Side</button></div>
      <div className="epi-review-body">{changes.length === 0 ? <p>No changes detected in the proposal.</p> : tab === 'summary' ? changes.map((change, i) => <article className="epi-review-change" key={i}><h3>{change.path}</h3><p>{change.before === undefined ? 'Added' : change.after === undefined ? 'Removed' : 'Updated'}</p><div className="epi-review-value">{display(change.path, change.after)}</div></article>) : <div className="epi-review-compare">{changes.map((change, i) => <article key={i} className="epi-review-row"><h3>{change.path}</h3><div className="epi-review-columns"><div><span>Current</span><p>{display(change.path, change.before)}</p></div><div><span>Proposed</span><p>{display(change.path, change.after)}</p></div></div></article>)}</div>}</div>
      <footer className="epi-review-footer"><button type="button" onClick={onClose}>Back to Chat</button><button type="button" disabled={busy} onClick={onDiscard}>Discard Proposal</button><button type="button" className="primary" disabled={busy || !changes.length} onClick={onApply}><Check size={17}/> Apply Changes</button></footer>
    </section>
  </div>, document.body);
}
async function call(path: string, method = 'GET', body?: unknown) {
  const response = await fetch(`${API}${path}`, { method, headers: body ? { 'Content-Type': 'application/json' } : undefined, body: body ? JSON.stringify(body) : undefined });
  const data = await response.json();
  if (!response.ok) throw new Error(typeof data.detail === 'string' ? data.detail : `HTTP ${response.status}`);
  return data;
}
export default function RefinementSidePanel({ projectId, open, onClose, current, onApplied }: {
  projectId: string; open: boolean; onClose: () => void; current: Obj; onApplied: () => Promise<void>;
}) {
  const [state, setState] = useState<RefinementState | null>(null);
  const [draft, setDraft] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [review, setReview] = useState<'summary' | 'compare' | null>(null);
  const chatEnd = useRef<HTMLDivElement>(null);
  const base = `/api/projects/${encodeURIComponent(projectId)}/refinement`;
  const refresh = useCallback(async () => {
    try { setState(await call(base)); setError(''); }
    catch (e) { setError(e instanceof Error ? e.message : String(e)); }
  }, [base]);
  useEffect(() => { if (open) void refresh(); }, [open, refresh]);
  useEffect(() => { if (open) chatEnd.current?.scrollIntoView({ behavior: 'smooth', block: 'end' }); }, [open, state?.messages.length]);
  const action = async (name: 'propose' | 'apply' | 'discard', body?: unknown) => {
    if (busy) return;
    setBusy(true); setError('');
    try {
      const next = await call(`${base}/${name}`, 'POST', body);
      setState(next);
      if (name === 'propose') { setDraft(''); setReview(null); }
      if (name === 'apply') { setReview(null); await onApplied(); }
    } catch (e) { setError(e instanceof Error ? e.message : String(e)); }
    finally { setBusy(false); }
  };
  const proposal = state?.proposal;
  const changed = proposal ? diffs(current, proposal) : [];
  return <aside className={`epi-ai-panel ${open ? 'is-open' : ''}`} aria-label="Refine event concept with Gemini" aria-hidden={!open}>
    <header className="epi-ai-panel-header"><div><Sparkles size={18}/><strong>Refine with AI</strong><small>Gemini · Event Concept</small></div><button type="button" onClick={onClose} aria-label="Close AI chat"><X size={20}/></button></header>
    <div className="epi-ai-panel-intro">Ask about your event or request a change. Gemini uses the saved event brief, research, and approved concept.</div>
    <div className="epi-ai-panel-suggestions">{['Improve the activity mix','Make it more family-friendly','Reduce production costs'].map(s => <button type="button" key={s} onClick={() => setDraft(s)}>{s}</button>)}</div>
    <div className="epi-ai-panel-chat" role="log" aria-live="polite">{!state?.messages?.length && <p className="epi-ai-panel-empty">How would you like to improve this event?</p>}{state?.messages?.map((m, i) => <div className={`epi-ai-panel-message ${m.role === 'user' ? 'user' : 'assistant'}`} key={i}><p>{m.text}</p>{m.changes?.map((c,j) => <p key={j} className="epi-ai-panel-change"><Check size={13}/>{c}</p>)}</div>)}<div ref={chatEnd}/></div>
    {proposal && <section className="epi-ai-panel-proposal epi-ai-panel-proposal-compact"><div className="epi-ai-panel-proposal-heading"><strong>Proposed revision ready</strong><span>{changed.length} changes</span></div><p>Review the proposed changes in a larger workspace before applying them.</p><div className="epi-ai-panel-review-tabs"><button type="button" onClick={() => setReview('summary')}>View Changes</button><button type="button" onClick={() => setReview('compare')}>Compare</button></div><div className="epi-ai-panel-proposal-actions"><button type="button" disabled={busy} onClick={() => void action('discard')}>Discard</button><button type="button" disabled={busy || !changed.length} onClick={() => void action('apply')}><Check size={15}/> Apply Changes</button></div></section>}
    {proposal && review && <ReviewModal mode={review} changes={changed} busy={busy} onClose={() => setReview(null)} onApply={() => void action('apply')} onDiscard={() => { setReview(null); void action('discard'); }}/>}
    {error && <p className="epi-ai-panel-error" role="alert">{error} <button type="button" onClick={() => void refresh()}>Retry <ChevronRight size={13}/></button></p>}
    <form className="epi-ai-panel-form" onSubmit={e => { e.preventDefault(); if (draft.trim()) void action('propose', { message: draft.trim() }); }}><textarea aria-label="Message Gemini" placeholder="Ask Gemini to refine your concept…" value={draft} onChange={e => setDraft(e.target.value)} maxLength={2500} disabled={busy}/><button type="submit" aria-label="Send message" disabled={busy || !draft.trim()}><Send size={19}/></button></form>
  </aside>;
}
