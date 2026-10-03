-- Sistema A - "Sair" revoga a sessao no servidor (T-0005).
-- Independe de 001-003: usa apenas as tabelas de sessao e logs_auditoria.
-- Aplicar somente apos backup e verify_004.sql (colacao de token_hash).
--
-- Decisoes (T-0005, aprovadas em 03/10/2026):
-- D2 resultado identico com ou sem sessao valida (o endpoint nao confirma tokens);
-- D3 revoga apenas a sessao do token apresentado;
-- D4 auditoria minima, sem token nem hash, somente quando houve revogacao.
--
-- O hash e calculado numa variavel com a colacao da coluna comparada:
-- security_sessoes_clientes usa utf8mb4_uca1400_ai_ci em producao e o
-- schema usa utf8mb4_unicode_ci; misturar as duas gera o erro 1267.

DROP PROCEDURE IF EXISTS sp_funcionario_logout;
DROP PROCEDURE IF EXISTS sp_cliente_logout;

DELIMITER $$

CREATE PROCEDURE sp_funcionario_logout(
    IN p_token VARCHAR(128)
)
SQL SECURITY INVOKER
proc: BEGIN
    DECLARE v_hash CHAR(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    DECLARE v_sessao_id INT(11) DEFAULT NULL;
    DECLARE v_funcionario_id INT(11) DEFAULT NULL;
    DECLARE v_request_id CHAR(36) DEFAULT UUID();
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    IF p_token IS NULL
       OR p_token NOT REGEXP '^[0-9A-Za-z]{20,128}$' THEN
        SELECT TRUE AS success, 'logged_out' AS result;
        LEAVE proc;
    END IF;

    SET v_hash = SHA2(p_token, 256);

    START TRANSACTION;

    BEGIN
        DECLARE CONTINUE HANDLER FOR NOT FOUND SET v_sessao_id = NULL;
        SELECT id, funcionario_id
          INTO v_sessao_id, v_funcionario_id
          FROM security_sessoes_funcionarios
         WHERE token_hash = v_hash
           AND revogado_em IS NULL
           AND expira_em > UTC_TIMESTAMP()
         LIMIT 1
         FOR UPDATE;
    END;

    IF v_sessao_id IS NOT NULL THEN
        UPDATE security_sessoes_funcionarios
           SET revogado_em = UTC_TIMESTAMP()
         WHERE id = v_sessao_id
           AND revogado_em IS NULL;

        INSERT INTO logs_auditoria (
            funcionario_id, acao, tabela_afetada, registro_id,
            detalhes, ip_origem
        ) VALUES (
            v_funcionario_id, 'employee_logout',
            'security_sessoes_funcionarios', v_sessao_id,
            JSON_OBJECT('request_id', v_request_id),
            NULL
        );
    END IF;

    COMMIT;

    SELECT TRUE AS success, 'logged_out' AS result;
END$$

CREATE PROCEDURE sp_cliente_logout(
    IN p_token VARCHAR(128)
)
SQL SECURITY INVOKER
proc: BEGIN
    DECLARE v_hash CHAR(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_uca1400_ai_ci;
    DECLARE v_sessao_id BIGINT(20) DEFAULT NULL;
    DECLARE v_cliente_id INT(11) DEFAULT NULL;
    DECLARE v_request_id CHAR(36) DEFAULT UUID();
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    IF p_token IS NULL
       OR p_token NOT REGEXP '^[0-9A-Za-z]{20,128}$' THEN
        SELECT TRUE AS success, 'logged_out' AS result;
        LEAVE proc;
    END IF;

    SET v_hash = SHA2(p_token, 256);

    START TRANSACTION;

    BEGIN
        DECLARE CONTINUE HANDLER FOR NOT FOUND SET v_sessao_id = NULL;
        SELECT id, cliente_id
          INTO v_sessao_id, v_cliente_id
          FROM security_sessoes_clientes
         WHERE token_hash = v_hash
           AND revogado_em IS NULL
           AND expira_em > UTC_TIMESTAMP()
         LIMIT 1
         FOR UPDATE;
    END;

    IF v_sessao_id IS NOT NULL THEN
        UPDATE security_sessoes_clientes
           SET revogado_em = UTC_TIMESTAMP()
         WHERE id = v_sessao_id
           AND revogado_em IS NULL;

        -- registro_id guarda o cliente: o id da sessao e BIGINT e a coluna e INT.
        INSERT INTO logs_auditoria (
            funcionario_id, acao, tabela_afetada, registro_id,
            detalhes, ip_origem
        ) VALUES (
            NULL, 'client_logout',
            'security_sessoes_clientes', v_cliente_id,
            JSON_OBJECT('request_id', v_request_id),
            NULL
        );
    END IF;

    COMMIT;

    SELECT TRUE AS success, 'logged_out' AS result;
END$$

DELIMITER ;
