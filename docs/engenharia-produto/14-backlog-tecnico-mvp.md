# Serdial21 — Backlog Técnico do MVP

| Controle | Valor |
|---|---|
| Status | **APROVADO COMO BASE — aguardando refinamento e estimativa** |
| Versão | 1.0 |
| Baseline | DAT-01 a DAT-10 e duas verticais aprovadas |
| Aprovação | S0 a S8 aprovados pelo responsável do produto em 02/09/2026 |
| Método | Fatias verticais completas, com segurança e auditoria em cada slice |

## 1. Resultado de release

O MVP estará apto a piloto quando um escritório conseguir:

1. administrar tenant, empresas, memberships, empresas autorizadas e papéis mínimos;
2. importar/sincronizar plano, cadastros e DE/PARA do recorte;
3. receber XML estruturado e extrato bancário preservando evidência e origem;
4. normalizar os dois formatos para modelos canônicos versionados;
5. aplicar regras determinísticas e sugestões de IA explicáveis;
6. gerar propostas contábeis balanceadas no pré-ledger;
7. tratar pendências, conciliações e aprovações humanas no M19;
8. respeitar períodos e bloqueios por todos os canais;
9. exportar por layout genérico e primeiro conector estratégico;
10. confirmar, rejeitar ou reconciliar estado incerto sem duplicidade;
11. reconstruir tudo pela trilha de auditoria.

O MVP não promete razão, saldo ou fechamento oficial no Serdial21.

## 2. Ordem das fatias

```mermaid
flowchart LR
    S0[S0 Espinha segura] --> S1[S1 Onboarding contábil]
    S1 --> S2[S2 Walking skeleton XML]
    S2 --> S3[S3 Robustez XML]
    S1 --> S4[S4 Walking skeleton bancário]
    S3 --> S5[S5 Regras governadas]
    S4 --> S5
    S5 --> S6[S6 Efeito externo seguro]
    S6 --> S7[S7 IA assistiva]
    S7 --> S8[S8 Piloto e endurecimento]
```

| Slice | Resultado demonstrável |
|---|---|
| S0 — Espinha segura | Primeiro comando tenant-aware, autorizado, idempotente e auditado |
| S1 — Onboarding | Empresa, plano mínimo, conta, período e DE/PARA sincronizados |
| S2 — XML ponta a ponta | XML → evidência → canônico → proposta → M19 → aprovação → arquivo genérico |
| S3 — Robustez XML | Quarentena, erros por campo, duplicidade, versões, dry-run e reprocessamento |
| S4 — Bancário ponta a ponta | Extrato → transações → candidatos → conciliação manual → proposta/aprovação |
| S5 — Regras governadas | Release versionada, trace, simulação, conflitos e N0–N2 |
| S6 — Efeito externo seguro | Locks, lote, primeiro conector, acknowledgement, parcial e UNKNOWN |
| S7 — IA assistiva | Sugestão explicada, feedback, avaliação, privacidade e fallback |
| S8 — Piloto/endurecimento | Volume real, recuperação, retenção, segurança, operação e métricas |

S7 vem depois de um fluxo determinístico funcional para provar que IA é assistência e não dependência. Nada impede experimentos controlados em paralelo, mas o release não depende deles para manter integridade.

## 3. Épicos

| Épico | Resultado | Slices predominantes |
|---|---|---|
| EP0 — Espinha arquitetural | Limites, tipos, transações, idempotência e testes de arquitetura | S0 |
| EP1 — Tenant e acesso | Isolamento, memberships, CompanyAccess, papéis e identidades técnicas | S0–S1 |
| EP2 — Cadastros, plano e autoridade | Empresa, plano, contas, períodos, referências e conflitos | S1 |
| EP3 — Documentos e staging | Evidência, lote, quarentena, deduplicação e reprocessamento | S2–S4 |
| EP4 — XML e extrato | Normalização fiscal e bancária com linhagem | S2–S4 |
| EP5 — DE/PARA e regras | Mapeamentos, release determinística, trace e simulação | S2–S5 |
| EP6 — Pré-ledger | Proposta, JournalEntry/Revision/Line e invariantes | S2–S6 |
| EP7 — M19 | Pendência, tarefa, decisão, alçada e efeito autorizado | S2–S7 |
| EP8 — Conciliação e bloqueios | Match/alocação, divergência, AccountLock e nova conferência | S4–S6 |
| EP9 — Integrações | Canônico, layout, lote, conector, retorno e estado incerto | S2–S6 |
| EP10 — IA assistiva | Sugestões, evidências, feedback, avaliação e política de dados | S7 |
| EP11 — Auditoria e governança | Trilha, acesso, finalidade, retenção e recuperação | Transversal |
| EP12 — Operação e piloto | Jobs, alertas, suporte, desempenho e rollout | S3–S8 |

