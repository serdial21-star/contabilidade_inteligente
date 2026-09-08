# Encerramento da Execução 27 — gate de banco do piloto

Data da decisão: 08/09/2026

## Decisão

`DATABASE RUNTIME GATE: PASS_FOR_PILOT`

`MIGRATION HARNESS: DEFERRED_HARDENING`

`WORKFLOW_AFTER_UNLOCK: DEFERRED_NOT_IN_PILOT_SCOPE`

A Execução 27 está encerrada para avanço do piloto. Essa decisão não declara
que toda a suíte histórica e state-specific do Migration Lab passou. O caminho
operacional do piloto é forward-only e não usa downgrade de schema como forma
de recuperação.

## Banco homologado e evidências consolidadas

O banco homologado do piloto é MariaDB 11.8.x, tendo sido exercitada a versão
11.8.8 por meio do dialeto `mysql+pymysql`. O Runtime dedicado é
`u621451815_serdial21_hom` e foi confirmado em `20260907_0009` (HEAD).

As evidências obtidas nas execuções anteriores e aceitas nesta decisão são:

- migrations 0001–0008 comprovadas em `base -> head` e `head -> base -> head`;
- correção de downgrade/FK da migration 0002 comprovada;
- correção de collation/FK composta da migration 0006 comprovada;
- migration 0009 comprovada em `0008 -> 0009 -> 0008 -> 0009`;
- AccountLock ORM, repositório SQLAlchemy, criação, liberação e guard persistido
  aprovados;
- estado `BLOCKED`, liberação autorizada e negação de liberação não autorizada
  comprovados;
- isolamento tenant/company dos locks comprovado;
- AuditEvent de lock e rollback atômico de lock + AuditEvent comprovados;
- unicidade concorrente de lock `ACTIVE` comprovada;
- Runtime e Migration Lab comprovadamente separados.

Nenhuma migration 0001–0009 foi alterada por esta decisão.

## Incidente do harness

Os testes históricos de migrations não são completamente herméticos: alguns
dependem de uma combinação específica entre revision registrada e schema
físico. O incidente observado deixou o Migration Lab state-specific com HEAD
registrado e schema divergente. Isso é um problema do harness de teste, não uma
evidência de defeito no Runtime homologado.

O Migration Lab nunca pode ser apontado para o Runtime. A suíte destrutiva não
é gate do piloto e não deve ser reexecutada até existir ambiente efêmero e
descartável adequado.

## Política de migration do piloto

`RUNTIME MIGRATION POLICY = FORWARD_ONLY`

No piloto é permitido somente upgrade versionado, revisado e previamente
testado. Downgrade de schema é proibido como mecanismo de recuperação
operacional. A recuperação deve ocorrer por backup lógico validado e restore
testado em destino distinto do Runtime.

## Dívida técnica

`MIGRATION_HARNESS_STATEFUL`

Os testes históricos de migrations dependem de preparação específica de
revision/schema e ainda não são completamente herméticos. O hardening fica
destinado a CI futuro com banco efêmero/descartável apropriado. Essa dívida é
não bloqueante para o piloto e os testes não podem ser executados no Runtime.

## Workflow após desbloqueio

`WORKFLOW_AFTER_UNLOCK = NOT_IN_PILOT_SCOPE`

Não existe contrato persistente aprovado que automatize `release -> alteração
-> nova revisão -> DRAFT -> REQUIRES_REVIEW`. Nenhuma futura API ou borda do
piloto pode prometer ou expor esse fluxo como funcionalidade suportada. O tema
permanece no backlog funcional e não é classificado como defeito do MariaDB.

## Conclusão

`DATABASE RUNTIME GATE: PASS_FOR_PILOT`

O encerramento remove o banco Runtime e a política de migrations do conjunto de
bloqueadores do piloto, sem remover os gates independentes de backup/restore,
identidade, privacidade, operação e integrações externas.
