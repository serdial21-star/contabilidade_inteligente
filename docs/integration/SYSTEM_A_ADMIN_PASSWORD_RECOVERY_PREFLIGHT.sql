-- Somente leitura. Não altera dados nem schema.
-- Execute no banco operacional do Sistema A antes de preparar a migration.

SELECT
    VERSION() AS database_version,
    @@session.time_zone AS session_time_zone,
    @@system_time_zone AS system_time_zone,
    LENGTH(RANDOM_BYTES(32)) AS random_bytes_length,
    UTC_TIMESTAMP() AS checked_at_utc;

SHOW CREATE TABLE funcionarios;
SHOW CREATE TABLE security_sessoes_funcionarios;
SHOW CREATE TABLE logs_auditoria;
SHOW CREATE TABLE log_tentativas_login;

SHOW TABLES LIKE 'security_password_reset_funcionarios';

-- O phpMyAdmin pode truncar SHOW CREATE TABLE. Estas consultas devolvem a
-- mesma estrutura relevante em linhas, sem acessar dados das tabelas.
SELECT
    TABLE_NAME,
    ENGINE,
    TABLE_COLLATION
FROM information_schema.TABLES
WHERE TABLE_SCHEMA = DATABASE()
  AND TABLE_NAME IN (
      'funcionarios',
      'security_sessoes_funcionarios',
      'logs_auditoria',
      'log_tentativas_login'
  )
ORDER BY TABLE_NAME;

SELECT
    TABLE_NAME,
    ORDINAL_POSITION,
    COLUMN_NAME,
    COLUMN_TYPE,
    IS_NULLABLE,
    COLUMN_DEFAULT,
    EXTRA,
    CHARACTER_SET_NAME,
    COLLATION_NAME
FROM information_schema.COLUMNS
WHERE TABLE_SCHEMA = DATABASE()
  AND TABLE_NAME IN (
      'funcionarios',
      'security_sessoes_funcionarios',
      'logs_auditoria',
      'log_tentativas_login'
  )
ORDER BY TABLE_NAME, ORDINAL_POSITION;

SELECT
    TABLE_NAME,
    INDEX_NAME,
    NON_UNIQUE,
    SEQ_IN_INDEX,
    COLUMN_NAME,
    SUB_PART
FROM information_schema.STATISTICS
WHERE TABLE_SCHEMA = DATABASE()
  AND TABLE_NAME IN (
      'funcionarios',
      'security_sessoes_funcionarios',
      'logs_auditoria',
      'log_tentativas_login'
  )
ORDER BY TABLE_NAME, INDEX_NAME, SEQ_IN_INDEX;

SELECT
    kcu.TABLE_NAME,
    kcu.CONSTRAINT_NAME,
    kcu.COLUMN_NAME,
    kcu.REFERENCED_TABLE_NAME,
    kcu.REFERENCED_COLUMN_NAME,
    rc.UPDATE_RULE,
    rc.DELETE_RULE
FROM information_schema.KEY_COLUMN_USAGE AS kcu
JOIN information_schema.REFERENTIAL_CONSTRAINTS AS rc
  ON rc.CONSTRAINT_SCHEMA = kcu.CONSTRAINT_SCHEMA
 AND rc.CONSTRAINT_NAME = kcu.CONSTRAINT_NAME
 AND rc.TABLE_NAME = kcu.TABLE_NAME
WHERE kcu.CONSTRAINT_SCHEMA = DATABASE()
  AND kcu.TABLE_NAME IN (
      'funcionarios',
      'security_sessoes_funcionarios',
      'logs_auditoria',
      'log_tentativas_login'
  )
  AND kcu.REFERENCED_TABLE_NAME IS NOT NULL
ORDER BY kcu.TABLE_NAME, kcu.CONSTRAINT_NAME, kcu.ORDINAL_POSITION;
