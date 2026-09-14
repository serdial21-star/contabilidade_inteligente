'use strict';
// Presentation only. No fetch, credentials, storage or backend authorization.
(() => {
  const M = window.S21Mock;
  const $ = s => document.querySelector(s);
  const escape = v => String(v ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const paths = {
    grid:'M3 3h7v7H3z M14 3h7v7h-7z M3 14h7v7H3z M14 14h7v7h-7z',
    file:'M6 3h8l4 4v14H6z M14 3v5h4 M9 12h6 M9 16h6',
    check:'M5 12l4 4L19 6', clock:'M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18 M12 7v5l3 2',
    alert:'M12 3L2 21h20z M12 9v5 M12 17v1',lock:'M5 10h14v11H5z M8 10V6a4 4 0 0 1 8 0v4',
    spark:'M12 2l3 7 7 3-7 3-3 7-3-7-7-3 7-3z',user:'M12 3a4 4 0 1 0 0 8 4 4 0 0 0 0-8 M4 21v-3a8 6 0 0 1 16 0v3',
    settings:'M4 6h16 M4 12h16 M4 18h16 M8 3v6 M16 9v6 M10 15v6',
    close:'M6 6l12 12 M18 6L6 18',menu:'M3 6h18 M3 12h18 M3 18h18',
    arrow:'M4 12h16 M14 6l6 6-6 6',bell:'M5 17h14l-2-3V9a5 5 0 0 0-10 0v5z M10 21h4',
    plus:'M12 4v16 M4 12h16',info:'M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18 M12 10v7 M12 7v1'
  };
  const icon = name => `<svg class="icon" viewBox="0 0 24 24" aria-hidden="true"><path d="${paths[name] || paths.info}"/></svg>`;
  const states = {
    IMPORTED:['info','file','Recebido / importado'], EVALUATED:['info','check','Regra avaliada'], VALIDATED:['info','check','Validado'],
    DRAFT:['neutral','file','Rascunho'], IN_REVIEW:['warning','clock','Em revisão'], PENDING_APPROVAL:['warning','clock','Aguardando aprovação'],
    PENDING_RULE:['warning','alert','Exceção · regra pendente'], QUARANTINED:['danger','alert','Em quarentena'],
    APPROVED:['success','check','Aprovado por profissional'], REJECTED:['danger','close','Rejeitado por profissional'],
    BLOCKED:['danger','lock','Bloqueado'], INACTIVE:['neutral','info','Inativo'], PROCESSING:['info','clock','Processando']
  };
  const badge = status => { const [tone,symbol,label] = states[status] || ['neutral','info','Estado indisponível']; return `<span class="badge ${tone}">${icon(symbol)}${label}</span>`; };
  const intelligent = () => `<span class="badge intelligent">${icon('spark')}Sugestão inteligente</span>`;
  const btn = (text, action, variant='secondary', extra='') => `<button type="button" class="btn ${variant}" data-action="${action}" ${extra}>${text}</button>`;
  const alert = (tone,title,text) => `<div class="alert ${tone}">${icon(tone==='error'?'alert':'info')}<div><strong>${title}</strong><p>${text}</p></div></div>`;
  const option = (value, current, label=value) => `<option value="${escape(value)}" ${value===current?'selected':''}>${escape(label)}</option>`;
  let activeWidgets = [...M.presets['Minha Visão']], preset='Minha Visão', editing=false, wide=new Set(), saved=null;
  let currentRecord=M.records[0], selected=new Set(), page=0, sortAsc=true, collapsed=false;
  let filters={search:'',status:'all',company:'all',from:'',to:'',owner:'all'};
  let lastTrigger=null, toastTimer;
  const notice = text => { $('#notice').textContent=text; clearTimeout(toastTimer); toastTimer=setTimeout(()=>$('#notice').textContent='',6500); };
  const brand = (vertical=false) => `<img class="${vertical?'brand-vertical':'brand-image'}" src="../ui/assets/brand/S21%20assinatura%20${vertical?'vertical':'principal'}.png" alt="Serdial21 Contabilidade Inteligente">`;
  const route = () => location.hash.slice(1) || 'dashboard';
  function nav() {
    return `<nav class="nav" aria-label="Navegação principal">${[
      ['INÍCIO','dashboard','grid','Minha Visão'],['OPERAÇÃO','documents','file','Documentos'],
      ['FISCAL','fiscal','file','Fiscal'],['FINANCEIRO','financial','grid','Financeiro'],
      ['CONTÁBIL','proposals','file','Propostas contábeis'],['CLIENTES','clients','user','Clientes'],
      ['OBRIGAÇÕES','obligations','clock','Obrigações'],['GOVERNANÇA','timeline','clock','Linha da Decisão'],
      ['ADMINISTRAÇÃO','settings','settings','Configurações']
    ].map(([group,id,symbol,label])=>`<span class="nav-section">${group}</span><a href="#${id}" title="${label}" ${route()===id?'aria-current="page"':''}>${icon(symbol)}<span class="nav-label">${label}</span></a>`).join('')}</nav>`;
  }
  function shell(content) {
    return `<div class="app-shell ${collapsed?'collapsed':''}"><aside class="sidebar"><a class="brand-link" href="#dashboard">${collapsed?'<img class="brand-image" src="../ui/assets/brand/S21%20logo%20simplificada.png" alt="Serdial21">':brand()}</a><div class="office">${M.office}<small>Ambiente de demonstração</small></div>${nav()}<div class="sidebar-foot">${icon('user')} <span class="nav-label">${M.user}</span><br><small>Profissional fictícia</small><br>${btn(icon('menu')+'<span class="nav-label">Recolher menu</span>','collapse','ghost','aria-label="Alternar menu compacto" aria-expanded="'+(!collapsed)+'"')}</div></aside><div class="workspace"><header class="topbar"><div class="context">${btn(icon('menu'),'mobile-nav','ghost mobile-menu','aria-label="Abrir navegação"')}<span class="eyebrow">Workspace</span><label>Empresa de demonstração<select id="context-company">${option('all',filters.company,'Todas as empresas sintéticas')}${M.companies.map(c=>option(c,filters.company)).join('')}</select></label></div><div class="topbar-actions"><span class="profile-label">${M.date}</span>${btn(icon('bell'),'notifications','ghost','aria-label="Notificações de demonstração"')}<a class="btn ghost" href="#login" aria-label="Perfil e tela de login"><span class="avatar">AE</span><span class="profile-label">${M.user}</span></a></div></header><div class="demo">Protótipo local · Dados sintéticos · Sem sessão autenticada ou decisões reais</div><main id="main" tabindex="-1">${content}<p class="footer-note">Serdial21 Contabilidade Inteligente · A automação prepara. O profissional decide. · <a href="#components">Biblioteca de componentes</a></p></main></div></div>`;
  }
  const heading = (title,description,actions='') => `<div class="page-heading"><div><span class="eyebrow">${M.office}</span><h1>${title}</h1><p>${description}</p></div><div class="actions">${actions}</div></div>`;
  function login() {
    return `<main id="main" class="login-layout" tabindex="-1"><section class="login-brand">${brand()}<div class="gold-line"></div><h1>Inteligência para automatizar.<br>Controle para decidir.</h1><p>Uma rotina organizada. Propostas rastreáveis. A decisão nas mãos do profissional.</p><small class="demo">DEVELOPMENT · Protótipo sintético local</small></section><section class="login-form"><div class="stack"><div><span class="eyebrow">Acesso ao escritório</span><h2>Bem-vindo de volta.</h2><p>Serdial21 Contabilidade Inteligente</p></div><label>E-mail / usuário<input type="email" value="${M.email}" disabled autocomplete="off"></label><label>Senha<input type="password" placeholder="Gerenciada pelo provedor de identidade" disabled autocomplete="off"></label><button class="btn" disabled>Entrar · integração OIDC futura</button>${alert('info','Tela demonstrativa','O acesso real é gerenciado pelo provedor de identidade do escritório. Nenhuma credencial é coletada aqui.')}<small>Recuperação de senha, MFA e login social: não implementados nesta prévia.</small><a class="btn secondary" href="#dashboard">Explorar protótipo sem autenticar ${icon('arrow')}</a></div></section></main>`;
  }
  function widget(w) {
    let body=`<strong class="widget-value">${w.value}</strong>`;
    if(w.type==='PROGRESS') body+='<progress value="5" max="6" aria-label="5 de 6 documentos processados"></progress>';
    if(w.type==='STATUS') body+=badge(w.id==='exceptions'?'PENDING_RULE':'PENDING_APPROVAL');
    if(w.type==='LIST'||w.type==='TIMELINE') body+=`<ul class="widget-list">${w.items.map(x=>`<li>${escape(x)}</li>`).join('')}</ul>`;
    if(w.type==='TABLE_PREVIEW') body+=`<table><caption>Agenda demonstrativa</caption><tbody>${w.items.map(x=>`<tr><td>${escape(x)}</td></tr>`).join('')}</tbody></table>`;
    return `<article class="card widget ${w.tone||''} ${wide.has(w.id)?'wide':''}" data-widget="${w.id}"><div class="widget-title"><h3>${w.label}</h3>${icon(w.type==='TIMELINE'?'clock':'grid')}</div>${body}<p class="widget-note">${w.note}</p>${editing?`<div class="widget-controls">${btn('←','move-left','ghost small',`data-id="${w.id}" aria-label="Mover ${w.label} para antes" ${activeWidgets.indexOf(w.id)===0?'disabled':''}`)}${btn('→','move-right','ghost small',`data-id="${w.id}" aria-label="Mover ${w.label} para depois" ${activeWidgets.indexOf(w.id)===activeWidgets.length-1?'disabled':''}`)}${btn(wide.has(w.id)?'Reduzir':'Ampliar','resize','ghost small',`data-id="${w.id}" aria-label="Redimensionar ${w.label}"`)}${btn('Remover','remove-widget','ghost small',`data-id="${w.id}" aria-label="Remover ${w.label}"`)}</div>`:''}</article>`;
  }
  function queue() {
    const rows=M.records.filter(r=>['PENDING_APPROVAL','PENDING_RULE','BLOCKED'].includes(r.status)&& (filters.company==='all'||r.company===filters.company));
    return `<section class="card"><header class="card-head"><div><h2>Fila Inteligente</h2><p>O que precisa da sua atenção agora.</p></div><span class="badge warning">${rows.length} itens</span></header><div class="table-scroll" tabindex="0" role="region" aria-label="Fila Inteligente rolável"><table><thead><tr><th>Tipo / empresa</th><th>Motivo / recebido em</th><th>Prioridade</th><th>Responsável</th><th>Ação</th></tr></thead><tbody>${rows.map(r=>`<tr><td><strong>${r.type} · ${r.id}</strong><small>${r.company}</small></td><td>${r.reason}<small>${r.date} · ${r.time}</small></td><td><span class="badge ${r.priority==='Alta'?'warning':'neutral'}">${r.priority}</span></td><td>${r.owner}</td><td>${btn('Revisar '+icon('arrow'),'review','ghost',`data-id="${r.id}"`)}</td></tr>`).join('')}</tbody></table></div></section>`;
  }
  function dashboard() {
    return heading('Minha Visão','Bom dia, Ana. Visão Geral — acompanhe o que avançou e o que precisa de decisão.',btn(icon('settings')+' Personalizar','personalize'))+
      `<div class="preset-bar"><label>Organização da visão<select id="preset">${Object.keys(M.presets).map(p=>option(p,preset)).join('')}</select></label><div class="actions">${editing?btn(icon('plus')+' Adicionar widget','add-widget')+btn('Salvar visão nesta sessão','save-view','')+btn('Concluir','personalize','ghost'):intelligent()}</div></div>${filters.company!=='all'?alert('info','Contexto selecionado: '+escape(filters.company),'Os indicadores abaixo demonstram o conjunto global; a fila reflete a empresa selecionada. Agregados por empresa dependem de contrato futuro.'):''}<section class="widgets" aria-label="Widgets da Minha Visão">${activeWidgets.map(id=>widget(M.widgets.find(w=>w.id===id))).join('')||'<p>Nenhum widget na visão. Use Adicionar widget para organizar seu trabalho.</p>'}</section><div class="two-col">${queue()}<section class="card"><header class="card-head"><h2>Atividade recente</h2></header><div class="pad stack">${intelligent()}<p>09:12 · Uma proposta foi preparada automaticamente.</p><span class="decision-label">${icon('check')} APROVADO POR Bruno Exemplo</span><p>13/09/2026, 10:05 · Cenário fictício DOC-004.</p>${btn('Linha da Decisão '+icon('arrow'),'history','secondary','data-id="DOC-004"')}</div></section></div>`;
  }
  function visibleRecords() {
    return M.records.filter(r=>(route()!=='proposals'||r.proposal)&&(!filters.search||`${r.id} ${r.name} ${r.owner}`.toLocaleLowerCase('pt-BR').includes(filters.search.toLocaleLowerCase('pt-BR')))&&(filters.status==='all'||r.status===filters.status)&&(filters.company==='all'||r.company===filters.company)&&(filters.owner==='all'||r.owner===filters.owner)&&(!filters.from||r.date>=filters.from)&&(!filters.to||r.date<=filters.to)).sort((a,b)=>sortAsc?a.id.localeCompare(b.id):b.id.localeCompare(a.id));
  }
  function tableBody() {
    const all=visibleRecords(); page=Math.min(page,Math.max(0,Math.ceil(all.length/4)-1));
    const rows=all.slice(page*4,page*4+4);
    return `<div class="table-scroll" tabindex="0" role="region" aria-label="Tabela de documentos rolável"><table><thead><tr><th><label class="check"><input id="select-page" type="checkbox" aria-label="Selecionar registros desta página" ${rows.length&&rows.every(r=>selected.has(r.id))?'checked':''} ${rows.length?'':'disabled'}></label></th><th aria-sort="${sortAsc?'ascending':'descending'}">${btn('Documento '+(sortAsc?'↑':'↓'),'sort','ghost small')}</th><th>Empresa</th><th>Status</th><th>Responsável</th><th>Ações</th></tr></thead><tbody>${rows.map(r=>`<tr class="${selected.has(r.id)?'selected-row':''}"><td><input type="checkbox" data-select="${r.id}" aria-label="Selecionar ${r.id}" ${selected.has(r.id)?'checked':''}></td><td><strong>${r.id}</strong><small>${r.name}</small></td><td>${r.company}</td><td>${badge(r.status)}</td><td>${r.owner}</td><td><div class="actions">${btn('Detalhes','details','ghost small',`data-id="${r.id}"`)}${btn('Revisar','review','secondary small',`data-id="${r.id}"`)}${btn('Ver histórico','history','ghost small',`data-id="${r.id}"`)}</div></td></tr>`).join('')||`<tr><td colspan="6"><div class="empty">${icon('file')}<h3>Nenhum item corresponde aos filtros.</h3><p>Ajuste o período ou limpe os filtros para continuar.</p>${btn('Limpar filtros','clear-filters')}</div></td></tr>`}</tbody></table></div><div class="table-footer"><span role="status">${all.length} resultados · ${selected.size} selecionados · Página ${page+1} de ${Math.max(1,Math.ceil(all.length/4))}</span><div class="actions">${btn('Anterior','previous','ghost',page===0?'disabled':'')}${btn('Próxima','next','ghost',(page+1)*4>=all.length?'disabled':'')}</div></div>`;
  }
  function documents() {
    const proposals=route()==='proposals';
    return heading(proposals?'Propostas contábeis':'Documentos','Dados fictícios para demonstrar consulta, filtros e rastreabilidade.',btn('Receber documento','upload'))+`<section class="card"><div class="filters"><label>Pesquisar<input id="search" type="search" value="${escape(filters.search)}" placeholder="Documento ou responsável"></label><label>Status<select id="status-filter">${option('all',filters.status,'Todos os status')}${Object.keys(states).filter(k=>M.records.some(r=>r.status===k)).map(k=>option(k,filters.status,states[k][2])).join('')}</select></label>${btn(icon('settings')+' Filtros avançados','filters')}${btn('Limpar','clear-filters','ghost')}</div><div id="table-content">${tableBody()}</div></section>`;
  }
  function trail(r) {
    const entries=r.type==='OFX'?[['SOURCE',r.time,'Extrato recebido','Cenário OFX sintético'],['PROCESSING',r.time,'Importação demonstrada','Sem jornada contábil NF-e']]:r.status==='PENDING_RULE'?[...M.trail.slice(0,2),['RULE','09:12','Regra pendente','Nenhuma proposta gerada']]:[...M.trail,['REVIEW','10:03',r.status==='APPROVED'||r.status==='REJECTED'?'Revisado por '+r.owner:'Revisão pendente',r.status==='APPROVED'||r.status==='REJECTED'?'Evento exclusivamente fictício da demonstração':'Abrir esta tela não registra revisão'],['APPROVAL',r.status==='APPROVED'||r.status==='REJECTED'?'10:05':'—',r.status==='APPROVED'?'Aprovado por '+r.owner:r.status==='REJECTED'?'Rejeitado por '+r.owner:r.status==='BLOCKED'?'Aprovação bloqueada':'Aguardando aprovação','Nenhum efeito real ou AuditEvent criado']];
    return `<ol class="timeline">${entries.map(([phase,time,title,description])=>`<li><span class="step-icon">${icon(phase==='APPROVAL'?'user':phase==='RULE'?'spark':'clock')}</span><span class="eyebrow">${phase}</span><br><strong>${title}</strong><p>${r.date} · ${time}</p><p>${description}</p>${phase==='RULE'&&r.status!=='PENDING_RULE'?intelligent():''}</li>`).join('')}</ol>`;
  }
  function review() {
    const r=currentRecord, actionable=r.status==='PENDING_APPROVAL';
    return heading('Revisão da proposta',r.id+' · '+r.company,btn('Linha da Decisão','history','secondary',`data-id="${r.id}"`))+`<div class="stack">${r.status==='BLOCKED'?alert('error','Período bloqueado',`${M.lock.reason}. Escopo: ${M.lock.scope}. Criado por ${M.lock.actor}, ${M.lock.date}. Aprovação, edição e rejeição estão indisponíveis neste cenário.`):''}${r.status==='PENDING_RULE'?alert('warning','Regra pendente','Nenhuma proposta foi gerada. Resolva a pendência no fluxo autorizado antes de solicitar aprovação.'):''}<div class="two-col"><section class="card pad stack"><div class="actions">${badge(r.status)}${r.proposal?intelligent():''}</div><dl class="detail-grid"><div><dt>SOURCE · origem</dt><dd>${r.name}</dd></div><div><dt>RULE APPLIED · regra aplicada</dt><dd>${r.proposal?M.rule:'Não disponível'}</dd></div><div><dt>EVIDENCE · evidência</dt><dd>Fixture ilustrativa ${r.id}; sem arquivo real</dd></div><div><dt>STATUS · revisão</dt><dd>${r.proposal?'Revisão demonstrativa v1':'Proposta indisponível'}</dd></div></dl>${r.proposal?`<div class="account-lines"><div class="account-line"><span class="eyebrow">DÉBITO</span><strong>${M.amount}</strong><p>${M.debit}</p></div><div class="account-line"><span class="eyebrow">CRÉDITO</span><strong>${M.amount}</strong><p>${M.credit}</p></div></div><span class="badge success">${icon('check')}BALANCEADO · exemplo visual</span><small>Contas fictícias sem códigos ou validade contábil. Nenhuma regra ou conta é cadastrada.</small>`:''}<div class="actions">${btn('Aprovar','decision-approve','',actionable?'':'disabled')}${btn('Editar','edit-proposal','secondary',actionable?'':'disabled')}${btn('Rejeitar','decision-reject','danger',actionable?'':'disabled')}</div><p id="decision-result" role="status">${r.status==='APPROVED'?'APROVADO POR '+r.owner+' · '+r.date+' 10:05 · Cenário fictício':r.status==='REJECTED'?'REJEITADO POR '+r.owner+' · '+r.date+' 10:05 · Cenário fictício':'Ações demonstrativas. Nenhuma decisão é enviada ou persistida.'}</p></section><aside class="card pad stack"><h2>Conferência profissional</h2><p>Compare origem, regra e valores antes de decidir.</p><label class="check"><input type="checkbox" id="review-check" ${actionable?'':'disabled'}> Conferi o exemplo visual</label>${alert('info','Decisão deliberada','A confirmação exibirá apenas um resultado de simulação. A revisão/hash, os acessos e bloqueios reais pertencem ao backend.')}<a class="btn ghost" href="#proposals">Voltar às propostas</a></aside></div></div>`;
  }
  function settings() {
    return heading('Configurações da Minha Visão','Preferências organizam conteúdo; não concedem acesso.')+`<div class="two-col"><section class="card pad stack"><h2>Personalização</h2><label>Preset<select id="preset">${Object.keys(M.presets).map(p=>option(p,preset)).join('')}</select></label><div class="actions">${btn('Organizar widgets','go-personalize')}${btn('Restaurar visão salva nesta sessão','restore-view','secondary',saved?'':'disabled')}${btn('Descartar personalização','reset-view','danger')}</div>${alert('info','Somente nesta sessão','Salvar visão mantém o layout apenas em memória. Recarregar a página descarta a personalização.')}<fieldset><legend>Densidade</legend><label class="check"><input type="radio" checked name="density"> Comfortable</label><label class="check"><input type="radio" disabled name="density"> Compact · futura</label></fieldset></section><section class="card pad stack"><h2>Visibilidade e acesso</h2><p>VISIBILITY ≤ AUTHORIZATION</p><p>O menu apenas refletirá as permissões fornecidas pelo backend. O catálogo demonstrativo não representa permissões de um usuário real.</p>${btn('Ver exemplo sem permissão','permission')}${btn('Abrir biblioteca de componentes','components','ghost')}</section></div>`;
  }
  function components() {
    return heading('Biblioteca de componentes','Fundação visual · estados e padrões reutilizáveis')+`<div class="stack"><section class="card pad stack"><h2>Marca e cores oficiais</h2><div class="swatches">${[['navy','Azul','#17295B'],['gold','Ouro','#DAA84F'],['red','Vermelho','#D8232A'],['white','Branco','#FFFFFF'],['gray','Cinza','#F3F4F6']].map(([c,n,v])=>`<div class="swatch ${c}">${n}<br>${v}</div>`).join('')}</div><details><summary>Assinatura vertical oficial</summary>${brand(true)}</details><h2>Botões</h2><div class="actions">${['','secondary','tertiary','ghost','danger'].map(v=>btn(v||'Primary','info-modal',v)).join('')}${btn('Small','info-modal','secondary small')}${btn('Large','info-modal','secondary large')}${btn('Desabilitado','info-modal','','disabled')}</div><h2>Status e linguagem</h2><div class="actions">${Object.keys(states).map(badge).join('')}${intelligent()}</div></section><section class="card pad stack"><h2>Formulários</h2><div class="form-grid"><label>Texto<input placeholder="Nome da visão"></label><label>Somente leitura<input readonly value="Escritório Demonstração"></label><label>Desabilitado<input disabled value="Integração futura"></label><label>Erro<input aria-invalid="true" aria-describedby="field-error" value=""><span class="field-error" id="field-error">Informe um nome para a visão.</span></label><label class="field-success">Sucesso<input value="Minha rotina" aria-describedby="field-success"><small id="field-success">✓ Nome disponível neste exemplo.</small></label><label>Data<input type="date"></label><label>Valor monetário (texto; sem cálculo)<input inputmode="decimal" placeholder="R$ 0,00"></label><label>Empresa<select>${M.companies.map(c=>option(c,'')).join('')}</select></label><label>Múltipla seleção<select multiple size="2" aria-describedby="multi-help">${M.companies.map(c=>option(c,'')).join('')}</select><small id="multi-help">Use Ctrl/Cmd ou Shift com as setas para selecionar.</small></label><label>Observação<textarea rows="3" placeholder="Somente dados fictícios"></textarea></label><label>Arquivo (não implementado)<input type="file" disabled><small>Nenhum arquivo é lido neste protótipo.</small></label><fieldset><legend>Controles de seleção</legend><label class="check"><input type="checkbox"> Exibir resumo</label><label class="check"><input type="radio" name="demo-radio" checked> Opção A</label><label class="check"><input type="radio" name="demo-radio"> Opção B</label><label class="check"><input type="checkbox" role="switch"> Destaques visuais</label></fieldset></div></section><section class="card pad stack"><h2>Alertas, modais e drawers</h2>${alert('info','Informação','Este exemplo é local e sintético.')}${alert('success','Preferência salva','Somente durante esta sessão.')}${alert('warning','Conferência necessária','Revise a proposta antes de decidir.')}${alert('error','Ação indisponível','Não foi possível concluir a solicitação.')}<div class="actions">${btn('Informação','info-modal')}${btn('Formulário','form-modal')}${btn('Confirmação','confirmation-modal')}${btn('Destrutiva','reset-view','danger')}${btn('Drawer / histórico','history','secondary',`data-id="${currentRecord.id}"`)}</div></section><section class="card pad stack"><h2>Vazio, carregamento e erros</h2><div class="empty">${icon('file')}<h3>Nenhuma proposta aguardando revisão.</h3><p>Consulte os documentos recebidos para acompanhar novas propostas.</p><a class="btn secondary" href="#documents">Ver documentos</a></div><div aria-label="Exemplo de conteúdo em carregamento" role="status"><span>Carregando indicadores…</span><div class="skeleton metric" aria-hidden="true"></div><div class="skeleton" aria-hidden="true"></div></div><div class="loading" role="status"><span class="spinner" aria-hidden="true"></span>Carregando detalhes…</div>${alert('error','Erro na página','Não foi possível carregar esta visão. Tente novamente.')}${alert('error','Erro no campo','Revise o valor informado.')}${alert('warning','Falha temporária','O serviço está temporariamente indisponível. Tente novamente em instantes.')}<div class="actions">${btn('Sem permissão','permission')}${btn('Não encontrado','not-found')}${btn('Tentar novamente (simulação)','retry')}</div></section></div>`;
  }
  function render(focus=true) {
    const pages={dashboard,documents,proposals:documents,review,settings,components,timeline:()=>heading('Linha da Decisão',currentRecord.id+' · histórico exclusivamente sintético')+`<section class="card pad">${trail(currentRecord)}</section>`};
    if(route()==='login') $('#app').innerHTML=login();
    else $('#app').innerHTML=shell(pages[route()]?pages[route()]():heading(({fiscal:'Fiscal',financial:'Financeiro',clients:'Clientes',obligations:'Obrigações'})[route()]||'Recurso indisponível','Fundação de navegação')+alert('info','Página conceitual','Este módulo completo pertence a uma fase futura. Explore Documentos ou Propostas para navegar pelos exemplos.'));
    document.title=($('#main h1')?.textContent || 'Login')+' · Serdial21 Contabilidade Inteligente';
    if(focus) $('#main')?.focus({preventScroll:true});
  }
  function open(title,content,drawer=false) {
    const dialog=$('#overlay'); lastTrigger=document.activeElement;
    dialog.className=drawer?'drawer':'';
    $('#overlay-content').innerHTML=`<div class="dialog-heading"><h2 id="overlay-title">${title}</h2>${btn(icon('close'),'close','ghost','aria-label="Fechar diálogo"')}</div>${content}`;
    dialog.showModal();
  }
  const close=()=>$('#overlay').close();
  $('#overlay').addEventListener('close',()=>{ if(lastTrigger?.isConnected) lastTrigger.focus(); else $('#main')?.focus({preventScroll:true}); });
  function refreshTable() { if($('#table-content')) $('#table-content').innerHTML=tableBody(); }
  document.addEventListener('input',event=>{if(event.target.id==='search'){filters.search=event.target.value;page=0;refreshTable();}});
  document.addEventListener('change',event=>{
    const el=event.target;
    if(el.id==='preset'){preset=el.value;activeWidgets=[...M.presets[preset]];wide.clear();render(false);$('#preset')?.focus();}
    if(el.id==='status-filter'){filters.status=el.value;page=0;refreshTable();}
    if(el.id==='context-company'){filters.company=el.value;page=0;render(false);$('#context-company')?.focus();}
    if(el.dataset.select){el.checked?selected.add(el.dataset.select):selected.delete(el.dataset.select);refreshTable();document.querySelector(`[data-select="${el.dataset.select}"]`)?.focus();}
    if(el.id==='select-page'){visibleRecords().slice(page*4,page*4+4).forEach(r=>el.checked?selected.add(r.id):selected.delete(r.id));refreshTable();$('#select-page')?.focus();}
  });
  document.addEventListener('click',event=>{
    if(event.target.closest('a[href^="#"]') && $('#overlay').open) close();
    const el=event.target.closest('[data-action]'); if(!el||el.disabled)return;
    const action=el.dataset.action,id=el.dataset.id;
    if(id&&M.records.some(r=>r.id===id)) currentRecord=M.records.find(r=>r.id===id);
    if(action==='close')return close();
    if(action==='collapse'){collapsed=!collapsed;render(false);document.querySelector('[data-action="collapse"]')?.focus();}
    if(action==='mobile-nav')open('Navegação',`<aside class="sidebar mobile">${nav()}</aside>`,true);
    if(action==='personalize'){editing=!editing;render(false);document.querySelector('[data-action="personalize"]')?.focus();}
    if(action==='go-personalize'){editing=true;location.hash='dashboard';}
    if(action==='save-view'){saved={widgets:[...activeWidgets],wide:[...wide],preset};notice('Visão salva somente nesta sessão. Recarregar descarta as preferências.');}
    if(action==='restore-view'&&saved){activeWidgets=[...saved.widgets];wide=new Set(saved.wide);preset=saved.preset;render(false);notice('Visão da sessão restaurada.');}
    if(action==='add-widget')open('Adicionar widget',`<div class="stack"><p>Catálogo sintético; não representa concessão de permissões.</p>${M.widgets.filter(w=>!activeWidgets.includes(w.id)).map(w=>btn(w.label+' · '+w.type,'insert-widget','secondary',`data-id="${w.id}"`)).join('')||'<p>Todos os widgets já estão na visão.</p>'}</div>`);
    if(action==='insert-widget'){activeWidgets.push(id);close();render(false);notice('Widget adicionado.');}
    if(['move-left','move-right','resize','remove-widget'].includes(action)){
      const index=activeWidgets.indexOf(id);
      if(action==='resize')wide.has(id)?wide.delete(id):wide.add(id);
      else if(action==='remove-widget')activeWidgets=activeWidgets.filter(x=>x!==id);
      else {const next=index+(action==='move-left'?-1:1);if(next>=0&&next<activeWidgets.length)[activeWidgets[index],activeWidgets[next]]=[activeWidgets[next],activeWidgets[index]];}
      render(false);document.querySelector(`[data-widget="${id}"] button:not(:disabled)`)?.focus();if(action==='remove-widget')document.querySelector('[data-action="add-widget"]')?.focus();notice('Organização atualizada somente no protótipo.');
    }
    if(action==='review'){location.hash='review';if(route()==='review')render();}
    if(action==='history')open('Linha da Decisão · '+currentRecord.id,trail(currentRecord)+`<div class="actions"><a class="btn secondary" href="#timeline">Abrir página de histórico</a></div>`,true);
    if(action==='details')open(currentRecord.id+' · Detalhes',`<div class="stack">${badge(currentRecord.status)}<p>${currentRecord.name}</p><p>${currentRecord.company} · ${currentRecord.owner}</p><p>${currentRecord.reason}</p>${btn('Linha da Decisão','replace-history')}${btn('Abrir revisão','open-review')}</div>`,true);
    if(action==='replace-history'){close();open('Linha da Decisão · '+currentRecord.id,trail(currentRecord),true);}
    if(action==='open-review'){close();location.hash='review';}
    if(action==='filters')open('Filtros avançados',`<form id="filter-form" class="stack"><label>Empresa<select name="company">${option('all',filters.company,'Todas')}${M.companies.map(c=>option(c,filters.company)).join('')}</select></label><label>Responsável<select name="owner">${option('all',filters.owner,'Todos')}${M.owners.map(c=>option(c,filters.owner)).join('')}</select></label><label>De<input type="date" name="from" value="${filters.from}"></label><label>Até<input type="date" name="to" value="${filters.to}"></label><p id="filter-error" role="alert"></p><button class="btn" type="submit">Aplicar filtros</button></form>`,true);
    if(action==='clear-filters'){filters={search:'',status:'all',company:'all',from:'',to:'',owner:'all'};page=0;render(false);$('#search')?.focus();}
    if(action==='sort'){sortAsc=!sortAsc;refreshTable();document.querySelector('[data-action="sort"]')?.focus();}
    if(action==='previous'||action==='next'){page+=action==='previous'?-1:1;refreshTable();$('#table-content')?.querySelector('button:not(:disabled)')?.focus();}
    if(action==='decision-approve'||action==='decision-reject'){
      if(!$('#review-check')?.checked){notice('Marque a conferência do exemplo antes de simular uma decisão.');$('#review-check')?.focus();return;}
      open(action==='decision-approve'?'Simular aprovação':'Simular rejeição',`<div class="stack"><p>${currentRecord.id} · revisão ilustrativa v1. Esta ação não grava uma decisão real.</p><label class="check"><input id="confirm-decision" type="checkbox"> Confirmo que desejo simular esta decisão</label>${btn('Confirmar simulação','confirm-decision',action==='decision-approve'?'':'danger',`data-decision="${action==='decision-approve'?'APROVADO':'REJEITADO'}"`)}</div>`);
    }
    if(action==='confirm-decision'){if(!$('#confirm-decision').checked){$('#confirm-decision').focus();return;}const result=el.dataset.decision;close();$('#decision-result').textContent=`SIMULAÇÃO: ${result} POR ${M.user} · ${M.date}, 10:05. Sem persistência ou alteração da evidência.`;notice('Simulação concluída. Nenhum AuditEvent foi criado.');}
    if(action==='edit-proposal')open('Editar proposta · escopo futuro',alert('info','Sem edição contábil nesta fase','A edição real exige revisão versionada e contrato autorizado. Este protótipo não modifica valores, contas ou regras.'));
    if(action==='reset-view')open('Descartar personalização',`<div class="stack"><p>Remove somente o layout desta sessão e restaura Minha Visão. Documentos e dados não são afetados.</p><label class="check"><input id="confirm-reset" type="checkbox"> Confirmo descartar minha personalização local</label>${btn('Descartar layout local','confirm-reset','danger')}</div>`);
    if(action==='confirm-reset'){if(!$('#confirm-reset').checked){$('#confirm-reset').focus();return;}activeWidgets=[...M.presets['Minha Visão']];preset='Minha Visão';wide.clear();saved=null;close();render(false);notice('Layout local restaurado.');}
    if(action==='upload')open('Receber documento',alert('info','Upload futuro','A API existente recebe bytes NF-e/OFX com identidade e permissões. Este exemplo não lê nem envia arquivos.')+'<label>Arquivo<input type="file" disabled></label>');
    if(action==='permission')open('Acesso não permitido',alert('error','Sem permissão','Você não possui permissão para acessar este recurso.'));
    if(action==='not-found')open('Recurso indisponível',alert('info','Não encontrado','Não foi possível disponibilizar o recurso solicitado.'));
    if(action==='notifications')open('Notificações',alert('info','Demonstração local','Notificações reais ainda não estão integradas. A Fila Inteligente mostra pendências sintéticas.'));
    if(action==='info-modal')open('Modal de informação',alert('info','Fundação visual','Componentes locais para demonstrar o produto.'));
    if(action==='form-modal')open('Modal de formulário','<form id="sample-form" class="stack"><label>Nome da visão<input name="view" required maxlength="60"></label><button class="btn" type="submit">Demonstrar envio local</button></form>');
    if(action==='confirmation-modal')open('Modal de confirmação',`<p>Confirmar apenas a demonstração desta mensagem?</p><div class="actions">${btn('Cancelar','close')}${btn('Confirmar demonstração','confirm-info','')}</div>`);
    if(action==='confirm-info'){close();notice('Demonstração confirmada.');}
    if(action==='retry')notice('Nova tentativa simulada; sem conexão com serviços.');
    if(action==='components')location.hash='components';
  });
  document.addEventListener('submit',event=>{
    event.preventDefault();
    if(event.target.id==='filter-form'){
      const data=new FormData(event.target),from=data.get('from'),to=data.get('to');
      if(from&&to&&from>to){$('#filter-error').textContent='A data inicial deve ser anterior ou igual à final.';return;}
      Object.assign(filters,{company:data.get('company'),owner:data.get('owner'),from,to});page=0;close();render(false);$('#search')?.focus();
    }
    if(event.target.id==='sample-form'){close();notice('Formulário demonstrado. Nenhum dado foi armazenado.');}
  });
  window.addEventListener('hashchange',()=>{if($('#overlay').open)close();page=0;render();window.scrollTo(0,0);});
  render(false);
})();
