// Presentation interactions only. Risk calculations remain in index.html.
(() => {
 // Move segmented-chart labels into a responsive HTML legend. Values and segment widths are unchanged.
 const drawSegment=window.segmentBar;
 if(drawSegment)window.segmentBar=(host,options)=>{
  drawSegment(host,options);
  const svg=host.querySelector('svg'),view=svg.getAttribute('viewBox').split(' ');
  svg.querySelectorAll('text.axt,text.dlab,rect[y="44"]').forEach(node=>node.remove());
  svg.setAttribute('height','40');svg.setAttribute('viewBox',`0 0 ${view[2]} 40`);
  const legend=document.createElement('div');legend.className='enterprise-mix-legend';
  const total=options.parts.reduce((sum,part)=>sum+part.value,0)||1;
  options.parts.forEach(part=>{const row=document.createElement('div'),label=document.createElement('span'),dot=document.createElement('i'),value=document.createElement('b');dot.style.background=part.color;label.append(dot,document.createTextNode(part.name));value.textContent=options.fmtVal(part.value)+' · '+options.fmtPct(part.value/total);row.append(label,value);legend.append(row);});host.append(legend);
 };
 const side=document.querySelector('.side'),toggle=document.getElementById('enterpriseMenu');
 if(!side||!toggle)return;
 function close(){side.classList.remove('menu-open');toggle.setAttribute('aria-expanded','false');toggle.setAttribute('aria-label','Mở menu điều hướng');}
 toggle.addEventListener('click',()=>{const open=side.classList.toggle('menu-open');toggle.setAttribute('aria-expanded',String(open));toggle.setAttribute('aria-label',open?'Đóng menu điều hướng':'Mở menu điều hướng');});
 document.getElementById('nav').addEventListener('click',event=>{if(event.target.closest('a'))close();});
 document.addEventListener('keydown',event=>{if(event.key==='Escape'&&side.classList.contains('menu-open')){close();toggle.focus();}});
 const nav=document.getElementById('nav');
 const current=()=>nav.querySelectorAll('a').forEach(a=>{if(a.classList.contains('on'))a.setAttribute('aria-current','page');else a.removeAttribute('aria-current');});
 new MutationObserver(current).observe(nav,{subtree:true,attributes:true,attributeFilter:['class'],childList:true});current();
})();
