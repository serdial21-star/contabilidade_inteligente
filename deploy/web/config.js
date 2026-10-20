(function configure(root) {
  'use strict';
  root.S21_CONFIG = Object.freeze({
    environment: 'homologation',
    environmentLabel: 'PILOTO INTERNO',
    apiBaseUrl: '/api/v1',
    dataMode: 'real',
    authMode: 'bridge',
    // T-0012: login único S21 também aceito (endereço e chave vêm do servidor); #entrar abre a tela dele.
    s21Login: true,
    // T-0010: endereço do S21 Administrativo que emite um crachá novo e devolve à mesma tela (F5).
    bridgeRelaunchUrl: 'https://serdial21.com/admin/abrir-contabil',
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
