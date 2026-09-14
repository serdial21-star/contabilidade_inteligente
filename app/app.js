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

  const apiClient = root.S21ApiClient.createApiClient({
    baseUrl: config.apiBaseUrl,
    getAccessToken: session.token,
    onAuthenticationFailure: () => { session.expire(); renderLogin(); },
  });
  const oidcClient = root.S21OidcClient.createOidcClient({config, getAccessToken: session.token});

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
    const company = profile.companies.find((item) => item.id === companyId);
    return [...new Set([...(profile.permissions || []), ...(company?.permissions || [])])];
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

  function overviewMarkup() {
    const data = root.S21SyntheticProvider.loadDashboard();
    return `<div class="page-heading"><div><span class="eyebrow">Sua operação</span><h1>Minha Visão</h1><p>Acompanhe o que precisa de atenção. Indicadores demonstrativos, sem dados reais.</p></div><span class="badge intelligent">Base sintética</span></div><section class="placeholder-grid" aria-label="Indicadores sintéticos">${data.metrics.map((metric) => `<article class="card placeholder-card"><span class="widget-title">${escapeHtml(metric.label)}</span><strong>${escapeHtml(metric.value)}</strong><small>${escapeHtml(metric.note)}</small></article>`).join('')}</section><div class="two-col"><section class="card"><header class="card-head"><div><h2>Fila Inteligente</h2><p>Itens fictícios que aguardam atenção.</p></div></header><div class="pad"><ul class="queue-list">${data.queue.map((item) => `<li><strong>${escapeHtml(item.id)}</strong><span>${escapeHtml(item.type)} · ${escapeHtml(item.reason)}</span><span class="badge ${item.priority === 'Alta' ? 'warning' : 'neutral'}">${escapeHtml(item.priority)}</span></li>`).join('')}</ul></div></section><aside class="card pad stack"><h2>Fundação pronta</h2><p>Os agregados reais pertencem à Phase 05.</p><div class="alert info"><div><strong>Backend continua soberano</strong><p>Visibilidade na interface não substitui autorização na API.</p></div></div></aside></div>`;
  }

  function placeholderMarkup(item, profile) {
    if (!item || !hasPermission(currentPermissions(profile), item.permissions)) return null;
    return `<div class="page-heading"><div><span class="eyebrow">Aplicativo Serdial21</span><h1>${escapeHtml(item.label)}</h1><p>Esta área será integrada em uma etapa futura.</p></div></div><section class="card empty"><h2>Disponível em próxima etapa</h2><p>Nenhuma funcionalidade operacional fictícia foi criada.</p><a class="btn secondary" href="#overview">Voltar</a></section>`;
  }

  function renderShell() {
    const {profile, mode} = session.snapshot();
    if (!profile || session.snapshot().state !== STATES.AUTHENTICATED) { renderLogin(); return; }
    companyId = companyId || profile.companies[0]?.id || null;
    const target = navigation.find((item) => item.id === route());
    const content = route() === 'overview' && hasPermission(currentPermissions(profile), ['company.read'])
      ? overviewMarkup() : placeholderMarkup(target, profile);
    if (!content) { session.forbid(); renderState(STATES.FORBIDDEN); return; }
    const currentCompany = profile.companies.find((company) => company.id === companyId);
    app.innerHTML = `<div class="app-shell auth-shell"><aside class="sidebar ${drawerOpen ? 'open' : ''}" aria-label="Navegação lateral"><a class="brand-link" href="#overview"><img class="brand-image shell-logo" src="../ui/assets/brand/S21%20assinatura%20principal.png" alt="Serdial21 Contabilidade Inteligente"></a><div class="office">${escapeHtml(profile.tenant.name)}<small>${mode === 'synthetic' ? 'Contexto fictício' : 'Contexto autorizado'}</small></div><nav class="nav" aria-label="Navegação principal">${navMarkup(profile)}</nav><div class="sidebar-foot"><span>${escapeHtml(profile.user.displayName)}</span><small>${escapeHtml(profile.user.roleLabel || '')}</small><button class="btn ghost drawer-close" data-action="close-drawer">Fechar menu</button></div></aside><button class="drawer-backdrop ${drawerOpen ? 'open' : ''}" data-action="close-drawer" aria-label="Fechar navegação"></button><div class="workspace"><header class="topbar"><div class="context"><button class="btn ghost mobile-menu" data-action="open-drawer" aria-label="Abrir navegação">☰</button><div class="context-copy"><strong>${escapeHtml(currentCompany?.name || 'Sem empresa autorizada')}</strong><small>${escapeHtml(profile.tenant.name)}</small></div><label>Empresa<select id="company-context" ${profile.companies.length < 2 ? 'disabled' : ''}>${profile.companies.map((company) => `<option value="${escapeHtml(company.id)}" ${company.id === companyId ? 'selected' : ''}>${escapeHtml(company.name)}</option>`).join('')}</select></label></div><div class="topbar-actions"><span class="environment-banner">${escapeHtml(config.environmentLabel)}</span><div class="profile-menu"><button class="btn ghost profile-trigger" data-action="toggle-user-menu" aria-expanded="${userMenuOpen}" aria-controls="user-popover"><span class="avatar">${escapeHtml(initials(profile.user.displayName))}</span><span class="profile-label">${escapeHtml(profile.user.displayName)}</span></button><div class="profile-popover" id="user-popover" ${userMenuOpen ? '' : 'hidden'}><strong>${escapeHtml(profile.user.displayName)}</strong><p>${escapeHtml(profile.tenant.name)}</p><button class="btn secondary" data-action="logout">Sair do aplicativo</button></div></div></div></header><div class="mode-banner">${mode === 'synthetic' ? 'DEMONSTRAÇÃO LOCAL · identidade, empresas e conteúdo sintéticos · sem acesso à API' : `SESSÃO OIDC · ${config.dataMode === 'synthetic' ? 'conteúdo de negócio sintético' : 'contexto autorizado'}`}</div><main id="main" tabindex="-1">${content}<p class="footer-note">Serdial21 Contabilidade Inteligente · A automação prepara. O profissional decide.</p></main></div></div>`;
    app.setAttribute('aria-busy', 'false');
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
    const routeLink = event.target.closest('[data-route]');
    if (routeLink?.getAttribute('aria-disabled') === 'true') { event.preventDefault(); setAnnouncement('Disponível em próxima etapa.'); return; }
    if (action === 'begin-login') {
      session.authenticating(); renderLogin();
      try { await oidcClient.beginLogin(`#${route()}`); }
      catch (_) { session.unauthenticated(); renderLogin('Não foi possível iniciar a autenticação. Verifique a configuração do ambiente.'); }
    } else if (action === 'start-demo' && config.authMode === 'synthetic' && config.environment === 'development') {
      session.startSyntheticWorkspace(root.S21SyntheticProvider.loadProfile()); companyId = null; location.hash = 'overview'; renderShell();
    } else if (action === 'logout') {
      const wasOidc = session.snapshot().mode === 'oidc';
      session.logout(); userMenuOpen = false; companyId = null;
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
    if (event.target.id === 'company-context') { companyId = event.target.value; location.hash = 'overview'; renderShell(); setAnnouncement('Contexto de empresa alterado.'); }
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
