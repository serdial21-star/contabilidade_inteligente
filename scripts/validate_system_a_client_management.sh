#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ASSET_DIR="${ROOT_DIR}/docs/integration/system_a_client_management"
CONTAINER="serdial21-client-management-test-$$"
DB_NAME="serdial21_client_management_test"
DB_PASSWORD="$(openssl rand -hex 24)"

cleanup() {
  docker rm -f "${CONTAINER}" >/dev/null 2>&1 || true
}
trap cleanup EXIT

for required in docker openssl grep awk; do
  command -v "${required}" >/dev/null 2>&1 || {
    echo "MISSING_COMMAND=${required}"
    exit 1
  }
done

for required_file in \
  test_base_schema.sql 001_up.sql 002_up.sql 003_up.sql 003_down.sql \
  002_down.sql 001_down.sql verify.sql; do
  test -f "${ASSET_DIR}/${required_file}" || {
    echo "MISSING_FILE=${ASSET_DIR}/${required_file}"
    exit 1
  }
done

docker run --name "${CONTAINER}" \
  --env "MARIADB_ROOT_PASSWORD=${DB_PASSWORD}" \
  --detach mariadb:11.8.9 >/dev/null

for _ in $(seq 1 60); do
  if docker exec "${CONTAINER}" mariadb-admin \
      --user=root --password="${DB_PASSWORD}" ping \
      --silent >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

db() {
  docker exec "${CONTAINER}" mariadb \
    --batch --skip-column-names \
    --user=root --password="${DB_PASSWORD}" \
    "${DB_NAME}" --execute="$1"
}

apply_sql() {
  docker exec -i "${CONTAINER}" mariadb \
    --user=root --password="${DB_PASSWORD}" \
    "${DB_NAME}" < "${ASSET_DIR}/$1"
}

assert_contains() {
  local output="$1"
  local expected="$2"
  grep -q "${expected}" <<<"${output}" || {
    echo "ASSERT_CONTAINS_FAILED=${expected}"
    exit 1
  }
}

assert_scalar() {
  local query="$1"
  local expected="$2"
  local actual
  actual="$(db "${query}")"
  test "${actual}" = "${expected}" || {
    echo "ASSERT_SCALAR_FAILED expected=${expected} actual=${actual}"
    exit 1
  }
}

docker exec -i "${CONTAINER}" mariadb \
  --user=root --password="${DB_PASSWORD}" \
  < "${ASSET_DIR}/test_base_schema.sql"
apply_sql 001_up.sql
apply_sql 002_up.sql
apply_sql 003_up.sql

# Sessao invalida, expirada e revogada nunca produzem efeito.
result="$(db "CALL sp_admin_cliente_create('InvalidSyntheticToken0000','Nao Criado','invalid-session@example.invalid','', 'Lead', NULL);")"
assert_contains "${result}" $'0\tunauthorized'
assert_scalar "SELECT COUNT(*) FROM clientes_emails_autorizados WHERE email = 'invalid-session@example.invalid';" "0"
result="$(db "CALL sp_admin_cliente_list('InvalidSyntheticToken0000');")"
assert_contains "${result}" $'0\tunauthorized'
test "$(awk 'END { print NR }' <<<"${result}")" = "1"

db "UPDATE security_sessoes_funcionarios SET expira_em = UTC_TIMESTAMP() - INTERVAL 1 MINUTE WHERE funcionario_id = 3;" >/dev/null
result="$(db "CALL sp_admin_cliente_create('SyntheticOperatorAllowed1003','Nao Criado','expired-session@example.invalid','', 'Lead', NULL);")"
assert_contains "${result}" $'0\tunauthorized'
db "UPDATE security_sessoes_funcionarios SET expira_em = UTC_TIMESTAMP() + INTERVAL 1 HOUR, revogado_em = UTC_TIMESTAMP() WHERE funcionario_id = 3;" >/dev/null
result="$(db "CALL sp_admin_cliente_create('SyntheticOperatorAllowed1003','Nao Criado','revoked-session@example.invalid','', 'Lead', NULL);")"
assert_contains "${result}" $'0\tunauthorized'
db "UPDATE security_sessoes_funcionarios SET revogado_em = NULL WHERE funcionario_id = 3;" >/dev/null

