# Serdial21 — Arquitetura Modular Python

| Controle | Valor |
|---|---|
| Status | **APROVADA — sem código de produção** |
| Versão | 1.0 |
| Baseline | Arquitetura macro e modelo lógico v0.1 |
| Aprovação | PY-01 a PY-08 aprovadas pelo responsável do produto em 02/09/2026 |
| Objetivo | Definir pacotes, responsabilidades, dependências e contratos internos |

## 1. Estrutura proposta

```text
src/
  serdial21/
    bootstrap/                  # composição, configuração e ciclo de vida
    shared_kernel/              # IDs, Money, datas, contexto, erros e envelopes; mínimo
    modules/
      access_control/
      company_registry/
      intake_documents/
      fiscal_documents/
      banking/
      chart_of_accounts/
      mappings/
      accounting_rules/
      accounting_core/
      reconciliation/
      accounting_controls/
      workflow_m19/
      ai_assistance/
      integration_hub/
      audit_governance/
      operations/
    entrypoints/                # web/API, CLI administrativa, consumers e scheduler

tests/
  architecture/                # limites de importação e dependência
  unit/                        # invariantes e políticas puras
  contracts/                   # portas, eventos, layouts e conectores
  integration/                 # persistência, filas, storage e fornecedores
  journeys/                    # verticais XML e bancária ponta a ponta
  security/                    # tenancy, permissões e conteúdo hostil
  performance/                 # volumes acordados do piloto
  fixtures/                    # XML/extratos anonimizados e versionados
```

Estrutura interna uniforme:

```text
<module>/
  domain/
    entities/                  # agregados e entidades
    value_objects/             # Money, competência, códigos e fingerprints locais
    policies/                  # invariantes e decisões puras
    services/                  # serviços de domínio sem infraestrutura
    events/                    # fatos publicados pelo módulo
  application/
    commands/                  # intenção de mudança
    queries/                   # leitura autorizada
    handlers/                  # orquestração de caso de uso
    dto/                       # entrada/saída sem ORM
    ports/                     # interfaces exigidas pelo módulo
  contracts/
    public_api/                # fachada para outros módulos
    events/                    # schemas versionados
  adapters/
    inbound/                   # consumidores específicos, quando pertencentes ao módulo
    outbound/                  # persistência, storage e serviços externos
```

Essa árvore é uma convenção arquitetural, não uma exigência de um arquivo por item.

## 2. Regras de dependência

1. Adaptadores e entrypoints dependem de aplicação; aplicação depende de domínio e portas.
2. Domínio é Python puro: não importa framework, ORM, HTTP, fila, arquivo, SDK de nuvem ou provedor de IA.
3. Um módulo não consulta nem grava diretamente o repositório privado de outro.
4. Comunicação entre módulos ocorre por fachada pública, consulta autorizada ou evento versionado.
5. `shared_kernel` só contém conceitos comprovadamente universais; não recebe `Account`, `JournalEntry`, regra, reconciliação ou lock.
6. Relógio, IDs, contexto de autorização, transação, repositórios e publicadores são injetados por portas.
7. Todo comando carrega tenant, empresa quando aplicável, ator, canal, correlação, causalidade e idempotency key.
8. IA e conector recebem portas mínimas; nunca uma interface genérica de mutação.
9. M19 autoriza versão/hash; o domínio proprietário revalida decisão, permissão, bloqueio e concorrência.
10. Testes de arquitetura falham o build se um módulo violar os imports autorizados.

## 3. Responsabilidades por pacote

