(function defineApiClient(root) {
  'use strict';
  class ApiError extends Error {
    constructor(code, status) { super(code); this.name = 'ApiError'; this.code = code; this.status = status; }
  }
  function createApiClient({baseUrl, getAccessToken, onAuthenticationFailure, fetchImpl}) {
    const requestFetch = fetchImpl || root.fetch;
    const normalizedBase = String(baseUrl || '').replace(/\/$/, '');
    if (!normalizedBase.startsWith('/')) throw new Error('API base URL must be same-origin');
    async function request(path, options = {}) {
      const token = getAccessToken();
      if (!token) throw new ApiError('UNAUTHENTICATED', 0);
      const headers = new Headers(options.headers || {});
      headers.set('Accept', 'application/json');
      headers.set('Authorization', `Bearer ${token}`);
      if (root.crypto && typeof root.crypto.randomUUID === 'function') headers.set('X-Correlation-ID', root.crypto.randomUUID());
      let response;
      try { response = await requestFetch(`${normalizedBase}${path}`, {...options, headers, credentials: 'omit'}); }
      catch (_) { throw new ApiError('NETWORK_UNAVAILABLE', 0); }
      if (response.status === 401) { onAuthenticationFailure(); throw new ApiError('SESSION_EXPIRED', 401); }
      if (response.status === 403) throw new ApiError('FORBIDDEN', 403);
      if (response.status >= 500) throw new ApiError('SERVER_TEMPORARY_FAILURE', response.status);
      if (!response.ok) throw new ApiError('REQUEST_FAILED', response.status);
      if (response.status === 204) return null;
      try { return await response.json(); }
      catch (_) { throw new ApiError('INVALID_RESPONSE', response.status); }
    }
    return Object.freeze({
      request,
      currentApplication: () => request('/identity/me'),
      identityContext: (companyId) => request(`/identity/context?company_id=${encodeURIComponent(companyId)}`),
      dashboardReviews: (companyId) => request(`/operations/companies/${encodeURIComponent(companyId)}/reviews?limit=50`),
      dashboardExceptions: (companyId) => request(`/operations/companies/${encodeURIComponent(companyId)}/exceptions?limit=50`),
      dashboardActivity: (companyId) => request(`/operations/companies/${encodeURIComponent(companyId)}/audit-events?limit=10`),
      company: (companyId) => request(`/operations/companies/${encodeURIComponent(companyId)}`),
      documents: (companyId, filters = {}) => {
        const query = new URLSearchParams();
        Object.entries(filters).forEach(([key, value]) => {
          if (value !== '' && value !== null && value !== undefined) query.set(key, String(value));
        });
        return request(`/operations/companies/${encodeURIComponent(companyId)}/documents?${query}`);
      },
      document: (companyId, documentId) => request(`/operations/companies/${encodeURIComponent(companyId)}/documents/${encodeURIComponent(documentId)}`),
      documentSummary: (companyId) => request(`/operations/companies/${encodeURIComponent(companyId)}/documents/summary`),
      fiscalDocuments: (companyId, filters = {}) => request(`/operations/companies/${encodeURIComponent(companyId)}/fiscal-documents?${queryString(filters)}`),
      fiscalDocument: (companyId, id) => request(`/operations/companies/${encodeURIComponent(companyId)}/fiscal-documents/${encodeURIComponent(id)}`),
      importNfe: (companyId, file, fields) => request(`/operations/companies/${encodeURIComponent(companyId)}/imports/nfe?${queryString(fields)}`, {
        method: 'POST', body: file, headers: {'Content-Type': file.type || 'application/xml', 'X-Filename': file.name, 'Idempotency-Key': root.crypto.randomUUID()},
      }),
      bankStatements: (companyId, filters = {}) => request(`/operations/companies/${encodeURIComponent(companyId)}/bank-statements?${queryString(filters)}`),
      bankStatement: (companyId, id, filters = {}) => request(`/operations/companies/${encodeURIComponent(companyId)}/bank-statements/${encodeURIComponent(id)}?${queryString(filters)}`),
      importOfx: (companyId, file) => request(`/operations/companies/${encodeURIComponent(companyId)}/imports/ofx`, {
        method: 'POST', body: file, headers: {'Content-Type': file.type || 'application/x-ofx', 'X-Filename': file.name, 'Idempotency-Key': root.crypto.randomUUID()},
      }),
    });
  }
  function queryString(filters) {
    const query = new URLSearchParams();
    Object.entries(filters || {}).forEach(([key, value]) => {
      if (value !== '' && value !== null && value !== undefined) query.set(key, String(value));
    });
    return query.toString();
  }
  root.S21ApiClient = Object.freeze({ApiError, createApiClient});
}(globalThis));
