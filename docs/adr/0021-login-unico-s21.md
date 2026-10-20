# ADR 0021 — Entrada pelo login único S21 (revisa o ADR 0014)

## Status

Aceita em 2026-10-20 por decisão de Sérgio: ADR 0025 do Sistema C ("login único S21", D-100 do C) e T-0012 ("Aprovo T-0012, opção a").

## Contexto

O ADR 0014 abriu a ponte de login do Sistema A como entrada do B: o A conferia a sessão da equipe (login próprio pelo n8n, senha em SHA-256 sem sal) e emitia um passe para o B. O ADR 0025 do C unificou o login dos sistemas S21 no Supabase do Financeiro (São Paulo, plano Pro, bcrypt, código no celular, senha vazada conferida, chave RS256, passe de 15 min).

## Decisão

1. O B aceita **dois emissores** durante a transição: a ponte do A (até a etapa 3 do ADR 0025 do C) e o login S21 (`<S21_LOGIN_URL>/auth/v1`, audiência `authenticated`, RS256, JWKS público). O verificador é escolhido pelo emissor declarado; quem confere assinatura, emissor, audiência e validade é sempre o verificador escolhido; emissor desconhecido é recusado.
2. Passe S21 só vale com `role = authenticated`, não anônimo e `aal = aal2` (código no celular).
3. O passe S21 não traz `tenant_id`: o escritório vem de `S21_LOGIN_TENANT_ID` (o B tem um tenant fixo, ADR 0014 item 3). O vínculo do usuário no B continua obrigatório (`IdentityNotLinkedError`, T-0011).
4. **Revisa a regra "a tela nunca pede senha"** (shell-smoke 8 e `test_app_shell`): a tela do B tem um formulário de e-mail, senha e código; o navegador entrega esses dados **direto ao serviço de login S21** (`app/s21-login.js`), nunca à API do B. Passe e renovação só na memória (sem Web Storage, mantido), renovação automática antes de vencer. A política de conteúdo libera só o endereço do login S21 em `connect-src`.
5. Endereço e chave publicável vêm do servidor (`GET /api/v1/identity/login-config`); nada secreto no código.

## Consequências

- Recarregar a página continua usando a re-entrada pela ponte (T-0010) enquanto ela existir; `#entrar` abre direto a tela do login S21.
- Depois da etapa 3 do ADR 0025 do C: `authMode: 's21'`, retirar a ponte da configuração (`OIDC_*`) e o `bridgeRelaunchUrl`.