# Sem linha, negacao explicita, cargo desconhecido e cargo nulo falham fechados.
result="$(db "CALL sp_admin_cliente_create('SyntheticOperatorMissing1004','Nao Criado','missing-permission@example.invalid','', 'Lead', NULL);")"
assert_contains "${result}" $'0\tforbidden'
assert_scalar "SELECT COUNT(*) FROM clientes_emails_autorizados WHERE email='missing-permission@example.invalid';" "0"
result="$(db "CALL sp_admin_cliente_create('SyntheticOperatorDenied1005','Nao Criado','denied-permission@example.invalid','', 'Lead', NULL);")"
assert_contains "${result}" $'0\tforbidden'
assert_scalar "SELECT COUNT(*) FROM clientes_emails_autorizados WHERE email='denied-permission@example.invalid';" "0"
result="$(db "CALL sp_admin_cliente_list('SyntheticOperatorMissing1004');")"
assert_contains "${result}" $'0\tforbidden'
test "$(awk 'END { print NR }' <<<"${result}")" = "1"
result="$(db "CALL sp_admin_cliente_list('SyntheticOperatorDenied1005');")"
assert_contains "${result}" $'0\tforbidden'
test "$(awk 'END { print NR }' <<<"${result}")" = "1"
result="$(db "CALL sp_admin_cliente_list('SyntheticUnknownRoleToken1007');")"
assert_contains "${result}" $'0\tforbidden'
test "$(awk 'END { print NR }' <<<"${result}")" = "1"
result="$(db "CALL sp_admin_cliente_list('SyntheticNullRoleToken100008');")"
assert_contains "${result}" $'0\tforbidden'
test "$(awk 'END { print NR }' <<<"${result}")" = "1"
result="$(db "CALL sp_admin_cliente_list('SyntheticEmptyRoleToken10009');")"
assert_contains "${result}" $'0\tforbidden'
test "$(awk 'END { print NR }' <<<"${result}")" = "1"
result="$(db "CALL sp_admin_cliente_list('SyntheticSpacesRoleToken1010');")"
assert_contains "${result}" $'0\tforbidden'
test "$(awk 'END { print NR }' <<<"${result}")" = "1"
result="$(db "CALL sp_admin_cliente_list('SyntheticAccentedRoleToken11');")"
assert_contains "${result}" $'0\tforbidden'
test "$(awk 'END { print NR }' <<<"${result}")" = "1"
assert_contains "$(db "CALL sp_admin_cliente_list('SyntheticTrimmedAdminToken12');")" $'1\tlisted'
assert_scalar "SELECT COUNT(*) >= 9 FROM logs_auditoria WHERE acao = 'client_action_forbidden';" "1"
assert_scalar "SELECT COUNT(*) FROM logs_auditoria WHERE acao = 'client_action_forbidden' AND registro_id IS NOT NULL;" "0"

# Os dois cargos administrativos ignoram a matriz; visualizar explicito tambem funciona.
assert_contains "$(db "CALL sp_admin_cliente_list('SyntheticAdministratorToken1001');")" $'1\tlisted'
assert_contains "$(db "CALL sp_admin_cliente_list('SyntheticAdminToken1000000002');")" $'1\tlisted'
assert_contains "$(db "CALL sp_admin_cliente_list('SyntheticOperatorAllowed1003');")" $'1\tlisted'
assert_contains "$(db "CALL sp_admin_cliente_list('SyntheticAuditorToken100006');")" $'1\tlisted'