## 4. Backlog detalhado

### EP0 — Espinha arquitetural

| ID | Prioridade | Item e entrega verificável | Dependência |
|---|---|---|---|
| EN-001 | P0 | Formalizar módulos, APIs públicas e regras de importação; teste falha em dependência proibida | — |
| EN-002 | P0 | Definir value objects de dinheiro, competência, identificadores, versões e fingerprints | EN-001 |
| EN-003 | P0 | Definir ExecutionContext com tenant, empresa, ator, canal, finalidade e correlação | EN-001 |
| EN-004 | P0 | Unidade de trabalho com optimistic concurrency e resultado idempotente | EN-002 |
| EN-005 | P0 | Inbox/outbox e envelope versionado de comandos/eventos | EN-003, EN-004 |
| EN-006 | P0 | Registrar auditoria mínima no mesmo commit do efeito | EN-004 |
| EN-007 | P0 | Kit de testes de contrato para repositório, storage, layout, conector e IA | EN-001 |
| EN-008 | P1 | Corpus de fixtures anonimizadas/versionadas e política de inclusão | EN-007, GOV-001 |

### EP1 — Tenant, empresas e acesso

| ID | Prioridade | Item e entrega verificável | Dependência |
|---|---|---|---|
| IAM-101 | P0 | Criar tenant-escritório e ciclo de ativação/encerramento | EN-003, EN-006 |
| IAM-102 | P0 | Cadastrar empresa/estabelecimento sem relacionamento cross-tenant | IAM-101 |
| IAM-103 | P0 | Administrar TenantMembership com vigência e revogação | IAM-101 |
| IAM-104 | P0 | Conceder/revogar CompanyAccess e trocar contexto explicitamente | IAM-102, IAM-103 |
| IAM-105 | P0 | Papéis/permissões mínimos de auxiliar, analista, contador e gestor | IAM-104 |
| IAM-106 | P0 | Aplicar autorização em comandos, consultas, jobs, arquivos e exportações | IAM-105, EN-003 |
| IAM-107 | P0 | ServicePrincipal por conexão com escopo/revogação próprios | IAM-105 |
| IAM-108 | P1 | Acesso excepcional de suporte com prazo, aprovação e auditoria | IAM-106, WF-706 |

### EP2 — Cadastros, plano, período e autoridade

| ID | Prioridade | Item e entrega verificável | Dependência |
|---|---|---|---|
| MDM-201 | P0 | Registrar empresa canônica e DomainAuthorityPolicy por domínio | IAM-102 |
| COA-201 | P0 | Importar plano e AccountVersion mantendo ID/referência externa | MDM-201, INT-901 |
| COA-202 | P0 | Validar hierarquia acíclica, natureza, conta analítica e vigência | COA-201 |
| COA-203 | P0 | Registrar AccountingPeriod interno e observação externa separada | MDM-201 |
| COA-204 | P0 | Detectar atualização concorrente/conflito com autoridade externa e abrir pendência | COA-201, WF-701 |
| MDM-202 | P1 | Cadastros mínimos de Party, CostCenter e histórico do piloto | MDM-201 |

### EP3 — Documentos, evidências e staging

| ID | Prioridade | Item e entrega verificável | Dependência |
|---|---|---|---|
| DOC-301 | P0 | Receber batch/item com idempotency key, origem e contagens | IAM-106, EN-005 |
| DOC-302 | P0 | Selar EvidenceArtifact por hash e armazenar metadados/classificação | DOC-301 |
| DOC-303 | P0 | Preservar cada ArtifactReceipt mesmo quando duplicado | DOC-302 |
| DOC-304 | P0 | Inspecionar/quarentenar arquivo hostil, inválido ou excessivo sem efeito parcial | DOC-302 |
| DOC-305 | P0 | Deduplicar por chave oficial/fingerprint/hash no tenant/empresa corretos | DOC-303 |
| DOC-306 | P0 | Registrar ValidationIssue por campo/código/severidade | DOC-304 |
| DOC-307 | P1 | Dry-run e diff de reprocessamento com versões fixadas | DOC-305, AUD-1102 |
| DOC-308 | P1 | Política de retenção/descarte e legal hold do artefato | GOV-1104 |

