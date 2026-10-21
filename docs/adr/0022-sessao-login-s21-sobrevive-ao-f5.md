# ADR 0022 — Sessão do login S21 que sobrevive ao F5 (emenda ao ADR 0021, item 4)

## Status

Aceita em 2026-10-21 por decisão de Sérgio: "essa era a regra, já mudamos no financeiro e está funcionando, então mude a regra e registre… o F5 não vai para o login, atualiza e mantém na página que estava antes". Mesma decisão do Sistema C (D-059, emenda ao ADR 0003 item 6; D-101 do C).

## Contexto

O ADR 0021 (T-0012) deixou passe e renovação só na memória da página: o F5 pedia senha e código de novo. A T-0013 levou o F5 à tela do login S21, e não à ponte. Para a equipe, isso é o mesmo que "sair a cada F5". O Financeiro resolveu o mesmo problema em 2026-10-14 (EXEC-34, D-059) e está em produção.

## Decisão

1. Depois do código do celular, a tela entrega a renovação (refresh token do Supabase) ao servidor do B (`POST /api/v1/identity/session`). O servidor renova uma vez no Supabase e confere que o passe novo é do login S21, tem o código do celular (`aal2`) e é **da mesma pessoa** (emissor, sujeito e escritório). Depois guarda a renovação num cookie **HttpOnly, Secure, SameSite=Strict**, restrito a `/api/v1/identity/session`, por **20 min** (`S21_SESSION_COOKIE_MAX_AGE_SECONDS`, como no Financeiro).
2. F5 ou recarga: `POST /api/v1/identity/session/refresh` devolve passe novo pelo cookie, que é trocado a cada uso. A tela volta à mesma rota, com a lista de parâmetros da T-0010. Sem cookie válido, a resposta é 401, o cookie é apagado e a tela segue a T-0013: login S21 em `#entrar` ou ponte.
3. Depois da entrega, **só o servidor renova**: a tela pede passe novo a cada 10 min no máximo. Uma renovação em paralelo pelo navegador seria vista como reuso e derrubaria a sessão.
4. Sair: `POST /api/v1/identity/session/logout` encerra no Supabase (melhor esforço) e apaga o cookie.
5. As três rotas exigem o cabeçalho `X-S21-Session: 1`, que um formulário ou link de outro site não envia. Passe da ponte do A não abre sessão de cookie. Sem o login S21 configurado, as rotas respondem 409 e a sessão segue só na memória.
6. O passe de acesso continua só na memória (sem Web Storage). A página nunca lê o cookie. A renovação nunca volta à página nem aparece em registro.

## Consequências

- Emenda o ADR 0021 item 4 ("passe e renovação só na memória"): a renovação passa a morar no cookie do servidor.
- Chamada ao Supabase fora de transação de negócio. Indisponibilidade do serviço de login → 503 sem apagar o cookie.
- Diferença em relação ao Financeiro: o B não tem saída por inatividade na tela (D-020 do C). Com a página aberta, a sessão segue renovando. Fechada por mais de 20 min, o cookie vence.
