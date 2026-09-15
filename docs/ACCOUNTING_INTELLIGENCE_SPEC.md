# Inteligência Contábil — Fase 08

## Escopo entregue

A jornada operacional suportada é `NF-e 55 → regra determinística publicada → proposta → revisão profissional → aprovação ou rejeição`. O sistema contábil externo continua autoridade sobre escrituração, saldos e fechamento. OFX e `BankTransaction` permanecem somente como fontes financeiras importadas: não existe caso de uso seguro que gere proposta contábil a partir delas.

Não foi criado segundo motor, tabela, status ou workflow. A implementação projeta a jornada, o catálogo versionado, o `JournalProposal`, a revisão imutável, as linhas e a decisão já existentes. Não há postagem, exportação Domínio, SPED ou aprovação automática.

## Regras e proposta

Somente catálogo `PUBLISHED`, efetivo para a empresa e com hash íntegro é consultado. A data efetiva é informada explicitamente na UI/API e não é inferida do timezone do servidor. A regra preserva ID da versão, nome, escopo, prioridade, condições, nível de automação e contas resultado. Nenhuma expressão executável é exposta. Empate de prioridade ou ausência de regra segue o resultado seguro do motor existente (`PENDING_RULE`), sem inventar conta.

A proposta preserva `source_id`, `rule_version_id`, `revision_id`, `revision_hash`, data contábil e contas versionadas. A lista é paginada e filtrada no servidor. O detalhe apresenta evidência fiscal minimizada e vínculos company-scoped para NF-e e receipt documental.

Linhas são compostas: a UI não pressupõe uma partida 1×1. O backend soma `Decimal` e informa `total_debit`, `total_credit` e `balanced`. A interface só formata; não recalcula nem arredonda a autoridade contábil. A precisão publicada (`decimal_places`) e `amount_field` são exibidos no catálogo.

## Revisão e decisão

Estados expostos são os existentes: `PENDING_APPROVAL`, `APPROVED`, `REJECTED`, `BLOCKED_FOR_HOMOLOGATION` e `SUPERSEDED`. Aprovar/rejeitar reutiliza os comandos `/reviews/{journey_id}/approve|reject`, sempre com versão, revisão, hash e chave idempotente. A decisão requer origem humana, `journal.approve`, papel do workflow, CompanyAccess vigente, segregação, proposta pendente, revisão válida, balanceamento e ausência de `AccountLock` aplicável.

Rejeição não possui campo seguro de comentário no schema atual. Edição de proposta, regra e mapping também não possui caso de uso granular seguro; todos ficam `DEFERRED`, sem migration. Desbloqueio pertence à governança e não foi exposto.

## Permissões e UX

- `journal.read`: lista e detalhe de propostas.
- `journal.approve`: controles de aprovação/rejeição; o backend continua a autoridade.
- `catalog.review`: catálogo, regras, contas e mappings read-only.
- `audit.read`: histórico contextual minimizado da correlação.

W003, W005 e W006 direcionam à fila contábil real. Automação usa linguagem ouro de “SUGESTÃO/PROPOSTA CONTÁBIL”; decisão humana usa estado próprio. `AccountLock` mostra escopo, alvo, operações, motivo seguro e criação, mas o backend revalida a aplicabilidade no instante do efeito.

## Gaps e limites

- `PROPOSAL_EDIT`, `RULE_WRITE`, `ACCOUNT_MAPPING_WRITE`: `DEFERRED`.
- `ACCOUNTING_FROM_FINANCIAL`: `DEFERRED`.
- Motivo textual de rejeição: `PHASE08_SCHEMA_GAP`; nenhuma migration criada.
- Linha da Decisão completa e visualização cross-module: `DEFERRED_PHASE09`.
- Preferências de dashboard server-side, reconciliação e malware scanning continuam fora do escopo.
