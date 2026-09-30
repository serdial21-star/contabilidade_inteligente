-- Somente leitura. Nao altera dados nem schema.
-- Execute no banco operacional do Sistema A antes de 001_up.sql.

USE u621451815_serdial21;

SELECT
    VERSION() AS database_version,
    @@session.time_zone AS session_time_zone,
    @@system_time_zone AS system_time_zone,
    LENGTH(RANDOM_BYTES(32)) AS random_bytes_length,
    UTC_TIMESTAMP() AS checked_at_utc;

SELECT
    COUNT(*) AS documentos_duplicados
FROM (
    SELECT 1
    FROM clientes
    WHERE COALESCE(
        NULLIF(TRIM(cnpj), ''),
        NULLIF(TRIM(cnpj_cpf), '')
    ) IS NOT NULL
    GROUP BY UPPER(
        REPLACE(REPLACE(REPLACE(REPLACE(
            COALESCE(
                NULLIF(TRIM(cnpj), ''),
                NULLIF(TRIM(cnpj_cpf), '')
            ),
            '.', ''), '/', ''), '-', ''), ' ', '')
    )
    HAVING COUNT(*) > 1
) AS grupos_duplicados;

SELECT
    COUNT(*) AS documentos_com_caractere_nao_suportado
FROM clientes
WHERE COALESCE(
        NULLIF(TRIM(cnpj), ''),
        NULLIF(TRIM(cnpj_cpf), '')
      ) IS NOT NULL
  AND UPPER(
        COALESCE(
            NULLIF(TRIM(cnpj), ''),
            NULLIF(TRIM(cnpj_cpf), '')
        )
      ) NOT REGEXP '^[0-9A-Z./ -]+$';

SELECT
    COUNT(*) AS documentos_com_formato_incompativel
FROM clientes
WHERE COALESCE(
        NULLIF(TRIM(cnpj), ''),
        NULLIF(TRIM(cnpj_cpf), '')
      ) IS NOT NULL
  AND UPPER(
        REPLACE(REPLACE(REPLACE(REPLACE(
            COALESCE(
                NULLIF(TRIM(cnpj), ''),
                NULLIF(TRIM(cnpj_cpf), '')
            ),
            '.', ''), '/', ''), '-', ''), ' ', '')
      ) NOT REGEXP '(^[0-9]{11}$)|(^[0-9A-Z]{12}[0-9]{2}$)';

SELECT
    COUNT(*) AS emails_normalizados_duplicados
FROM (
    SELECT 1
    FROM clientes_emails_autorizados
    WHERE TRIM(email) <> ''
    GROUP BY LOWER(TRIM(email))
    HAVING COUNT(*) > 1
) AS grupos_duplicados;

SELECT
    TABLE_NAME,
    ENGINE,
    TABLE_COLLATION
FROM information_schema.TABLES
WHERE TABLE_SCHEMA = DATABASE()
  AND TABLE_NAME IN (
      'clientes',
      'clientes_emails_autorizados',
      'funcionarios',
      'security_sessoes_funcionarios',
      'logs_auditoria',
      'security_sessoes_clientes',
      'security_password_reset_clientes'
  )
ORDER BY TABLE_NAME;
