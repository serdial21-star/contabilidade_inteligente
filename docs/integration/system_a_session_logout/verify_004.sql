-- Somente leitura. Antes de 004_up.sql: as duas primeiras consultas devem
-- mostrar as colacoes esperadas; se diferirem, NAO aplique a 004.
-- Depois de 004_up.sql: a terceira consulta deve listar as duas procedures INVOKER.

USE u621451815_serdial21;

SELECT TABLE_NAME, COLUMN_NAME, CHARACTER_SET_NAME, COLLATION_NAME,
       CASE
           WHEN TABLE_NAME = 'security_sessoes_funcionarios'
                AND COLLATION_NAME = 'utf8mb4_unicode_ci' THEN 'OK'
           WHEN TABLE_NAME = 'security_sessoes_clientes'
                AND COLLATION_NAME = 'utf8mb4_uca1400_ai_ci' THEN 'OK'
           ELSE 'DIVERGENTE - NAO APLICAR'
       END AS conferencia
FROM information_schema.COLUMNS
WHERE TABLE_SCHEMA = 'u621451815_serdial21'
  AND COLUMN_NAME = 'token_hash'
  AND TABLE_NAME IN ('security_sessoes_funcionarios', 'security_sessoes_clientes')
ORDER BY TABLE_NAME;

SELECT COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE
FROM information_schema.COLUMNS
WHERE TABLE_SCHEMA = 'u621451815_serdial21'
  AND TABLE_NAME = 'logs_auditoria'
  AND COLUMN_NAME IN ('funcionario_id', 'acao', 'tabela_afetada', 'registro_id', 'detalhes')
ORDER BY ORDINAL_POSITION;

SELECT ROUTINE_NAME, ROUTINE_TYPE, SECURITY_TYPE
FROM information_schema.ROUTINES
WHERE ROUTINE_SCHEMA = 'u621451815_serdial21'
  AND ROUTINE_NAME IN ('sp_funcionario_logout', 'sp_cliente_logout')
ORDER BY ROUTINE_NAME;
