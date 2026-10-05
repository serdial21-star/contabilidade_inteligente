CREATE DATABASE IF NOT EXISTS serdial21_portal_details_test
    CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE serdial21_portal_details_test;

CREATE TABLE clientes (
    id INT(11) NOT NULL AUTO_INCREMENT,
    nome_cliente VARCHAR(150) NOT NULL,
    id_pasta_raiz VARCHAR(100) NULL,
    PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE security_sessoes_clientes (
    id BIGINT(20) NOT NULL AUTO_INCREMENT,
    cliente_id INT(11) NOT NULL,
    token_hash CHAR(64) NOT NULL,
    expira_em DATETIME NOT NULL,
    revogado_em DATETIME NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uq_token_hash (token_hash),
    KEY idx_cliente_id (cliente_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;

CREATE TABLE tickets_master (
    id INT(11) NOT NULL AUTO_INCREMENT,
    cliente_id INT(11) NOT NULL,
    numero_ticket VARCHAR(50) NOT NULL,
    assunto VARCHAR(255) NOT NULL,
    descricao TEXT NOT NULL,
    status VARCHAR(100) NOT NULL,
    area VARCHAR(100) NULL,
    prioridade VARCHAR(50) NULL,
    competencia VARCHAR(20) NULL,
    data_limite DATE NULL,
    pessoa_responsavel VARCHAR(150) NULL,
    data_entrega DATE NULL,
    responsavel_interno VARCHAR(150) NULL,
    criado_em DATETIME NOT NULL DEFAULT UTC_TIMESTAMP(),
    atualizado_em DATETIME NOT NULL DEFAULT UTC_TIMESTAMP(),
    PRIMARY KEY (id),
    KEY idx_ticket_cliente (cliente_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE tickets_mensagens (
    id INT(11) NOT NULL AUTO_INCREMENT,
    ticket_id INT(11) NOT NULL,
    remetente_tipo ENUM('Cliente', 'Equipe') NOT NULL,
    remetente_id INT(11) NOT NULL,
    mensagem TEXT NOT NULL,
    anexo_url VARCHAR(255) NULL,
    criado_em DATETIME NOT NULL DEFAULT UTC_TIMESTAMP(),
    PRIMARY KEY (id),
    KEY idx_ticket_mensagem (ticket_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE evidencias_protocolos (
    id INT(11) NOT NULL AUTO_INCREMENT,
    cliente_id INT(11) NOT NULL,
    nome_evidencia VARCHAR(255) NOT NULL,
    tipo VARCHAR(100) NULL,
    link_arquivo VARCHAR(255) NOT NULL,
    ticket_id INT(11) NULL,
    PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE inbox_documentos (
    id INT(11) NOT NULL AUTO_INCREMENT,
    titulo VARCHAR(255) NOT NULL,
    area_responsavel VARCHAR(100) NULL,
    competencia VARCHAR(20) NULL,
    tipo_documento VARCHAR(100) NULL,
    link_externo_url VARCHAR(255) NULL,
    status VARCHAR(100) NOT NULL,
    observacao_escritorio TEXT NULL,
    observacao_cliente TEXT NULL,
    ticket_id INT(11) NULL,
    entrega_id INT(11) NULL,
    cliente_id INT(11) NOT NULL,
    criado_em DATETIME NOT NULL DEFAULT UTC_TIMESTAMP(),
    atualizado_em DATETIME NOT NULL DEFAULT UTC_TIMESTAMP(),
    origem_documento VARCHAR(100) NULL,
    nome_arquivo VARCHAR(255) NULL,
    PRIMARY KEY (id),
    KEY idx_documento_cliente (cliente_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE logs_auditoria (
    id INT(11) NOT NULL AUTO_INCREMENT,
    funcionario_id INT(11) NULL,
    acao VARCHAR(100) NOT NULL,
    tabela_afetada VARCHAR(50) NULL,
    registro_id INT(11) NULL,
    detalhes TEXT NULL,
    ip_origem VARCHAR(50) NULL,
    data_hora TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP(),
    PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO clientes (nome_cliente, id_pasta_raiz) VALUES
    ('Cliente Sintetico A', 'folder-a'),
    ('Cliente Sintetico B', 'folder-b');

INSERT INTO security_sessoes_clientes (
    cliente_id, token_hash, expira_em, revogado_em
) VALUES
    (1, SHA2('SyntheticPortalClientTokenA01', 256), UTC_TIMESTAMP() + INTERVAL 1 HOUR, NULL),
    (2, SHA2('SyntheticPortalClientTokenB02', 256), UTC_TIMESTAMP() + INTERVAL 1 HOUR, NULL),
    (1, SHA2('SyntheticPortalExpiredToken03', 256), UTC_TIMESTAMP() - INTERVAL 1 MINUTE, NULL),
    (1, SHA2('SyntheticPortalRevokedToken04', 256), UTC_TIMESTAMP() + INTERVAL 1 HOUR, UTC_TIMESTAMP());

INSERT INTO tickets_master (
    cliente_id, numero_ticket, assunto, descricao, status, area, prioridade
) VALUES
    (1, 'SYN-001', 'Chamado aberto A', 'Descricao sintetica', 'aberto', 'Fiscal', 'normal'),
    (2, 'SYN-002', 'Chamado aberto B', 'Descricao sintetica', 'aberto', 'Contabil', 'normal'),
    (1, 'SYN-003', 'Chamado fechado A', 'Descricao sintetica', 'concluido', 'Fiscal', 'normal');

INSERT INTO evidencias_protocolos (
    cliente_id, nome_evidencia, tipo, link_arquivo, ticket_id
) VALUES (1, 'abertura.pdf', 'application/pdf', 'https://example.invalid/opening', 1);

INSERT INTO inbox_documentos (
    titulo, area_responsavel, status, cliente_id, nome_arquivo
) VALUES
    ('Documento aberto A', 'Fiscal', 'pendente', 1, 'documento-a.pdf'),
    ('Documento aberto B', 'Contabil', 'pendente', 2, 'documento-b.pdf'),
    ('Documento fechado A', 'Fiscal', 'processado', 1, 'documento-c.pdf');
