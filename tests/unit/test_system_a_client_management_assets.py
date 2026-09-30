import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ASSET_DIR = ROOT / 'docs' / 'integration' / 'system_a_client_management'
UP = ASSET_DIR / '001_up.sql'
DOWN = ASSET_DIR / '001_down.sql'
CREATE_WORKFLOW = ASSET_DIR / 'n8n_admin_client_create_v3.json'
LIST_WORKFLOW = ASSET_DIR / 'n8n_admin_client_list_v2.json'
RESET_WORKFLOW = ASSET_DIR / 'n8n_client_password_recovery_v2.json'
EDIT_UP = ASSET_DIR / '002_up.sql'
EDIT_DOWN = ASSET_DIR / '002_down.sql'
EDIT_WORKFLOW = ASSET_DIR / 'n8n_admin_client_update_v1.json'


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
    query = next(
        node['parameters']['query']
        for node in workflow['nodes']
        if node['name'] == 'Buscar Todos os Clientes'
    )
    assert "status = 'Ativo'" not in query
    for field in ('cnpj_cpf', 'whatsapp', 'telefone', 'status', 'email', 'emails'):
        assert field in query


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
