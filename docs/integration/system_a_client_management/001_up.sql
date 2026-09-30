-- Sistema A - cadastro e recuperacao segura de clientes
-- Requer MariaDB 11.8+, InnoDB e RANDOM_BYTES().
-- Aplicar somente apos backup e execucao do preflight documentado.

ALTER TABLE clientes
    ADD COLUMN IF NOT EXISTS documento_fiscal_canonico VARCHAR(20)
        CHARACTER SET ascii COLLATE ascii_bin
        GENERATED ALWAYS AS (
            NULLIF(
                UPPER(
                    REPLACE(REPLACE(REPLACE(REPLACE(
                        COALESCE(
                            NULLIF(TRIM(cnpj), ''),
                            NULLIF(TRIM(cnpj_cpf), '')
                        ),
                        '.', ''), '/', ''), '-', ''), ' ', '')
                ),
                ''
            )
        ) PERSISTENT,
    ADD UNIQUE KEY IF NOT EXISTS uq_clientes_documento_fiscal_canonico (
        documento_fiscal_canonico
    );

CREATE TABLE IF NOT EXISTS security_password_reset_clientes (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    cliente_id INT(11) NULL,
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
    UNIQUE KEY uq_client_password_reset_request_id (request_id),
    UNIQUE KEY uq_client_password_reset_token_hash (token_hash),
    KEY idx_client_password_reset_identity_time (identity_hash, solicitado_em),
    KEY idx_client_password_reset_source_time (source_hash, solicitado_em),
    KEY idx_client_password_reset_cliente_time (cliente_id, solicitado_em),
    KEY idx_client_password_reset_expiry (expira_em),
    CONSTRAINT fk_client_password_reset_cliente
        FOREIGN KEY (cliente_id) REFERENCES clientes (id)
        ON UPDATE RESTRICT ON DELETE CASCADE,
    CONSTRAINT chk_client_password_reset_token_shape CHECK (
        (resultado_solicitacao = 'issued'
            AND token_hash IS NOT NULL
            AND expira_em IS NOT NULL)
        OR
        (resultado_solicitacao IN ('not_found', 'rate_limited')
            AND token_hash IS NULL
            AND expira_em IS NULL)
    ),
    CONSTRAINT chk_client_password_reset_terminal_state CHECK (
        utilizado_em IS NULL OR revogado_em IS NULL
    )
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP PROCEDURE IF EXISTS sp_cliente_password_reset_apply;
DROP PROCEDURE IF EXISTS sp_cliente_password_reset_request;
DROP PROCEDURE IF EXISTS sp_admin_cliente_set_folder;
DROP PROCEDURE IF EXISTS sp_admin_cliente_create;

DELIMITER $$

CREATE PROCEDURE sp_admin_cliente_create(
    IN p_admin_token VARCHAR(128),
    IN p_nome VARCHAR(150),
    IN p_email VARCHAR(100),
    IN p_documento VARCHAR(20),
    IN p_status VARCHAR(16),
    IN p_whatsapp VARCHAR(20)
)
SQL SECURITY INVOKER
proc: BEGIN
    DECLARE v_admin_id INT(11) DEFAULT NULL;
    DECLARE v_cliente_id INT(11) DEFAULT NULL;
    DECLARE v_nome VARCHAR(150);
    DECLARE v_email VARCHAR(100);
    DECLARE v_documento VARCHAR(20);
    DECLARE v_status VARCHAR(16);
    DECLARE v_whatsapp VARCHAR(20);
    DECLARE v_request_id CHAR(36) DEFAULT UUID();
    DECLARE v_token CHAR(64) DEFAULT NULL;
    DECLARE v_duplicate_count INT UNSIGNED DEFAULT 0;

    DECLARE EXIT HANDLER FOR 1062
    BEGIN
        ROLLBACK;
        SELECT
            FALSE AS success,
            'conflict' AS result,
            NULL AS cliente_id,
            FALSE AS should_send,
            NULL AS delivery_email,
            NULL AS reset_token,
            v_request_id AS request_id;
    END;

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    SET v_nome = TRIM(COALESCE(p_nome, ''));
    SET v_email = LOWER(TRIM(COALESCE(p_email, '')));
    SET v_documento = NULLIF(
        UPPER(REPLACE(REPLACE(REPLACE(REPLACE(
            TRIM(COALESCE(p_documento, '')),
            '.', ''), '/', ''), '-', ''), ' ', '')),
        ''
    );
    SET v_status = TRIM(COALESCE(p_status, 'Ativo'));
    SET v_whatsapp = NULLIF(TRIM(COALESCE(p_whatsapp, '')), '');

    IF p_admin_token IS NULL
       OR p_admin_token NOT REGEXP '^[0-9A-Za-z]{20,128}$' THEN
        SELECT FALSE AS success, 'unauthorized' AS result,
               NULL AS cliente_id, FALSE AS should_send,
               NULL AS delivery_email, NULL AS reset_token,
               v_request_id AS request_id;
        LEAVE proc;
    END IF;

    IF CHAR_LENGTH(v_nome) < 2
       OR CHAR_LENGTH(v_nome) > 150
       OR CHAR_LENGTH(v_email) > 100
       OR v_email NOT REGEXP '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+[.][A-Za-z]{2,}$'
       OR v_status NOT IN ('Ativo', 'Inativo', 'Lead')
       OR (v_status <> 'Lead' AND v_documento IS NULL)
       OR (
            v_documento IS NOT NULL
            AND v_documento NOT REGEXP '(^[0-9]{11}$)|(^[0-9A-Z]{12}[0-9]{2}$)'
       )
       OR (v_whatsapp IS NOT NULL AND v_whatsapp NOT REGEXP '^[0-9]{10,15}$') THEN
        SELECT FALSE AS success, 'invalid_input' AS result,
               NULL AS cliente_id, FALSE AS should_send,
               NULL AS delivery_email, NULL AS reset_token,
               v_request_id AS request_id;
        LEAVE proc;
    END IF;

    START TRANSACTION;

    BEGIN
        DECLARE CONTINUE HANDLER FOR NOT FOUND SET v_admin_id = NULL;

        SELECT f.id
          INTO v_admin_id
          FROM security_sessoes_funcionarios AS s
          JOIN funcionarios AS f ON f.id = s.funcionario_id
         WHERE s.token_hash = SHA2(p_admin_token, 256)
           AND s.expira_em > UTC_TIMESTAMP()
           AND s.revogado_em IS NULL
           AND f.status = 'Ativo'
         LIMIT 1
         FOR UPDATE;
    END;

    IF v_admin_id IS NULL THEN
        ROLLBACK;
        SELECT FALSE AS success, 'unauthorized' AS result,
               NULL AS cliente_id, FALSE AS should_send,
               NULL AS delivery_email, NULL AS reset_token,
               v_request_id AS request_id;
        LEAVE proc;
    END IF;

    SELECT COUNT(*)
      INTO v_duplicate_count
      FROM clientes_emails_autorizados
     WHERE LOWER(TRIM(email)) = v_email;

    IF v_duplicate_count > 0 THEN
        ROLLBACK;
        SELECT FALSE AS success, 'email_conflict' AS result,
               NULL AS cliente_id, FALSE AS should_send,
               NULL AS delivery_email, NULL AS reset_token,
               v_request_id AS request_id;
        LEAVE proc;
    END IF;

    IF v_documento IS NOT NULL THEN
        SELECT COUNT(*)
          INTO v_duplicate_count
          FROM clientes
         WHERE documento_fiscal_canonico = v_documento;

        IF v_duplicate_count > 0 THEN
            ROLLBACK;
            SELECT FALSE AS success, 'document_conflict' AS result,
                   NULL AS cliente_id, FALSE AS should_send,
                   NULL AS delivery_email, NULL AS reset_token,
                   v_request_id AS request_id;
            LEAVE proc;
        END IF;
    END IF;

    INSERT INTO clientes (
        nome_cliente,
        cnpj_cpf,
        cnpj,
        status,
        senha,
        whatsapp
    ) VALUES (
        v_nome,
        CASE WHEN CHAR_LENGTH(v_documento) = 11 THEN v_documento ELSE NULL END,
        CASE WHEN CHAR_LENGTH(v_documento) = 14 THEN v_documento ELSE NULL END,
        v_status,
        NULL,
        v_whatsapp
    );

    SET v_cliente_id = LAST_INSERT_ID();

    INSERT INTO clientes_emails_autorizados (cliente_id, email)
    VALUES (v_cliente_id, v_email);

    IF v_status = 'Ativo' THEN
        SET v_token = LOWER(HEX(RANDOM_BYTES(32)));

        INSERT INTO security_password_reset_clientes (
            cliente_id,
            request_id,
            identity_hash,
            source_hash,
            token_hash,
            resultado_solicitacao,
            expira_em
        ) VALUES (
            v_cliente_id,
            v_request_id,
            SHA2(v_email, 256),
            SHA2(CONCAT('admin:', v_admin_id), 256),
            SHA2(v_token, 256),
            'issued',
            UTC_TIMESTAMP() + INTERVAL 30 MINUTE
        );
    END IF;

    INSERT INTO logs_auditoria (
        funcionario_id,
        acao,
        tabela_afetada,
        registro_id,
        detalhes,
        ip_origem
    ) VALUES (
        v_admin_id,
        'client_created',
        'clientes',
        v_cliente_id,
        JSON_OBJECT(
            'request_id', v_request_id,
            'status', v_status,
            'activation_issued', v_status = 'Ativo'
        ),
        NULL
    );

    COMMIT;

    SELECT
        TRUE AS success,
        'created' AS result,
        v_cliente_id AS cliente_id,
        v_status = 'Ativo' AS should_send,
        CASE WHEN v_status = 'Ativo' THEN v_email ELSE NULL END AS delivery_email,
        v_token AS reset_token,
        v_request_id AS request_id;
END$$

CREATE PROCEDURE sp_admin_cliente_set_folder(
    IN p_admin_token VARCHAR(128),
    IN p_cliente_id INT(11),
    IN p_folder_id VARCHAR(100)
)
SQL SECURITY INVOKER
proc: BEGIN
    DECLARE v_admin_id INT(11) DEFAULT NULL;
    DECLARE v_updated INT DEFAULT 0;
    DECLARE v_request_id CHAR(36) DEFAULT UUID();

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    IF p_admin_token IS NULL
       OR p_admin_token NOT REGEXP '^[0-9A-Za-z]{20,128}$'
       OR p_cliente_id IS NULL
       OR p_cliente_id < 1
       OR p_folder_id IS NULL
       OR CHAR_LENGTH(TRIM(p_folder_id)) < 3
       OR CHAR_LENGTH(TRIM(p_folder_id)) > 100 THEN
        SELECT FALSE AS success, 'invalid_input' AS result,
               v_request_id AS request_id;
        LEAVE proc;
    END IF;

    START TRANSACTION;

    BEGIN
        DECLARE CONTINUE HANDLER FOR NOT FOUND SET v_admin_id = NULL;

        SELECT f.id
          INTO v_admin_id
          FROM security_sessoes_funcionarios AS s
          JOIN funcionarios AS f ON f.id = s.funcionario_id
         WHERE s.token_hash = SHA2(p_admin_token, 256)
           AND s.expira_em > UTC_TIMESTAMP()
           AND s.revogado_em IS NULL
           AND f.status = 'Ativo'
         LIMIT 1
         FOR UPDATE;
    END;

    IF v_admin_id IS NULL THEN
        ROLLBACK;
        SELECT FALSE AS success, 'unauthorized' AS result,
               v_request_id AS request_id;
        LEAVE proc;
    END IF;

    UPDATE clientes
       SET id_pasta_raiz = TRIM(p_folder_id)
     WHERE id = p_cliente_id
       AND id_pasta_raiz IS NULL;

    SET v_updated = ROW_COUNT();

    IF v_updated <> 1 THEN
        ROLLBACK;
        SELECT FALSE AS success, 'not_updated' AS result,
               v_request_id AS request_id;
        LEAVE proc;
    END IF;

    INSERT INTO logs_auditoria (
        funcionario_id,
        acao,
        tabela_afetada,
        registro_id,
        detalhes,
        ip_origem
    ) VALUES (
        v_admin_id,
        'client_folder_linked',
        'clientes',
        p_cliente_id,
        JSON_OBJECT('request_id', v_request_id),
        NULL
    );

    COMMIT;

    SELECT TRUE AS success, 'updated' AS result,
           v_request_id AS request_id;
END$$

CREATE PROCEDURE sp_cliente_password_reset_request(
    IN p_email VARCHAR(100),
    IN p_source_key VARCHAR(128)
)
SQL SECURITY INVOKER
proc: BEGIN
    DECLARE v_email VARCHAR(100);
    DECLARE v_source_key VARCHAR(128);
    DECLARE v_identity_hash CHAR(64);
    DECLARE v_source_hash CHAR(64);
    DECLARE v_request_id CHAR(36) DEFAULT UUID();
    DECLARE v_cliente_id INT(11) DEFAULT NULL;
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
    SET v_source_key = LEFT(COALESCE(NULLIF(TRIM(p_source_key), ''), 'unknown'), 128);
    SET v_identity_hash = SHA2(v_email, 256);
    SET v_source_hash = SHA2(v_source_key, 256);

    START TRANSACTION;

    SELECT COUNT(*) INTO v_identity_count
      FROM security_password_reset_clientes
     WHERE identity_hash = v_identity_hash
       AND solicitado_em > UTC_TIMESTAMP() - INTERVAL 15 MINUTE;

    SELECT COUNT(*) INTO v_source_count
      FROM security_password_reset_clientes
     WHERE source_hash = v_source_hash
       AND solicitado_em > UTC_TIMESTAMP() - INTERVAL 15 MINUTE;

    IF v_identity_count >= 3 OR v_source_count >= 20 THEN
        INSERT INTO security_password_reset_clientes (
            cliente_id, request_id, identity_hash, source_hash,
            token_hash, resultado_solicitacao, expira_em
        ) VALUES (
            NULL, v_request_id, v_identity_hash, v_source_hash,
            NULL, 'rate_limited', NULL
        );

        COMMIT;
        SELECT TRUE AS accepted, FALSE AS should_send,
               NULL AS delivery_email, NULL AS reset_token,
               v_request_id AS request_id;
        LEAVE proc;
    END IF;

    SELECT MAX(c.id), MAX(e.email)
      INTO v_cliente_id, v_delivery_email
      FROM clientes AS c
      JOIN clientes_emails_autorizados AS e ON e.cliente_id = c.id
     WHERE LOWER(TRIM(e.email)) = v_email
       AND c.status = 'Ativo';

    IF v_cliente_id IS NULL THEN
        INSERT INTO security_password_reset_clientes (
            cliente_id, request_id, identity_hash, source_hash,
            token_hash, resultado_solicitacao, expira_em
        ) VALUES (
            NULL, v_request_id, v_identity_hash, v_source_hash,
            NULL, 'not_found', NULL
        );

        COMMIT;
        SELECT TRUE AS accepted, FALSE AS should_send,
               NULL AS delivery_email, NULL AS reset_token,
               v_request_id AS request_id;
        LEAVE proc;
    END IF;

    UPDATE security_password_reset_clientes
       SET revogado_em = UTC_TIMESTAMP()
     WHERE cliente_id = v_cliente_id
       AND resultado_solicitacao = 'issued'
       AND utilizado_em IS NULL
       AND revogado_em IS NULL;

    SET v_token = LOWER(HEX(RANDOM_BYTES(32)));

    INSERT INTO security_password_reset_clientes (
        cliente_id, request_id, identity_hash, source_hash,
        token_hash, resultado_solicitacao, expira_em
    ) VALUES (
        v_cliente_id, v_request_id, v_identity_hash, v_source_hash,
        SHA2(v_token, 256), 'issued',
        UTC_TIMESTAMP() + INTERVAL 30 MINUTE
    );

    INSERT INTO logs_auditoria (
        funcionario_id, acao, tabela_afetada, registro_id,
        detalhes, ip_origem
    ) VALUES (
        NULL, 'client_password_reset_requested', 'clientes', v_cliente_id,
        JSON_OBJECT('request_id', v_request_id, 'result', 'issued'), NULL
    );

    COMMIT;

    SELECT TRUE AS accepted, TRUE AS should_send,
           v_delivery_email AS delivery_email, v_token AS reset_token,
           v_request_id AS request_id;
END$$

CREATE PROCEDURE sp_cliente_password_reset_apply(
    IN p_token VARCHAR(128),
    IN p_new_password VARCHAR(255)
)
SQL SECURITY INVOKER
proc: BEGIN
    DECLARE v_reset_id BIGINT UNSIGNED DEFAULT NULL;
    DECLARE v_cliente_id INT(11) DEFAULT NULL;
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
        SELECT FALSE AS success, 'invalid_or_expired' AS result,
               v_request_id AS request_id;
        LEAVE proc;
    END IF;

    START TRANSACTION;

    BEGIN
        DECLARE CONTINUE HANDLER FOR NOT FOUND SET v_reset_id = NULL;

        SELECT id, cliente_id
          INTO v_reset_id, v_cliente_id
          FROM security_password_reset_clientes
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
        UPDATE security_password_reset_clientes
           SET tentativas_invalidas = LEAST(tentativas_invalidas + 1, 65535)
         WHERE token_hash = SHA2(p_token, 256)
           AND utilizado_em IS NULL
           AND revogado_em IS NULL;

        COMMIT;
        SELECT FALSE AS success, 'invalid_or_expired' AS result,
               v_request_id AS request_id;
        LEAVE proc;
    END IF;

    UPDATE clientes
       SET senha = SHA2(p_new_password, 256)
     WHERE id = v_cliente_id
       AND status = 'Ativo';

    SET v_updated = ROW_COUNT();

    IF v_updated <> 1 THEN
        ROLLBACK;
        SELECT FALSE AS success, 'invalid_or_expired' AS result,
               v_request_id AS request_id;
        LEAVE proc;
    END IF;

    UPDATE security_password_reset_clientes
       SET utilizado_em = UTC_TIMESTAMP()
     WHERE id = v_reset_id;

    UPDATE security_password_reset_clientes
       SET revogado_em = UTC_TIMESTAMP()
     WHERE cliente_id = v_cliente_id
       AND id <> v_reset_id
       AND resultado_solicitacao = 'issued'
       AND utilizado_em IS NULL
       AND revogado_em IS NULL;

    UPDATE security_sessoes_clientes
       SET revogado_em = UTC_TIMESTAMP()
     WHERE cliente_id = v_cliente_id
       AND revogado_em IS NULL;

    INSERT INTO logs_auditoria (
        funcionario_id, acao, tabela_afetada, registro_id,
        detalhes, ip_origem
    ) VALUES (
        NULL, 'client_password_reset_completed', 'clientes', v_cliente_id,
        JSON_OBJECT('request_id', v_request_id, 'result', 'success'), NULL
    );

    COMMIT;

    SELECT TRUE AS success, 'success' AS result,
           v_request_id AS request_id;
END$$

DELIMITER ;
