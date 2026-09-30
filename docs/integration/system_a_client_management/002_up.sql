-- Sistema A - edicao segura de clientes.
-- Aplicar somente depois de 001_up.sql e com backup verificado.

ALTER TABLE clientes
    ADD COLUMN IF NOT EXISTS telefone VARCHAR(20) NULL AFTER whatsapp;

DROP PROCEDURE IF EXISTS sp_admin_cliente_update;

DELIMITER $$

CREATE PROCEDURE sp_admin_cliente_update(
    IN p_admin_token VARCHAR(128),
    IN p_cliente_id INT(11),
    IN p_nome VARCHAR(150),
    IN p_email VARCHAR(100),
    IN p_documento VARCHAR(20),
    IN p_status VARCHAR(16),
    IN p_whatsapp VARCHAR(20),
    IN p_telefone VARCHAR(20)
)
SQL SECURITY INVOKER
proc: BEGIN
    DECLARE v_admin_id INT(11) DEFAULT NULL;
    DECLARE v_nome VARCHAR(150);
    DECLARE v_email VARCHAR(100);
    DECLARE v_documento VARCHAR(20);
    DECLARE v_status VARCHAR(16);
    DECLARE v_whatsapp VARCHAR(20);
    DECLARE v_telefone VARCHAR(20);
    DECLARE v_status_anterior VARCHAR(16) DEFAULT NULL;
    DECLARE v_cliente_encontrado INT(11) DEFAULT NULL;
    DECLARE v_senha VARCHAR(255) DEFAULT NULL;
    DECLARE v_folder_id VARCHAR(100) DEFAULT NULL;
    DECLARE v_request_id CHAR(36) DEFAULT UUID();
    DECLARE v_token CHAR(64) DEFAULT NULL;
    DECLARE v_duplicate_count INT UNSIGNED DEFAULT 0;
    DECLARE v_email_count INT UNSIGNED DEFAULT 0;

    DECLARE EXIT HANDLER FOR 1062
    BEGIN
        ROLLBACK;
        SELECT FALSE AS success, 'conflict' AS result,
               FALSE AS should_send, NULL AS delivery_email,
               NULL AS reset_token, NULL AS folder_id,
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
    SET v_status = TRIM(COALESCE(p_status, ''));
    SET v_whatsapp = NULLIF(TRIM(COALESCE(p_whatsapp, '')), '');
    SET v_telefone = NULLIF(TRIM(COALESCE(p_telefone, '')), '');

    IF p_admin_token IS NULL
       OR p_admin_token NOT REGEXP '^[0-9A-Za-z]{20,128}$' THEN
        SELECT FALSE AS success, 'unauthorized' AS result,
               FALSE AS should_send, NULL AS delivery_email,
               NULL AS reset_token, NULL AS folder_id,
               v_request_id AS request_id;
        LEAVE proc;
    END IF;

    IF p_cliente_id IS NULL
       OR p_cliente_id < 1
       OR CHAR_LENGTH(v_nome) < 2
       OR CHAR_LENGTH(v_nome) > 150
       OR CHAR_LENGTH(v_email) > 100
       OR v_email NOT REGEXP '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+[.][A-Za-z]{2,}$'
       OR v_status NOT IN ('Ativo', 'Inativo', 'Lead')
       OR (v_status <> 'Lead' AND v_documento IS NULL)
       OR (
            v_documento IS NOT NULL
            AND v_documento NOT REGEXP '(^[0-9]{11}$)|(^[0-9A-Z]{12}[0-9]{2}$)'
       )
       OR (v_whatsapp IS NOT NULL AND v_whatsapp NOT REGEXP '^[0-9]{10,15}$')
       OR (v_telefone IS NOT NULL AND v_telefone NOT REGEXP '^[0-9]{10,15}$') THEN
        SELECT FALSE AS success, 'invalid_input' AS result,
               FALSE AS should_send, NULL AS delivery_email,
               NULL AS reset_token, NULL AS folder_id,
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
               FALSE AS should_send, NULL AS delivery_email,
               NULL AS reset_token, NULL AS folder_id,
               v_request_id AS request_id;
        LEAVE proc;
    END IF;

    BEGIN
        DECLARE CONTINUE HANDLER FOR NOT FOUND SET v_cliente_encontrado = NULL;

        SELECT id, status, senha, id_pasta_raiz
          INTO v_cliente_encontrado, v_status_anterior, v_senha, v_folder_id
          FROM clientes
         WHERE id = p_cliente_id
         LIMIT 1
         FOR UPDATE;
    END;

    IF v_cliente_encontrado IS NULL THEN
        ROLLBACK;
        SELECT FALSE AS success, 'not_found' AS result,
               FALSE AS should_send, NULL AS delivery_email,
               NULL AS reset_token, NULL AS folder_id,
               v_request_id AS request_id;
        LEAVE proc;
    END IF;

    SELECT COUNT(*) INTO v_duplicate_count
      FROM clientes_emails_autorizados
     WHERE LOWER(TRIM(email)) = v_email
       AND cliente_id <> p_cliente_id;

    IF v_duplicate_count > 0 THEN
        ROLLBACK;
        SELECT FALSE AS success, 'email_conflict' AS result,
               FALSE AS should_send, NULL AS delivery_email,
               NULL AS reset_token, NULL AS folder_id,
               v_request_id AS request_id;
        LEAVE proc;
    END IF;

    IF v_documento IS NOT NULL THEN
        SELECT COUNT(*) INTO v_duplicate_count
          FROM clientes
         WHERE documento_fiscal_canonico = v_documento
           AND id <> p_cliente_id;

        IF v_duplicate_count > 0 THEN
            ROLLBACK;
            SELECT FALSE AS success, 'document_conflict' AS result,
                   FALSE AS should_send, NULL AS delivery_email,
                   NULL AS reset_token, NULL AS folder_id,
                   v_request_id AS request_id;
            LEAVE proc;
        END IF;
    END IF;

    UPDATE clientes
       SET nome_cliente = v_nome,
           cnpj_cpf = CASE
               WHEN CHAR_LENGTH(v_documento) = 11 THEN v_documento
               ELSE NULL
           END,
           cnpj = CASE
               WHEN CHAR_LENGTH(v_documento) = 14 THEN v_documento
               ELSE NULL
           END,
           status = v_status,
           whatsapp = v_whatsapp,
           telefone = v_telefone
     WHERE id = p_cliente_id;

    SELECT COUNT(*) INTO v_email_count
      FROM clientes_emails_autorizados
     WHERE cliente_id = p_cliente_id;

    IF v_email_count = 0 THEN
        INSERT INTO clientes_emails_autorizados (cliente_id, email)
        VALUES (p_cliente_id, v_email);
    ELSE
        UPDATE clientes_emails_autorizados
           SET email = v_email
         WHERE cliente_id = p_cliente_id
         ORDER BY id
         LIMIT 1;
    END IF;

    IF v_status <> 'Ativo' THEN
        UPDATE security_sessoes_clientes
           SET revogado_em = UTC_TIMESTAMP()
         WHERE cliente_id = p_cliente_id
           AND revogado_em IS NULL;

        UPDATE security_password_reset_clientes
           SET revogado_em = UTC_TIMESTAMP()
         WHERE cliente_id = p_cliente_id
           AND resultado_solicitacao = 'issued'
           AND utilizado_em IS NULL
           AND revogado_em IS NULL;
    ELSEIF COALESCE(v_status_anterior, '') <> 'Ativo' AND v_senha IS NULL THEN
        UPDATE security_password_reset_clientes
           SET revogado_em = UTC_TIMESTAMP()
         WHERE cliente_id = p_cliente_id
           AND resultado_solicitacao = 'issued'
           AND utilizado_em IS NULL
           AND revogado_em IS NULL;

        SET v_token = LOWER(HEX(RANDOM_BYTES(32)));

        INSERT INTO security_password_reset_clientes (
            cliente_id, request_id, identity_hash, source_hash,
            token_hash, resultado_solicitacao, expira_em
        ) VALUES (
            p_cliente_id, v_request_id, SHA2(v_email, 256),
            SHA2(CONCAT('admin:', v_admin_id), 256),
            SHA2(v_token, 256), 'issued',
            UTC_TIMESTAMP() + INTERVAL 30 MINUTE
        );
    END IF;

    INSERT INTO logs_auditoria (
        funcionario_id, acao, tabela_afetada, registro_id,
        detalhes, ip_origem
    ) VALUES (
        v_admin_id, 'client_updated', 'clientes', p_cliente_id,
        JSON_OBJECT(
            'request_id', v_request_id,
            'previous_status', v_status_anterior,
            'new_status', v_status
        ),
        NULL
    );

    COMMIT;

    SELECT TRUE AS success, 'updated' AS result,
           v_token IS NOT NULL AS should_send,
           CASE WHEN v_token IS NOT NULL THEN v_email ELSE NULL END AS delivery_email,
           v_token AS reset_token, v_folder_id AS folder_id,
           v_request_id AS request_id;
END$$

DELIMITER ;
