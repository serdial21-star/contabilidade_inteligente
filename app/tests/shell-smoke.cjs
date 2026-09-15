/* Focused Phase 04 tests. No browser/layout claim. Run with Node 18+. */
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const appDir = path.resolve(__dirname, '..');
const read = (file) => fs.readFileSync(path.join(appDir, file), 'utf8');
function load(files, additions = {}) {
  const context = {...additions};
  context.globalThis = context;
  vm.createContext(context);
  files.forEach((file) => vm.runInContext(read(file), context, {filename: file}));
  return context;
}

test('application entry provides branded boot state and defensive metadata', () => {
  const html = read('index.html');
  assert.match(html, /Inicializando ambiente seguro/);
  assert.match(html, /noindex,nofollow/);
  assert.match(html, /connect-src 'self'/);
  assert.match(html, /form-action 'none'/);
  for (const asset of ['config.js', 'core.js', 'api-client.js', 'oidc-client.js', 'mock-provider.js', 'operational-service.js', 'intelligence-service.js', 'accounting-service.js', 'app.js', 'app-shell.css']) {
    assert.ok(fs.existsSync(path.join(appDir, asset)), asset);
    assert.ok(html.includes(asset), asset);
  }
});

test('session begins protected and exposes every required application state', () => {
  const {S21Core} = load(['core.js']);
  const store = S21Core.createSessionStore();
  assert.equal(store.snapshot().state, 'BOOTING');
  for (const state of ['UNAUTHENTICATED', 'AUTHENTICATING', 'AUTHENTICATED', 'SESSION_EXPIRED', 'FORBIDDEN', 'NETWORK_ERROR', 'SERVER_ERROR']) {
    assert.equal(S21Core.STATES[state], state);
  }
  assert.equal(store.snapshot().profile, null);
  assert.equal(store.token(), null);
});

test('synthetic workspace is explicit and never gains a bearer token', () => {
  const context = load(['core.js', 'mock-provider.js']);
  const store = context.S21Core.createSessionStore();
  store.startSyntheticWorkspace(context.S21SyntheticProvider.loadProfile());
  assert.equal(store.snapshot().state, 'AUTHENTICATED');
  assert.equal(store.snapshot().mode, 'synthetic');
  assert.equal(store.token(), null);
  assert.match(store.snapshot().profile.user.displayName, /Exemplo/);
});

test('OIDC token remains only in the private in-memory session slot', () => {
  const {S21Core} = load(['core.js']);
  const store = S21Core.createSessionStore();
  store.establish({token: 'opaque-test-value', userProfile: {permissions: []}});
  assert.equal(store.token(), 'opaque-test-value');
  assert.equal(Object.hasOwn(store.snapshot(), 'token'), false);
  store.logout();
  assert.equal(store.token(), null);
  const sources = ['core.js', 'app.js', 'api-client.js', 'mock-provider.js'].map(read).join('\n');
  assert.doesNotMatch(sources, /localStorage|sessionStorage/);
});

test('permission presentation preserves exact segmented backend identifiers', () => {
  const {S21Core} = load(['core.js']);
  assert.equal(S21Core.hasPermission(['privacy.dsr.search'], ['privacy.dsr.search']), true);
  assert.equal(S21Core.hasPermission(['privacy.dsr.search'], ['privacy']), false);
  const items = [{id: 'a', permissions: ['company.read']}, {id: 'b', permissions: ['identity.manage']}];
  assert.deepEqual(S21Core.allowedNavigation(items, ['company.read']).map((item) => item.id), ['a']);
});

test('API client uses only the real identity context route and bearer in memory', async () => {
  let request;
  const context = load(['api-client.js'], {Headers, crypto: {randomUUID: () => '00000000-0000-4000-8000-000000000000'}});
  const client = context.S21ApiClient.createApiClient({
    baseUrl: '/api/v1', getAccessToken: () => 'opaque-test-value', onAuthenticationFailure() {},
    fetchImpl: async (url, options) => { request = {url, options}; return {status: 200, ok: true, json: async () => ({permission: 'company.read'})}; },
  });
  const response = await client.identityContext('synthetic-company');
  assert.equal(request.url, '/api/v1/identity/context?company_id=synthetic-company');
  assert.equal(request.options.headers.get('Authorization'), 'Bearer opaque-test-value');
  assert.equal(request.options.credentials, 'omit');
  assert.equal(response.permission, 'company.read');
});

test('401 expires the frontend session and 403 remains a safe generic error', async () => {
  const context = load(['api-client.js'], {Headers});
  let expired = false;
  const make = (status) => context.S21ApiClient.createApiClient({
    baseUrl: '/api/v1', getAccessToken: () => 'opaque-test-value', onAuthenticationFailure: () => { expired = true; },
    fetchImpl: async () => ({status, ok: false}),
  });
  await assert.rejects(make(401).request('/protected'), (error) => error.code === 'SESSION_EXPIRED');
  assert.equal(expired, true);
  await assert.rejects(make(403).request('/protected'), (error) => error.code === 'FORBIDDEN' && error.message === 'FORBIDDEN');
});

test('login UI delegates credentials to the IdP', () => {
  const source = read('app.js');
  assert.doesNotMatch(source, /type="email"/);
  assert.doesNotMatch(source, /type="password"/);
  assert.match(source, /data-action="begin-login"/);
  assert.match(source, /credenciais são tratadas somente pelo provedor/);
  assert.doesNotMatch(source, /console\.|\.value[^\n]*(password|senha)|(password|senha)[^\n]*\.value/i);
});

test('raw network calls are centralized and public configuration contains no secret', () => {
  for (const file of ['app.js', 'core.js', 'config.js', 'mock-provider.js']) assert.doesNotMatch(read(file), /\bfetch\s*\(/, file);
  const config = read('config.js');
  assert.match(config, /apiBaseUrl: '\/api\/v1'/);
  assert.match(config, /dataMode: 'synthetic'/);
  assert.doesNotMatch(config, /(clientSecret|privateKey|databaseUrl|password|token)\s*:/i);
});

test('OIDC adapter uses authorization code PKCE and stores only the transaction', () => {
  const source = read('oidc-client.js');
  assert.match(source, /response_type', 'code'/);
  assert.match(source, /code_challenge_method', 'S256'/);
  assert.match(source, /parameters\.get\('state'\) !== transaction\.state/);
  assert.match(source, /transactionStore\.removeItem\(TRANSACTION_KEY\)/);
  assert.doesNotMatch(source, /localStorage|refresh_token|console\./);
});

test('shell includes authorized navigation, safe states, logout, context and responsive accessibility', () => {
  const js = read('app.js');
  const css = read('app-shell.css');
  for (const label of ['Minha Visão', 'Operação', 'Fiscal', 'Financeiro', 'Contábil', 'Clientes', 'Obrigações', 'Governança', 'Administração']) assert.ok(js.includes(label), label);
  for (const phrase of ['Você não possui permissão', 'Sua sessão expirou', 'Não foi possível conectar', 'Sair do aplicativo']) assert.ok(js.includes(phrase), phrase);
  assert.match(js, /aria-label="Navegação principal"/);
  assert.match(js, /aria-expanded/);
  assert.match(css, /@media\(max-width:800px\)/);
  assert.match(css, /drawer-backdrop\.open/);
});

test('original prototype remains present as a separate historical reference', () => {
  assert.ok(fs.existsSync(path.join(appDir, 'prototype.html')));
  assert.ok(fs.existsSync(path.join(appDir, 'foundation.js')));
  assert.ok(fs.existsSync(path.join(appDir, 'mocks.js')));
});