| Pacote | Objetos próprios | Contratos públicos principais | Dependências permitidas |
|---|---|---|---|
| `access_control` | Tenant, Membership, Role, Permission, CompanyAccess, ServicePrincipal | resolver contexto; autorizar ação; emitir revogação | shared kernel; provedor de identidade via porta |
| `company_registry` | Company, Establishment, Party, CostCenter, DomainAuthorityPolicy | consultar versão canônica e autoridade | access context; referências externas por contrato |
| `intake_documents` | EvidenceArtifact, Receipt, ImportBatch/Item, TransformationRun, issues | receber; selar; deduplicar; quarentenar; reprocessar | storage/antivírus/parser por portas |
| `fiscal_documents` | FiscalDocument/Item/Tax/Event | detectar schema; validar; normalizar; explicar erro | intake e schemas canônicos |
| `banking` | BankAccount, Statement, Transaction | validar/normalizar/deduplicar extrato | intake e company registry |
| `chart_of_accounts` | Chart, Account, AccountVersion, referência | resolver conta vigente e lançável | company registry |
| `mappings` | MappingSet/Version/Entry | resolver DE/PARA; simular; explicar conflito | chart/company por contratos de leitura |
| `accounting_rules` | Rule/Version, RuleSetRelease, Evaluation | publicar release; avaliar deterministicamente; trace | canônico, mapping e contas por contratos |
| `accounting_core` | Ledger, Period, Proposal, JournalEntry/Revision/Line, batch | criar/validar/revisar proposta; autorizar materialização | regras, contas e controles por fachadas |
| `reconciliation` | Reconciliation, Match, Participant, Allocation, Exception | gerar candidatos; propor; aprovar versão; reabrir | banking, accounting core e workflow por contratos |
| `accounting_controls` | ExternalPeriodObservation, AccountLock, period lock | verificar guardas; bloquear; liberar; requerer revisão | access, workflow e accounting refs |
| `workflow_m19` | WorkflowCase, WorkItem, Assignment, ApprovalRequest/Decision, AuthorizedEffect | abrir tarefa; atribuir; solicitar/registrar decisão | access; objetos externos somente por referência/version |
| `ai_assistance` | Profile, PromptTemplate, InferenceRun, Suggestion, Explanation, Outcome | solicitar sugestão; validar envelope; registrar feedback | projeções permitidas e provedor via portas |
| `integration_hub` | Connector/Layout, Connection/Route, Import/Export, Delivery/Ack | transformar; entregar; consultar; reconciliar | canônico e efeitos autorizados |
| `audit_governance` | Audit/Security/DataAccess Event, DataUse, Retention, LegalHold | registrar evidência; consultar autorizadamente | contexto e commit hook; sem mutação dos módulos |
| `operations` | ProcessingJob, failure, retry, metric, alert | agendar; retomar; cancelar com segurança; observar | contratos públicos de casos de uso |

## 4. Decisões Python propostas

| ID | DECISÃO | MOTIVO | ALTERNATIVAS | IMPACTOS | RECOMENDAÇÃO |
|---|---|---|---|---|---|
| PY-01 | Forma do produto Python | MVP precisa consistência sem sobrecarga operacional | Microsserviços; monólito comum; monólito modular | Modular exige disciplina, mas reduz distribuição e mantém opção de extração | **Um projeto implantável com módulos isolados e workers** |
| PY-02 | Dependência do domínio | Regras precisam ser rápidas, reprodutíveis e testáveis | Domínio acoplado a ORM; scripts; domínio puro | Domínio puro exige mapeamento, mas evita aprisionamento | **Domínio e políticas em Python puro** |
| PY-03 | Compartilhamento | Shared kernel grande recria acoplamento | Biblioteca global rica; duplicação; kernel mínimo | Alguma duplicação local é preferível a domínio global confuso | **Kernel mínimo e contratos explícitos** |
| PY-04 | Regras configuráveis | Código arbitrário compromete segurança e reprodutibilidade | `eval`/scripts; plugins Python; linguagem declarativa | DSL declarativa requer parser/validador, mas permite simulação e governança | **Condições/ações declarativas, sem Python arbitrário** |
| PY-05 | Conectores | Fornecedor não pode contaminar o núcleo | SDK usado no domínio; adaptador por fornecedor | Adaptador repete código operacional controlado | **Porta canônica + layout + adapter específico com testes de contrato** |
| PY-06 | IA | Provedor e resposta são não determinísticos | SDK espalhado; agente privilegiado; gateway | Gateway cria envelope e fallback, reduzindo acoplamento/risco | **AI gateway que retorna apenas SuggestionEnvelope validado** |
| PY-07 | Transação e eventos | Efeito e auditoria não podem divergir | auditoria posterior; transação distribuída; UoW/outbox | UoW/outbox exige infraestrutura e disciplina | **Unit of Work local com audit record e outbox no mesmo commit** |
| PY-08 | Leitura entre módulos | Acesso direto a tabelas destrói ownership | ORM compartilhado; views; query contracts | Contratos podem duplicar read models, mas protegem fronteiras | **Fachadas/queries públicas e projeções autorizadas** |

## 5. Unidade de trabalho e efeitos

Ordem de um comando mutável:

1. autenticar e resolver `ExecutionContext`;
2. validar membership, CompanyAccess, permissão e segregação;
3. resolver idempotency key e recuperar resultado anterior, se houver;
4. carregar agregado pelo repositório do módulo, já no escopo tenant/company;
5. revalidar versão, período e AccountLock;
6. executar política/invariante de domínio;
7. persistir agregado, evento mínimo de auditoria e outbox no mesmo commit;
8. publicar eventos depois do commit;
9. realizar efeitos externos em worker;
10. registrar tentativa/acknowledgement e atualizar projeção por novo comando.

