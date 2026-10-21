# T-0014 — Sessão do login S21 que sobrevive ao F5 (ADR 0022 do B; D-059 e D-101 do Sistema C)

| Campo | Valor |
|---|---|
| Estado | IMPLEMENTADA — aguardando publicação na VPS e conferência do usuário |
| Origem | Conferência da T-0013 em 2026-10-21: "no contábil quando aperta o f5 sai e entra na tela de login"; Sérgio: "mude a regra e registre… o f5 não vai para o login, atualiza e mantém na página que estava antes" |
| Sistema | Sistema B (servidor e tela) |
| Exige ADR | sim: **ADR 0022 do B** (emenda o ADR 0021 item 4) |
| Exige ação do usuário | publicar na VPS (comandos preparados pelo Claude) e conferir |

## 1. Escopo

Igual à sessão do Financeiro (D-059 do C): renovação no cookie HttpOnly do servidor, F5 mantém a sessão e a tela, saída encerra a sessão. Detalhes no ADR 0022.

## 2. Resultado (Claude)

- Servidor: porta `modules/identity/application/ports/session.py`; adaptador `modules/identity/adapters/outbound/s21_session.py` (só `token?grant_type=refresh_token` e `logout`, chave publicável, 5 s); rotas `entrypoints/http/routes/identity_session.py` (`POST /identity/session`, `/refresh` e `/logout`; cabeçalho `X-S21-Session: 1`; mesma pessoa; cookie `s21_contabil_session`); configuração `S21_SESSION_COOKIE_MAX_AGE_SECONDS` (padrão 1200); ligado só com o login S21 configurado.
- Tela: `s21-login.js` com `keepSignedIn`, `resume`, `renew` e `logout` pelo servidor depois da entrega; `app.js` retoma no F5 e volta à mesma tela, renova no máximo a cada 10 min e, sem o recurso no servidor, entra só na memória.
- Defeito achado no teste de navegador e corrigido: a renovação usava a validade do passe sem teto. Um passe longo fazia o navegador renovar em sequência; com o passe real de 1 h, o cookie de 20 min venceria antes da renovação. Teto de 10 min (como no Financeiro).
- Testes: `tests/api/test_s21_session.py` 9/0 (entrega com cookie HttpOnly/Secure/SameSite/Path/Max-Age; F5 troca o cookie e entra; sem cookie ou sessão vencida → 401 e cookie apagado; serviço fora → 503 sem apagar; cabeçalho exigido nas 3 rotas; sem passe, `aal1`, sem cadastro e passe da ponte recusados; renovação de outra pessoa recusada e encerrada; sair encerra e apaga; recurso desligado → 409); `app/tests/s21-login-smoke.cjs` 7/0; `tests/frontend` com contrato T-0014; pytest sem MariaDB 697/0; node 32/5 (as mesmas 5 falhas antigas da T-0012); Edge sem interface com API e login simulados: 11/11 (T-0014) e 12/12 (T-0013).
- 2026-10-21, conferência de Sérgio na publicação `t0014`: F5 manteve a sessão e a tela, mas reabriu a janela "Contexto de trabalho" (opção "Solicitar empresa e período sempre que eu entrar"). Correção (`t0014b`): a janela só abre na entrada de fato (senha e código, ou botão do Administrativo); F5 pela sessão do cookie ou pela ponte com a marca `r=1` (lida antes de limpar a URL) é continuação. Testes: contrato `test_t0014b_…`; Edge 13/13 (inclui: entrada pede o contexto; F5 não pede; F5 pela ponte `r=1` não pede; botão do Administrativo pede).
