-- Somente leitura. Execute antes e depois de 006_up.sql.
-- Divergencia de tipo, colacao ou nulabilidade exige interromper a publicacao.

USE u621451815_serdial21;

SELECT TABLE_NAME, COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE, COLLATION_NAME
FROM information_schema.COLUMNS
WHERE TABLE_SCHEMA = DATABASE()
  AND (
      (TABLE_NAME = 'security_sessoes_clientes'
       AND COLUMN_NAME IN ('cliente_id', 'token_hash', 'expira_em', 'revogado_em'))
      OR (TABLE_NAME = 'tickets_master'
          AND COLUMN_NAME IN ('id', 'cliente_id', 'status', 'atualizado_em'))
      OR (TABLE_NAME = 'tickets_mensagens'
          AND COLUMN_NAME IN (
              'id', 'ticket_id', 'remetente_tipo', 'remetente_id',
              'mensagem', 'anexo_url', 'anexo_nome', 'criado_em'
          ))
      OR (TABLE_NAME = 'inbox_documentos'
          AND COLUMN_NAME IN ('id', 'cliente_id', 'status', 'atualizado_em'))
      OR (TABLE_NAME = 'logs_auditoria'
          AND COLUMN_NAME IN (
              'funcionario_id', 'acao', 'tabela_afetada', 'registro_id', 'detalhes'
          ))
  )
ORDER BY TABLE_NAME, ORDINAL_POSITION;

SELECT TABLE_NAME, COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE, COLUMN_DEFAULT
FROM information_schema.COLUMNS
WHERE TABLE_SCHEMA = DATABASE()
  AND TABLE_NAME = 'inbox_documentos_complementos'
ORDER BY ORDINAL_POSITION;

SELECT CONSTRAINT_NAME, CONSTRAINT_TYPE
FROM information_schema.TABLE_CONSTRAINTS
WHERE CONSTRAINT_SCHEMA = DATABASE()
  AND TABLE_NAME = 'inbox_documentos_complementos'
ORDER BY CONSTRAINT_NAME;

SELECT ROUTINE_NAME, ROUTINE_TYPE, SECURITY_TYPE
FROM information_schema.ROUTINES
WHERE ROUTINE_SCHEMA = DATABASE()
  AND ROUTINE_NAME IN (
      'sp_portal_detalhe_chamado',
      'sp_portal_complementar_chamado',
      'sp_portal_detalhe_documento',
      'sp_portal_complementar_documento'
  )
ORDER BY ROUTINE_NAME;

SELECT 'Execute SHOW GRANTS FOR CURRENT_USER e confirme EXECUTE, SELECT, INSERT e UPDATE necessarios.'
       AS lembrete_show_grants_n8n;
