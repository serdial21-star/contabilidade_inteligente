/* Focused Phase 08 service tests. Run with Node 18+. */
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const appDir = path.resolve(__dirname, '..');
const context = {};
context.globalThis = context;
vm.createContext(context);
for (const file of ['mock-provider.js', 'accounting-service.js']) {
  vm.runInContext(fs.readFileSync(path.join(appDir, file), 'utf8'), context, {filename: file});
}
const service = context.S21Accounting.createAccountingService({
  dataMode: 'synthetic', apiClient: {}, syntheticProvider: context.S21SyntheticProvider,
});

test('proposal is company scoped, balanced and traceable', async () => {
  const page = await service.accountingProposals('synthetic-company-a', {status: 'PENDING_APPROVAL'});
  assert.equal(page.total, 1);
  assert.equal(page.items[0].balanced, true);
  const detail = await service.accountingProposal('synthetic-company-a', page.items[0].journey_id);
  assert.equal(detail.lines.length, 2);
  assert.equal(detail.sources[0].document_receipt_id, 'synthetic-document-1');
  await assert.rejects(service.accountingProposal('synthetic-company-b', page.items[0].journey_id));
});

test('published rule preserves exact accounts and conditions', async () => {
  const catalog = await service.accountingCatalog('synthetic-company-a');
  const rule = await service.accountingRule('synthetic-company-a', catalog.rules[0].id);
  assert.equal(rule.conditions[0].value, '55');
  assert.equal(rule.debit_account_code, '1.1');
  assert.equal(rule.credit_account_code, '3.1');
});
