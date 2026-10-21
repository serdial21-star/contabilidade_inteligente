'''Renovação da sessão do login único S21 no Supabase do Financeiro (T-0014; D-059 do Sistema C).

Só `POST /auth/v1/token?grant_type=refresh_token` e `POST /auth/v1/logout`, com a chave publicável (não é segredo).
Fora de qualquer transação de negócio; nunca registra passe nem renovação.
'''

import json
from typing import Any
import urllib.error
import urllib.request

from serdial21.modules.identity.application.ports.session import RefreshedSession, SessionRefreshError


TIMEOUT_SECONDS = 5
DEFAULT_EXPIRES_IN = 900


class SupabaseSessionProvider:
    def __init__(self, base_url: str, publishable_key: str) -> None:
        if not base_url.startswith('https://'):
            raise ValueError('S21_LOGIN_URL deve usar HTTPS')
        self._base = base_url.rstrip('/') + '/auth/v1'
        self._key = publishable_key

    def __repr__(self) -> str:
        return f'SupabaseSessionProvider(url={self._base!r})'

    def _post(self, path: str, body: dict[str, Any], bearer: str | None = None) -> Any:
        headers = {'Content-Type': 'application/json', 'apikey': self._key}
        if bearer:
            headers['Authorization'] = 'Bearer ' + bearer
        request = urllib.request.Request(  # noqa: S310 - endereço HTTPS conferido no construtor
            self._base + path, data=json.dumps(body).encode(), method='POST', headers=headers,
        )
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:  # noqa: S310
            raw = response.read(1_000_000)
        return json.loads(raw.decode()) if raw else None

    def refresh(self, refresh_token: str) -> RefreshedSession:
        try:
            payload = self._post('/token?grant_type=refresh_token', {'refresh_token': refresh_token})
        except urllib.error.HTTPError as error:
            kind = 'unavailable' if error.code >= 500 or error.code == 429 else 'invalid'
            raise SessionRefreshError(kind) from None
        except (urllib.error.URLError, TimeoutError, OSError, ValueError):
            raise SessionRefreshError('unavailable') from None
        if not isinstance(payload, dict):
            raise SessionRefreshError('unavailable')
        access, refresh, expires = payload.get('access_token'), payload.get('refresh_token'), payload.get('expires_in')
        if not isinstance(access, str) or not isinstance(refresh, str) or not access or not refresh:
            raise SessionRefreshError('unavailable')
        return RefreshedSession(access, refresh, expires if isinstance(expires, int) and expires > 0 else DEFAULT_EXPIRES_IN)

    def logout(self, access_token: str) -> None:
        # Melhor esforço: o cookie é apagado de qualquer jeito; sem resposta, a sessão vence sozinha.
        try:
            self._post('/logout?scope=local', {}, access_token)
        except (urllib.error.URLError, TimeoutError, OSError, ValueError):
            return
