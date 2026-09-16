# Product Backlog

## Atualização Phase 14 — Human UAT remediation

| ID | Prioridade | Item | Motivo | Bloqueia piloto? | Dependência |
|---|---|---|---|---|---|
| PB-049 | P1 | Manutenção autorizada de contas bancárias por Company | persistência existe, UI/caso de uso não | sim para OFX real | master-data, autorização, auditoria |
| PB-050 | P1 | Expandir Company (IE/IM, endereço, contatos) | campos ausentes no schema | avaliar piloto | domínio e migration dedicada |
| PB-051 | P1 | Criar Supplier/Vendor master quando requerido | domínio inexistente | não no sintético | incremento aprovado |
| PB-052 | P2 | Metadados genéricos de documento | número/descrição/observação/competência ausentes | não | contrato e migration |
| PB-053 | P2 | ZIP seguro de XML | traversal, limites e zip bomb | não | desenho de segurança |
| PB-054 | P2 | Destinos operacionais W008/W009 | módulos seguros não entregues | não | obrigações/conciliação |

## Atualização Phase 08

| ID | EPIC | STORY | PRIORITY | STATUS | TARGET_PHASE |
|---|---|---|---|---|---|
| PB-013 | EPIC-008 | Catálogo/regras/propostas reutilizando motor existente | P1 | DONE | PHASE 08 |
| PB-014 | EPIC-008 | Revisão/aprovação/rejeição com guardas existentes | P0 | DONE | PHASE 08 |
| PB-037 | EPIC-008 | Caso de uso auditável para nova revisão/edição | P1 | PLANNED | FUTURE_APPROVED_SCOPE |
| PB-038 | EPIC-008 | Persistir motivo seguro de rejeição, se aprovado | P2 | PLANNED | FUTURE_APPROVED_SCOPE |
| PB-039 | EPIC-008 | Proposta contábil a partir de fonte financeira | P1 | PLANNED | FUTURE_APPROVED_SCOPE |

PB-015 permanece não iniciado para a Fase 09.

## Atualização Phase 07

| ID | EPIC | STORY | PRIORITY | STATUS | TARGET_PHASE |
|---|---|---|---|---|---|
| PB-035 | EPIC-007 | Persistir/projetar matching e conciliação com autorização e auditoria | P1 | PLANNED | FUTURE_APPROVED_SCOPE |
| PB-036 | EPIC-005 | Agregar issues documentais ao detalhe fiscal sem duplicar exceção | P2 | PLANNED | PHASE 09+ |

## Atualização Phase 06

| ID | EPIC | STORY | PRIORITY | STATUS | TARGET_PHASE |
|---|---|---|---|---|---|
| PB-031 | EPIC-004 | Lista/detalhe de empresas autorizadas sem novo domínio | P1 | DONE | PHASE 06 |
| PB-032 | EPIC-005 | Inbox, filtros, paginação e detalhe documental seguro | P1 | DONE | PHASE 06 |
| PB-033 | EPIC-005 | Definir upload documental genérico | P1 | PLANNED | PHASE 07+ |
| PB-034 | EPIC-005 | Download e histórico por documento minimizados | P2 | PLANNED | PHASE 09+ |

Backlog inicial de productização, 14/09/2026. Somente a baseline documental está concluída. P0 = condição necessária para funcionamento seguro ou liberação de um escopo com segurança; P1 = jornada principal; P2 = melhoria/complemento; P3 = exploração futura. Não são prazos nem autorização para iniciar fases.

STATUS: DONE (entrega desta fase), PLANNED (não iniciado), BLOCKED (depende de gate externo/humano). “Reutilizar” reconhece implementação existente e evita recriar o backend. TARGET_PHASE referencia o [roadmap](PRODUCTIZATION_ROADMAP.md).

## Epics

| EPIC | Nome | Reuso / limite |
| --- | --- | --- |
| EPIC-001 | Design System | Prévia `ui/` revisável e brief aprovado. |
| EPIC-002 | Application Shell | API/OIDC existentes; sem shell autenticado. |
| EPIC-003 | Minha Visão | Consultas operacionais; agregações/persistência da visão não comprovadas. |
| EPIC-004 | Clients | Empresas e CompanyAccess existentes, não novo CRM. |
| EPIC-005 | Documents | Intake/evidência/storage existentes. |
| EPIC-006 | Fiscal Intelligence | NF-e 55 existente. |
| EPIC-007 | Financial Intelligence | OFX/CSV existentes; conciliação operacional parcial. |
| EPIC-008 | Accounting Intelligence | Catálogo/regras/propostas/workflow existentes. |
| EPIC-009 | Decision Line | AuditEvent/checkpoints; mapa de gaps no fluxo. |
| EPIC-010 | Portal & Operations Integration | Reutiliza o portal do Sistema A; não criar segundo portal no B. |
| EPIC-011 | Security Infrastructure | Controles locais e gates externos. |
| EPIC-012 | Observability | Métricas locais/runbooks/ensaio de restore. |
| EPIC-013 | Privacy & Legal | Controles internos; aprovações pendentes. |
| EPIC-014 | Commercial Website | Prévia site/ revisável; brief comercial. |
| EPIC-015 | Onboarding | Lifecycle de identidade existente; UX/operação comercial pendentes. |
| EPIC-016 | Billing & SaaS Operations | Sem billing implementado; definição comercial futura. |
| EPIC-017 | Serdial21 Connect Hub | Port canônico + conector Serdial21; sem acoplamento do core a n8n/Drive/APIs admin. |

