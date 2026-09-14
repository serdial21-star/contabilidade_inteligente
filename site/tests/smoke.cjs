const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const root=path.resolve(__dirname,'..');
const html=fs.readFileSync(path.join(root,'index.html'),'utf8');
const legal=fs.readFileSync(path.join(root,'legal.html'),'utf8');
const css=fs.readFileSync(path.join(root,'marketing.css'),'utf8');
const js=fs.readFileSync(path.join(root,'marketing.js'),'utf8');
const decode=value=>decodeURIComponent(value.split('#')[0]);

test('site renders with metadata, header, main and footer',()=>{
  assert.match(html,/<!doctype html>/i);assert.match(html,/<title>[^<]+Serdial21|<title>Serdial21/);
  for(const element of ['<header','<main','<footer','meta name="description"'])assert.ok(html.includes(element),element);
});
test('hero and both demonstration CTAs exist',()=>{
  assert.match(html,/id="hero-title"[^>]*>Inteligência para automatizar/);
  assert.ok((html.match(/href="#demonstracao"/g)||[]).length>=2);assert.match(html,/Conhecer a plataforma/);
});
test('official brand assets and favicon resolve',()=>{
  const refs=[...html.matchAll(/(?:src|href)="([^"#]+\.(?:png|css|js))"/gi)].map(x=>x[1]);
  assert.ok(refs.some(x=>x.includes('S21%20assinatura%20principal.png')));assert.ok(refs.some(x=>x.includes('S21%20logo%20simplificada.png')));
  for(const ref of refs)assert.ok(fs.existsSync(path.resolve(root,decode(ref))),ref);
});
test('main navigation and core commercial sections exist',()=>{
  assert.match(html,/id="main-navigation"/);
  for(const id of ['plataforma','solucoes','contabilidade','linha-decisao','seguranca','escritorios','sobre','demonstracao'])assert.match(html,new RegExp(`id="${id}"`));
  for(const label of ['Minha Visão','Fila Inteligente','Inteligência fiscal','Inteligência financeira','Portal e relacionamento','AccountLock'])assert.ok(html.includes(label),label);
});
test('all same-page links and local document targets resolve',()=>{
  const ids=new Set([...html.matchAll(/\sid="([^"]+)"/g)].map(x=>x[1]));
  for(const [,href] of html.matchAll(/href="([^"]+)"/g)){
    if(href.startsWith('#'))assert.ok(ids.has(href.slice(1)),href);
    else if(!/^(?:https?:|mailto:|tel:)/.test(href)){const [file,fragment]=href.split('#');const target=path.resolve(root,decode(file));assert.ok(fs.existsSync(target),href);if(fragment&&!file.endsWith('app/prototype.html')){const body=fs.readFileSync(target,'utf8');assert.match(body,new RegExp(`id="${fragment}"`),href);}}
  }
});
test('copy contains no prohibited unsupported claims',()=>{
  const forbidden=[/substitui o contador/i,/IA faz tudo/i,/contabilidade sem contador/i,/100% autom[aá]tic/i,/zero erro/i,/sem interven[cç][aã]o humana/i,/totalmente aut[oô]nom/i,/100% segur/i,/invulner[aá]vel/i,/certificad[oa] LGPD/i,/l[ií]der do mercado/i,/mais avan[cç]ado do Brasil/i,/reduza custos em \d+%/i,/economize \d+ horas/i,/integra[cç][aã]o direta com todos os bancos/i,/Open Finance completo/i,/Integra[cç][aã]o Dom[ií]nio/i,/Exporta[cç][aã]o oficial Dom[ií]nio/i,/Parceria com Dom[ií]nio/i];
  for(const claim of forbidden)assert.doesNotMatch(html,claim);
});
test('public files contain no absolute Windows path or obvious secret',()=>{
  const publicText=[html,legal,css,js].join('\n');assert.doesNotMatch(publicText,/[A-Za-z]:\\/);assert.doesNotMatch(publicText,/BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY/);assert.doesNotMatch(publicText,/DATABASE_URL\s*=/);assert.doesNotMatch(publicText,/(?:api[_-]?key|token|password)\s*[:=]\s*["'][^"']+/i);
});
test('form is non-transmitting and legal placeholders are explicit',()=>{
  assert.doesNotMatch(html,/<form[^>]+action=/);assert.match(html,/connect-src 'none'/);assert.match(html,/form-action 'none'/);assert.match(js,/Nenhuma informação foi enviada ou armazenada/);assert.match(legal,/PENDING_LEGAL_APPROVAL/);assert.match(html,/legal\.html#privacidade/);assert.match(html,/legal\.html#termos/);
});
test('SEO and structured data foundation are present without invented proof',()=>{
  for(const field of ['og:type','og:title','og:description','twitter:card'])assert.ok(html.includes(field),field);
  assert.match(html,/"@type":"SoftwareApplication"/);assert.doesNotMatch(html,/aggregateRating|reviewCount|price|award/);assert.match(html,/name="robots" content="noindex,nofollow"/);
});
test('responsive, reduced-motion and JavaScript syntax foundations pass',()=>{
  for(const width of ['1050px','800px','480px'])assert.ok(css.includes(`max-width:${width}`),width);
  assert.match(css,/prefers-reduced-motion:reduce/);new vm.Script(js,{filename:'marketing.js'});
});
