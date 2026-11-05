import { categories } from './data.js';
import { cards } from './content.js';

const supportFirst = new Set(['Threats, violence, control, or feeling unsafe','Concerned that someone’s whereabouts are unknown','Not enough food','Unstable housing','Irregular meals or difficulty accessing food']);
export function buildPlan(input = {}) {
  const selected = input.selected || [];
  const details = (input.details || []).filter(d => cards[d]);
  const urgent = details.find(d => supportFirst.has(d));
  const requested = details.includes(input.primary) ? input.primary : details[0];
  const fallback = categories.find(c => selected.includes(c.id))?.subs[0];
  const detail = urgent || requested || fallback || 'Can’t start';
  const card = cards[detail] || cards['Can’t start'];
  const duration = Math.max(1, Math.min(60, Number(input.minutes) || 15, input.energy === 'Very low' ? 5 : 60, input.small ? 2 : 60));
  const human = ['Find a person to help', 'Feel supported'].includes(input.priority);
  const first = input.small || (input.energy === 'Very low' && card.kind === 'study' && !human) ? card.smaller : human && card.kind === 'study' ? `Choose ${card.support.toLowerCase()} and write down one thing you would like help with.` : card.first;
  const steps = [...card.steps];
  if (input.approach === 'ask') return {detail,card,duration,first:`Ask ${card.support.toLowerCase()} for help with one specific next step.`,steps,sourceIds:card.sourceIds,kind:'support',support:card.support};
  return {detail,card,duration,first,steps,sourceIds:card.sourceIds,kind:human?'support':card.kind,support:card.support};
}
export function reviewDate(rating, from = new Date()) {
  const next = new Date(from);
  next.setDate(next.getDate() + (rating === 'again' ? 1 : rating === 'hard' ? 2 : 4));
  const y=next.getFullYear(), m=String(next.getMonth()+1).padStart(2,'0'), d=String(next.getDate()).padStart(2,'0');
  return `${y}-${m}-${d}`;
}
export function calculateGrade(rows) {
  if(rows.some(r=>String(r.score).trim()===''||String(r.weight).trim()===''))return null;
  const clean=rows.map(r=>({score:Number(r.score),weight:Number(r.weight)}));
  if(clean.some(r=>!Number.isFinite(r.score)||!Number.isFinite(r.weight)||r.score<0||r.score>100||r.weight<0))return null;
  if(Math.abs(clean.reduce((n,r)=>n+r.weight,0)-100)>0.001)return null;
  return clean.reduce((n,r)=>n+r.score*r.weight/100,0);
}