## Stories

| ID | EPIC | STORY | PRIORITY | DEPENDENCY | STATUS | TARGET_PHASE |
| --- | --- | --- | --- | --- | --- | --- |
| PB-001 | EPIC-016 | Consolidar os nove documentos e inventário preservando gates e arquivos | P1 | Fechamento de engenharia | DONE | PHASE 01 |
| PB-002 | EPIC-016 | Revisar composição do RC: virtualenv antigo tracked, exemplo de homologação e prévia untracked; preparar pacote reproduzível preservando originais | P1 | PB-001 | PLANNED | PHASE 16 |
| PB-003 | EPIC-001 | Conciliar marca, slogan, cores e nomes da prévia; aprovar tokens e componentes acessíveis | P1 | PB-001 | PLANNED | PHASE 02 |
| PB-004 | EPIC-001 | Prototipar estados de automação, revisão humana, bloqueio e erro com texto além de cor | P1 | PB-003 | PLANNED | PHASE 02 |
| PB-005 | EPIC-002 | Integrar UX de sessão OIDC real, expiração/logout e falhas sem conceder acesso | P0 | PB-003; backend identity; IdP homologado | PLANNED | PHASE 04 |
| PB-006 | EPIC-002 | Implementar shell/seleção de empresa com CompanyAccess e testes negativos | P0 | PB-005; AuthorizationService | PLANNED | PHASE 04 |
| PB-007 | EPIC-003 | Entregar Minha Visão com ações prioritárias e agregados autorizados completos | P1 | PB-006; levantamento de contratos de agregação | DONE_SYNTHETIC | PHASE 05 |
| PB-008 | EPIC-003 | Adicionar/remover/mover/redimensionar widgets e salvar visão; revalidar permissões ao carregar | P2 | PB-007; persistência local sem dados operacionais | DONE_LOCAL_ONLY | PHASE 05 |
| PB-009 | EPIC-004 | Expor empresas autorizadas reutilizando a fronteira de acesso existente | P1 | PB-006 | PLANNED | PHASE 06 |
| PB-010 | EPIC-005 | Integrar upload por bytes, duplicidade, quarentena e consulta de evidência conforme contratos | P1 | PB-009; intake/API | PLANNED | PHASE 06 |
| PB-011 | EPIC-006 | Expor processamento NF-e 55 e exceções com rastreabilidade | P1 | PB-010; parser/importador existentes | DONE | PHASE 07 |
| PB-012 | EPIC-007 | Expor OFX, sinal e duplicidade; especificar gaps de conciliação antes de estender serviços | P1 | PB-010; banking/reconciliation | DONE_PARTIAL_RECONCILIATION_DEFERRED | PHASE 07 |
| PB-013 | EPIC-008 | Integrar catálogo/regras/propostas sem recriar o motor determinístico | P1 | PB-011; catálogo publicado | PLANNED | PHASE 08 |
| PB-014 | EPIC-008 | Validar revisão/aprovação/rejeição ponta a ponta com hash, versão, alçada, segregação, locks e idempotência | P0 | PB-013; workflow/API | PLANNED | PHASE 08 |
| PB-015 | EPIC-009 | Projetar Linha da Decisão a partir dos dados existentes, resolver gaps de DTO e preservar minimização | P1 | PB-014; PRODUCT_FLOW | PLANNED | PHASE 09 |
| PB-016 | EPIC-010 | Definir jornadas e contratos para reutilizar Portal/Operações A sem conceder aprovação contábil | P1 | PB-006; PB-010; Phase 09A; gates externos/jurídicos | PLANNED | PHASE 10 |
| PB-017 | EPIC-011 | Homologar CORS_ALLOWLIST, HTTPS_REVERSE_PROXY e HSTS | P0 | Infraestrutura autorizada; ENVIRONMENT_STRATEGY | BLOCKED | PHASE 11 |
| PB-018 | EPIC-011 | Homologar DISTRIBUTED_RATE_LIMIT e IDP_SESSION_REVOCATION | P0 | PB-017; IdP/provedor | BLOCKED | PHASE 11 |
| PB-019 | EPIC-012 | Entregar CENTRAL_METRICS e ALERT_TRANSPORT com ensaio de entrega | P0 | PB-017; observabilidade local | BLOCKED | PHASE 12 |
| PB-020 | EPIC-012 | Validar PRE_DEPLOY_BACKUP, hash e restore de banco/storage com evidências atuais | P0 | Operação autorizada; runbooks | BLOCKED | PHASE 12 |
| PB-021 | EPIC-011 | Ensaiar/aplicar cadeia faltante forward-only e comprovar MIGRATION_0012_VERIFIED antes do deploy | P0 | PB-020; CI; janela autorizada | BLOCKED | PHASE 12 |
| PB-022 | EPIC-013 | Obter AUTHORIZED_REAL_CORPUS com finalidade e escopo explícitos | P0 | Autorização humana | BLOCKED | PHASE 13 |
| PB-023 | EPIC-013 | Obter LEGAL_APPROVAL e PRIVACY_OPERATIONAL_APPROVAL para corpus, DSR, retenção, holds e cópias | P0 | Revisão jurídico-operacional; PB-020 | BLOCKED | PHASE 13 |
| PB-024 | EPIC-008 | Executar QA/UAT integrado e obter ACCOUNTANT_SIGNOFF | P0 | PB-014; entregas integradas; corpus permitido | AUTOMATED_PASS_HUMAN_SIGNOFF_PENDING | PHASE 14 |
| PB-025 | EPIC-015 | Planejar piloto real controlado, critérios de parada e recuperação; executar somente após GO humano | P1 | PB-017–024 e gates externos aplicáveis | BLOCKED | PHASE 15 |
| PB-026 | EPIC-014 | Produzir páginas/conteúdo do marketing brief com alegações verificáveis | P1 | PB-003; MARKETING_SITE_BRIEF | PLANNED | PHASE 03 |
| PB-027 | EPIC-015 | Criar onboarding guiado reutilizando lifecycle e aprovação de alçadas | P1 | PB-006; PB-023; piloto | PLANNED | PHASE 16 |
| PB-028 | EPIC-016 | Definir planos, cobrança, suporte e SaaS operations antes de escolher provedor/contrato | P2 | PB-023; resultados do piloto | PLANNED | PHASE 16 |
| PB-029 | EPIC-016 | Avaliar automações adicionais de billing após definição do modelo comercial | P3 | PB-028; escopo específico aprovado | PLANNED | PHASE 16 (avaliação) |
| PB-030 | EPIC-016 | Consolidar launch readiness e decisão formal comercial | P1 | PB-002; PB-025; PB-027–028; gates | BLOCKED | PHASE 16 |

