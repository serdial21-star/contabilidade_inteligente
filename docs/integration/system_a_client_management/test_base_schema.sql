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

CREATE TABLE permissoes_funcionario_modulos (
    id INT(11) NOT NULL AUTO_INCREMENT,
    funcionario_id INT(11) NOT NULL,
    modulo VARCHAR(50) NOT NULL,
    acao VARCHAR(20) NOT NULL,
    permitido TINYINT(1) NOT NULL DEFAULT 1,
    criado_em DATETIME NULL DEFAULT CURRENT_TIMESTAMP(),
    atualizado_em DATETIME NULL DEFAULT CURRENT_TIMESTAMP()
        ON UPDATE CURRENT_TIMESTAMP(),
    PRIMARY KEY (id),
    UNIQUE KEY uk_func_modulo_acao (funcionario_id, modulo, acao),
    KEY idx_func_id (funcionario_id)
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

INSERT INTO funcionarios (nome_funcionario, email, senha, cargo, status) VALUES
    ('Administrador Sintetico', 'administrator@example.invalid', SHA2('SyntheticOnly9x!', 256), 'Administrador', 'Ativo'),
    ('Admin Sintetico', 'admin@example.invalid', SHA2('SyntheticOnly9x!', 256), 'Admin', 'Ativo'),
    ('Operador Permitido', 'operator-allowed@example.invalid', SHA2('SyntheticOnly9x!', 256), 'Operador', 'Ativo'),
    ('Operador Sem Linhas', 'operator-missing@example.invalid', SHA2('SyntheticOnly9x!', 256), 'Operador', 'Ativo'),
    ('Operador Negado', 'operator-denied@example.invalid', SHA2('SyntheticOnly9x!', 256), 'Operador', 'Ativo'),
    ('Auditor Sintetico', 'auditor@example.invalid', SHA2('SyntheticOnly9x!', 256), 'Auditor', 'Ativo'),
    ('Cargo Desconhecido', 'unknown-role@example.invalid', SHA2('SyntheticOnly9x!', 256), 'Desconhecido', 'Ativo'),
    ('Cargo Nulo', 'null-role@example.invalid', SHA2('SyntheticOnly9x!', 256), NULL, 'Ativo'),
    ('Cargo Vazio', 'empty-role@example.invalid', SHA2('SyntheticOnly9x!', 256), '', 'Ativo'),
    ('Cargo Espacos', 'spaces-role@example.invalid', SHA2('SyntheticOnly9x!', 256), '   ', 'Ativo'),
    ('Cargo Acentuado', 'accented-role@example.invalid', SHA2('SyntheticOnly9x!', 256), 'Admín', 'Ativo'),
    ('Admin Espacado', 'trimmed-admin@example.invalid', SHA2('SyntheticOnly9x!', 256), ' ADMIN ', 'Ativo');

INSERT INTO security_sessoes_funcionarios (funcionario_id, token_hash, expira_em) VALUES
    (1, SHA2('SyntheticAdministratorToken1001', 256), UTC_TIMESTAMP() + INTERVAL 1 HOUR),
    (2, SHA2('SyntheticAdminToken1000000002', 256), UTC_TIMESTAMP() + INTERVAL 1 HOUR),
    (3, SHA2('SyntheticOperatorAllowed1003', 256), UTC_TIMESTAMP() + INTERVAL 1 HOUR),
    (4, SHA2('SyntheticOperatorMissing1004', 256), UTC_TIMESTAMP() + INTERVAL 1 HOUR),
    (5, SHA2('SyntheticOperatorDenied1005', 256), UTC_TIMESTAMP() + INTERVAL 1 HOUR),
    (6, SHA2('SyntheticAuditorToken100006', 256), UTC_TIMESTAMP() + INTERVAL 1 HOUR),
    (7, SHA2('SyntheticUnknownRoleToken1007', 256), UTC_TIMESTAMP() + INTERVAL 1 HOUR),
    (8, SHA2('SyntheticNullRoleToken100008', 256), UTC_TIMESTAMP() + INTERVAL 1 HOUR),
    (9, SHA2('SyntheticEmptyRoleToken10009', 256), UTC_TIMESTAMP() + INTERVAL 1 HOUR),
    (10, SHA2('SyntheticSpacesRoleToken1010', 256), UTC_TIMESTAMP() + INTERVAL 1 HOUR),
    (11, SHA2('SyntheticAccentedRoleToken11', 256), UTC_TIMESTAMP() + INTERVAL 1 HOUR),
    (12, SHA2('SyntheticTrimmedAdminToken12', 256), UTC_TIMESTAMP() + INTERVAL 1 HOUR);

INSERT INTO permissoes_funcionario_modulos (
    funcionario_id, modulo, acao, permitido
) VALUES
    (3, 'clientes', 'visualizar', 1),
    (3, 'clientes', 'criar', 1),
    (3, 'clientes', 'editar', 1),
    (5, 'clientes', 'visualizar', 0),
    (5, 'clientes', 'criar', 0),
    (5, 'clientes', 'editar', 0),
    (6, 'clientes', 'visualizar', 1),
    (6, 'clientes', 'criar', 0),
    (6, 'clientes', 'editar', 0);
