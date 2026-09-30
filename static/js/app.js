(function(){
  const root=document.documentElement;
  const saved=localStorage.getItem('seid-theme');
  if(saved==='light'){document.body.classList.add('light');root.dataset.theme='light'}
  window.toggleTheme=function(){document.body.classList.toggle('light');const light=document.body.classList.contains('light');root.dataset.theme=light?'light':'dark';localStorage.setItem('seid-theme',light?'light':'dark')};
  window.toggleMenu=function(){document.getElementById('mobile-menu')?.classList.toggle('open')};
  window.toggleAI=function(){const p=document.getElementById('ai-panel');if(!p)return;p.classList.toggle('open');p.setAttribute('aria-hidden',p.classList.contains('open')?'false':'true');if(p.classList.contains('open'))document.getElementById('ai-input')?.focus()};
  document.addEventListener('click',function(e){const button=e.target.closest('[data-action]');if(!button)return;if(button.dataset.action==='toggle-theme')window.toggleTheme();if(button.dataset.action==='toggle-menu')window.toggleMenu();if(button.dataset.action==='toggle-ai')window.toggleAI()});

  const csrf=()=>{
    const hidden=document.querySelector('[name=csrfmiddlewaretoken]');
    if(hidden&&hidden.value) return hidden.value;
    const cookie=document.cookie.split('; ').find(row=>row.startsWith('csrftoken='));
    return cookie ? decodeURIComponent(cookie.split('=')[1]) : '';
  };
  const form=document.getElementById('ai-form');
  if(form){form.addEventListener('submit',async function(e){
    e.preventDefault();const input=document.getElementById('ai-input');const box=document.getElementById('ai-messages');const message=input.value.trim();if(!message)return;
    if(message.length>1200){const error='Please keep your question under 1200 characters.';const pending=document.createElement('div');pending.className='ai-bubble bot';pending.textContent=error;box.appendChild(pending);box.scrollTop=box.scrollHeight;return;}
    const user=document.createElement('div');user.className='ai-bubble user';user.textContent=message;box.appendChild(user);input.value='';
    const pending=document.createElement('div');pending.className='ai-bubble bot';pending.textContent='Thinking…';box.appendChild(pending);box.scrollTop=box.scrollHeight;
    try{
      const token=csrf();
      const r=await fetch('/api/ai/chat/',{method:'POST',credentials:'same-origin',headers:{'X-Requested-With':'XMLHttpRequest','Content-Type':'application/json',...(token ? {'X-CSRFToken': token} : {})},body:JSON.stringify({message})});
      const data=await r.json().catch(()=>({error:'The assistant is temporarily unavailable. Please try again.'}));
      const reply=data.reply||data.answer;
      if(!r.ok){pending.textContent=data.error||reply||'The assistant is temporarily unavailable. Please try again.';return;}
      pending.textContent=reply||'The assistant is temporarily unavailable. Please try again.';
    }catch(err){pending.textContent='The assistant is temporarily unavailable. Please try again.'}
    box.scrollTop=box.scrollHeight;
  })}

  const newsletter=document.getElementById('newsletter-form');
  if(newsletter){newsletter.addEventListener('submit',async function(e){
    e.preventDefault();const button=newsletter.querySelector('button');const data=new FormData(newsletter);button.disabled=true;button.textContent='Sending…';
    try{const token=csrf();const r=await fetch('/newsletter/',{method:'POST',credentials:'same-origin',headers:{'X-Requested-With':'XMLHttpRequest',...(token ? {'X-CSRFToken': token} : {})},body:data});const out=await r.json();button.textContent=out.message||'Done';if(out.ok){newsletter.reset()}}catch(e){button.textContent='Try again'}finally{setTimeout(()=>{button.disabled=false;button.textContent='Subscribe'},2200)}
  })}

  if(!sessionStorage.getItem('seid-tracked')){fetch('/analytics/track/?path='+encodeURIComponent(location.pathname),{credentials:'same-origin'}).catch(()=>{});sessionStorage.setItem('seid-tracked','1')}
})();