Os itens P0 não aprovam gates: exigem evidência e responsável. Dados reais e exposição externa continuam NO_GO. Domínio permanece BLOCKED_FOR_HOMOLOGATION; especificação oficial, golden files e homologação são dependências externas a levantar na janela de integrações, sem história de export fictício. Billing, IA assistente, mobile e novas regras não são implementados nesta fase.

Fase 09 concluída para o piloto sintético: projeção read-only e entry points suportados. Antes de exposição, medir planos MySQL e decidir índice composto de auditoria; ação de revisão, motivo de rejeição, causalidade de locks e links W010 permanecem backlog explícito.

## Atualização Phase 09A — Integration Readiness

| ID | EPIC | STORY | PRIORITY | DEPENDENCY | STATUS | TARGET_PHASE |
| --- | --- | --- | --- | --- | --- | --- |
| PB-040 | EPIC-017 | Verificar runtime do Sistema A e congelar `/api/integrations/v1/*`, schemas e legados | P0 | acesso HOM e owner A | PLANNED | PHASE 10 / WAVE 0 |
| PB-041 | EPIC-017 | Projetar/implementar identidade M2M, HMAC, rotação, scopes e proteção de replay | P0 | secret store; owners Security | PLANNED | PHASE 10A / WAVE 1 |
| PB-042 | EPIC-017 | Implementar referência externa tenant-aware com correlação CNPJ e revisão de ambiguidade | P0 | contract freeze | PLANNED | PHASE 10A / WAVE 2 |
| PB-043 | EPIC-017 | Implementar outbox/inbox, idempotência por hash, retry, DLQ e reconciliação | P0 | PB-041 | PLANNED | PHASE 10A / WAVE 1 |
| PB-044 | EPIC-017 | Contratar e validar pull documental por URL curta, quarentena e evidência imutável | P0 | PB-041–043; storage HOM | PLANNED | PHASE 10A / WAVE 3 |
| PB-045 | EPIC-017 | Corrigir persistência do Kanban A e integrar `TASK_REQUIRED` sem autoridade contábil | P0 | owner A; PB-043–044 | PLANNED | PHASE 10A / WAVE 4 |
| PB-046 | EPIC-017 | Entregar callbacks minimizados de decisão e E2E sintético A HOM↔Hub HOM↔B HOM | P0 | PB-040–045 | PLANNED | PHASE 10A / WAVE 5 |
| PB-047 | EPIC-017 | Definir workflow cross-system de privacidade, retenção, legal hold e DSR | P0 | Privacy/Legal | BLOCKED | PHASE 13, antes de real data |
| PB-048 | EPIC-017 | Criar publicação documental/obrigações após upload admin→cliente seguro no A | P1 | PB-046; privacy/legal | PLANNED | FUTURE / WAVE 6 |

`EPIC-017 — Serdial21 Connect Hub` é um conector desacoplado do core. Phase 10 passa a **Portal & Operations Integration**; Phase 10A é a implementação futura do Hub em homologação. Nenhuma história foi iniciada pela Phase 09A.
