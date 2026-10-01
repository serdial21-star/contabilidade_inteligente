-- Somente leitura. Execute depois de 001_up.sql, 002_up.sql e 003_up.sql.

USE u621451815_serdial21;

SELECT DEFAULT_CHARACTER_SET_NAME, DEFAULT_COLLATION_NAME
FROM information_schema.SCHEMATA
WHERE SCHEMA_NAME = 'u621451815_serdial21';

SELECT TABLE_NAME, COLUMN_NAME, CHARACTER_SET_NAME, COLLATION_NAME
FROM information_schema.COLUMNS
WHERE TABLE_SCHEMA = 'u621451815_serdial21'
  AND (
      (TABLE_NAME = 'funcionarios' AND COLUMN_NAME IN ('cargo', 'status'))
      OR (TABLE_NAME = 'permissoes_funcionario_modulos'
          AND COLUMN_NAME IN ('modulo', 'acao'))
      OR (TABLE_NAME = 'security_sessoes_funcionarios'
          AND COLUMN_NAME = 'token_hash')
  )
ORDER BY TABLE_NAME, COLUMN_NAME;

SELECT TABLE_NAME, ENGINE, TABLE_COLLATION
FROM information_schema.TABLES
WHERE TABLE_SCHEMA = 'u621451815_serdial21'
  AND TABLE_NAME IN (
      'clientes',
      'security_sessoes_clientes',
      'security_password_reset_clientes'
  )
ORDER BY TABLE_NAME;

SELECT COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE, EXTRA
FROM information_schema.COLUMNS
WHERE TABLE_SCHEMA = 'u621451815_serdial21'
  AND TABLE_NAME = 'clientes'
  AND COLUMN_NAME = 'documento_fiscal_canonico';

SELECT INDEX_NAME, NON_UNIQUE, COLUMN_NAME
FROM information_schema.STATISTICS
WHERE TABLE_SCHEMA = 'u621451815_serdial21'
  AND (
      (TABLE_NAME = 'clientes'
       AND INDEX_NAME = 'uq_clientes_documento_fiscal_canonico')
      OR TABLE_NAME IN (
          'security_sessoes_clientes',
          'security_password_reset_clientes'
      )
  )
ORDER BY TABLE_NAME, INDEX_NAME, SEQ_IN_INDEX;

SELECT ROUTINE_NAME, ROUTINE_TYPE, SECURITY_TYPE
FROM information_schema.ROUTINES
WHERE ROUTINE_SCHEMA = 'u621451815_serdial21'
  AND ROUTINE_NAME IN (
      'sp_admin_cliente_create',
      'sp_admin_cliente_list',
      'sp_admin_cliente_update',
      'sp_admin_client_authorize',
      'sp_admin_cliente_set_folder',
      'sp_cliente_password_reset_request',
      'sp_cliente_password_reset_apply'
  )
ORDER BY ROUTINE_NAME;

SELECT COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE, COLUMN_DEFAULT, EXTRA
FROM information_schema.COLUMNS
WHERE TABLE_SCHEMA = 'u621451815_serdial21'
  AND TABLE_NAME = 'permissoes_funcionario_modulos'
ORDER BY ORDINAL_POSITION;

SELECT INDEX_NAME, NON_UNIQUE, COLUMN_NAME
FROM information_schema.STATISTICS
WHERE TABLE_SCHEMA = 'u621451815_serdial21'
  AND TABLE_NAME = 'permissoes_funcionario_modulos'
ORDER BY INDEX_NAME, SEQ_IN_INDEX;

SELECT INDEX_NAME, NON_UNIQUE, COLUMN_NAME
FROM information_schema.STATISTICS
WHERE TABLE_SCHEMA = 'u621451815_serdial21'
  AND TABLE_NAME = 'security_sessoes_funcionarios'
ORDER BY INDEX_NAME, SEQ_IN_INDEX;

SELECT CONCAT(
    'ACAO DO USUARIO: execute SHOW GRANTS FOR o usuario e host reais do n8n; ',
    'confirme EXECUTE nas procedures 003 e SELECT em permissoes_funcionario_modulos.'
) AS lembrete_show_grants_n8n;

SELECT COUNT(*) AS documentos_duplicados
FROM (
    SELECT documento_fiscal_canonico
    FROM u621451815_serdial21.clientes
    WHERE documento_fiscal_canonico IS NOT NULL
    GROUP BY documento_fiscal_canonico
    HAVING COUNT(*) > 1
) AS duplicados;
