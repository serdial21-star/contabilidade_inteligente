(function defineDashboardService(root) {
  'use strict';

  const PREFERENCE_KEY = 's21.dashboard.preferences.v1';
  const ALL_AUTHORIZED = 'all-authorized';

  const WIDGETS = Object.freeze([
    Object.freeze({id: 'W001', label: 'Documentos recebidos', kind: 'METRIC', permissions: ['company.read'], action: 'Ver documentos'}),
    Object.freeze({id: 'W002', label: 'Processados', kind: 'METRIC', permissions: ['company.read'], action: 'Ver processamento'}),
    Object.freeze({id: 'W003', label: 'Pendentes de revisão', kind: 'METRIC', permissions: ['journal.read'], action: 'Revisar'}),
    Object.freeze({id: 'W004', label: 'Fila Inteligente', kind: 'LIST', permissions: ['company.read'], action: 'Ver exceções'}),
    Object.freeze({id: 'W005', label: 'Propostas contábeis', kind: 'METRIC', permissions: ['journal.read'], action: 'Ver propostas'}),
    Object.freeze({id: 'W006', label: 'Aprovações pendentes', kind: 'STATUS', permissions: ['journal.approve'], action: 'Conferir aprovações'}),
    Object.freeze({id: 'W007', label: 'Empresas com pendências', kind: 'LIST', permissions: ['company.read'], action: 'Ver empresas'}),
    Object.freeze({id: 'W008', label: 'Obrigações próximas', kind: 'TABLE_PREVIEW', permissions: ['company.read'], action: 'Ver obrigações'}),
    Object.freeze({id: 'W009', label: 'Conciliações pendentes', kind: 'LIST', permissions: ['reconciliation.manage'], action: 'Ver conciliações'}),
    Object.freeze({id: 'W010', label: 'Atividade recente', kind: 'TIMELINE', permissions: ['audit.read'], action: 'Ver atividade'}),
  ]);

  const PRESETS = Object.freeze({
    'Visão Executiva': Object.freeze(['W004', 'W006', 'W007', 'W008', 'W010']),
    'Visão Contábil': Object.freeze(['W005', 'W003', 'W006', 'W010']),
    'Visão Fiscal': Object.freeze(['W001', 'W002', 'W004']),
    'Visão Operacional': Object.freeze(['W001', 'W004', 'W003', 'W007', 'W010']),
    'Minha Visão': Object.freeze(['W001', 'W003', 'W004', 'W005', 'W007', 'W010']),
  });

  const hasAnyPermission = (granted, required) => {
    if (!required || required.length === 0) return true;
    const available = new Set(granted || []);
    return required.some((permission) => available.has(permission));
  };

  function authorizedCatalog(permissions) {
    return WIDGETS.filter((widget) => hasAnyPermission(permissions, widget.permissions));
  }

  function defaultLayout(permissions, preset = 'Minha Visão') {
    const allowed = new Set(authorizedCatalog(permissions).map((widget) => widget.id));
    const widgets = (PRESETS[preset] || PRESETS['Minha Visão']).filter((id) => allowed.has(id));
    const wide = widgets.filter((id) => id === 'W004' || id === 'W010');
    return Object.freeze({preset: PRESETS[preset] ? preset : 'Minha Visão', widgets: Object.freeze(widgets), wide: Object.freeze(wide)});
  }

  function sanitizePreferences(value, permissions) {
    const fallback = defaultLayout(permissions);
    if (!value || typeof value !== 'object') return fallback;
    const allowed = new Set(authorizedCatalog(permissions).map((widget) => widget.id));
    const widgets = Array.isArray(value.widgets)
      ? [...new Set(value.widgets.filter((id) => typeof id === 'string' && allowed.has(id)))]
      : [...fallback.widgets];
    const wide = Array.isArray(value.wide)
      ? [...new Set(value.wide.filter((id) => widgets.includes(id)))]
      : [];
    const preset = typeof value.preset === 'string' && Object.hasOwn(PRESETS, value.preset)
      ? value.preset : 'Minha Visão';
    return Object.freeze({preset, widgets: Object.freeze(widgets), wide: Object.freeze(wide)});
  }

  function createPreferenceStore(storage) {
    return Object.freeze({
      load(permissions) {
        if (!storage) return defaultLayout(permissions);
        try { return sanitizePreferences(JSON.parse(storage.getItem(PREFERENCE_KEY)), permissions); }
        catch (_) { return defaultLayout(permissions); }
      },
      save(layout, permissions) {
        const safe = sanitizePreferences(layout, permissions);
        if (storage) {
          try { storage.setItem(PREFERENCE_KEY, JSON.stringify({preset: safe.preset, widgets: safe.widgets, wide: safe.wide})); }
          catch (_) { /* A preferência local é opcional; a aplicação continua funcional. */ }
        }
        return safe;
      },
      clear() {
        if (!storage) return;
        try { storage.removeItem(PREFERENCE_KEY); }
        catch (_) { /* Sem impacto em dados operacionais. */ }
      },
    });
  }

  function createApiProvider(apiClient) {
    const available = (state, payload) => Object.freeze({state, ...payload});
    async function forCompanies(context, loader) {
      const responses = await Promise.all(context.companyIds.map((id) => loader(id)));
      return responses.flat();
    }
    return Object.freeze({
      async loadWidget(widgetId, context) {
        if (widgetId === 'W001' || widgetId === 'W002' || widgetId === 'W007') {
          const summaries = await Promise.all(context.companyIds.map(async (id) => ({id, summary: await apiClient.documentSummary(id)})));
          if (widgetId === 'W001') {
            const value = summaries.reduce((total, item) => total + item.summary.received, 0);
            return available(value ? 'READY' : 'EMPTY', {value: String(value), note: value ? 'Recebimentos documentais autorizados' : 'Nenhum documento recebido.', items: []});
          }
          if (widgetId === 'W002') {
            const value = summaries.reduce((total, item) => total + item.summary.processed, 0);
            return available(value ? 'READY' : 'EMPTY', {value: String(value), note: value ? 'Transformações concluídas; não significa aprovação' : 'Nenhum processamento concluído.', items: []});
          }
          const pending = summaries.filter((item) => item.summary.attention_required > 0);
          return available(pending.length ? 'READY' : 'EMPTY', {
            value: String(pending.length), note: pending.length ? 'Somente empresas autorizadas com exceções documentais' : 'Nenhuma empresa com exceção documental.',
            items: pending.slice(0, 5).map((item) => ({title: context.companyNames?.[item.id] || 'Empresa autorizada', detail: `${item.summary.attention_required} item(ns) requerem atenção`, meta: 'Contexto autorizado'})),
          });
        }
        if (widgetId === 'W003' || widgetId === 'W005' || widgetId === 'W006') {
          const reviews = await forCompanies(context, (id) => apiClient.dashboardReviews(id));
          const pending = reviews.filter((item) => item.status === 'PENDING_APPROVAL');
          if (widgetId === 'W003') return available(pending.length ? 'READY' : 'EMPTY', {value: String(pending.length), note: pending.length ? 'Revisões que exigem conferência' : 'Nenhuma proposta aguardando revisão.', items: []});
          if (widgetId === 'W006') return available(pending.length ? 'READY' : 'EMPTY', {value: String(pending.length), note: pending.length ? 'Dentro da sua alçada autorizada' : 'Nenhuma aprovação pendente.', items: []});
          return available(reviews.length ? 'READY' : 'EMPTY', {value: String(reviews.length), note: reviews.length ? 'Propostas disponíveis para consulta' : 'Nenhuma proposta contábil disponível.', items: []});
        }
        if (widgetId === 'W004') {
          const issues = await forCompanies(context, (id) => apiClient.dashboardExceptions(id));
          return available(issues.length ? 'READY' : 'EMPTY', {value: String(issues.length), note: issues.length ? 'Exceções abertas no contexto atual' : 'Nenhuma exceção pendente.', items: issues.slice(0, 5).map((item) => ({title: item.code, detail: item.severity, meta: item.created_at}))});
        }
        if (widgetId === 'W010') {
          const events = await forCompanies(context, (id) => apiClient.dashboardActivity(id));
          return available(events.length ? 'READY' : 'EMPTY', {value: '', note: events.length ? 'Eventos operacionais verificados' : 'Nenhuma atividade recente.', items: events.slice(0, 5).map((item) => ({title: item.action, detail: item.module, meta: item.occurred_at}))});
        }
        return available('UNAVAILABLE', {value: '', note: 'Fonte agregada ainda não disponível.', items: []});
      },
    });
  }

  function createDashboardService({dataMode, apiClient, syntheticProvider, storage}) {
    const preferences = createPreferenceStore(storage === undefined ? root.localStorage : storage);
    const provider = dataMode === 'synthetic' ? syntheticProvider : createApiProvider(apiClient);
    async function loadWidget(widgetId, context) {
      const widget = WIDGETS.find((item) => item.id === widgetId);
      if (!widget || !hasAnyPermission(context.permissions, widget.permissions)) return Object.freeze({state: 'FORBIDDEN'});
      return provider.loadWidget(widgetId, context);
    }
    async function loadSummary(widgetIds, context) {
      const entries = await Promise.all(widgetIds.map(async (id) => {
        try { return [id, await loadWidget(id, context)]; }
        catch (error) {
          const state = error?.code === 'FORBIDDEN' ? 'FORBIDDEN' : 'ERROR';
          return [id, Object.freeze({state, value: '', note: state === 'FORBIDDEN' ? 'Conteúdo não autorizado.' : 'Não foi possível atualizar este indicador.', items: []})];
        }
      }));
      return Object.freeze(Object.fromEntries(entries));
    }
    return Object.freeze({
      widgets: WIDGETS, presets: PRESETS, allAuthorizedId: ALL_AUTHORIZED,
      authorizedCatalog, defaultLayout, sanitizePreferences,
      loadPreferences: preferences.load, savePreferences: preferences.save, clearPreferences: preferences.clear,
      loadWidget, loadSummary,
    });
  }

  root.S21Dashboard = Object.freeze({createDashboardService, WIDGETS, PRESETS, ALL_AUTHORIZED});
}(globalThis));
