import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ASSET_DIR = ROOT / 'docs' / 'integration' / 'system_a_client_management'
UP = ASSET_DIR / '001_up.sql'
DOWN = ASSET_DIR / '001_down.sql'
CREATE_WORKFLOW = ASSET_DIR / 'n8n_admin_client_create_v3.json'
LIST_WORKFLOW = ASSET_DIR / 'n8n_admin_client_list_v2.json'
LIST_ROLLBACK_WORKFLOW = ASSET_DIR / 'n8n_admin_client_list_v2_rollback.json'
RESET_WORKFLOW = ASSET_DIR / 'n8n_client_password_recovery_v2.json'
EDIT_UP = ASSET_DIR / '002_up.sql'
EDIT_DOWN = ASSET_DIR / '002_down.sql'
EDIT_WORKFLOW = ASSET_DIR / 'n8n_admin_client_update_v1.json'
AUTH_UP = ASSET_DIR / '003_up.sql'
AUTH_DOWN = ASSET_DIR / '003_down.sql'
BASE_SCHEMA = ASSET_DIR / 'test_base_schema.sql'
VALIDATION_SCRIPT = ROOT / 'scripts' / 'validate_system_a_client_management.sh'
CI_WORKFLOW = ROOT / '.github' / 'workflows' / 'ci.yml'
VERIFY_SQL = ASSET_DIR / 'verify.sql'


def _workflow(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding='utf-8'))


def test_schema_enforces_canonical_document_uniqueness() -> None:
    migration = UP.read_text(encoding='utf-8')
    assert 'documento_fiscal_canonico' in migration
    assert 'GENERATED ALWAYS AS' in migration
    assert 'UNIQUE KEY IF NOT EXISTS uq_clientes_documento_fiscal_canonico' in migration
    assert "UPPER(" in migration


def test_security_tables_use_hashed_random_tokens() -> None:
    migration = UP.read_text(encoding='utf-8')
    table_ddl = migration.split('DELIMITER', maxsplit=1)[0]
    assert 'RANDOM_BYTES(32)' in migration
    assert 'Math.random' not in migration
    assert 'token_hash CHAR(64)' in table_ddl
    assert ' token ' not in table_ddl.lower()
    assert 'UNIQUE KEY uq_client_password_reset_token_hash' in migration
    assert 'CREATE TABLE security_sessoes_clientes' not in migration


def test_client_creation_is_atomic_and_has_no_shared_password() -> None:
    migration = UP.read_text(encoding='utf-8')
    procedure = migration.split('CREATE PROCEDURE sp_admin_cliente_create', 1)[1]
    procedure = procedure.split('CREATE PROCEDURE sp_admin_cliente_set_folder', 1)[0]
    assert 'START TRANSACTION;' in procedure
    assert 'ROLLBACK;' in procedure
    assert 'COMMIT;' in procedure
    assert 'INSERT INTO clientes (' in procedure
    assert 'INSERT INTO clientes_emails_autorizados' in procedure
    assert 'RANDOM_BYTES(32)' in procedure
    assert 'Serdial21@Mudar' not in procedure


def test_password_apply_is_atomic_and_revokes_sessions() -> None:
    migration = UP.read_text(encoding='utf-8')
    procedure = migration.split(
        'CREATE PROCEDURE sp_cliente_password_reset_apply', 1,
    )[1]
    assert 'START TRANSACTION;' in procedure
    assert 'UPDATE clientes' in procedure
    assert 'UPDATE security_sessoes_clientes' in procedure
    assert "'client_password_reset_completed'" in procedure
    assert 'senha = SHA2(p_new_password, 256)' in procedure


def test_workflows_are_inactive_and_do_not_save_execution_data() -> None:
    for path in (CREATE_WORKFLOW, LIST_WORKFLOW, RESET_WORKFLOW, EDIT_WORKFLOW):
        workflow = _workflow(path)
        assert workflow['active'] is False
        settings = workflow['settings']
        assert settings['saveDataErrorExecution'] == 'none'
        assert settings['saveDataSuccessExecution'] == 'none'
        assert settings['saveManualExecutions'] is False
        assert settings['availableInMCP'] is False


def test_mysql_dynamic_values_use_bound_parameters() -> None:
    for path in (CREATE_WORKFLOW, LIST_WORKFLOW, RESET_WORKFLOW, EDIT_WORKFLOW):
        workflow = _workflow(path)
        for node in workflow['nodes']:
            if node['type'] != 'n8n-nodes-base.mySql':
                continue
            query = node['parameters']['query']
            assert '{{' not in query
            if '$' in query:
                assert 'queryReplacement' in node['parameters']['options']


