'use strict';
for(const [buttonSelector,menuSelector] of [['.menu-toggle','#public-nav'],['.workspace-menu','#workspace-nav']]){
 const button=document.querySelector(buttonSelector),menu=document.querySelector(menuSelector);
 if(button&&menu){button.addEventListener('click',()=>{const open=menu.classList.toggle('open');button.setAttribute('aria-expanded',String(open));});document.addEventListener('keydown',e=>{if(e.key==='Escape'){menu.classList.remove('open');button.setAttribute('aria-expanded','false');}});}
}
for(const link of document.querySelectorAll('.sidebar nav a')){if(link.pathname===location.pathname)link.classList.add('active');}
for(const button of document.querySelectorAll('[data-favorite]')){
 const key='estate-favorite-'+button.dataset.favorite;
 function render(){try{const saved=localStorage.getItem(key)==='1';button.setAttribute('aria-pressed',String(saved));button.textContent=saved?'♥':'♡';}catch{button.title='Browser storage is unavailable';}}
 render();document.addEventListener('estate-favorites-updated',render);button.addEventListener('click',()=>{try{localStorage.setItem(key,localStorage.getItem(key)==='1'?'0':'1');document.dispatchEvent(new Event('estate-favorites-updated'));}catch{button.title='Unable to save: browser storage is unavailable';}});
}
for(const button of document.querySelectorAll('[data-gallery]'))button.addEventListener('click',()=>{document.querySelector('#gallery-main').src=button.dataset.gallery;});
for(const form of document.querySelectorAll('[data-confirm]'))form.addEventListener('submit',event=>{if(!confirm(form.dataset.confirm))event.preventDefault();});
function connection(){const status=document.querySelector('#connection-status');if(status){status.textContent=navigator.onLine?'Online':'Offline · drafts only';status.style.color=navigator.onLine?'':'#b97b27';}}
addEventListener('online',connection);addEventListener('offline',connection);connection();
const synced=document.querySelector('#synced-operation');
if(synced){try{const key=`estate-inspection-drafts-v1-${synced.dataset.agency}-${synced.dataset.user}`;const drafts=JSON.parse(localStorage.getItem(key)||'[]');for(const draft of drafts)if(draft.id===synced.dataset.operation)draft.state='Successfully synchronized';localStorage.setItem(key,JSON.stringify(drafts));}catch{/* The server record remains saved even when browser storage is unavailable. */}}
