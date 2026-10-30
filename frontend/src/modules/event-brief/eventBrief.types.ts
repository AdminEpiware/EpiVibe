export type EventBrief = {
  id: string; eventType: string; eventTypeOther: string; title: string;
  location: string; audiences: string[]; audienceOther: string;
  dateStart: string; dateEnd: string; goals: string[]; goalOther: string;
  currency: string; budget: string; context: string;
  status: 'Draft' | 'Researching' | 'In Progress' | 'Planning Completed'; completedStages?: number[]; updatedAt: string;
};
export const emptyBrief = (): EventBrief => ({id:'',eventType:'',eventTypeOther:'',title:'',location:'',audiences:[],audienceOther:'',dateStart:'',dateEnd:'',goals:[],goalOther:'',currency:'INR',budget:'',context:'',status:'Draft',updatedAt:''});
