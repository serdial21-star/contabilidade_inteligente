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
    });
  }
  root.S21ApiClient = Object.freeze({ApiError, createApiClient});
}(globalThis));
