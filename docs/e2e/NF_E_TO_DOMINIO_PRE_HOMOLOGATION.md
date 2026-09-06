# NF-e para Domínio: pré-homologação

Esta fatia permite navegar uma NF-e importada até uma intenção de exportação, mas não produz arquivo, entrega ou efeito contábil externo.

`EvidenceArtifact -> ImportBatch/ImportItem -> CanonicalRecord -> FiscalDocument -> WorkflowCase -> WorkItem -> ApprovalRequest -> AuthorizedEffect -> ExportBatch`

O fluxo é interrompido com `PENDING_RULE` quando não há regra determinística publicada aplicável. Não se cria proposta, revisão, lançamento ou aprovação de conveniência. A solicitação de aprovação permanece `PENDING`; o `AuthorizedEffect` fica `PENDING` e `NOT_EXECUTED`.

Todo `ExportBatch` desta fatia fica exclusivamente em `BLOCKED_FOR_HOMOLOGATION`, com os motivos:

- `DOMINIO_CONNECTOR_NOT_HOMOLOGATED`
- `DOMINIO_GOLDEN_FILE_MISSING`
- `DOMINIO_LAYOUT_VERSION_UNKNOWN`

Um mesmo `correlation_id` é gravado no caso, item, solicitação, efeito, lote e eventos de auditoria. A navegação reversa parte do lote, passa pelo efeito e chega ao `FiscalDocument`, `CanonicalRecord` e `EvidenceArtifact`; o `EvidenceArtifact` preserva o XML original no armazenamento de evidência.

Papéis previstos: Assistente prepara/complementa/encaminha; Analista revisa/devolve/solicita informação; somente Contador pode aprovar ou rejeitar um efeito contábil. IA não aprova, não cria efeito, não exporta nem desbloqueia. Uma aprovação futura deve referenciar a revisão e o hash exatos; qualquer alteração material invalida a aprovação.

PENDÊNCIAS: golden file oficial Domínio, versão formal do layout e homologação real. Enquanto faltarem, a serialização e qualquer entrega permanecem proibidas.
