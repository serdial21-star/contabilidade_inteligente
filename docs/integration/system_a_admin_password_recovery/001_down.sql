-- Rollback estrutural. Executar somente se nenhum reset real precisar ser
-- preservado e após revisão do impacto.

DROP PROCEDURE IF EXISTS sp_admin_password_reset_apply;
DROP PROCEDURE IF EXISTS sp_admin_password_reset_request;
DROP TABLE IF EXISTS security_password_reset_funcionarios;
