# Data Ownership Matrix

Cada linha possui uma autoridade única. “Sincronização” significa projeção/contrato, nunca tabela compartilhada ou FK entre bancos.

| Dado/domínio | Master | Consumidor | Direção | Frequência | Política de conflito |
| --- | --- | --- | --- | --- | --- |
| Perfil administrativo do cliente | Sistema A | B | A→B | por evento + reconciliação | A vence campos operacionais; ambiguidade vai a revisão |
| CNPJ cadastral | Sistema A | B | A→B | por evento | normalizar 14 dígitos; mudança não reatribui automaticamente vínculo |
| Contatos | Sistema A | B somente se necessário | A→B | por evento | minimizar; A vence |
| Relação/pasta Google Drive | Sistema A | B recebe referência temporária | A→B sob demanda | por documento | A vence; estrutura não entra no core B |
| Tarefas operacionais/Kanban | Sistema A | B recebe ref/status | B solicita; A retorna | por evento | lifecycle de A; conclusão não aprova no B |
| Tickets | Sistema A | B quando necessário | A→B futura | por evento | A vence |
| Agenda | Sistema A | nenhum no MVP | — | — | A vence |
| Obrigações | Sistema A | B futuro | A→B | futura | A vence estado operacional |
| Guias/impostos publicados | Sistema A | B futuro | A→B | futura | A vence publicação/entrega |
| Honorários | Sistema A | nenhum no MVP | — | — | A vence |
| Comunicações WhatsApp/e-mail | Sistema A | B recebe recibo se aprovado | A↔B futura | por evento | A vence canal/entrega |
| Arquivo operacional enviado pelo cliente | Sistema A | B por secure pull | A→B | por evento | A vence disponibilidade operacional |
| Evidência imutável usada no processamento | Sistema B | A recebe status/ref | B→A | por processamento | B vence hash, cadeia e retenção própria |
| Processamento fiscal | Sistema B | A | B→A | por evento | B vence |
| Extratos/processamento bancário | Sistema B | A futuro/minimizado | B→A | por evento | B vence |
| Configuração de inteligência contábil | Sistema B | A não edita | — | — | B vence |
| Plano/contas canônicas do produto | Sistema B | A recebe projeção apenas se aprovada | B→A | futura | B vence; sistema contábil externo continua autoridade oficial |
| Regras e DE/PARA | Sistema B | A recebe status, não conteúdo autoritativo | B→A | por evento necessário | B vence; versões publicadas imutáveis |
| Propostas contábeis | Sistema B | A recebe status/ref | B→A | por evento | B vence |
| Aprovações/rejeições | Sistema B | A recebe projeção | B→A | por evento | B vence; decisão humana/autorização no B |
| `AccountLock` | Sistema B | A recebe alerta/status se necessário | B→A | por evento | B vence; A não desbloqueia |
| Auditoria do processo contábil | Sistema B | A não replica integralmente | — | consulta autorizada | B vence e é append-oriented |
| Auditoria operacional | Sistema A | B não replica integralmente | — | consulta autorizada | A vence |
| Publicações no portal do cliente | Sistema A | B recebe confirmação | B solicita; A publica | por evento | A vence publicação/canal |

## Identidade e referência externa

Chave lógica proposta:

```text
external_system = SERDIAL21_OPERATIONAL
external_type   = CLIENT
external_id     = <ID opaco do Sistema A>
business_key    = CNPJ normalizado (dígitos, 14 caracteres)
```

CNPJ é identificador de correlação, não ID técnico imutável nem autorização. Correções, matriz/filial, registros duplicados e entidades futuras exigem referência externa persistida. PKs continuam locais. O Sistema B não demonstra hoje uma capacidade genérica desse mapeamento: `EXTERNAL_REFERENCE_GAP` de implementação, resolvido antes da Wave 2.

## Módulos do Sistema A

| Módulo | Classificação | Decisão |
| --- | --- | --- |
| Clients | `KEEP_IN_OPERATIONAL` + `INTEGRATE` | mestre cadastral |
| Team / Permissions | `KEEP_IN_OPERATIONAL` | não reutilizar como autorização B |
| Tickets | `KEEP_IN_OPERATIONAL`; `INTEGRATE` later | lifecycle em A |
| Documents | `KEEP_IN_OPERATIONAL` + `INTEGRATE` | arquivo operacional A; evidência B quando processada |
| Kanban | `KEEP_IN_OPERATIONAL` + `INTEGRATE` | tarefa em A; corrigir persistência |
| Agenda | `KEEP_IN_OPERATIONAL` | fora do MVP |
| Taxes / Obrigações | `KEEP_IN_OPERATIONAL`; `INTEGRATE` later | evitar duplicação |
| Honorários | `KEEP_IN_OPERATIONAL` | fora do B |
| Client Portal | `KEEP_IN_OPERATIONAL` + `INTEGRATE` | reutilizar, não reconstruir no B |
| Fiscal IA | `DUPLICATION_TO_AVOID` / `POTENTIAL_RETIREMENT` | após equivalência, B deve concentrar inteligência fiscal |
| AI tools | `OUT_OF_SCOPE` | avaliar separadamente; sem autoridade |
| Shortcuts | `KEEP_IN_OPERATIONAL` | UX local, sem contrato core |

## Módulos do Sistema B

Companies integra cadastro sem virar CRM; Documents guarda evidência processada; Minha Visão, Fiscal, Financial, Accounting, Rules, Proposals, AccountLock, Audit e Decision Line permanecem no B. O conceito futuro de Client Portal torna-se redundante: deve ser substituído por integração/deep links/componentes autorizados no portal A, não por um segundo portal.
