# Serdial21 Integration Readiness

Data da análise: 2026-09-15. Escopo: Phase 09A, exclusivamente documental e arquitetural.

## Pre-flight e preservação do workspace

- branch: `main`;
- últimos commits: `547133d` (Phase 08), `92c18d1` (Phase 07), `dacd068` (Phase 05), `8c27bb3` (Phase 04), `7a37fc2` (Phase 03);
- os três inputs existem no caminho canônico `docs/integration-input/`;
- o `git status --short` inicial já continha alterações de código, testes e documentos da Phase 09, além de arquivos untracked. Elas foram tratadas como trabalho preexistente e preservadas;
- a Phase 09A alterou somente os oito documentos em `docs/integration/` e os três documentos de planejamento explicitamente permitidos. Nenhum código de produção, teste, banco, migration, workflow, segredo ou deploy foi criado/alterado por esta fase.

## Conclusão executiva

**INTEGRATION: CONDITIONAL_GO.** A arquitetura é **APPROVED_WITH_ADJUSTMENTS**: o Sistema A permanece o mestre operacional e do relacionamento com o cliente; o Sistema B permanece o mestre da inteligência e decisão contábil. Bancos continuam independentes, sem escrita direta cruzada. A comunicação deve passar por contratos versionados em `/api/integrations/v1/*`, por uma camada anticorrupção e pelo Connect Hub, com entrega *at least once* e consumidores idempotentes.

O desenho está pronto para planejamento, não para conexão. Antes do MVP são necessários: inventário runtime e congelamento dos contratos do Sistema A; identidade M2M; autorização fail-closed; referência externa; transporte documental seguro; entrega durável/DLQ; ambientes de homologação isolados. Dados reais e exposição externa continuam `NO_GO`.

## Sistemas comparados

| Sistema | Papel-alvo | Evidência | Prontidão |
| --- | --- | --- | --- |
| A — Serdial21 Operacional | Portal, cadastro administrativo, relacionamento, documentos operacionais, tarefas, tickets, agenda, obrigações, honorários e comunicação | Três dossiês; nenhum código/runtime do Sistema A disponível | `PARTIAL_EVIDENCE` |
| B — Contabilidade Inteligente | Evidência processada, NF-e/OFX, regras, propostas, revisão, aprovação, locks, auditoria e Linha da Decisão | Código e documentação deste repositório | `READY` para desenho; exposição/real data pendentes |

## Fontes e classificação

Foram lidos integralmente:

- `docs/integration-input/DOSSIE_INTEGRACAO_SERDIAL21.md` — fonte documental mais recente para o Sistema A;
- `docs/integration-input/DOSSIE_SERDIAL21.md` — levantamento técnico anterior;
- `docs/integration-input/PROMPT_DIAGNOSTICO_SERDIAL21.md` — roteiro/hipóteses de diagnóstico, não resultado runtime;
- arquitetura, segurança, documentos, produto e contratos do Sistema B no repositório.

Classificações usadas: `DOCUMENTED` é alegado nos dossiês; `VERIFIED_IN_AVAILABLE_CODE` exige código do Sistema A (não disponível); `NOT_VERIFIED` exige teste/runtime; `CONFLICTING_EVIDENCE` indica fontes documentais incompatíveis; `VERIFIED_IN_REPOSITORY` aplica-se ao Sistema B.

## Achados do Sistema A

| Achado | Classificação | Observação |
| --- | --- | --- |
| SPA React/Vite; portal `/login`; painel `/admin/login` | `DOCUMENTED` | Não verificado em build/runtime. |
| n8n self-hosted como middleware/webhooks | `DOCUMENTED` | Base documentada em `n8n.serdial21.com/webhook`; não testada. |
| MySQL Hostinger | `DOCUMENTED` | Schema, constraints e backups não verificados. |
| Google Drive para arquivos e MySQL para metadados | `DOCUMENTED` | IDs de pasta divergem entre fontes. |
| Supabase Edge Functions/Storage, SMTP e WhatsApp/Z-API | `DOCUMENTED` | Credenciais e disponibilidade não verificadas. |
| Tokens de navegador em `localStorage` | `DOCUMENTED` | Risco de produção; proibido para M2M. |
| Upload admin→cliente ausente | `DOCUMENTED` | Bloqueia publicação documental integrada. |
| Atualização Kanban pode responder sucesso sem persistir | `DOCUMENTED` | Bloqueia integração confiável de tarefas. |
| Rotas de cliente sem guards e fallback permissivo | `DOCUMENTED` | Bloqueador de segurança da produção; protocolo M2M deve ser separado. |
| Estado efetivo de endpoints, auditoria, CORS e E2E | `NOT_VERIFIED` | Exige homologação/runtime. |

