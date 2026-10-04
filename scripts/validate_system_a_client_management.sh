#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ASSET_DIR="${ROOT_DIR}/docs/integration/system_a_client_management"
LOGOUT_DIR="${ROOT_DIR}/docs/integration/system_a_session_logout"
HARDENING_DIR="${ROOT_DIR}/docs/integration/system_a_webhook_hardening"
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

for required_file in 004_up.sql 004_down.sql; do
  test -f "${LOGOUT_DIR}/${required_file}" || {
    echo "MISSING_FILE=${LOGOUT_DIR}/${required_file}"
    exit 1
  }
done

for required_file in 005_up.sql 005_down.sql verify_005.sql; do
  test -f "${HARDENING_DIR}/${required_file}" || {
    echo "MISSING_FILE=${HARDENING_DIR}/${required_file}"
    exit 1
  }
done

docker run --name "${CONTAINER}" \
  --env "MARIADB_ROOT_PASSWORD=${DB_PASSWORD}" \
  --detach mariadb:11.8.9 >/dev/null

DB_READY=false
for _ in $(seq 1 60); do
  if docker exec "${CONTAINER}" mariadb \
      --protocol=tcp --host=127.0.0.1 \
      --user=root --password="${DB_PASSWORD}" \
      --execute='SELECT 1' >/dev/null 2>&1; then
    DB_READY=true
    break
  fi
  sleep 1
done

if [[ "${DB_READY}" != true ]]; then
  echo "MARIADB_READY_TIMEOUT container=${CONTAINER}" >&2
  docker logs --tail 50 "${CONTAINER}" >&2 || true
  exit 1
fi

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

apply_logout_sql() {
  docker exec -i "${CONTAINER}" mariadb \
    --user=root --password="${DB_PASSWORD}" \
    "${DB_NAME}" < "${LOGOUT_DIR}/$1"
}

apply_hardening_sql() {
  docker exec -i "${CONTAINER}" mariadb \
    --user=root --password="${DB_PASSWORD}" \
    "${DB_NAME}" < "${HARDENING_DIR}/$1"
}

assert_contains() {
  local output="$1"
  local expected="$2"
  local label="$3"
  grep -q "${expected}" <<<"${output}" || {
    echo "ASSERT_CONTAINS_FAILED label=${label} expected=${expected} actual=${output}"
    exit 1
  }
}

assert_scalar() {
  local query="$1"
  local expected="$2"
  local actual
  actual="$(db "${query}")"
  test "${actual}" = "${expected}" || {
    echo "ASSERT_SCALAR_FAILED query=${query} expected=${expected} actual=${actual}"
    exit 1
  }
}

docker exec -i "${CONTAINER}" mariadb \
  --user=root --password="${DB_PASSWORD}" \
  < "${ASSET_DIR}/test_base_schema.sql"
apply_sql 001_up.sql
apply_sql 002_up.sql
apply_sql 003_up.sql
apply_hardening_sql 005_up.sql

administrator_id="$(db "SELECT id FROM funcionarios WHERE email='administrator@example.invalid';")"
admin_id="$(db "SELECT id FROM funcionarios WHERE email='admin@example.invalid';")"
operator_allowed_id="$(db "SELECT id FROM funcionarios WHERE email='operator-allowed@example.invalid';")"

# T-0006: autorizacao generica de modulo/acao falha fechada e audita somente
# funcionario autenticado sem permissao. Nenhum token ou hash entra no evento.
db "INSERT INTO permissoes_funcionario_modulos (funcionario_id, modulo, acao, permitido) VALUES
  (${operator_allowed_id}, 'ferramentas_ia', 'criar', 1),
  ((SELECT id FROM funcionarios WHERE email='operator-denied@example.invalid'), 'ferramentas_ia', 'criar', 0);" >/dev/null
db "INSERT INTO funcionarios (nome_funcionario,email,senha,cargo,status) VALUES
  ('Inativo Ferramentas','inactive-tools@example.invalid',SHA2('SyntheticOnly9x!',256),'Operador','Inativo');" >/dev/null