### EP4 — XML estruturado e movimentação bancária

| ID | Prioridade | Item e entrega verificável | Dependência |
|---|---|---|---|
| XML-401 | P0 | Selecionar/detectar schema XML do piloto e validar estrutura com segurança | DOC-304, DEC-001 |
| XML-402 | P0 | Normalizar FiscalDocument, itens, tributos e eventos para versão canônica | XML-401 |
| XML-403 | P0 | Registrar linhagem de campo canônico à evidência/parser/layout | XML-402 |
| XML-404 | P1 | Tratar correção/cancelamento como evento, sem sobrescrever documento | XML-402 |
| BNK-401 | P0 | Selecionar/detectar formatos de extrato do piloto | DOC-304, DEC-002 |
| BNK-402 | P0 | Normalizar BankStatement/Transaction com timezone, sinal e moeda definidos | BNK-401 |
| BNK-403 | P0 | Deduplicar movimento por ID oficial/fingerprint semântico | BNK-402 |
| BNK-404 | P0 | Registrar linhagem do movimento à linha/campo do extrato | BNK-402 |
| BNK-405 | P1 | Tratar sobreposição, correção e saldo divergente do extrato | BNK-403 |

### EP5 — DE/PARA e regras

| ID | Prioridade | Item e entrega verificável | Dependência |
|---|---|---|---|
| MAP-501 | P0 | Criar conjunto/versão/entrada DE/PARA com escopo e vigência | COA-202 |
| MAP-502 | P0 | Resolver mapping e explicar precedência; empate abre pendência | MAP-501, WF-701 |
| MAP-503 | P1 | Simular nova versão sobre corpus sem alterar histórico | MAP-502, EN-008 |
| RUL-501 | P0 | Criar AccountingRuleVersion declarativa, sem código arbitrário | EN-002, MAP-501 |
| RUL-502 | P0 | Validar/testar/aprovar/publicar RuleSetRelease imutável | RUL-501, WF-703 |
| RUL-503 | P0 | Avaliar deterministicamente com trace e conflitos explícitos | RUL-502, MAP-502 |
| RUL-504 | P1 | Simular release nova e mostrar diff de propostas | RUL-503, EN-008 |
| RUL-505 | P1 | Registrar níveis N0–N3, mantendo N3 bloqueado para efeitos externos | RUL-502, POL-001 |

### EP6 — Pré-ledger e propostas

| ID | Prioridade | Item e entrega verificável | Dependência |
|---|---|---|---|
| ACC-601 | P0 | Criar Ledger/AccountingPeriod e JournalEntry com revisões próprias | COA-203, EN-002 |
| ACC-602 | P0 | Gerar JournalLine com AccountVersion, origem e dimensões | ACC-601, RUL-503 |
| ACC-603 | P0 | Validar exatamente um lado, valores positivos, equilíbrio e competência | ACC-602 |
| ACC-604 | P0 | Criar AccountingProposal e alternativas explicáveis | ACC-603 |
| ACC-605 | P0 | Congelar revisão submetida/aprovada e superseder aprovação após mudança | ACC-604, WF-703 |
| ACC-606 | P0 | Separar preparação, aprovação, entrega e status externo | ACC-601 |
| ACC-607 | P1 | Registrar estorno/ajuste ligado ao original após confirmação externa | ACC-606, INT-910 |

### EP7 — M19 Workflow, Pendências e Aprovações

| ID | Prioridade | Item e entrega verificável | Dependência |
|---|---|---|---|
| WF-701 | P0 | Abrir WorkItem com motivo estruturado, sujeito/version, prioridade e evidências | IAM-106, EN-006 |
| WF-702 | P0 | Filtrar, atribuir, assumir e transferir com histórico e CompanyAccess | WF-701 |
| WF-703 | P0 | Solicitar aprovação para versão/hash exatos e registrar decisão/justificativa | WF-702 |
| WF-704 | P0 | Rejeitar, solicitar retrabalho, expirar e cancelar sem efeito residual | WF-703 |
| WF-705 | P0 | Aplicar alçada, quórum e segregação configurados | IAM-105, WF-703 |
| WF-706 | P0 | Emitir AuthorizedEffect causal, idempotente e revalidado pelo domínio | WF-703, EN-005 |
| WF-707 | P1 | SLA, alertas, escalonamento e indicadores de fila | WF-702, OPS-1203 |

