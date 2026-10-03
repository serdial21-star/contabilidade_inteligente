import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ASSET_DIR = ROOT / 'docs' / 'integration' / 'system_a_session_logout'
UP = ASSET_DIR / '004_up.sql'
DOWN = ASSET_DIR / '004_down.sql'
VERIFY = ASSET_DIR / 'verify_004.sql'
WORKFLOWS = {
    'sp_funcionario_logout': ASSET_DIR / 'n8n_admin_logout_v1.json',
    'sp_cliente_logout': ASSET_DIR / 'n8n_client_logout_v1.json',
}
VALIDATION_SCRIPT = ROOT / 'scripts' / 'validate_system_a_client_management.sh'
LOVABLE_PROMPT = ASSET_DIR / 'LOVABLE_PROMPT.md'


def _procedure(name: str) -> str:
    migration = UP.read_text(encoding='utf-8')
    body = migration.split(f'CREATE PROCEDURE {name}(', 1)[1]
    return body.split('END$$', 1)[0]


def test_logout_procedures_revoke_only_the_presented_live_session() -> None:
    for name, table in (
        ('sp_funcionario_logout', 'security_sessoes_funcionarios'),
        ('sp_cliente_logout', 'security_sessoes_clientes'),
    ):
        body = _procedure(name)
        assert 'SQL SECURITY INVOKER' in body
        assert "NOT REGEXP '^[0-9A-Za-z]{20,128}$'" in body
        assert 'WHERE token_hash = v_hash' in body
        assert 'AND revogado_em IS NULL' in body
        assert 'AND expira_em > UTC_TIMESTAMP()' in body
        assert (
            f'UPDATE {table}\n           SET revogado_em = UTC_TIMESTAMP()\n'
            '         WHERE id = v_sessao_id'
        ) in body
        assert 'NOW()' not in body


def test_logout_hash_uses_the_collation_of_each_token_column() -> None:
    # Producao: sessoes de funcionario em utf8mb4_unicode_ci e de cliente em
    # utf8mb4_uca1400_ai_ci (conferido em 03/10/2026); misturar gera erro 1267.
    assert (
        'v_hash CHAR(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci'
        in _procedure('sp_funcionario_logout')
    )
    assert (
        'v_hash CHAR(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_uca1400_ai_ci'
        in _procedure('sp_cliente_logout')
    )
    verify = VERIFY.read_text(encoding='utf-8')
    assert "AND COLLATION_NAME = 'utf8mb4_unicode_ci' THEN 'OK'" in verify
    assert "AND COLLATION_NAME = 'utf8mb4_uca1400_ai_ci' THEN 'OK'" in verify


def test_logout_result_is_identical_and_audit_is_minimal() -> None:
    for name, action in (
        ('sp_funcionario_logout', 'employee_logout'),
        ('sp_cliente_logout', 'client_logout'),
    ):
        body = _procedure(name)
        assert body.count("SELECT TRUE AS success, 'logged_out' AS result;") == 2
        revocation = body.split('IF v_sessao_id IS NOT NULL THEN', 1)[1]
        audit = revocation.split('INSERT INTO logs_auditoria', 1)[1]
        assert f"'{action}'" in audit
        assert "JSON_OBJECT('request_id', v_request_id)" in audit
        assert 'p_token' not in audit and 'v_hash' not in audit
        assert 'ROLLBACK;' in body and 'COMMIT;' in body


def test_logout_rollback_removes_only_its_procedures() -> None:
    statements = [
        line for line in DOWN.read_text(encoding='utf-8').splitlines()
        if line.strip() and not line.startswith('--')
    ]
    assert statements == [
        'DROP PROCEDURE IF EXISTS sp_funcionario_logout;',
        'DROP PROCEDURE IF EXISTS sp_cliente_logout;',
    ]


def test_logout_workflows_are_thin_neutral_and_do_not_retain_data() -> None:
    for procedure, path in WORKFLOWS.items():
        workflow = json.loads(path.read_text(encoding='utf-8'))
        nodes = {node['name']: node for node in workflow['nodes']}
        serialized = json.dumps(workflow, ensure_ascii=False)
        assert workflow['active'] is False
        assert workflow['settings']['saveDataSuccessExecution'] == 'none'
        assert workflow['settings']['saveDataErrorExecution'] == 'none'
        assert 'credentials' not in serialized
        assert '"*"' not in serialized
        token_code = nodes['Extrair Token']['parameters']['jsCode']
        assert r'/^Bearer\s+([A-Za-z0-9]{20,128})$/i' in token_code
        query = nodes['Revogar Sessao']['parameters']
        assert query['query'] == f'CALL {procedure}($1);'
        assert query['options']['queryReplacement'] == '={{ [$json.token] }}'
        assert nodes['Responder Sucesso']['parameters']['responseBody'] == '={{ { success: true } }}'
        assert nodes['POST Logout']['parameters']['httpMethod'] == 'POST'


def test_ci_executes_logout_procedures_and_rollback() -> None:
    script = VALIDATION_SCRIPT.read_text(encoding='utf-8')
    assert 'apply_logout_sql 004_up.sql' in script
    assert 'apply_logout_sql 004_down.sql' in script
    assert 'revoked employee session cannot list' in script
    assert 'other session of same employee keeps working' in script
    assert 'SESSION_LOGOUT_TESTS=PASS' in script


def test_lovable_prompt_never_blocks_local_logout() -> None:
    prompt = LOVABLE_PROMPT.read_text(encoding='utf-8')
    assert 'finally' in prompt
    assert 'NUNCA pode depender da resposta do servidor' in prompt
    assert 'admin/logout-v1' in prompt and 'cliente/logout-v1' in prompt