inactive_tools_id="$(db "SELECT id FROM funcionarios WHERE email='inactive-tools@example.invalid';")"
db "INSERT INTO security_sessoes_funcionarios (funcionario_id,token_hash,expira_em) VALUES
  (${inactive_tools_id},SHA2('SyntheticInactiveToolsToken01',256),UTC_TIMESTAMP()+INTERVAL 1 HOUR);" >/dev/null

assert_contains "$(db "CALL sp_admin_module_authorize('SyntheticAdministratorToken1001','ferramentas_ia','criar');")" $'1\tauthorized\t' "Administrator bypasses matrix"
assert_contains "$(db "CALL sp_admin_module_authorize('SyntheticAdminToken1000000002','ferramentas_ia','criar');")" $'1\tauthorized\t' "Admin bypasses matrix"
assert_contains "$(db "CALL sp_admin_module_authorize('SyntheticTrimmedAdminToken12','ferramentas_ia','criar');")" $'1\tauthorized\t' "trimmed Admin bypasses matrix"
assert_contains "$(db "CALL sp_admin_module_authorize('SyntheticOperatorAllowed1003','ferramentas_ia','criar');")" $'1\tauthorized\t' "explicit module permission authorizes"

for token in \
  SyntheticOperatorMissing1004 \
  SyntheticOperatorDenied1005 \
  SyntheticUnknownRoleToken1007 \
  SyntheticNullRoleToken100008 \
  SyntheticEmptyRoleToken10009 \
  SyntheticSpacesRoleToken1010 \
  SyntheticAccentedRoleToken11; do
  assert_contains "$(db "CALL sp_admin_module_authorize('${token}','ferramentas_ia','criar');")" $'0\tforbidden\t' "module authorization fails closed"
done

assert_contains "$(db "CALL sp_admin_module_authorize('bad token!','ferramentas_ia','criar');")" $'0\tunauthorized' "malformed module token"
assert_contains "$(db "CALL sp_admin_module_authorize('SyntheticUnknownModuleToken99','ferramentas_ia','criar');")" $'0\tunauthorized' "unknown module session"
assert_contains "$(db "CALL sp_admin_module_authorize('SyntheticInactiveToolsToken01','ferramentas_ia','criar');")" $'0\tunauthorized' "inactive employee session"

db "UPDATE security_sessoes_funcionarios SET expira_em=UTC_TIMESTAMP()-INTERVAL 1 MINUTE WHERE funcionario_id=${operator_allowed_id};" >/dev/null
assert_contains "$(db "CALL sp_admin_module_authorize('SyntheticOperatorAllowed1003','ferramentas_ia','criar');")" $'0\tunauthorized' "expired module session"
db "UPDATE security_sessoes_funcionarios SET expira_em=UTC_TIMESTAMP()+INTERVAL 1 HOUR,revogado_em=UTC_TIMESTAMP() WHERE funcionario_id=${operator_allowed_id};" >/dev/null
assert_contains "$(db "CALL sp_admin_module_authorize('SyntheticOperatorAllowed1003','ferramentas_ia','criar');")" $'0\tunauthorized' "revoked module session"
db "UPDATE security_sessoes_funcionarios SET revogado_em=NULL WHERE funcionario_id=${operator_allowed_id};" >/dev/null

assert_scalar "SELECT COUNT(*) FROM logs_auditoria WHERE acao='employee_module_action_forbidden';" "7"
assert_scalar "SELECT COUNT(*) FROM logs_auditoria WHERE acao='employee_module_action_forbidden' AND (detalhes LIKE '%Synthetic%' OR detalhes REGEXP '[0-9a-f]{64}');" "0"
assert_scalar "SELECT COUNT(*) FROM logs_auditoria WHERE acao='employee_module_action_forbidden' AND JSON_LENGTH(detalhes)=3 AND JSON_UNQUOTE(JSON_EXTRACT(detalhes,'$.module'))='ferramentas_ia' AND JSON_UNQUOTE(JSON_EXTRACT(detalhes,'$.action'))='criar' AND JSON_UNQUOTE(JSON_EXTRACT(detalhes,'$.request_id')) IS NOT NULL;" "7"

