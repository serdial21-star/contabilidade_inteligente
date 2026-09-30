CREATE DATABASE IF NOT EXISTS serdial21_client_management_test
    CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE serdial21_client_management_test;

CREATE TABLE funcionarios (
    id INT(11) NOT NULL AUTO_INCREMENT,
    nome_funcionario VARCHAR(150) NOT NULL,
    email VARCHAR(100) NOT NULL,
    senha VARCHAR(64) NOT NULL,
    cargo VARCHAR(50) NULL DEFAULT 'Operador',
    status ENUM('Ativo', 'Inativo') NULL DEFAULT 'Ativo',
    atualizado_em TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP()
        ON UPDATE CURRENT_TIMESTAMP(),
    PRIMARY KEY (id),
    UNIQUE KEY email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE clientes (
    id INT(11) NOT NULL AUTO_INCREMENT,
    nome_cliente VARCHAR(150) NOT NULL,
    nome_fantasia VARCHAR(255) NULL,
    cnpj_cpf VARCHAR(20) NULL,
    cnpj VARCHAR(20) NULL,
    status ENUM('Ativo', 'Inativo', 'Lead') NULL DEFAULT 'Ativo',
    senha VARCHAR(255) NULL,
    codigo_sistema VARCHAR(50) NULL,
    id_pasta_inbox VARCHAR(100) NULL,
    id_pasta_raiz VARCHAR(100) NULL,
    responsavel VARCHAR(100) NULL,
    whatsapp VARCHAR(20) NULL,
    inicio_prestacao_servicos DATE NULL,
    valor_contrato DECIMAL(10, 2) NULL,
    vencimento_contrato DATE NULL,
    criado_em TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP(),
    aceita_notificacao_email TINYINT(1) NULL DEFAULT 1,
    aceita_notificacao_whatsapp TINYINT(1) NULL DEFAULT 1,
    PRIMARY KEY (id),
    UNIQUE KEY cnpj (cnpj)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE clientes_emails_autorizados (
    id INT(11) NOT NULL AUTO_INCREMENT,
    cliente_id INT(11) NOT NULL,
    email VARCHAR(100) NOT NULL,
    adicionado_em TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP(),
    PRIMARY KEY (id),
    UNIQUE KEY email (email),
    KEY cliente_id (cliente_id),
    CONSTRAINT clientes_emails_autorizados_ibfk_1
        FOREIGN KEY (cliente_id) REFERENCES clientes (id)
        ON UPDATE RESTRICT ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE security_sessoes_funcionarios (
    id INT(11) NOT NULL AUTO_INCREMENT,
    funcionario_id INT(11) NOT NULL,
    token_hash VARCHAR(64) NOT NULL,
    criado_em TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP(),
    expira_em DATETIME NOT NULL,
    revogado_em DATETIME NULL,
    PRIMARY KEY (id),
    KEY funcionario_id (funcionario_id),
    CONSTRAINT security_sessoes_funcionarios_ibfk_1
        FOREIGN KEY (funcionario_id) REFERENCES funcionarios (id)
        ON UPDATE RESTRICT ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE security_sessoes_clientes (
    id BIGINT(20) NOT NULL AUTO_INCREMENT,
    cliente_id INT(11) NOT NULL,
    email VARCHAR(100) NULL,
    token_hash CHAR(64) NOT NULL,
    criado_em TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP(),
    expira_em DATETIME NOT NULL,
    ultimo_uso_em DATETIME NULL,
    revogado_em DATETIME NULL,
    ip_origem VARCHAR(50) NULL,
    user_agent VARCHAR(255) NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uq_token_hash (token_hash),
    KEY idx_token_hash (token_hash),
    KEY idx_cliente_id (cliente_id),
    KEY idx_expira_em (expira_em)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;

CREATE TABLE logs_auditoria (
    id INT(11) NOT NULL AUTO_INCREMENT,
    funcionario_id INT(11) NULL,
    acao VARCHAR(100) NOT NULL,
    tabela_afetada VARCHAR(50) NULL,
    registro_id INT(11) NULL,
    detalhes TEXT NULL,
    ip_origem VARCHAR(50) NULL,
    data_hora TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP(),
    PRIMARY KEY (id),
    KEY funcionario_id (funcionario_id),
    CONSTRAINT logs_auditoria_ibfk_1
        FOREIGN KEY (funcionario_id) REFERENCES funcionarios (id)
        ON UPDATE RESTRICT ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO funcionarios (
    nome_funcionario, email, senha, cargo, status
) VALUES (
    'Usuario Sintetico', 'synthetic-admin@example.invalid',
    SHA2('SyntheticOnly9x!', 256), 'Administrador', 'Ativo'
);

INSERT INTO security_sessoes_funcionarios (
    funcionario_id, token_hash, expira_em
) VALUES (
    1, SHA2('SyntheticAdminToken1234567890', 256),
    UTC_TIMESTAMP() + INTERVAL 1 HOUR
);