### EP8 — Conciliação e bloqueios

| ID | Prioridade | Item e entrega verificável | Dependência |
|---|---|---|---|
| REC-801 | P0 | Criar Reconciliation e candidatos explicáveis para movimentos | BNK-403, RUL-503 |
| REC-802 | P0 | Suportar match um-para-um, divisão e agrupamento com alocações | REC-801 |
| REC-803 | P0 | Impedir dupla/sobre-alocação e controlar tolerância aprovada | REC-802, DEC-005 |
| REC-804 | P0 | Enviar versão exata para aprovação humana no M19 | REC-802, WF-703 |
| REC-805 | P0 | Reabrir/desfazer com nova decisão e histórico | REC-804, AUD-1102 |
| LCK-801 | P0 | Aplicar AccountLock por conta/grupo/módulo/competência/exercício | COA-203, IAM-105 |
| LCK-802 | P0 | Guard comum impede alteração/aprovação/reprocesso/export em todo canal | LCK-801, EN-004 |
| LCK-803 | P0 | Desbloqueio com alçada/justificativa e REQUER_NOVA_CONFERENCIA | LCK-802, WF-703 |
| LCK-804 | P1 | Espelhar/reconciliar restrições externas sem confundi-las com lock interno | LCK-801, INT-910 |

### EP9 — Exportação e primeiro conector

| ID | Prioridade | Item e entrega verificável | Dependência |
|---|---|---|---|
| INT-901 | P0 | Definir CanonicalSchemaVersion e contrato de compatibilidade | EN-001 |
| INT-902 | P0 | Definir LayoutVersion de importação/exportação genérica | INT-901 |
| INT-903 | P0 | Configurar conexão/rota com secret ref, tenant/empresa e capacidades | IAM-107, INT-902 |
| INT-904 | P0 | Gerar ExportBatch/Item imutável com manifesto, totais e payload hash | ACC-605, WF-706, LCK-802 |
| INT-905 | P0 | Validar layout e oferecer visualização antes do envio | INT-904 |
| INT-906 | P0 | Entregar com token idempotente e registrar cada tentativa | INT-903, INT-904 |
| INT-907 | P0 | Tratar timeout como UNKNOWN e consultar antes de reenviar | INT-906 |
| INT-908 | P0 | Tratar retorno parcial por item e reconciliar contagens/valores | INT-906 |
| INT-909 | P0 | Implementar primeiro conector usando a suíte comum de contratos | DEC-003, INT-903, EN-007 |
| INT-910 | P0 | Registrar ExternalAcknowledgement/PostingObservation autenticado | INT-907, INT-909 |
| INT-911 | P1 | SyncCheckpoint, retomada segura e mudança de layout detectável | INT-909 |

### EP10 — IA assistiva

| ID | Prioridade | Item e entrega verificável | Dependência |
|---|---|---|---|
| AI-1001 | P0 | Definir tarefas liberadas, contrato de saída, evidência e custo do erro | DEC-006, GOV-1101 |
| AI-1002 | P0 | Criar AIModelProfile/PromptTemplate versionados e redaction policy | AI-1001 |
| AI-1003 | P0 | Solicitar sugestão por gateway sem porta de aprovação/exportação | AI-1002, EN-007 |
| AI-1004 | P0 | Validar resposta, reason codes, evidências e confiança; inválida vira pendência | AI-1003, WF-701 |
| AI-1005 | P0 | Registrar SuggestionOutcome: aprovado, corrigido ou rejeitado e conta final | AI-1004, WF-703 |
| AI-1006 | P0 | Fallback determinístico quando IA estiver indisponível | AI-1003, RUL-503 |
| AI-1007 | P0 | Testar prompt injection e isolamento de contexto de tenant | AI-1003, SEC-001 |
| AI-1008 | P1 | Conjunto de avaliação segmentado por tarefa/layout e gate de nova versão | EN-008, AI-1005 |

### EP11 — Auditoria, segurança e governança de dados