# Sessao invalida, expirada e revogada nunca produzem efeito.
result="$(db "CALL sp_admin_cliente_create('InvalidSyntheticToken0000','Nao Criado','invalid-session@example.invalid','', 'Lead', NULL);")"
assert_contains "${result}" $'0\tunauthorized' "invalid session cannot create"
assert_scalar "SELECT COUNT(*) FROM clientes_emails_autorizados WHERE email = 'invalid-session@example.invalid';" "0"
result="$(db "CALL sp_admin_cliente_list('InvalidSyntheticToken0000');")"
assert_contains "${result}" $'0\tunauthorized' "invalid session cannot list"
test "$(awk 'END { print NR }' <<<"${result}")" = "1"

db "UPDATE security_sessoes_funcionarios SET expira_em = UTC_TIMESTAMP() - INTERVAL 1 MINUTE WHERE funcionario_id = ${operator_allowed_id};" >/dev/null
result="$(db "CALL sp_admin_cliente_create('SyntheticOperatorAllowed1003','Nao Criado','expired-session@example.invalid','', 'Lead', NULL);")"
assert_contains "${result}" $'0\tunauthorized' "expired session cannot create"
db "UPDATE security_sessoes_funcionarios SET expira_em = UTC_TIMESTAMP() + INTERVAL 1 HOUR, revogado_em = UTC_TIMESTAMP() WHERE funcionario_id = ${operator_allowed_id};" >/dev/null
result="$(db "CALL sp_admin_cliente_create('SyntheticOperatorAllowed1003','Nao Criado','revoked-session@example.invalid','', 'Lead', NULL);")"
assert_contains "${result}" $'0\tunauthorized' "revoked session cannot create"
db "UPDATE security_sessoes_funcionarios SET revogado_em = NULL WHERE funcionario_id = ${operator_allowed_id};" >/dev/null

# Sem linha, negacao explicita, cargo desconhecido e cargo nulo falham fechados.
result="$(db "CALL sp_admin_cliente_create('SyntheticOperatorMissing1004','Nao Criado','missing-permission@example.invalid','', 'Lead', NULL);")"
assert_contains "${result}" $'0\tforbidden' "missing create permission"
assert_scalar "SELECT COUNT(*) FROM clientes_emails_autorizados WHERE email='missing-permission@example.invalid';" "0"
result="$(db "CALL sp_admin_cliente_create('SyntheticOperatorDenied1005','Nao Criado','denied-permission@example.invalid','', 'Lead', NULL);")"
assert_contains "${result}" $'0\tforbidden' "explicitly denied create permission"
assert_scalar "SELECT COUNT(*) FROM clientes_emails_autorizados WHERE email='denied-permission@example.invalid';" "0"
result="$(db "CALL sp_admin_cliente_list('SyntheticOperatorMissing1004');")"
assert_contains "${result}" $'0\tforbidden' "missing list permission"
test "$(awk 'END { print NR }' <<<"${result}")" = "1"
result="$(db "CALL sp_admin_cliente_list('SyntheticOperatorDenied1005');")"
assert_contains "${result}" $'0\tforbidden' "explicitly denied list permission"
test "$(awk 'END { print NR }' <<<"${result}")" = "1"
result="$(db "CALL sp_admin_cliente_list('SyntheticUnknownRoleToken1007');")"
assert_contains "${result}" $'0\tforbidden' "unknown role cannot list"
test "$(awk 'END { print NR }' <<<"${result}")" = "1"
result="$(db "CALL sp_admin_cliente_list('SyntheticNullRoleToken100008');")"
assert_contains "${result}" $'0\tforbidden' "null role cannot list"
test "$(awk 'END { print NR }' <<<"${result}")" = "1"
result="$(db "CALL sp_admin_cliente_list('SyntheticEmptyRoleToken10009');")"
assert_contains "${result}" $'0\tforbidden' "empty role cannot list"
test "$(awk 'END { print NR }' <<<"${result}")" = "1"
result="$(db "CALL sp_admin_cliente_list('SyntheticSpacesRoleToken1010');")"
assert_contains "${result}" $'0\tforbidden' "spaces-only role cannot list"
test "$(awk 'END { print NR }' <<<"${result}")" = "1"
result="$(db "CALL sp_admin_cliente_list('SyntheticAccentedRoleToken11');")"
assert_contains "${result}" $'0\tforbidden' "accented admin variant cannot list"
test "$(awk 'END { print NR }' <<<"${result}")" = "1"
assert_contains "$(db "CALL sp_admin_cliente_list('SyntheticTrimmedAdminToken12');")" $'1\tlisted' "trimmed Admin role can list"
assert_scalar "SELECT COUNT(*) >= 9 FROM logs_auditoria WHERE acao = 'client_action_forbidden';" "1"
assert_scalar "SELECT COUNT(*) FROM logs_auditoria WHERE acao = 'client_action_forbidden' AND registro_id IS NOT NULL;" "0"

