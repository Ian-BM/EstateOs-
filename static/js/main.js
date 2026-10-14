'use strict';
const mobileNavigation = matchMedia('(max-width: 960px)');
const backdrop = document.querySelector('.nav-backdrop');
const navigationPairs = [['.menu-toggle','#public-nav'],['.workspace-menu','#workspace-nav']]
  .map(([button,menu])=>({button:document.querySelector(button),menu:document.querySelector(menu)}))
  .filter(pair=>pair.button&&pair.menu);
let activeNavigation = null;
function closeNavigation(restoreFocus=false){
  const previous=activeNavigation;
  for(const pair of navigationPairs){
    pair.menu.classList.remove('open');pair.button.setAttribute('aria-expanded','false');
    pair.menu.inert=mobileNavigation.matches;
  }
  activeNavigation=null;document.body.classList.remove('nav-open');
  const main=document.querySelector('.workspace-main');if(main)main.inert=false;
  if(backdrop)backdrop.hidden=true;
  if(restoreFocus&&previous)previous.button.focus();
}
for(const pair of navigationPairs){
  pair.menu.inert=mobileNavigation.matches;
  pair.button.addEventListener('click',()=>{
    if(activeNavigation===pair){closeNavigation(true);return;}
    closeNavigation();activeNavigation=pair;pair.menu.inert=false;
    pair.menu.classList.add('open');pair.button.setAttribute('aria-expanded','true');
    document.body.classList.add('nav-open');if(backdrop)backdrop.hidden=false;
    if(pair.menu.id==='workspace-nav')document.querySelector('.workspace-main').inert=true;
    pair.menu.querySelector('a,button')?.focus();
  });
  pair.menu.querySelectorAll('a').forEach(link=>link.addEventListener('click',()=>closeNavigation()));
  pair.menu.querySelectorAll('[data-close-nav]').forEach(button=>button.addEventListener('click',()=>closeNavigation(true)));
}
backdrop?.addEventListener('click',()=>closeNavigation(true));
mobileNavigation.addEventListener('change',()=>closeNavigation());
document.addEventListener('keydown',event=>{
  if(!activeNavigation)return;
  if(event.key==='Escape'){event.preventDefault();closeNavigation(true);return;}
  if(event.key==='Tab'){
    const focusable=[...(activeNavigation.menu.id==='public-nav'?[activeNavigation.button]:[]),...activeNavigation.menu.querySelectorAll('a,button,input,select,textarea,[tabindex="0"]')].filter(el=>el.offsetParent!==null&&!el.disabled);
    const first=focusable[0],last=focusable[focusable.length-1];
    if(event.shiftKey&&document.activeElement===first){event.preventDefault();last.focus();}
    else if(!event.shiftKey&&document.activeElement===last){event.preventDefault();first.focus();}
  }
});
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