| ID | Prioridade | Item e entrega verificável | Dependência |
|---|---|---|---|
| AUD-1101 | P0 | AuditEvent para sucesso, falha, negação, antes/depois minimizado e versões | EN-006 |
| AUD-1102 | P0 | Navegação por correlação da evidência ao retorno externo | EN-005, AUD-1101 |
| AUD-1103 | P0 | Trilha append-only com correção vinculada e detecção de adulteração | AUD-1101 |
| SEC-001 | P0 | Testes sistemáticos cross-tenant em DB, busca, cache, arquivo, job e IA | IAM-106 |
| SEC-002 | P0 | Segredos/redação: impedir token, credencial, XML, extrato ou prompt bruto em log | IAM-107, AUD-1101 |
| GOV-1101 | P0 | Inventário/classificação e DataUseAuthorization por finalidade | IAM-101 |
| GOV-1102 | P0 | Padrão negado para treinamento; inferência não implica melhoria/treinamento | GOV-1101, AI-1002 |
| GOV-1103 | P0 | Registrar DataProcessingRecord para inferências/exportações sensíveis | GOV-1101 |
| GOV-1104 | P0 | Política de retenção, descarte, legal hold e offboarding do tenant | GOV-1101, DEC-008 |
| BCP-1101 | P0 | Backup lógico completo e restauração testada sem mistura de tenants | DEC-009 |
| BCP-1102 | P1 | Exercício de recuperação e evidência de RPO/RTO acordados | BCP-1101 |

### EP12 — Operação e piloto

| ID | Prioridade | Item e entrega verificável | Dependência |
|---|---|---|---|
| OPS-1201 | P0 | ProcessingJob retomável, cancelável e tenant-aware | EN-005, IAM-106 |
| OPS-1202 | P0 | Painel de quarentena, falhas, UNKNOWN, retries e reconciliação | DOC-304, INT-907 |
| OPS-1203 | P0 | Métricas/alertas com severidade, responsável e runbook | AUD-1102 |
| OPS-1204 | P1 | Reprocessamento/replay com dry-run, diff e autorização | DOC-307, WF-703 |
| PERF-1201 | P0 | Medir jornadas com volume/sazonalidade acordados, sem relaxar guardrails | DEC-010 |
| PILOT-1201 | P0 | Onboarding controlado do primeiro escritório e conjunto de empresas | todas as P0 anteriores |
| PILOT-1202 | P0 | Execução paralela, reconciliação de resultados e aceite contábil | PILOT-1201 |
| PILOT-1203 | P0 | Go/no-go baseado em segurança, qualidade, operação e valor | PILOT-1202 |

## 5. Spikes e decisões bloqueadoras

| ID | Decisão/evidência necessária | Bloqueia |
|---|---|---|
| DEC-001 | Tipos/schemas/eventos de XML do piloto | XML-401 |
| DEC-002 | Formatos de extrato, timezone, sinal e correções | BNK-401 |
| DEC-003 | Sistema externo e capacidades do primeiro conector | INT-909 |
| DEC-004 | Granularidade de lançamento por documento/item/movimento | ACC-602 |
| DEC-005 | Precisão, arredondamento, moeda e tolerância de conciliação | ACC-603, REC-803 |
| DEC-006 | Tarefas de IA, evidências, limiares e custo por erro | AI-1001 |
| DEC-007 | Matriz inicial de papéis, alçadas, quórum e SoD | IAM-105, WF-705, LCK-803 |
| DEC-008 | Inventário LGPD, retenção, legal hold e encerramento | GOV-1104 |
| DEC-009 | SLA, RPO, RTO e frequência de restauração | BCP-1101 |
| DEC-010 | Volumes médios/picos e linha de base do piloto | PERF-1201 |
| DEC-011 | Estratégia física de isolamento e tecnologias | início da implementação física |

Não se atribuem estimativas até que DEC-001 a DEC-010 tenham evidência suficiente e a equipe esteja identificada.

## 6. Casos perigosos que bloqueiam release

