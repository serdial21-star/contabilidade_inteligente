# Correção da migration 0006 para MariaDB 11.8

Data: 07/09/2026  
Escopo: correção mínima do bloqueador encontrado na Execução 27B. Esta etapa
não conclui a homologação MariaDB nem executa as revisions 0007 e 0008.

## Erro original

No banco dedicado `u621451815_serdial21_hom`, MariaDB 11.8.8 interrompeu a
revision `20260905_0006_ofx_banking` ao criar `bank_accounts`:

```text
errno 150: Foreign key constraint is incorrectly formed
```

A FK envolvida é `(tenant_id, company_id) -> companies(tenant_id, id)`.

## Diagnóstico comprovado

O DDL real de `companies` mostrou:

- engine `InnoDB`;
- pai `tenant_id` e `id` como `CHAR(32) NOT NULL`;
- charset `utf8mb4`, collation `utf8mb4_unicode_ci`;
- UNIQUE `uq_companies_tenant_id_id (tenant_id, id)` nessa ordem.

Portanto, não houve ausência de índice pai, incompatibilidade de tipo,
comprimento, ordem, nulidade ou engine. Não existiam objetos parciais de 0006:
`bank_accounts`, `bank_statements` e `bank_transactions` estavam ausentes.

A causa raiz é **COLLATION_MISMATCH**. A revision 0006 definia somente
`mysql_charset='utf8mb4'`. Na Hostinger, a collation padrão do banco/conexão é
`utf8mb4_uca1400_ai_ci`; assim, os `CHAR(32)` filhos seriam criados com
collation diferente dos `CHAR(32)` pai em `companies`, que usa
`utf8mb4_unicode_ci`. MariaDB exige collation compatível para a FK em colunas
de caracteres.

## Correção mínima

Foi alterada a própria revision `20260905_0006_ofx_banking.py` para adicionar
`mysql_collate='utf8mb4_unicode_ci'` a `bank_accounts`, `bank_statements` e
`bank_transactions`, preservando `mysql_charset='utf8mb4'`, FKs, UNIQUEs e
índices existentes.

O model ORM bancário já declarava essa mesma collation em `TABLE_OPTIONS`; a
mudança sincroniza o DDL Alembic com o contrato ORM. Não foi adicionada uma
UNIQUE, removida uma constraint, desabilitado `FOREIGN_KEY_CHECKS` ou reduzido
o isolamento tenant/company.

É seguro corrigir esta revision no histórico local pré-piloto porque a única
tentativa real anterior falhou antes de criá-la e a evidência disponível a
limita ao banco descartável de homologação. Não há evidência de aplicação bem
sucedida de 0006 em ambiente compartilhado. Caso surja tal evidência, não
reescrever o histórico: criar migration compatível para o ambiente afetado.

## Prova executada

Após a correção, foi executado somente `20260904_0005 -> 20260905_0006` no
banco dedicado. A revision foi registrada como `20260905_0006`,
`bank_accounts` ficou em `utf8mb4_unicode_ci` e a FK para `companies` foi
criada. Os testes SQLite de migrations e regressão OFX também passaram: **3
passed**. O teste MariaDB de diagnóstico/correção passou: **2 passed**.

## Estado e estratégia de recriação

O banco de homologação permanece dedicado e agora está em `20260905_0006`.
Não foi apagada nenhuma tabela automaticamente. Para uma futura execução
`base -> head` limpa, primeiro inspecionar e registrar novamente o banco; só
então, mediante autorização explícita para o banco descartável, recriá-lo do
zero e executar as revisions. A Execução 27D deve retomar desse procedimento e
provar as migrations restantes, schema completo e cenários transacionais.

## Arquivos e riscos

- Alterado: `alembic/versions/20260905_0006_ofx_banking.py`.
- Criados: `tests/mariadb/test_migration_0006_diagnosis.py` e este documento.
- Riscos restantes: 0007/0008, JSON, DECIMAL, CHECK, concorrência, rollback,
  isolamento e auditoria ainda não foram homologados no MariaDB real.
