(function configure(root) {
  'use strict';
  root.S21_CONFIG = Object.freeze({
    environment: 'homologation',
    environmentLabel: 'PILOTO INTERNO',
    apiBaseUrl: '/api/v1',
    dataMode: 'real',
    authMode: 'bridge',
    oidc: Object.freeze({
      issuer: '',
      discoveryUrl: '',
      clientId: '',
      redirectUri: '',
      postLogoutRedirectUri: '',
      scope: Object.freeze(['openid']),
      audience: '',
      remoteLogoutEnabled: false,
    }),
  });
}(globalThis));
