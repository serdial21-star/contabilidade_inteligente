# ADR 0010 — Incremento operacional pós-UAT

## Status

Aceita para o incremento direcionado posterior à remediação da Fase 14. Não inicia a Fase 15.

## Contexto e decisão

O cadastro bancário existente passa a ser o cadastro mestre autorizado por empresa. Ele recebe nome, apelido, estado ativo/inativo e edição auditada; a identidade externa continua composta pelos campos bancários normalizados. O importador OFX somente associa extratos a uma conta ativa e pertencente ao mesmo tenant e à mesma empresa. Conta ausente ou inativa produz quarentena, sem criação implícita.

Metadados operacionais de documento ficam em `document_metadata`, vinculados por chave composta ao `artifact_receipts`. Número, descrição e observação podem evoluir com versão e auditoria, sem alterar a evidência recebida, seu hash ou o histórico append-oriented.

A fila contábil mantém o checkpoint imutável como autoridade. Campos de busca derivados (`account_search`, `rule_search`, `source_search` e `accounting_date_index`) são persistidos junto a cada novo checkpoint e preenchidos para o histórico na migration. Eles servem apenas à consulta paginada e não alteram regra, proposta ou decisão.

## Consequências

- A migration `20260916_0013` é aditiva e reversível para os novos campos e tabela.
- Identidades e números bancários permanecem mascarados nas respostas e na auditoria.
- Toda escrita exige `company.manage`; leitura exige `company.read`; CompanyAccess e isolamento de tenant continuam revalidados no backend.
- A pesquisa do plano de contas usa a versão publicada já carregada e é somente leitura.
- Observação/histórico próprios de uma proposta contábil continuam como lacuna de schema; nenhum campo foi inventado.
- UAT humana permanece `RETEST_REQUIRED` até nova execução manual.
