# Linha da Decisão — especificação da Fase 09

## Propósito e autoridade

A Linha da Decisão explica, em leitura, como um recurso chegou ao estado atual. Ela é uma projeção de `AuditEvent` e de estado canônico já persistido; não é um segundo histórico, não grava eventos e não representa escrituração, saldo ou fechamento oficial.

## Mapa de rastreabilidade confirmado

| Etapa | Evidência existente | Projeção |
|---|---|---|
| Fonte e recebimento | `ImportBatch`, `EvidenceArtifact`, `ArtifactReceipt` e seus `AuditEvent` | `SOURCE`, `RECEIPT` |
| Transformação e validação | `TransformationRun`, `ValidationIssue`, linhagem e auditoria | `PROCESSING`, `VALIDATION`, `EXCEPTION` |
| NF-e canônica | `FiscalDocument` e `nfe55.imported` | `PROCESSING` |
| OFX canônico | `BankStatement`, `BankTransaction` e `ofx.imported` | `PROCESSING`, sem inferência contábil |
| Regra | `RuleEvaluation` e `rule_evaluation.completed` | `RULE` |
| Proposta/revisão | jornada, proposta, revisão e eventos do workflow | `PROPOSAL`, `REVIEW`, `EDIT` quando real |
| Decisão | `ApprovalDecision` e `approval_decision.recorded` | `APPROVAL` ou `REJECTION` |
| Governança | `AccountLock` e eventos de bloqueio/liberação | `BLOCK`, `UNBLOCK` |

Raízes suportadas: `DOCUMENT`, `FISCAL_DOCUMENT`, `BANK_STATEMENT`, `ACCOUNTING_PROPOSAL` e `REVIEW`. Documento, NF-e e extrato são resolvidos primeiro no tenant/empresa; proposta e revisão exigem uma proposta real na jornada.

## Contrato e ordenação

`GET /api/v1/operations/companies/{company_id}/decision-lines/{root_type}/{root_id}?limit=100`

A resposta contém somente título/status da raiz, completude, códigos de lacuna e eventos seguros. Cada evento expõe sequência, timestamp persistido, categoria, classe de ator, nome de exibição, texto controlado, origem da evidência e validade de integridade. Eventos são ordenados por `(occurred_at, id)`; o `id` apenas desempata e não é exposto.

As classes de ator são `AUTOMATED`, `PROFESSIONAL_ACTION` e `SYSTEM_GOVERNANCE`. A classificação decorre da semântica da transição, não apenas de `AuditOrigin`, pois eventos automáticos da jornada preservam o iniciador humano. Nome pessoal aparece apenas para ação profissional e é resolvido em lote dentro do tenant.

## Eventos derivados e apresentação

O único evento derivado atual é o bloqueio vigente que determinísticamente impede aprovação da proposta. Ele usa `AccountLock.created_at`, é marcado `DOMAIN_DERIVED_EVENT` e não afirma tentativa bloqueada. Demais eventos são `AUDIT_EVENT`; payloads `before/after`, hashes, e-mails, IDs técnicos de ator, correlação e caminhos de storage não são expostos.

A interface reutiliza cards, badges, alertas, tipografia e tokens existentes. A linha aparece nos detalhes da Central de Documentos, NF-e, extrato OFX e proposta/revisão quando `audit.read` está disponível. W010 permanece resumido: seus itens atuais não carregam vínculo seguro de entidade suficiente para navegação contextual.

Não existem endpoints de escrita, exportação PDF oficial ou persistência de timeline nesta fase.