# Admin tambem cria sem linha de permissao; o reset do portal continua funcional.
result="$(db "CALL sp_admin_cliente_create('SyntheticAdminToken1000000002','Cliente Reset','portal-reset@example.invalid','39053344705','Ativo',NULL);")"
assert_contains "${result}" $'1\tcreated'
reset_token="$(awk -F '\t' 'NR == 1 { print $6 }' <<<"${result}")"
test "${#reset_token}" -eq 64
result="$(db "CALL sp_cliente_password_reset_apply('${reset_token}','SyntheticClient9x!');")"
assert_contains "${result}" $'1\tsuccess'
result="$(db "CALL sp_cliente_password_reset_apply('${reset_token}','SyntheticClient9x!');")"
assert_contains "${result}" $'0\tinvalid_or_expired'

# Operador com permissao cria e edita campos comuns.
result="$(db "CALL sp_admin_cliente_create('SyntheticOperatorAllowed1003','Cliente Operador','z-primary@example.invalid','', 'Lead', '11999999999');")"
assert_contains "${result}" $'1\tcreated'
operator_client_id="$(awk -F '\t' 'NR == 1 { print $3 }' <<<"${result}")"
db "INSERT INTO clientes_emails_autorizados (cliente_id,email) VALUES (${operator_client_id},'a-secondary@example.invalid');" >/dev/null
result="$(db "CALL sp_admin_cliente_list('SyntheticOperatorAllowed1003');")"
listed_email="$(awk -F '\t' -v id="${operator_client_id}" '$5 == id { print $12 }' <<<"${result}")"
test "${listed_email}" = "z-primary@example.invalid"
result="$(db "CALL sp_admin_cliente_update('SyntheticOperatorAllowed1003',${operator_client_id},'Cliente Operador Atualizado','${listed_email}','', 'Lead','11999999999','1133334444');")"
assert_contains "${result}" $'1\tupdated'
assert_scalar "SELECT nome_cliente FROM clientes WHERE id = ${operator_client_id};" "Cliente Operador Atualizado"

# Unauthorized e as duas formas de negacao de editar nao alteram o cliente.
result="$(db "CALL sp_admin_cliente_update('InvalidSyntheticToken0000',${operator_client_id},'Alteracao Indevida','z-primary@example.invalid','', 'Lead','11999999999','1133334444');")"
assert_contains "${result}" $'0\tunauthorized'
assert_scalar "SELECT nome_cliente FROM clientes WHERE id=${operator_client_id};" "Cliente Operador Atualizado"
result="$(db "CALL sp_admin_cliente_update('SyntheticOperatorMissing1004',${operator_client_id},'Alteracao Indevida','z-primary@example.invalid','', 'Lead','11999999999','1133334444');")"
assert_contains "${result}" $'0\tforbidden'
assert_scalar "SELECT nome_cliente FROM clientes WHERE id=${operator_client_id};" "Cliente Operador Atualizado"
result="$(db "CALL sp_admin_cliente_update('SyntheticOperatorDenied1005',${operator_client_id},'Alteracao Indevida','z-primary@example.invalid','', 'Lead','11999999999','1133334444');")"
assert_contains "${result}" $'0\tforbidden'
assert_scalar "SELECT nome_cliente FROM clientes WHERE id=${operator_client_id};" "Cliente Operador Atualizado"

# D3: quem pode editar preenche o primeiro documento de um Lead, mas nao o substitui.
result="$(db "CALL sp_admin_cliente_update('SyntheticOperatorAllowed1003',${operator_client_id},'Cliente Operador Atualizado','z-primary@example.invalid','12345678909', 'Lead','11999999999','1133334444');")"
assert_contains "${result}" $'1\tupdated'
assert_scalar "SELECT documento_fiscal_canonico FROM clientes WHERE id=${operator_client_id};" "12345678909"
assert_scalar "SELECT COUNT(*) FROM logs_auditoria WHERE registro_id=${operator_client_id} AND funcionario_id=1003 AND acao='document_changed' AND JSON_UNQUOTE(JSON_EXTRACT(detalhes,'$.request_id')) IS NOT NULL AND JSON_LENGTH(detalhes)=1;" "1"
result="$(db "CALL sp_admin_cliente_update('SyntheticOperatorAllowed1003',${operator_client_id},'Cliente Operador Atualizado','z-primary@example.invalid','22233344405', 'Lead','11999999999','1133334444');")"
assert_contains "${result}" $'0\tforbidden'
assert_scalar "SELECT documento_fiscal_canonico FROM clientes WHERE id=${operator_client_id};" "12345678909"