# Os dois cargos administrativos ignoram a matriz; visualizar explicito tambem funciona.
assert_contains "$(db "CALL sp_admin_cliente_list('SyntheticAdministratorToken1001');")" $'1\tlisted' "Administrador can list"
assert_contains "$(db "CALL sp_admin_cliente_list('SyntheticAdminToken1000000002');")" $'1\tlisted' "Admin can list"
assert_contains "$(db "CALL sp_admin_cliente_list('SyntheticOperatorAllowed1003');")" $'1\tlisted' "permitted operator can list"
assert_contains "$(db "CALL sp_admin_cliente_list('SyntheticAuditorToken100006');")" $'1\tlisted' "permitted auditor can list"

# Admin tambem cria sem linha de permissao; o reset do portal continua funcional.
result="$(db "CALL sp_admin_cliente_create('SyntheticAdminToken1000000002','Cliente Reset','portal-reset@example.invalid','39053344705','Ativo',NULL);")"
assert_contains "${result}" $'1\tcreated' "Admin can create without permission row"
reset_token="$(awk -F '\t' 'NR == 1 { print $6 }' <<<"${result}")"
test "${#reset_token}" -eq 64
result="$(db "CALL sp_cliente_password_reset_apply('${reset_token}','SyntheticClient9x!');")"
assert_contains "${result}" $'1\tsuccess' "password reset succeeds once"
result="$(db "CALL sp_cliente_password_reset_apply('${reset_token}','SyntheticClient9x!');")"
assert_contains "${result}" $'0\tinvalid_or_expired' "password reset token cannot be reused"

# Operador com permissao cria e edita campos comuns.
result="$(db "CALL sp_admin_cliente_create('SyntheticOperatorAllowed1003','Cliente Operador','z-primary@example.invalid','', 'Lead', '11999999999');")"
assert_contains "${result}" $'1\tcreated' "permitted operator can create"
operator_client_id="$(awk -F '\t' 'NR == 1 { print $3 }' <<<"${result}")"
db "INSERT INTO clientes_emails_autorizados (cliente_id,email) VALUES (${operator_client_id},'a-secondary@example.invalid');" >/dev/null
result="$(db "CALL sp_admin_cliente_list('SyntheticOperatorAllowed1003');")"
listed_email="$(awk -F '\t' -v id="${operator_client_id}" '$5 == id { print $12 }' <<<"${result}")"
test "${listed_email}" = "z-primary@example.invalid"
result="$(db "CALL sp_admin_cliente_update('SyntheticOperatorAllowed1003',${operator_client_id},'Cliente Operador Atualizado','${listed_email}','', 'Lead','11999999999','1133334444');")"
assert_contains "${result}" $'1\tupdated' "operator updates common fields"
assert_scalar "SELECT nome_cliente FROM clientes WHERE id = ${operator_client_id};" "Cliente Operador Atualizado"

# Unauthorized e as duas formas de negacao de editar nao alteram o cliente.
result="$(db "CALL sp_admin_cliente_update('InvalidSyntheticToken0000',${operator_client_id},'Alteracao Indevida','z-primary@example.invalid','', 'Lead','11999999999','1133334444');")"
assert_contains "${result}" $'0\tunauthorized' "invalid session cannot update"
assert_scalar "SELECT nome_cliente FROM clientes WHERE id=${operator_client_id};" "Cliente Operador Atualizado"
result="$(db "CALL sp_admin_cliente_update('SyntheticOperatorMissing1004',${operator_client_id},'Alteracao Indevida','z-primary@example.invalid','', 'Lead','11999999999','1133334444');")"
assert_contains "${result}" $'0\tforbidden' "missing edit permission"
assert_scalar "SELECT nome_cliente FROM clientes WHERE id=${operator_client_id};" "Cliente Operador Atualizado"
result="$(db "CALL sp_admin_cliente_update('SyntheticOperatorDenied1005',${operator_client_id},'Alteracao Indevida','z-primary@example.invalid','', 'Lead','11999999999','1133334444');")"
assert_contains "${result}" $'0\tforbidden' "explicitly denied edit permission"
assert_scalar "SELECT nome_cliente FROM clientes WHERE id=${operator_client_id};" "Cliente Operador Atualizado"

