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

  const navigation = Object.freeze([
    {group: 'Principal', id: 'overview', label: 'Minha Visão', permissions: ['company.read']},
    {group: 'Operação', id: 'operation', label: 'Operação', permissions: ['company.read'], planned: true},
    {group: 'Operação', id: 'fiscal', label: 'Fiscal', permissions: ['company.read'], planned: true},
    {group: 'Operação', id: 'financial', label: 'Financeiro', permissions: ['reconciliation.manage'], planned: true},
    {group: 'Operação', id: 'accounting', label: 'Contábil', permissions: ['journal.read']},
    {group: 'Relacionamento', id: 'clients', label: 'Clientes', permissions: ['company.read'], planned: true},
    {group: 'Relacionamento', id: 'obligations', label: 'Obrigações', permissions: [], planned: true},
    {group: 'Controle', id: 'governance', label: 'Governança', permissions: ['audit.read', 'lock.manage']},
    {group: 'Controle', id: 'administration', label: 'Administração', permissions: ['identity.manage', 'catalog.manage']},
  ]);

  const escapeHtml = (value) => String(value).replace(/[&<>'"]/g, (character) => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[character]));
  const initials = (name) => name.split(/\s+/).slice(0, 2).map((part) => part[0]).join('').toUpperCase();
  const route = () => (location.hash.slice(1) || 'overview').split('?')[0];
  const setAnnouncement = (message) => { announcer.textContent = ''; root.setTimeout(() => { announcer.textContent = message; }, 0); };

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
    return Object.freeze({companyIds: Object.freeze(companyIds), permissions: Object.freeze(currentPermissions(profile))});
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
    const wide = layout.wide.includes(widget.id) || ['LIST', 'TIMELINE', 'TABLE_PREVIEW'].includes(widget.kind);
    const classes = `card dashboard-widget ${wide ? 'wide' : ''} ${state?.state === 'ERROR' ? 'widget-error' : ''}`;
    const heading = `<header class="widget-heading"><div><span class="widget-code">${widget.id}</span><h2 id="heading-${widget.id}">${escapeHtml(widget.label)}</h2></div>${config.dataMode === 'synthetic' ? '<span class="badge intelligent">Sintético</span>' : ''}</header>`;
    let body = '<div class="widget-loading" role="status"><span>Carregando indicador…</span><div class="skeleton metric" aria-hidden="true"></div></div>';
    if (state?.state === 'ERROR') body = `<div class="widget-state" role="alert"><strong>Indicador indisponível</strong><p>${escapeHtml(state.note)}</p><button class="btn secondary small" data-action="dashboard-refresh">Tentar novamente</button></div>`;
    else if (state?.state === 'UNAVAILABLE') body = `<div class="widget-state"><strong>Fonte ainda não integrada</strong><p>${escapeHtml(state.note)}</p></div>`;
    else if (state?.state === 'EMPTY') body = `<div class="widget-state"><strong>${escapeHtml(state.note)}</strong><p>Nenhuma ação é necessária neste contexto.</p></div>`;
    else if (state?.state === 'READY') {
      const value = state.value === '' ? '' : `<strong class="dashboard-value">${escapeHtml(state.value)}</strong>`;
      body = `${value}<p class="widget-note">${escapeHtml(state.note)}</p>${widgetItems(state.items, widget.kind === 'TIMELINE')}<footer class="widget-footer"><small>${escapeHtml(formatUpdatedAt(state.updatedAt))}</small><button class="btn ghost small" type="button" disabled title="Destino operacional ainda não integrado">${escapeHtml(widget.action)}</button></footer>`;
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

  function placeholderMarkup(item, profile) {
    if (!item || !hasPermission(currentPermissions(profile), item.permissions)) return null;
    return `<div class="page-heading"><div><span class="eyebrow">Aplicativo Serdial21</span><h1>${escapeHtml(item.label)}</h1><p>Esta área será integrada em uma etapa futura.</p></div></div><section class="card empty"><h2>Disponível em próxima etapa</h2><p>Nenhuma funcionalidade operacional fictícia foi criada.</p><a class="btn secondary" href="#overview">Voltar</a></section>`;
  }

  function renderShell(loadDashboard = true) {
    const {profile, mode} = session.snapshot();
    if (!profile || session.snapshot().state !== STATES.AUTHENTICATED) { renderLogin(); return; }
    companyId = companyId || profile.companies[0]?.id || null;
    const target = navigation.find((item) => item.id === route());
    const content = route() === 'overview' && hasPermission(currentPermissions(profile), ['company.read'])
      ? overviewMarkup(profile) : placeholderMarkup(target, profile);
    if (!content) { session.forbid(); renderState(STATES.FORBIDDEN); return; }
    const currentCompany = profile.companies.find((company) => company.id === companyId);
    const contextName = companyId === dashboardService.allAuthorizedId
      ? 'Todas as empresas autorizadas'
      : currentCompany?.name || 'Sem empresa autorizada';
    const allOption = profile.companies.length > 1
      ? `<option value="${dashboardService.allAuthorizedId}" ${companyId === dashboardService.allAuthorizedId ? 'selected' : ''}>Todas as empresas autorizadas</option>`
      : '';
    app.innerHTML = `<div class="app-shell auth-shell"><aside class="sidebar ${drawerOpen ? 'open' : ''}" aria-label="Navegação lateral"><a class="brand-link" href="#overview"><img class="brand-image shell-logo" src="../ui/assets/brand/S21%20assinatura%20principal.png" alt="Serdial21 Contabilidade Inteligente"></a><div class="office">${escapeHtml(profile.tenant.name)}<small>${mode === 'synthetic' ? 'Contexto fictício' : 'Contexto autorizado'}</small></div><nav class="nav" aria-label="Navegação principal">${navMarkup(profile)}</nav><div class="sidebar-foot"><span>${escapeHtml(profile.user.displayName)}</span><small>${escapeHtml(profile.user.roleLabel || '')}</small><button class="btn ghost drawer-close" data-action="close-drawer">Fechar menu</button></div></aside><button class="drawer-backdrop ${drawerOpen ? 'open' : ''}" data-action="close-drawer" aria-label="Fechar navegação"></button><div class="workspace"><header class="topbar"><div class="context"><button class="btn ghost mobile-menu" data-action="open-drawer" aria-label="Abrir navegação">☰</button><div class="context-copy"><strong>${escapeHtml(contextName)}</strong><small>${escapeHtml(profile.tenant.name)}</small></div><label>Empresa<select id="company-context" ${profile.companies.length < 2 ? 'disabled' : ''}>${allOption}${profile.companies.map((company) => `<option value="${escapeHtml(company.id)}" ${company.id === companyId ? 'selected' : ''}>${escapeHtml(company.name)}</option>`).join('')}</select></label></div><div class="topbar-actions"><span class="environment-banner">${escapeHtml(config.environmentLabel)}</span><div class="profile-menu"><button class="btn ghost profile-trigger" data-action="toggle-user-menu" aria-expanded="${userMenuOpen}" aria-controls="user-popover"><span class="avatar">${escapeHtml(initials(profile.user.displayName))}</span><span class="profile-label">${escapeHtml(profile.user.displayName)}</span></button><div class="profile-popover" id="user-popover" ${userMenuOpen ? '' : 'hidden'}><strong>${escapeHtml(profile.user.displayName)}</strong><p>${escapeHtml(profile.tenant.name)}</p><button class="btn secondary" data-action="logout">Sair do aplicativo</button></div></div></div></header><div class="mode-banner">${mode === 'synthetic' ? 'DEMONSTRAÇÃO LOCAL · identidade, empresas e conteúdo sintéticos · sem acesso à API' : `SESSÃO OIDC · ${config.dataMode === 'synthetic' ? 'conteúdo de negócio sintético' : 'contexto autorizado'}`}</div><main id="main" tabindex="-1">${content}<p class="footer-note">Serdial21 Contabilidade Inteligente · A automação prepara. O profissional decide.</p></main></div></div>`;
    app.setAttribute('aria-busy', 'false');
    if (loadDashboard && route() === 'overview') refreshDashboard(profile);
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
      companyId = profile.companies[0]?.id || null;
      session.establish({token: accessToken, userProfile: profile});
      const permissions = currentPermissions(profile);
      const requested = String(returnTo || '').match(/^#[a-z-]+$/)?.[0]?.slice(1);
      const firstAllowed = allowedNavigation(navigation, permissions).find((item) => !item.planned)?.id;
      location.hash = navigation.some((item) => item.id === requested && hasPermission(permissions, item.permissions)) ? requested : firstAllowed || 'overview';
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
    renderShell();
  }

  app.addEventListener('click', async (event) => {
    const action = event.target.closest('[data-action]')?.dataset.action;
    const actionElement = event.target.closest('[data-action]');
    const widgetId = actionElement?.dataset.widgetId;
    const routeLink = event.target.closest('[data-route]');
    if (routeLink?.getAttribute('aria-disabled') === 'true') { event.preventDefault(); setAnnouncement('Disponível em próxima etapa.'); return; }
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
    if (action === 'begin-login') {
      session.authenticating(); renderLogin();
      try { await oidcClient.beginLogin(`#${route()}`); }
      catch (_) { session.unauthenticated(); renderLogin('Não foi possível iniciar a autenticação. Verifique a configuração do ambiente.'); }
    } else if (action === 'start-demo' && config.authMode === 'synthetic' && config.environment === 'development') {
      session.startSyntheticWorkspace(root.S21SyntheticProvider.loadProfile()); companyId = null; location.hash = 'overview'; renderShell();
    } else if (action === 'logout') {
      const wasOidc = session.snapshot().mode === 'oidc';
      session.logout(); userMenuOpen = false; companyId = null; dashboardLayout = null; dashboardModel = null; dashboardRequest += 1;
      history.replaceState(null, '', location.pathname);
      if (wasOidc) await oidcClient.logout();
      renderLogin('A sessão do aplicativo foi encerrada.');
    } else if (action === 'toggle-user-menu') {
      userMenuOpen = !userMenuOpen; renderShell(); document.querySelector('[data-action="toggle-user-menu"]').focus();
    } else if (action === 'open-drawer') { drawerOpen = true; renderShell(); }
    else if (action === 'close-drawer') { drawerOpen = false; renderShell(); document.querySelector('[data-action="open-drawer"]')?.focus(); }
    else if (action === 'safe-return') {
      if (session.snapshot().profile) { session.resume(); renderShell(); } else renderLogin();
    }
  });

  app.addEventListener('change', (event) => {
    if (event.target.id === 'company-context') {
      dashboardRequest += 1; dashboardModel = null; dashboardLayout = null;
      companyId = event.target.value; location.hash = 'overview'; renderShell();
      setAnnouncement('Contexto de empresa alterado. Dados anteriores descartados.');
    }
    if (event.target.id === 'dashboard-preset') {
      dashboardLayout = dashboardService.defaultLayout(currentPermissions(session.snapshot().profile), event.target.value);
      dashboardLayout = dashboardService.savePreferences(dashboardLayout, currentPermissions(session.snapshot().profile));
      refreshDashboard(session.snapshot().profile);
      setAnnouncement(`${event.target.value} aplicada.`);
    }
  });

  async function boot() {
    if (config.authMode === 'synthetic' && config.environment === 'development') { session.unauthenticated(); renderLogin(); return; }
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
