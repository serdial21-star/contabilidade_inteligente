/* Focused Phase 06 service tests. Run with Node 18+. */
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const appDir = path.resolve(__dirname, '..');
const context = {};
context.globalThis = context;
vm.createContext(context);
for (const file of ['mock-provider.js', 'operational-service.js']) {
  vm.runInContext(fs.readFileSync(path.join(appDir, file), 'utf8'), context, {filename: file});
}

test('company search operates only on the already authorized profile projection', () => {
  const service = context.S21Operational.createOperationalService({dataMode: 'synthetic', apiClient: {}, syntheticProvider: context.S21SyntheticProvider});
  const profile = context.S21SyntheticProvider.loadProfile();
  assert.deepEqual(service.listCompanies(profile, 'Aurora').map((item) => item.id), ['synthetic-company-b']);
  assert.equal(service.listCompanies(profile, '').length, 2);
});

test('document filters, pagination and hostile filenames remain plain data', async () => {
  const service = context.S21Operational.createOperationalService({dataMode: 'synthetic', apiClient: {}, syntheticProvider: context.S21SyntheticProvider});
  const page = await service.documents('synthetic-company-a', {search: '<documento', limit: 10, offset: 0});
  assert.equal(page.total, 1);
  assert.equal(page.items[0].filename, '<documento-ficticio>.ofx');
  assert.equal(service.statusLabel(page.items[0].processing_status), 'Processado');
  const detail = await service.document('synthetic-company-a', page.items[0].id);
  assert.equal(detail.document.company_id, 'synthetic-company-a');
});

test('unknown document is not returned from another company scope', async () => {
  const service = context.S21Operational.createOperationalService({dataMode: 'synthetic', apiClient: {}, syntheticProvider: context.S21SyntheticProvider});
  await assert.rejects(service.document('synthetic-company-b', 'synthetic-document-1'));
});
