# Serdial21 — Índice e Rastreabilidade da Engenharia do Produto

| Artefato | Estado | Conteúdo |
|---|---|---|
| [01 — Visão e Escopo](./01-fase-visao-e-escopo.md) | **Aprovado v1.0** | DAT-01 a DAT-10, autoridade por domínio e verticais XML/bancária |
| [02–03 — Arquitetura Macro e Domínios](./02-03-arquitetura-macro-e-dominios.md) | **Aprovado v1.0** | Estilo, componentes, bounded contexts, fluxos, estados, eventos e permissões macro |
| [04 — Modelo de Dados](./04-modelo-dados-conceitual-logico.md) | **Aprovado v1.0** | Entidades, relacionamentos, autoridades, versões, estados, invariantes e idempotência |
| [10 — Arquitetura Modular Python](./10-arquitetura-modular-python.md) | **Aprovado v1.0** | Pacotes, dependências, contratos, transações, conectores, IA e testes |
| [14 — Backlog Técnico MVP](./14-backlog-tecnico-mvp.md) | **Aprovado como base v1.0** | Slices, épicos, itens P0/P1, dependências, testes perigosos, DoD e métricas |
| [15 — Cronograma de Desenvolvimento](./15-cronograma-desenvolvimento-mvp.md) | **Proposto v0.2** | Equipe-base, fases, datas, entregas, caminho crítico, gates e critérios de go-live |

## Baseline aprovada

- MVP como camada inteligente integrada, preparado para evolução a sistema principal.
- Autoridade externa: escrituração, saldos e fechamento oficiais.
- Autoridade Serdial21: evidências, canônico, regras, DE/PARA, propostas, workflow, aprovações, integrações, IA e auditoria.
- Duas verticais: XML/documentos estruturados e movimentação bancária/extratos.
- Todo efeito contábil exige aprovação humana no piloto.
- Tenant é o escritório; empresa/estabelecimento são subescopos; acesso por TenantMembership e CompanyAccess.
- Integração separa modelo canônico, layout versionado e conector específico.
- M19 — Workflow, Pendências e Aprovações — é transversal e obrigatório.
- Dados de clientes não treinam modelos externos por padrão.
- Desenvolvimento por fatias verticais completas.

## Matriz de rastreabilidade DAT → engenharia

| Decisão aprovada | Arquitetura/domínios | Dados | Python | Backlog |
|---|---|---|---|---|
| DAT-01 — camada integrada evolutiva | ARQ-01, ARQ-05; pré-ledger | Ledger, Account, JournalEntry/Line, Period, observações externas | `accounting_core`, `accounting_controls` | EP2, EP6, S1–S6 |
| DAT-02 — XML + banco | Fluxos 6.1/6.2 | FiscalDocument, BankStatement/Transaction, evidências | `fiscal_documents`, `banking`, `reconciliation` | EP3, EP4, S2–S4 |
| DAT-03 — autoridade por domínio | Seção 3, ARQ-05 | DomainAuthorityPolicy, ExternalReference/Observation | `company_registry`, contratos de autoridade | MDM-201, COA-204, INT-910 |
| DAT-04 — personas/alçadas | access_control e M19 | Membership, CompanyAccess, Role/Permission/Binding | `access_control`, `workflow_m19` | EP1, EP7, DEC-007 |
| DAT-05 — canônico+layout+conector | ARQ-06, Integration Hub | CanonicalSchema, Layout, Connector, Route, Batch/Ack | `integration_hub` e adapters | EP9, S6, DEC-003 |
| DAT-06 — humano antes do efeito | ARQ-07/08; estados separados | ApprovalRequest/Decision, AuthorizedEffect, SuggestionOutcome | M19 e AI sem porta privilegiada | EP7, EP10; casos 8/9/18 |
| DAT-07 — tenant escritório | ARQ-10 | Tenant, Membership, CompanyAccess, tenant-aware FKs | ExecutionContext e autorização comum | EP1; casos 1/2/24 |
| DAT-08 — M19 obrigatório | Contexto `workflow_m19` | WorkflowCase, WorkItem, Approval e evidências | pacote `workflow_m19` | EP7 transversal |
| DAT-09 — IA e finalidades | AI consultiva e governança | DataUseAuthorization/Record, AI run, DatasetInclusion | AI gateway, redaction e policy ports | EP10, EP11, GOV-1101–1104 |
| DAT-10 — fatias verticais | Slices arquiteturais | Entidades entram conforme cada jornada completa | módulos habilitados incrementalmente | S0–S8 e DoD por slice |

## Decisões aprovadas em 02/09/2026

1. **ARQ-01 a ARQ-10:** monólito modular, portas/adaptadores, workers, inbox/outbox, pré-ledger, fronteira de integração, IA consultiva, aprovação por versão, auditoria atômica e tenancy em profundidade.
2. **Modelo lógico:** raiz + versões imutáveis, estados independentes, catálogo de entidades e invariantes da Fase 4.
3. **PY-01 a PY-08:** organização Python, domínio puro, kernel mínimo, regras declarativas, adapters, AI gateway, Unit of Work e contratos de leitura.
4. **Backlog S0–S8:** sequência, P0/P1, definição de pronto e casos perigosos bloqueadores.

A autorização para iniciar o aplicativo foi dada pelo responsável do produto em 03/09/2026. A seleção tecnológica permanece no Gate G0; entrada em produção continua condicionada aos gates do backlog e do cronograma.

## Estado das decisões de descoberta

- **DEC-001 — escopo resolvido:** NF-e 55, CT-e 57 e NFS-e padrão nacional; ordem NF-e → CT-e → NFS-e. Bundles XSD continuam versionados operacionalmente.
- **DEC-002 — formato resolvido, semântica parcial:** OFX 1.x/2.x e CSV configurável; timezone, correções e particularidades por banco serão fechados com o corpus.
- **DEC-003 — produto resolvido, homologação pendente:** Domínio Sistemas por TXT e confirmação humana; layout/versão/golden file exatos são Gate G0/G3.
- DEC-004: granularidade dos lançamentos.
- DEC-005: precisão, arredondamento, moedas e tolerâncias.
- DEC-006: tarefas/limiares/evidências de IA.
- DEC-007: matriz de papéis, alçadas, quórum e SoD.
- DEC-008: LGPD, retenção, legal hold e encerramento.
- DEC-009: SLA, RPO e RTO.
- **DEC-010 — parcialmente resolvida:** aproximadamente 1.000 documentos/mês; faltam pico, tamanho, itens, transações, empresas, usuários e SLA.
- DEC-011: tecnologias e isolamento físico, após comparar equipe, volume, custo e risco.

## Regra de mudança

Uma nova decisão que contradiga a baseline deve:

1. identificar o requisito/decisão afetado;
2. registrar motivo, alternativas e impactos;
3. receber aprovação explícita;
4. gerar nova versão dos artefatos dependentes;
5. atualizar esta matriz de rastreabilidade.

Artefatos v0.1 podem orientar a construção autorizada, mas somente versões aprovadas e gates cumpridos podem sustentar o piloto ou a produção.
