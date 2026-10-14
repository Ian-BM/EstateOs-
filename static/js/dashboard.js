'use strict';
// Deliberately limited local draft prototype. No cached pages or automatic sync.
const form=document.querySelector('#inspection-form');
if(form){
 const key=`estate-inspection-drafts-v1-${form.dataset.agency}-${form.dataset.user}`;
 const status=document.querySelector('#draft-status'),list=document.querySelector('#draft-list'),op=document.querySelector('#operation-id');
 const safeFields=['property','date','inspection_type','condition'];
 const operationId=()=>crypto.randomUUID();
 op.value=operationId();
 let drafts=[];
 try{drafts=JSON.parse(localStorage.getItem(key)||'[]');if(!Array.isArray(drafts))drafts=[];}catch{status.textContent='Browser draft storage is unavailable.';}
 const store=()=>localStorage.setItem(key,JSON.stringify(drafts));
 function render(){list.replaceChildren();for(const draft of drafts){const row=document.createElement('div');row.className='draft-item';const text=document.createElement('span');text.textContent=`Property #${draft.fields.property||'unselected'} · ${draft.fields.date||'No date'} · ${draft.state}`;row.append(text);const load=document.createElement('button');load.type='button';load.className='button secondary';load.textContent='Load draft';load.addEventListener('click',()=>{for(const field of safeFields)form.elements[field].value=draft.fields[field]||'';op.value=draft.id;status.textContent='Draft loaded. Review all fields, assign an inspector and save online to synchronize.';});const remove=document.createElement('button');remove.type='button';remove.className='button secondary';remove.textContent='Delete';remove.addEventListener('click',()=>{try{drafts=drafts.filter(d=>d.id!==draft.id);store();render();}catch{status.textContent='Unable to update browser storage.';}});row.append(load,remove);list.append(row);}}
 document.querySelector('#save-draft').addEventListener('click',()=>{try{const draft={id:op.value,fields:Object.fromEntries(safeFields.map(field=>[field,form.elements[field].value])),state:'Saved locally · pending manual sync'};drafts=drafts.filter(d=>d.id!==draft.id);drafts.push(draft);store();render();status.textContent='Saved locally on this browser. No photos or free-text notes were stored.';}catch{status.textContent='Draft could not be saved. Browser storage may be disabled or full.';}});
 form.addEventListener('submit',event=>{if(!navigator.onLine){event.preventDefault();status.textContent='You are offline. Save a local draft, then submit when connected.';}});
 render();
}