def test_create_workflow_validates_tax_ids_and_sends_activation_link() -> None:
    workflow = _workflow(CREATE_WORKFLOW)
    serialized = json.dumps(workflow, ensure_ascii=False)
    assert 'cpfDigit' in serialized
    assert 'cnpjDigit' in serialized
    assert 'Math.random' not in serialized
    assert 'senha_padrao' not in serialized
    assert '/redefinir-senha#token=' in serialized
    assert 'CONFIGURE_ROOT_FOLDER_ID' in serialized


def test_list_workflow_returns_all_statuses_and_display_fields() -> None:
    workflow = _workflow(LIST_WORKFLOW)
    serialized = json.dumps(workflow, ensure_ascii=False)
    migration = AUTH_UP.read_text(encoding='utf-8')
    procedure = migration.split('CREATE PROCEDURE sp_admin_cliente_list', 1)[1]
    procedure = procedure.split('CREATE PROCEDURE sp_admin_cliente_create', 1)[0]
    assert 'CALL sp_admin_cliente_list($1)' in serialized
    assert 'is_meta' in serialized
    assert 'JSON_ARRAYAGG' not in procedure
    assert "status = 'Ativo'" not in procedure
    for field in ('cnpj_cpf', 'whatsapp', 'telefone', 'status', 'email', 'emails'):
        assert field in procedure
    assert 'WHERE e_primary.cliente_id = c.id' in procedure
    assert 'ORDER BY e_primary.id' in procedure
    assert 'MIN(e.email) AS email' not in procedure


def test_list_workflow_ignores_call_status_packet() -> None:
    # O CALL devolve, depois do result set, um pacote de status sem is_meta;
    # tratá-lo como cliente gerou uma linha vazia na publicação de 03/10/2026.
    workflow = _workflow(LIST_WORKFLOW)
    code = next(
        node['parameters']['jsCode']
        for node in workflow['nodes']
        if node['name'] == 'Normalizar Resultado'
    )
    assert "Number(value.is_meta || 0) === 0" not in code
    assert "hasOwnProperty.call(value, 'is_meta') && Number(value.is_meta) === 0" in code
    assert 'value.id != null' in code


def test_edit_migration_authenticates_actor_and_handles_nullable_status() -> None:
    migration = EDIT_UP.read_text(encoding='utf-8')
    procedure = migration.split('CREATE PROCEDURE sp_admin_cliente_update', 1)[1]
    assert 'security_sessoes_funcionarios' in procedure
    assert 'SHA2(p_admin_token, 256)' in procedure
    assert 'p_funcionario_id' not in procedure
    assert 'v_cliente_encontrado' in procedure
    assert 'IF v_cliente_encontrado IS NULL THEN' in procedure
    assert 'IF v_status_anterior IS NULL THEN' not in procedure
    assert "COALESCE(v_status_anterior, '') <> 'Ativo'" in procedure
    assert 'UPDATE security_sessoes_clientes' in procedure
    assert 'UPDATE security_password_reset_clientes' in procedure


def test_edit_workflow_matches_lovable_contract() -> None:
    workflow = _workflow(EDIT_WORKFLOW)
    serialized = json.dumps(workflow, ensure_ascii=False)
    webhook = next(node for node in workflow['nodes'] if node['name'] == 'Receber Edicao')
    assert webhook['parameters']['httpMethod'] == 'POST'
    assert webhook['parameters']['path'] == 'admin/editar-cliente-v2'
    for field in (
        'cliente_id', 'nome_cliente', 'cnpj_cpf', 'status', 'email',
        'whatsapp', 'telefone',
    ):
        assert field in serialized
    assert 'funcionario_id' not in serialized
    assert 'authorization' in serialized
    assert 'CALL sp_admin_cliente_update($1, $2, $3, $4, $5, $6, $7, $8)' in serialized
    assert 'Math.random' not in serialized


def test_reset_workflow_uses_fragment_and_neutral_response() -> None:
    workflow = _workflow(RESET_WORKFLOW)
    serialized = json.dumps(workflow, ensure_ascii=False)
    assert '/redefinir-senha#token=' in serialized
    assert '/redefinir-senha?token=' not in serialized
    assert 'Se o e-mail existir e estiver ativo' in serialized
    assert 'Math.random' not in serialized


def test_cors_is_not_wildcard() -> None:
    for path in (CREATE_WORKFLOW, LIST_WORKFLOW, RESET_WORKFLOW, EDIT_WORKFLOW):
        serialized = json.dumps(_workflow(path), ensure_ascii=False)
        assert 'Access-Control-Allow-Origin' in serialized
        assert '"value": "*"' not in serialized


