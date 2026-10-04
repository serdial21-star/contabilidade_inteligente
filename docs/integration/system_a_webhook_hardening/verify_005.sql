-- Somente leitura. Execute antes e depois de 005_up.sql.
-- Qualquer colacao divergente em token_hash exige interromper a publicacao.

USE u621451815_serdial21;

SELECT TABLE_NAME, COLUMN_NAME, CHARACTER_SET_NAME, COLLATION_NAME,
       CASE
           WHEN TABLE_NAME = 'security_sessoes_funcionarios'
                AND COLLATION_NAME = 'utf8mb4_unicode_ci' THEN 'OK'
           ELSE 'DIVERGENTE - NAO APLICAR'
       END AS conferencia
FROM information_schema.COLUMNS
WHERE TABLE_SCHEMA = 'u621451815_serdial21'
  AND TABLE_NAME = 'security_sessoes_funcionarios'
  AND COLUMN_NAME = 'token_hash';

SELECT TABLE_NAME, COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE, COLLATION_NAME
FROM information_schema.COLUMNS
WHERE TABLE_SCHEMA = 'u621451815_serdial21'
  AND (
      (TABLE_NAME = 'funcionarios' AND COLUMN_NAME IN ('id', 'cargo', 'status'))
      OR (TABLE_NAME = 'permissoes_funcionario_modulos'
          AND COLUMN_NAME IN ('funcionario_id', 'modulo', 'acao', 'permitido'))
      OR (TABLE_NAME = 'logs_auditoria'
          AND COLUMN_NAME IN (
              'funcionario_id', 'acao', 'tabela_afetada', 'registro_id', 'detalhes'
          ))
  )
ORDER BY TABLE_NAME, ORDINAL_POSITION;

SELECT ROUTINE_NAME, ROUTINE_TYPE, SECURITY_TYPE
FROM information_schema.ROUTINES
WHERE ROUTINE_SCHEMA = 'u621451815_serdial21'
  AND ROUTINE_NAME = 'sp_admin_module_authorize';

SELECT 'Execute SHOW GRANTS FOR CURRENT_USER manualmente e confirme EXECUTE/SELECT/INSERT necessarios.'
       AS lembrete_show_grants_n8n;
