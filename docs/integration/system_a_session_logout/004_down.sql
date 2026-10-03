-- Reverte somente 004_up.sql. Sessoes ja revogadas e eventos de auditoria
-- permanecem: sao historico e nao sao desfeitos.

DROP PROCEDURE IF EXISTS sp_funcionario_logout;
DROP PROCEDURE IF EXISTS sp_cliente_logout;