# D3: quem pode editar preenche o primeiro documento de um Lead, mas nao o substitui.
result="$(db "CALL sp_admin_cliente_update('SyntheticOperatorAllowed1003',${operator_client_id},'Cliente Operador Atualizado','z-primary@example.invalid','12345678909', 'Lead','11999999999','1133334444');")"
assert_contains "${result}" $'1\tupdated' "operator fills first Lead document"
assert_scalar "SELECT documento_fiscal_canonico FROM clientes WHERE id=${operator_client_id};" "12345678909"
assert_scalar "SELECT COUNT(*) FROM logs_auditoria WHERE registro_id=${operator_client_id} AND funcionario_id=${operator_allowed_id} AND acao='document_changed' AND JSON_UNQUOTE(JSON_EXTRACT(detalhes,'$.request_id')) IS NOT NULL AND JSON_LENGTH(detalhes)=1;" "1"
result="$(db "CALL sp_admin_cliente_update('SyntheticOperatorAllowed1003',${operator_client_id},'Cliente Operador Atualizado','z-primary@example.invalid','22233344405', 'Lead','11999999999','1133334444');")"
assert_contains "${result}" $'0\tforbidden' "operator cannot replace existing document"
assert_scalar "SELECT documento_fiscal_canonico FROM clientes WHERE id=${operator_client_id};" "12345678909"

# D3 nao abre excecao para e-mail: ate o primeiro e-mail exige cargo administrativo.
email_empty_client_id="$(db "INSERT INTO clientes (nome_cliente,status) VALUES ('Lead Sem Email','Lead'); SELECT LAST_INSERT_ID();")"
result="$(db "CALL sp_admin_cliente_update('SyntheticOperatorAllowed1003',${email_empty_client_id},'Lead Sem Email','first-email@example.invalid','', 'Lead',NULL,NULL);")"
assert_contains "${result}" $'0\tforbidden' "operator cannot set first email"
assert_scalar "SELECT COUNT(*) FROM clientes_emails_autorizados WHERE cliente_id=${email_empty_client_id};" "0"

# Vincular pasta exige a mesma permissao de criar.
result="$(db "CALL sp_admin_cliente_set_folder('SyntheticOperatorMissing1004',${operator_client_id},'synthetic-folder-id');")"
assert_contains "${result}" $'0\tforbidden' "folder link requires create permission"
assert_scalar "SELECT COUNT(*) FROM clientes WHERE id=${operator_client_id} AND id_pasta_raiz IS NULL;" "1"

# Auditor sem editar recebe forbidden; nenhum efeito e registrado no cliente.
result="$(db "CALL sp_admin_cliente_update('SyntheticAuditorToken100006',${operator_client_id},'Alteracao Indevida','z-primary@example.invalid','', 'Lead','11999999999','1133334444');")"
assert_contains "${result}" $'0\tforbidden' "auditor cannot update"
assert_scalar "SELECT nome_cliente FROM clientes WHERE id = ${operator_client_id};" "Cliente Operador Atualizado"

# Cliente ativo administrativo fornece alvo para os testes sensiveis.
result="$(db "CALL sp_admin_cliente_create('SyntheticAdministratorToken1001','Cliente Sensivel','sensitive-old@example.invalid','52998224725','Ativo','11988887777');")"
assert_contains "${result}" $'1\tcreated' "Administrador creates sensitive test client"
sensitive_client_id="$(awk -F '\t' 'NR == 1 { print $3 }' <<<"${result}")"
db "INSERT INTO security_sessoes_clientes (cliente_id,email,token_hash,expira_em) VALUES (${sensitive_client_id},'sensitive-old@example.invalid',SHA2('SyntheticClientSession',256),UTC_TIMESTAMP()+INTERVAL 1 HOUR);" >/dev/null

