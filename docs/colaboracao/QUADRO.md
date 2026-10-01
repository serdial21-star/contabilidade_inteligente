# Quadro de tarefas

Protocolo: [README.md](README.md). Atualizado por quem mudar o estado de uma tarefa.

## Em andamento

| ID | Título | Estado | Com quem | Arquivo |
|---|---|---|---|---|
| T-0002 | CI verde: falsos positivos da varredura de segredos sem afrouxá-la | ACEITA (aguardando confirmação do usuário) | Usuário | [T-0002](tarefas/T-0002-ci-varredura-de-segredos.md) |

## Fila (ainda sem briefing; ordem sugerida, sujeita à decisão do usuário)

| Ordem | Tema | Origem | Sistema | Observação |
|---|---|---|---|---|
| 1 | Exigir cargo/permissão nas procedures e workflows "admin" de clientes; auditar troca de e-mail e documento; revogar sessões do cliente quando o e-mail mudar | Auditoria #3 | Sistema A (artefatos em `docs/integration`) | Exige ADR e ações do usuário no n8n/phpMyAdmin |
| 2 | Retenção, CORS e SQL parametrizado no workflow "[SECURITY] Validar Sessão de Funcionário" | Auditoria #7 | Sistema A | Ação do usuário no n8n |
| 3 | Onboarding não sobrescreve nome e e-mail do usuário compartilhado entre tenants | Auditoria #5 | Sistema B | Isolamento multi-tenant |
| 4 | Limite global da recuperação de senha não contar tentativas já bloqueadas; alerta | Auditoria #6 | Sistema A | — |
| 5 | Plano de migração de SHA-256 para Argon2id nas senhas | Auditoria #4; dossiê 26.1 | Sistema A | Exige ADR; depende do login do Sistema A |
| 6 | `state`/nonce na ponte de login e cabeçalhos anti-framing no Caddy | Auditoria #8 e #9 | A e B | — |
| 7 | Login legado de clientes (`Math.random`, SQL interpolado) | Dossiê mestre 26.1 e 32 | Sistema A | Exige ADR |
| 8 | Competência pelo fuso da empresa: filtros de período em UTC e data OFX sem fuso | [REFERENCIAS.md](REFERENCIAS.md), seção 3 | Sistema B | Possível defeito contábil; exige decisão sobre o fuso de referência |
| 9 | Formalizar fontes normativas versionadas (MOC/NT/XSD NF-e, OFX, IN RFB) e citá-las no código e nos ADRs | [REFERENCIAS.md](REFERENCIAS.md), seção 2 | Sistema B | Parte depende de você obter os documentos oficiais |
| 10 | Qualidade automática: adotar Ruff e verificador de tipos (mypy ou pyright) como dependência de desenvolvimento e no CI; alinhar o Python do CI (3.12) ao de produção (3.14) | Análise de ferramentas, 01/10/2026 | Sistema B | Muda dependências: exige justificativa conforme `AGENTS.md` seção 3 |
| 11 | Segundo limite de requisições por usuário autenticado, aplicado depois da verificação do token | T-0001, decisão de 01/10/2026 | Sistema B | Fazer antes de ampliar o número de usuários atrás do mesmo IP |
| 14 | Varredura de segredos não detecta credencial dentro de URL (`DATABASE_URL=mysql+pymysql://usuario:senha@host`), o tipo de vazamento mais provável neste projeto | Briefing da T-0002 | Sistema B | Exige tratar os placeholders existentes (`replace_me`, `SUA_SENHA`) sem allowlist |

## Concluídas

| ID | Título | Commit | Data |
|---|---|---|---|
| T-0001 | Rate limit por origem confiável e cache JWKS com validade | `14f3450` | 01/10/2026 |
