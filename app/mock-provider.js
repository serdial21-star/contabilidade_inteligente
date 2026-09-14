(function defineSyntheticProvider(root) {
  'use strict';

  const profile = Object.freeze({
    user: Object.freeze({id: 'synthetic-user', displayName: 'Ana Exemplo', roleLabel: 'Profissional fictícia'}),
    tenant: Object.freeze({id: 'synthetic-tenant', name: 'Escritório Demonstração'}),
    companies: Object.freeze([
      Object.freeze({
        id: 'synthetic-company-a', name: 'Empresa Horizonte · Matriz',
        permissions: Object.freeze(['company.read', 'journal.read', 'journal.approve', 'reconciliation.manage', 'audit.read']),
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

  root.S21SyntheticProvider = Object.freeze({loadProfile: () => profile, loadWidget});
}(globalThis));