def test_rollback_removes_only_objects_from_this_package() -> None:
    rollback = DOWN.read_text(encoding='utf-8')
    assert 'DROP TABLE IF EXISTS security_password_reset_clientes' in rollback
    assert 'DROP TABLE IF EXISTS security_sessoes_clientes' not in rollback
    assert 'DROP COLUMN IF EXISTS documento_fiscal_canonico' in rollback
    assert 'DROP TABLE IF EXISTS clientes;' not in rollback
    assert 'DROP TABLE IF EXISTS clientes_emails_autorizados' not in rollback

    edit_rollback = EDIT_DOWN.read_text(encoding='utf-8')
    assert 'DROP PROCEDURE IF EXISTS sp_admin_cliente_update' in edit_rollback
    assert 'DROP COLUMN IF EXISTS telefone' in edit_rollback
    assert 'DROP TABLE' not in edit_rollback


def test_authorization_migration_is_fail_closed_and_centralized() -> None:
    migration = AUTH_UP.read_text(encoding='utf-8')
    assert 'CREATE PROCEDURE sp_admin_client_authorize' in migration
    assert "p_result = 'unauthorized'" in migration
    assert "p_result = 'forbidden'" in migration
    assert "IN ('administrador', 'admin')" in migration
    assert 'FROM permissoes_funcionario_modulos' in migration
    assert 'permitido' in migration
    assert "'client_action_forbidden'" in migration
    assert "BINARY LOWER(TRIM(COALESCE(p_cargo, '')))" in migration
    for action in ('visualizar', 'criar', 'editar'):
        assert f"'clientes', '{action}'" in migration


def test_sensitive_identity_change_policy_and_minimal_audit() -> None:
    migration = AUTH_UP.read_text(encoding='utf-8')
    update = migration.split('CREATE PROCEDURE sp_admin_cliente_update', 1)[1]
    assert 'IF (v_email_changed' in update
    assert 'v_documento_anterior IS NULL' in update
    assert "COALESCE(v_status_anterior, '') = 'Lead'" in update
    assert "NOT IN ('administrador', 'admin')" in update
    assert "'email_changed'" in update
    assert "'document_changed'" in update
    assert "JSON_OBJECT('request_id', v_request_id)" in update
    assert "'previous_hash'" not in update
    assert "'new_hash'" not in update
    assert 'SHA2(v_email_anterior, 256)' not in update
    assert 'SHA2(v_documento_anterior, 256)' not in update


def test_email_change_revokes_sessions_and_pending_links() -> None:
    migration = AUTH_UP.read_text(encoding='utf-8')
    update = migration.split('CREATE PROCEDURE sp_admin_cliente_update', 1)[1]
    email_branch = update.split('IF v_email_changed THEN', 1)[1]
    email_branch = email_branch.split('END IF;', 1)[0]
    assert 'UPDATE security_sessoes_clientes' in email_branch
    assert 'UPDATE security_password_reset_clientes' in email_branch
    assert 'revogado_em = UTC_TIMESTAMP()' in email_branch


def test_permission_fixture_matches_verified_runtime_shape() -> None:
    schema = BASE_SCHEMA.read_text(encoding='utf-8')
    table = schema.split('CREATE TABLE permissoes_funcionario_modulos', 1)[1]
    table = table.split(') ENGINE=', 1)[0]
    for column in (
        'id INT(11) NOT NULL AUTO_INCREMENT',
        'funcionario_id INT(11) NOT NULL',
        'modulo VARCHAR(50) NOT NULL',
        'acao VARCHAR(20) NOT NULL',
        'permitido TINYINT(1) NOT NULL DEFAULT 1',
        'criado_em DATETIME NULL DEFAULT CURRENT_TIMESTAMP()',
        'atualizado_em DATETIME NULL DEFAULT CURRENT_TIMESTAMP()',
    ):
        assert column in table
    assert 'UNIQUE KEY uk_func_modulo_acao (funcionario_id, modulo, acao)' in table
    assert 'KEY idx_func_id (funcionario_id)' in table
    for role in (
        'Administrador', 'Admin', 'Operador', 'Auditor', 'Desconhecido',
        'Admín', "' ADMIN '", 'Cargo Vazio', 'Cargo Espacos',
    ):
        assert role in schema


def test_workflows_map_authentication_and_authorization_statuses() -> None:
    for path in (CREATE_WORKFLOW, LIST_WORKFLOW, EDIT_WORKFLOW):
        serialized = json.dumps(_workflow(path), ensure_ascii=False)
        assert "result === 'unauthorized' ? 401" in serialized
        assert "result === 'forbidden' ? 403" in serialized


def test_create_and_edit_forward_empty_token_to_unauthorized_procedure_result() -> None:
    for path in (CREATE_WORKFLOW, EDIT_WORKFLOW):
        serialized = json.dumps(_workflow(path), ensure_ascii=False)
        assert "if (!adminToken) throw" not in serialized
        assert "if (!adminToken) return" in serialized
        assert "admin_token: adminToken" in serialized


