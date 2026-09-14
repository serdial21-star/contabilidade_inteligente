(function defineOidcClient(root) {
  'use strict';

  const TRANSACTION_KEY = 'serdial21.oidc.transaction';
  const MAX_TRANSACTION_AGE_MS = 10 * 60 * 1000;

  class OidcError extends Error {
    constructor(code) { super(code); this.name = 'OidcError'; this.code = code; }
  }

  const encode = (bytes) => btoa(String.fromCharCode(...bytes))
    .replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');

  function randomValue(cryptoProvider, size) {
    const bytes = new Uint8Array(size);
    cryptoProvider.getRandomValues(bytes);
    return encode(bytes);
  }

  async function challengeFor(cryptoProvider, verifier) {
    const digest = await cryptoProvider.subtle.digest(
      'SHA-256', new TextEncoder().encode(verifier),
    );
    return encode(new Uint8Array(digest));
  }

  function createOidcClient({config, fetchImpl, storage, locationRef, historyRef, cryptoProvider, getAccessToken}) {
    const requestFetch = fetchImpl || root.fetch;
    const transactionStore = storage || root.sessionStorage;
    const browserLocation = locationRef || root.location;
    const browserHistory = historyRef || root.history;
    const secureRandom = cryptoProvider || root.crypto;

    function trustedEndpoint(value) {
      let endpoint;
      try { endpoint = new URL(value); }
      catch (_) { throw new OidcError('OIDC_METADATA_INVALID'); }
      const localDevelopment = config.environment === 'development'
        && endpoint.protocol === 'http:'
        && ['localhost', '127.0.0.1'].includes(endpoint.hostname);
      if (endpoint.protocol !== 'https:' && !localDevelopment) throw new OidcError('OIDC_ENDPOINT_INSECURE');
      return endpoint;
    }

    function isConfigured() {
      return config.authMode === 'oidc'
        && Boolean(config.oidc?.issuer && config.oidc?.clientId && config.oidc?.redirectUri);
    }

    function validateBrowserRedirects() {
      const redirect = trustedEndpoint(config.oidc.redirectUri);
      if (redirect.origin !== browserLocation.origin) throw new OidcError('OIDC_REDIRECT_ORIGIN_INVALID');
      if (config.oidc.postLogoutRedirectUri) {
        const postLogout = trustedEndpoint(config.oidc.postLogoutRedirectUri);
        if (postLogout.origin !== browserLocation.origin) throw new OidcError('OIDC_REDIRECT_ORIGIN_INVALID');
      }
    }

    async function discovery() {
      if (!isConfigured()) throw new OidcError('OIDC_NOT_CONFIGURED');
      validateBrowserRedirects();
      const issuer = config.oidc.issuer.replace(/\/$/, '');
      trustedEndpoint(issuer);
      const discoveryUrl = trustedEndpoint(
        config.oidc.discoveryUrl || `${issuer}/.well-known/openid-configuration`,
      ).toString();
      let response;
      try { response = await requestFetch(discoveryUrl, {headers: {Accept: 'application/json'}, credentials: 'omit'}); }
      catch (_) { throw new OidcError('OIDC_DISCOVERY_UNAVAILABLE'); }
      if (!response.ok) throw new OidcError('OIDC_DISCOVERY_UNAVAILABLE');
      const metadata = await response.json();
      if (metadata.issuer?.replace(/\/$/, '') !== issuer) throw new OidcError('OIDC_ISSUER_MISMATCH');
      if (!metadata.authorization_endpoint || !metadata.token_endpoint) throw new OidcError('OIDC_METADATA_INVALID');
      trustedEndpoint(metadata.authorization_endpoint);
      trustedEndpoint(metadata.token_endpoint);
      if (metadata.end_session_endpoint) trustedEndpoint(metadata.end_session_endpoint);
      return metadata;
    }

    async function beginLogin(returnTo = '#overview') {
      const metadata = await discovery();
      const state = randomValue(secureRandom, 32);
      const verifier = randomValue(secureRandom, 64);
      const challenge = await challengeFor(secureRandom, verifier);
      transactionStore.setItem(TRANSACTION_KEY, JSON.stringify({state, verifier, returnTo, createdAt: Date.now()}));
      const authorization = new URL(metadata.authorization_endpoint);
      authorization.searchParams.set('response_type', 'code');
      authorization.searchParams.set('client_id', config.oidc.clientId);
      authorization.searchParams.set('redirect_uri', config.oidc.redirectUri);
      authorization.searchParams.set('scope', config.oidc.scope.join(' '));
      authorization.searchParams.set('state', state);
      authorization.searchParams.set('code_challenge', challenge);
      authorization.searchParams.set('code_challenge_method', 'S256');
      if (config.oidc.audience) authorization.searchParams.set('audience', config.oidc.audience);
      browserLocation.assign(authorization.toString());
    }

    function hasCallback() {
      const parameters = new URLSearchParams(browserLocation.search);
      return parameters.has('code') || parameters.has('error');
    }

    async function handleCallback() {
      const parameters = new URLSearchParams(browserLocation.search);
      const serialized = transactionStore.getItem(TRANSACTION_KEY);
      transactionStore.removeItem(TRANSACTION_KEY);
      browserHistory.replaceState(null, '', `${browserLocation.pathname}${browserLocation.hash || ''}`);
      if (!serialized) throw new OidcError('OIDC_TRANSACTION_MISSING');
      let transaction;
      try { transaction = JSON.parse(serialized); }
      catch (_) { throw new OidcError('OIDC_TRANSACTION_INVALID'); }
      if (parameters.has('error')) throw new OidcError('OIDC_AUTHORIZATION_FAILED');
      if (!parameters.get('state') || parameters.get('state') !== transaction.state) throw new OidcError('OIDC_STATE_INVALID');
      if (Date.now() - transaction.createdAt > MAX_TRANSACTION_AGE_MS) throw new OidcError('OIDC_TRANSACTION_EXPIRED');
      const code = parameters.get('code');
      if (!code || !transaction.verifier) throw new OidcError('OIDC_CALLBACK_INVALID');
      const metadata = await discovery();
      const body = new URLSearchParams({
        grant_type: 'authorization_code', code,
        client_id: config.oidc.clientId,
        redirect_uri: config.oidc.redirectUri,
        code_verifier: transaction.verifier,
      });
      let response;
      try {
        response = await requestFetch(metadata.token_endpoint, {
          method: 'POST', headers: {'Content-Type': 'application/x-www-form-urlencoded'},
          body, credentials: 'omit',
        });
      } catch (_) { throw new OidcError('OIDC_TOKEN_EXCHANGE_FAILED'); }
      if (!response.ok) throw new OidcError('OIDC_TOKEN_EXCHANGE_FAILED');
      const tokens = await response.json();
      if (String(tokens.token_type).toLowerCase() !== 'bearer' || typeof tokens.access_token !== 'string' || !tokens.access_token) {
        throw new OidcError('OIDC_TOKEN_RESPONSE_INVALID');
      }
      return Object.freeze({accessToken: tokens.access_token, returnTo: transaction.returnTo});
    }

    function clearLocalSession() { transactionStore.removeItem(TRANSACTION_KEY); }

    async function logout() {
      clearLocalSession();
      if (!config.oidc?.remoteLogoutEnabled || !config.oidc?.postLogoutRedirectUri) return 'LOCAL_ONLY';
      const metadata = await discovery();
      if (!metadata.end_session_endpoint) return 'LOCAL_ONLY';
      const target = new URL(metadata.end_session_endpoint);
      target.searchParams.set('client_id', config.oidc.clientId);
      target.searchParams.set('post_logout_redirect_uri', config.oidc.postLogoutRedirectUri);
      browserLocation.assign(target.toString());
      return 'REMOTE_REQUESTED';
    }

    return Object.freeze({
      isConfigured, beginLogin, handleCallback, hasCallback,
      getAccessToken: () => getAccessToken?.() || null,
      getSessionState: () => Object.freeze({configured: isConfigured(), authMode: config.authMode}),
      refreshOrRenew: () => 'REAUTH_REQUIRED',
      logout, clearLocalSession,
    });
  }

  root.S21OidcClient = Object.freeze({OidcError, createOidcClient});
}(globalThis));
