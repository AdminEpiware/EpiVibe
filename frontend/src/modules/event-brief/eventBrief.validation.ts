import type {EventBrief} from './eventBrief.types';
export function validateBrief(b: EventBrief): Record<string,string> {
 const e: Record<string,string> = {};
 if(!b.eventType) e.eventType='Select an event type.';
 if(b.eventType==='Other' && !b.eventTypeOther.trim()) e.eventTypeOther='Specify the event type.';
 if(!b.title.trim()) e.title='Enter an event title.';
 if(!b.audiences.length) e.audiences='Select at least one audience.';
 if(b.audiences.includes('Other') && !b.audienceOther.trim()) e.audienceOther='Specify the audience.';
 if(!b.goals.length) e.goals='Select at least one event goal.';
 if(b.goals.includes('Other') && !b.goalOther.trim()) e.goalOther='Specify the goal.';
 if(!b.budget.trim() || !Number.isFinite(Number(b.budget)) || Number(b.budget)<=0) e.budget='Enter a total budget greater than zero.';
 if(b.dateStart && b.dateEnd && b.dateEnd < b.dateStart) e.dateEnd='End date cannot be before start date.';
 if(Boolean(b.dateStart)!==Boolean(b.dateEnd)) e.dateEnd='Select both dates or leave both blank.';
 return e;
}
