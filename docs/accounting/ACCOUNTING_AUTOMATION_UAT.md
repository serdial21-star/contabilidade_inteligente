# UAT — automação contábil

Usar somente dados sintéticos. Validar SC01–SC10, NF-e mista com três intenções, mapping para conta analítica, rejeições de conta sintética/ciclo/duplicidade/cross-company, decisão única versus reutilizável, conflito, explicação e ausência de aprovação automática.

Também validar autorização, auditoria atômica, AccountLock, responsividade e linguagem de proposta. Estado em 2026-09-23: API, UI e orquestração persistente concluídas e migration 0014 validada em MariaDB real; automatizado (`pytest`) `READY`. Segue `HUMAN_UAT_NOT_READY`: falta vincular `accounting.classification.review` a um papel real no ambiente de homologação (decisão do escritório) e executar o roteiro SC01–SC10 com uma pessoa profissional.
