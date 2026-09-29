import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ASSET_DIR = ROOT / 'docs' / 'integration' / 'system_a_admin_password_recovery'
UP = ASSET_DIR / '001_up.sql'
DOWN = ASSET_DIR / '001_down.sql'
WORKFLOW = ASSET_DIR / 'n8n_admin_password_recovery.json'
BASE_SCHEMA = ASSET_DIR / 'test_base_schema.sql'
VALIDATION_SCRIPT = ROOT / 'scripts' / 'validate_system_a_password_recovery.sh'


def _workflow() -> dict[str, object]:
    return json.loads(WORKFLOW.read_text(encoding='utf-8'))


def test_password_reset_schema_uses_database_randomness_and_hashed_tokens() -> None:
    migration = UP.read_text(encoding='utf-8')
    table_ddl = migration.split('DELIMITER', maxsplit=1)[0]
    assert 'RANDOM_BYTES(32)' in migration
    assert 'Math.random' not in migration
    assert 'token_hash CHAR(64)' in table_ddl
    assert ' token ' not in table_ddl.lower()
    assert 'UNIQUE KEY uq_password_reset_token_hash' in migration
    assert 'FOREIGN KEY (funcionario_id) REFERENCES funcionarios (id)' in migration


def test_password_reset_apply_is_atomic_and_revokes_existing_sessions() -> None:
    migration = UP.read_text(encoding='utf-8')
    apply_procedure = migration.split(
        'CREATE PROCEDURE sp_admin_password_reset_apply', maxsplit=1,
    )[1]
    assert 'START TRANSACTION;' in apply_procedure
    assert 'ROLLBACK;' in apply_procedure
    assert 'COMMIT;' in apply_procedure
    assert 'UPDATE funcionarios' in apply_procedure
    assert 'UPDATE security_sessoes_funcionarios' in apply_procedure
    assert "'admin_password_reset_completed'" in apply_procedure
    assert 'senha = SHA2(p_new_password, 256)' in apply_procedure


def test_password_reset_audit_payload_excludes_secrets() -> None:
    migration = UP.read_text(encoding='utf-8')
    audit_payloads = [
        line.strip()
        for line in migration.splitlines()
        if 'JSON_OBJECT(' in line
    ]
    assert len(audit_payloads) == 2
    for payload in audit_payloads:
        lowered = payload.lower()
        assert 'password' not in lowered
        assert 'senha' not in lowered
        assert 'token' not in lowered
        assert 'email' not in lowered


def test_password_reset_workflow_is_inactive_and_does_not_save_execution_data() -> None:
    workflow = _workflow()
    assert workflow['active'] is False
    settings = workflow['settings']
    assert settings['saveDataErrorExecution'] == 'none'
    assert settings['saveDataSuccessExecution'] == 'none'
    assert settings['saveManualExecutions'] is False
    assert settings['availableInMCP'] is False


def test_password_reset_workflow_uses_bound_query_parameters() -> None:
    workflow = _workflow()
    mysql_nodes = [
        node for node in workflow['nodes']
        if node['type'] == 'n8n-nodes-base.mySql'
    ]
    assert len(mysql_nodes) == 2
    for node in mysql_nodes:
        query = node['parameters']['query']
        options = node['parameters']['options']
        assert '{{' not in query
        assert '$1' in query and '$2' in query
        assert 'queryReplacement' in options


def test_password_reset_workflow_does_not_trust_public_rate_limit_header() -> None:
    workflow = _workflow()
    request_node = next(
        node for node in workflow['nodes'] if node['name'] == 'Emitir Token no Banco'
    )
    replacements = request_node['parameters']['options']['queryReplacement']
    assert "'unknown'" in replacements
    assert 'x-rate-limit-key' not in replacements.lower()


def test_password_reset_workflow_normalizes_mariadb_call_result_sets() -> None:
    workflow = _workflow()
    code_nodes = {
        node['name']: node['parameters']['jsCode']
        for node in workflow['nodes']
        if node['type'] == 'n8n-nodes-base.code'
    }
    assert set(code_nodes) == {
        'Normalizar Solicitacao',
        'Normalizar Aplicacao',
    }
    for code in code_nodes.values():
        assert 'Array.isArray(item.json)' in code
        assert "hasOwnProperty.call(value, 'request_id')" in code
        assert 'Math.random' not in code


def test_password_reset_workflow_contains_only_admin_webhooks() -> None:
    workflow = _workflow()
    assert workflow['name'] == '[Auth] Recuperacao de Senha Admin v1.1'
    webhook_paths = {
        node['parameters']['path']
        for node in workflow['nodes']
        if node['type'] == 'n8n-nodes-base.webhook'
    }
    assert webhook_paths == {
        'admin/solicitar-senha',
        'admin/redefinir-senha',
    }


def test_password_reset_token_uses_url_fragment_in_email_link() -> None:
    workflow = _workflow()
    email_nodes = [
        node for node in workflow['nodes']
        if node['type'] == 'n8n-nodes-base.emailSend'
    ]
    assert len(email_nodes) == 1
    html = email_nodes[0]['parameters']['html']
    assert '/admin/redefinir-senha#token=' in html
    assert '/admin/redefinir-senha?token=' not in html


def test_password_reset_rollback_removes_only_new_objects() -> None:
    rollback = DOWN.read_text(encoding='utf-8')
    assert 'DROP PROCEDURE IF EXISTS sp_admin_password_reset_apply' in rollback
    assert 'DROP PROCEDURE IF EXISTS sp_admin_password_reset_request' in rollback
    assert 'DROP TABLE IF EXISTS security_password_reset_funcionarios' in rollback
    assert 'funcionarios;' not in rollback.replace(
        'security_password_reset_funcionarios;', '',
    )


def test_isolated_validation_uses_matching_mariadb_without_host_ports() -> None:
    script = VALIDATION_SCRIPT.read_text(encoding='utf-8')
    assert 'mariadb:11.8.9' in script
    assert '--publish' not in script
    assert '-p ' not in script
    assert 'docker rm -f "${CONTAINER}"' in script
    assert 'PASSWORD_RESET_MIGRATION=VALID' in script
    assert 'PASSWORD_RESET_FUNCTIONAL_TESTS=PASS' in script
    assert 'PASSWORD_RESET_ROLLBACK=PASS' in script


def test_isolated_schema_contains_only_synthetic_identity() -> None:
    schema = BASE_SCHEMA.read_text(encoding='utf-8')
    assert 'synthetic@example.invalid' in schema
    assert 'Usuario Sintetico' in schema
    assert 'serdial21_recovery_test' in schema
