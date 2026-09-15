# Lacunas de dados da Linha da Decisão

| STAGE | EXPECTED EVIDENCE | CURRENT SOURCE | STATUS | IMPACT | FUTURE REMEDIATION |
|---|---|---|---|---|---|
| Ação de revisão | evento/ator distinto quando o profissional efetivamente abre ou conclui a conferência | `work_item.created` e `approval_request.created` apenas comprovam encaminhamento | PARTIAL | a linha não afirma que uma revisão humana ocorreu antes da decisão | definir transição de revisão real e emissão atômica, se aprovada pelo domínio |
| Motivo de rejeição | motivo estruturado ligado à decisão e revisão/hash | `ApprovalDecision` não possui motivo | PARTIAL | exibe rejeição, sem inventar justificativa | decisão de domínio e migration futura, com retenção/minimização |
| Tentativa bloqueada | auditoria atômica da tentativa e do bloqueio aplicado | apenas estado `AccountLock` vigente é autoritativo | PARTIAL | mostra bloqueio vigente derivado, não tentativa | avaliar emissão de evento real no caso de uso crítico |
| Histórico de locks no contexto | vínculo explícito entre lock e jornada afetada | locks possuem correlação própria | PARTIAL | desbloqueios históricos não são anexados à jornada sem evidência | contrato de causalidade futuro, sem reescrever histórico |
| W010 → recurso | tipo e ID seguro do recurso por item | widget agrega texto minimizado | PARTIAL | não há navegação contextual confiável | enriquecer contrato do widget com referência autorizável |
| Índice de consulta | `(tenant_id, company_id, subject_type, subject_id)` e correlação com empresa | índices atuais incluem tenant/sujeito e tenant/correlação | PRE_DEPLOY | adequado ao piloto sintético; deve ser medido antes de exposição | revisar plano MySQL e propor migration explícita se necessária |
| Dados antigos opcionais | evento ou correlação ausente em registros legados | fallback `CORRELATED_AUDIT_NOT_AVAILABLE` | SAFE_FALLBACK | linha parcial e vazia, sem fabricação | backfill somente com plano aprovado e evidência verificável |
| Financeiro → contábil | relação canônica aprovada | nenhuma no MVP | NOT_SUPPORTED | OFX termina em processamento/transações | manter fora até fase/domínio autorizado |

Não há gap que autorize uma segunda tabela de histórico. `TRACEABILITY INDEX GAP`: revisão composta pré-deploy descrita acima; migration não criada na Fase 09.
