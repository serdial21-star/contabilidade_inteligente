-- Verificação somente leitura após aplicar 001_up.sql.

SELECT
    TABLE_NAME,
    ENGINE,
    TABLE_COLLATION
FROM information_schema.TABLES
WHERE TABLE_SCHEMA = DATABASE()
  AND TABLE_NAME = 'security_password_reset_funcionarios';

SELECT
    COLUMN_NAME,
    COLUMN_TYPE,
    IS_NULLABLE,
    COLUMN_DEFAULT,
    EXTRA
FROM information_schema.COLUMNS
WHERE TABLE_SCHEMA = DATABASE()
  AND TABLE_NAME = 'security_password_reset_funcionarios'
ORDER BY ORDINAL_POSITION;

SELECT
    ROUTINE_NAME,
    ROUTINE_TYPE,
    SECURITY_TYPE
FROM information_schema.ROUTINES
WHERE ROUTINE_SCHEMA = DATABASE()
  AND ROUTINE_NAME IN (
      'sp_admin_password_reset_request',
      'sp_admin_password_reset_apply'
  )
ORDER BY ROUTINE_NAME;

SELECT
    CONSTRAINT_NAME,
    COLUMN_NAME,
    REFERENCED_TABLE_NAME,
    REFERENCED_COLUMN_NAME
FROM information_schema.KEY_COLUMN_USAGE
WHERE CONSTRAINT_SCHEMA = DATABASE()
  AND TABLE_NAME = 'security_password_reset_funcionarios'
  AND REFERENCED_TABLE_NAME IS NOT NULL;
