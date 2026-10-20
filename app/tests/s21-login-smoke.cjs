/* T-0012: login único S21 (ADR 0025 do Sistema C). Sem navegador; fetch falso. Run with Node 18+. */
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const appDir = path.resolve(__dirname, '..');
const read = (file) => fs.readFileSync(path.join(appDir, file), 'utf8');

function load(fetchImpl) {
  const context = {atob: (value) => Buffer.from(value, 'base64').toString('binary')};
  context.globalThis = context;
  vm.createContext(context);
  vm.runInContext(read('s21-login.js'), context, {filename: 's21-login.js'});
  return context.S21Login.createS21LoginClient({apiBaseUrl: '/api/v1', fetchImpl});
}

const reply = (status, body) => ({ok: status >= 200 && status < 300, status, json: async () => body});
const token = (claims) => `h.${Buffer.from(JSON.stringify(claims)).toString('base64url')}.s`;

function fakeServer(overrides = {}) {
  const calls = [];
  const routes = {
    '/api/v1/identity/login-config': () => reply(200, {s21: {url: 'https://login.example.test', publishable_key: 'chave-publica'}}),
    'https://login.example.test/auth/v1/token?grant_type=password': () => reply(200, {
      access_token: 'aal1', refresh_token: 'r1', user: {factors: [{id: 'f1', factor_type: 'totp', status: 'verified'}]}}),
    'https://login.example.test/auth/v1/factors/f1/challenge': () => reply(200, {id: 'c1'}),
    'https://login.example.test/auth/v1/factors/f1/verify': () => reply(200, {access_token: 'aal2', refresh_token: 'r2'}),
    'https://login.example.test/auth/v1/token?grant_type=refresh_token': () => reply(200, {access_token: 'aal2-b', refresh_token: 'r3'}),
    'https://login.example.test/auth/v1/logout?scope=local': () => reply(204, null),
    ...overrides,
  };
  const fetchImpl = async (url, options = {}) => {
    calls.push({url, options});
    const handler = routes[url];
    if (!handler) throw new Error(`unexpected ${url}`);
    return handler(options);
  };
  return {calls, fetchImpl};
}

test('entra com e-mail, senha e código; renova e sai', async () => {
  const server = fakeServer();
  const client = load(server.fetchImpl);
  assert.equal(await client.load(), true);
  await client.signIn('pessoa@example.test', 'senha-ficticia');
  assert.equal(await client.verifyCode('123456'), 'aal2');
  assert.equal(await client.renew(), 'aal2-b');
  const verify = server.calls.find((call) => call.url.endsWith('/factors/f1/verify'));
  assert.equal(verify.options.headers.Authorization, 'Bearer aal1');
  assert.deepEqual(JSON.parse(verify.options.body), {challenge_id: 'c1', code: '123456'});
  assert.ok(server.calls.slice(1).every((call) => call.options.headers.apikey === 'chave-publica' && call.options.credentials === 'omit'));
  await client.logout();
  await assert.rejects(client.renew(), {code: 'NOT_STARTED'});
});

test('sem código do celular cadastrado, não entra', async () => {
  const client = load(fakeServer({
    'https://login.example.test/auth/v1/token?grant_type=password': () => reply(200, {access_token: 'a', refresh_token: 'r', user: {factors: []}}),
  }).fetchImpl);
  await client.load();
  await assert.rejects(client.signIn('p@example.test', 's'), {code: 'NO_CODE'});
  await assert.rejects(client.verifyCode('123456'), {code: 'NOT_STARTED'});
});

test('senha errada, excesso de tentativas e servidor sem configuração', async () => {
  let client = load(fakeServer({'https://login.example.test/auth/v1/token?grant_type=password': () => reply(400, {})}).fetchImpl);
  await client.load();
  await assert.rejects(client.signIn('p@example.test', 'x'), {code: 'REJECTED'});
  client = load(fakeServer({'https://login.example.test/auth/v1/token?grant_type=password': () => reply(429, {})}).fetchImpl);
  await client.load();
  await assert.rejects(client.signIn('p@example.test', 'x'), {code: 'RATE_LIMITED'});
  client = load(fakeServer({'/api/v1/identity/login-config': () => reply(200, {s21: null})}).fetchImpl);
  assert.equal(await client.load(), false);
  assert.equal(client.isConfigured(), false);
  client = load(fakeServer({'/api/v1/identity/login-config': () => reply(200, {s21: {url: 'http://inseguro.example.test', publishable_key: 'k'}})}).fetchImpl);
  assert.equal(await client.load(), false);
});

test('tempo restante lido do passe', () => {
  const client = load(fakeServer().fetchImpl);
  assert.equal(client.secondsLeft(token({exp: 1000}), 400_000), 600);
  assert.equal(client.secondsLeft('lixo'), 0);
});

test('nada de armazenamento do navegador, registro ou passe na URL', () => {
  const source = read('s21-login.js');
  assert.doesNotMatch(source, /localStorage|sessionStorage|console\.|indexedDB|document\.cookie/);
  const html = read('index.html');
  assert.match(html, /connect-src 'self' https:\/\/bmpzxbihsvflqamdsjsp\.supabase\.co;/);
  assert.ok(html.indexOf('s21-login.js') < html.indexOf('app.js'));
});
