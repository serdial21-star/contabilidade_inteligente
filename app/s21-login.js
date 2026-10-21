(function defineS21Login(root) {
  'use strict';
  // T-0012 (ADR 0025 do Sistema C): login único S21 (Supabase do Financeiro), pela API pública de login.
  // Passes só na memória desta página (nunca no armazenamento do navegador, na URL ou em registros).
  class S21LoginError extends Error {
    constructor(code) { super(code); this.name = 'S21LoginError'; this.code = code; }
  }

  function createS21LoginClient({apiBaseUrl, fetchImpl}) {
    const http = fetchImpl || root.fetch;
    let settings = null;
    let access = null;
    let renewal = null;
    let factorId = null;
    // T-0014 (D-059 do Sistema C): depois da entrega, a renovação mora no cookie HttpOnly do servidor do B e só ele renova.
    let serverSession = false;
    const apiUrl = (path) => `${String(apiBaseUrl).replace(/\/$/, '')}/identity/session${path}`;

    /** Rotas da sessão no servidor do B (mesma origem; o cookie vai junto, a página nunca o lê). */
    async function sessionCall(path, {body, token} = {}) {
      const headers = {Accept: 'application/json', 'X-S21-Session': '1'};
      if (body !== undefined) headers['Content-Type'] = 'application/json';
      if (token) headers.Authorization = `Bearer ${token}`;
      try {
        const response = await http(apiUrl(path), {method: 'POST', headers, body: body === undefined ? undefined : JSON.stringify(body), credentials: 'same-origin'});
        if (!response.ok) return null;
        const payload = await response.json().catch(() => null);
        return payload && typeof payload.access_token === 'string' ? payload.access_token : null;
      } catch (_) { return null; }
    }

    async function call(url, {method = 'POST', body, token} = {}) {
      const headers = {apikey: settings.publishable_key, Accept: 'application/json'};
      if (body !== undefined) headers['Content-Type'] = 'application/json';
      if (token) headers.Authorization = `Bearer ${token}`;
      let response;
      try { response = await http(url, {method, headers, body: body === undefined ? undefined : JSON.stringify(body), credentials: 'omit'}); }
      catch (_) { throw new S21LoginError('NETWORK'); }
      if (response.status === 429) throw new S21LoginError('RATE_LIMITED');
      if (response.status === 400 || response.status === 401 || response.status === 422) throw new S21LoginError('REJECTED');
      if (!response.ok) throw new S21LoginError('UNAVAILABLE');
      try { return await response.json(); } catch (_) { throw new S21LoginError('UNAVAILABLE'); }
    }

    const auth = (path) => `${settings.url}/auth/v1${path}`;

    function keep(payload) {
      if (!payload || typeof payload.access_token !== 'string' || typeof payload.refresh_token !== 'string') {
        throw new S21LoginError('UNAVAILABLE');
      }
      access = payload.access_token;
      renewal = payload.refresh_token;
      return payload;
    }

    return Object.freeze({
      /** Endereço e chave publicável vêm do servidor do B; sem configuração, não há login S21. */
      async load() {
        let response;
        try { response = await http(`${String(apiBaseUrl).replace(/\/$/, '')}/identity/login-config`, {headers: {Accept: 'application/json'}, credentials: 'omit'}); }
        catch (_) { return false; }
        if (!response.ok) return false;
        const payload = await response.json().catch(() => null);
        const candidate = payload && payload.s21;
        if (!candidate || typeof candidate.url !== 'string' || !candidate.url.startsWith('https://') || typeof candidate.publishable_key !== 'string') return false;
        settings = Object.freeze({url: candidate.url.replace(/\/$/, ''), publishable_key: candidate.publishable_key});
        return true;
      },
      isConfigured: () => settings !== null,
      /** 1º passo: e-mail e senha. A equipe precisa do código do celular (aal2) para entrar no Contábil. */
      async signIn(email, password) {
        if (!settings) throw new S21LoginError('NOT_CONFIGURED');
        const payload = keep(await call(auth('/token?grant_type=password'), {body: {email, password}}));
        const factors = Array.isArray(payload.user?.factors) ? payload.user.factors : [];
        const totp = factors.find((factor) => factor.factor_type === 'totp' && factor.status === 'verified');
        if (!totp) { access = null; renewal = null; throw new S21LoginError('NO_CODE'); }
        factorId = totp.id;
      },
      /** 2º passo: código de 6 dígitos do aplicativo do celular; devolve o passe com aal2. */
      async verifyCode(code) {
        if (!settings || !access || !factorId) throw new S21LoginError('NOT_STARTED');
        const challenge = await call(auth(`/factors/${encodeURIComponent(factorId)}/challenge`), {body: {}, token: access});
        if (!challenge || typeof challenge.id !== 'string') throw new S21LoginError('UNAVAILABLE');
        keep(await call(auth(`/factors/${encodeURIComponent(factorId)}/verify`), {body: {challenge_id: challenge.id, code}, token: access}));
        return access;
      },
      /** T-0014: entrega a renovação ao servidor (cookie HttpOnly); sem sucesso, a sessão segue só na memória. */
      async keepSignedIn() {
        if (!settings || !access || !renewal) return null;
        const token = await sessionCall('', {body: {refresh_token: renewal}, token: access});
        if (!token) return null;
        access = token; renewal = null; serverSession = true;
        return access;
      },
      /** T-0014: F5 ou recarga — passe novo pelo cookie; null se não houver sessão. */
      async resume() {
        if (!settings) return null;
        const token = await sessionCall('/refresh');
        if (!token) return null;
        access = token; renewal = null; serverSession = true;
        return access;
      },
      /** Renova o passe antes de vencer (o nível aal2 se mantém na renovação). */
      async renew() {
        if (serverSession) {
          const token = await sessionCall('/refresh');
          if (!token) throw new S21LoginError('REJECTED');
          access = token;
          return access;
        }
        if (!settings || !renewal) throw new S21LoginError('NOT_STARTED');
        keep(await call(auth('/token?grant_type=refresh_token'), {body: {refresh_token: renewal}}));
        return access;
      },
      async logout() {
        const token = access;
        const viaServer = serverSession;
        access = null; renewal = null; factorId = null; serverSession = false;
        if (viaServer) { await sessionCall('/logout', {token}); return; }
        if (settings && token) { try { await call(auth('/logout?scope=local'), {body: {}, token}); } catch (_) { /* sair local sempre vale */ } }
      },
      forget() { access = null; renewal = null; factorId = null; serverSession = false; },
      /** Segundos até o passe vencer (lido do próprio passe; sem conferir assinatura — quem confere é o servidor). */
      secondsLeft(token, now = Date.now()) {
        try {
          const part = String(token).split('.')[1].replace(/-/g, '+').replace(/_/g, '/');
          const claims = JSON.parse(root.atob(part.padEnd(Math.ceil(part.length / 4) * 4, '=')));
          return Math.floor(Number(claims.exp) - now / 1000);
        } catch (_) { return 0; }
      },
    });
  }

  root.S21Login = Object.freeze({createS21LoginClient, S21LoginError});
}(globalThis));
