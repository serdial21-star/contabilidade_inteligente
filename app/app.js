(function startApplication(root) {
  'use strict';
  const {STATES, createSessionStore, allowedNavigation, hasPermission} = root.S21Core;
  const config = root.S21_CONFIG;
  const session = createSessionStore();
  const app = document.querySelector('#app');
  const announcer = document.querySelector('#announcer');
  let companyId = null;
  let drawerOpen = false;
  let userMenuOpen = false;
  let dashboardLayout = null;
  let dashboardModel = null;
  let dashboardEditing = false;
  let dashboardRequest = 0;
  let operationalModel = null;
  let operationalRequest = 0;
  let documentFilters = Object.freeze({search: '', status: '', source: '', received_from: '', received_to: '', offset: 0, limit: 10});
  let intelligenceModel = null;
  let intelligenceRequest = 0;
  let importFeedback = null;
  let pendingNfeFiles = [];
  let workContext = null;
  let workContextSettings = null;
  let workContextDialogOpen = false;
  let fiscalFilters = Object.freeze({search: '', status: '', issued_from: '', issued_to: '', offset: 0, limit: 10});
  let statementFilters = Object.freeze({offset: 0, limit: 10});
  let transactionFilters = Object.freeze({search: '', direction: '', posted_from: '', posted_to: '', offset: 0, limit: 25});
  let accountingModel = null;
  let accountingRequest = 0;
  let proposalFilters = Object.freeze({status: '', account: '', source: '', document: '', rule: '', created_from: '', created_to: '', offset: 0, limit: 10});
  let itemQueueFilters = Object.freeze({offset: 0, limit: 10});
  let catalogSearch = '';
  let decisionIntent = null;
  let decisionFeedback = null;
  let itemDecisionOpen = false;
  let itemDecisionFeedback = null;

  const apiClient = root.S21ApiClient.createApiClient({
    baseUrl: config.apiBaseUrl,
    getAccessToken: session.token,
    onAuthenticationFailure: () => { session.expire(); renderLogin(); },
  });
  const oidcClient = root.S21OidcClient.createOidcClient({config, getAccessToken: session.token});
  const dashboardService = root.S21Dashboard.createDashboardService({
    dataMode: config.dataMode,
    apiClient,
    syntheticProvider: root.S21SyntheticProvider,
  });
  const workContextService = root.S21WorkContext.createWorkContextService();
  const operationalService = root.S21Operational.createOperationalService({
    dataMode: config.dataMode, apiClient, syntheticProvider: root.S21SyntheticProvider,
  });
  const intelligenceService = root.S21Intelligence.createIntelligenceService({
    dataMode: config.dataMode, apiClient, syntheticProvider: root.S21SyntheticProvider,
  });
  const accountingService = root.S21Accounting.createAccountingService({
    dataMode: config.dataMode, apiClient, syntheticProvider: root.S21SyntheticProvider,
  });

  const navigation = Object.freeze([
    {group: 'Principal', id: 'overview', label: 'Minha Visão', permissions: ['company.read']},
    {group: 'Operação', id: 'inbox', label: 'Caixa de entrada', permissions: ['company.read']},
    {group: 'Operação', id: 'documents', label: 'Documentos', permissions: ['company.read']},
    {group: 'Operação', id: 'fiscal', label: 'Fiscal · NF-e', permissions: ['company.read']},
    {group: 'Operação', id: 'financial', label: 'Financeiro · OFX', permissions: ['company.read']},
    {group: 'Operação', id: 'accounting', label: 'Contábil', permissions: ['journal.read']},
    {group: 'Relacionamento', id: 'clients', label: 'Empresas', permissions: ['company.read']},
    {group: 'Relacionamento', id: 'obligations', label: 'Obrigações', permissions: [], planned: true},
    {group: 'Controle', id: 'governance', label: 'Governança', permissions: ['audit.read', 'lock.manage']},
    {group: 'Controle', id: 'administration', label: 'Administração', permissions: ['identity.manage', 'catalog.manage']},
  ]);

  const escapeHtml = (value) => String(value).replace(/[&<>'"]/g, (character) => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[character]));
  const initials = (name) => name.split(/\s+/).slice(0, 2).map((part) => part[0]).join('').toUpperCase();
  const route = () => (location.hash.slice(1) || 'overview').split('?')[0];
  const routeParams = () => new URLSearchParams((location.hash.split('?')[1] || ''));
  const setAnnouncement = (message) => { announcer.textContent = ''; root.setTimeout(() => { announcer.textContent = message; }, 0); };
  const authorizedRoute = (profile, requested = route()) => {
    const permissions = currentPermissions(profile);
    const candidate = navigation.find((item) => item.id === requested && !item.planned
      && hasPermission(permissions, item.permissions));
    return candidate?.id || allowedNavigation(navigation, permissions).find((item) => !item.planned)?.id || 'overview';
  };

  function decisionLineMarkup(line) {
    if (!line) return '';
    const actorLabels = {AUTOMATED: 'Automação', PROFESSIONAL_ACTION: 'Ação profissional', SYSTEM_GOVERNANCE: 'Governança do sistema'};
    const gapLabels = {DISTINCT_REVIEW_ACTION_NOT_AVAILABLE: 'Ação de revisão distinta ainda não disponível', REJECTION_REASON_NOT_AVAILABLE: 'Motivo estruturado de rejeição não disponível', CORRELATED_AUDIT_NOT_AVAILABLE: 'Auditoria correlacionada não disponível', AUDIT_INTEGRITY_NOT_CONFIRMED: 'Integridade de auditoria não confirmada', UNMAPPED_AUDIT_ACTION: 'Existe evento ainda sem apresentação específica'};
    const events = line.events.map((event) => `<li class="decision-event"><span class="decision-marker" aria-hidden="true"></span><div><div class="decision-meta"><span class="badge neutral">${escapeHtml(event.category)}</span><span>${escapeHtml(actorLabels[event.actor_kind] || 'Origem não identificada')}</span><time datetime="${escapeHtml(event.occurred_at)}">${escapeHtml(formatDate(event.occurred_at))}</time></div><h3>${escapeHtml(event.title)}</h3><p>${escapeHtml(event.description)}</p><small>${escapeHtml(event.actor_display_name)} · ${escapeHtml(event.evidence_kind === 'DOMAIN_DERIVED_EVENT' ? 'Estado de domínio derivado' : 'Evento de auditoria')}</small></div></li>`).join('');
    const gaps = line.data_gaps.length
      ? `<div class="alert info"><div><strong>Rastreabilidade parcial</strong><p>${line.data_gaps.map((gap) => escapeHtml(gapLabels[gap] || 'Evidência complementar indisponível')).join(' · ')}</p></div></div>` : '';
    return `<section class="card decision-line" aria-labelledby="decision-line-title"><div class="decision-line-heading"><div><span class="eyebrow">Linha da Decisão</span><h2 id="decision-line-title">Como este estado foi formado</h2></div><span class="badge ${line.completeness === 'COMPLETE' ? 'success' : 'warning'}">${escapeHtml(line.completeness)}</span></div>${gaps}<ol class="decision-events">${events || '<li>Nenhuma evidência correlacionada disponível.</li>'}</ol><p class="row-note">Projeção somente leitura. Não representa escrituração, saldo ou fechamento oficial.</p></section>`;
  }

  function currentPermissions(profile) {
    const tenantPermissions = profile.permissions || [];
    if (companyId === dashboardService.allAuthorizedId) {
      const companySets = profile.companies.map((company) => new Set(company.permissions || []));
      const shared = companySets.length
        ? [...companySets[0]].filter((permission) => companySets.every((set) => set.has(permission)))
        : [];
      return [...new Set([...tenantPermissions, ...shared])];
    }
    const company = profile.companies.find((item) => item.id === companyId);
    return [...new Set([...tenantPermissions, ...(company?.permissions || [])])];
  }

  function normalizeCurrentApplication(current) {
    return Object.freeze({
      user: Object.freeze({id: current.user.id, displayName: current.user.display_name, roleLabel: ''}),
      tenant: Object.freeze({id: current.tenant.id, name: current.tenant.display_name}),
      companies: Object.freeze(current.companies.map((company) => Object.freeze({
        id: company.id, name: company.display_name,
        permissions: Object.freeze([...company.permissions]),
      }))),
      permissions: Object.freeze([...current.permissions]),
    });
  }

  function renderLogin(message = '') {
    const state = session.snapshot().state;
    const expired = state === STATES.SESSION_EXPIRED;
    const authenticating = state === STATES.AUTHENTICATING;
    const synthetic = config.authMode === 'synthetic' && config.environment === 'development';
    const oidcConfigured = oidcClient.isConfigured();
    const configurationError = (config.authMode === 'oidc' && !oidcConfigured)
      || (config.authMode === 'synthetic' && config.environment !== 'development');
    const title = configurationError ? 'Autenticação não configurada neste ambiente.'
      : message || (synthetic ? 'Modo sintético habilitado explicitamente.' : 'Acesse com o provedor de identidade do escritório.');
    app.innerHTML = `<main id="main" class="login-layout" tabindex="-1">
      <section class="login-brand"><img class="brand-vertical" src="../ui/assets/brand/S21%20assinatura%20vertical.png" alt="Serdial21 Contabilidade Inteligente"><div class="gold-line"></div><h1>Inteligência para automatizar.<br>Controle para decidir.</h1><p>Ambiente de trabalho seguro para a rotina do escritório contábil.</p></section>
      <section class="login-form"><div class="stack">
        <div class="actions"><span class="environment-banner">${escapeHtml(config.environmentLabel)}</span>${synthetic ? '<span class="badge intelligent">DADOS SINTÉTICOS</span>' : ''}</div>
        <div><span class="eyebrow">Acesso ao aplicativo</span><h2>Bem-vindo.</h2><p>Suas credenciais são tratadas somente pelo provedor de identidade.</p></div>
        ${expired ? '<div class="alert warning" role="alert"><div><strong>Sessão expirada</strong><p>Sua sessão expirou. Entre novamente para continuar.</p></div></div>' : ''}
        <div id="auth-feedback" class="alert ${configurationError ? 'error' : 'info'}" role="status" aria-live="polite"><div><strong>${authenticating ? 'Autenticando com segurança' : configurationError ? 'Configuração necessária' : 'Ambiente controlado'}</strong><p>${escapeHtml(authenticating ? 'Aguarde a resposta do provedor de identidade.' : title)}</p></div></div>
        ${config.authMode === 'oidc' ? `<button class="btn" type="button" data-action="begin-login" ${oidcConfigured && !authenticating ? '' : 'disabled'}>${authenticating ? '<span class="spinner" aria-hidden="true"></span>Autenticando…' : 'Entrar'}</button>` : ''}
        ${synthetic ? '<div class="demo-entry"><strong>AMBIENTE DE DESENVOLVIMENTO</strong><p>Esta entrada usa identidade, empresas e permissões fictícias. Não concede acesso à API.</p><button class="btn secondary" type="button" data-action="start-demo">Abrir demonstração sintética</button></div>' : ''}
        <small class="login-help">Authorization Code + PKCE. MFA, recuperação de senha e revogação global pertencem ao IdP aprovado.</small>
      </div></section></main>`;
    app.setAttribute('aria-busy', 'false');
    document.querySelector('[data-action="begin-login"]:not([disabled]), [data-action="start-demo"]')?.focus();
  }

  function renderState(state) {
    const states = {
      [STATES.FORBIDDEN]: ['Acesso não permitido', 'Você não possui permissão para acessar este recurso.', 'Voltar'],
      [STATES.NETWORK_ERROR]: ['Não foi possível conectar', 'Verifique sua conexão e tente novamente.', 'Tentar novamente'],
      [STATES.SERVER_ERROR]: ['Serviço temporariamente indisponível', 'Não foi possível concluir a solicitação agora.', 'Tentar novamente'],
    };
    const [title, text, action] = states[state] || states[STATES.SERVER_ERROR];
    app.innerHTML = `<main id="main" class="page-state" tabindex="-1"><section class="card"><img width="76" src="../ui/assets/brand/S21%20logo%20simplificada.png" alt=""><span class="eyebrow">Serdial21</span><h1>${title}</h1><p>${text}</p><button class="btn" data-action="safe-return">${action}</button></section></main>`;
    app.setAttribute('aria-busy', 'false');
    document.querySelector('[data-action="safe-return"]').focus();
  }

  function navMarkup(profile) {
    let group = '';
    return allowedNavigation(navigation, currentPermissions(profile)).map((item) => {
      const heading = group === item.group ? '' : `<span class="nav-section">${escapeHtml(item.group)}</span>`;
      group = item.group;
      const disabled = item.planned ? ' aria-disabled="true" title="Disponível em próxima etapa"' : '';
      return `${heading}<a href="#${item.id}" data-route="${item.id}"${route() === item.id ? ' aria-current="page"' : ''}${disabled}><span aria-hidden="true">${item.planned ? '○' : '◆'}</span><span class="nav-label">${escapeHtml(item.label)}</span>${item.planned ? '<small>Em breve</small>' : ''}</a>`;
    }).join('');
  }

  function dashboardContext(profile) {
    const companyIds = companyId === dashboardService.allAuthorizedId
      ? profile.companies.map((company) => company.id)
      : profile.companies.filter((company) => company.id === companyId).map((company) => company.id);
    const companyNames = Object.freeze(Object.fromEntries(profile.companies.map((company) => [company.id, company.name])));
    return Object.freeze({companyIds: Object.freeze(companyIds), companyNames, permissions: Object.freeze(currentPermissions(profile))});
  }

  function initializeWorkContext(profile, allowPrompt = true) {
    const loaded = workContextService.load(profile.companies);
    workContext = loaded.context;
    workContextSettings = loaded.settings;
    companyId = workContext.companyId;
    workContextDialogOpen = allowPrompt && workContextSettings.askAtStart;
  }

  function workContextDialogMarkup(profile) {
    if (!workContext || !workContextSettings) return '';
    const companyOptions = profile.companies.map((company) => `<option value="${escapeHtml(company.id)}" ${company.id === workContext.companyId ? 'selected' : ''}>${escapeHtml(company.name)}</option>`).join('');
    return `<dialog id="work-context-dialog" aria-labelledby="work-context-title"><form id="work-context-form" class="stack"><div class="dialog-heading"><div><span class="eyebrow">Contexto de trabalho</span><h2 id="work-context-title">Empresa e período</h2></div><button class="btn ghost" type="button" data-action="close-work-context" aria-label="Fechar contexto">×</button></div><p>Este contexto preenche os períodos operacionais. O backend continua validando empresa, competência, bloqueios e permissões.</p><label>Empresa<select name="company_id" required>${companyOptions}</select></label><label>Competência<input name="reference_month" type="month" value="${escapeHtml(workContext.referenceMonth)}" required><small>O início e o fim do mês serão preenchidos automaticamente, mas poderão ser ajustados na operação.</small></label><label>Dias para revisão<input name="review_days" type="number" min="1" max="90" value="${escapeHtml(workContextSettings.reviewDays)}" required></label><label>Contar prazo a partir de<select name="review_basis"><option value="IMPORT_DATE" ${workContextSettings.reviewBasis === 'IMPORT_DATE' ? 'selected' : ''}>Data da importação</option><option value="PERIOD_END" ${workContextSettings.reviewBasis === 'PERIOD_END' ? 'selected' : ''}>Fim do período de referência</option></select><small>Para competências antigas, prefira a data da importação para evitar prazo já vencido.</small></label><label class="check"><input name="ask_at_start" type="checkbox" ${workContextSettings.askAtStart ? 'checked' : ''}> Solicitar empresa e período sempre que eu entrar</label><div class="actions"><button class="btn" type="submit">Aplicar contexto</button><button class="btn secondary" type="button" data-action="close-work-context">Continuar sem alterar</button></div><small>A preferência local guarda somente o identificador autorizado da empresa, a competência e a política de revisão. Nenhum XML, valor ou credencial é armazenado.</small></form></dialog>`;
  }

  function ensureDashboardLayout(profile) {
    const permissions = currentPermissions(profile);
    dashboardLayout = dashboardService.sanitizePreferences(
      dashboardLayout || dashboardService.loadPreferences(permissions), permissions,
    );
    return dashboardLayout;
  }

  function formatUpdatedAt(value) {
    if (!value) return '';
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return '';
    return `Atualizado às ${new Intl.DateTimeFormat('pt-BR', {hour: '2-digit', minute: '2-digit'}).format(date)}`;
  }

  function widgetItems(items, timeline = false) {
    if (!items?.length) return '';
    const tag = timeline ? 'ol' : 'ul';
    return `<${tag} class="dashboard-list ${timeline ? 'activity-list' : ''}">${items.map((item) => `<li><span><strong>${escapeHtml(item.title)}</strong><small>${escapeHtml(item.detail || '')}</small></span><time>${escapeHtml(item.meta || '')}</time></li>`).join('')}</${tag}>`;
  }

  function widgetControls(widgetId, layout) {
    if (!dashboardEditing) return '';
    const index = layout.widgets.indexOf(widgetId);
    return `<div class="widget-controls" aria-label="Organizar ${widgetId}">
      <button class="btn ghost small" data-action="dashboard-move" data-direction="up" data-widget-id="${widgetId}" ${index === 0 ? 'disabled' : ''}>Mover antes</button>
      <button class="btn ghost small" data-action="dashboard-move" data-direction="down" data-widget-id="${widgetId}" ${index === layout.widgets.length - 1 ? 'disabled' : ''}>Mover depois</button>
      <button class="btn ghost small" data-action="dashboard-resize" data-widget-id="${widgetId}">${layout.wide.includes(widgetId) ? 'Tamanho normal' : 'Ampliar'}</button>
      <button class="btn ghost small" data-action="dashboard-remove" data-widget-id="${widgetId}">Remover</button>
    </div>`;
  }

  function widgetMarkup(widget, state, layout) {
    if (state?.state === 'FORBIDDEN') return '';
    const wide = layout.wide.includes(widget.id) || widget.id === 'W010';
    const classes = `card dashboard-widget ${wide ? 'wide' : ''} ${state?.state === 'ERROR' ? 'widget-error' : ''}`;
    const heading = `<header class="widget-heading"><div><span class="widget-code">${widget.id}</span><h2 id="heading-${widget.id}">${escapeHtml(widget.label)}</h2></div>${config.dataMode === 'synthetic' ? '<span class="badge intelligent">Sintético</span>' : ''}</header>`;
    let body = '<div class="widget-loading" role="status"><span>Carregando indicador…</span><div class="skeleton metric" aria-hidden="true"></div></div>';
    if (state?.state === 'ERROR') body = `<div class="widget-state" role="alert"><strong>Indicador indisponível</strong><p>${escapeHtml(state.note)}</p><button class="btn secondary small" data-action="dashboard-refresh">Tentar novamente</button></div>`;
    else if (state?.state === 'UNAVAILABLE') body = `<div class="widget-state"><strong>Fonte ainda não integrada</strong><p>${escapeHtml(state.note)}</p></div>`;
    else if (state?.state === 'EMPTY') body = `<div class="widget-state"><strong>${escapeHtml(state.note)}</strong><p>Nenhuma ação é necessária neste contexto.</p></div>`;
    else if (state?.state === 'READY') {
      const value = state.value === '' ? '' : `<strong class="dashboard-value">${escapeHtml(state.value)}</strong>`;
      const destination = ['W001', 'W002'].includes(widget.id) ? '#documents'
        : ['W003', 'W005', 'W006'].includes(widget.id) ? '#accounting'
          : widget.id === 'W004' ? '#inbox'
            : widget.id === 'W007' ? '#clients' : '';
      const action = destination
        ? `<a class="btn ghost small" href="${destination}">${escapeHtml(widget.action)}</a>`
        : `<button class="btn ghost small" type="button" disabled title="Destino operacional ainda não integrado">${escapeHtml(widget.action)}</button>`;
      body = `${value}<p class="widget-note">${escapeHtml(state.note)}</p>${widgetItems(state.items, widget.kind === 'TIMELINE')}<footer class="widget-footer"><small>${escapeHtml(formatUpdatedAt(state.updatedAt))}</small>${action}</footer>`;
    }
    return `<article class="${classes}" data-dashboard-widget="${widget.id}" aria-labelledby="heading-${widget.id}">${heading}<div class="widget-body">${body}</div>${widgetControls(widget.id, layout)}</article>`;
  }

  function customizationMarkup(profile, layout) {
    const allowed = dashboardService.authorizedCatalog(currentPermissions(profile));
    return `<dialog id="dashboard-customizer" aria-labelledby="customizer-title"><div class="dialog-heading"><div><span class="eyebrow">Preferência local</span><h2 id="customizer-title">Personalizar Minha Visão</h2></div><button class="btn ghost" data-action="close-customizer" aria-label="Fechar personalização">×</button></div><p>Escolha e organize apenas widgets autorizados. A preferência não amplia seu acesso.</p><div class="customizer-list">${allowed.map((widget) => {
      const active = layout.widgets.includes(widget.id);
      return `<div class="customizer-item"><label class="check"><input type="checkbox" data-action="dashboard-toggle" data-widget-id="${widget.id}" ${active ? 'checked' : ''}> <span><strong>${widget.id} · ${escapeHtml(widget.label)}</strong><small>${escapeHtml(widget.kind)}</small></span></label></div>`;
    }).join('')}</div><div class="actions"><button class="btn" data-action="save-dashboard">Salvar visão</button><button class="btn secondary" data-action="reset-dashboard">Restaurar padrão</button></div><small>Armazenado neste navegador: IDs, ordem, tamanho e preset. Nenhum dado contábil, documento, token ou permissão é persistido.</small></dialog>`;
  }

  function overviewMarkup(profile) {
    const layout = ensureDashboardLayout(profile);
    const allowedById = new Map(dashboardService.authorizedCatalog(currentPermissions(profile)).map((widget) => [widget.id, widget]));
    const visible = layout.widgets.filter((id) => allowedById.has(id));
    const firstName = profile.user.displayName.split(/\s+/)[0];
    const contextLabel = companyId === dashboardService.allAuthorizedId
      ? 'Todas as empresas autorizadas'
      : profile.companies.find((company) => company.id === companyId)?.name || 'Sem empresa autorizada';
    const results = dashboardModel?.results || {};
    const widgets = visible.map((id) => widgetMarkup(allowedById.get(id), results[id], layout)).join('');
    return `<section class="dashboard-intro"><div><span class="eyebrow">${escapeHtml(profile.tenant.name)}</span><h1>Olá, ${escapeHtml(firstName)}. Esta é a sua visão.</h1><p>Prioridades do contexto <strong>${escapeHtml(contextLabel)}</strong>. Veja o que aconteceu e o que precisa de atenção agora.</p></div><div class="dashboard-actions"><button class="btn secondary" data-action="dashboard-refresh">Atualizar</button><button class="btn" data-action="open-customizer">Personalizar</button></div></section><div class="preset-bar dashboard-toolbar"><label>Visão<select id="dashboard-preset">${Object.keys(dashboardService.presets).map((preset) => `<option ${preset === layout.preset ? 'selected' : ''}>${escapeHtml(preset)}</option>`).join('')}</select></label><div><span class="badge intelligent">${config.dataMode === 'synthetic' ? 'BASE SINTÉTICA' : 'FONTE AUTORIZADA'}</span><small>${dashboardModel?.updatedAt ? ` ${escapeHtml(formatUpdatedAt(dashboardModel.updatedAt))}` : ' Atualização sob demanda'}</small></div></div>${dashboardEditing ? '<div class="alert info dashboard-editing" role="status"><div><strong>Modo de organização ativo</strong><p>Use os botões de cada widget ou abra Personalizar. Não é necessário arrastar.</p></div></div>' : ''}<section class="dashboard-grid" aria-label="Widgets da Minha Visão" aria-busy="${dashboardModel?.loading ? 'true' : 'false'}">${widgets || '<div class="card empty dashboard-empty"><h2>Sua visão está vazia</h2><p>Adicione um widget autorizado para acompanhar sua operação.</p><button class="btn" data-action="open-customizer">Adicionar widget</button></div>'}</section>${customizationMarkup(profile, layout)}`;
  }

  async function refreshDashboard(profile) {
    const requestId = ++dashboardRequest;
    const layout = ensureDashboardLayout(profile);
    const context = dashboardContext(profile);
    dashboardModel = {loading: true, results: {}, updatedAt: null};
    renderShell(false);
    const results = await dashboardService.loadSummary(layout.widgets, context);
    if (requestId !== dashboardRequest || session.snapshot().state !== STATES.AUTHENTICATED) return;
    dashboardModel = {loading: false, results, updatedAt: new Date().toISOString()};
    renderShell(false);
    setAnnouncement('Minha Visão atualizada.');
  }

  const formatDate = (value) => {
    const parsed = new Date(value);
    return Number.isNaN(parsed.getTime()) ? 'Data indisponível' : new Intl.DateTimeFormat('pt-BR', {dateStyle: 'short', timeStyle: 'short'}).format(parsed);
  };
  const statusClass = (status) => status === 'COMPLETED' ? 'success' : ['FAILED', 'QUARANTINED'].includes(status) ? 'danger' : status === 'DUPLICATE' ? 'warning' : 'info';
  const loadingOperational = (label) => `<section class="card operational-state" aria-busy="true"><div class="loading" role="status"><span class="spinner" aria-hidden="true"></span>Carregando ${escapeHtml(label)}…</div></section>`;
  const localizedError = () => '<section class="card empty" role="alert"><h2>Não foi possível carregar esta área</h2><p>Tente novamente. A navegação e os demais módulos continuam disponíveis.</p><button class="btn secondary" data-action="operational-refresh">Tentar novamente</button></section>';

  function companyListMarkup(profile) {
    if (operationalModel?.error) return localizedError();
    if (!operationalModel || operationalModel.loading || !operationalModel.items) return loadingOperational('empresas autorizadas');
    const search = operationalModel.search || '';
    const rows = operationalService.listCompanies({companies: operationalModel.items.map((item) => ({...item.profile, detail: item.detail, summary: item.summary}))}, search);
    return `<div class="page-heading"><div><span class="eyebrow">Relacionamento</span><h1>Empresas</h1><p>Somente empresas autorizadas pelo CompanyAccess vigente.</p></div></div>
      <section class="card"><form class="filter-bar" id="company-search-form"><label>Buscar empresa<input name="search" type="search" maxlength="100" value="${escapeHtml(search)}" placeholder="Nome da empresa"></label><button class="btn secondary" type="submit">Buscar</button></form>
      <div class="table-wrap"><table><thead><tr><th>Nome</th><th>Nome empresarial</th><th>Status</th><th>Pendências documentais</th><th>Ação</th></tr></thead><tbody>${rows.map((profileRow) => {
        const row = operationalModel.items.find((item) => item.profile.id === profileRow.id);
        return `<tr><td><strong>${escapeHtml(row.profile.name)}</strong></td><td>${escapeHtml(row.detail.legal_name)}</td><td><span class="badge ${row.detail.status === 'active' ? 'success' : 'neutral'}">${escapeHtml(row.detail.status === 'active' ? 'Ativa' : 'Inativa')}</span></td><td>${escapeHtml(row.summary.attention_required)}</td><td><button class="btn ghost small" data-action="open-company" data-company-id="${escapeHtml(row.profile.id)}">Abrir</button></td></tr>`;
      }).join('') || '<tr><td colspan="5">Nenhuma empresa autorizada encontrada.</td></tr>'}</tbody></table></div></section>`;
  }

  function companyDetailMarkup() {
    if (operationalModel?.error) return localizedError();
    if (!operationalModel || operationalModel.loading || !operationalModel.item?.detail) return loadingOperational('detalhe da empresa');
    const item = operationalModel.item;
    const canManage = hasPermission(currentPermissions(session.snapshot().profile), ['company.manage']);
    const accounts = (item.bankAccounts || []).map((account) => `<tr><td><strong>${escapeHtml(account.nickname || account.bank_name || account.bank_code)}</strong><small class="row-note">${escapeHtml(account.bank_code)} · ${escapeHtml(account.account_type || 'Tipo não informado')}</small></td><td>${escapeHtml(account.branch_masked)}</td><td>${escapeHtml(account.account_masked)}</td><td><span class="badge ${account.status === 'ACTIVE' ? 'success' : 'neutral'}">${escapeHtml(account.status === 'ACTIVE' ? 'Ativa' : 'Inativa')}</span></td><td>${canManage ? `<button class="btn ghost small" data-action="bank-edit" data-account-id="${escapeHtml(account.id)}">Editar</button><button class="btn ghost small" data-action="bank-status" data-account-id="${escapeHtml(account.id)}" data-status="${account.status === 'ACTIVE' ? 'INACTIVE' : 'ACTIVE'}">${account.status === 'ACTIVE' ? 'Desativar' : 'Ativar'}</button>` : 'Somente leitura'}</td></tr>`).join('');
    const form = canManage ? `<details class="card"><summary>Cadastrar conta bancária</summary><form id="bank-account-form" class="filter-bar"><label>Código do banco<input name="bank_code" maxlength="40" required></label><label>Nome do banco<input name="bank_name" maxlength="120"></label><label>Agência<input name="branch" maxlength="40" required></label><label>Conta<input name="account_number" maxlength="80" required></label><label>Tipo<input name="account_type" maxlength="40" placeholder="CHECKING"></label><label>Apelido<input name="nickname" maxlength="120"></label><label>Moeda<input name="currency_code" maxlength="3" value="BRL" required></label><button class="btn">Salvar conta</button></form></details>` : '';
    return `<div class="page-heading"><div><span class="eyebrow">Empresa autorizada</span><h1>${escapeHtml(item.profile.name)}</h1><p>Hub contextual de documentos, contas bancárias e pendências desta empresa.</p></div><a class="btn secondary" href="#clients">Voltar às empresas</a></div>
      <section class="operational-cards"><article class="card"><span class="eyebrow">Resumo</span><h2>${escapeHtml(item.detail.legal_name)}</h2><dl class="detail-list"><div><dt>Nome fantasia</dt><dd>${escapeHtml(item.detail.trade_name || 'Não informado')}</dd></div><div><dt>Identificador fiscal</dt><dd>${escapeHtml(item.detail.tax_identifier)}</dd></div><div><dt>Status</dt><dd>${escapeHtml(item.detail.status)}</dd></div><div><dt>Fuso / moeda</dt><dd>${escapeHtml(item.detail.timezone)} · ${escapeHtml(item.detail.currency_code)}</dd></div></dl></article>
      <article class="card"><span class="eyebrow">Documentos</span><strong class="dashboard-value">${escapeHtml(item.summary.received)}</strong><p>${escapeHtml(item.summary.processed)} processado(s); ${escapeHtml(item.summary.attention_required)} requer(em) atenção.</p><button class="btn secondary" data-action="company-documents" data-company-id="${escapeHtml(item.profile.id)}">Ver documentos</button></article></section><section class="card"><h2>Contas bancárias autorizadas para OFX</h2><p>O importador associa o extrato somente a uma conta ativa desta empresa.</p><div class="table-wrap"><table><thead><tr><th>Banco/Apelido</th><th>Agência</th><th>Conta</th><th>Status</th><th>Ação</th></tr></thead><tbody>${accounts || '<tr><td colspan="5">Nenhuma conta bancária cadastrada.</td></tr>'}</tbody></table></div></section>${form}`;
  }

  function documentFiltersMarkup() {
    return `<form class="filter-bar document-filters" id="document-filter-form"><label>Pesquisar<input type="search" name="search" maxlength="100" value="${escapeHtml(documentFilters.search)}" placeholder="Nome do arquivo"></label><label>Status<select name="status"><option value="">Todos</option>${['COMPLETED', 'STARTED', 'FAILED', 'QUARANTINED', 'DUPLICATE'].map((value) => `<option value="${value}" ${documentFilters.status === value ? 'selected' : ''}>${escapeHtml(operationalService.statusLabel(value))}</option>`).join('')}</select></label><label>Origem<select name="source"><option value="">Todas</option><option value="NFE55" ${documentFilters.source === 'NFE55' ? 'selected' : ''}>NF-e 55</option><option value="OFX_OPERATIONAL" ${documentFilters.source === 'OFX_OPERATIONAL' ? 'selected' : ''}>OFX</option></select></label><label>De<input type="date" name="received_from" value="${escapeHtml(documentFilters.received_from)}"></label><label>Até<input type="date" name="received_to" value="${escapeHtml(documentFilters.received_to)}"></label><button class="btn secondary" type="submit">Aplicar filtros</button><button class="btn ghost" type="button" data-action="clear-document-filters">Limpar</button></form>`;
  }

  function documentsMarkup(profile, inbox = false) {
    const title = inbox ? 'Caixa de entrada' : 'Central de Documentos';
    if (companyId === dashboardService.allAuthorizedId) return `<div class="page-heading"><div><span class="eyebrow">Operação</span><h1>${title}</h1></div></div><section class="card empty"><h2>Selecione uma empresa</h2><p>A consulta documental é paginada e autorizada por empresa. Escolha uma empresa no topo para evitar mistura de contextos.</p></section>`;
    if (operationalModel?.error) return localizedError();
    if (!operationalModel || operationalModel.loading || !operationalModel.page) return `<div class="page-heading"><div><span class="eyebrow">Operação</span><h1>${title}</h1></div></div>${loadingOperational('documentos')}`;
    let items = operationalModel.page.items;
    if (inbox) items = items.slice(0, 10);
    const company = profile.companies.find((item) => item.id === companyId);
    const rows = items.map((item) => `<tr><td><button class="link-button" data-action="open-document" data-document-id="${escapeHtml(item.id)}">${escapeHtml(item.document_number || item.filename)}</button><small class="row-note">${escapeHtml(item.description || item.filename)}${item.observation ? ' · possui observação' : ''}</small></td><td>${escapeHtml(item.source === 'NFE55' ? 'NF-e 55' : item.source)}</td><td>${escapeHtml(company?.name || 'Empresa autorizada')}</td><td>${escapeHtml(formatDate(item.received_at))}</td><td><span class="badge ${statusClass(item.processing_status)}">${escapeHtml(operationalService.statusLabel(item.processing_status))}</span>${item.receipt_result === 'DUPLICATE' ? '<small class="row-note">Documento já recebido anteriormente.</small>' : ''}</td></tr>`).join('');
    const previous = Math.max(0, operationalModel.page.offset - operationalModel.page.limit);
    const next = operationalModel.page.offset + operationalModel.page.limit;
    return `<div class="page-heading"><div><span class="eyebrow">Operação</span><h1>${title}</h1><p>${inbox ? 'Recebimentos recentes que pedem atenção inicial.' : 'Metadados seguros dos documentos recebidos.'}</p></div></div>${inbox ? '' : documentFiltersMarkup()}
      <div class="alert info"><div><strong>Upload documental genérico ainda não disponível</strong><p>Os contratos atuais são imports especializados de NF-e e OFX. A interface não inventa parâmetros contábeis nem amplia tipos aceitos.</p></div></div>
      <section class="card"><div class="table-wrap"><table><thead><tr><th>Documento</th><th>Tipo/origem</th><th>Empresa</th><th>Recebido em</th><th>Status</th></tr></thead><tbody>${rows || `<tr><td colspan="5">${inbox ? 'Nenhum item requer atenção inicial.' : 'Nenhum documento encontrado para os filtros.'}</td></tr>`}</tbody></table></div>${inbox ? '' : `<footer class="pagination"><span>${escapeHtml(operationalModel.page.total)} documento(s)</span><div><button class="btn ghost small" data-action="document-page" data-offset="${previous}" ${operationalModel.page.offset === 0 ? 'disabled' : ''}>Anterior</button><button class="btn ghost small" data-action="document-page" data-offset="${next}" ${next >= operationalModel.page.total ? 'disabled' : ''}>Próxima</button></div></footer>`}</section>`;
  }

  function hydrateRemediationUi() {
    if (route() === 'inbox' && !document.querySelector('#document-filter-form')) {
      document.querySelector('.page-heading')?.insertAdjacentHTML('afterend', documentFiltersMarkup());
    }
    const actions = {
      'fiscal-filter-form': 'clear-fiscal-filters',
      'transaction-filter-form': 'clear-transaction-filters',
      'proposal-filter-form': 'clear-proposal-filters',
    };
    const proposalForm = document.querySelector('#proposal-filter-form');
    if (proposalForm && !proposalForm.querySelector('[name="created_from"]')) {
      proposalForm.querySelector('button')?.insertAdjacentHTML('beforebegin',
        `<label>Registrada de<input name="created_from" type="date" value="${escapeHtml(proposalFilters.created_from)}"></label><label>Registrada até<input name="created_to" type="date" value="${escapeHtml(proposalFilters.created_to)}"></label>`);
    }
    Object.entries(actions).forEach(([formId, action]) => {
      const form = document.querySelector(`#${formId}`);
      if (!form || form.querySelector(`[data-action="${action}"]`)) return;
      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'btn ghost';
      button.dataset.action = action;
      button.textContent = 'Limpar filtros';
      form.append(button);
    });
  }

  function documentDetailMarkup(profile) {
    if (operationalModel?.error) return localizedError();
    if (!operationalModel || operationalModel.loading || !operationalModel.item?.document) return loadingOperational('detalhe do documento');
    const item = operationalModel.item.document;
    const company = profile.companies.find((entry) => entry.id === item.company_id);
    const related = operationalModel.item.fiscal_document_id
      ? `<a class="btn ghost" href="#fiscal?company=${encodeURIComponent(companyId)}&fiscal=${encodeURIComponent(operationalModel.item.fiscal_document_id)}">Abrir dados fiscais da NF-e</a>`
      : operationalModel.item.bank_statement_id
        ? `<a class="btn ghost" href="#financial?company=${encodeURIComponent(companyId)}&statement=${encodeURIComponent(operationalModel.item.bank_statement_id)}">Abrir extrato e transações</a>` : '';
    const metadata = hasPermission(currentPermissions(profile), ['company.manage']) ? `<article class="card"><h2>Metadados operacionais</h2><form id="document-metadata-form" class="stack"><label>Número<input name="document_number" maxlength="100" value="${escapeHtml(item.document_number || '')}"></label><label>Descrição<input name="description" maxlength="500" value="${escapeHtml(item.description || '')}"></label><label>Observação<textarea name="observation" maxlength="1000">${escapeHtml(item.observation || '')}</textarea></label><button class="btn">Salvar metadados</button></form><small>Versão ${escapeHtml(item.metadata_version || 0)}. A evidência original permanece imutável.</small></article>` : `<article class="card"><h2>Metadados operacionais</h2><dl class="detail-list"><div><dt>Número</dt><dd>${escapeHtml(item.document_number || 'Não informado')}</dd></div><div><dt>Descrição</dt><dd>${escapeHtml(item.description || 'Não informada')}</dd></div><div><dt>Observação</dt><dd>${escapeHtml(item.observation || 'Não informada')}</dd></div></dl></article>`;
    return `<div class="page-heading"><div><span class="eyebrow">Documento autorizado</span><h1>${escapeHtml(item.filename)}</h1><p>Metadados minimizados; conteúdo original e caminhos de storage não são expostos.</p></div><a class="btn secondary" href="#documents">Voltar aos documentos</a></div><section class="operational-cards"><article class="card"><h2>Detalhes</h2><dl class="detail-list"><div><dt>Empresa</dt><dd>${escapeHtml(company?.name || 'Empresa autorizada')}</dd></div><div><dt>Origem</dt><dd>${escapeHtml(item.source)}</dd></div><div><dt>Canal</dt><dd>${escapeHtml(item.channel)}</dd></div><div><dt>Recebido em</dt><dd>${escapeHtml(formatDate(item.received_at))}</dd></div><div><dt>Tamanho</dt><dd>${escapeHtml(item.size_bytes)} bytes</dd></div><div><dt>Status</dt><dd><span class="badge ${statusClass(item.processing_status)}">${escapeHtml(operationalService.statusLabel(item.processing_status))}</span></dd></div></dl>${related}</article>${metadata}<article class="card"><h2>Validação</h2>${operationalModel.item.issues.length ? `<ul class="dashboard-list">${operationalModel.item.issues.map((issue) => `<li><span><strong>${escapeHtml(issue.code)}</strong><small>${escapeHtml(issue.severity)} · ${escapeHtml(issue.resolution_status)}</small></span><time>${escapeHtml(formatDate(issue.created_at))}</time></li>`).join('')}</ul>` : '<p>Nenhuma exceção segura associada a este documento.</p>'}<p class="row-note">Download e histórico contextual permanecem adiados até existir contrato específico autorizado.</p></article></section>`;
  }

  async function refreshOperational(profile) {
    const requestId = ++operationalRequest;
    const view = route();
    operationalModel = {loading: true};
    renderShell(false);
    let nextModel;
    try {
      if (view === 'clients') {
        const detailId = routeParams().get('company');
        if (detailId) {
          const authorized = profile.companies.find((item) => item.id === detailId);
          if (!authorized) throw Object.assign(new Error('FORBIDDEN'), {code: 'FORBIDDEN'});
          companyId = detailId;
          const [detail, summary, bankAccounts] = await Promise.all([operationalService.company(detailId), operationalService.summary(detailId), operationalService.bankAccounts(detailId)]);
          nextModel = {loading: false, item: {profile: authorized, detail, summary, bankAccounts}};
        } else {
          const items = await Promise.all(profile.companies.map(async (profileItem) => ({profile: profileItem, detail: await operationalService.company(profileItem.id), summary: await operationalService.summary(profileItem.id)})));
          nextModel = {loading: false, items, search: ''};
        }
      } else {
        const requestedCompany = routeParams().get('company');
        if (requestedCompany) {
          if (!profile.companies.some((item) => item.id === requestedCompany)) throw Object.assign(new Error('FORBIDDEN'), {code: 'FORBIDDEN'});
          companyId = requestedCompany;
        }
        if (companyId === dashboardService.allAuthorizedId) { nextModel = {loading: false, page: {items: [], total: 0, offset: 0, limit: 10}}; }
        else {
          const documentId = routeParams().get('document');
          if (documentId) {
            const item = await operationalService.document(companyId, documentId);
            const decisionLine = hasPermission(currentPermissions(profile), ['audit.read'])
              ? await operationalService.decisionLine(companyId, 'DOCUMENT', documentId) : null;
            nextModel = {loading: false, item, decisionLine};
          }
          else if (view === 'inbox') {
            nextModel = {loading: false, page: await operationalService.documents(
              companyId, {...documentFilters, offset: 0, limit: 25},
            )};
          } else nextModel = {loading: false, page: await operationalService.documents(companyId, documentFilters)};
        }
      }
    } catch (error) {
      nextModel = {loading: false, error: error?.code || 'ERROR'};
    }
    if (requestId !== operationalRequest || session.snapshot().state !== STATES.AUTHENTICATED) return;
    operationalModel = nextModel;
    renderShell(false);
  }

  const money = (value, currency = 'BRL') => value === null || value === undefined ? 'Não informado' : new Intl.NumberFormat('pt-BR', {style: 'currency', currency: currency || 'BRL'}).format(Number(value));
  const importFeedbackMarkup = (scope = route()) => {
    if (!importFeedback || importFeedback.scope !== scope) return '';
    const loading = importFeedback.state === 'LOADING';
    const danger = importFeedback.state === 'ERROR' || importFeedback.status === 'QUARANTINED';
    const duplicate = Number(importFeedback.duplicate_items || 0) > 0 || importFeedback.status === 'IDEMPOTENT_REDELIVERY';
    const title = loading ? 'Importando arquivo…' : danger ? 'Importação requer atenção' : duplicate ? 'Documento já recebido anteriormente' : 'Importação recebida';
    const items = (importFeedback.items || []).map((item) => {
      const presentation = {
        PROCESSING: ['neutral', 'Processando'], SUCCESS: ['success', 'Recebido'],
        DUPLICATE: ['warning', 'Duplicado'], INVALID: ['danger', 'Inválido'],
        WRONG_COMPANY: ['danger', 'Empresa divergente'], PERIOD_MISMATCH: ['danger', 'Fora do período'],
        FAILED: ['danger', 'Falhou'],
      }[item.status] || ['neutral', 'Resultado disponível'];
      return `<li><span><strong>${escapeHtml(item.filename)}</strong><small>${escapeHtml(item.message || '')}</small></span><span class="badge ${presentation[0]}">${presentation[1]}</span></li>`;
    }).join('');
    const detail = items ? `<ul class="import-results" aria-label="Resultado por arquivo">${items}</ul>` : '';
    return `<div class="alert ${loading ? 'info' : danger ? 'error' : duplicate ? 'warning' : 'success'}" role="status" aria-live="polite"><div><strong>${title}</strong><p>${escapeHtml(importFeedback.message || (importFeedback.synthetic ? 'Simulação local: nenhum arquivo foi enviado ou persistido.' : 'Acompanhe o processamento no módulo e na Central de Documentos.'))}</p>${detail}</div></div>`;
  };
  const selectedCompanyRequired = (title) => `<div class="page-heading"><div><span class="eyebrow">Inteligência operacional</span><h1>${title}</h1></div></div><section class="card empty"><h2>Selecione uma empresa</h2><p>Importações e consultas fiscais/financeiras são sempre autorizadas por empresa.</p></section>`;

  async function inspectNfeXml(file) {
    try {
      const xml = await file.text();
      if (/<!DOCTYPE|<!ENTITY/i.test(xml)) return Object.freeze({error: 'XML contém declaração não permitida.'});
      const documentXml = new root.DOMParser().parseFromString(xml, 'application/xml');
      if (documentXml.getElementsByTagName('parsererror').length) return Object.freeze({error: 'XML malformado.'});
      const issued = documentXml.getElementsByTagNameNS('*', 'dhEmi')[0]
        || documentXml.getElementsByTagNameNS('*', 'dEmi')[0];
      const issuedDate = issued?.textContent?.trim().slice(0, 10) || '';
      if (!/^\d{4}-\d{2}-\d{2}$/.test(issuedDate)) return Object.freeze({error: 'Data de emissão não encontrada no XML.'});
      return Object.freeze({issuedDate});
    } catch (_) {
      return Object.freeze({error: 'Não foi possível conferir a data de emissão do XML.'});
    }
  }

  function nfeSelectionMarkup() {
    if (!pendingNfeFiles.length) return '<p class="row-note">Nenhum XML selecionado.</p>';
    return `<p><strong>${pendingNfeFiles.length} arquivo(s) pronto(s) para importar</strong></p><ul class="selected-files">${pendingNfeFiles.map((file, index) => `<li><span><strong>${escapeHtml(file.name)}</strong><small>${escapeHtml(`${Math.max(1, Math.ceil(file.size / 1024))} KB`)}</small></span><button class="btn ghost small" type="button" data-action="remove-nfe-file" data-file-index="${index}">Remover</button></li>`).join('')}</ul>`;
  }

  function updateNfeSelection() {
    const container = document.querySelector('#nfe-selection');
    if (container) container.innerHTML = nfeSelectionMarkup();
  }

  function nfeImportMarkup(profile) {
    if (!hasPermission(currentPermissions(profile), ['journal.propose'])) return '<div class="alert info"><div><strong>Consulta disponível</strong><p>Seu contexto não possui permissão para importar documentos.</p></div></div>';
    const expiryDate = workContextService.reviewExpiry(workContext.periodEnd, workContextSettings.reviewDays, workContextSettings.reviewBasis);
    const reviewBasisLabel = workContextSettings.reviewBasis === 'PERIOD_END' ? 'o fim do período' : 'a data da importação';
    return `<details class="card import-panel" open><summary>Importar NF-e XML</summary><div class="work-context-summary"><span><strong>${escapeHtml(profile.companies.find((company) => company.id === companyId)?.name || 'Empresa selecionada')}</strong><small>Período padrão: ${escapeHtml(workContext.periodStart)} a ${escapeHtml(workContext.periodEnd)}</small></span><button class="btn ghost small" type="button" data-action="open-work-context">Alterar contexto</button></div><form id="nfe-import-form" class="filter-bar import-form"><label>Adicionar arquivos XML<input id="nfe-file-input" name="file" type="file" accept=".xml,application/xml,text/xml" multiple><small>Você poderá conferir e remover arquivos antes de importar.</small></label><label>Adicionar pasta de XML (opcional)<input id="nfe-folder-input" name="folder" type="file" accept=".xml,application/xml,text/xml" multiple webkitdirectory directory><small>Seleção progressiva de pasta, quando suportada pelo navegador.</small></label><div id="nfe-selection" class="file-selection" aria-live="polite">${nfeSelectionMarkup()}</div><label>Data contábil (opcional)<input name="accounting_date" type="date"><small>Em branco, usa a emissão do XML. Preencha somente para um ajuste contábil consciente dentro do período.</small></label><label>Início do período<input name="period_start" type="date" value="${escapeHtml(workContext.periodStart)}" required></label><label>Fim do período<input name="period_end" type="date" value="${escapeHtml(workContext.periodEnd)}" required></label><label>Revisão válida até<input name="approval_expiry_date" type="date" value="${escapeHtml(expiryDate)}" aria-describedby="approval-expiry-help" required><small id="approval-expiry-help">Preenchida automaticamente: ${escapeHtml(workContextSettings.reviewDays)} dia(s) após ${escapeHtml(reviewBasisLabel)}. Você pode ajustar.</small></label><button class="btn" type="submit">Importar XML</button></form><small>Somente NF-e modelo 55. Sem data contábil manual, XML fora do período é recusado antes da importação. O backend repete as validações.</small></details>`;
  }

  function fiscalMarkup(profile) {
    if (companyId === dashboardService.allAuthorizedId) return selectedCompanyRequired('Fiscal · NF-e');
    if (routeParams().has('fiscal')) return fiscalDetailMarkup(profile) + decisionLineMarkup(intelligenceModel?.decisionLine);
    if (intelligenceModel?.error) return localizedError();
    if (!intelligenceModel?.page) return loadingOperational('documentos fiscais');
    const rows = intelligenceModel.page.items.map((item) => `<tr><td><button class="link-button" data-action="open-fiscal" data-fiscal-id="${escapeHtml(item.id)}">NF-e ${escapeHtml(item.document_number || 'sem número')}</button><small class="row-note">Série ${escapeHtml(item.series || '—')} · ${escapeHtml(item.direction || 'direção não determinada')}</small></td><td>${escapeHtml(item.issuer_name || 'Não informado')}</td><td>${escapeHtml(formatDate(item.issued_at))}</td><td>${escapeHtml(money(item.invoice_total))}</td><td><span class="badge ${item.observed_status === 'REPORTED_AUTHORIZED' ? 'success' : 'warning'}">${escapeHtml(intelligenceService.fiscalStatusLabel(item.observed_status))}</span></td></tr>`).join('');
    const previous = Math.max(0, intelligenceModel.page.offset - intelligenceModel.page.limit);
    const next = intelligenceModel.page.offset + intelligenceModel.page.limit;
    return `<div class="page-heading"><div><span class="eyebrow">Inteligência Fiscal</span><h1>NF-e · Documentos fiscais</h1><p>Importação e leitura estruturada do modelo 55; sem cálculo fiscal completo.</p></div></div>${importFeedbackMarkup()}${nfeImportMarkup(profile)}<form id="fiscal-filter-form" class="filter-bar document-filters"><label>Chave, número ou emitente<input name="search" type="search" maxlength="100" value="${escapeHtml(fiscalFilters.search)}"></label><label>Status<select name="status"><option value="">Todos</option><option value="REPORTED_AUTHORIZED" ${fiscalFilters.status === 'REPORTED_AUTHORIZED' ? 'selected' : ''}>Autorizada informada</option><option value="UNVERIFIED" ${fiscalFilters.status === 'UNVERIFIED' ? 'selected' : ''}>Não verificada</option></select></label><label>Emissão de<input name="issued_from" type="date" value="${escapeHtml(fiscalFilters.issued_from)}"></label><label>Emissão até<input name="issued_to" type="date" value="${escapeHtml(fiscalFilters.issued_to)}"></label><button class="btn secondary">Aplicar filtros</button></form><section class="card"><div class="table-wrap"><table><thead><tr><th>Documento</th><th>Emitente</th><th>Emissão</th><th>Valor</th><th>Status observado</th></tr></thead><tbody>${rows || '<tr><td colspan="5">Nenhuma NF-e encontrada.</td></tr>'}</tbody></table></div><footer class="pagination"><span>${escapeHtml(intelligenceModel.page.total)} NF-e</span><div><button class="btn ghost small" data-action="fiscal-page" data-offset="${previous}" ${intelligenceModel.page.offset === 0 ? 'disabled' : ''}>Anterior</button><button class="btn ghost small" data-action="fiscal-page" data-offset="${next}" ${next >= intelligenceModel.page.total ? 'disabled' : ''}>Próxima</button></div></footer></section>`;
  }

  function fiscalDetailMarkup(profile) {
    if (intelligenceModel?.error) return localizedError();
    if (!intelligenceModel?.item?.document) return loadingOperational('detalhe fiscal');
    const detail = intelligenceModel.item, item = detail.document;
    const itemRows = detail.items.map((row) => `<tr><td>${escapeHtml(row.sequence)}</td><td>${escapeHtml(row.description || 'Não informado')}</td><td>${escapeHtml(row.ncm || '—')}</td><td>${escapeHtml(row.cfop || '—')}</td><td>${escapeHtml(row.quantity ?? '—')} ${escapeHtml(row.commercial_unit || '')}</td><td>${escapeHtml(money(row.gross_total))}</td></tr>`).join('');
    return `<div class="page-heading"><div><span class="eyebrow">NF-e modelo ${escapeHtml(item.model)}</span><h1>NF-e ${escapeHtml(item.document_number || 'sem número')}</h1><p>Dados estruturados pelo parser seguro; status do protocolo é apenas o observado no XML.</p></div><a class="btn secondary" href="#fiscal">Voltar</a></div><section class="operational-cards"><article class="card"><h2>Resumo fiscal</h2><dl class="detail-list"><div><dt>Chave</dt><dd class="monospace">${escapeHtml(item.access_key)}</dd></div><div><dt>Série</dt><dd>${escapeHtml(item.series || '—')}</dd></div><div><dt>Emissão</dt><dd>${escapeHtml(formatDate(item.issued_at))}</dd></div><div><dt>Emitente</dt><dd>${escapeHtml(item.issuer_name || 'Não informado')}</dd></div><div><dt>Destinatário</dt><dd>${escapeHtml(item.recipient_name || 'Não informado')}</dd></div><div><dt>Natureza</dt><dd>${escapeHtml(item.operation_nature || 'Não informada')}</dd></div><div><dt>Total NF-e</dt><dd>${escapeHtml(money(item.invoice_total))}</dd></div></dl>${item.document_receipt_id ? `<a class="btn ghost" href="#documents?company=${encodeURIComponent(companyId)}&document=${encodeURIComponent(item.document_receipt_id)}">Ver na Central de Documentos</a>` : ''}</article><article class="card"><h2>Tributos normalizados</h2>${detail.tax_totals.length ? `<ul class="dashboard-list">${detail.tax_totals.map((tax) => `<li><strong>${escapeHtml(tax.tax_type)}</strong><span>${escapeHtml(money(tax.amount))}</span></li>`).join('')}</ul>` : '<p>Nenhum total tributário suportado foi encontrado.</p>'}<p class="row-note">Não representa cálculo fiscal completo.</p></article></section><section class="card"><h2>Itens (${escapeHtml(detail.item_count)})</h2><div class="table-wrap"><table><thead><tr><th>#</th><th>Descrição</th><th>NCM</th><th>CFOP</th><th>Quantidade</th><th>Total</th></tr></thead><tbody>${itemRows || '<tr><td colspan="6">Nenhum item disponível.</td></tr>'}</tbody></table></div>${detail.item_count > detail.items.length ? '<p>Exibição limitada aos primeiros 200 itens.</p>' : ''}</section>`;
  }

  function ofxImportMarkup(profile) {
    if (!hasPermission(currentPermissions(profile), ['journal.propose'])) return '<div class="alert info"><div><strong>Consulta disponível</strong><p>Seu contexto não possui permissão para importar extratos.</p></div></div>';
    return `<details class="card import-panel"><summary>Importar extrato OFX</summary><form id="ofx-import-form" class="filter-bar import-form"><label>Arquivo OFX<input name="file" type="file" accept=".ofx,application/x-ofx,application/ofx,text/plain" required></label><button class="btn" type="submit">Importar OFX</button></form><small>O sinal de TRNAMT é preservado. Importar não concilia, classifica nem aprova transações.</small></details>`;
  }

  function financialMarkup(profile) {
    if (companyId === dashboardService.allAuthorizedId) return selectedCompanyRequired('Financeiro · OFX');
    if (routeParams().has('statement')) return statementDetailMarkup() + decisionLineMarkup(intelligenceModel?.decisionLine);
    if (intelligenceModel?.error) return localizedError();
    if (!intelligenceModel?.page) return loadingOperational('extratos financeiros');
    const rows = intelligenceModel.page.items.map((item) => `<tr><td><button class="link-button" data-action="open-statement" data-statement-id="${escapeHtml(item.id)}">${escapeHtml(item.bank_id || 'Instituição não informada')}</button></td><td>${escapeHtml(item.branch_masked || '—')} · ${escapeHtml(item.account_masked)}</td><td>${escapeHtml(item.start_date || '—')} a ${escapeHtml(item.end_date || '—')}</td><td>${escapeHtml(money(item.closing_balance, item.currency_code || 'BRL'))}</td><td>${escapeHtml(formatDate(item.imported_at))}</td></tr>`).join('');
    const previous = Math.max(0, intelligenceModel.page.offset - intelligenceModel.page.limit);
    const next = intelligenceModel.page.offset + intelligenceModel.page.limit;
    return `<div class="page-heading"><div><span class="eyebrow">Inteligência Financeira</span><h1>Extratos · OFX</h1><p>Extratos e transações importados, com identificadores bancários minimizados.</p></div></div>${importFeedbackMarkup()}${ofxImportMarkup(profile)}<div class="alert info"><div><strong>Conciliação ainda não operacional</strong><p>O domínio puro existe, mas não há persistência/caso de uso seguro. Matching, sugestões e match manual permanecem adiados.</p></div></div><section class="card"><div class="table-wrap"><table><thead><tr><th>Instituição</th><th>Conta mascarada</th><th>Período</th><th>Saldo final</th><th>Importado em</th></tr></thead><tbody>${rows || '<tr><td colspan="5">Nenhum extrato OFX encontrado.</td></tr>'}</tbody></table></div><footer class="pagination"><span>${escapeHtml(intelligenceModel.page.total)} extrato(s)</span><div><button class="btn ghost small" data-action="statement-page" data-offset="${previous}" ${intelligenceModel.page.offset === 0 ? 'disabled' : ''}>Anterior</button><button class="btn ghost small" data-action="statement-page" data-offset="${next}" ${next >= intelligenceModel.page.total ? 'disabled' : ''}>Próxima</button></div></footer></section>`;
  }

  function statementDetailMarkup() {
    if (intelligenceModel?.error) return localizedError();
    if (!intelligenceModel?.item?.statement) return loadingOperational('extrato e transações');
    const detail = intelligenceModel.item, item = detail.statement;
    const rows = detail.transactions.items.map((row) => `<tr><td>${escapeHtml(row.transaction_date || '—')}<small class="row-note">Postada: ${escapeHtml(row.posted_date || '—')}</small></td><td>${escapeHtml(row.description || 'Sem descrição')}<small class="row-note">Documento: ${escapeHtml(row.document_number || 'não informado')}</small></td><td><span class="badge ${row.direction === 'CREDIT' ? 'success' : 'neutral'}">${row.direction === 'CREDIT' ? 'Crédito +' : 'Débito −'}</span></td><td class="amount ${row.direction === 'CREDIT' ? 'credit' : 'debit'}">${escapeHtml(money(row.amount, item.currency_code || 'BRL'))}</td><td>${escapeHtml(row.identity_kind)}<small class="row-note">Referência preservada e minimizada</small></td></tr>`).join('');
    const previous = Math.max(0, detail.transactions.offset - detail.transactions.limit);
    const next = detail.transactions.offset + detail.transactions.limit;
    return `<div class="page-heading"><div><span class="eyebrow">Extrato OFX</span><h1>${escapeHtml(item.bank_id || 'Instituição não informada')} · ${escapeHtml(item.account_masked)}</h1><p>${escapeHtml(item.start_date || '—')} a ${escapeHtml(item.end_date || '—')}</p></div><a class="btn secondary" href="#financial">Voltar</a></div><section class="operational-cards"><article class="card"><h2>Resumo</h2><dl class="detail-list"><div><dt>Agência</dt><dd>${escapeHtml(item.branch_masked || '—')}</dd></div><div><dt>Conta</dt><dd>${escapeHtml(item.account_masked)}</dd></div><div><dt>Saldo inicial</dt><dd>${escapeHtml(money(item.opening_balance, item.currency_code || 'BRL'))}</dd></div><div><dt>Saldo final</dt><dd>${escapeHtml(money(item.closing_balance, item.currency_code || 'BRL'))}</dd></div></dl>${item.document_receipt_id ? `<a class="btn ghost" href="#documents?company=${encodeURIComponent(companyId)}&document=${encodeURIComponent(item.document_receipt_id)}">Ver arquivo na Central</a>` : ''}</article><article class="card"><h2>Semântica</h2><p>Crédito mantém valor positivo; débito mantém valor negativo conforme <code>${escapeHtml(item.sign_policy)}</code>.</p><p>Nenhuma classificação ou conciliação foi inferida.</p></article></section><form id="transaction-filter-form" class="filter-bar document-filters"><label>Descrição<input name="search" type="search" maxlength="100" value="${escapeHtml(transactionFilters.search)}"></label><label>Movimento<select name="direction"><option value="">Todos</option><option value="CREDIT" ${transactionFilters.direction === 'CREDIT' ? 'selected' : ''}>Crédito</option><option value="DEBIT" ${transactionFilters.direction === 'DEBIT' ? 'selected' : ''}>Débito</option></select></label><label>De<input name="posted_from" type="date" value="${escapeHtml(transactionFilters.posted_from)}"></label><label>Até<input name="posted_to" type="date" value="${escapeHtml(transactionFilters.posted_to)}"></label><button class="btn secondary">Aplicar</button></form><section class="card"><h2>Transações (${escapeHtml(detail.transactions.total)})</h2><div class="table-wrap"><table><thead><tr><th>Data</th><th>Descrição</th><th>Tipo</th><th>Valor</th><th>Identidade</th></tr></thead><tbody>${rows || '<tr><td colspan="5">Nenhuma transação encontrada.</td></tr>'}</tbody></table></div><footer class="pagination"><span>${escapeHtml(detail.transactions.total)} transação(ões)</span><div><button class="btn ghost small" data-action="transaction-page" data-offset="${previous}" ${detail.transactions.offset === 0 ? 'disabled' : ''}>Anterior</button><button class="btn ghost small" data-action="transaction-page" data-offset="${next}" ${next >= detail.transactions.total ? 'disabled' : ''}>Próxima</button></div></footer></section>`;
  }

  async function refreshIntelligence(profile) {
    const requestId = ++intelligenceRequest;
    intelligenceModel = {loading: true}; renderShell(false);
    let nextModel;
    try {
      const requestedCompany = routeParams().get('company');
      if (requestedCompany) {
        if (!profile.companies.some((item) => item.id === requestedCompany)) throw Object.assign(new Error('FORBIDDEN'), {code: 'FORBIDDEN'});
        companyId = requestedCompany;
      }
      if (companyId === dashboardService.allAuthorizedId) nextModel = {loading: false, page: {items: [], total: 0, offset: 0, limit: 10}};
      else if (route() === 'fiscal') {
        const id = routeParams().get('fiscal');
        if (id) {
          const item = await intelligenceService.fiscalDocument(companyId, id);
          const decisionLine = hasPermission(currentPermissions(profile), ['audit.read']) ? await intelligenceService.decisionLine(companyId, 'FISCAL_DOCUMENT', id) : null;
          nextModel = {loading: false, item, decisionLine};
        } else nextModel = {loading: false, page: await intelligenceService.fiscalDocuments(companyId, fiscalFilters)};
      } else {
        const id = routeParams().get('statement');
        if (id) {
          const item = await intelligenceService.bankStatement(companyId, id, transactionFilters);
          const decisionLine = hasPermission(currentPermissions(profile), ['audit.read']) ? await intelligenceService.decisionLine(companyId, 'BANK_STATEMENT', id) : null;
          nextModel = {loading: false, item, decisionLine};
        } else nextModel = {loading: false, page: await intelligenceService.bankStatements(companyId, statementFilters)};
      }
    } catch (error) { nextModel = {loading: false, error: error?.code || 'ERROR'}; }
    if (requestId !== intelligenceRequest || session.snapshot().state !== STATES.AUTHENTICATED) return;
    intelligenceModel = nextModel; renderShell(false);
  }

  const accountingStatusClass = (status) => status === 'APPROVED' ? 'success'
    : status === 'REJECTED' ? 'danger'
      : status === 'BLOCKED_FOR_HOMOLOGATION' ? 'warning' : 'info';
  const ruleOperator = Object.freeze({EQ: 'igual a', NE: 'diferente de', IN: 'contido em', CONTAINS: 'contém'});

  function accountingTabs(profile, active = 'proposals') {
    const rules = hasPermission(currentPermissions(profile), ['catalog.review'])
      ? `<a class="btn ${active === 'rules' ? '' : 'ghost'} small" href="#accounting?view=rules">Regras, contas e mapeamentos</a>` : '';
    return `<nav class="accounting-tabs" aria-label="Áreas contábeis"><a class="btn ${active === 'proposals' ? '' : 'ghost'} small" href="#accounting">Propostas e revisão</a><a class="btn ${active === 'items' ? '' : 'ghost'} small" href="#accounting?view=items">Itens pendentes</a>${rules}</nav>`;
  }

  function proposalListMarkup(profile) {
    if (accountingModel?.error) return localizedError();
    if (!accountingModel?.page) return loadingOperational('propostas contábeis');
    const page = accountingModel.page;
    const rows = page.items.map((item) => `<tr><td>${escapeHtml(item.accounting_date)}</td><td><button class="link-button" data-action="open-proposal" data-proposal-id="${escapeHtml(item.journey_id)}">${escapeHtml(item.document_number || (item.source_type === 'FiscalDocument' ? 'NF-e 55' : item.source_type))}</button><small class="row-note">${escapeHtml(item.source_type)}</small></td><td><span class="intelligence-label">SUGESTÃO</span><small class="row-note">${escapeHtml(item.rule_name || item.rule_version_id)}</small></td><td>${escapeHtml((item.debit_accounts || []).join('; ') || 'Conta não informada')}<small class="row-note">${escapeHtml(money(item.total_debit))}</small></td><td>${escapeHtml((item.credit_accounts || []).join('; ') || 'Conta não informada')}<small class="row-note">${escapeHtml(money(item.total_credit))}</small></td><td><span class="badge ${accountingStatusClass(item.status)}">${escapeHtml(accountingService.statusLabel(item.status))}</span></td><td><button class="btn ghost small" data-action="open-proposal" data-proposal-id="${escapeHtml(item.journey_id)}">Revisar</button></td></tr>`).join('');
    const previous = Math.max(0, page.offset - page.limit), next = page.offset + page.limit;
    return `<div class="page-heading"><div><span class="eyebrow">Inteligência Contábil</span><h1>Propostas e revisão profissional</h1><p>A automação prepara uma sugestão determinística. Somente o profissional autorizado decide.</p></div></div>${accountingTabs(profile)}<div class="alert info"><div><strong>AUTOMATION ≠ PROFESSIONAL DECISION</strong><p>Nenhuma proposta desta tela representa escrituração, postagem ou exportação oficial.</p></div></div><form id="proposal-filter-form" class="filter-bar document-filters"><label>Conta<input name="account" value="${escapeHtml(proposalFilters.account)}" placeholder="Código ou nome"></label><label>Origem<input name="source" value="${escapeHtml(proposalFilters.source)}" placeholder="FiscalDocument"></label><label>Documento<input name="document" value="${escapeHtml(proposalFilters.document)}"></label><label>Regra<input name="rule" value="${escapeHtml(proposalFilters.rule)}"></label><label>Data contábil de<input name="created_from" type="date" value="${escapeHtml(proposalFilters.created_from)}"></label><label>Data contábil até<input name="created_to" type="date" value="${escapeHtml(proposalFilters.created_to)}"></label><label>Status<select name="status"><option value="">Todos</option>${Object.entries(root.S21Accounting.STATUS).map(([value, label]) => `<option value="${value}" ${proposalFilters.status === value ? 'selected' : ''}>${escapeHtml(label)}</option>`).join('')}</select></label><button class="btn secondary">Aplicar filtros</button><button class="btn ghost" type="button" data-action="clear-proposal-filters">Limpar</button></form><section class="card"><div class="table-wrap"><table><thead><tr><th>Data contábil</th><th>Origem/documento</th><th>Regra</th><th>Débito</th><th>Crédito</th><th>Status</th><th>Ação</th></tr></thead><tbody>${rows || '<tr><td colspan="7">Nenhuma proposta contábil encontrada.</td></tr>'}</tbody></table></div><footer class="pagination"><span>${escapeHtml(page.total)} proposta(s)</span><div><button class="btn ghost small" data-action="proposal-page" data-offset="${previous}" ${page.offset === 0 ? 'disabled' : ''}>Anterior</button><button class="btn ghost small" data-action="proposal-page" data-offset="${next}" ${next >= page.total ? 'disabled' : ''}>Próxima</button></div></footer></section>`;
  }

  function sourceEvidenceMarkup(source) {
    const sourceLink = source.source_type === 'FiscalDocument'
      ? `<a class="btn ghost small" href="#fiscal?company=${encodeURIComponent(companyId)}&fiscal=${encodeURIComponent(source.source_id)}">Abrir NF-e</a>` : '';
    const receiptLink = source.document_receipt_id
      ? `<a class="btn ghost small" href="#documents?company=${encodeURIComponent(companyId)}&document=${encodeURIComponent(source.document_receipt_id)}">Central de Documentos</a>` : '';
    return `<article class="evidence-item"><dl class="detail-list"><div><dt>Origem</dt><dd>${escapeHtml(source.source_type === 'FiscalDocument' ? 'NF-e modelo 55' : source.source_type)}</dd></div><div><dt>Documento</dt><dd>${escapeHtml(source.document_number || 'Não informado')}</dd></div><div><dt>Emitente</dt><dd>${escapeHtml(source.issuer_name || 'Não informado')}</dd></div><div><dt>Emissão</dt><dd>${source.issued_at ? escapeHtml(formatDate(source.issued_at)) : 'Não informada'}</dd></div><div><dt>Valor de origem</dt><dd>${escapeHtml(money(source.amount))}</dd></div></dl><div class="actions">${sourceLink}${receiptLink}</div></article>`;
  }

  function decisionDialogMarkup(summary) {
    if (!decisionIntent) return '';
    const approve = decisionIntent === 'APPROVED';
    const feedback = decisionFeedback ? `<div class="alert ${decisionFeedback.state === 'ERROR' ? 'error' : 'info'}" role="status"><div><strong>${decisionFeedback.state === 'LOADING' ? 'Registrando decisão…' : 'Decisão não registrada'}</strong><p>${escapeHtml(decisionFeedback.message)}</p></div></div>` : '';
    return `<dialog id="accounting-decision-dialog" aria-labelledby="decision-title"><form id="accounting-decision-form"><input type="hidden" name="decision" value="${decisionIntent}"><div class="dialog-heading"><div><span class="eyebrow">Decisão profissional</span><h2 id="decision-title">${approve ? 'Aprovar internamente' : 'Rejeitar proposta'}</h2></div><button class="btn ghost" type="button" data-action="close-decision" aria-label="Fechar">×</button></div>${feedback}<p>${approve ? 'Confirme que revisou a origem, a regra, as contas e o balanceamento. Isto não posta nem exporta o lançamento.' : 'A rejeição encerra esta revisão. O domínio atual não possui campo seguro para persistir um motivo textual.'}</p><label class="check"><input type="checkbox" name="confirmed" required> <span>Confirmo esta decisão humana sobre a revisão <code>${escapeHtml(summary.revision_id)}</code>.</span></label><div class="actions"><button class="btn" type="submit" ${decisionFeedback?.state === 'LOADING' ? 'disabled' : ''}>Confirmar ${approve ? 'aprovação' : 'rejeição'}</button><button class="btn secondary" type="button" data-action="close-decision">Cancelar</button></div></form></dialog>`;
  }

  function proposalDetailMarkup(profile) {
    if (accountingModel?.error) return localizedError();
    if (!accountingModel?.item?.summary) return loadingOperational('revisão contábil');
    const detail = accountingModel.item, summary = detail.summary, rule = detail.rule;
    const conditions = rule.conditions.map((condition) => `<li><strong>${escapeHtml(condition.field)}</strong> ${escapeHtml(ruleOperator[condition.operator] || condition.operator)} <code>${escapeHtml(condition.value)}</code></li>`).join('');
    const lines = detail.lines.map((line) => `<tr><td>${escapeHtml(line.account_code)}</td><td>${escapeHtml(line.account_name)}</td><td>${escapeHtml(money(line.debit))}</td><td>${escapeHtml(money(line.credit))}</td></tr>`).join('');
    const locks = detail.active_locks.length ? `<div class="alert warning" role="alert"><div><strong>Período/operação bloqueada</strong>${detail.active_locks.map((lock) => `<p>${escapeHtml(lock.scope)} · ${escapeHtml(lock.target)} · ${escapeHtml(lock.reason)} · criado em ${escapeHtml(formatDate(lock.created_at))}. Operações: ${escapeHtml(lock.operations.join(', '))}.</p>`).join('')}<p>A autoridade final de bloqueio é revalidada pelo backend no instante da decisão.</p></div></div>` : '';
    const decision = summary.decision_actor_id ? `<div class="alert ${summary.status === 'APPROVED' ? 'success' : 'warning'}"><div><strong>${summary.status === 'APPROVED' ? 'Aprovado' : 'Rejeitado'} por profissional</strong><p>Ator ${escapeHtml(summary.decision_actor_id)} · ${escapeHtml(formatDate(summary.decided_at))}</p></div></div>` : '';
    const canDecide = summary.status === 'PENDING_APPROVAL' && hasPermission(currentPermissions(profile), ['journal.approve']);
    const actions = canDecide ? `<div class="professional-actions"><button class="btn" data-action="open-decision" data-decision="APPROVED">Aprovar internamente</button><button class="btn secondary" data-action="open-decision" data-decision="REJECTED">Rejeitar</button></div>` : summary.status === 'PENDING_APPROVAL' ? '<p class="row-note">Seu contexto permite consultar, mas não decidir esta proposta.</p>' : '';
    const activity = accountingModel.activity ? `<section class="card"><h2>Histórico contextual</h2><ol class="dashboard-list activity-list">${accountingModel.activity.map((event) => `<li><span><strong>${escapeHtml(event.action)}</strong><small>${escapeHtml(event.origin)} · versão ${escapeHtml(event.subject_version)}</small></span><time>${escapeHtml(formatDate(event.occurred_at))}</time></li>`).join('') || '<li>Nenhum evento contextual encontrado.</li>'}</ol><p class="row-note">Prévia minimizada. A Linha da Decisão completa permanece para a Fase 09.</p></section>` : '';
    return `<div class="page-heading"><div><span class="eyebrow">PROPOSTA CONTÁBIL · SUGESTÃO DETERMINÍSTICA</span><h1>Revisão profissional</h1><p>A proposta é assistiva e não substitui decisão humana nem sistema contábil externo.</p></div><a class="btn secondary" href="#accounting">Voltar à fila</a></div>${accountingTabs(profile)}<section class="proposal-priority"><article class="card"><span class="eyebrow">1 · Status</span><h2><span class="badge ${accountingStatusClass(summary.status)}">${escapeHtml(accountingService.statusLabel(summary.status))}</span></h2><dl class="detail-list"><div><dt>Data contábil</dt><dd>${escapeHtml(summary.accounting_date)}</dd></div><div><dt>Responsável</dt><dd>${escapeHtml(summary.responsible_role)}</dd></div><div><dt>Validação</dt><dd>${escapeHtml(summary.validation_status || 'Não informada')}</dd></div></dl>${actions}</article><article class="card intelligence-card"><span class="eyebrow">2 · Regra / por quê</span><h2>${escapeHtml(rule.name || rule.id)}</h2><p>Escopo ${escapeHtml(rule.scope)}, prioridade ${escapeHtml(rule.priority)} e automação ${escapeHtml(rule.automation_level)}.</p><ul>${conditions}</ul><p><strong>Resultado:</strong> débito ${escapeHtml(rule.debit_account_code)} · ${escapeHtml(rule.debit_account_name)} / crédito ${escapeHtml(rule.credit_account_code)} · ${escapeHtml(rule.credit_account_name)}.</p></article></section>${locks}${decision}<section class="card"><span class="eyebrow">3 · Débitos e créditos</span><h2>Partida contábil proposta</h2><div class="table-wrap"><table><thead><tr><th>Conta</th><th>Nome</th><th>Débito</th><th>Crédito</th></tr></thead><tbody>${lines}</tbody><tfoot><tr><th colspan="2">Totais autorizados pelo backend</th><th>${escapeHtml(money(summary.total_debit))}</th><th>${escapeHtml(money(summary.total_credit))}</th></tr></tfoot></table></div><p><span class="badge ${summary.balanced ? 'success' : 'danger'}">${summary.balanced ? 'BALANCEADO' : 'NÃO BALANCEADO'}</span> O frontend apenas apresenta a validação; não recalcula a autoridade contábil.</p></section><section class="card"><span class="eyebrow">4 · Origem e evidências</span><h2>Rastreabilidade</h2>${detail.sources.map(sourceEvidenceMarkup).join('')}</section><section class="card"><h2>Revisão</h2><dl class="detail-list"><div><dt>Proponente</dt><dd>${escapeHtml(summary.proposer_id)}</dd></div><div><dt>Revisão imutável</dt><dd><code>${escapeHtml(summary.revision_id)}</code></dd></div><div><dt>Hash</dt><dd class="monospace">${escapeHtml(summary.revision_hash)}</dd></div><div><dt>Expira em</dt><dd>${summary.expires_at ? escapeHtml(formatDate(summary.expires_at)) : 'Sem expiração informada'}</dd></div></dl><p class="row-note">Edição de proposta está adiada: não existe caso de uso seguro de escrita. Uma nova revisão invalidaria a aprovação anterior.</p></section>${activity}${decisionDialogMarkup(summary)}`;
  }

  function catalogMarkup(profile) {
    if (accountingModel?.error) return localizedError();
    if (accountingModel?.needsEffectiveDate) return `<div class="page-heading"><div><span class="eyebrow">Automação contábil</span><h1>Regras, contas e mapeamentos</h1><p>Informe a data contábil de referência; ela não é inferida do relógio do servidor.</p></div></div>${accountingTabs(profile, 'rules')}<form id="catalog-effective-form" class="filter-bar document-filters"><label>Data efetiva<input name="effective_at" type="date" required></label><button class="btn">Consultar catálogo publicado</button></form>`;
    if (!accountingModel?.catalog) return loadingOperational('catálogo contábil publicado');
    const catalog = accountingModel.catalog;
    const rules = catalog.rules.map((rule) => `<tr><td><button class="link-button" data-action="open-rule" data-rule-id="${escapeHtml(rule.id)}">${escapeHtml(rule.name || rule.id)}</button></td><td>${escapeHtml(rule.scope)}</td><td>${escapeHtml(rule.priority)}</td><td><span class="badge intelligent">${escapeHtml(rule.status)}</span></td><td>${escapeHtml(rule.debit_account_code)} → ${escapeHtml(rule.credit_account_code)}</td></tr>`).join('');
    const term = catalogSearch.trim().toLocaleLowerCase('pt-BR');
    const accounts = catalog.accounts.filter((account) => !term || [account.code, account.name, account.nature, account.status].some((value) => String(value).toLocaleLowerCase('pt-BR').includes(term))).map((account) => `<tr><td>${escapeHtml(account.code)}</td><td>${escapeHtml(account.name)}</td><td>${escapeHtml(account.nature)}</td><td>${account.is_postable ? 'Analítica / lançável' : 'Não lançável'}</td><td><span class="badge intelligent">${escapeHtml(account.status)}</span></td></tr>`).join('');
    const mappings = catalog.mappings.map((mapping) => `<tr><td>${escapeHtml(mapping.key)}</td><td>${escapeHtml(mapping.external_code || mapping.history_contains || mapping.dimension_code || 'Condição canônica')}</td><td>${escapeHtml(mapping.target_account_code)} · ${escapeHtml(mapping.target_account_name)}</td><td>${escapeHtml(mapping.priority)}</td></tr>`).join('');
    return `<div class="page-heading"><div><span class="eyebrow">Automação contábil</span><h1>Regras, contas e mapeamentos</h1><p>Catálogo publicado e efetivo, em modo somente leitura.</p></div></div>${accountingTabs(profile, 'rules')}<div class="alert info"><div><strong>Versão ${escapeHtml(catalog.version_no)} · válida desde ${escapeHtml(catalog.valid_from)}</strong><p>Precisão: ${escapeHtml(catalog.decimal_places)} casas; campo monetário: ${escapeHtml(catalog.amount_field)}. A integridade da versão publicada é validada no backend.</p></div></div><section class="card"><h2>Regras determinísticas</h2><div class="table-wrap"><table><thead><tr><th>Regra</th><th>Escopo</th><th>Prioridade</th><th>Status</th><th>Resultado</th></tr></thead><tbody>${rules || '<tr><td colspan="5">Nenhuma regra publicada.</td></tr>'}</tbody></table></div></section><section class="card"><h2>Plano de contas</h2><form id="catalog-account-search" class="filter-bar"><label>Buscar por código, nome, natureza ou status<input name="search" type="search" value="${escapeHtml(catalogSearch)}"></label><button class="btn secondary">Buscar</button></form><div class="table-wrap"><table><thead><tr><th>Código</th><th>Nome</th><th>Natureza</th><th>Uso</th><th>Status</th></tr></thead><tbody>${accounts || '<tr><td colspan="5">Nenhuma conta publicada para a busca.</td></tr>'}</tbody></table></div></section><section class="card"><h2>Mapeamentos</h2><div class="table-wrap"><table><thead><tr><th>Chave</th><th>Condição</th><th>Conta alvo</th><th>Prioridade</th></tr></thead><tbody>${mappings || '<tr><td colspan="4">Nenhum mapeamento publicado.</td></tr>'}</tbody></table></div><p class="row-note">Escrita de regras e mapeamentos está adiada: o contrato atual governa a versão completa e não oferece editor granular seguro.</p></section>`;
  }

  function ruleDetailMarkup(profile) {
    if (accountingModel?.error) return localizedError();
    if (!accountingModel?.rule) return loadingOperational('detalhe da regra');
    const rule = accountingModel.rule;
    return `<div class="page-heading"><div><span class="eyebrow">Regra determinística publicada</span><h1>${escapeHtml(rule.name || rule.id)}</h1><p>Explicação segura da versão exata; sem expressão executável.</p></div><a class="btn secondary" href="#accounting?view=rules&effective_at=${encodeURIComponent(routeParams().get('effective_at'))}">Voltar ao catálogo</a></div>${accountingTabs(profile, 'rules')}<section class="card intelligence-card"><dl class="detail-list"><div><dt>Identificador da versão</dt><dd><code>${escapeHtml(rule.id)}</code></dd></div><div><dt>Escopo</dt><dd>${escapeHtml(rule.scope)}</dd></div><div><dt>Prioridade</dt><dd>${escapeHtml(rule.priority)}</dd></div><div><dt>Status</dt><dd>${escapeHtml(rule.status)}</dd></div><div><dt>Automação</dt><dd>${escapeHtml(rule.automation_level)}</dd></div></dl><h2>Quando se aplica</h2><ul>${rule.conditions.map((condition) => `<li><strong>${escapeHtml(condition.field)}</strong> ${escapeHtml(ruleOperator[condition.operator] || condition.operator)} <code>${escapeHtml(condition.value)}</code></li>`).join('')}</ul><h2>Resultado sugerido</h2><p>Débito em <strong>${escapeHtml(rule.debit_account_code)} · ${escapeHtml(rule.debit_account_name)}</strong> e crédito em <strong>${escapeHtml(rule.credit_account_code)} · ${escapeHtml(rule.credit_account_name)}</strong>.</p></section>`;
  }

  function itemClassificationQueueMarkup(profile) {
    if (accountingModel?.error) return localizedError();
    if (!accountingModel?.page) return loadingOperational('itens pendentes de classificação');
    const page = accountingModel.page;
    const rows = page.items.map((item) => `<tr><td>${escapeHtml(item.item_description)}</td><td><span class="badge ${accountingStatusClass(item.status)}">${escapeHtml(accountingService.itemClassificationStatusLabel(item.status))}</span></td><td>${escapeHtml(item.confidence_level)}</td><td>${escapeHtml(formatDate(item.created_at))}</td><td><button class="btn ghost small" data-action="open-item-classification" data-classification-id="${escapeHtml(item.id)}">Revisar</button></td></tr>`).join('');
    const previous = Math.max(0, page.offset - page.limit), next = page.offset + page.limit;
    return `<div class="page-heading"><div><span class="eyebrow">Inteligência Contábil</span><h1>Itens pendentes de classificação</h1><p>Cada item fiscal exige confirmação profissional antes de compor uma proposta contábil.</p></div></div>${accountingTabs(profile, 'items')}<div class="alert info"><div><strong>AUTOMATION ≠ PROFESSIONAL DECISION</strong><p>Nenhum item desta fila representa lançamento, escrituração ou proposta aprovada.</p></div></div><section class="card"><div class="table-wrap"><table><thead><tr><th>Item</th><th>Situação</th><th>Confiança</th><th>Detectado em</th><th>Ação</th></tr></thead><tbody>${rows || '<tr><td colspan="5">Nenhum item pendente de classificação.</td></tr>'}</tbody></table></div><footer class="pagination"><span>${escapeHtml(page.total)} item(ns)</span><div><button class="btn ghost small" data-action="item-queue-page" data-offset="${previous}" ${page.offset === 0 ? 'disabled' : ''}>Anterior</button><button class="btn ghost small" data-action="item-queue-page" data-offset="${next}" ${next >= page.total ? 'disabled' : ''}>Próxima</button></div></footer></section>`;
  }

  function itemClassificationDecisionDialogMarkup(detail) {
    if (!itemDecisionOpen) return '';
    const feedback = itemDecisionFeedback ? `<div class="alert ${itemDecisionFeedback.state === 'ERROR' ? 'error' : 'info'}" role="status"><div><strong>${itemDecisionFeedback.state === 'LOADING' ? 'Registrando decisão…' : 'Decisão não registrada'}</strong><p>${escapeHtml(itemDecisionFeedback.message)}</p></div></div>` : '';
    const intents = Object.entries(root.S21Accounting.ACCOUNTING_INTENTS).map(([value, label]) => `<option value="${value}" ${detail.summary.selected_intent === value ? 'selected' : ''}>${escapeHtml(label)}</option>`).join('');
    const scopes = Object.entries(root.S21Accounting.APPLY_SCOPE).map(([value, label]) => `<option value="${value}">${escapeHtml(label)}</option>`).join('');
    return `<dialog id="item-classification-decision-dialog" aria-labelledby="item-decision-title"><form id="item-classification-decision-form"><div class="dialog-heading"><div><span class="eyebrow">Decisão profissional</span><h2 id="item-decision-title">Confirmar classificação do item</h2></div><button class="btn ghost" type="button" data-action="close-item-decision" aria-label="Fechar">×</button></div>${feedback}<label>Intenção contábil final<select name="final_intent" required>${intents}</select></label><label>Alcance da decisão<select name="apply_scope" required>${scopes}</select></label><label class="check"><input type="checkbox" name="confirmed" required> <span>Confirmo esta decisão humana sobre o item <code>${escapeHtml(detail.summary.id)}</code>.</span></label><div class="actions"><button class="btn" type="submit" ${itemDecisionFeedback?.state === 'LOADING' ? 'disabled' : ''}>Confirmar classificação</button><button class="btn secondary" type="button" data-action="close-item-decision">Cancelar</button></div></form></dialog>`;
  }

  function itemClassificationDetailMarkup(profile) {
    if (accountingModel?.error) return localizedError();
    if (!accountingModel?.detail) return loadingOperational('detalhe do item');
    const detail = accountingModel.detail, summary = detail.summary;
    const evidence = detail.evidence.map((item) => `<li><strong>${escapeHtml(item.kind)}</strong> → ${escapeHtml(item.intent)} (peso ${escapeHtml(item.weight)})<p>${escapeHtml(item.explanation)}</p></li>`).join('') || '<li>Nenhuma evidência registrada.</li>';
    const alternatives = detail.alternatives.length ? `<p class="row-note">Alternativas em conflito: ${detail.alternatives.map((intent) => escapeHtml(root.S21Accounting.ACCOUNTING_INTENTS[intent] || intent)).join(', ')}.</p>` : '';
    const canDecide = ['REVIEW_REQUIRED', 'CONFLICTING_EVIDENCE'].includes(summary.status)
      && hasPermission(currentPermissions(profile), ['accounting.classification.review']);
    const actions = canDecide
      ? `<div class="professional-actions"><button class="btn" data-action="open-item-decision">Classificar item</button></div>`
      : summary.status === 'REVIEWED'
        ? '<p class="row-note">Classificação já confirmada por decisão profissional.</p>'
        : '<p class="row-note">Seu contexto permite consultar, mas não decidir este item.</p>';
    return `<div class="page-heading"><div><span class="eyebrow">ITEM FISCAL · CLASSIFICAÇÃO DETERMINÍSTICA</span><h1>Revisão do item</h1><p>A classificação é assistiva e não substitui decisão humana.</p></div><a class="btn secondary" href="#accounting?view=items">Voltar à fila</a></div>${accountingTabs(profile, 'items')}<section class="proposal-priority"><article class="card"><span class="eyebrow">1 · Status</span><h2><span class="badge ${accountingStatusClass(summary.status)}">${escapeHtml(accountingService.itemClassificationStatusLabel(summary.status))}</span></h2><dl class="detail-list"><div><dt>Item</dt><dd>${escapeHtml(summary.item_description)}</dd></div><div><dt>Intenção sugerida</dt><dd>${escapeHtml(root.S21Accounting.ACCOUNTING_INTENTS[summary.selected_intent] || summary.selected_intent)}</dd></div><div><dt>Confiança</dt><dd>${escapeHtml(summary.confidence_level)}</dd></div><div><dt>Documento</dt><dd>${escapeHtml(detail.document_number || 'Não informado')} · ${escapeHtml(detail.issuer_name || 'Emitente não informado')}</dd></div></dl>${actions}</article></section><section class="card"><h2>Evidências</h2><ul class="dashboard-list">${evidence}</ul>${alternatives}</section>${itemClassificationDecisionDialogMarkup(detail)}`;
  }

  function accountingMarkup(profile) {
    if (companyId === dashboardService.allAuthorizedId) return selectedCompanyRequired('Contábil');
    if (routeParams().has('rule')) return ruleDetailMarkup(profile);
    if (routeParams().get('view') === 'rules') return catalogMarkup(profile);
    if (routeParams().has('proposal')) return proposalDetailMarkup(profile) + decisionLineMarkup(accountingModel?.decisionLine);
    if (routeParams().has('item')) return itemClassificationDetailMarkup(profile);
    if (routeParams().get('view') === 'items') return itemClassificationQueueMarkup(profile);
    return proposalListMarkup(profile);
  }

  async function refreshAccounting(profile) {
    const requestId = ++accountingRequest;
    accountingModel = {loading: true}; renderShell(false);
    let nextModel;
    try {
      const requestedCompany = routeParams().get('company');
      if (requestedCompany) {
        if (!profile.companies.some((item) => item.id === requestedCompany)) throw Object.assign(new Error('FORBIDDEN'), {code: 'FORBIDDEN'});
        companyId = requestedCompany;
      }
      if (companyId === dashboardService.allAuthorizedId) nextModel = {loading: false, page: {items: [], total: 0, offset: 0, limit: 10}};
      else if (routeParams().has('rule')) {
        const effectiveAt = routeParams().get('effective_at');
        nextModel = effectiveAt ? {loading: false, rule: await accountingService.accountingRule(companyId, routeParams().get('rule'), effectiveAt)} : {loading: false, needsEffectiveDate: true};
      }
      else if (routeParams().get('view') === 'rules') {
        const effectiveAt = routeParams().get('effective_at');
        nextModel = effectiveAt ? {loading: false, catalog: await accountingService.accountingCatalog(companyId, effectiveAt)} : {loading: false, needsEffectiveDate: true};
      }
      else if (routeParams().has('proposal')) {
        const proposalId = routeParams().get('proposal');
        const [item, activity] = await Promise.all([
          accountingService.accountingProposal(companyId, proposalId),
          accountingService.proposalActivity(companyId, proposalId),
        ]);
        let decisionLine = null;
        if (hasPermission(currentPermissions(profile), ['audit.read'])) decisionLine = await accountingService.decisionLine(companyId, 'ACCOUNTING_PROPOSAL', proposalId);
        nextModel = {loading: false, item, activity, decisionLine};
      }
      else if (routeParams().has('item')) {
        nextModel = {loading: false, detail: await accountingService.itemClassification(companyId, routeParams().get('item'))};
      }
      else if (routeParams().get('view') === 'items') {
        nextModel = {loading: false, page: await accountingService.itemClassifications(companyId, itemQueueFilters)};
      } else nextModel = {loading: false, page: await accountingService.accountingProposals(companyId, proposalFilters)};
    } catch (error) { nextModel = {loading: false, error: error?.code || 'ERROR'}; }
    if (requestId !== accountingRequest || session.snapshot().state !== STATES.AUTHENTICATED) return;
    accountingModel = nextModel; renderShell(false);
    if (decisionIntent) document.querySelector('#accounting-decision-dialog')?.showModal();
  }

  function placeholderMarkup(item, profile) {
    if (!item || !hasPermission(currentPermissions(profile), item.permissions)) return null;
    return `<div class="page-heading"><div><span class="eyebrow">Aplicativo Serdial21</span><h1>${escapeHtml(item.label)}</h1><p>Esta área será integrada em uma etapa futura.</p></div></div><section class="card empty"><h2>Disponível em próxima etapa</h2><p>Nenhuma funcionalidade operacional fictícia foi criada.</p><a class="btn secondary" href="#overview">Voltar</a></section>`;
  }

  function renderShell(loadDashboard = true) {
    const {profile, mode} = session.snapshot();
    if (!profile || session.snapshot().state !== STATES.AUTHENTICATED) { renderLogin(); return; }
    if (!workContext || !workContextSettings) initializeWorkContext(profile, false);
    companyId = companyId || profile.companies[0]?.id || null;
    const target = navigation.find((item) => item.id === route());
    const currentRoute = route();
    let content = null;
    if (currentRoute === 'overview' && hasPermission(currentPermissions(profile), ['company.read'])) content = overviewMarkup(profile);
    else if (currentRoute === 'clients' && hasPermission(currentPermissions(profile), ['company.read'])) content = routeParams().has('company') ? companyDetailMarkup() : companyListMarkup(profile);
    else if (currentRoute === 'documents' && hasPermission(currentPermissions(profile), ['company.read'])) content = routeParams().has('document') ? documentDetailMarkup(profile) + decisionLineMarkup(operationalModel?.decisionLine) : documentsMarkup(profile, false);
    else if (currentRoute === 'inbox' && hasPermission(currentPermissions(profile), ['company.read'])) content = documentsMarkup(profile, true);
    else if (currentRoute === 'fiscal' && hasPermission(currentPermissions(profile), ['company.read'])) content = fiscalMarkup(profile);
    else if (currentRoute === 'financial' && hasPermission(currentPermissions(profile), ['company.read'])) content = financialMarkup(profile);
    else if (currentRoute === 'accounting' && hasPermission(currentPermissions(profile), ['journal.read'])) content = accountingMarkup(profile);
    else content = placeholderMarkup(target, profile);
    if (!content) { session.forbid(); renderState(STATES.FORBIDDEN); return; }
    const currentCompany = profile.companies.find((company) => company.id === companyId);
    const contextName = companyId === dashboardService.allAuthorizedId
      ? 'Todas as empresas autorizadas'
      : currentCompany?.name || 'Sem empresa autorizada';
    const allOption = profile.companies.length > 1
      ? `<option value="${dashboardService.allAuthorizedId}" ${companyId === dashboardService.allAuthorizedId ? 'selected' : ''}>Todas as empresas autorizadas</option>`
      : '';
    app.innerHTML = `<div class="app-shell auth-shell"><aside class="sidebar ${drawerOpen ? 'open' : ''}" aria-label="Navegação lateral"><a class="brand-link" href="#overview"><img class="brand-image shell-logo" src="../ui/assets/brand/S21%20assinatura%20principal.png" alt="Serdial21 Contabilidade Inteligente"></a><div class="office">${escapeHtml(profile.tenant.name)}<small>${mode === 'synthetic' ? 'Contexto fictício' : 'Contexto autorizado'}</small></div><nav class="nav" aria-label="Navegação principal">${navMarkup(profile)}</nav><div class="sidebar-foot"><span>${escapeHtml(profile.user.displayName)}</span><small>${escapeHtml(profile.user.roleLabel || '')}</small><button class="btn ghost drawer-close" data-action="close-drawer">Fechar menu</button></div></aside><button class="drawer-backdrop ${drawerOpen ? 'open' : ''}" data-action="close-drawer" aria-label="Fechar navegação"></button><div class="workspace"><header class="topbar"><div class="context"><button class="btn ghost mobile-menu" data-action="open-drawer" aria-label="Abrir navegação">☰</button><div class="context-copy"><strong>${escapeHtml(contextName)}</strong><small>${escapeHtml(profile.tenant.name)}</small></div><label>Empresa<select id="company-context" ${profile.companies.length < 2 ? 'disabled' : ''}>${allOption}${profile.companies.map((company) => `<option value="${escapeHtml(company.id)}" ${company.id === companyId ? 'selected' : ''}>${escapeHtml(company.name)}</option>`).join('')}</select></label><button class="btn ghost context-period" type="button" data-action="open-work-context"><span>Competência</span><strong>${escapeHtml(workContext.referenceMonth)}</strong></button></div><div class="topbar-actions"><span class="environment-banner">${escapeHtml(config.environmentLabel)}</span><div class="profile-menu"><button class="btn ghost profile-trigger" data-action="toggle-user-menu" aria-expanded="${userMenuOpen}" aria-controls="user-popover"><span class="avatar">${escapeHtml(initials(profile.user.displayName))}</span><span class="profile-label">${escapeHtml(profile.user.displayName)}</span></button><div class="profile-popover" id="user-popover" ${userMenuOpen ? '' : 'hidden'}><strong>${escapeHtml(profile.user.displayName)}</strong><p>${escapeHtml(profile.tenant.name)}</p><button class="btn ghost" data-action="open-work-context">Contexto e preferências</button><button class="btn secondary" data-action="logout">Sair do aplicativo</button></div></div></div></header><div class="mode-banner">${mode === 'synthetic' ? 'DEMONSTRAÇÃO LOCAL · identidade, empresas e conteúdo sintéticos · sem acesso à API' : `SESSÃO OIDC · ${config.dataMode === 'synthetic' ? 'conteúdo de negócio sintético' : 'contexto autorizado'}`}</div><main id="main" tabindex="-1">${content}<p class="footer-note">Serdial21 Contabilidade Inteligente · A automação prepara. O profissional decide.</p></main>${workContextDialogMarkup(profile)}</div></div>`;
    app.setAttribute('aria-busy', 'false');
    hydrateRemediationUi();
    if (workContextDialogOpen) document.querySelector('#work-context-dialog')?.showModal();
    if (loadDashboard && route() === 'overview') refreshDashboard(profile);
    if (loadDashboard && ['clients', 'documents', 'inbox'].includes(route())) refreshOperational(profile);
    if (loadDashboard && ['fiscal', 'financial'].includes(route())) refreshIntelligence(profile);
    if (loadDashboard && route() === 'accounting') refreshAccounting(profile);
  }

  async function bootstrapAuthenticated(accessToken, returnTo = '#overview') {
    const bootstrapClient = root.S21ApiClient.createApiClient({
      baseUrl: config.apiBaseUrl,
      getAccessToken: () => accessToken,
      onAuthenticationFailure: () => session.expire(),
    });
    try {
      const current = await bootstrapClient.currentApplication();
      const profile = normalizeCurrentApplication(current);
      session.establish({token: accessToken, userProfile: profile});
      initializeWorkContext(profile, true);
      const requested = String(returnTo || '').match(/^#[a-z-]+$/)?.[0]?.slice(1);
      location.hash = authorizedRoute(profile, requested);
      renderShell();
    } catch (error) {
      if (error.code === 'SESSION_EXPIRED') { session.expire(); renderLogin(); }
      else if (error.code === 'FORBIDDEN') { session.unauthenticated(); session.forbid(); renderState(STATES.FORBIDDEN); }
      else if (error.code === 'NETWORK_UNAVAILABLE') { session.failNetwork(); renderState(STATES.NETWORK_ERROR); }
      else { session.failServer(); renderState(STATES.SERVER_ERROR); }
    }
  }

  function navigateSafe() {
    if (session.snapshot().state !== STATES.AUTHENTICATED) { renderLogin(); return; }
    const profile = session.snapshot().profile;
    const safe = authorizedRoute(profile);
    if (safe !== route()) { location.hash = safe; return; }
    if (importFeedback && importFeedback.scope !== route()) importFeedback = null;
    if (route() !== 'fiscal') pendingNfeFiles = [];
    renderShell();
  }

  app.addEventListener('click', async (event) => {
    const action = event.target.closest('[data-action]')?.dataset.action;
    const actionElement = event.target.closest('[data-action]');
    const widgetId = actionElement?.dataset.widgetId;
    const routeLink = event.target.closest('[data-route]');
    if (routeLink?.getAttribute('aria-disabled') === 'true') { event.preventDefault(); setAnnouncement('Disponível em próxima etapa.'); return; }
    if (action === 'remove-nfe-file') {
      const index = Number(actionElement.dataset.fileIndex);
      if (Number.isInteger(index) && index >= 0 && index < pendingNfeFiles.length) {
        const [removed] = pendingNfeFiles.splice(index, 1);
        updateNfeSelection();
        setAnnouncement(`${removed.name} removido da seleção.`);
      }
      return;
    }
    if (action === 'open-work-context') {
      userMenuOpen = false;
      workContextDialogOpen = true;
      renderShell(false);
      return;
    }
    if (action === 'close-work-context') {
      workContextDialogOpen = false;
      document.querySelector('#work-context-dialog')?.close();
      return;
    }
    if (action === 'open-customizer') {
      dashboardEditing = true;
      renderShell(false);
      document.querySelector('#dashboard-customizer')?.showModal();
      return;
    }
    if (action === 'close-customizer') {
      document.querySelector('#dashboard-customizer')?.close();
      return;
    }
    if (action === 'dashboard-refresh') {
      const profile = session.snapshot().profile;
      if (profile) refreshDashboard(profile);
      return;
    }
    if (action === 'dashboard-toggle' && widgetId) {
      const widgets = [...dashboardLayout.widgets];
      if (actionElement.checked && !widgets.includes(widgetId)) widgets.push(widgetId);
      if (!actionElement.checked && widgets.includes(widgetId)) widgets.splice(widgets.indexOf(widgetId), 1);
      dashboardLayout = dashboardService.sanitizePreferences({...dashboardLayout, widgets}, currentPermissions(session.snapshot().profile));
      return;
    }
    if (action === 'dashboard-move' && widgetId) {
      const widgets = [...dashboardLayout.widgets];
      const index = widgets.indexOf(widgetId);
      const target = index + (actionElement.dataset.direction === 'up' ? -1 : 1);
      if (index >= 0 && target >= 0 && target < widgets.length) [widgets[index], widgets[target]] = [widgets[target], widgets[index]];
      dashboardLayout = dashboardService.sanitizePreferences({...dashboardLayout, widgets}, currentPermissions(session.snapshot().profile));
      renderShell(false);
      return;
    }
    if (action === 'dashboard-resize' && widgetId) {
      const wide = new Set(dashboardLayout.wide);
      wide.has(widgetId) ? wide.delete(widgetId) : wide.add(widgetId);
      dashboardLayout = dashboardService.sanitizePreferences({...dashboardLayout, wide: [...wide]}, currentPermissions(session.snapshot().profile));
      renderShell(false);
      return;
    }
    if (action === 'dashboard-remove' && widgetId) {
      dashboardLayout = dashboardService.sanitizePreferences({...dashboardLayout, widgets: dashboardLayout.widgets.filter((id) => id !== widgetId)}, currentPermissions(session.snapshot().profile));
      renderShell(false);
      return;
    }
    if (action === 'save-dashboard') {
      dashboardLayout = dashboardService.savePreferences(dashboardLayout, currentPermissions(session.snapshot().profile));
      dashboardEditing = false;
      document.querySelector('#dashboard-customizer')?.close();
      refreshDashboard(session.snapshot().profile);
      setAnnouncement('Preferência da Minha Visão salva neste navegador.');
      return;
    }
    if (action === 'reset-dashboard') {
      dashboardService.clearPreferences();
      dashboardLayout = dashboardService.defaultLayout(currentPermissions(session.snapshot().profile));
      dashboardEditing = false;
      document.querySelector('#dashboard-customizer')?.close();
      refreshDashboard(session.snapshot().profile);
      setAnnouncement('Minha Visão restaurada ao padrão autorizado.');
      return;
    }
    if (action === 'operational-refresh') {
      const profile = session.snapshot().profile;
      if (profile) refreshOperational(profile);
      return;
    }
    if (action === 'open-company') {
      companyId = actionElement.dataset.companyId;
      operationalModel = null; operationalRequest += 1;
      location.hash = `clients?company=${encodeURIComponent(actionElement.dataset.companyId)}`;
      return;
    }
    if (action === 'company-documents') {
      companyId = actionElement.dataset.companyId;
      operationalModel = null; operationalRequest += 1;
      location.hash = 'documents';
      return;
    }
    if (action === 'bank-edit') {
      const account = operationalModel?.item?.bankAccounts?.find((item) => item.id === actionElement.dataset.accountId);
      const form = document.querySelector('#bank-account-form');
      if (!account || !form) return;
      form.dataset.accountId = account.id;
      form.elements.bank_code.value = account.bank_code;
      form.elements.bank_name.value = account.bank_name || '';
      form.elements.branch.value = '';
      form.elements.branch.placeholder = 'Deixe em branco para manter a agência atual';
      form.elements.account_number.value = '';
      form.elements.account_number.placeholder = 'Deixe em branco para manter a conta atual';
      form.elements.account_type.value = account.account_type || '';
      form.elements.nickname.value = account.nickname || '';
      form.elements.currency_code.value = account.currency_code || 'BRL';
      form.closest('details').open = true; form.elements.bank_name.focus();
      return;
    }
    if (action === 'bank-status') {
      await operationalService.setBankAccountStatus(companyId, actionElement.dataset.accountId, actionElement.dataset.status);
      await refreshOperational(session.snapshot().profile);
      setAnnouncement('Status da conta bancária atualizado.');
      return;
    }
    if (action === 'open-document') {
      location.hash = `documents?company=${encodeURIComponent(companyId)}&document=${encodeURIComponent(actionElement.dataset.documentId)}`;
      return;
    }
    if (action === 'open-fiscal') {
      intelligenceModel = null; intelligenceRequest += 1;
      location.hash = `fiscal?company=${encodeURIComponent(companyId)}&fiscal=${encodeURIComponent(actionElement.dataset.fiscalId)}`;
      return;
    }
    if (action === 'open-statement') {
      transactionFilters = Object.freeze({...transactionFilters, offset: 0});
      intelligenceModel = null; intelligenceRequest += 1;
      location.hash = `financial?company=${encodeURIComponent(companyId)}&statement=${encodeURIComponent(actionElement.dataset.statementId)}`;
      return;
    }
    if (action === 'fiscal-page') {
      fiscalFilters = Object.freeze({...fiscalFilters, offset: Number(actionElement.dataset.offset || 0)});
      refreshIntelligence(session.snapshot().profile);
      return;
    }
    if (action === 'statement-page') {
      statementFilters = Object.freeze({...statementFilters, offset: Number(actionElement.dataset.offset || 0)});
      refreshIntelligence(session.snapshot().profile);
      return;
    }
    if (action === 'transaction-page') {
      transactionFilters = Object.freeze({...transactionFilters, offset: Number(actionElement.dataset.offset || 0)});
      refreshIntelligence(session.snapshot().profile);
      return;
    }
    if (action === 'document-page') {
      documentFilters = Object.freeze({...documentFilters, offset: Number(actionElement.dataset.offset || 0)});
      refreshOperational(session.snapshot().profile);
      return;
    }
    if (action === 'clear-document-filters') {
      documentFilters = Object.freeze({search: '', status: '', source: '', received_from: '', received_to: '', offset: 0, limit: 10});
      refreshOperational(session.snapshot().profile);
      return;
    }
    if (action === 'clear-fiscal-filters') {
      fiscalFilters = Object.freeze({search: '', status: '', issued_from: '', issued_to: '', offset: 0, limit: 10});
      importFeedback = null;
      refreshIntelligence(session.snapshot().profile);
      return;
    }
    if (action === 'clear-transaction-filters') {
      transactionFilters = Object.freeze({search: '', direction: '', posted_from: '', posted_to: '', offset: 0, limit: 25});
      refreshIntelligence(session.snapshot().profile);
      return;
    }
    if (action === 'clear-proposal-filters') {
      proposalFilters = Object.freeze({status: '', account: '', source: '', document: '', rule: '', created_from: '', created_to: '', offset: 0, limit: 10});
      refreshAccounting(session.snapshot().profile);
      return;
    }
    if (action === 'open-proposal') {
      accountingModel = null; accountingRequest += 1; decisionIntent = null; decisionFeedback = null;
      location.hash = `accounting?company=${encodeURIComponent(companyId)}&proposal=${encodeURIComponent(actionElement.dataset.proposalId)}`;
      return;
    }
    if (action === 'open-item-classification') {
      accountingModel = null; accountingRequest += 1; itemDecisionOpen = false; itemDecisionFeedback = null;
      location.hash = `accounting?company=${encodeURIComponent(companyId)}&item=${encodeURIComponent(actionElement.dataset.classificationId)}`;
      return;
    }
    if (action === 'item-queue-page') {
      itemQueueFilters = Object.freeze({...itemQueueFilters, offset: Number(actionElement.dataset.offset || 0)});
      refreshAccounting(session.snapshot().profile);
      return;
    }
    if (action === 'open-item-decision') {
      itemDecisionOpen = true; itemDecisionFeedback = null;
      renderShell(false); document.querySelector('#item-classification-decision-dialog')?.showModal();
      return;
    }
    if (action === 'close-item-decision') {
      document.querySelector('#item-classification-decision-dialog')?.close(); itemDecisionOpen = false; itemDecisionFeedback = null;
      renderShell(false);
      return;
    }
    if (action === 'open-rule') {
      accountingModel = null; accountingRequest += 1;
      const effectiveAt = routeParams().get('effective_at');
      location.hash = `accounting?company=${encodeURIComponent(companyId)}&rule=${encodeURIComponent(actionElement.dataset.ruleId)}&effective_at=${encodeURIComponent(effectiveAt)}`;
      return;
    }
    if (action === 'proposal-page') {
      proposalFilters = Object.freeze({...proposalFilters, offset: Number(actionElement.dataset.offset || 0)});
      refreshAccounting(session.snapshot().profile);
      return;
    }
    if (action === 'open-decision') {
      decisionIntent = actionElement.dataset.decision; decisionFeedback = null;
      renderShell(false); document.querySelector('#accounting-decision-dialog')?.showModal();
      return;
    }
    if (action === 'close-decision') {
      document.querySelector('#accounting-decision-dialog')?.close(); decisionIntent = null; decisionFeedback = null;
      renderShell(false);
      return;
    }
    if (action === 'begin-login') {
      session.authenticating(); renderLogin();
      try { await oidcClient.beginLogin(`#${route()}`); }
      catch (_) { session.unauthenticated(); renderLogin('Não foi possível iniciar a autenticação. Verifique a configuração do ambiente.'); }
    } else if (action === 'start-demo' && config.authMode === 'synthetic' && config.environment === 'development') {
      const profile = root.S21SyntheticProvider.loadProfile();
      session.startSyntheticWorkspace(profile); initializeWorkContext(profile, true);
      location.hash = authorizedRoute(profile); renderShell();
    } else if (action === 'logout') {
      const wasOidc = session.snapshot().mode === 'oidc';
      session.logout(); userMenuOpen = false; companyId = null; workContext = null; workContextSettings = null; workContextDialogOpen = false; dashboardLayout = null; dashboardModel = null; dashboardRequest += 1; operationalModel = null; operationalRequest += 1; intelligenceModel = null; intelligenceRequest += 1; importFeedback = null; pendingNfeFiles = []; accountingModel = null; accountingRequest += 1; decisionIntent = null; decisionFeedback = null; itemDecisionOpen = false; itemDecisionFeedback = null;
      history.replaceState(null, '', location.pathname);
      if (wasOidc) await oidcClient.logout();
      renderLogin('A sessão do aplicativo foi encerrada.');
    } else if (action === 'toggle-user-menu') {
      userMenuOpen = !userMenuOpen; renderShell(false); document.querySelector('[data-action="toggle-user-menu"]').focus();
    } else if (action === 'open-drawer') { drawerOpen = true; renderShell(false); }
    else if (action === 'close-drawer') { drawerOpen = false; renderShell(false); document.querySelector('[data-action="open-drawer"]')?.focus(); }
    else if (action === 'safe-return') {
      if (session.snapshot().profile) { session.resume(); renderShell(); } else renderLogin();
    }
  });

  app.addEventListener('change', (event) => {
    if (event.target.matches('#nfe-import-form [name="period_end"]')) {
      const form = event.target.form;
      try { form.elements.approval_expiry_date.value = workContextService.reviewExpiry(event.target.value, workContextSettings.reviewDays, workContextSettings.reviewBasis); }
      catch (_) { form.elements.approval_expiry_date.value = ''; }
      return;
    }
    if (event.target.matches('#nfe-file-input, #nfe-folder-input')) {
      const selected = [...event.target.files];
      const compatible = selected.filter((file) => file.name.toLocaleLowerCase('pt-BR').endsWith('.xml'));
      const known = new Set(pendingNfeFiles.map((file) => `${file.name}:${file.size}:${file.lastModified}`));
      const added = compatible.filter((file) => !known.has(`${file.name}:${file.size}:${file.lastModified}`));
      pendingNfeFiles.push(...added);
      event.target.value = '';
      updateNfeSelection();
      const ignored = selected.length - compatible.length;
      setAnnouncement(`${added.length} XML adicionado(s).${ignored ? ` ${ignored} arquivo(s) incompatível(is) ignorado(s).` : ''}`);
      return;
    }
    if (event.target.id === 'company-context') {
      dashboardRequest += 1; dashboardModel = null; dashboardLayout = null;
      operationalRequest += 1; operationalModel = null;
      intelligenceRequest += 1; intelligenceModel = null; importFeedback = null; pendingNfeFiles = [];
      accountingRequest += 1; accountingModel = null; decisionIntent = null; decisionFeedback = null; itemDecisionOpen = false; itemDecisionFeedback = null;
      fiscalFilters = Object.freeze({...fiscalFilters, offset: 0});
      statementFilters = Object.freeze({...statementFilters, offset: 0});
      transactionFilters = Object.freeze({...transactionFilters, offset: 0});
      proposalFilters = Object.freeze({...proposalFilters, offset: 0});
      itemQueueFilters = Object.freeze({...itemQueueFilters, offset: 0});
      companyId = event.target.value;
      if (companyId !== dashboardService.allAuthorizedId) {
        const saved = workContextService.save({...workContext, companyId}, workContextSettings, session.snapshot().profile.companies);
        workContext = saved.context; workContextSettings = saved.settings;
      }
      const destination = ['documents', 'inbox', 'fiscal', 'financial', 'accounting'].includes(route()) ? route() : 'overview';
      location.hash = destination; renderShell();
      setAnnouncement('Contexto de empresa alterado. Dados anteriores descartados.');
    }
    if (event.target.id === 'dashboard-preset') {
      dashboardLayout = dashboardService.defaultLayout(currentPermissions(session.snapshot().profile), event.target.value);
      dashboardLayout = dashboardService.savePreferences(dashboardLayout, currentPermissions(session.snapshot().profile));
      refreshDashboard(session.snapshot().profile);
      setAnnouncement(`${event.target.value} aplicada.`);
    }
  });

  app.addEventListener('submit', async (event) => {
    if (event.target.id === 'work-context-form') {
      event.preventDefault();
      const profile = session.snapshot().profile;
      const values = Object.fromEntries(new FormData(event.target).entries());
      const saved = workContextService.save(
        {companyId: String(values.company_id), referenceMonth: String(values.reference_month)},
        {askAtStart: values.ask_at_start === 'on', reviewDays: Number(values.review_days), reviewBasis: String(values.review_basis)},
        profile.companies,
      );
      workContext = saved.context; workContextSettings = saved.settings;
      companyId = workContext.companyId; workContextDialogOpen = false; pendingNfeFiles = []; importFeedback = null;
      dashboardModel = null; dashboardLayout = null; dashboardRequest += 1;
      operationalModel = null; operationalRequest += 1;
      intelligenceModel = null; intelligenceRequest += 1;
      accountingModel = null; accountingRequest += 1; decisionIntent = null; decisionFeedback = null; itemDecisionOpen = false; itemDecisionFeedback = null;
      renderShell();
      setAnnouncement(`Contexto aplicado: ${workContext.referenceMonth}.`);
      return;
    }
    if (event.target.id === 'company-search-form') {
      event.preventDefault();
      const value = new FormData(event.target).get('search') || '';
      operationalModel = {...operationalModel, search: String(value)};
      renderShell(false);
      return;
    }
    if (event.target.id === 'document-filter-form') {
      event.preventDefault();
      const values = Object.fromEntries(new FormData(event.target).entries());
      documentFilters = Object.freeze({...documentFilters, ...values, offset: 0});
      refreshOperational(session.snapshot().profile);
    }
    if (event.target.id === 'bank-account-form') {
      event.preventDefault();
      const payload = Object.fromEntries(new FormData(event.target).entries());
      const accountId = event.target.dataset.accountId;
      await (accountId ? operationalService.updateBankAccount(companyId, accountId, payload) : operationalService.createBankAccount(companyId, payload));
      await refreshOperational(session.snapshot().profile);
      setAnnouncement(accountId ? 'Conta bancária atualizada.' : 'Conta bancária cadastrada.');
      return;
    }
    if (event.target.id === 'document-metadata-form') {
      event.preventDefault();
      const documentId = routeParams().get('document');
      await operationalService.updateDocumentMetadata(companyId, documentId, Object.fromEntries(new FormData(event.target).entries()));
      await refreshOperational(session.snapshot().profile);
      setAnnouncement('Metadados do documento atualizados; a evidência original não foi alterada.');
      return;
    }
    if (event.target.id === 'fiscal-filter-form') {
      event.preventDefault();
      importFeedback = null;
      fiscalFilters = Object.freeze({...fiscalFilters, ...Object.fromEntries(new FormData(event.target).entries()), offset: 0});
      refreshIntelligence(session.snapshot().profile);
    }
    if (event.target.id === 'transaction-filter-form') {
      event.preventDefault();
      transactionFilters = Object.freeze({...transactionFilters, ...Object.fromEntries(new FormData(event.target).entries()), offset: 0});
      refreshIntelligence(session.snapshot().profile);
    }
    if (event.target.id === 'proposal-filter-form') {
      event.preventDefault();
      proposalFilters = Object.freeze({...proposalFilters, ...Object.fromEntries(new FormData(event.target).entries()), offset: 0});
      refreshAccounting(session.snapshot().profile);
      return;
    }
    if (event.target.id === 'catalog-effective-form') {
      event.preventDefault();
      const effectiveAt = new FormData(event.target).get('effective_at');
      accountingModel = null; accountingRequest += 1;
      location.hash = `accounting?view=rules&company=${encodeURIComponent(companyId)}&effective_at=${encodeURIComponent(effectiveAt)}`;
      return;
    }
    if (event.target.id === 'catalog-account-search') {
      event.preventDefault();
      catalogSearch = String(new FormData(event.target).get('search') || '');
      renderShell(false);
      return;
    }
    if (event.target.id === 'accounting-decision-form') {
      event.preventDefault();
      const summary = accountingModel?.item?.summary;
      if (!summary || !decisionIntent) return;
      const requestId = ++accountingRequest;
      decisionFeedback = {state: 'LOADING', message: 'A revisão, o hash, a versão, as permissões e os bloqueios serão revalidados no backend.'};
      renderShell(false); document.querySelector('#accounting-decision-dialog')?.showModal();
      (async () => {
        try {
          await accountingService.decideProposal(companyId, summary.journey_id, decisionIntent, summary);
          if (requestId !== accountingRequest) return;
          decisionIntent = null; decisionFeedback = null;
          setAnnouncement('Decisão profissional registrada. Nenhuma postagem ou exportação foi realizada.');
          await refreshAccounting(session.snapshot().profile);
        } catch (error) {
          if (requestId !== accountingRequest) return;
          const messages = {
            RESOURCE_LOCKED: 'A operação está bloqueada. Confira o escopo e o motivo do bloqueio exibido na proposta.',
            FORBIDDEN: 'Seu contexto não autoriza esta decisão ou a segregação de funções a impede.',
            REQUEST_FAILED: 'A proposta mudou, expirou ou já recebeu uma decisão. Atualize antes de tentar novamente.',
          };
          decisionFeedback = {state: 'ERROR', message: messages[error?.code] || 'A decisão não pôde ser registrada com segurança.'};
          renderShell(false); document.querySelector('#accounting-decision-dialog')?.showModal();
        }
      })();
      return;
    }
    if (event.target.id === 'item-classification-decision-form') {
      event.preventDefault();
      const detail = accountingModel?.detail;
      if (!detail || !itemDecisionOpen) return;
      const values = Object.fromEntries(new FormData(event.target).entries());
      const finalIntent = String(values.final_intent || '');
      const applyScope = String(values.apply_scope || '');
      const decisionType = finalIntent === detail.summary.selected_intent ? 'CONFIRMATION' : 'CORRECTION';
      const requestId = ++accountingRequest;
      itemDecisionFeedback = {state: 'LOADING', message: 'A permissão e o escopo de empresa serão revalidados no backend.'};
      renderShell(false); document.querySelector('#item-classification-decision-dialog')?.showModal();
      (async () => {
        try {
          await accountingService.decideItemClassification(companyId, detail.summary.id, {finalIntent, decisionType, applyScope});
          if (requestId !== accountingRequest) return;
          itemDecisionOpen = false; itemDecisionFeedback = null;
          setAnnouncement('Classificação profissional registrada. Nenhuma escrituração foi realizada.');
          await refreshAccounting(session.snapshot().profile);
        } catch (error) {
          if (requestId !== accountingRequest) return;
          const messages = {
            FORBIDDEN: 'Seu contexto não autoriza esta decisão de classificação.',
            REQUEST_FAILED: 'O item mudou ou já foi decidido. Atualize antes de tentar novamente.',
          };
          itemDecisionFeedback = {state: 'ERROR', message: messages[error?.code] || 'A classificação não pôde ser registrada com segurança.'};
          renderShell(false); document.querySelector('#item-classification-decision-dialog')?.showModal();
        }
      })();
      return;
    }
    if (event.target.id === 'nfe-import-form' || event.target.id === 'ofx-import-form') {
      event.preventDefault();
      const isNfe = event.target.id === 'nfe-import-form';
      const extension = isNfe ? '.xml' : '.ofx';
      const files = isNfe ? [...pendingNfeFiles] : [...event.target.elements.file.files];
      if (!files.length || files.some((file) => !file.name.toLocaleLowerCase('pt-BR').endsWith(extension))) {
        importFeedback = {scope: route(), state: 'ERROR', message: `Selecione arquivo(s) ${extension} compatível(is).`}; renderShell(false); return;
      }
      const values = Object.fromEntries(new FormData(event.target).entries());
      if (isNfe && (values.period_start > values.period_end
        || (values.accounting_date && (values.accounting_date < values.period_start || values.accounting_date > values.period_end)))) {
        importFeedback = {scope: route(), state: 'ERROR', message: values.period_start > values.period_end ? 'O início do período não pode ser posterior ao fim.' : 'A data contábil informada precisa estar dentro do período.'};
        renderShell(false); return;
      }
      importFeedback = {scope: route(), state: 'LOADING', message: `Validando ${files.length} arquivo(s) no contrato autorizado…`, items: files.map((file) => ({filename: file.name, status: 'PROCESSING', message: 'Aguardando validação.'}))}; renderShell(false);
      const requestId = ++intelligenceRequest;
      (async () => {
        try {
          let result;
          if (isNfe) {
            const expires = new Date(`${String(values.approval_expiry_date)}T23:59:59`);
            if (Number.isNaN(expires.getTime())) throw new Error('invalid date');
            const summary = {total: files.length, success: 0, duplicate: 0, invalid: 0, period_mismatch: 0, wrong_company: 0, failed: 0};
            const items = [];
            const retryFiles = [];
            for (const file of files) {
              try {
                const inspection = await inspectNfeXml(file);
                if (inspection.error) {
                  summary.invalid += 1;
                  items.push({filename: file.name, status: 'INVALID', message: inspection.error});
                  continue;
                }
                if (!values.accounting_date && (inspection.issuedDate < values.period_start || inspection.issuedDate > values.period_end)) {
                  summary.period_mismatch += 1;
                  retryFiles.push(file);
                  items.push({filename: file.name, status: 'PERIOD_MISMATCH', message: `Emissão ${inspection.issuedDate}; período escolhido ${values.period_start} a ${values.period_end}. Ajuste o contexto ou informe conscientemente outra data contábil.`});
                  continue;
                }
                const item = await intelligenceService.importNfe(companyId, file, {
                  accounting_date: values.accounting_date || '', period_start: values.period_start,
                  period_end: values.period_end, approval_expires_at: expires.toISOString(),
                });
                if (item.status === 'IDEMPOTENT_REDELIVERY' || Number(item.duplicate_items || 0) > 0) {
                  summary.duplicate += 1;
                  items.push({filename: file.name, status: 'DUPLICATE', message: 'Este conteúdo já havia sido recebido; o resultado anterior foi reutilizado.'});
                } else if (item.status === 'QUARANTINED') {
                  summary.invalid += 1;
                  items.push({filename: file.name, status: 'INVALID', message: 'O arquivo não passou pela validação e requer atenção.'});
                } else {
                  summary.success += 1;
                  items.push({filename: file.name, status: 'SUCCESS', message: item.synthetic ? 'Teste sintético concluído; nenhum arquivo foi persistido.' : 'Arquivo recebido e encaminhado para processamento.'});
                }
              } catch (error) {
                if (error?.code === 'NFE_COMPANY_MISMATCH') {
                  summary.wrong_company += 1;
                  items.push({filename: file.name, status: 'WRONG_COMPANY', message: 'O CNPJ da NF-e não corresponde à empresa selecionada.'});
                } else {
                  summary.failed += 1;
                  items.push({filename: file.name, status: 'FAILED', message: error?.code === 'COMPANY_TAX_ID_GAP' ? 'A empresa selecionada não possui CNPJ configurado.' : 'Não foi possível importar este arquivo.'});
                }
              }
            }
            pendingNfeFiles = retryFiles;
            result = {scope: 'fiscal', state: summary.failed || summary.invalid || summary.period_mismatch || summary.wrong_company ? 'ERROR' : 'SUCCESS', synthetic: config.dataMode === 'synthetic', items, message: `Total ${summary.total} · recebido ${summary.success} · duplicado ${summary.duplicate} · fora do período ${summary.period_mismatch} · inválido ${summary.invalid} · empresa divergente ${summary.wrong_company} · falhou ${summary.failed}${config.dataMode === 'synthetic' ? ' · simulação sem persistência' : ''}`};
          } else result = {...await intelligenceService.importOfx(companyId, files[0]), scope: 'financial'};
          if (requestId !== intelligenceRequest) return;
          importFeedback = result;
          setAnnouncement('Resultado da importação disponível.');
          await refreshIntelligence(session.snapshot().profile);
        } catch (error) {
          if (requestId !== intelligenceRequest) return;
          importFeedback = {scope: route(), state: 'ERROR', message: error?.code === 'FORBIDDEN' ? 'Importação não autorizada.' : 'Não foi possível importar. Verifique o arquivo e os campos.'};
          renderShell(false);
        }
      })();
    }
  });

  async function boot() {
    if (config.authMode === 'synthetic' && config.environment === 'development') {
      if (location.hash && route() !== 'overview') {
        const profile = root.S21SyntheticProvider.loadProfile();
        session.startSyntheticWorkspace(profile);
        initializeWorkContext(profile, true);
        location.hash = authorizedRoute(profile);
        renderShell();
      } else { session.unauthenticated(); renderLogin(); }
      return;
    }
    if (config.authMode !== 'oidc' || !oidcClient.isConfigured()) { session.unauthenticated(); renderLogin(); return; }
    if (!oidcClient.hasCallback()) { session.unauthenticated(); renderLogin(); return; }
    session.authenticating(); renderLogin();
    try {
      const callback = await oidcClient.handleCallback();
      await bootstrapAuthenticated(callback.accessToken, callback.returnTo);
    } catch (_) {
      session.unauthenticated();
      renderLogin('A autenticação não pôde ser concluída. Tente entrar novamente.');
    }
  }

  root.addEventListener('hashchange', navigateSafe);
  root.S21Application = Object.freeze({apiClient, oidcClient});
  boot();
}(globalThis));
