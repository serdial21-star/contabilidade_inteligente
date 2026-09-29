-- Estrutura mínima anonimizada para validar a migration em MariaDB isolado.
-- Não contém dados nem credenciais reais.

CREATE DATABASE IF NOT EXISTS serdial21_recovery_test
    CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE serdial21_recovery_test;

CREATE TABLE funcionarios (
    id INT(11) NOT NULL AUTO_INCREMENT,
    nome_funcionario VARCHAR(150) NOT NULL,
    email VARCHAR(100) NOT NULL,
    senha VARCHAR(64) NOT NULL,
    cargo VARCHAR(50) NULL DEFAULT 'Operador',
    telefone VARCHAR(20) NULL,
    status ENUM('Ativo', 'Inativo') NULL DEFAULT 'Ativo',
    ultimo_acesso DATETIME NULL,
    criado_em TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP(),
    atualizado_em TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP() ON UPDATE CURRENT_TIMESTAMP(),
    endereco TEXT NULL,
    matricula VARCHAR(50) NULL,
    data_admissao DATE NULL,
    data_demissao DATE NULL,
    contato_emergencia VARCHAR(100) NULL,
    observacao TEXT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY email (email)
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
    PRIMARY KEY (id),
    KEY funcionario_id (funcionario_id),
    CONSTRAINT logs_auditoria_ibfk_1
        FOREIGN KEY (funcionario_id) REFERENCES funcionarios (id)
        ON UPDATE RESTRICT ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE log_tentativas_login (
    id INT(11) NOT NULL AUTO_INCREMENT,
    email VARCHAR(100) NOT NULL,
    criado_em TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP(),
    PRIMARY KEY (id),
    KEY idx_tentativas_email (email)
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

INSERT INTO funcionarios (
    nome_funcionario,
    email,
    senha,
    cargo,
    status
) VALUES (
    'Usuario Sintetico',
    'synthetic@example.invalid',
    SHA2('OldSyntheticPassword123', 256),
    'Administrador',
    'Ativo'
);

INSERT INTO security_sessoes_funcionarios (
    funcionario_id,
    token_hash,
    expira_em
) VALUES (
    1,
    SHA2('synthetic-session-token', 256),
    UTC_TIMESTAMP() + INTERVAL 12 HOUR
);
