/* Trusted source render/interaction smoke in Node VM. No browser/layout claim.
   Run: node --test app/tests/smoke.cjs (Node 18+). No dependencies. */
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const app = path.resolve(__dirname, '..');

function fixture() {
  const events = {}, windowEvents = {}, elements = {};
  for (const id of ['#app','#notice','#overlay','#overlay-content','#main','#review-check','#confirm-decision','#decision-result','#table-content','#search']) {
    elements[id] = {innerHTML:'',textContent:'',checked:false,open:false,focus(){},querySelector(){return null;},addEventListener(){},showModal(){this.open=true;},close(){this.open=false;}};
  }
  let hash='';
  const location={get hash(){return hash;},set hash(value){hash=value.startsWith('#')?value:'#'+value;}};
  const context = {document:{querySelector:s=>elements[s]||null,addEventListener:(event,callback)=>events[event]=callback},
    location,setTimeout:()=>0,clearTimeout(){},FormData:class {}};
  context.window={addEventListener:(event,callback)=>windowEvents[event]=callback,scrollTo(){}};
  vm.createContext(context);
  for (const file of ['mocks.js','foundation.js']) vm.runInContext(fs.readFileSync(path.join(app,file),'utf8'),context,{filename:file});
  return {elements,context,
    route(name){context.location.hash='#'+name;windowEvents.hashchange();return elements['#app'].innerHTML;},
    click(action,id,decision){events.click({target:{closest:selector=>selector==='[data-action]'?({dataset:{action,id,decision}}):null}});},
    input(id,value){events.input({target:{id,value}});},
    html(){return elements['#app'].innerHTML;}
  };
}
test('seven prototype routes render with navigation and decision line',()=>{
  const f=fixture();
  for(const [route,label] of [['login','Bem-vindo'],['dashboard','Minha Visão'],['documents','Documentos'],['proposals','Propostas contábeis'],['review','Revisão da proposta'],['timeline','Linha da Decisão'],['settings','Personalização']])assert.ok(f.route(route).includes(label),route);
  assert.ok(f.route('dashboard').includes('Navegação principal'));
  assert.ok(f.route('timeline').includes('SOURCE'));
  assert.ok(f.html().includes('APPROVAL'));
});
test('login does not accept credentials; normal UI cannot send data',()=>{
  const f=fixture(),html=f.route('login');
  assert.match(html,/type="password"[^>]*disabled/);
  assert.match(html,/type="email"[^>]*disabled/);
  assert.match(html,/sem autenticar/);
  const entry=fs.readFileSync(path.join(app,'prototype.html'),'utf8');
  assert.ok(entry.includes("connect-src 'none'"));
  assert.ok(entry.includes("form-action 'none'"));
  assert.doesNotMatch(fs.readFileSync(path.join(app,'foundation.js'),'utf8'),/\bfetch\s*\(|localStorage\.|sessionStorage\./);
});
test('widgets can be removed, inserted, resized and reordered in memory',()=>{
  const f=fixture();f.route('dashboard');f.click('personalize');
  f.click('remove-widget','received');assert.ok(!f.html().includes('data-widget="received"'));
  f.click('insert-widget','received');assert.ok(f.html().includes('data-widget="received"'));
  f.click('resize','received');assert.match(f.html(),/widget  wide" data-widget="received"/);
  f.click('move-left','received');assert.ok(f.html().indexOf('data-widget="received"')<f.html().indexOf('data-widget="approvals"'));
  f.click('save-view');assert.match(f.elements['#notice'].textContent,/somente nesta sessão/);
});
test('filters yield useful empty state, sort and pagination are interactive',()=>{
  const f=fixture();f.route('documents');f.input('search','INEXISTENTE');
  assert.match(f.elements['#table-content'].innerHTML,/Nenhum item corresponde/);
  f.click('clear-filters');f.click('next');assert.match(f.elements['#table-content'].innerHTML,/Página 2 de 2/);
  f.click('previous');f.click('sort');assert.match(f.elements['#table-content'].innerHTML,/aria-sort="descending"/);
});
test('decision requires both deliberate checks; blocked mock has disabled actions',()=>{
  const f=fixture();f.route('review');f.click('decision-approve');assert.equal(f.elements['#overlay'].open,false);
  f.elements['#review-check'].checked=true;f.click('decision-approve');assert.equal(f.elements['#overlay'].open,true);
  f.click('confirm-decision',undefined,'APROVADO');assert.equal(f.elements['#decision-result'].textContent,'');
  f.elements['#confirm-decision'].checked=true;f.click('confirm-decision',undefined,'APROVADO');assert.match(f.elements['#decision-result'].textContent,/SIMULAÇÃO: APROVADO/);
  f.click('review','DOC-003');assert.match(f.html(),/Período bloqueado/);assert.match(f.html(),/data-action="decision-approve" disabled/);
});
test('missing rule and OFX do not invent accounting proposal or NF-e trail',()=>{
  const f=fixture();f.click('review','DOC-002');f.route('review');assert.ok(!f.html().includes('Conta de débito sintética'));
  f.click('history','DOC-005');assert.match(f.elements['#overlay-content'].innerHTML,/Sem jornada contábil NF-e/);
  assert.ok(!f.elements['#overlay-content'].innerHTML.includes('Regra aplicada'));
});
