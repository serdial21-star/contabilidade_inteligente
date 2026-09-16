# Insumo técnico para RIPD

**RIPD_STATUS: TECHNICAL_INPUT_ONLY — LEGAL_REVIEW_REQUIRED**

Este arquivo não conclui se um RIPD é obrigatório, não avalia conformidade e não substitui a aprovação do responsável competente.

## Contexto e escopo

Plataforma multi-tenant para escritórios contábeis. Pode processar identidade, documentos fiscais, extratos e dados contábeis sensíveis ao negócio. O sistema externo permanece autoridade para escrituração oficial; propostas exigem aprovação humana.

## Necessidade e proporcionalidade técnicas

- isolamento tenant/company, acesso mínimo e trilha auditável;
- conteúdo bruto fora de logs/auditoria; IDs e hashes quando suficientes;
- IA sem autoridade decisória e sem provedor externo ativo;
- retenção destrutiva bloqueada até política aprovada;
- DSR interno condicionado a identidade, permissão e fontes declaradas.

## Riscos e medidas

Usar `PRIVACY_RISK_REGISTER.md`. Riscos centrais: isolamento, conteúdo documental, identidade DSR, retenção/hold, backup/restore, fornecedores e incidentes. Medidas: autorização central, testes negativos, imutabilidade, sanitização, versionamento, dry-run, auditoria e gates de infraestrutura/jurídico.

## Decisões pendentes

Papéis, bases, titulares, prazo, transferências, fornecedores, canal DSR, critérios de risco, necessidade formal do RIPD, aceite residual e sign-off. Evidências complementares estão no inventário, mapa de fluxo, ROPA técnico e registro de suboperadores.