Nenhuma alegação do Sistema A alcança `VERIFIED_IN_AVAILABLE_CODE`, pois seu código não faz parte do material disponível.

## Achados do Sistema B

O repositório verifica (`VERIFIED_IN_REPOSITORY`) monólito modular FastAPI/SQLAlchemy, OIDC e contexto de autorização, `Tenant`, `Company`, `CompanyAccess`, intake/evidência documental, NF-e 55, OFX, regras, contas, propostas, workflow humano, `AccountLock`, `AuditEvent`, projeções operacionais e Linha da Decisão. Limitações relevantes: IdP de produção pendente; API de upload/download genérico incompleta; ausência de principal M2M e de mapeamento genérico de referências externas; Domínio bloqueado para homologação; dados reais e exposição externa não autorizados.

## Conflitos entre dossiês

Há **10 grupos de conflito documental**. A fonte mais recente orienta descoberta, mas não substitui verificação runtime.

| # | Fonte A | Fonte B | Conflito | Evidência mais recente | Verificação requerida |
| --- | --- | --- | --- | --- | --- |
| 1 | Integração: criação `/admin-create-item-v5` | Diagnóstico: criação `v3` | Versão de criação | Integração (`v5`) | Lista/export dos workflows ativos e chamada em homologação |
| 2 | Integração: atualização `v5` | Dossiê técnico/diagnóstico: atualização `v1` | Versão e persistência | Integração (`v5`, com falha relatada) | Teste de persistência e leitura posterior |
| 3 | Integração: dashboard/agenda `v2` | Fontes antigas: `v1` | Versões operacionais | Integração (`v2`) | Rotas efetivas e consumidores do frontend |
| 4 | Integração: `/admin/impostos-v2` | Técnico: `/admin/impostos` e `/admin/novo-imposto` | Caminho/método de impostos | Integração (`v2`) | Workflow ativo e contrato |
| 5 | Integração: `/admin/equipe-v2` | Técnico: `/admin/funcionarios` | Recurso de equipe | Integração (`equipe-v2`) | Workflow ativo e payload |
| 6 | Integração: `/portal/*` | Diagnóstico: `/cliente/*` | Namespace do portal | Integração (`/portal/*`) | Build publicado e rede do navegador |
| 7 | Integração: `drive_folder_id` | Técnico: `id_pasta_raiz` | Coluna de pasta Drive | Integração | `SHOW COLUMNS`/migration autorizada em homologação |
| 8 | Integração: `admin_sessoes` | Técnico: `security_sessoes_funcionarios` | Tabela de sessões | Integração | Schema e workflows ativos |
| 9 | Integração: `tasks_master` | Técnico: `tarefas_internas` | Modelo de tarefas | Integração | Schema, ownership e CRUD efetivo |
| 10 | Dossiê técnico usa `entregas_master` | Outro material indica módulo removido/alterado | Existência/uso de entregas | Inconclusiva | Consulta de schema e tráfego runtime |

## Inventário canônico dos endpoints documentados

Todos permanecem `NEEDS_RUNTIME_VERIFICATION`; `CONFIRMED_BY_DOC` significa apenas presença em documento.