# D2: operador com editar nao pode trocar e-mail nem documento.
result="$(db "CALL sp_admin_cliente_update('SyntheticOperatorAllowed1003',${sensitive_client_id},'Cliente Sensivel','blocked-email@example.invalid','52998224725','Ativo','11988887777',NULL);")"
assert_contains "${result}" $'0\tforbidden' "operator cannot change email"
assert_scalar "SELECT COUNT(*) FROM clientes_emails_autorizados WHERE cliente_id=${sensitive_client_id} AND email='sensitive-old@example.invalid';" "1"
result="$(db "CALL sp_admin_cliente_update('SyntheticOperatorAllowed1003',${sensitive_client_id},'Cliente Sensivel','sensitive-old@example.invalid','11144477735','Ativo','11988887777',NULL);")"
assert_contains "${result}" $'0\tforbidden' "operator cannot change existing document"
assert_scalar "SELECT documento_fiscal_canonico FROM clientes WHERE id=${sensitive_client_id};" "52998224725"

# Administrador troca e-mail: sessoes e links sao revogados na mesma operacao.
result="$(db "CALL sp_admin_cliente_update('SyntheticAdministratorToken1001',${sensitive_client_id},'Cliente Sensivel','sensitive-new@example.invalid','52998224725','Ativo','11988887777',NULL);")"
assert_contains "${result}" $'1\tupdated' "Administrador changes email"
assert_scalar "SELECT COUNT(*) FROM security_sessoes_clientes WHERE cliente_id=${sensitive_client_id} AND revogado_em IS NULL;" "0"
assert_scalar "SELECT COUNT(*) FROM security_password_reset_clientes WHERE cliente_id=${sensitive_client_id} AND resultado_solicitacao='issued' AND utilizado_em IS NULL AND revogado_em IS NULL;" "0"
assert_scalar "SELECT COUNT(*) FROM logs_auditoria WHERE registro_id=${sensitive_client_id} AND funcionario_id=${administrator_id} AND acao='email_changed' AND JSON_UNQUOTE(JSON_EXTRACT(detalhes,'$.request_id')) IS NOT NULL AND JSON_LENGTH(detalhes)=1;" "1"

# Admin (sinonimo) troca documento; a auditoria registra somente a ocorrencia.
result="$(db "CALL sp_admin_cliente_update('SyntheticAdminToken1000000002',${sensitive_client_id},'Cliente Sensivel','sensitive-new@example.invalid','11144477735','Ativo','11988887777',NULL);")"
assert_contains "${result}" $'1\tupdated' "Admin changes document"
assert_scalar "SELECT COUNT(*) FROM logs_auditoria WHERE registro_id=${sensitive_client_id} AND funcionario_id=${admin_id} AND acao='document_changed' AND JSON_UNQUOTE(JSON_EXTRACT(detalhes,'$.request_id')) IS NOT NULL AND JSON_LENGTH(detalhes)=1;" "1"
assert_scalar "SELECT COUNT(*) FROM logs_auditoria WHERE acao IN ('email_changed','document_changed') AND (JSON_EXTRACT(detalhes,'$.previous_hash') IS NOT NULL OR JSON_EXTRACT(detalhes,'$.new_hash') IS NOT NULL);" "0"
assert_scalar "SELECT COUNT(*) FROM logs_auditoria WHERE acao IN ('email_changed','document_changed') AND (detalhes LIKE '%sensitive-old@example.invalid%' OR detalhes LIKE '%sensitive-new@example.invalid%' OR detalhes LIKE '%52998224725%' OR detalhes LIKE '%11144477735%');" "0"
assert_scalar "SELECT COUNT(*) FROM logs_auditoria WHERE acao='client_action_forbidden';" "17"
assert_scalar "SELECT COUNT(*) FROM logs_auditoria WHERE acao='client_action_forbidden' AND registro_id IS NOT NULL;" "0"

