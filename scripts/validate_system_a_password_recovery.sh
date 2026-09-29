#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ASSET_DIR="${REPO_ROOT}/docs/integration/system_a_admin_password_recovery"
IMAGE="mariadb:11.8.9"
CONTAINER="serdial21-password-reset-validation-$$"
DB_NAME="serdial21_recovery_test"
DB_PASSWORD="$(openssl rand -hex 24)"

cleanup() {
  docker rm -f "${CONTAINER}" >/dev/null 2>&1 || true
}
trap cleanup EXIT

for required in docker openssl; do
  command -v "${required}" >/dev/null 2>&1 || {
    echo "MISSING_COMMAND=${required}"
    exit 1
  }
done

for required_file in test_base_schema.sql 001_up.sql 001_down.sql verify.sql; do
  test -f "${ASSET_DIR}/${required_file}" || {
    echo "MISSING_FILE=${ASSET_DIR}/${required_file}"
    exit 1
  }
done

docker run --detach --rm \
  --name "${CONTAINER}" \
  --env "MARIADB_ROOT_PASSWORD=${DB_PASSWORD}" \
  --mount "type=bind,src=${ASSET_DIR},dst=/validation,readonly" \
  "${IMAGE}" >/dev/null

for _ in $(seq 1 60); do
  if docker exec "${CONTAINER}" mariadb-admin \
      --host=127.0.0.1 --user=root --password="${DB_PASSWORD}" ping \
      >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

docker exec "${CONTAINER}" mariadb-admin \
  --host=127.0.0.1 --user=root --password="${DB_PASSWORD}" ping \
  >/dev/null

docker exec -i "${CONTAINER}" mariadb \
  --host=127.0.0.1 --user=root --password="${DB_PASSWORD}" \
  < "${ASSET_DIR}/test_base_schema.sql"

docker exec -i "${CONTAINER}" mariadb \
  --host=127.0.0.1 --user=root --password="${DB_PASSWORD}" "${DB_NAME}" \
  < "${ASSET_DIR}/001_up.sql"

docker exec -i "${CONTAINER}" mariadb \
  --host=127.0.0.1 --user=root --password="${DB_PASSWORD}" "${DB_NAME}" \
  < "${ASSET_DIR}/verify.sql" >/dev/null

request_result="$(docker exec "${CONTAINER}" mariadb \
  --host=127.0.0.1 --user=root --password="${DB_PASSWORD}" \
  --batch --skip-column-names "${DB_NAME}" \
  --execute="CALL sp_admin_password_reset_request('synthetic@example.invalid', 'synthetic-source');")"

IFS=$'\t' read -r accepted should_send delivery_email reset_token request_id \
  <<< "${request_result}"

test "${accepted}" = "1"
test "${should_send}" = "1"
test "${delivery_email}" = "synthetic@example.invalid"
test "${#reset_token}" -eq 64
[[ "${reset_token}" =~ ^[0-9a-f]{64}$ ]]
test "${#request_id}" -eq 36

stored_token_check="$(docker exec "${CONTAINER}" mariadb \
  --host=127.0.0.1 --user=root --password="${DB_PASSWORD}" \
  --batch --skip-column-names "${DB_NAME}" \
  --execute="SELECT token_hash = SHA2('${reset_token}', 256) AND token_hash <> '${reset_token}' FROM security_password_reset_funcionarios WHERE request_id = '${request_id}';")"
test "${stored_token_check}" = "1"

apply_result="$(docker exec "${CONTAINER}" mariadb \
  --host=127.0.0.1 --user=root --password="${DB_PASSWORD}" \
  --batch --skip-column-names "${DB_NAME}" \
  --execute="CALL sp_admin_password_reset_apply('${reset_token}', 'NewSyntheticPassword456');")"

IFS=$'\t' read -r apply_success apply_status apply_request_id \
  <<< "${apply_result}"
test "${apply_success}" = "1"
test "${apply_status}" = "success"
test "${#apply_request_id}" -eq 36

effects="$(docker exec "${CONTAINER}" mariadb \
  --host=127.0.0.1 --user=root --password="${DB_PASSWORD}" \
  --batch --skip-column-names "${DB_NAME}" \
  --execute="SELECT (f.senha = SHA2('NewSyntheticPassword456', 256)), (r.utilizado_em IS NOT NULL), (s.revogado_em IS NOT NULL), (SELECT COUNT(*) FROM logs_auditoria WHERE funcionario_id = 1 AND acao IN ('admin_password_reset_requested', 'admin_password_reset_completed')) FROM funcionarios f JOIN security_password_reset_funcionarios r ON r.funcionario_id = f.id JOIN security_sessoes_funcionarios s ON s.funcionario_id = f.id WHERE f.id = 1 AND r.request_id = '${request_id}';")"
test "${effects}" = $'1\t1\t1\t2'

reuse_result="$(docker exec "${CONTAINER}" mariadb \
  --host=127.0.0.1 --user=root --password="${DB_PASSWORD}" \
  --batch --skip-column-names "${DB_NAME}" \
  --execute="CALL sp_admin_password_reset_apply('${reset_token}', 'AnotherSyntheticPassword789');")"
IFS=$'\t' read -r reuse_success reuse_status _ <<< "${reuse_result}"
test "${reuse_success}" = "0"
test "${reuse_status}" = "invalid_or_expired"

unknown_result="$(docker exec "${CONTAINER}" mariadb \
  --host=127.0.0.1 --user=root --password="${DB_PASSWORD}" \
  --batch --skip-column-names "${DB_NAME}" \
  --execute="CALL sp_admin_password_reset_request('missing@example.invalid', 'synthetic-source-2');")"
IFS=$'\t' read -r unknown_accepted unknown_should_send _ _ _ \
  <<< "${unknown_result}"
test "${unknown_accepted}" = "1"
test "${unknown_should_send}" = "0"

docker exec -i "${CONTAINER}" mariadb \
  --host=127.0.0.1 --user=root --password="${DB_PASSWORD}" "${DB_NAME}" \
  < "${ASSET_DIR}/001_down.sql"

remaining_objects="$(docker exec "${CONTAINER}" mariadb \
  --host=127.0.0.1 --user=root --password="${DB_PASSWORD}" \
  --batch --skip-column-names "${DB_NAME}" \
  --execute="SELECT (SELECT COUNT(*) FROM information_schema.TABLES WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'security_password_reset_funcionarios') + (SELECT COUNT(*) FROM information_schema.ROUTINES WHERE ROUTINE_SCHEMA = DATABASE() AND ROUTINE_NAME IN ('sp_admin_password_reset_request', 'sp_admin_password_reset_apply'));")"
test "${remaining_objects}" = "0"

echo "MARIADB_VERSION=$(docker exec "${CONTAINER}" mariadb --host=127.0.0.1 --user=root --password="${DB_PASSWORD}" --batch --skip-column-names --execute='SELECT VERSION();')"
echo "PASSWORD_RESET_MIGRATION=VALID"
echo "PASSWORD_RESET_FUNCTIONAL_TESTS=PASS"
echo "PASSWORD_RESET_ROLLBACK=PASS"
