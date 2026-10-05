-- Reverte a estrutura da 006. Complementos e auditoria sao historico.
-- Por seguranca, o downgrade recusa remover a tabela se ela contiver linhas.
-- Eventos de logs_auditoria e valores de atualizado_em nao sao desfeitos.

DROP PROCEDURE IF EXISTS sp_006_guarded_down;

DELIMITER $$
CREATE PROCEDURE sp_006_guarded_down()
SQL SECURITY INVOKER
BEGIN
    IF EXISTS (SELECT 1 FROM inbox_documentos_complementos LIMIT 1) THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = '006_down recusado: preserve ou remova conscientemente os complementos primeiro';
    END IF;
    IF EXISTS (
        SELECT 1 FROM tickets_mensagens WHERE anexo_nome IS NOT NULL LIMIT 1
    ) THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = '006_down recusado: preserve nomes dos anexos de chamados primeiro';
    END IF;

    DROP TABLE inbox_documentos_complementos;
    ALTER TABLE inbox_documentos
        DROP INDEX uq_inbox_documentos_id_cliente;
    ALTER TABLE tickets_mensagens
        DROP COLUMN anexo_nome;
END$$
DELIMITER ;

CALL sp_006_guarded_down();
DROP PROCEDURE sp_006_guarded_down;

DROP PROCEDURE IF EXISTS sp_portal_detalhe_chamado;
DROP PROCEDURE IF EXISTS sp_portal_complementar_chamado;
DROP PROCEDURE IF EXISTS sp_portal_detalhe_documento;
DROP PROCEDURE IF EXISTS sp_portal_complementar_documento;