def test_set_folder_revalidates_create_permission() -> None:
    migration = AUTH_UP.read_text(encoding='utf-8')
    procedure = migration.split('CREATE PROCEDURE sp_admin_cliente_set_folder', 1)[1]
    procedure = procedure.split('CREATE PROCEDURE sp_admin_cliente_list', 1)[0]
    assert 'CALL sp_admin_client_authorize' in procedure
    assert "'clientes', 'criar'" in procedure


def test_list_rollback_workflow_is_previous_version() -> None:
    rollback = _workflow(LIST_ROLLBACK_WORKFLOW)
    serialized = json.dumps(rollback, ensure_ascii=False)
    assert "SELECT f.id FROM security_sessoes_funcionarios" in serialized
    assert "CALL sp_admin_cliente_list" not in serialized
    assert rollback['active'] is False


def test_authorization_rollback_restores_previous_procedures() -> None:
    rollback = AUTH_DOWN.read_text(encoding='utf-8')
    assert 'DROP PROCEDURE IF EXISTS sp_admin_client_authorize' in rollback
    assert 'DROP PROCEDURE IF EXISTS sp_admin_cliente_list' in rollback
    assert 'CREATE PROCEDURE sp_admin_cliente_create' in rollback
    assert 'CREATE PROCEDURE sp_admin_cliente_update' in rollback
    assert 'CREATE PROCEDURE sp_admin_cliente_set_folder' in rollback
    assert 'permissoes_funcionario_modulos' not in rollback
    assert 'client_action_forbidden' not in rollback
    assert 'DROP TABLE' not in rollback


def test_ci_runs_disposable_mariadb_authorization_validation() -> None:
    ci = CI_WORKFLOW.read_text(encoding='utf-8')
    script = VALIDATION_SCRIPT.read_text(encoding='utf-8')
    assert 'bash scripts/validate_system_a_client_management.sh' in ci
    for migration in ('001_up.sql', '002_up.sql', '003_up.sql', '003_down.sql'):
        assert migration in script
    assert 'CLIENT_MANAGEMENT_AUTHORIZATION_TESTS=PASS' in script
    assert 'CLIENT_MANAGEMENT_AUDIT_TESTS=PASS' in script


def test_mariadb_wait_requires_authenticated_tcp_query_and_fails_closed() -> None:
    script = VALIDATION_SCRIPT.read_text(encoding='utf-8')
    wait = script.split('DB_READY=false', 1)[1].split('db() {', 1)[0]
    assert 'mariadb-admin' not in wait
    assert '--protocol=tcp --host=127.0.0.1' in wait
    assert "--execute='SELECT 1'" in wait
    assert 'DB_READY=true' in wait
    assert 'if [[ "${DB_READY}" != true ]]' in wait
    assert 'MARIADB_READY_TIMEOUT' in wait
    assert 'docker logs --tail 50 "${CONTAINER}"' in wait
    assert 'exit 1' in wait


def test_validation_resolves_seeded_employee_ids_and_reports_assertion_context() -> None:
    script = VALIDATION_SCRIPT.read_text(encoding='utf-8')
    schema = BASE_SCHEMA.read_text(encoding='utf-8')

    employee_lookups = {
        'administrator_id': 'administrator@example.invalid',
        'admin_id': 'admin@example.invalid',
        'operator_allowed_id': 'operator-allowed@example.invalid',
    }
    for variable, email in employee_lookups.items():
        assert email in schema
        expected_lookup = (
            f'{variable}="$(db "SELECT id FROM funcionarios '
            f"WHERE email='{email}';\")\""
        )
        assert expected_lookup in script
        assert f'funcionario_id=${{{variable}}}' in script

    assert re.search(r'funcionario_id\s*=\s*\d+', script) is None
    audit_assertions = [
        line for line in script.splitlines()
        if line.startswith('assert_scalar "SELECT COUNT(*) FROM logs_auditoria')
        and 'funcionario_id=' in line
    ]
    assert len(audit_assertions) == 3
    assert all('funcionario_id=${' in line for line in audit_assertions)

    assert 'local label="$3"' in script
    assert 'ASSERT_CONTAINS_FAILED label=${label}' in script
    assert 'ASSERT_SCALAR_FAILED query=${query}' in script


def test_prepublication_verification_covers_collations_indexes_and_grants() -> None:
    verification = VERIFY_SQL.read_text(encoding='utf-8')
    assert 'DEFAULT_COLLATION_NAME' in verification
    assert "COLUMN_NAME IN ('cargo', 'status')" in verification
    assert "COLUMN_NAME IN ('modulo', 'acao')" in verification
    assert "TABLE_NAME = 'security_sessoes_funcionarios'" in verification
    assert 'lembrete_show_grants_n8n' in verification
    assert 'SHOW GRANTS' in verification
