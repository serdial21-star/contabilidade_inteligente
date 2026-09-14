(function defineSyntheticProvider(root) {
  'use strict';
  const profile = Object.freeze({
    user: Object.freeze({id: 'synthetic-user', displayName: 'Ana Exemplo', roleLabel: 'Profissional fictícia'}),
    tenant: Object.freeze({id: 'synthetic-tenant', name: 'Escritório Demonstração'}),
    companies: Object.freeze([
      Object.freeze({id: 'synthetic-company-a', name: 'Empresa Horizonte · Matriz'}),
      Object.freeze({id: 'synthetic-company-b', name: 'Comercial Aurora · Matriz'}),
    ]),
    permissions: Object.freeze(['company.read', 'journal.read', 'reconciliation.manage', 'audit.read']),
  });
  const dashboard = Object.freeze({
    metrics: Object.freeze([
      Object.freeze({label: 'Documentos recebidos', value: '24', note: 'Conjunto sintético'}),
      Object.freeze({label: 'Aguardando revisão', value: '7', note: 'Decisão profissional'}),
      Object.freeze({label: 'Com pendências', value: '3', note: 'Atenção necessária'}),
    ]),
    queue: Object.freeze([
      Object.freeze({id: 'DOC-001', type: 'NF-e', reason: 'Revisão humana', priority: 'Alta'}),
      Object.freeze({id: 'DOC-002', type: 'NF-e', reason: 'Regra pendente', priority: 'Alta'}),
      Object.freeze({id: 'DOC-003', type: 'OFX', reason: 'Conferência necessária', priority: 'Normal'}),
    ]),
  });
  root.S21SyntheticProvider = Object.freeze({loadProfile: () => profile, loadDashboard: () => dashboard});
}(globalThis));