# D3 nao abre excecao para e-mail: ate o primeiro e-mail exige cargo administrativo.
email_empty_client_id="$(db "INSERT INTO clientes (nome_cliente,status) VALUES ('Lead Sem Email','Lead'); SELECT LAST_INSERT_ID();")"
result="$(db "CALL sp_admin_cliente_update('SyntheticOperatorAllowed1003',${email_empty_client_id},'Lead Sem Email','first-email@example.invalid','', 'Lead',NULL,NULL);")"
assert_contains "${result}" $'0\tforbidden'
assert_scalar "SELECT COUNT(*) FROM clientes_emails_autorizados WHERE cliente_id=${email_empty_client_id};" "0"

# Vincular pasta exige a mesma permissao de criar.
result="$(db "CALL sp_admin_cliente_set_folder('SyntheticOperatorMissing1004',${operator_client_id},'synthetic-folder-id');")"
assert_contains "${result}" $'0\tforbidden'
assert_scalar "SELECT COUNT(*) FROM clientes WHERE id=${operator_client_id} AND id_pasta_raiz IS NULL;" "1"

# Auditor sem editar recebe forbidden; nenhum efeito e registrado no cliente.
result="$(db "CALL sp_admin_cliente_update('SyntheticAuditorToken100006',${operator_client_id},'Alteracao Indevida','z-primary@example.invalid','', 'Lead','11999999999','1133334444');")"
assert_contains "${result}" $'0\tforbidden'
assert_scalar "SELECT nome_cliente FROM clientes WHERE id = ${operator_client_id};" "Cliente Operador Atualizado"

# Cliente ativo administrativo fornece alvo para os testes sensiveis.
result="$(db "CALL sp_admin_cliente_create('SyntheticAdministratorToken1001','Cliente Sensivel','sensitive-old@example.invalid','52998224725','Ativo','11988887777');")"
assert_contains "${result}" $'1\tcreated'
sensitive_client_id="$(awk -F '\t' 'NR == 1 { print $3 }' <<<"${result}")"
db "INSERT INTO security_sessoes_clientes (cliente_id,email,token_hash,expira_em) VALUES (${sensitive_client_id},'sensitive-old@example.invalid',SHA2('SyntheticClientSession',256),UTC_TIMESTAMP()+INTERVAL 1 HOUR);" >/dev/null

# D2: operador com editar nao pode trocar e-mail nem documento.
result="$(db "CALL sp_admin_cliente_update('SyntheticOperatorAllowed1003',${sensitive_client_id},'Cliente Sensivel','blocked-email@example.invalid','52998224725','Ativo','11988887777',NULL);")"
assert_contains "${result}" $'0\tforbidden'
assert_scalar "SELECT COUNT(*) FROM clientes_emails_autorizados WHERE cliente_id=${sensitive_client_id} AND email='sensitive-old@example.invalid';" "1"
result="$(db "CALL sp_admin_cliente_update('SyntheticOperatorAllowed1003',${sensitive_client_id},'Cliente Sensivel','sensitive-old@example.invalid','11144477735','Ativo','11988887777',NULL);")"
assert_contains "${result}" $'0\tforbidden'
assert_scalar "SELECT documento_fiscal_canonico FROM clientes WHERE id=${sensitive_client_id};" "52998224725"

