# Arquitetura do plano de contas

O catálogo versionado existente permanece autoridade sobre ledger, plano, `AccountVersion`, regras e mappings. Conta publicada é imutável; correção cria versão. Hierarquia usa `parent_account_id`, não o texto do código.

Conta sintética ou não lançável não recebe linha. Conta analítica já usada não pode ser transformada silenciosamente em pai. Templates podem ter escopo `SYSTEM` ou `OFFICE`; a empresa mantém sua versão customizável.
