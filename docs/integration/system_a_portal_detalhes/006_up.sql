-- Sistema A - detalhes e complementos do portal (T-0008).
-- Requer as tabelas existentes de clientes, sessoes, chamados, documentos,
-- mensagens, evidencias e auditoria. Aplicar somente depois de backup e da
-- conferencia de verify_006.sql.
--
-- A migration e aditiva. Os complementos sao append-only; as procedures
-- derivam cliente_id exclusivamente da sessao apresentada.

ALTER TABLE tickets_mensagens
    ADD COLUMN IF NOT EXISTS anexo_nome VARCHAR(255) NULL AFTER anexo_url;

ALTER TABLE inbox_documentos
    ADD UNIQUE KEY IF NOT EXISTS uq_inbox_documentos_id_cliente (id, cliente_id);

CREATE TABLE IF NOT EXISTS inbox_documentos_complementos (
    id BIGINT(20) NOT NULL AUTO_INCREMENT,
    documento_id INT(11) NOT NULL,
    cliente_id INT(11) NOT NULL,
    remetente_tipo ENUM('Cliente', 'Equipe') NOT NULL,
    remetente_id INT(11) NOT NULL,
    mensagem TEXT NOT NULL,
    anexo_url VARCHAR(255) NULL,
    anexo_nome VARCHAR(255) NULL,
    criado_em DATETIME NOT NULL DEFAULT UTC_TIMESTAMP(),
    PRIMARY KEY (id),
    KEY idx_doc_complementos_documento_ordem (documento_id, criado_em, id),
    KEY idx_doc_complementos_cliente (cliente_id),
    CONSTRAINT fk_doc_complementos_documento_cliente
        FOREIGN KEY (documento_id, cliente_id)
        REFERENCES inbox_documentos (id, cliente_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT ck_doc_complementos_conteudo
        CHECK (CHAR_LENGTH(TRIM(mensagem)) > 0 OR anexo_url IS NOT NULL),
    CONSTRAINT ck_doc_complementos_anexo_par
        CHECK ((anexo_url IS NULL) = (anexo_nome IS NULL))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP PROCEDURE IF EXISTS sp_portal_detalhe_chamado;
DROP PROCEDURE IF EXISTS sp_portal_complementar_chamado;
DROP PROCEDURE IF EXISTS sp_portal_detalhe_documento;
DROP PROCEDURE IF EXISTS sp_portal_complementar_documento;

DELIMITER $$

CREATE PROCEDURE sp_portal_detalhe_chamado(
    IN p_token VARCHAR(128),
    IN p_ticket_id INT(11)
)
SQL SECURITY INVOKER
proc: BEGIN
    DECLARE v_hash CHAR(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_uca1400_ai_ci;
    DECLARE v_cliente_id INT(11) DEFAULT NULL;

    IF p_token IS NULL
       OR p_token NOT REGEXP '^[0-9A-Za-z]{20,128}$' THEN
        SELECT FALSE AS success, 'unauthorized' AS result;
        LEAVE proc;
    END IF;

    SET v_hash = SHA2(p_token, 256);

    BEGIN
        DECLARE CONTINUE HANDLER FOR NOT FOUND SET v_cliente_id = NULL;
        SELECT cliente_id INTO v_cliente_id
          FROM security_sessoes_clientes
         WHERE token_hash = v_hash
           AND expira_em > UTC_TIMESTAMP()
           AND revogado_em IS NULL
         LIMIT 1;
    END;

    IF v_cliente_id IS NULL THEN
        SELECT FALSE AS success, 'unauthorized' AS result;
        LEAVE proc;
    END IF;

    IF p_ticket_id IS NULL OR p_ticket_id <= 0
       OR NOT EXISTS (
           SELECT 1 FROM tickets_master
            WHERE id = p_ticket_id AND cliente_id = v_cliente_id
       ) THEN
        SELECT FALSE AS success, 'not_found' AS result;
        LEAVE proc;
    END IF;

    SELECT TRUE AS success, 'found' AS result,
           t.id, t.numero_ticket, t.assunto, t.descricao, t.status,
           t.area, t.prioridade, t.competencia, t.data_limite,
           t.pessoa_responsavel, t.data_entrega, t.responsavel_interno,
           t.criado_em, t.atualizado_em,
           c.id_pasta_raiz AS drive_folder_id,
           COALESCE((
               SELECT JSON_ARRAYAGG(JSON_OBJECT(
                   'id', m.id,
                   'mensagem', m.mensagem,
                   'arquivo_url', m.anexo_url,
                   'arquivo_nome', m.anexo_nome,
                   'criado_em', m.criado_em,
                   'autor', m.remetente_tipo,
                   'tipo', IF(m.remetente_tipo = 'Cliente', 'cliente', 'equipe')
               ) ORDER BY m.criado_em, m.id)
                 FROM tickets_mensagens AS m
                WHERE m.ticket_id = t.id
           ), JSON_ARRAY()) AS complementos,
           COALESCE((
               SELECT JSON_ARRAYAGG(JSON_OBJECT(
                   'nome', e.nome_evidencia,
                   'tipo', e.tipo,
                   'arquivo_url', e.link_arquivo
               ) ORDER BY e.id)
                 FROM evidencias_protocolos AS e
                WHERE e.ticket_id = t.id
                  AND e.cliente_id = v_cliente_id
           ), JSON_ARRAY()) AS anexos_abertura
      FROM tickets_master AS t
      JOIN clientes AS c ON c.id = t.cliente_id
     WHERE t.id = p_ticket_id
       AND t.cliente_id = v_cliente_id
     LIMIT 1;
END$$

CREATE PROCEDURE sp_portal_complementar_chamado(
    IN p_token VARCHAR(128),
    IN p_ticket_id INT(11),
    IN p_mensagem TEXT,
    IN p_anexo_url VARCHAR(255),
    IN p_anexo_nome VARCHAR(255)
)
SQL SECURITY INVOKER
proc: BEGIN
    DECLARE v_hash CHAR(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_uca1400_ai_ci;
    DECLARE v_cliente_id INT(11) DEFAULT NULL;
    DECLARE v_status VARCHAR(100) DEFAULT NULL;
    DECLARE v_complemento_id BIGINT(20) DEFAULT NULL;
    DECLARE v_request_id CHAR(36) DEFAULT UUID();
    DECLARE v_mensagem TEXT;
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    SET v_mensagem = TRIM(COALESCE(p_mensagem, ''));

    IF p_token IS NULL
       OR p_token NOT REGEXP '^[0-9A-Za-z]{20,128}$' THEN
        SELECT FALSE AS success, 'unauthorized' AS result;
        LEAVE proc;
    END IF;
    IF p_ticket_id IS NULL OR p_ticket_id <= 0
       OR CHAR_LENGTH(v_mensagem) > 5000
       OR ((p_anexo_url IS NULL) <> (p_anexo_nome IS NULL))
       OR (v_mensagem = '' AND p_anexo_url IS NULL) THEN
        SELECT FALSE AS success, 'invalid_input' AS result;
        LEAVE proc;
    END IF;

    SET v_hash = SHA2(p_token, 256);
    START TRANSACTION;

    BEGIN
        DECLARE CONTINUE HANDLER FOR NOT FOUND SET v_cliente_id = NULL;
        SELECT cliente_id INTO v_cliente_id
          FROM security_sessoes_clientes
         WHERE token_hash = v_hash
           AND expira_em > UTC_TIMESTAMP()
           AND revogado_em IS NULL
         LIMIT 1
         FOR UPDATE;
    END;

    IF v_cliente_id IS NULL THEN
        ROLLBACK;
        SELECT FALSE AS success, 'unauthorized' AS result;
        LEAVE proc;
    END IF;

    BEGIN
        DECLARE CONTINUE HANDLER FOR NOT FOUND SET v_status = NULL;
        SELECT status INTO v_status
          FROM tickets_master
         WHERE id = p_ticket_id
           AND cliente_id = v_cliente_id
         LIMIT 1
         FOR UPDATE;
    END;

    IF v_status IS NULL THEN
        ROLLBACK;
        SELECT FALSE AS success, 'not_found' AS result;
        LEAVE proc;
    END IF;
    IF BINARY LOWER(TRIM(v_status)) IN ('concluido', 'concluído') THEN
        ROLLBACK;
        SELECT FALSE AS success, 'closed' AS result;
        LEAVE proc;
    END IF;

    INSERT INTO tickets_mensagens (
        ticket_id, remetente_tipo, remetente_id, mensagem,
        anexo_url, anexo_nome, criado_em
    ) VALUES (
        p_ticket_id, 'Cliente', v_cliente_id, v_mensagem,
        p_anexo_url, p_anexo_nome, UTC_TIMESTAMP()
    );
    SET v_complemento_id = LAST_INSERT_ID();

    UPDATE tickets_master
       SET atualizado_em = UTC_TIMESTAMP()
     WHERE id = p_ticket_id AND cliente_id = v_cliente_id;

    INSERT INTO logs_auditoria (
        funcionario_id, acao, tabela_afetada, registro_id, detalhes, ip_origem
    ) VALUES (
        NULL, 'client_ticket_complement', 'tickets_master', p_ticket_id,
        JSON_OBJECT(
            'request_id', v_request_id,
            'complement_id', v_complemento_id,
            'has_attachment', p_anexo_url IS NOT NULL
        ), NULL
    );

    COMMIT;
    SELECT TRUE AS success, 'created' AS result,
           v_complemento_id AS complemento_id, v_request_id AS request_id;
END$$

CREATE PROCEDURE sp_portal_detalhe_documento(
    IN p_token VARCHAR(128),
    IN p_documento_id INT(11)
)
SQL SECURITY INVOKER
proc: BEGIN
    DECLARE v_hash CHAR(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_uca1400_ai_ci;
    DECLARE v_cliente_id INT(11) DEFAULT NULL;

    IF p_token IS NULL
       OR p_token NOT REGEXP '^[0-9A-Za-z]{20,128}$' THEN
        SELECT FALSE AS success, 'unauthorized' AS result;
        LEAVE proc;
    END IF;
    SET v_hash = SHA2(p_token, 256);

    BEGIN
        DECLARE CONTINUE HANDLER FOR NOT FOUND SET v_cliente_id = NULL;
        SELECT cliente_id INTO v_cliente_id
          FROM security_sessoes_clientes
         WHERE token_hash = v_hash
           AND expira_em > UTC_TIMESTAMP()
           AND revogado_em IS NULL
         LIMIT 1;
    END;

    IF v_cliente_id IS NULL THEN
        SELECT FALSE AS success, 'unauthorized' AS result;
        LEAVE proc;
    END IF;

    IF p_documento_id IS NULL OR p_documento_id <= 0
       OR NOT EXISTS (
           SELECT 1 FROM inbox_documentos
            WHERE id = p_documento_id AND cliente_id = v_cliente_id
       ) THEN
        SELECT FALSE AS success, 'not_found' AS result;
        LEAVE proc;
    END IF;

    SELECT TRUE AS success, 'found' AS result,
           d.id, d.titulo, d.area_responsavel, d.competencia,
           d.tipo_documento, d.link_externo_url, d.status,
           d.observacao_escritorio, d.observacao_cliente,
           d.ticket_id, d.entrega_id, d.origem_documento,
           d.nome_arquivo, d.criado_em, d.atualizado_em,
           c.id_pasta_raiz AS drive_folder_id,
           COALESCE((
               SELECT JSON_ARRAYAGG(JSON_OBJECT(
                   'id', x.id,
                   'mensagem', x.mensagem,
                   'arquivo_url', x.anexo_url,
                   'arquivo_nome', x.anexo_nome,
                   'criado_em', x.criado_em,
                   'autor', x.remetente_tipo,
                   'tipo', IF(x.remetente_tipo = 'Cliente', 'cliente', 'equipe')
               ) ORDER BY x.criado_em, x.id)
                 FROM inbox_documentos_complementos AS x
                WHERE x.documento_id = d.id
                  AND x.cliente_id = v_cliente_id
           ), JSON_ARRAY()) AS complementos
      FROM inbox_documentos AS d
      JOIN clientes AS c ON c.id = d.cliente_id
     WHERE d.id = p_documento_id
       AND d.cliente_id = v_cliente_id
     LIMIT 1;
END$$

CREATE PROCEDURE sp_portal_complementar_documento(
    IN p_token VARCHAR(128),
    IN p_documento_id INT(11),
    IN p_mensagem TEXT,
    IN p_anexo_url VARCHAR(255),
    IN p_anexo_nome VARCHAR(255)
)
SQL SECURITY INVOKER
proc: BEGIN
    DECLARE v_hash CHAR(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_uca1400_ai_ci;
    DECLARE v_cliente_id INT(11) DEFAULT NULL;
    DECLARE v_status VARCHAR(100) DEFAULT NULL;
    DECLARE v_complemento_id BIGINT(20) DEFAULT NULL;
    DECLARE v_request_id CHAR(36) DEFAULT UUID();
    DECLARE v_mensagem TEXT;
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    SET v_mensagem = TRIM(COALESCE(p_mensagem, ''));

    IF p_token IS NULL
       OR p_token NOT REGEXP '^[0-9A-Za-z]{20,128}$' THEN
        SELECT FALSE AS success, 'unauthorized' AS result;
        LEAVE proc;
    END IF;
    IF p_documento_id IS NULL OR p_documento_id <= 0
       OR CHAR_LENGTH(v_mensagem) > 5000
       OR ((p_anexo_url IS NULL) <> (p_anexo_nome IS NULL))
       OR (v_mensagem = '' AND p_anexo_url IS NULL) THEN
        SELECT FALSE AS success, 'invalid_input' AS result;
        LEAVE proc;
    END IF;

    SET v_hash = SHA2(p_token, 256);
    START TRANSACTION;

    BEGIN
        DECLARE CONTINUE HANDLER FOR NOT FOUND SET v_cliente_id = NULL;
        SELECT cliente_id INTO v_cliente_id
          FROM security_sessoes_clientes
         WHERE token_hash = v_hash
           AND expira_em > UTC_TIMESTAMP()
           AND revogado_em IS NULL
         LIMIT 1
         FOR UPDATE;
    END;

    IF v_cliente_id IS NULL THEN
        ROLLBACK;
        SELECT FALSE AS success, 'unauthorized' AS result;
        LEAVE proc;
    END IF;

    BEGIN
        DECLARE CONTINUE HANDLER FOR NOT FOUND SET v_status = NULL;
        SELECT status INTO v_status
          FROM inbox_documentos
         WHERE id = p_documento_id
           AND cliente_id = v_cliente_id
         LIMIT 1
         FOR UPDATE;
    END;

    IF v_status IS NULL THEN
        ROLLBACK;
        SELECT FALSE AS success, 'not_found' AS result;
        LEAVE proc;
    END IF;
    IF BINARY LOWER(TRIM(v_status)) IN (
        'processado', 'concluido', 'concluído', 'rejeitado'
    ) THEN
        ROLLBACK;
        SELECT FALSE AS success, 'closed' AS result;
        LEAVE proc;
    END IF;

    INSERT INTO inbox_documentos_complementos (
        documento_id, cliente_id, remetente_tipo, remetente_id,
        mensagem, anexo_url, anexo_nome, criado_em
    ) VALUES (
        p_documento_id, v_cliente_id, 'Cliente', v_cliente_id,
        v_mensagem, p_anexo_url, p_anexo_nome, UTC_TIMESTAMP()
    );
    SET v_complemento_id = LAST_INSERT_ID();

    UPDATE inbox_documentos
       SET atualizado_em = UTC_TIMESTAMP()
     WHERE id = p_documento_id AND cliente_id = v_cliente_id;

    INSERT INTO logs_auditoria (
        funcionario_id, acao, tabela_afetada, registro_id, detalhes, ip_origem
    ) VALUES (
        NULL, 'client_document_complement', 'inbox_documentos', p_documento_id,
        JSON_OBJECT(
            'request_id', v_request_id,
            'complement_id', v_complemento_id,
            'has_attachment', p_anexo_url IS NOT NULL
        ), NULL
    );

    COMMIT;
    SELECT TRUE AS success, 'created' AS result,
           v_complemento_id AS complemento_id, v_request_id AS request_id;
END$$

DELIMITER ;
