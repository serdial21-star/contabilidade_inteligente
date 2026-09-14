(function defineCore(root) {
  'use strict';
  const STATES = Object.freeze({
    BOOTING: 'BOOTING', UNAUTHENTICATED: 'UNAUTHENTICATED',
    AUTHENTICATING: 'AUTHENTICATING', AUTHENTICATED: 'AUTHENTICATED',
    SESSION_EXPIRED: 'SESSION_EXPIRED', FORBIDDEN: 'FORBIDDEN',
    NETWORK_ERROR: 'NETWORK_ERROR', SERVER_ERROR: 'SERVER_ERROR',
  });

  function createSessionStore() {
    let state = STATES.BOOTING;
    let accessToken = null;
    let profile = null;
    let mode = null;
    const clear = () => { accessToken = null; profile = null; mode = null; };
    return Object.freeze({
      states: STATES,
      snapshot: () => Object.freeze({state, profile, mode}),
      token: () => accessToken,
      unauthenticated: () => { clear(); state = STATES.UNAUTHENTICATED; },
      authenticating: () => { clear(); state = STATES.AUTHENTICATING; },
      establish: ({token, userProfile}) => {
        if (!token || !userProfile) throw new Error('invalid authenticated session');
        accessToken = token; profile = userProfile; mode = 'oidc'; state = STATES.AUTHENTICATED;
      },
      startSyntheticWorkspace: (userProfile) => {
        clear(); profile = userProfile; mode = 'synthetic'; state = STATES.AUTHENTICATED;
      },
      resume: () => {
        if (!profile) throw new Error('cannot resume without profile');
        state = STATES.AUTHENTICATED;
      },
      expire: () => { clear(); state = STATES.SESSION_EXPIRED; },
      forbid: () => { state = STATES.FORBIDDEN; },
      failNetwork: () => { clear(); state = STATES.NETWORK_ERROR; },
      failServer: () => { clear(); state = STATES.SERVER_ERROR; },
      logout: () => { clear(); state = STATES.UNAUTHENTICATED; },
    });
  }

  function hasPermission(granted, required) {
    if (!required || required.length === 0) return true;
    const permissions = new Set(granted || []);
    return required.some((permission) => permissions.has(permission));
  }
  const allowedNavigation = (items, granted) => items.filter((item) => hasPermission(granted, item.permissions));
  function normalizeHttpError(status) {
    if (status === 401) return STATES.SESSION_EXPIRED;
    if (status === 403) return STATES.FORBIDDEN;
    if (status >= 500) return STATES.SERVER_ERROR;
    return 'REQUEST_ERROR';
  }
  root.S21Core = Object.freeze({STATES, createSessionStore, hasPermission, allowedNavigation, normalizeHttpError});
}(globalThis));