| Path documentado | Método | Consumidor | Versão | Auth | Status documental | Fonte | Conflito | Relevância |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `/admin-create-item-v3` / `v5` | não congelado | Admin | v3/v5 | token admin documentado | `CONFLICTING` | Diagnóstico / Integração | versão | Não reutilizar; candidato legado |
| `/admin-update-item-v1` / `v5` | não congelado | Admin | v1/v5 | token admin | `CONFLICTING` | Técnico / Integração | versão e persistência | Tarefas; bloqueia Wave 4 |
| `/admin/dashboard-v1` / `v2` | GET documentado | Admin | v1/v2 | token admin | `CONFLICTING` | múltiplas | versão | Sem uso no MVP |
| `/admin/agenda-v1` / `v2` | não congelado | Admin | v1/v2 | token admin | `CONFLICTING` | múltiplas | versão | Later |
| `/admin/impostos`, `/admin/novo-imposto`, `/admin/impostos-v2` | misto | Admin | sem versão/v2 | token admin | `CONFLICTING` | Técnico / Integração | paths | Later: obrigações/guias |
| `/admin/funcionarios` / `/admin/equipe-v2` | não congelado | Admin | sem versão/v2 | token admin | `CONFLICTING` | Técnico / Integração | recurso | Fora do MVP |
| `/cliente/*` / `/portal/*` | misto | Portal | sem versão | token cliente | `CONFLICTING` | Diagnóstico / Integração | namespace | Portal será reutilizado, não chamado pelo B |
| `/admin/upload-documento-cliente` | POST esperado | Admin | sem versão | token admin | `LEGACY_CANDIDATE` ausente | Integração | implementação ausente | Bloqueia publicação na Wave 6 |
| `/contabil/*` | proposta | Integração | não definido | API key sugerida | `NEEDS_RUNTIME_VERIFICATION` | Integração | não implementado | Substituído pelo padrão canônico |

### Inventário complementar por capacidade

Para não transformar hipóteses antigas em contratos, método e auth ficam “não congelado” quando os dossiês não são consistentes. Cada path abaixo é somente `CONFIRMED_BY_DOC` e `NEEDS_RUNTIME_VERIFICATION`.

