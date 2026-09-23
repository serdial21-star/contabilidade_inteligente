# ADR 0012 — Referência externa de Company

## Status

Aceita como preparação aditiva, sem iniciar a conexão com o Sistema A.

## Decisão

`Company` pode guardar a referência técnica opcional definida pelo contrato do
Connect Hub: `external_system + external_type + external_id`. Os três valores
são strings opacas; CNPJ permanece somente uma chave de negócio auxiliar e não
autoriza acesso.

A tripla é única dentro do tenant e é sempre lida por consultas escopadas por
`tenant_id + company_id`, depois da autorização e do `CompanyAccess` vigentes.
Registros existentes permanecem compatíveis porque as três colunas são
nullable.

A migration `20260923_0015` é aditiva. Este incremento não cria endpoint,
credencial, conector, chamada de rede, sincronização, correlação automática por
CNPJ nem conexão real com o Sistema A.
