# Phase 13 — avaliação técnica de privacidade

Este documento registra evidência de engenharia. Não é parecer jurídico, não
certifica conformidade com a LGPD e não aprova base legal, contrato, papel das
partes, prazo de retenção ou transferência internacional.

## Matriz de capacidades

| Capacidade | Implementação atual | Evidência | Status | Ação |
|---|---|---|---|---|
| isolamento tenant/company | autorização central, CompanyAccess e filtros de repositório | testes security, API e privacy | READY | regressão contínua |
| retenção | política persistente e avaliação auditada | `privacy/application/services.py` | READY | períodos exigem revisão humana |
| retenção destrutiva | runner recusa `dry_run=False` | testes de privacy | READY / DISABLED_SAFE | não habilitar |
| Legal Hold | persistente, escopado, auditado e prioritário | módulo privacy + migration 0012 | READY | migration continua pre-deploy |
| DSR | registro, verificação, busca USERS e relatório mínimo em memória | módulo privacy + testes | PARTIAL | fontes documentais são manuais |
| prova de identidade DSR | estado e ator de verificação | entidade DSR | PARTIAL | procedimento operacional obrigatório |
| exportação/portabilidade | relatório mínimo em memória; sem arquivo/endpoint | `dsr_search.py` | PARTIAL | `MANUAL_ASSISTED` |
| eliminação/anonimização | não implementada | fail-closed do runner | MISSING_SAFE | decisão legal e arquitetura futuras |
| auditoria | eventos append-oriented, conteúdo minimizado | módulo audit e testes | READY | retenção especial |
| backup/restore | tooling e runbooks; sem destino produtivo | docs de recovery | PARTIAL | reconciliar ações pós-backup |
| incidente de privacidade | playbook técnico | `PRIVACY_INCIDENT_PLAYBOOK.md` | READY | contatos/prazos sob revisão legal |
| fornecedores/transferência | nenhum fornecedor produtivo confirmado | registro técnico | LEGAL_REVIEW_REQUIRED | procurement e contratos |
| IA externa | porta abstrata, sem adaptador de rede ativo | módulo ai e composição | NOT_APPLICABLE | reavaliar antes de ativar |

## Verificações transversais

- `DATA_MINIMIZATION = PASS`: projeções evitam token, payload bruto de
  auditoria e XML/OFX quando resumo basta.
- `PURPOSE_LIMITATION = READY`: identidade autentica/autoriza; documentos
  suportam processamento contábil; auditoria presta accountability; logs e
  métricas operam segurança; backup suporta recuperação.
- `PRIVACY_BY_DEFAULT = PASS`: nenhuma empresa é liberada sem CompanyAccess,
  não há link público, exportação ampla ou compartilhamento externo.
- `ACCESS_TOKEN_PERSISTENCE = NONE`: token permanece em memória; PKCE efêmero
  usa `sessionStorage`; `localStorage` contém somente preferências de widgets.
- `COOKIE_INVENTORY = NONE_IMPLEMENTED`: não há cookie de autenticação,
  analytics ou marketing no código atual.
- `ANALYTICS_TRACKING = NONE`: CSP do site bloqueia conexão e o formulário de
  demonstração não envia nem persiste dados.
- `METRICS_PERSONAL_DATA = NONE`: o schema fechado não permite tenant, empresa,
  usuário, documento ou CNPJ como label.
- `LOG_PII_MINIMIZATION = PASS`: observabilidade registra referências técnicas
  e classes sanitizadas, não payload pessoal bruto.
- `EXTERNAL_AI_DATA_FLOW = NONE`: nenhum gateway externo está composto.
- `CONSENT_MECHANISM = NOT_REQUIRED_FOR_CURRENT_SCOPE`: não existe atividade
  técnica atual baseada em consentimento; eventual escolha é jurídica.
- `MINORS_DIRECT_PROCESSING = NOT_A_TARGET_USE_CASE`.

## Gates independentes

| Gate | Estado |
|---|---|
| `TECHNICAL_PRIVACY_GATE` | `PASS` |
| `LEGAL_REVIEW_GATE` | `PENDING` |
| `CONTRACTUAL_GATE` | `PENDING` |
| `REAL_DATA` | `NO_GO` |
| `APPLICATION_EXTERNAL_EXPOSURE` | `NO_GO` |
| `PRODUCTION_IDP_CONFIG` | `PENDING` |
| `MIGRATION_0012` | `PRE_DEPLOY_REQUIRED` |
| `DOMINIO_EXPORT` | `BLOCKED_FOR_HOMOLOGATION` |
| `SYSTEM_A_INTEGRATION` | `DEFERRED_NOT_BLOCKING` |

O gate técnico não altera os demais. Um piloto com dados reais exige aprovação
jurídica e contratual, fornecedores e infraestrutura homologados, IdP
produtivo, backup/restore operacional, corpus autorizado e aprovação do
operador/contador. Nenhum desses itens é inferido como concluído.
