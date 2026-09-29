-- Sistema A — recuperação administrativa de senha
-- Requer MariaDB 11.8+, InnoDB e RANDOM_BYTES().
-- Aplicar somente após backup verificado e aprovação do runbook.

CREATE TABLE security_password_reset_funcionarios (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    funcionario_id INT(11) NULL,
    request_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    identity_hash CHAR(64) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    source_hash CHAR(64) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    token_hash CHAR(64) CHARACTER SET ascii COLLATE ascii_bin NULL,
    resultado_solicitacao ENUM('issued', 'not_found', 'rate_limited') NOT NULL,
    solicitado_em DATETIME NOT NULL DEFAULT UTC_TIMESTAMP(),
    expira_em DATETIME NULL,
    utilizado_em DATETIME NULL,
    revogado_em DATETIME NULL,
    tentativas_invalidas SMALLINT UNSIGNED NOT NULL DEFAULT 0,
    PRIMARY KEY (id),
    UNIQUE KEY uq_password_reset_request_id (request_id),
    UNIQUE KEY uq_password_reset_token_hash (token_hash),
    KEY idx_password_reset_identity_time (identity_hash, solicitado_em),
    KEY idx_password_reset_source_time (source_hash, solicitado_em),
    KEY idx_password_reset_funcionario_time (funcionario_id, solicitado_em),
    KEY idx_password_reset_expiry (expira_em),
    CONSTRAINT fk_password_reset_funcionario
        FOREIGN KEY (funcionario_id) REFERENCES funcionarios (id)
        ON UPDATE RESTRICT ON DELETE CASCADE,
    CONSTRAINT chk_password_reset_token_shape CHECK (
        (resultado_solicitacao = 'issued' AND token_hash IS NOT NULL AND expira_em IS NOT NULL)
        OR
        (resultado_solicitacao IN ('not_found', 'rate_limited') AND token_hash IS NULL AND expira_em IS NULL)
    ),
    CONSTRAINT chk_password_reset_terminal_state CHECK (
        utilizado_em IS NULL OR revogado_em IS NULL
    )
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DELIMITER $$

CREATE PROCEDURE sp_admin_password_reset_request(
    IN p_email VARCHAR(100),
    IN p_source_key VARCHAR(128)
)
SQL SECURITY INVOKER
proc: BEGIN
    DECLARE v_email VARCHAR(100);
    DECLARE v_identity_hash CHAR(64);
    DECLARE v_source_hash CHAR(64);
    DECLARE v_request_id CHAR(36);
    DECLARE v_funcionario_id INT(11) DEFAULT NULL;
    DECLARE v_delivery_email VARCHAR(100) DEFAULT NULL;
    DECLARE v_token CHAR(64) DEFAULT NULL;
    DECLARE v_identity_count INT UNSIGNED DEFAULT 0;
    DECLARE v_source_count INT UNSIGNED DEFAULT 0;

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    SET v_email = LOWER(TRIM(COALESCE(p_email, '')));
    SET v_identity_hash = SHA2(v_email, 256);
    SET v_source_hash = SHA2(COALESCE(NULLIF(TRIM(p_source_key), ''), 'unknown'), 256);
    SET v_request_id = UUID();

    START TRANSACTION;

    SELECT COUNT(*)
      INTO v_identity_count
      FROM security_password_reset_funcionarios
     WHERE identity_hash = v_identity_hash
       AND solicitado_em >= UTC_TIMESTAMP() - INTERVAL 15 MINUTE;

    SELECT COUNT(*)
      INTO v_source_count
      FROM security_password_reset_funcionarios
     WHERE source_hash = v_source_hash
       AND solicitado_em >= UTC_TIMESTAMP() - INTERVAL 15 MINUTE;

    IF v_identity_count >= 3 OR v_source_count >= 30 THEN
        INSERT INTO security_password_reset_funcionarios (
            funcionario_id,
            request_id,
            identity_hash,
            source_hash,
            token_hash,
            resultado_solicitacao,
            expira_em
        ) VALUES (
            NULL,
            v_request_id,
            v_identity_hash,
            v_source_hash,
            NULL,
            'rate_limited',
            NULL
        );

        COMMIT;
        SELECT
            TRUE AS accepted,
            FALSE AS should_send,
            NULL AS delivery_email,
            NULL AS reset_token,
            v_request_id AS request_id;
        LEAVE proc;
    END IF;

    IF CHAR_LENGTH(v_email) BETWEEN 3 AND 100 AND LOCATE('@', v_email) > 1 THEN
        SELECT MAX(id), MAX(email)
          INTO v_funcionario_id, v_delivery_email
          FROM funcionarios
         WHERE email = v_email
           AND status = 'Ativo';
    END IF;

    IF v_funcionario_id IS NULL THEN
        INSERT INTO security_password_reset_funcionarios (
            funcionario_id,
            request_id,
            identity_hash,
            source_hash,
            token_hash,
            resultado_solicitacao,
            expira_em
        ) VALUES (
            NULL,
            v_request_id,
            v_identity_hash,
            v_source_hash,
            NULL,
            'not_found',
            NULL
        );

        COMMIT;
        SELECT
            TRUE AS accepted,
            FALSE AS should_send,
            NULL AS delivery_email,
            NULL AS reset_token,
            v_request_id AS request_id;
        LEAVE proc;
    END IF;

    UPDATE security_password_reset_funcionarios
       SET revogado_em = UTC_TIMESTAMP()
     WHERE funcionario_id = v_funcionario_id
       AND resultado_solicitacao = 'issued'
       AND utilizado_em IS NULL
       AND revogado_em IS NULL;

    SET v_token = LOWER(HEX(RANDOM_BYTES(32)));

    INSERT INTO security_password_reset_funcionarios (
        funcionario_id,
        request_id,
        identity_hash,
        source_hash,
        token_hash,
        resultado_solicitacao,
        expira_em
    ) VALUES (
        v_funcionario_id,
        v_request_id,
        v_identity_hash,
        v_source_hash,
        SHA2(v_token, 256),
        'issued',
        UTC_TIMESTAMP() + INTERVAL 30 MINUTE
    );

    INSERT INTO logs_auditoria (
        funcionario_id,
        acao,
        tabela_afetada,
        registro_id,
        detalhes,
        ip_origem
    ) VALUES (
        v_funcionario_id,
        'admin_password_reset_requested',
        'funcionarios',
        v_funcionario_id,
        JSON_OBJECT('request_id', v_request_id, 'result', 'issued'),
        NULL
    );

    COMMIT;

    SELECT
        TRUE AS accepted,
        TRUE AS should_send,
        v_delivery_email AS delivery_email,
        v_token AS reset_token,
        v_request_id AS request_id;
END$$

CREATE PROCEDURE sp_admin_password_reset_apply(
    IN p_token VARCHAR(128),
    IN p_new_password VARCHAR(255)
)
SQL SECURITY INVOKER
proc: BEGIN
    DECLARE v_reset_id BIGINT UNSIGNED DEFAULT NULL;
    DECLARE v_funcionario_id INT(11) DEFAULT NULL;
    DECLARE v_request_id CHAR(36) DEFAULT UUID();
    DECLARE v_updated INT DEFAULT 0;

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    IF p_token IS NULL
       OR p_token NOT REGEXP '^[0-9a-f]{64}$'
       OR p_new_password IS NULL
       OR CHAR_LENGTH(p_new_password) < 12
       OR CHAR_LENGTH(p_new_password) > 128
       OR p_new_password NOT REGEXP '[[:alpha:]]'
       OR p_new_password NOT REGEXP '[[:digit:]]' THEN
        SELECT
            FALSE AS success,
            'invalid_or_expired' AS result,
            v_request_id AS request_id;
        LEAVE proc;
    END IF;

    START TRANSACTION;

    BEGIN
        DECLARE CONTINUE HANDLER FOR NOT FOUND SET v_reset_id = NULL;

        SELECT id, funcionario_id
          INTO v_reset_id, v_funcionario_id
          FROM security_password_reset_funcionarios
         WHERE token_hash = SHA2(p_token, 256)
           AND resultado_solicitacao = 'issued'
           AND utilizado_em IS NULL
           AND revogado_em IS NULL
           AND expira_em > UTC_TIMESTAMP()
           AND tentativas_invalidas < 5
         LIMIT 1
         FOR UPDATE;
    END;

    IF v_reset_id IS NULL THEN
        UPDATE security_password_reset_funcionarios
           SET tentativas_invalidas = LEAST(tentativas_invalidas + 1, 65535)
         WHERE token_hash = SHA2(p_token, 256)
           AND utilizado_em IS NULL
           AND revogado_em IS NULL;

        COMMIT;
        SELECT
            FALSE AS success,
            'invalid_or_expired' AS result,
            v_request_id AS request_id;
        LEAVE proc;
    END IF;

    UPDATE funcionarios
       SET senha = SHA2(p_new_password, 256),
           atualizado_em = CURRENT_TIMESTAMP()
     WHERE id = v_funcionario_id
       AND status = 'Ativo';

    SET v_updated = ROW_COUNT();

    IF v_updated <> 1 THEN
        ROLLBACK;
        SELECT
            FALSE AS success,
            'invalid_or_expired' AS result,
            v_request_id AS request_id;
        LEAVE proc;
    END IF;

    UPDATE security_password_reset_funcionarios
       SET utilizado_em = UTC_TIMESTAMP()
     WHERE id = v_reset_id;

    UPDATE security_password_reset_funcionarios
       SET revogado_em = UTC_TIMESTAMP()
     WHERE funcionario_id = v_funcionario_id
       AND id <> v_reset_id
       AND resultado_solicitacao = 'issued'
       AND utilizado_em IS NULL
       AND revogado_em IS NULL;

    UPDATE security_sessoes_funcionarios
       SET revogado_em = UTC_TIMESTAMP()
     WHERE funcionario_id = v_funcionario_id
       AND revogado_em IS NULL;

    INSERT INTO logs_auditoria (
        funcionario_id,
        acao,
        tabela_afetada,
        registro_id,
        detalhes,
        ip_origem
    ) VALUES (
        v_funcionario_id,
        'admin_password_reset_completed',
        'funcionarios',
        v_funcionario_id,
        JSON_OBJECT('request_id', v_request_id, 'result', 'success'),
        NULL
    );

    COMMIT;

    SELECT
        TRUE AS success,
        'success' AS result,
        v_request_id AS request_id;
END$$

DELIMITER ;
