-- Reverte somente a procedure criada pela 005.
-- Eventos de auditoria permanecem como historico append-only.

DROP PROCEDURE IF EXISTS sp_admin_module_authorize;