# Administrador troca e-mail: sessoes e links sao revogados na mesma operacao.
result="$(db "CALL sp_admin_cliente_update('SyntheticAdministratorToken1001',${sensitive_client_id},'Cliente Sensivel','sensitive-new@example.invalid','52998224725','Ativo','11988887777',NULL);")"
assert_contains "${result}" $'1\tupdated'
assert_scalar "SELECT COUNT(*) FROM security_sessoes_clientes WHERE cliente_id=${sensitive_client_id} AND revogado_em IS NULL;" "0"
assert_scalar "SELECT COUNT(*) FROM security_password_reset_clientes WHERE cliente_id=${sensitive_client_id} AND resultado_solicitacao='issued' AND utilizado_em IS NULL AND revogado_em IS NULL;" "0"
assert_scalar "SELECT COUNT(*) FROM logs_auditoria WHERE registro_id=${sensitive_client_id} AND funcionario_id=1001 AND acao='email_changed' AND JSON_UNQUOTE(JSON_EXTRACT(detalhes,'$.request_id')) IS NOT NULL AND JSON_LENGTH(detalhes)=1;" "1"

# Admin (sinonimo) troca documento; a auditoria registra somente a ocorrencia.
result="$(db "CALL sp_admin_cliente_update('SyntheticAdminToken1000000002',${sensitive_client_id},'Cliente Sensivel','sensitive-new@example.invalid','11144477735','Ativo','11988887777',NULL);")"
assert_contains "${result}" $'1\tupdated'
assert_scalar "SELECT COUNT(*) FROM logs_auditoria WHERE registro_id=${sensitive_client_id} AND funcionario_id=1000000002 AND acao='document_changed' AND JSON_UNQUOTE(JSON_EXTRACT(detalhes,'$.request_id')) IS NOT NULL AND JSON_LENGTH(detalhes)=1;" "1"
assert_scalar "SELECT COUNT(*) FROM logs_auditoria WHERE acao IN ('email_changed','document_changed') AND (JSON_EXTRACT(detalhes,'$.previous_hash') IS NOT NULL OR JSON_EXTRACT(detalhes,'$.new_hash') IS NOT NULL);" "0"
assert_scalar "SELECT COUNT(*) FROM logs_auditoria WHERE acao IN ('email_changed','document_changed') AND (detalhes LIKE '%sensitive-old@example.invalid%' OR detalhes LIKE '%sensitive-new@example.invalid%' OR detalhes LIKE '%52998224725%' OR detalhes LIKE '%11144477735%');" "0"
assert_scalar "SELECT COUNT(*) FROM logs_auditoria WHERE acao='client_action_forbidden';" "17"
assert_scalar "SELECT COUNT(*) FROM logs_auditoria WHERE acao='client_action_forbidden' AND registro_id IS NOT NULL;" "0"

# O downgrade remove a fronteira nova e restaura create/update de 002.
apply_sql 003_down.sql
assert_scalar "SELECT COUNT(*) FROM information_schema.ROUTINES WHERE ROUTINE_SCHEMA=DATABASE() AND ROUTINE_NAME IN ('sp_admin_client_authorize','sp_admin_cliente_list');" "0"
result="$(db "CALL sp_admin_cliente_create('SyntheticOperatorMissing1004','Cliente Pos Rollback','rollback-client@example.invalid','', 'Lead', NULL);")"
assert_contains "${result}" $'1\tcreated'
result="$(db "CALL sp_admin_cliente_update('SyntheticOperatorAllowed1003',${sensitive_client_id},'Cliente Pos Rollback','rollback-email@example.invalid','11144477735','Ativo','11988887777',NULL);")"
assert_contains "${result}" $'1\tupdated'

apply_sql 002_down.sql
apply_sql 001_down.sql

echo "CLIENT_MANAGEMENT_MIGRATION_003=VALID"
echo "CLIENT_MANAGEMENT_AUTHORIZATION_TESTS=PASS"
echo "CLIENT_MANAGEMENT_AUDIT_TESTS=PASS"
echo "CLIENT_MANAGEMENT_ROLLBACK=PASS"
