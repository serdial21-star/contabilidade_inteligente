(function defineSyntheticProvider(root) {
  'use strict';

  const profile = Object.freeze({
    user: Object.freeze({id: 'synthetic-user', displayName: 'Ana Exemplo', roleLabel: 'Profissional fictícia'}),
    tenant: Object.freeze({id: 'synthetic-tenant', name: 'Escritório Demonstração'}),
    companies: Object.freeze([
      Object.freeze({
        id: 'synthetic-company-a', name: 'Empresa Horizonte · Matriz',
        permissions: Object.freeze(['company.read', 'company.manage', 'journal.read', 'journal.propose', 'journal.approve', 'reconciliation.manage', 'audit.read', 'catalog.manage', 'catalog.review']),
      }),
      Object.freeze({
        id: 'synthetic-company-b', name: 'Comercial Aurora · Matriz',
        permissions: Object.freeze(['company.read', 'journal.read', 'audit.read']),
      }),
    ]),
    permissions: Object.freeze([]),
  });

  const snapshots = Object.freeze({
    'synthetic-company-a': Object.freeze({
      received: 18, processed: 15, reviews: 4, proposals: 7, approvals: 2,
      exceptions: Object.freeze([
        Object.freeze({title: 'NF-e · revisão humana', detail: 'Empresa Horizonte', meta: 'Recebida há 18 min'}),
        Object.freeze({title: 'Período bloqueado', detail: 'Empresa Horizonte', meta: 'Ação indisponível'}),
      ]),
      obligations: Object.freeze([{title: 'Checklist demonstrativo', detail: 'Sem agenda fiscal real', meta: 'Amanhã'}]),
      reconciliations: Object.freeze([{title: 'Extrato de demonstração', detail: 'Conferência necessária', meta: 'Hoje'}]),
      activity: Object.freeze([
        Object.freeze({title: 'Documento recebido', detail: 'Empresa Horizonte', meta: '09:10'}),
        Object.freeze({title: 'Proposta preparada', detail: 'Revisão profissional necessária', meta: '09:12'}),
        Object.freeze({title: 'Decisão humana registrada', detail: 'Cenário sintético aprovado', meta: '10:05'}),
      ]),
    }),
    'synthetic-company-b': Object.freeze({
      received: 9, processed: 8, reviews: 1, proposals: 3, approvals: 0,
      exceptions: Object.freeze([
        Object.freeze({title: 'Regra pendente', detail: 'Comercial Aurora', meta: 'Recebida há 42 min'}),
      ]),
      obligations: Object.freeze([{title: 'Conferência demonstrativa', detail: 'Sem agenda fiscal real', meta: 'Em 3 dias'}]),
      reconciliations: Object.freeze([]),
      activity: Object.freeze([
        Object.freeze({title: 'Documento processado', detail: 'Comercial Aurora', meta: '08:48'}),
        Object.freeze({title: 'Exceção identificada', detail: 'Regra pendente', meta: '09:15'}),
      ]),
    }),
  });

  const companyDetails = Object.freeze({
    'synthetic-company-a': Object.freeze({id: 'synthetic-company-a', legal_name: 'Empresa Horizonte Demonstração Ltda.', trade_name: 'Horizonte', tax_identifier: '00.000.000/0000-00', status: 'active', timezone: 'America/Sao_Paulo', currency_code: 'BRL'}),
    'synthetic-company-b': Object.freeze({id: 'synthetic-company-b', legal_name: 'Comercial Aurora Fictícia Ltda.', trade_name: 'Aurora', tax_identifier: '11.111.111/1111-11', status: 'active', timezone: 'America/Sao_Paulo', currency_code: 'BRL'}),
  });
  const documents = Object.freeze([
    Object.freeze({id: 'synthetic-document-1', company_id: 'synthetic-company-a', batch_id: 'synthetic-batch-1', filename: 'nfe-demonstracao-001.xml', media_type: 'application/xml', size_bytes: 2840, source: 'NFE55', channel: 'UPLOAD', receipt_result: 'ACCEPTED', processing_status: 'COMPLETED', error_code: null, received_at: '2026-09-14T12:10:00Z'}),
    Object.freeze({id: 'synthetic-document-2', company_id: 'synthetic-company-a', batch_id: 'synthetic-batch-2', filename: '<documento-ficticio>.ofx', media_type: 'application/x-ofx', size_bytes: 940, source: 'OFX_OPERATIONAL', channel: 'UPLOAD', receipt_result: 'DUPLICATE', processing_status: 'COMPLETED', error_code: null, received_at: '2026-09-14T11:32:00Z'}),
    Object.freeze({id: 'synthetic-document-3', company_id: 'synthetic-company-a', batch_id: 'synthetic-batch-3', filename: 'nfe-com-regra-pendente.xml', media_type: 'application/xml', size_bytes: 3012, source: 'NFE55', channel: 'UPLOAD', receipt_result: 'ACCEPTED', processing_status: 'FAILED', error_code: 'SYNTHETIC_VALIDATION', received_at: '2026-09-14T10:15:00Z'}),
    Object.freeze({id: 'synthetic-document-4', company_id: 'synthetic-company-b', batch_id: 'synthetic-batch-4', filename: 'nfe-aurora-001.xml', media_type: 'application/xml', size_bytes: 2501, source: 'NFE55', channel: 'UPLOAD', receipt_result: 'ACCEPTED', processing_status: 'COMPLETED', error_code: null, received_at: '2026-09-13T17:40:00Z'}),
    Object.freeze({id: 'synthetic-document-5', company_id: 'synthetic-company-b', batch_id: 'synthetic-batch-5', filename: 'arquivo-divergente.xml', media_type: 'application/xml', size_bytes: 2700, source: 'NFE55', channel: 'UPLOAD', receipt_result: 'ACCEPTED', processing_status: 'QUARANTINED', error_code: 'SYNTHETIC_DIVERGENCE', received_at: '2026-09-13T16:20:00Z'}),
  ]);
  const documentMetadata = new Map();
  let bankAccounts = [
    {id: 'synthetic-bank-account-1', company_id: 'synthetic-company-a', bank_code: '000', bank_name: 'Banco demonstração', branch: '0001', account_number: '00001', account_type: 'CHECKING', currency_code: 'BRL', nickname: 'Conta operacional', status: 'ACTIVE', created_at: '2026-09-01T12:00:00Z', updated_at: null},
  ];
  const enrichedDocument = (item) => Object.freeze({...item, document_number: null, description: null, observation: null, metadata_version: null, ...(documentMetadata.get(item.id) || {})});

  async function loadCompany(id) { return companyDetails[id] || null; }
  async function listDocuments(companyId, filters = {}) {
    const offset = Number(filters.offset || 0);
    const limit = Number(filters.limit || 25);
    const search = String(filters.search || '').toLocaleLowerCase('pt-BR');
    let rows = documents.filter((item) => item.company_id === companyId).map(enrichedDocument);
    if (search) rows = rows.filter((item) => [item.filename, item.document_number, item.description].some((value) => String(value || '').toLocaleLowerCase('pt-BR').includes(search)));
    if (filters.status) rows = rows.filter((item) => item.processing_status === filters.status || item.receipt_result === filters.status);
    if (filters.source) rows = rows.filter((item) => item.source === filters.source);
    if (filters.received_from) rows = rows.filter((item) => item.received_at.slice(0, 10) >= filters.received_from);
    if (filters.received_to) rows = rows.filter((item) => item.received_at.slice(0, 10) <= filters.received_to);
    return Object.freeze({items: Object.freeze(rows.slice(offset, offset + limit)), total: rows.length, offset, limit});
  }
  async function loadDocument(companyId, documentId) {
    const document = documents.find((item) => item.company_id === companyId && item.id === documentId);
    if (!document) throw Object.assign(new Error('REQUEST_FAILED'), {code: 'REQUEST_FAILED'});
    const issues = document.error_code ? [Object.freeze({id: 'synthetic-issue', code: document.error_code, severity: 'WARNING', resolution_status: 'QUARANTINED', created_at: document.received_at})] : [];
    return Object.freeze({
      document: enrichedDocument(document), issues: Object.freeze(issues),
      fiscal_document_id: fiscal.find((item) => item.company_id === companyId && item.document_receipt_id === documentId)?.id || null,
      bank_statement_id: statements.find((item) => item.company_id === companyId && item.document_receipt_id === documentId)?.id || null,
    });
  }
  async function updateDocumentMetadata(companyId, documentId, payload) {
    const item = documents.find((row) => row.company_id === companyId && row.id === documentId);
    if (!item) throw Object.assign(new Error('REQUEST_FAILED'), {code: 'REQUEST_FAILED'});
    const previous = documentMetadata.get(documentId);
    documentMetadata.set(documentId, {...payload, metadata_version: (previous?.metadata_version || 0) + 1});
    return enrichedDocument(item);
  }
  const masked = (value) => `••••${String(value || '').slice(-2)}`;
  const bankAccountView = (item) => Object.freeze({...item, branch_masked: masked(item.branch), account_masked: masked(item.account_number), branch: undefined, account_number: undefined});
  async function listBankAccounts(companyId) { return bankAccounts.filter((item) => item.company_id === companyId).map(bankAccountView); }
  async function createBankAccount(companyId, payload) {
    const item = {...payload, id: `synthetic-bank-account-${bankAccounts.length + 1}`, company_id: companyId, status: 'ACTIVE', created_at: new Date().toISOString(), updated_at: null};
    bankAccounts = [...bankAccounts, item]; return bankAccountView(item);
  }
  async function updateBankAccount(companyId, accountId, payload) {
    const index = bankAccounts.findIndex((item) => item.company_id === companyId && item.id === accountId);
    if (index < 0) throw Object.assign(new Error('REQUEST_FAILED'), {code: 'REQUEST_FAILED'});
    const clean = {...payload};
    if (!clean.branch) delete clean.branch;
    if (!clean.account_number) delete clean.account_number;
    const item = {...bankAccounts[index], ...clean, updated_at: new Date().toISOString()};
    bankAccounts = bankAccounts.map((row, rowIndex) => rowIndex === index ? item : row); return bankAccountView(item);
  }
  async function setBankAccountStatus(companyId, accountId, status) {
    const current = bankAccounts.find((item) => item.company_id === companyId && item.id === accountId);
    if (!current) throw Object.assign(new Error('REQUEST_FAILED'), {code: 'REQUEST_FAILED'});
    return updateBankAccount(companyId, accountId, {...current, status});
  }
  async function loadSummary(companyId) {
    const rows = documents.filter((item) => item.company_id === companyId);
    return Object.freeze({received: rows.length, processed: rows.filter((item) => item.processing_status === 'COMPLETED').length, attention_required: rows.filter((item) => ['FAILED', 'QUARANTINED'].includes(item.processing_status)).length});
  }
  const fiscal = Object.freeze([
    Object.freeze({id: 'synthetic-fiscal-1', company_id: 'synthetic-company-a', access_key: '00000000000000000000000000000000000000000000', model: '55', schema_version: '4.00', series: '1', document_number: '1001', operation_nature: 'Venda fictícia', issuer_tax_id: '00.000.000/0000-00', issuer_name: 'Emitente Sintético', recipient_tax_id: '11.111.111/1111-11', recipient_name: 'Empresa Horizonte Demonstração', issued_at: '2026-09-14T12:00:00Z', movement_at: '2026-09-14T12:00:00Z', products_total: '100.00', freight_total: '0.00', insurance_total: '0.00', discount_total: '0.00', other_total: '0.00', tax_total: '18.00', invoice_total: '100.00', observed_status: 'REPORTED_AUTHORIZED', protocol_status_code: '100', protocol_status_reason: 'Autorização sintética', created_at: '2026-09-14T12:10:00Z', document_receipt_id: 'synthetic-document-1'}),
    Object.freeze({id: 'synthetic-fiscal-2', company_id: 'synthetic-company-b', access_key: '11111111111111111111111111111111111111111111', model: '55', schema_version: '4.00', series: '1', document_number: '2001', operation_nature: 'Operação fictícia', issuer_tax_id: '22.222.222/2222-22', issuer_name: 'Fornecedor Demonstração', recipient_tax_id: '11.111.111/1111-11', recipient_name: 'Comercial Aurora Fictícia', issued_at: '2026-09-13T17:00:00Z', movement_at: null, products_total: '75.00', freight_total: null, insurance_total: null, discount_total: null, other_total: null, tax_total: null, invoice_total: '75.00', observed_status: 'UNVERIFIED', protocol_status_code: null, protocol_status_reason: null, created_at: '2026-09-13T17:40:00Z', document_receipt_id: 'synthetic-document-4'}),
  ]);
  const fiscalItems = Object.freeze({
    'synthetic-fiscal-1': Object.freeze([{id: 'synthetic-fiscal-item-1', sequence: 1, product_code: 'DEMO-1', description: 'Produto exclusivamente fictício', ncm: '00000000', cfop: '5102', commercial_unit: 'UN', quantity: '1.000000', unit_value: '100.0000000000', gross_total: '100.00', discount_total: null, other_total: null, included_in_total: true}]),
    'synthetic-fiscal-2': Object.freeze([]),
  });
  const statements = Object.freeze([
    Object.freeze({id: 'synthetic-statement-1', company_id: 'synthetic-company-a', bank_id: '000', branch_masked: '••••01', account_masked: '••••01', account_type: 'CHECKING', start_date: '2026-09-01', end_date: '2026-09-14', opening_balance: '100.00', closing_balance: '135.00', currency_code: 'BRL', sign_policy: 'OFX_TRNAMT_SIGN_PRESERVED_V1', imported_at: '2026-09-14T11:32:00Z', document_receipt_id: 'synthetic-document-2'}),
  ]);
  const transactions = Object.freeze({'synthetic-statement-1': Object.freeze([
    Object.freeze({id: 'synthetic-transaction-1', bank_statement_id: 'synthetic-statement-1', transaction_date: '2026-09-12', posted_date: '2026-09-12', amount: '-15.00', direction: 'DEBIT', description: 'Débito fictício', document_number: null, identity_kind: 'FITID'}),
    Object.freeze({id: 'synthetic-transaction-2', bank_statement_id: 'synthetic-statement-1', transaction_date: '2026-09-13', posted_date: '2026-09-13', amount: '50.00', direction: 'CREDIT', description: 'Crédito fictício', document_number: null, identity_kind: 'FITID'}),
  ])});
  let syntheticProposalStatus = 'PENDING_APPROVAL';
  const syntheticRule = Object.freeze({
    id: 'synthetic-rule-version-1', name: 'Regra NF-e exclusivamente fictícia', scope: 'NFE',
    priority: 10, status: 'PUBLISHED', automation_level: 'SUGGEST',
    conditions: Object.freeze([{field: 'model', operator: 'EQ', value: '55'}]),
    debit_account_version_id: 'synthetic-account-debit', debit_account_code: '1.1', debit_account_name: 'Conta débito fictícia',
    credit_account_version_id: 'synthetic-account-credit', credit_account_code: '3.1', credit_account_name: 'Conta crédito fictícia',
  });
  const syntheticAccounts = Object.freeze([
    Object.freeze({id: 'synthetic-account-debit', code: '1.1', name: 'Conta débito fictícia', nature: 'ASSET', normal_balance: 'DEBIT', is_synthetic: false, is_postable: true, status: 'PUBLISHED'}),
    Object.freeze({id: 'synthetic-account-credit', code: '3.1', name: 'Conta crédito fictícia', nature: 'REVENUE', normal_balance: 'CREDIT', is_synthetic: false, is_postable: true, status: 'PUBLISHED'}),
  ]);
  function syntheticProposalSummary(companyId) {
    return Object.freeze({
      journey_id: 'synthetic-journey-1', company_id: companyId, version: syntheticProposalStatus === 'PENDING_APPROVAL' ? 8 : 10,
      status: syntheticProposalStatus, proposal_id: 'synthetic-proposal-1', revision_id: 'synthetic-revision-1',
      revision_hash: 'synthetic-revision-hash', accounting_date: '2026-09-14', source_type: 'FiscalDocument',
      source_id: 'synthetic-fiscal-1', source_document_receipt_id: 'synthetic-document-1',
      document_number: '1001', debit_accounts: ['1.1 · Conta débito fictícia'], credit_accounts: ['3.1 · Conta crédito fictícia'],
      rule_version_id: syntheticRule.id, rule_name: syntheticRule.name,
      total_debit: '100.00', total_credit: '100.00', balanced: true, validation_status: 'VALID',
      proposer_id: 'synthetic-proposer', approval_role: 'CONTADOR', responsible_role: 'CONTADOR',
      expires_at: '2026-09-30T23:59:59Z', decision_actor_id: syntheticProposalStatus === 'PENDING_APPROVAL' ? null : 'synthetic-accountant',
      decided_at: syntheticProposalStatus === 'PENDING_APPROVAL' ? null : '2026-09-15T13:00:00Z',
    });
  }
  async function listAccountingProposals(companyId, filters = {}) {
    let rows = companyId === 'synthetic-company-a' ? [syntheticProposalSummary(companyId)] : [];
    if (filters.status) rows = rows.filter((item) => item.status === filters.status);
    if (filters.account) rows = rows.filter((item) => [...item.debit_accounts, ...item.credit_accounts].join(' ').toLocaleLowerCase('pt-BR').includes(String(filters.account).toLocaleLowerCase('pt-BR')));
    if (filters.source) rows = rows.filter((item) => item.source_type === filters.source);
    if (filters.document) rows = rows.filter((item) => String(item.document_number || '').includes(filters.document));
    if (filters.rule) rows = rows.filter((item) => String(item.rule_name || '').toLocaleLowerCase('pt-BR').includes(String(filters.rule).toLocaleLowerCase('pt-BR')));
    if (filters.created_from) rows = rows.filter((item) => item.accounting_date >= filters.created_from);
    if (filters.created_to) rows = rows.filter((item) => item.accounting_date <= filters.created_to);
    const offset = Number(filters.offset || 0), limit = Number(filters.limit || 10);
    return {items: rows.slice(offset, offset + limit), total: rows.length, offset, limit};
  }
  async function accountingProposal(companyId, id) {
    if (companyId !== 'synthetic-company-a' || id !== 'synthetic-journey-1') throw Object.assign(new Error('REQUEST_FAILED'), {code: 'REQUEST_FAILED'});
    return {
      summary: syntheticProposalSummary(companyId), rule: syntheticRule,
      lines: [
        {account_version_id: 'synthetic-account-debit', account_code: '1.1', account_name: 'Conta débito fictícia', debit: '100.00', credit: '0.00'},
        {account_version_id: 'synthetic-account-credit', account_code: '3.1', account_name: 'Conta crédito fictícia', debit: '0.00', credit: '100.00'},
      ],
      sources: [{source_type: 'FiscalDocument', source_id: 'synthetic-fiscal-1', document_receipt_id: 'synthetic-document-1', document_number: '1001', issuer_name: 'Emitente Sintético', issued_at: '2026-09-14T12:00:00Z', amount: '100.00'}],
      active_locks: [],
    };
  }
  async function syntheticAccountingCatalog(companyId) {
    if (companyId !== 'synthetic-company-a') throw Object.assign(new Error('REQUEST_FAILED'), {code: 'REQUEST_FAILED'});
    return {version_id: 'synthetic-catalog-version-1', version_no: 1, valid_from: '2026-01-01', valid_to: null, decimal_places: 2, amount_field: 'invoice_total', rules: [syntheticRule], accounts: syntheticAccounts, mappings: [{id: 'synthetic-mapping-1', key: 'synthetic-map', priority: 10, external_code: 'DEMO', history_contains: null, dimension_code: null, canonical_entity: 'FiscalDocument', target_account_version_id: 'synthetic-account-debit', target_account_code: '1.1', target_account_name: 'Conta débito fictícia'}]};
  }
  async function syntheticAccountingRule(companyId, id) {
    const catalog = await syntheticAccountingCatalog(companyId);
    const rule = catalog.rules.find((item) => item.id === id);
    if (!rule) throw Object.assign(new Error('REQUEST_FAILED'), {code: 'REQUEST_FAILED'});
    return rule;
  }
  async function syntheticDecision(companyId, id, decision) {
    if (companyId !== 'synthetic-company-a' || id !== 'synthetic-journey-1' || syntheticProposalStatus !== 'PENDING_APPROVAL') throw Object.assign(new Error('REQUEST_FAILED'), {code: 'OPERATION_CONFLICT'});
    syntheticProposalStatus = decision;
    return {journey_id: id, version: 10, status: decision, decision_id: 'synthetic-decision-1', synthetic: true};
  }
  async function syntheticProposalActivity(companyId, id) {
    if (companyId !== 'synthetic-company-a' || id !== 'synthetic-journey-1') throw Object.assign(new Error('REQUEST_FAILED'), {code: 'REQUEST_FAILED'});
    return [{id: 'synthetic-audit-1', actor_id: 'synthetic-proposer', origin: 'HUMAN', module: 'workflow', action: 'accounting_proposal.created', subject_type: 'NFeJourney', subject_id: id, subject_version: 3, correlation_id: 'synthetic-correlation', occurred_at: '2026-09-14T12:10:00Z', integrity_valid: true}];
  }
  async function decisionLine(companyId, rootType, id) {
    const valid = profile.companies.some((company) => company.id === companyId);
    if (!valid) throw Object.assign(new Error('REQUEST_FAILED'), {code: 'REQUEST_FAILED'});
    const approved = rootType === 'ACCOUNTING_PROPOSAL' && syntheticProposalStatus === 'APPROVED';
    return Object.freeze({
      root_type: rootType, root_id: id, root_title: 'Rastreabilidade sintética',
      root_status: approved ? 'APPROVED' : 'PROCESSED', completeness: 'PARTIAL',
      data_gaps: Object.freeze(['DISTINCT_REVIEW_ACTION_NOT_AVAILABLE']),
      events: Object.freeze([
        Object.freeze({sequence: 1, occurred_at: '2026-09-14T12:10:00Z', category: 'RECEIPT', actor_kind: 'PROFESSIONAL_ACTION', actor_display_name: 'Ana Exemplo', title: 'Documento recebido', description: 'Evidência exclusivamente sintética.', evidence_kind: 'AUDIT_EVENT', integrity_valid: true}),
        Object.freeze({sequence: 2, occurred_at: '2026-09-14T12:11:00Z', category: 'PROCESSING', actor_kind: 'AUTOMATED', actor_display_name: 'Automação', title: 'Processamento executado', description: 'Cenário demonstrativo sem dado real.', evidence_kind: 'AUDIT_EVENT', integrity_valid: true}),
        ...(rootType === 'ACCOUNTING_PROPOSAL' ? [Object.freeze({sequence: 3, occurred_at: '2026-09-14T12:12:00Z', category: approved ? 'APPROVAL' : 'PROPOSAL', actor_kind: approved ? 'PROFESSIONAL_ACTION' : 'AUTOMATED', actor_display_name: approved ? 'Ana Exemplo' : 'Automação', title: approved ? 'Proposta aprovada' : 'Proposta contábil criada', description: 'Decisão ou proposta do cenário sintético.', evidence_kind: 'AUDIT_EVENT', integrity_valid: true})] : []),
      ]),
    });
  }
  let syntheticItemClassificationStatus = 'REVIEW_REQUIRED';
  function syntheticItemClassificationSummary() {
    return Object.freeze({
      id: 'synthetic-item-classification-1', fiscal_document_id: 'synthetic-fiscal-1',
      fiscal_item_id: 'synthetic-fiscal-item-1', item_description: 'Produto exclusivamente fictício',
      selected_intent: 'PURCHASE_USE_CONSUMPTION', classification_category: 'OFFICE_SUPPLY',
      confidence_level: syntheticItemClassificationStatus === 'REVIEWED' ? 'HIGH' : 'MEDIUM',
      status: syntheticItemClassificationStatus,
      version: syntheticItemClassificationStatus === 'REVIEWED' ? 2 : 1,
      created_at: '2026-09-14T12:11:00Z',
    });
  }
  async function listItemClassifications(companyId, filters = {}) {
    const rows = companyId === 'synthetic-company-a' && syntheticItemClassificationStatus !== 'REVIEWED'
      ? [syntheticItemClassificationSummary()] : [];
    const offset = Number(filters.offset || 0), limit = Number(filters.limit || 10);
    return {items: rows.slice(offset, offset + limit), total: rows.length, offset, limit};
  }
  async function syntheticItemClassification(companyId, id) {
    if (companyId !== 'synthetic-company-a' || id !== 'synthetic-item-classification-1') throw Object.assign(new Error('REQUEST_FAILED'), {code: 'REQUEST_FAILED'});
    return {
      summary: syntheticItemClassificationSummary(),
      evidence: [{kind: 'DESCRIPTION_MATCH', intent: 'PURCHASE_USE_CONSUMPTION', weight: 45, explanation: 'Categoria determinística de material de uso/consumo exclusivamente sintética.', reference_id: null}],
      alternatives: [], document_number: '1001', issuer_name: 'Emitente Sintético',
    };
  }
  async function syntheticItemClassificationDecision(companyId, id, decision) {
    if (companyId !== 'synthetic-company-a' || id !== 'synthetic-item-classification-1' || syntheticItemClassificationStatus === 'REVIEWED') throw Object.assign(new Error('REQUEST_FAILED'), {code: 'OPERATION_CONFLICT'});
    syntheticItemClassificationStatus = 'REVIEWED';
    return {...syntheticItemClassificationSummary(), selected_intent: decision.finalIntent};
  }
  async function listFiscal(companyId, filters = {}) {
    let rows = fiscal.filter((item) => item.company_id === companyId);
    const search = String(filters.search || '').toLocaleLowerCase('pt-BR');
    if (search) rows = rows.filter((item) => [item.access_key, item.document_number, item.issuer_name].some((value) => String(value || '').toLocaleLowerCase('pt-BR').includes(search)));
    if (filters.status) rows = rows.filter((item) => item.observed_status === filters.status);
    const offset = Number(filters.offset || 0), limit = Number(filters.limit || 10);
    return {items: rows.slice(offset, offset + limit), total: rows.length, offset, limit};
  }
  async function fiscalDetail(companyId, id) {
    const document = fiscal.find((item) => item.company_id === companyId && item.id === id);
    if (!document) throw Object.assign(new Error('REQUEST_FAILED'), {code: 'REQUEST_FAILED'});
    const items = fiscalItems[id] || [];
    return {document, items, item_count: items.length, tax_totals: [{tax_type: 'ICMS', amount: '18.00'}]};
  }
  async function listStatements(companyId, filters = {}) {
    const rows = statements.filter((item) => item.company_id === companyId);
    const offset = Number(filters.offset || 0), limit = Number(filters.limit || 10);
    return {items: rows.slice(offset, offset + limit), total: rows.length, offset, limit};
  }
  async function statementDetail(companyId, id, filters = {}) {
    const statement = statements.find((item) => item.company_id === companyId && item.id === id);
    if (!statement) throw Object.assign(new Error('REQUEST_FAILED'), {code: 'REQUEST_FAILED'});
    let rows = [...(transactions[id] || [])];
    if (filters.direction) rows = rows.filter((item) => item.direction === filters.direction);
    if (filters.search) rows = rows.filter((item) => String(item.description || '').toLocaleLowerCase('pt-BR').includes(String(filters.search).toLocaleLowerCase('pt-BR')));
    const offset = Number(filters.offset || 0), limit = Number(filters.limit || 25);
    return {statement, transactions: {items: rows.slice(offset, offset + limit), total: rows.length, offset, limit}};
  }
  async function syntheticImport(file, kind) {
    const name = String(file?.name || '').toLocaleLowerCase('pt-BR');
    return {resource_id: `synthetic-${kind}-result`, resource_kind: kind === 'nfe' ? 'JOURNEY' : 'BATCH', status: name.includes('duplic') ? 'IDEMPOTENT_REDELIVERY' : name.includes('inval') ? 'QUARANTINED' : 'IMPORTED', duplicate_items: name.includes('duplic') ? 1 : 0, synthetic: true};
  }

  const sum = (rows, field) => rows.reduce((total, row) => total + row[field], 0);
  const collect = (rows, field) => rows.flatMap((row) => row[field]);
  const result = (value, note, items = []) => Object.freeze({
    state: items.length || Number(value) > 0 ? 'READY' : 'EMPTY',
    value: String(value), note, items: Object.freeze(items.slice(0, 5)),
    updatedAt: '2026-09-14T16:20:00-03:00',
  });

  async function loadWidget(widgetId, context) {
    const rows = context.companyIds.map((id) => snapshots[id]).filter(Boolean);
    const companyCount = rows.length;
    if (widgetId === 'W001') return result(sum(rows, 'received'), 'Recebidos no cenário sintético atual');
    if (widgetId === 'W002') return result(sum(rows, 'processed'), 'Preparação concluída; não significa aprovação');
    if (widgetId === 'W003') return result(sum(rows, 'reviews'), 'Conferências que exigem atenção');
    if (widgetId === 'W004') return result(collect(rows, 'exceptions').length, 'Prioridades explicadas, sem pontuação de IA', collect(rows, 'exceptions'));
    if (widgetId === 'W005') return result(sum(rows, 'proposals'), 'Propostas sem escrituração oficial');
    if (widgetId === 'W006') return result(sum(rows, 'approvals'), 'Somente quando há permissão de aprovação');
    if (widgetId === 'W007') {
      const items = context.companyIds.map((id) => snapshots[id] && ({
        title: profile.companies.find((company) => company.id === id)?.name || 'Empresa autorizada',
        detail: snapshots[id].exceptions.length ? `${snapshots[id].exceptions.length} pendência(s)` : 'Sem pendências',
        meta: 'Contexto autorizado',
      })).filter(Boolean);
      return result(items.filter((item) => !item.detail.startsWith('Sem')).length, companyCount === 1 ? 'Empresa atual' : 'Somente empresas autorizadas', items);
    }
    if (widgetId === 'W008') return result(collect(rows, 'obligations').length, 'Agenda exclusivamente fictícia', collect(rows, 'obligations'));
    if (widgetId === 'W009') return result(collect(rows, 'reconciliations').length, 'Prévia conceitual; integração operacional adiada', collect(rows, 'reconciliations'));
    if (widgetId === 'W010') return result('', 'Projeção sintética sem payload bruto de auditoria', collect(rows, 'activity'));
    return Object.freeze({state: 'UNAVAILABLE', value: '', note: 'Indicador indisponível.', items: Object.freeze([])});
  }

  root.S21SyntheticProvider = Object.freeze({
    loadProfile: () => profile, loadWidget, company: loadCompany,
    documents: listDocuments, document: loadDocument, summary: loadSummary, updateDocumentMetadata,
    bankAccounts: listBankAccounts, createBankAccount, updateBankAccount, setBankAccountStatus,
    fiscalDocuments: listFiscal, fiscalDocument: fiscalDetail,
    bankStatements: listStatements, bankStatement: statementDetail,
    importNfe: (companyId, file) => syntheticImport(file, 'nfe'),
    importOfx: (companyId, file) => syntheticImport(file, 'ofx'),
    accountingProposals: listAccountingProposals, accountingProposal,
    proposalActivity: syntheticProposalActivity,
    accountingCatalog: syntheticAccountingCatalog, accountingRule: syntheticAccountingRule,
    decideProposal: syntheticDecision,
    decisionLine,
    itemClassifications: listItemClassifications, itemClassification: syntheticItemClassification,
    decideItemClassification: syntheticItemClassificationDecision,
  });
}(globalThis));
