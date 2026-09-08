# Runbook de backup e restore MariaDB — piloto

## Objetivo e escopo

Este runbook protege o banco Runtime `u621451815_serdial21_hom` por backup
lógico e comprova a recuperação exclusivamente no Restore Lab descartável
`u621451815_serdial21_mig`.

O Runtime nunca pode receber `DROP`, restore ou downgrade durante o ensaio. A
política de migrations do piloto é forward-only.

## Responsabilidades

- Operador de infraestrutura: executa backup/restore e guarda o artefato;
- Engenharia responsável: confere guards, hash, schema e contagens;
- Responsável do piloto: aprova janela, retenção e eventual cutover em incidente;
- Responsável contábil/privacidade: autoriza acesso a dados e retenção.

Uma única pessoa não deve executar e aprovar a mesma recuperação real quando a
equipe do piloto permitir segregação.

## Ferramentas homologadas

O ambiente de 08/09/2026 possui MySQL Community Client 8.4.9:

- `mysqldump.exe` 8.4.9;
- `mysql.exe` 8.4.9.

`mariadb-dump`, `mysqldump`, `mariadb` e `mysql` não estavam no `PATH`; os dois
clientes MySQL foram encontrados em `C:\Program Files\MySQL\MySQL Server 8.4\bin`.

## Segredos e armazenamento

- nunca informar senha em argumento da linha de comando;
- usar provedor de segredos, `MYSQL_PWD` apenas no ambiente restrito do
  subprocesso, ou `--defaults-extra-file` protegido por ACL e fora do Git;
- apagar a variável do processo imediatamente após a chamada;
- nunca gravar credenciais, URL ou dados do dump em logs;
- armazenar dumps em `.backups/`, que deve permanecer ignorado pelo Git;
- criptografar o artefato em repouso antes de copiá-lo para armazenamento
  externo aprovado;
- limitar leitura aos responsáveis operacionais e registrar acesso/remoção.

Backup gerenciado pela Hostinger, quando habilitado e comprovado no painel,
complementa a estratégia. Ele não substitui o backup lógico da aplicação nem o
teste de restore.

## Guard obrigatório

Antes do backup, executar em conexão read-only:

```sql
SELECT VERSION(), DATABASE(),
       (SELECT version_num FROM alembic_version);
```

O backup só prossegue se `DATABASE()` retornar
`u621451815_serdial21_hom` e a revision esperada for HEAD.

Antes de qualquer restore, repetir o guard na conexão de destino. O único
resultado permitido é `u621451815_serdial21_mig`. Se retornar
`u621451815_serdial21_hom`, interromper imediatamente e abrir incidente.

## Gerar o backup

Executar `mysqldump` com credencial fora da linha de comando e estas opções:

```text
--single-transaction --quick --skip-lock-tables --no-tablespaces
--default-character-set=utf8mb4 --hex-blob --set-gtid-purged=OFF
--column-statistics=0 --triggers --add-drop-table
```

O database de origem deve ser explicitamente
`u621451815_serdial21_hom`. Redirecionar stdout diretamente para um novo arquivo
`.backups/serdial21-runtime-<UTC>.sql`; não imprimir o dump no terminal.

Registrar em evidência separada:

- timestamp UTC de início e fim;
- versão do servidor e do cliente;
- revision Alembic;
- nome do arquivo e tamanho em bytes;
- SHA-256 em minúsculas;
- código de saída e mensagens sanitizadas.

## Validar o backup

Sem exibir seu conteúdo:

1. confirmar existência e tamanho maior que zero;
2. calcular SHA-256 e registrá-lo fora do dump;
3. confirmar presença de DDL e referências a `alembic_version`,
   `audit_events` e `account_locks`;
4. confirmar que não há URL de conexão ou credencial conhecida no artefato;
5. executar `git check-ignore` para o arquivo;
6. capturar contagens read-only do Runtime no instante do backup.

Backup sem restore validado não é considerado recuperável.

## Restaurar no Lab

1. verificar novamente que o destino é `u621451815_serdial21_mig`;
2. verificar o SHA-256 do arquivo contra a evidência registrada;
3. confirmar que o Lab não contém dado exclusivo que precise ser preservado;
4. importar o dump com `mysql.exe`, usando a credencial do Lab fora da linha de
   comando e o database explicitamente informado;
5. deixar que o dump lógico aplique seu mecanismo normal de criação/remoção de
   tabelas; não usar `FOREIGN_KEY_CHECKS=0` como workaround de migration;
6. registrar duração, código de saída e erros sanitizados.

## Validação pós-restore

Executar somente leituras no Restore Lab:

- `alembic_version = 20260907_0009`;
- mesmas tabelas do Runtime, incluindo `tenants`, `companies`, `audit_events` e
  `account_locks`;
- mesmas contagens do instante do backup para todas as tabelas e, no mínimo,
  para tenants, companies, AuditEvent e AccountLock;
- tabelas InnoDB e collation `utf8mb4_*`;
- PKs, FKs simples/compostas, UNIQUE, CHECK e índices presentes;
- payload JSON de um AuditEvent legível quando houver eventos;
- `scope_fingerprint`, `active_marker` e status de AccountLock legíveis quando
  houver locks;
- leitura ORM básica e tenant-aware via aplicação.

Não modificar AuditEvents nem criar/liberar locks durante a validação.

## Falha e rollback da operação de restore

Se o restore falhar, interromper validações, preservar dump/hash/log sanitizado
e classificar o Lab como inválido. Como o Lab é descartável, a recuperação do
ensaio consiste em repetir o restore completo após corrigir a causa e confirmar
novamente sua identidade. Nunca compensar com alteração manual do Runtime.

Em incidente real, validar o backup em ambiente isolado antes de qualquer
cutover. Sobrescrever o Runtime exige plano específico, aprovação explícita,
janela e evidência independente; não faz parte deste ensaio.

## RPO e RTO do piloto

- RPO técnico alvo: 24 horas;
- RTO técnico alvo: 4 horas.

São objetivos técnicos iniciais, não SLA contratual. A frequência deve garantir
ao menos um backup lógico diário. O RTO deve ser reavaliado com a duração medida
do restore, validação, transferência, decisão humana e eventual cutover.

## Retenção

O dump local da homologação de 08/09/2026 deve permanecer protegido em
`.backups/` por sete dias corridos após a conclusão, até 15/09/2026, para revisão
das evidências. Depois desse prazo, o operador deve removê-lo de forma segura e
registrar timestamp, nome e SHA-256 da remoção, salvo retenção formalmente
aprovada ou legal hold. A remoção não é automática.

Para a operação do piloto, manter uma janela móvel mínima de sete backups
lógicos diários, criptografados em armazenamento externo aprovado. A política
de retenção definitiva depende da governança de privacidade/LGPD ainda pendente.
O backup gerenciado pelo provedor deve ter retenção e restore verificados
separadamente.

## Evidências e incidentes

Para cada execução, registrar identificador, operadores, aprovações, timestamps,
hash, tamanho, contagens, duração do restore, validações e desvios. Não anexar o
dump a tickets comuns. Qualquer destino incorreto, divergência de hash/contagem,
falha de constraint ou acesso não autorizado exige interrupção e incidente.
