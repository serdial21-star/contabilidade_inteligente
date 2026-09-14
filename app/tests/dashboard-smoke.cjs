/* Focused Phase 05 service tests. Run with Node 18+: node --test app/tests/dashboard-smoke.cjs */
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const source = fs.readFileSync(path.resolve(__dirname, '..', 'dashboard-service.js'), 'utf8');
function load(storage) {
  const context = {localStorage: storage};
  context.globalThis = context;
  vm.createContext(context);
  vm.runInContext(source, context, {filename: 'dashboard-service.js'});
  return context.S21Dashboard;
}

test('catalog exposes ten widgets and filters by exact permission', () => {
  const dashboard = load();
  const service = dashboard.createDashboardService({dataMode: 'synthetic', syntheticProvider: {loadWidget() {}}, apiClient: {}});
  assert.equal(service.widgets.length, 10);
  assert.deepEqual(
    service.authorizedCatalog(['audit.read']).map((widget) => widget.id),
    ['W010'],
  );
  assert.equal(service.authorizedCatalog(['audit']).length, 0);
});

test('preferences retain only authorized presentation fields', () => {
  let stored = '';
  const storage = {getItem: () => stored, setItem: (_, value) => { stored = value; }, removeItem: () => { stored = ''; }};
  const dashboard = load(storage);
  const service = dashboard.createDashboardService({dataMode: 'synthetic', syntheticProvider: {loadWidget() {}}, apiClient: {}, storage});
  const saved = service.savePreferences({preset: 'Minha Visão', widgets: ['W001', 'W006', 'UNKNOWN'], wide: ['W001', 'W006'], token: 'never-store'}, ['company.read']);
  assert.deepEqual([...saved.widgets], ['W001']);
  assert.deepEqual([...saved.wide], ['W001']);
  assert.deepEqual(Object.keys(JSON.parse(stored)).sort(), ['preset', 'widgets', 'wide']);
  assert.equal(stored.includes('never-store'), false);
});

test('one widget failure does not fail the dashboard', async () => {
  const dashboard = load();
  const provider = {loadWidget: async (id) => {
    if (id === 'W002') throw new Error('temporary');
    return {state: 'READY', value: '1', note: 'ok', items: []};
  }};
  const service = dashboard.createDashboardService({dataMode: 'synthetic', syntheticProvider: provider, apiClient: {}});
  const result = await service.loadSummary(['W001', 'W002'], {permissions: ['company.read'], companyIds: ['a']});
  assert.equal(result.W001.state, 'READY');
  assert.equal(result.W002.state, 'ERROR');
});

test('unauthorized widget is forbidden before provider access', async () => {
  const dashboard = load();
  let called = false;
  const service = dashboard.createDashboardService({dataMode: 'synthetic', syntheticProvider: {loadWidget: async () => { called = true; }}, apiClient: {}});
  const result = await service.loadWidget('W006', {permissions: ['company.read'], companyIds: ['a']});
  assert.equal(result.state, 'FORBIDDEN');
  assert.equal(called, false);
});
