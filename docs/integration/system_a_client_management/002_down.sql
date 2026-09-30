-- Reverte somente os objetos criados por 002_up.sql.
-- Use apenas antes de liberar o fluxo de edicao.

DROP PROCEDURE IF EXISTS sp_admin_cliente_update;

ALTER TABLE clientes
    DROP COLUMN IF EXISTS telefone;
