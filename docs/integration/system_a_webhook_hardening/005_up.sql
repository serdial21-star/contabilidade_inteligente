-- Sistema A - autorizacao generica de funcionario por modulo/acao (T-0006).
-- Requer as tabelas de sessao, funcionarios, permissoes e auditoria existentes.
-- Aplicar somente depois de backup e da conferencia de verify_005.sql.

DROP PROCEDURE IF EXISTS sp_admin_module_authorize;

DELIMITER $$

CREATE PROCEDURE sp_admin_module_authorize(
    IN p_admin_token VARCHAR(128),
    IN p_modulo VARCHAR(50),
    IN p_acao VARCHAR(20)
)
SQL SECURITY INVOKER
proc: BEGIN
    DECLARE v_hash CHAR(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    DECLARE v_funcionario_id INT(11) DEFAULT NULL;
    DECLARE v_cargo VARCHAR(50) DEFAULT NULL;
    DECLARE v_modulo VARCHAR(50);
    DECLARE v_acao VARCHAR(20);
    DECLARE v_permitido TINYINT(1) DEFAULT 0;
    DECLARE v_result VARCHAR(16) DEFAULT 'unauthorized';
    DECLARE v_request_id CHAR(36) DEFAULT UUID();

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    SET v_modulo = LOWER(TRIM(COALESCE(p_modulo, '')));
    SET v_acao = LOWER(TRIM(COALESCE(p_acao, '')));

    IF p_admin_token IS NULL
       OR p_admin_token NOT REGEXP '^[0-9A-Za-z]{20,128}$'
       OR v_modulo = ''
       OR v_acao = '' THEN
        SELECT FALSE AS success, v_result AS result,
               NULL AS funcionario_id, v_request_id AS request_id;
        LEAVE proc;
    END IF;

    SET v_hash = SHA2(p_admin_token, 256);
    START TRANSACTION;

    BEGIN
        DECLARE CONTINUE HANDLER FOR NOT FOUND SET v_funcionario_id = NULL;

        SELECT f.id, f.cargo
          INTO v_funcionario_id, v_cargo
          FROM security_sessoes_funcionarios AS s
          JOIN funcionarios AS f ON f.id = s.funcionario_id
         WHERE s.token_hash = v_hash
           AND s.expira_em > UTC_TIMESTAMP()
           AND s.revogado_em IS NULL
           AND f.status = 'Ativo'
         LIMIT 1
         FOR UPDATE;
    END;

    IF v_funcionario_id IS NULL THEN
        ROLLBACK;
        SELECT FALSE AS success, v_result AS result,
               NULL AS funcionario_id, v_request_id AS request_id;
        LEAVE proc;
    END IF;

    SET v_result = 'forbidden';

    IF BINARY LOWER(TRIM(COALESCE(v_cargo, ''))) IN ('administrador', 'admin') THEN
        SET v_result = 'authorized';
    ELSE
        BEGIN
            DECLARE CONTINUE HANDLER FOR NOT FOUND SET v_permitido = 0;

            SELECT permitido
              INTO v_permitido
              FROM permissoes_funcionario_modulos
             WHERE funcionario_id = v_funcionario_id
               AND modulo = v_modulo
               AND acao = v_acao
             LIMIT 1
             FOR UPDATE;
        END;

        IF v_permitido = 1 THEN
            SET v_result = 'authorized';
        END IF;
    END IF;

    IF v_result = 'forbidden' THEN
        INSERT INTO logs_auditoria (
            funcionario_id, acao, tabela_afetada, registro_id,
            detalhes, ip_origem
        ) VALUES (
            v_funcionario_id, 'employee_module_action_forbidden',
            'permissoes_funcionario_modulos', v_funcionario_id,
            JSON_OBJECT(
                'request_id', v_request_id,
                'module', v_modulo,
                'action', v_acao
            ),
            NULL
        );
    END IF;

    COMMIT;

    SELECT v_result = 'authorized' AS success, v_result AS result,
           v_funcionario_id AS funcionario_id, v_request_id AS request_id;
END$$

DELIMITER ;
