# T-0015 — Caddy do host versionado e sem CSP repetida (M-116 do Financeiro)

| Campo | Valor |
|---|---|
| Estado | IMPLEMENTADA — aguardando aplicação na VPS e conferência |
| Origem | 2026-10-21: o Caddy do host (`/root/n8n/n8n/Caddyfile`) mandava uma segunda Content-Security-Policy, desatualizada, que bloqueou o login S21 (T-0012). Pendência M-116 do Sistema C |
| Sistema | Sistema B (borda da VPS de Campinas) |
| Exige ADR | não |
| Exige ação do usuário | aprovar ("organizar o próximo passo conforme sua orientação", 2026-10-21) e colar o roteiro na VPS |

## Decisão

- `deploy/host-caddy/Caddyfile` passa a ser a cópia fiel do Caddy do host (lida do servidor em 2026-10-21; sem senha nem chave).
- O host **não repete** a CSP: ela vive só em `deploy/web/Caddyfile` e `app/index.html`. Os demais cabeçalhos do host (HSTS, nosniff, Referrer-Policy, Permissions-Policy, X-Frame-Options) ficam.
- Teste de contrato: `tests/frontend/test_app_shell.py::test_t0015_…`.

## Aplicação

Roteiro no Sistema C: `Docs/painel-login-a/roteiros/N-09-caddy-do-host.md` (cópia de segurança, retirada das duas linhas `@static`, validação, recarga sem queda e volta automática se falhar).