# T-0005: "Sair" revoga somente a sessao do token, com auditoria minima e
# resultado identico para token valido, invalido, desconhecido ou expirado.
apply_logout_sql 004_up.sql
db "INSERT INTO security_sessoes_funcionarios (funcionario_id, token_hash, expira_em) VALUES
  (${operator_allowed_id}, SHA2('SyntheticLogoutEmployeeA0001', 256), UTC_TIMESTAMP() + INTERVAL 1 HOUR),
  (${operator_allowed_id}, SHA2('SyntheticLogoutEmployeeB0002', 256), UTC_TIMESTAMP() + INTERVAL 1 HOUR),
  (${operator_allowed_id}, SHA2('SyntheticLogoutExpiredEmp0003', 256), UTC_TIMESTAMP() - INTERVAL 1 MINUTE);" >/dev/null
employee_session_a="$(db "SELECT id FROM security_sessoes_funcionarios WHERE token_hash = SHA2('SyntheticLogoutEmployeeA0001', 256);")"
assert_contains "$(db "CALL sp_admin_cliente_list('SyntheticLogoutEmployeeA0001');")" $'1\tlisted' "employee session works before logout"
for token in 'SyntheticLogoutEmployeeA0001' 'SyntheticLogoutEmployeeA0001' 'bad token!' '' 'SyntheticUnknownLogout000009' 'SyntheticLogoutExpiredEmp0003'; do
  assert_contains "$(db "CALL sp_funcionario_logout('${token}');")" $'1\tlogged_out' "employee logout neutral result"
done
assert_contains "$(db "CALL sp_funcionario_logout(NULL);")" $'1\tlogged_out' "employee logout null token"
assert_scalar "SELECT revogado_em IS NOT NULL FROM security_sessoes_funcionarios WHERE id = ${employee_session_a};" "1"
assert_scalar "SELECT revogado_em IS NULL FROM security_sessoes_funcionarios WHERE token_hash = SHA2('SyntheticLogoutEmployeeB0002', 256);" "1"
assert_scalar "SELECT revogado_em IS NULL FROM security_sessoes_funcionarios WHERE token_hash = SHA2('SyntheticLogoutExpiredEmp0003', 256);" "1"
assert_scalar "SELECT COUNT(*) FROM security_sessoes_funcionarios WHERE token_hash = SHA2('SyntheticAdministratorToken1001', 256) AND revogado_em IS NULL;" "1"
assert_contains "$(db "CALL sp_admin_cliente_list('SyntheticLogoutEmployeeA0001');")" $'0\tunauthorized' "revoked employee session cannot list"
assert_contains "$(db "CALL sp_admin_cliente_list('SyntheticLogoutEmployeeB0002');")" $'1\tlisted' "other session of same employee keeps working"
assert_scalar "SELECT COUNT(*) FROM logs_auditoria WHERE acao = 'employee_logout';" "1"
assert_scalar "SELECT COUNT(*) FROM logs_auditoria WHERE acao = 'employee_logout' AND funcionario_id = ${operator_allowed_id} AND tabela_afetada = 'security_sessoes_funcionarios' AND registro_id = ${employee_session_a} AND JSON_LENGTH(detalhes) = 1 AND JSON_UNQUOTE(JSON_EXTRACT(detalhes, '$.request_id')) IS NOT NULL;" "1"

second_client_id="$(db "SELECT id FROM clientes WHERE id <> ${sensitive_client_id} ORDER BY id LIMIT 1;")"
db "INSERT INTO security_sessoes_clientes (cliente_id, token_hash, expira_em) VALUES
  (${sensitive_client_id}, SHA2('SyntheticLogoutClientA000001', 256), UTC_TIMESTAMP() + INTERVAL 1 HOUR),
  (${sensitive_client_id}, SHA2('SyntheticLogoutClientB000002', 256), UTC_TIMESTAMP() + INTERVAL 1 HOUR),
  (${second_client_id}, SHA2('SyntheticLogoutOtherClient03', 256), UTC_TIMESTAMP() + INTERVAL 1 HOUR),
  (${sensitive_client_id}, SHA2('SyntheticLogoutExpiredCli004', 256), UTC_TIMESTAMP() - INTERVAL 1 MINUTE);" >/dev/null
for token in 'SyntheticLogoutClientA000001' 'SyntheticLogoutClientA000001' 'bad token!' '' 'SyntheticUnknownLogout000009' 'SyntheticLogoutExpiredCli004' 'SyntheticLogoutEmployeeB0002'; do
  assert_contains "$(db "CALL sp_cliente_logout('${token}');")" $'1\tlogged_out' "client logout neutral result"
