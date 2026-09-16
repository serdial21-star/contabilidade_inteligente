# Registro de riscos de privacidade

Escala técnica: probabilidade/impacto `BAIXO`, `MÉDIO`, `ALTO`. Aceitação de risco exige responsável humano.

| Risco | P/I | Controles existentes | Tratamento / proprietário | Estado |
|---|---|---|---|---|
| acesso cross-tenant/company | M/A | autorização central, CompanyAccess, testes negativos; correção Phase 13 | engenharia/segurança | mitigado tecnicamente, monitorar |
| prazo/base/papel inferidos | M/A | estados pending e documentos-gate | jurídico/produto | OPEN_LEGAL_GATE |
| documento sensível em logs/auditoria | B/A | sanitização, campos proibidos e limites | engenharia/segurança | controlado, testar continuamente |
| DSR incompleto | A/M | USERS automatizado, storage manual, relatório em memória | privacidade/operação | OPEN; procedimento manual obrigatório |
| identidade do solicitante insuficiente | M/A | estado `IDENTITY_PENDING`; operador registra verificação | privacidade/jurídico | OPEN_PROCEDURE |
| eliminação incompatível com hold/backup | M/A | dry-run-only e hold prevalente | jurídico/infra/engenharia | BLOCKED_BY_DESIGN |
| restauração ressuscitar dado/estado antigo | M/A | restore runbook | infra/privacidade | OPEN_RECONCILIATION_GAP |
| storage/backup sem criptografia comprovada | M/A | requisitos documentados | infraestrutura | OPEN_PROVIDER_GATE |
| fornecedor/transferência desconhecido | M/A | registro técnico e no external deploy | jurídico/infra | OPEN_PROCUREMENT_GATE |
| ativação futura de IA/integrador com dados | M/A | nenhuma conexão atual; gateway abstrato | produto/privacidade/segurança | DEFERRED_REVIEW_REQUIRED |
| retenção excessiva | A/M | nenhuma destruição, política pendente | jurídico/contábil | OPEN_LEGAL_GATE |
| incidente sem contato/alçada definidos | M/A | playbook técnico | gestão/jurídico | OPEN_OPERATIONAL_GATE |

Revisar antes de dado real, após incidente, novo fornecedor, integração, mudança de finalidade ou publicação de política.

## Matriz de decisão do piloto

| ID | Dado/processo | Ameaça e impacto | Controle atual | Risco residual | Owner | Revisão legal? | Bloqueia piloto real? |
|---|---|---|---|---|---|---|---|
| PR-01 | todos os domínios | correlação cross-tenant/company; divulgação grave | autorização central e testes negativos | MÉDIO | Security/Engineering | sim | sim se falhar |
| PR-02 | documentos | IDOR ou conteúdo bruto em projeção/log | CompanyAccess, resumo, sanitização | MÉDIO | Documents/Security | sim | sim |
| PR-03 | backup | acesso indevido ou região desconhecida | tooling e requisito de cifra/acesso mínimo | ALTO até fornecedor | Infrastructure | sim | sim |
| PR-04 | retenção | eliminação incorreta ou perda de evidência | destruição desabilitada e hold prioritário | BAIXO para perda; ALTO para excesso | Privacy/Engineering | sim | sim antes de habilitar |
| PR-05 | DSR | solicitante incorreto ou escopo excessivo | estado de verificação, permissão e busca mínima | MÉDIO | Privacy/Operations | sim | sim sem procedimento |
| PR-06 | observabilidade | PII em log/label | redaction e schema fechado | BAIXO | Security/SRE | sim | sim se regredir |
| PR-07 | restore | reintrodução de dado/estado antigo | runbook e cutover bloqueável | ALTO | Infrastructure/Privacy | sim | sim para eliminação material |
| PR-08 | fornecedores/integração | compartilhamento ou transferência não aprovados | nenhum fluxo ativo; gates | ALTO se ativado | Product/Legal/Security | sim | sim |

“Bloqueia piloto real” não altera `REAL_DATA = NO_GO`; apenas explicita quais
condições continuariam impeditivas mesmo após a verificação técnica desta fase.
