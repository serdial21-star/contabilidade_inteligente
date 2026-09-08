# Persistência de AccountLock

## Decisão e escopo

A Execução 27G identificou que `AccountLock` existia apenas no domínio e em
fixtures. A arquitetura aprovada na 27H-R autorizou uma camada persistente sem
alterar a entidade, seus escopos, operações ou regras de bloqueio.

## Estrutura criada

A revision `20260907_0009_account_locks` cria `account_locks` após 0008, com
InnoDB, `utf8mb4` e `utf8mb4_unicode_ci`. A tabela replica os campos existentes
do domínio: tenant/company, escopo, operações, motivo, status, alvo único,
dados de release e timestamp técnico. A FK composta `(tenant_id, company_id)`
referencia `companies(tenant_id, id)`.

`scope_fingerprint` é SHA-256 do JSON canônico `{scope,target}`, onde target é
exatamente o alvo já usado por `_matches`: account, group, module, competência
ou exercício. `active_marker` é `ACTIVE` para locks ativos e `NULL` após
release. O UNIQUE `(tenant_id, company_id, scope_fingerprint, active_marker)`
permite histórico liberado e impede dois locks ativos equivalentes no MariaDB.

O adapter `SQLAlchemyAccountLockRepository` mapeia explicitamente ORM e
domínio, exige tenant em `get` e limita consulta ativa a tenant/company. Não
contém regra contábil.

## Evidência atual

O upgrade 0008 -> 0009 passou no banco MariaDB de homologação; engine,
collation e UNIQUE foram inspecionados. Os testes locais de migrations e locks
passaram.

## Limitações pendentes

O projeto ainda não possui UnitOfWork explícita, composição persistente de
locks, nem casos de uso de criação/release que coordenem AccountLock e
AuditEvent. Por isso a atomicidade, autorização, guard de produção, round-trip
de repository, concorrência, downgrade 0009 e jornadas de unlock ainda exigem
uma execução posterior; não são declarados como comprovados por este documento.
## Integração 27H-S

O padrão transacional existente foi preservado: `session_scope` abre a
`Session`, confirma somente após o retorno do caso de uso e executa rollback
em toda exceção. `SQLAlchemyAccountLockRepository` e
`SqlAlchemyAuditRepository` recebem a mesma `Session`; nenhum deles faz
`commit()` ou abre transação autônoma.

`bootstrap.locks.create_account_lock_runtime(session)` compõe a implementação
persistente com `AuthorizationService`, `AuditService`,
`SQLAlchemyAccountLockRepository`, `CreateAccountLock`, `ReleaseAccountLock`
e `PersistedAccountLockGuard`. A autorização reutilizada é a permission
atômica existente `lock.manage`, incluindo revalidação de membership,
CompanyAccess e escopo tenant/company pela fronteira central.

`CreateAccountLock` chama exclusivamente `create_lock` do domínio, persiste o
resultado e grava `account_lock.created`. `ReleaseAccountLock` faz lookup
tenant-aware, chama `AccountLockService.release`, mantém o histórico com
`active_marker = NULL` e grava `account_lock.released`. Ambos fazem `flush`
apenas para detectar falhas antes do retorno; commit/rollback continuam no
chamador. A colisão da UNIQUE de lock ativo é exposta como
`AccountLockConflictError`, sem vazar `IntegrityError` na interface de
aplicação.

O guard persistente carrega somente locks ativos pelo repository e chama
`validate_effect` do domínio. Assim a composição persistente não consulta
`SyntheticCatalog.current_locks`; o catálogo sintético continua restrito aos
testes de jornada já existentes.

Testes locais cobrem criação, persistência, bloqueio, release autorizado e
negado, eventos, rollback create+audit e unicidade. A homologação MariaDB
comprovou persistência entre sessões, `BLOCKED` pelo guard persistente,
CompanyAccess/tenant-aware lookup, release negado e autorizado, rollback de
create e release junto de seus eventos, e duas sessões concorrentes com uma
única criação e um conflito controlado. Inclui também pre-flight protegido e
o ciclo controlado `0009 -> 0008 -> 0009`.

Não existe nesta fatia um caso de uso persistente de alteração pós-release que
produza workflow `DRAFT`/`REQUIRES_REVIEW`; portanto essa evidência é
`NOT_APPLICABLE_FOR_27H-S` e pertence à 27I. O cenário de release/create
simultâneo não recebeu semântica adicional nesta fatia: a UNIQUE física
continua garantindo que não existam dois locks ativos equivalentes.