1. Sem CompanyAccess, comando, consulta, job ou exportação é negado sem revelar existência do objeto.
2. ID de outro tenant não vaza por filtro, busca, arquivo, cache, log ou job atrasado.
3. Upload simultâneo do mesmo conteúdo produz um documento lógico e no máximo uma proposta.
4. Mesma chave externa com conteúdo diferente gera conflito, nunca substituição.
5. XML malformado, entidade externa, encoding inválido ou volume excessivo vai para quarentena sem efeito parcial.
6. Débitos/créditos fecham na precisão aprovada; arredondamento nunca é inventado silenciosamente.
7. Toda JournalLine aponta para origem e versões de parser, canônico, DE/PARA e regra.
8. IA, N0, N1 ou N2 não alcançam exportação sem aprovação humana válida; N3 fica desabilitado.
9. Aprovações concorrentes geram uma transição e um AuthorizedEffect.
10. Revisão aprovada/exportada não é editada; correção cria versão ou estorno vinculado.
11. Lock surgido entre validação e commit impede aprovação, reprocessamento e exportação.
12. Transação bancária não é sobre-alocada; empate/ambiguidade fica pendente.
13. Mesma entrada/release produz mesmo resultado de regra; mudança não altera histórico.
14. Campo de autoridade externa divergente abre M19, sem `last write wins`.
15. Timeout do conector vira UNKNOWN; consulta/reconciliação precede reenvio.
16. Retry de exportação conserva manifesto, payload e identidade e não duplica lançamento.
17. Texto de XML/extrato é dado não confiável e não modifica política/prompt privilegiado.
18. Resposta da IA inválida, sem evidência ou fora do limite vira pendência.
19. Indisponibilidade da IA não interrompe o fluxo determinístico.
20. Alteração material e AuditEvent mínimo são atômicos; segredo/dado bruto não vai ao log.
21. Reprocessamento oferece dry-run/diff e não substitui resultado aprovado.
22. Falha parcial apresenta totais conciliáveis de recebidos, válidos, rejeitados, duplicados e pendentes.
23. Normativa importada mas não aprovada não influencia regra, IA ou proposta.
24. Revogação de membership, CompanyAccess ou credencial vale também para sessão/job ainda pendente.
25. Restauração comprova integridade e ausência de mistura de tenants.

## 7. Definição de pronto

Uma story só está pronta quando:

- critérios positivos, negativos, concorrentes e de autorização estão automatizados;
- invariantes possuem testes unitários e, quando adequado, testes de propriedades;
- portas têm testes de contrato reutilizáveis por adaptador;
- existe teste de jornada e de falha para a fatia;
- fixtures são representativas, anonimizadas, versionadas e autorizadas;
- schemas/eventos mantêm compatibilidade ou migração explícita;
- auditoria, proveniência, idempotência e métricas estão presentes;
- erros são acionáveis e sem dados sensíveis;
- há procedimento testado de retry, recuperação, replay ou reversão;
- domínio não depende de framework e limites de importação passam;
- houve revisão de segurança, privacidade e especialista contábil;
- impacto de migração e retrocompatibilidade foi avaliado;
- desempenho foi medido no volume acordado.

Um slice só está pronto quando a jornada funciona ponta a ponta em ambiente semelhante ao produtivo, inclusive falha intermediária, retry, reprocessamento, bloqueio, totais e recuperação.

## 8. Métricas do MVP

### Guardrails fixos

- Vazamentos entre tenants: **0**.
- Propostas aprovadas desbalanceadas: **0**.
- Efeitos externos sem aprovação válida: **0**.
- Duplicidades externas por retry: **0**.
- JournalLines sem proveniência: **0**.
- Transições materiais sem auditoria: **0**.
- Cobertura auditável das ações materiais: **100%**.

### Baseline e evolução

- Ingestão: aceitos/recebidos, duração, duplicados, quarentena e reprocessamentos.
- Canônico: issues por layout/campo e conflitos de autoridade.
- Regras: cobertura, conflito, override e regressão por versão.
- M19: tempo mediano/p95, idade, SLA vencido, rejeição e reabertura.
- Conciliação: cobertura, precisão confirmada, parcialidade, desfazimentos e tempo.
- Exportação: sucesso inicial, tempo até recibo e itens UNKNOWN.
- IA: aceite sem edição, correção por categoria, evidência válida, indisponibilidade e custo.
- Operação: minutos humanos por 100 documentos/transações e impacto no fechamento.
- Engenharia: lead time por slice, falha de mudança, recuperação e quebra de contrato.

Todas as métricas precisam ser segmentáveis por tenant, empresa, layout, regra/modelo e origem; médias globais não podem esconder risco.

## 9. Registro de aprovação e próximos gates

**Backlog S0 a S8 aprovado como base em 02/09/2026.** A aprovação cobre escopo, sequência e critérios; ainda não constitui compromisso de prazo. Próximos gates:

1. resolver DEC-001 a DEC-010;
2. decompor cada P0 com exemplos contábeis reais e fixtures autorizadas;
3. estimar com a equipe que executará o trabalho;
4. escolher tecnologias após comparar requisitos, volume, segurança, custo e competência da equipe;
5. aprovar arquitetura e modelo de dados antes do primeiro código de produção.
