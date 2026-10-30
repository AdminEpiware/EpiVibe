import {Check} from 'lucide-react';
import './event-progress.css';
const steps=['Event Brief','AI Research','Event Concept','Execution Plan'];
export default function EventProgress({currentStage=1,completedStages=[]}:{currentStage?:number;completedStages?:number[]}) {
 return <nav className="epi-progress" aria-label="Event planning progress"><ol>{steps.map((name,i)=>{
  const num=i+1,done=completedStages.includes(num);
  return <li key={name} className={`epi-progress-step ${num===currentStage?'is-current':''} ${done?'is-done':''}`} aria-current={num===currentStage?'step':undefined}>
   <span className="epi-progress-number">{done?<Check size={17} strokeWidth={3}/>:num}</span><span className="epi-progress-name">{name}</span>
  </li>;
 })}</ol><p className="epi-progress-mobile">Step {currentStage} of 4 — {steps[currentStage-1]}</p></nav>;
}