| Capacidade | Paths documentados | Consumidor / versão | Auth documentada | Fonte e conflitos | Relevância |
| --- | --- | --- | --- | --- | --- |
| Login/recuperação portal | `/portal-serdial-v2`, `/portal/me-v2`, `/portal/solicitar-senha`, `/portal/redefinir-senha` | Portal; v2/mista | token cliente após login | Integração + Técnico; fontes antigas usam namespace `/cliente/*` | Não reutilizar em M2M |
| Tickets portal | `/portal/meus-chamados-v2`, `/portal/abrir-ticket-v2`, `/portal/detalhe-chamado`, `/portal/complementar-chamado` | Portal; v2/mista | token cliente | Integração + Técnico | Portal A permanece owner |
| Documentos portal | `/portal/meus-documentos-v2`, `/portal/detalhe-documento`, `/portal/complementar-documento`, `/portal/receber-arquivo-v2` | Portal; v2/mista | token cliente | Integração + Técnico | Origem futura de `DOCUMENT_RECEIVED` |
| Conteúdo/obrigações portal | `/portal/certidoes-v2`, `/portal/livros-contabeis-v2`, `/portal/obrigacoes-v2` | Portal; v2 | token cliente | Integração + Técnico; diagnóstico usa `/cliente/*` | Wave 6/later |
| Impostos/honorários portal | `/portal/impostos-v2`, `/portal/pagar-imposto-v2`, `/portal/honorarios-v2`, `/cliente/honorarios-v2`, `/cliente/certidoes-v2`, `/cliente/livros-v2`, `/cliente/obrigacoes-v2` | Portal; v2 | token cliente | Integração/Técnico/Diagnóstico; namespaces conflitantes | Wave 6/later |
| Login/recuperação admin | `/admin/login-v2`, `/admin/solicitar-senha` | Admin; v2/mista | token admin após login | 3 fontes | Não reutilizar em M2M |
| Dashboard/Kanban | `/admin-dashboard-v1`, `/admin-dashboard-v2`, `/admin-kanban-v3`, `/admin-create-item-v3`, `/admin-create-item-v5`, `/admin-update-item-v1`, `/admin-update-item-v5`, `/admin-delete-item-v3` | Admin; v1/v2/v3/v5 | token admin | 3 fontes; conflito forte/persistência | Tarefas Wave 4 somente via API dedicada |
| Agenda/options | `/admin-agenda-v1`, `/admin-agenda-v2`, `/admin-clientes-options-v1`, `/admin-funcionarios-options-v1` | Admin; v1/v2 | token admin | múltiplas fontes | Agenda fora do MVP; options não são integração |
| Clientes | `/admin/clientes-v2`, `/admin/novo-cliente-v2` | Admin; v2 | token admin | Integração + Técnico + Diagnóstico | Fonte do evento, não endpoint a reutilizar |
| Equipe | `/admin/equipe-v2`, `/admin/funcionarios`, `/admin/novo-funcionario`, `/admin/editar-funcionario` | Admin; v2/sem versão | token admin | múltiplas; nomenclatura conflitante | Fora do MVP |
| Permissões | `/admin/permissoes/funcionario`, `/admin/permissoes/funcionario/salvar`, `/admin/permissoes/cliente`, `/admin/permissoes/cliente/salvar` | Admin; sem versão | token admin | múltiplas; fallback permissivo relatado | Bloqueador segurança A; não fonte de auth B |
| Tickets admin | `/admin/tickets`, `/admin/tickets-v2`, `/admin/responder-ticket-v2` | Admin; sem versão/v2 | token admin | diagnóstico vs dossiês | Later |
| Documentos admin | `/admin/documentos-v2`, `/admin/enviar-inbox`, `/admin/upload-documento-cliente`, `/admin/upload-documentos` | Admin; v2/mista | token admin | upload alvo ausente; nomes variam | Wave 6; não reutilizar diretamente |
| Impostos admin | `/admin/impostos`, `/admin/impostos-v2`, `/admin/novo-imposto`, `/admin/novo-imposto-v2` | Admin; mista | token admin | fontes conflitantes | Wave 6/later |
| Honorários admin | `/admin/honorarios-v2`, `/admin/honorarios-parcelas-v2`, `/admin/honorarios-servicos-v2` | Admin; v2 | token admin | integração/diagnóstico | Fora do B |
| Fiscal IA admin | `/admin/fiscal`, `/admin/fiscal/upload-xml`, `/admin/fiscal/listar`, `/admin/fiscal/conferir` | Admin; sem versão | token admin | fontes parciais | Duplicação a evitar; não integrar core B aqui |
| Atalhos/arquivos | `/admin/atalhos`, `/listar-arquivos` | Admin; sem versão | token admin | integração/técnico | Fora do MVP |
| Integração sugerida antiga | `/contabil/sync-clientes`, `/contabil/lancar-obrigacao`, `/contabil/publicar-documento`, `/contabil/lancar-imposto`, `/contabil/documentos-recebidos`, `/contabil/baixa-pagamento`, `/contabil/webhook-eventos` | Integração; sem versão explícita | API key/IP sugerida | somente dossiê recente; proposta, não runtime | `LEGACY_CANDIDATE`; substituir por `/api/integrations/v1/*` |

Métodos indicados como GET/POST em material antigo não são considerados congelados porque o conjunto de fontes diverge. O freeze deve produzir OpenAPI/event schemas e registrar cada método efetivo.

Rotas administrativas/browser não são contratos de integração. O inventário completo de produção deve ser gerado pelo dono do Sistema A antes do freeze.

## Aptidão, bloqueios e separação de riscos

| Item | Classificação | Consequência |
| --- | --- | --- |
| Contratos/versões conflitantes | `BLOCKS_INTEGRATION` | Impede integração estável. |
| Credencial M2M inexistente | `BLOCKS_INTEGRATION` | Proíbe conexão. |
| Referência externa ausente no B | `BLOCKS_INTEGRATION` | `EXTERNAL_REFERENCE_GAP`. |
| Transporte documental e URLs curtas não contratados | `BLOCKS_INTEGRATION` | Impede ingestão segura. |
| Entrega durável, idempotência ponta a ponta e DLQ não implementadas | `BLOCKS_INTEGRATION` | Risco de perda/duplicidade. |
| Kanban sem persistência confiável | `BLOCKS_INTEGRATION` antes da Wave 4 | Tarefa pode desaparecer. |
| Upload admin→cliente ausente | `BLOCKS_INTEGRATION` antes da Wave 6 | Não bloqueia MVP-1 a MVP-5. |
| Guards/fallback permissivo/localStorage/logout | `BLOCKS_PRODUCTION_ONLY` e `SHOULD_FIX` | Bloqueia portal seguro, não o protocolo backend isolado. |
| CORS | `BROWSER_RUNTIME_RISK` | Não é bloqueio M2M backend-to-backend. |
| Auditoria/E2E incertos | `BLOCKS_INTEGRATION` para piloto/produção | Evidência obrigatória. |
| Domínio export | `NON_BLOCKING` para este MVP | Continua `BLOCKED_FOR_HOMOLOGATION`. |