Não há chamada a fornecedor dentro da transação de negócio. Timeout externo gera estado recuperável, não rollback ilusório de algo possivelmente aceito.

## 6. Contratos fundamentais

### ExecutionContext

Carrega identidade, tenant, empresa, membership, CompanyAccess, permissões efetivas, canal, correlação, causalidade e finalidade de tratamento. Valores declarados pelo request são comparados ao contexto autorizado, não confiados isoladamente.

### CommandEnvelope e EventEnvelope

Incluem ID/schema version, contexto, agregado/version, correlação, causalidade, instante e idempotency key. Payloads são tipados e minimizados.

### SuggestionEnvelope

Inclui tarefa, saída estruturada, confiança, reason codes, evidências, perfil/modelo/template/redaction versions, limitações e idempotency key. Não expõe método para aprovar ou exportar.

### ConnectorPort

Capacidades mínimas: validar conexão, declarar capacidades, preparar entrega, enviar uma identidade idempotente, consultar recibo e reconciliar estado UNKNOWN.

### LayoutPort

Detectar versão, validar, transformar para/do canônico, gerar erros por campo e produzir manifesto/hash. Regra contábil não pertence ao layout.

### AuthorizationPort e ControlGuardPort

Autorização responde se o ator pode tentar a ação; ControlGuard valida se o estado atual permite o efeito. Ambos são necessários no instante da mudança.

## 7. Estrutura de conectores

```text
integration_hub/adapters/connectors/<system_name>/
  capabilities
  configuration_schema
  client
  inbound_adapter
  outbound_adapter
  acknowledgement_mapper
  error_classifier
  contract_tests
```

- Nenhum conector define `JournalEntry` próprio; traduz o contrato canônico.
- Segredos são obtidos por `SecretProviderPort` e nunca serializados em config/audit.
- Erros são classificados como transitório, permanente, autenticação, limite, conflito, parcial ou estado desconhecido.
- Cada conector executa a mesma suíte de contratos de idempotência, retorno e isolamento.

## 8. Motor de regras e níveis de automação

- Condições e ações usam representação declarativa versionada.
- A compilação/validação ocorre antes da publicação.
- Toda release contém testes, ordem, precedência e estratégia de conflito.
- A execução produz trace reproduzível e proposta; não grava diretamente em outro módulo.
- Resultado conflitante/sem conta válida abre pendência.

Níveis registrados:

- **N0:** somente sugestão.
- **N1:** sugestão com aprovação humana.
- **N2:** etapa preparatória por regra determinística validada; efeito contábil ainda exige aprovação no piloto.
- **N3:** automação com revisão por amostragem, modelada mas desabilitada para efeito externo no MVP.

Não existe objetivo genérico de autonomia total. Promoção de nível exige métricas, release aprovada e decisão de governança.

## 9. Estratégia de testes no repositório

| Suíte | Objetivo |
|---|---|
| `architecture` | Proibir imports de framework no domínio e acesso privado entre módulos |
| `unit` | Invariantes, estados, políticas e propriedades contábeis |
| `contracts` | Mesma expectativa para repositórios, layouts, conectores, storage e IA |
| `integration` | Transação, constraints, inbox/outbox, retry e adaptadores reais controlados |
| `journeys` | XML e extrato até aprovação/exportação/retorno |
| `security` | cross-tenant, permissões, prompt injection, documentos hostis e segredo em log |
| `performance` | lote, fechamento/sazonalidade e filas conforme volume do piloto |

Fixtures precisam ser representativas, anonimizadas, versionadas e vinculadas à autorização de uso.

## 10. Caminho de extração futura

Um módulo só se torna serviço separado quando houver justificativa mensurável, como escala independente, isolamento de dados/risco, disponibilidade distinta ou equipe proprietária. Candidatos naturais, sem decisão antecipada:

- processamento documental pesado;
- gateway de IA;
- worker de conector de alto risco;
- auditoria/analytics;
- pesquisa normativa.

Pré-condições: contratos versionados, ownership de dados, outbox/inbox, observabilidade e testes de contrato já funcionais dentro do monólito.

## 11. Decisões tecnológicas ainda pendentes

- Versão e distribuição Python suportadas.
- Convenção de nomes no código e idioma do domínio.
- Framework web/API e validação de DTOs.
- ORM/data mapper e estratégia de migrations.
- SGBD, storage, busca e fila.
- Provedor de identidade e secrets.
- Observabilidade e execução de workers.
- Provedores/modelos de IA e política de fallback.
- Empacotamento/deploy e ambientes.

Essas escolhas devem comparar perfil da equipe, volume, segurança, custo, manutenção e portabilidade antes de virar ADR aprovado.
