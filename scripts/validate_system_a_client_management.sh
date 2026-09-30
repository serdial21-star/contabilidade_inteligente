#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ASSET_DIR="${ROOT_DIR}/docs/integration/system_a_client_management"
CONTAINER="serdial21-client-management-test-$$"

cleanup() {
  docker rm -f "${CONTAINER}" >/dev/null 2>&1 || true
}
trap cleanup EXIT

docker run --name "${CONTAINER}" \
  --env MARIADB_ROOT_PASSWORD=synthetic-root-password \
  --detach mariadb:11.8.9 >/dev/null

for _ in $(seq 1 60); do
  if docker exec "${CONTAINER}" mariadb-admin \
      --user=root --password=synthetic-root-password ping \
      --silent >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

docker exec "${CONTAINER}" mariadb \
  --user=root --password=synthetic-root-password \
  < "${ASSET_DIR}/test_base_schema.sql"

docker exec "${CONTAINER}" mariadb \
  --user=root --password=synthetic-root-password \
  serdial21_client_management_test \
  < "${ASSET_DIR}/001_up.sql"

CREATE_RESULT="$(docker exec "${CONTAINER}" mariadb \
  --batch --skip-column-names \
  --user=root --password=synthetic-root-password \
  serdial21_client_management_test \
  --execute="CALL sp_admin_cliente_create(
    'SyntheticAdminToken1234567890',
    'Cliente Sintetico',
    'synthetic-client@example.invalid',
    '52998224725',
    'Ativo',
    '11999999999'
  );")"

grep -q $'1\tcreated\t1\t1' <<<"${CREATE_RESULT}"

TOKEN="$(awk -F '\t' 'NR == 1 { print $6 }' <<<"${CREATE_RESULT}")"
test "${#TOKEN}" -eq 64

APPLY_RESULT="$(docker exec "${CONTAINER}" mariadb \
  --batch --skip-column-names \
  --user=root --password=synthetic-root-password \
  serdial21_client_management_test \
  --execute="CALL sp_cliente_password_reset_apply(
    '${TOKEN}', 'SyntheticClient9x!'
  );")"

grep -q $'1\tsuccess' <<<"${APPLY_RESULT}"

SECOND_RESULT="$(docker exec "${CONTAINER}" mariadb \
  --batch --skip-column-names \
  --user=root --password=synthetic-root-password \
  serdial21_client_management_test \
  --execute="CALL sp_cliente_password_reset_apply(
    '${TOKEN}', 'SyntheticClient9x!'
  );")"

grep -q $'0\tinvalid_or_expired' <<<"${SECOND_RESULT}"

docker exec "${CONTAINER}" mariadb \
  --user=root --password=synthetic-root-password \
  serdial21_client_management_test \
  < "${ASSET_DIR}/001_down.sql"

echo "CLIENT_MANAGEMENT_MIGRATION=VALID"
echo "CLIENT_MANAGEMENT_FUNCTIONAL_TESTS=PASS"
echo "CLIENT_MANAGEMENT_ROLLBACK=PASS"
