(function configure(root) {
  'use strict';
  // Configuração pública e não secreta. Ambientes reais devem gerar este artefato no deploy.
  root.S21_CONFIG = Object.freeze({
    environment: 'development',
    environmentLabel: 'DESENVOLVIMENTO',
    apiBaseUrl: '/api/v1',
    dataMode: 'synthetic',
    authMode: 'synthetic',
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
