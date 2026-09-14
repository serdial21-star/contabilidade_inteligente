# UX Status Language

Vocabulário de apresentação da Phase 02. Não introduz enum no backend. Sempre interpretar o status dentro do recurso/módulo; `APPROVED` de política de privacidade não é aprovação contábil. Fontes inspecionadas: `workflow/application/services/nfe_to_dominio.py`, `workflow/domain/entities.py`, `operations/domain/entities.py`, `locks/domain/entities.py`, sob `src/serdial21/modules/`, e [API operacional](OPERATIONAL_API_MVP.md).

| DOMAIN STATUS | DISPLAY LABEL | COLOR TOKEN | ICON | DESCRIPTION |
| --- | --- | --- | --- | --- |
| Journey `IMPORTED` | Recebido / importado | info | file | Importação registrada; não implica proposta aprovada. |
| Journey `EVALUATED` | Regra avaliada | info | check | Avaliação determinística, sem decisão profissional. |
| Journey `VALIDATED` | Validado | info | check | Validação da revisão, não aprovação humana. |
| Journey `DRAFT` | Rascunho | neutral | file | Revisão ainda não aprovada. |
| Journey `IN_REVIEW` | Em revisão | warning | clock | Encaminhada à revisão; não prova leitura humana. |
| Journey `PENDING_APPROVAL`; ApprovalRequest/Step `PENDING` | Aguardando aprovação | warning | clock | Requer decisão válida, revisão/hash e alçada. |
| Journey `PENDING_RULE` | Exceção · regra pendente | warning | alert | Não inventar regra ou gerar aprovação para completar fluxo. |
| Journey `QUARANTINED` | Em quarentena | danger | alert | Divergência/condição de importação exige tratamento. |
| Journey/ApprovalDecision `APPROVED` | Aprovado por profissional | success | check | Exibir ator e timestamp quando disponíveis; não atesta escrituração externa. |
| Journey/ApprovalDecision `REJECTED` | Rejeitado por profissional | danger | close | Decisão humana negativa, preservada no histórico. |
| Job `BLOCKED`; AccountLock `ACTIVE` que impede efeito | Bloqueado / Período bloqueado | danger | lock | `ACTIVE` é estado real do lock; `BLOCKED` no mock de documento é estado visual composto, não novo status de Journey. |
| AccountLock `RELEASED` | Bloqueio liberado | neutral | lock | Não retoma automaticamente trabalho. |
| Job `RUNNING` | Processando | info | clock | A chave de galeria `PROCESSING` é apresentação demonstrativa, não enum enviado à API. |
| Sem mapeamento único no recorte | Inativo | neutral | info | Chave `INACTIVE` da galeria é conceitual; mapear por recurso em fase de integração. |
| Estado não reconhecido | Estado indisponível | neutral | info | Não inferir sucesso ou revelar erro interno. |

“Processados automaticamente” é indicador, “Exceções” é agrupamento e “Sugestão inteligente” é origem/qualificação visual; nenhum deles é um status de aprovação. Chaves da galeria são isoladas de contratos reais, sem nova API ou migration.

Padrões humanos: REVISADO POR, APROVADO POR, REJEITADO POR + ator + instante + decisão, quando a fonte os fornece. Eventos de revisão aberta/lida não existem no contrato atual: o exemplo REVISADO POR é mock explícito. Abrir a tela não registra revisão. O campo `origin=HUMAN` de transições coordenadas da jornada não permite concluir que todo processamento foi manual; usar ação e contexto conforme [PRODUCT_FLOW](PRODUCT_FLOW.md).
