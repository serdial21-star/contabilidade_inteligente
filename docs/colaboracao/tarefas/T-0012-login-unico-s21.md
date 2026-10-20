# T-0012 — S21 Contábil entra pelo login único S21 (ADR 0025 do Financeiro, etapa 1)

| Campo | Valor |
|---|---|
| Estado | IMPLEMENTADA — aguardando publicação na VPS e conferência do usuário |
| Origem | ADR 0025 do Sistema C ("login único S21"), aceito por Sérgio em 2026-10-20 17:40 (D-100 do C) |
| Sistema | Sistema B |
| Exige ADR | sim: **ADR 0021 do B** (revisa o ADR 0014 — a ponte do A deixa de ser a entrada), escrito junto com a implementação |
| Exige ação do usuário | sim: aprovar; convidar no login S21 quem usa o Contábil; publicar na VPS (comandos preparados pelo Claude) |

---

## 1. Briefing (Claude)

### Problema

Hoje a única porta do Contábil é a ponte do portal (ADR 0014): o portal confere o login fraco do n8n e emite um passe para o Contábil. Com o ADR 0025, todos os sistemas S21 usam o mesmo login (Supabase do Financeiro: São Paulo, plano Pro, bcrypt, código no celular, senha vazada conferida, passe de 15 min, chave RS256).

### Escopo

1. **Servidor do B aceita dois emissores durante a transição:** o login S21 (`https://bmpzxbihsvflqamdsjsp.supabase.co/auth/v1`, audiência `authenticated`, RS256, JWKS público) e a ponte atual (até a etapa 3 do ADR 0025, quando a ponte é desligada). Configuração por ambiente; nenhum segredo no código.
2. **Regras do passe S21 no servidor:** recusar `role` diferente de `authenticated`, `is_anonymous` verdadeiro e `aal` diferente de `aal2` (código no celular obrigatório para a equipe), além do que já é conferido (assinatura, emissor, audiência, validade, `kid`).
3. **Cadastro continua obrigatório:** o `sub` do login S21 precisa estar vinculado a um usuário do B (`scripts/bootstrap_user_access.py`, com o emissor S21). Sem vínculo: 403, como hoje (T-0011).
4. **Tela de entrada do B** com o login S21: e-mail, senha e código do celular, pelo serviço de login do Supabase; passe **só na memória** (recarregar pede o código de novo, mas a re-entrada automática da T-0010 continua valendo para quem vem do portal pela ponte, enquanto ela existir). Sem `localStorage`/`sessionStorage` para passe (teste 4 do shell-smoke).
5. **Testes:** passe S21 válido e vinculado → entra; `aal1` → 401; anônimo → 401; outro emissor → 401; sem vínculo → 403; ponte continua aceita enquanto configurada.

### Fora do escopo

Desligar a ponte (etapa 3); clientes do portal (etapa 4); qualquer dado de negócio entre sistemas.

### Pergunta ao usuário (decidir na aprovação)

**Como a equipe abre o Contábil depois da mudança:**
- **(a) Recomendado — tela própria do Contábil com o login S21:** a pessoa digita e-mail, senha e código ao abrir o Contábil (como no Financeiro). Mais simples e mais seguro.
- **(b) Passar direto do portal, sem digitar de novo:** o portal entrega ao Contábil o passe S21 da pessoa. Mais cômodo, mas o mesmo passe também abre o Financeiro; fica para depois, se quiser, com análise própria.

## 2. Aprovação

2026-10-20: Sérgio, "Aprovo T-0012, opção a" (tela própria do Contábil com o login S21).

## 3. Resultado (Claude)

- Servidor: `OidcJwtVerifier` com `fixed_tenant_id` e `claims_check`; `IssuerRoutingVerifier` (escolhe pelo emissor); `s21_login_claims_acceptable` (authenticated, não anônimo, aal2); configuração `S21_LOGIN_URL`, `S21_LOGIN_PUBLISHABLE_KEY`, `S21_LOGIN_TENANT_ID` (as três juntas; HTTPS fora de local/test; em homologation/production basta OIDC **ou** S21); `GET /api/v1/identity/login-config` público (endereço e chave publicável).
- Tela: `app/s21-login.js` (senha → código → passe aal2; renovação; saída), formulário na tela de entrada, `#entrar` abre direto, renovação 60 s antes de vencer, sem Web Storage; `connect-src` libera só `https://bmpzxbihsvflqamdsjsp.supabase.co` (index.html e Caddyfile); `deploy/web/config.js` com `s21Login: true`; `compose.yaml` passa as 3 variáveis.
- ADR 0021 do B (revisa o ADR 0014 e a regra "tela não pede senha", com a razão).
- Testes: `tests/api/test_s21_login.py` 13/0 (aal2 entra; aal1, sem aal, anônimo, role anon, outra audiência, outro emissor, vencido → 401; outra chave → 401; sem cadastro → 403; ponte continua; configuração e rota pública); `app/tests/s21-login-smoke.cjs` 5/0; pytest sem MariaDB 686/0. Testes de tela antigos ajustados (shell-smoke 8, `test_app_shell`) para a regra nova.
- Pré-existentes, não causados por esta tarefa: os mesmos 5 subtestes node (dashboard 2, intelligence 1, operational 1, shell 11), conferidos antes e depois; `tests/mariadb/test_migration_0017.py` com erro de sintaxe no Python 3.14 (coleta falha também sem a mudança); testes `tests/mariadb` exigem MariaDB descartável (não rodados).
