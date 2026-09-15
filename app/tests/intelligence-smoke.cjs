/* Focused Phase 07 service tests. Run with Node 18+. */
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const appDir = path.resolve(__dirname, '..');
const context = {};
context.globalThis = context;
vm.createContext(context);
for (const file of ['mock-provider.js', 'intelligence-service.js']) {
  vm.runInContext(fs.readFileSync(path.join(appDir, file), 'utf8'), context, {filename: file});
}

const service = context.S21Intelligence.createIntelligenceService({
  dataMode: 'synthetic', apiClient: {}, syntheticProvider: context.S21SyntheticProvider,
});

test('fiscal projection is company scoped and exposes safe structured items', async () => {
  const page = await service.fiscalDocuments('synthetic-company-a', {search: 'Emitente', limit: 10});
  assert.equal(page.total, 1);
  assert.equal(page.items[0].model, '55');
  assert.equal(page.items[0].document_receipt_id, 'synthetic-document-1');
  const detail = await service.fiscalDocument('synthetic-company-a', page.items[0].id);
  assert.equal(detail.items.length, 1);
  assert.equal(detail.items[0].gross_total, '100.00');
  await assert.rejects(service.fiscalDocument('synthetic-company-b', page.items[0].id));
});

test('financial projection preserves signs, labels and company isolation', async () => {
  const page = await service.bankStatements('synthetic-company-a', {limit: 10});
  assert.equal(page.total, 1);
  assert.match(page.items[0].account_masked, /•/);
  const detail = await service.bankStatement('synthetic-company-a', page.items[0].id, {});
  assert.deepEqual(detail.transactions.items.map((item) => item.direction), ['DEBIT', 'CREDIT']);
  assert.equal(detail.transactions.items[0].amount, '-15.00');
  assert.equal(detail.transactions.items[1].amount, '50.00');
  await assert.rejects(service.bankStatement('synthetic-company-b', page.items[0].id, {}));
});

test('synthetic import feedback is explicit and represents duplicate and quarantine states', async () => {
  const duplicate = await service.importNfe('synthetic-company-a', {name: 'duplicada.xml'});
  const quarantine = await service.importOfx('synthetic-company-a', {name: 'invalido.ofx'});
  assert.equal(duplicate.status, 'IDEMPOTENT_REDELIVERY');
  assert.equal(duplicate.synthetic, true);
  assert.equal(quarantine.status, 'QUARANTINED');
  assert.equal(quarantine.synthetic, true);
});
