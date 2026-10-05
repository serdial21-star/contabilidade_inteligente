#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ASSET_DIR="${ROOT_DIR}/docs/integration/system_a_portal_detalhes"
CONTAINER="serdial21-portal-details-test-$$"
DB_NAME="serdial21_portal_details_test"
DB_PASSWORD="$(openssl rand -hex 24)"

cleanup() {
  docker rm -f "${CONTAINER}" >/dev/null 2>&1 || true
}
trap cleanup EXIT

for required in docker openssl grep; do
  command -v "${required}" >/dev/null 2>&1 || {
    echo "MISSING_COMMAND=${required}"
    exit 1
  }
done

for required_file in test_base_schema.sql 006_up.sql 006_down.sql verify_006.sql; do
  test -f "${ASSET_DIR}/${required_file}" || {
    echo "MISSING_FILE=${ASSET_DIR}/${required_file}"
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
apply_sql 006_up.sql

TOKEN_A='SyntheticPortalClientTokenA01'
TOKEN_B='SyntheticPortalClientTokenB02'

# Detalhes: sessao viva, ownership e resposta uniforme para ausente/cross-client.
assert_contains "$(db "CALL sp_portal_detalhe_chamado('${TOKEN_A}',1);")" $'1\tfound' "ticket owner can read"
assert_contains "$(db "CALL sp_portal_detalhe_documento('${TOKEN_A}',1);")" $'1\tfound' "document owner can read"
assert_contains "$(db "CALL sp_portal_detalhe_chamado('${TOKEN_A}',2);")" $'0\tnot_found' "cross-client ticket hidden"
assert_contains "$(db "CALL sp_portal_detalhe_chamado('${TOKEN_A}',999);")" $'0\tnot_found' "missing ticket hidden identically"
assert_contains "$(db "CALL sp_portal_detalhe_documento('${TOKEN_B}',1);")" $'0\tnot_found' "cross-client document hidden"
assert_contains "$(db "CALL sp_portal_detalhe_documento('${TOKEN_B}',999);")" $'0\tnot_found' "missing document hidden identically"
for token in SyntheticPortalExpiredToken03 SyntheticPortalRevokedToken04 SyntheticUnknownPortalToken05; do
  assert_contains "$(db "CALL sp_portal_detalhe_chamado('${token}',1);")" $'0\tunauthorized' "invalid ticket session"
  assert_contains "$(db "CALL sp_portal_detalhe_documento('${token}',1);")" $'0\tunauthorized' "invalid document session"
done

# Complementos: mensagem ou anexo, limite, fechamento, isolamento e auditoria.
assert_contains "$(db "CALL sp_portal_complementar_chamado('${TOKEN_A}',1,'Mensagem sintetica',NULL,NULL);")" $'1\tcreated' "ticket message created"
assert_contains "$(db "CALL sp_portal_complementar_chamado('${TOKEN_A}',1,'','https://example.invalid/ticket-file','ticket.pdf');")" $'1\tcreated' "ticket attachment-only created"
assert_contains "$(db "CALL sp_portal_complementar_documento('${TOKEN_A}',1,'Documento complementado',NULL,NULL);")" $'1\tcreated' "document message created"
assert_contains "$(db "CALL sp_portal_complementar_documento('${TOKEN_A}',1,'','https://example.invalid/document-file','documento.xml');")" $'1\tcreated' "document attachment-only created"
assert_contains "$(db "CALL sp_portal_complementar_chamado('${TOKEN_A}',1,REPEAT('x',5001),NULL,NULL);")" $'0\tinvalid_input' "ticket message length enforced"
assert_contains "$(db "CALL sp_portal_complementar_documento('${TOKEN_A}',1,'',NULL,NULL);")" $'0\tinvalid_input' "empty document complement rejected"
assert_contains "$(db "CALL sp_portal_complementar_chamado('${TOKEN_A}',3,'Nao gravar',NULL,NULL);")" $'0\tclosed' "closed ticket rejected"
assert_contains "$(db "CALL sp_portal_complementar_documento('${TOKEN_A}',3,'Nao gravar',NULL,NULL);")" $'0\tclosed' "closed document rejected"
assert_contains "$(db "CALL sp_portal_complementar_chamado('${TOKEN_A}',2,'Nao gravar',NULL,NULL);")" $'0\tnot_found' "cross-client ticket write hidden"
assert_contains "$(db "CALL sp_portal_complementar_documento('${TOKEN_A}',2,'Nao gravar',NULL,NULL);")" $'0\tnot_found' "cross-client document write hidden"
assert_scalar "SELECT COUNT(*) FROM tickets_mensagens WHERE ticket_id=1 AND remetente_tipo='Cliente' AND remetente_id=1;" "2"
assert_scalar "SELECT COUNT(*) FROM inbox_documentos_complementos WHERE documento_id=1 AND cliente_id=1 AND remetente_tipo='Cliente' AND remetente_id=1;" "2"
assert_scalar "SELECT COUNT(*) FROM tickets_mensagens WHERE ticket_id IN (2,3);" "0"
assert_scalar "SELECT COUNT(*) FROM inbox_documentos_complementos WHERE documento_id IN (2,3);" "0"
assert_scalar "SELECT COUNT(*) FROM logs_auditoria WHERE acao='client_ticket_complement' AND JSON_LENGTH(detalhes)=3 AND detalhes NOT LIKE '%Mensagem sintetica%';" "2"
assert_scalar "SELECT COUNT(*) FROM logs_auditoria WHERE acao='client_document_complement' AND JSON_LENGTH(detalhes)=3 AND detalhes NOT LIKE '%Documento complementado%';" "2"

# Falha da auditoria reverte insercao e atualizado_em na mesma transacao.
db "UPDATE tickets_master SET atualizado_em='2000-01-01 00:00:00' WHERE id=1;
    UPDATE inbox_documentos SET atualizado_em='2000-01-01 00:00:00' WHERE id=1;" >/dev/null
db "CREATE TRIGGER synthetic_fail_audit BEFORE INSERT ON logs_auditoria FOR EACH ROW SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='synthetic audit failure';" >/dev/null
if db "CALL sp_portal_complementar_chamado('${TOKEN_A}',1,'Deve reverter',NULL,NULL);" >/dev/null 2>&1; then
  echo 'ASSERT_FAILED audit failure should abort complement'
  exit 1
fi
if db "CALL sp_portal_complementar_documento('${TOKEN_A}',1,'Deve reverter',NULL,NULL);" >/dev/null 2>&1; then
  echo 'ASSERT_FAILED audit failure should abort document complement'
  exit 1
fi
db "DROP TRIGGER synthetic_fail_audit;" >/dev/null
assert_scalar "SELECT COUNT(*) FROM tickets_mensagens WHERE ticket_id=1;" "2"
assert_scalar "SELECT COUNT(*) FROM inbox_documentos_complementos WHERE documento_id=1;" "2"
assert_scalar "SELECT DATE_FORMAT(atualizado_em,'%Y-%m-%d %H:%i:%s') FROM tickets_master WHERE id=1;" "2000-01-01 00:00:00"
assert_scalar "SELECT DATE_FORMAT(atualizado_em,'%Y-%m-%d %H:%i:%s') FROM inbox_documentos WHERE id=1;" "2000-01-01 00:00:00"

# Down falha fechado enquanto houver historico novo; depois reverte apenas 006.
if apply_sql 006_down.sql >/dev/null 2>&1; then
  echo 'ASSERT_FAILED guarded downgrade should reject existing complements'
  exit 1
fi
db "DELETE FROM inbox_documentos_complementos; UPDATE tickets_mensagens SET anexo_nome=NULL;" >/dev/null
apply_sql 006_down.sql
assert_scalar "SELECT COUNT(*) FROM information_schema.ROUTINES WHERE ROUTINE_SCHEMA=DATABASE() AND ROUTINE_NAME LIKE 'sp_portal_%';" "0"
assert_scalar "SELECT COUNT(*) FROM information_schema.TABLES WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='inbox_documentos_complementos';" "0"
assert_scalar "SELECT COUNT(*) FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='tickets_mensagens' AND COLUMN_NAME='anexo_nome';" "0"
assert_scalar "SELECT COUNT(*) FROM logs_auditoria WHERE acao IN ('client_ticket_complement','client_document_complement');" "4"

echo 'PORTAL_DETAILS_MIGRATION_006=VALID'
echo 'PORTAL_DETAILS_ISOLATION_TESTS=PASS'
echo 'PORTAL_DETAILS_AUDIT_ATOMICITY=PASS'
echo 'PORTAL_DETAILS_ROLLBACK=PASS'