## Topologia recomendada

`Portal/Admin A → API própria A → DB A/Drive A → Outbox/Connect Hub → /api/integrations/v1 do B → aplicação B → DB/storage B`

Retornos seguem eventos do B pelo Hub até API própria do A. Não há FK cruzada, credencial de navegador, acesso direto de escrita ou regra contábil no n8n. Leitura direta de banco é proibida no MVP; view read-only pode ser avaliada somente como fallback temporário de reconciliação, com owner, minimização e retirada planejada.

## Decisões

- `DATABASE_OWNERSHIP_BOUNDARY: PASS` no desenho; implementação de APIs próprias ainda requerida.
- `DIRECT CROSS-SYSTEM WRITES: PROHIBITED`.
- `DATABASE MERGE: NOT_RECOMMENDED`.
- `N8N CONNECT HUB ROLE: RECOMMENDED_WITH_LIMITS`.
- `CLIENT CORRELATION: READY_DESIGN`; CNPJ normalizado + referência externa, nunca PK/FK cruzada.
- `EXTERNAL REFERENCE STRATEGY: READY_DESIGN`; capacidade persistente no B é gap de implementação.
- `DOCUMENT TRANSPORT: short-lived download URL/secure pull`, seguida de evidência imutável controlada pelo B.
- `PORTAL REUSE: RECOMMENDED`; não duplicar portal no B.
- `CROSS_SYSTEM_PRIVACY_WORKFLOW: FUTURE_DESIGN_REQUIRED` antes de dados reais.
- `ROADMAP_CHANGE: ADJUSTED`; Phase 10 vira Portal & Operations Integration, com implementação do Hub separada em 10A.

## Gate Phase 09A

Os artefatos de responsabilidade, ownership, identidade, documentos, Hub, versionamento, segurança M2M, idempotência, eventos, tarefas, banco, homologação, P0 e roadmap estão prontos. Não houve uso de dados reais, segredo, banco, migration, workflow, deploy ou alteração de código nesta fase.

**PHASE 09A — INTEGRATION READINESS: PASS**  
**INTEGRATION: CONDITIONAL_GO**  
**CONNECT HUB IMPLEMENTATION: READY_TO_PLAN**

## Atualização 2026-09-21 — nova evidência, decisão inalterada

Um relatório de varredura de código de terceiros do frontend/Edge Functions do Sistema A foi recebido (`docs/integration-input/RELATORIO_VARREDURA_LOVABLE_20260921.md`) — a primeira evidência de nível código-fonte disponível a este workspace. Ele fortalece, sem contradizer, o desenho arquitetural acima: confirma que tokens de navegador/autorização do Sistema A não podem ser tratados como confiáveis pelo B (consistente com a decisão já registrada de credencial M2M própria) e adiciona evidência positiva de fail-open onde antes havia apenas ausência de evidência. Não altera `DATABASE_OWNERSHIP_BOUNDARY`, `PORTAL REUSE` nem `ROADMAP_CHANGE`. O detalhamento está em `SYSTEM_A_SECURITY_GAPS.md`, `SYSTEM_A_RUNTIME_VERIFICATION.md`, `CONNECT_HUB_PREREQUISITES.md` e `CANONICAL_OPERATIONAL_API_MAP.md`. A Phase 09B permanece `BLOCKED`/`NO_GO`; esta atualização não a reabre nem a resolve.
