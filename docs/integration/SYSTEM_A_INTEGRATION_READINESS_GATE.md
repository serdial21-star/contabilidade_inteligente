# System A Integration Readiness Gate

## Atualização 2026-09-25 — Wave 0 e publicação interna autorizadas (ADR 0015)

Por decisão explícita do usuário, registrada em
[`docs/adr/0015-publicacao-interna-e-wave-zero-connect-hub.md`](../adr/0015-publicacao-interna-e-wave-zero-connect-hub.md), ficam autorizadas:

- a preparação da primeira publicação interna do Sistema B, reutilizando a
  ponte de login já aprovada;
- a Wave 0 de inventário, estabilização e congelamento de contratos do Connect
  Hub.

Esta atualização **não autoriza sincronização runtime de dados de negócio**.
Cliente, documento, tarefa, honorário, imposto ou outro dado não será
transmitido automaticamente até que o primeiro fluxo seja escolhido, os
contratos versionados sejam aprovados e a homologação correspondente passe.
O `NO_GO` abaixo permanece aplicável à implementação e ativação dessas conexões.

## Atualização 2026-09-24 — exceção pontual e nomeada (ADR 0014)

O veredito `NO_GO` abaixo **continua valendo integralmente** para sincronização
de dados de negócio, workflows do n8n, credencial M2M genérica e qualquer
outro item desta página. Por decisão explícita do usuário, registrada em
[`docs/adr/0014-ponte-login-sistema-a.md`](../adr/0014-ponte-login-sistema-a.md),
abre-se uma exceção estreita **somente** para uma ponte de identidade de
login (Sistema A confere sua própria sessão de funcionário e emite um token
OIDC de vida curta; o Sistema B verifica com o mecanismo que já existe). Essa
ponte não sincroniza dado de cliente, não usa fila, não persiste nada em lote
e é escopada a um único tenant fixo (Serdial21) — não é uma reabertura do
Connect Hub, é uma exceção nomeada para uma peça específica.

## Resultado

| Critério mínimo | Resultado | Evidência/pendência |
| --- | --- | --- |
| Client master contract | `PARTIAL` | tabela/campos somente documentados |
| CNPJ correlation | `PARTIAL` | normalização desenhada; formato runtime desconhecido |
| Document receipt contract | `PARTIAL` | frontend/workflow/schema ausentes |
| Document reference/transport | `BLOCKER` | secure pull curto não demonstrado |
| Central Operations create | `PARTIAL` | v3/v5 conflitantes, sem teste |
| Central Operations update persists | `FAIL` | v1/v5 e persistência não verificadas |
| Authorization fail closed | `FAIL` no gate | falta evidência/teste positivo e negativo |
| Client route security | `PARTIAL` | route registry/guard ausente do workspace |
| Canonical endpoint map | `PARTIAL` | inventário pronto; sete conflitos runtime |
| M2M API hosting | `PARTIAL` | host n8n responde; API dedicada não demonstrada |
| M2M credential support | `MISSING` | nenhuma credencial de serviço demonstrada |
| Audit | `UNKNOWN` | tabela/população/writes não verificados |
| CORS browser readiness | `PARTIAL` | não testado por webhook/ambiente |
| Homologation | `MISSING` | nenhum conjunto isolado fornecido |

## Evidência aceita para reabrir o gate

- source tag do frontend e exports n8n redigidos;
- schema-only MySQL/read-only, sem dados de cliente;
- homologação separada para frontend, n8n, DB, Drive, credentials e logs;
- fixtures totalmente sintéticas;
- testes de login/session/401, route guards e permissions fail-closed;
- testes Central Ops create→read→update→read→delete/soft-delete;
- teste de intake documental com hash e referência segura;
- inventário de `Respond to Webhook`, CORS e SQL dos workflows relevantes;
- evidência de audit log sem payload sensível.

## Política de aprovação

O host n8n acessível não satisfaz o gate. Nenhum endpoint será `ACTIVE_VERIFIED` até source, workflow ativo e teste HOM convergirem. Alegação de dossiê permanece documental. Falta de evidência obrigatória é falha de readiness, mesmo sem confirmação de defeito.

## Alterações desta fase

- produção: nenhuma;
- banco/schema: nenhum;
- n8n/workflows: nenhum;
- credenciais: nenhuma;
- dados reais: nenhum;
- testes funcionais: não executados por ausência de source/HOM do Sistema A;
- probe público: apenas HEAD/GET da UI raiz n8n, sem autenticação nem webhook.

## Próxima fase recomendada

Uma tarefa isolada **SYSTEM A HOMOLOGATION & VERIFICATION PACKAGE** deve fornecer os artefatos e o ambiente acima. Não iniciar Connect Hub, Phase 10 ou conexão com o Sistema B.

**PHASE 09B — SYSTEM A RUNTIME VERIFICATION: BLOCKED**

**SYSTEM A: NOT_READY_FOR_CONNECT_HUB_MVP**

**INTEGRATION: NO_GO**

**NEXT RECOMMENDED PHASE: SYSTEM A HOMOLOGATION & VERIFICATION PACKAGE**