done
assert_contains "$(db "CALL sp_cliente_logout(NULL);")" $'1\tlogged_out' "client logout null token"
assert_scalar "SELECT COUNT(*) FROM security_sessoes_clientes WHERE revogado_em IS NOT NULL AND token_hash IN (SHA2('SyntheticLogoutClientA000001', 256), SHA2('SyntheticLogoutClientB000002', 256), SHA2('SyntheticLogoutOtherClient03', 256), SHA2('SyntheticLogoutExpiredCli004', 256));" "1"
assert_scalar "SELECT revogado_em IS NOT NULL FROM security_sessoes_clientes WHERE token_hash = SHA2('SyntheticLogoutClientA000001', 256);" "1"
assert_scalar "SELECT revogado_em IS NULL FROM security_sessoes_funcionarios WHERE token_hash = SHA2('SyntheticLogoutEmployeeB0002', 256);" "1"
assert_scalar "SELECT COUNT(*) FROM logs_auditoria WHERE acao = 'client_logout';" "1"
assert_scalar "SELECT COUNT(*) FROM logs_auditoria WHERE acao = 'client_logout' AND funcionario_id IS NULL AND tabela_afetada = 'security_sessoes_clientes' AND registro_id = ${sensitive_client_id} AND JSON_LENGTH(detalhes) = 1;" "1"
assert_scalar "SELECT COUNT(*) FROM logs_auditoria WHERE acao IN ('employee_logout', 'client_logout') AND (detalhes LIKE '%Synthetic%' OR detalhes REGEXP '[0-9a-f]{64}');" "0"

apply_logout_sql 004_down.sql
assert_scalar "SELECT COUNT(*) FROM information_schema.ROUTINES WHERE ROUTINE_SCHEMA = DATABASE() AND ROUTINE_NAME IN ('sp_funcionario_logout', 'sp_cliente_logout');" "0"
assert_scalar "SELECT COUNT(*) FROM logs_auditoria WHERE acao IN ('employee_logout', 'client_logout');" "2"

apply_hardening_sql 005_down.sql
assert_scalar "SELECT COUNT(*) FROM information_schema.ROUTINES WHERE ROUTINE_SCHEMA=DATABASE() AND ROUTINE_NAME='sp_admin_module_authorize';" "0"
assert_scalar "SELECT COUNT(*) FROM logs_auditoria WHERE acao='employee_module_action_forbidden';" "7"

# O downgrade remove a fronteira nova e restaura create/update de 002.
apply_sql 003_down.sql
assert_scalar "SELECT COUNT(*) FROM information_schema.ROUTINES WHERE ROUTINE_SCHEMA=DATABASE() AND ROUTINE_NAME IN ('sp_admin_client_authorize','sp_admin_cliente_list');" "0"
result="$(db "CALL sp_admin_cliente_create('SyntheticOperatorMissing1004','Cliente Pos Rollback','rollback-client@example.invalid','', 'Lead', NULL);")"
assert_contains "${result}" $'1\tcreated' "rollback restores create behavior"
result="$(db "CALL sp_admin_cliente_update('SyntheticOperatorAllowed1003',${sensitive_client_id},'Cliente Pos Rollback','rollback-email@example.invalid','11144477735','Ativo','11988887777',NULL);")"
assert_contains "${result}" $'1\tupdated' "rollback restores update behavior"

apply_sql 002_down.sql
apply_sql 001_down.sql

echo "CLIENT_MANAGEMENT_MIGRATION_003=VALID"
echo "CLIENT_MANAGEMENT_AUTHORIZATION_TESTS=PASS"
echo "CLIENT_MANAGEMENT_AUDIT_TESTS=PASS"
echo "CLIENT_MANAGEMENT_ROLLBACK=PASS"
echo "SESSION_LOGOUT_TESTS=PASS"
echo "SESSION_LOGOUT_ROLLBACK=PASS"
echo "WEBHOOK_HARDENING_AUTHORIZATION_TESTS=PASS"
echo "WEBHOOK_HARDENING_ROLLBACK=PASS"
