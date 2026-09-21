# ADR 0011 — Accounting Automation Core

## Status

Aceita para o incremento estrutural, sem iniciar Fase 15.

## Decisão

Reutilizar o catálogo versionado, `AccountingRuleVersion`, `AccountVersion`, mapping, proposta, workflow e auditoria existentes. Persistir somente perfil/atividade, contraparte mínima, perfil recorrente, resultado/evidência e feedback por item. Intenção é separada de conta; CNAE/CFOP/NCM/texto são evidências; regra de maior escopo precede menor e empate incompatível produz conflito.

A migration `20260916_0014` é aditiva. Não há integração externa, dado real, IA autônoma ou postagem final.
