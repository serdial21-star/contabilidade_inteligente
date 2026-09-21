(function defineWorkContext(root) {
  'use strict';

  const STORAGE_KEY = 's21.work-context.v1';
  const DEFAULT_REVIEW_DAYS = 10;

  const pad = (value) => String(value).padStart(2, '0');
  const localDate = (date) => `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
  const currentMonth = (now) => `${now.getFullYear()}-${pad(now.getMonth() + 1)}`;

  function monthRange(referenceMonth) {
    if (!/^\d{4}-(0[1-9]|1[0-2])$/.test(referenceMonth || '')) throw new Error('invalid reference month');
    const [year, month] = referenceMonth.split('-').map(Number);
    return Object.freeze({
      referenceMonth,
      periodStart: `${referenceMonth}-01`,
      periodEnd: localDate(new Date(year, month, 0)),
    });
  }

  function sanitizeDays(value) {
    const days = Number(value);
    return Number.isInteger(days) && days >= 1 && days <= 90 ? days : DEFAULT_REVIEW_DAYS;
  }

  const sanitizeBasis = (value) => value === 'PERIOD_END' ? 'PERIOD_END' : 'IMPORT_DATE';

  function createWorkContextService({storage = root.localStorage, now = () => new Date()} = {}) {
    const read = () => {
      try { return JSON.parse(storage.getItem(STORAGE_KEY) || '{}'); }
      catch (_) { return {}; }
    };
    const write = (value) => {
      try { storage.setItem(STORAGE_KEY, JSON.stringify(value)); }
      catch (_) { /* Preferência local indisponível não bloqueia o trabalho. */ }
    };

    function load(companies) {
      const saved = read();
      const authorizedIds = new Set((companies || []).map((company) => company.id));
      const companyId = authorizedIds.has(saved.companyId) ? saved.companyId : companies?.[0]?.id || null;
      const referenceMonth = /^\d{4}-(0[1-9]|1[0-2])$/.test(saved.referenceMonth || '')
        ? saved.referenceMonth : currentMonth(now());
      return Object.freeze({
        context: Object.freeze({companyId, ...monthRange(referenceMonth)}),
        settings: Object.freeze({
          askAtStart: saved.askAtStart !== false,
          reviewDays: sanitizeDays(saved.reviewDays),
          reviewBasis: sanitizeBasis(saved.reviewBasis),
        }),
      });
    }

    function save(context, settings, companies) {
      const authorizedIds = new Set((companies || []).map((company) => company.id));
      if (!authorizedIds.has(context.companyId)) throw new Error('unauthorized company context');
      const range = monthRange(context.referenceMonth);
      const normalized = Object.freeze({
        context: Object.freeze({companyId: context.companyId, ...range}),
        settings: Object.freeze({
          askAtStart: settings.askAtStart !== false,
          reviewDays: sanitizeDays(settings.reviewDays),
          reviewBasis: sanitizeBasis(settings.reviewBasis),
        }),
      });
      write({
        companyId: normalized.context.companyId,
        referenceMonth: normalized.context.referenceMonth,
        askAtStart: normalized.settings.askAtStart,
        reviewDays: normalized.settings.reviewDays,
        reviewBasis: normalized.settings.reviewBasis,
      });
      return normalized;
    }

    function reviewExpiry(periodEnd, reviewDays, reviewBasis = 'IMPORT_DATE') {
      if (!/^\d{4}-\d{2}-\d{2}$/.test(periodEnd || '')) throw new Error('invalid period end');
      const baseDate = sanitizeBasis(reviewBasis) === 'PERIOD_END' ? periodEnd : localDate(now());
      const [year, month, day] = baseDate.split('-').map(Number);
      const expiry = new Date(year, month - 1, day + sanitizeDays(reviewDays));
      return localDate(expiry);
    }

    return Object.freeze({load, save, monthRange, reviewExpiry});
  }

  root.S21WorkContext = Object.freeze({createWorkContextService, monthRange});
}(globalThis));
