# Controles técnicos de privacidade

## IMPLEMENTED

- `RetentionPolicy` persistente e tenant-scoped, com estado `PENDING` ou
  `APPROVED`; nenhuma política é semeada com prazo jurídico.
- `RetentionDecisionService` produz somente `KEEP`, `LEGAL_HOLD`,
  `PENDING_POLICY_APPROVAL`, `ELIGIBLE_FOR_RETENTION_ACTION` ou
  `NOT_APPLICABLE`. `AuditEvent` recebe tratamento especial e nunca é candidato
  a destruição automática.
- `RetentionRunner` aceita exclusivamente `dry_run=True`; `dry_run=False` lança
  `DestructiveRetentionDenied`.
- `LegalHold` persistente, tenant/company/resource-scoped, com criação e
  liberação auditadas. Hold ativo vence política de retenção.
- workflow DSR persistente: `IDENTITY_PENDING -> IN_REVIEW -> COMPLETED`;
  identificador é armazenado somente como SHA-256 e não há endpoint público nem
  exportação de conteúdo.
- Registry DSR conectado à fonte `USERS` MariaDB (email ou user ID, sempre
  tenant-scoped); `DOCUMENT_STORAGE` é declarado `MANUAL_SOURCE`, sem fingir
  busca no object storage local. O relatório é somente em memória, contém IDs e
  resumo mínimo, e manifesto declara `PARTIAL_WITH_MANUAL_SOURCES`.
- A busca exige a permissão central `privacy.dsr.search`, membership e
  CompanyAccess pelo `AuthorizationService`. As permissões privacy novas não
  são atribuídas automaticamente.
- DSR search e access report in-memory estão disponíveis para operação interna;
  o report exige `privacy.dsr.export`, preserva o manifesto e grava somente
  contagens/status em `AuditEvent`. Boundaries administrativos reutilizam
  `AuthorizationService`; retenção continua dry-run e destruição desabilitada.

`MIGRATION_0012_MARIADB = PRE_DEPLOY_GATE`. `HTTP_EXPOSURE = DEFERRED`.
- migration `20260908_0012_privacy_controls` cria apenas tabelas novas,
  InnoDB/utf8mb4 por padrão do projeto; migrations antigas não foram alteradas.

## PENDING_HUMAN_APPROVAL

Base legal, prazos, categorias autorizadas, modo de destruição, exceções,
papéis e critérios de legal hold, DSR, backup e comunicação de incidente.

## NOT_IMPLEMENTED

Destruição/anominização, busca DSR sobre dados reais, export DSR, endpoint
público, backup/expiração de object storage e execução destrutiva em Runtime.
Esses itens permanecem bloqueados e não são inferidos por esta implementação.
