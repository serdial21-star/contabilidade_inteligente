'use strict';
(() => {
  const menuButton=document.querySelector('.mobile-nav-button');
  const navigation=document.querySelector('#main-navigation');
  menuButton.addEventListener('click',()=>{const open=menuButton.getAttribute('aria-expanded')==='true';menuButton.setAttribute('aria-expanded',String(!open));menuButton.querySelector('.sr-only').textContent=open?'Abrir menu':'Fechar menu';navigation.classList.toggle('open',!open);});
  navigation.addEventListener('click',event=>{if(event.target.closest('a')){navigation.classList.remove('open');menuButton.setAttribute('aria-expanded','false');menuButton.querySelector('.sr-only').textContent='Abrir menu';}});
  document.querySelector('#current-year').textContent=String(new Date().getFullYear());
  document.querySelector('#demo-form').addEventListener('submit',event=>{event.preventDefault();const form=event.currentTarget,status=document.querySelector('#form-status');if(!form.checkValidity()){status.className='form-status error';status.textContent='Revise os campos obrigatórios para demonstrar o envio.';form.reportValidity();return;}status.className='form-status success';status.textContent='Simulação concluída. Nenhuma informação foi enviada ou armazenada.';form.reset();});
})();
