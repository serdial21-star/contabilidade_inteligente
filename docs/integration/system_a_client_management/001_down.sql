-- Reverte somente os objetos criados por 001_up.sql.
-- Nao remove clientes, e-mails autorizados, funcionarios ou auditoria.

DROP PROCEDURE IF EXISTS sp_cliente_password_reset_apply;
DROP PROCEDURE IF EXISTS sp_cliente_password_reset_request;
DROP PROCEDURE IF EXISTS sp_admin_cliente_set_folder;
DROP PROCEDURE IF EXISTS sp_admin_cliente_create;

DROP TABLE IF EXISTS security_password_reset_clientes;

ALTER TABLE clientes
    DROP INDEX IF EXISTS uq_clientes_documento_fiscal_canonico,
    DROP COLUMN IF EXISTS documento_fiscal_canonico;
