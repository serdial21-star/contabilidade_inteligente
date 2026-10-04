import copy
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ASSET_DIR = ROOT / 'docs' / 'integration' / 'system_a_webhook_hardening'
BASELINE_DIR = ASSET_DIR / 'baseline'
UP = ASSET_DIR / '005_up.sql'
DOWN = ASSET_DIR / '005_down.sql'
VERIFY = ASSET_DIR / 'verify_005.sql'
UPLOAD = ASSET_DIR / 'n8n_admin_upload_xml_v7_hardened.json'
APURACAO = ASSET_DIR / 'n8n_ferramentas_ia_apuracao_icms_v9_hardened.json'
HONORARIOS = ASSET_DIR / 'n8n_portal_honorarios_v2_hardened.json'
CND = ASSET_DIR / 'n8n_admin_integracao_cnd_v1_hardened.json'
MOTOR = ASSET_DIR / 'n8n_gerador_obrigacoes_auto_v1_cron_only.json'
PROMPT = ASSET_DIR / 'LOVABLE_PROMPT.md'
COLAB = ASSET_DIR / 'COLAB_SNIPPET.md'
RUNBOOK = ROOT / 'docs' / 'integration' / 'SYSTEM_A_WEBHOOK_HARDENING_RUNBOOK.md'
VALIDATION_SCRIPT = ROOT / 'scripts' / 'validate_system_a_client_management.sh'


def _workflow(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding='utf-8'))


def _node(workflow: dict[str, object], name: str) -> dict[str, object]:
    return next(node for node in workflow['nodes'] if node['name'] == name)


def _connections(
    workflow: dict[str, object], source: str, output: int = 0,
) -> list[dict[str, object]]:
    outputs = workflow['connections'][source]['main']
    if len(outputs) <= output or outputs[output] is None:
        return []
    return outputs[output]


def _targets(workflow: dict[str, object], source: str, output: int = 0) -> list[str]:
    return [connection['node'] for connection in _connections(workflow, source, output)]


def test_generic_authorization_is_fail_closed_and_audited() -> None:
    migration = UP.read_text(encoding='utf-8')
    assert 'CREATE PROCEDURE sp_admin_module_authorize' in migration
    assert 'SQL SECURITY INVOKER' in migration
    assert "NOT REGEXP '^[0-9A-Za-z]{20,128}$'" in migration
    assert 's.expira_em > UTC_TIMESTAMP()' in migration
    assert 's.revogado_em IS NULL' in migration
    assert "f.status = 'Ativo'" in migration
    assert "BINARY LOWER(TRIM(COALESCE(v_cargo, '')))" in migration
    assert "IN ('administrador', 'admin')" in migration
    assert 'FROM permissoes_funcionario_modulos' in migration
    assert "SET v_result = 'forbidden'" in migration
    assert "'employee_module_action_forbidden'" in migration
    assert "'request_id', v_request_id" in migration
    assert 'p_admin_token' not in migration.split('JSON_OBJECT(', 1)[1]


def test_migration_005_rollback_and_preflight_are_scoped() -> None:
    rollback = DOWN.read_text(encoding='utf-8')
    assert rollback.count('DROP PROCEDURE IF EXISTS') == 1
    assert 'sp_admin_module_authorize' in rollback
    assert 'DROP TABLE' not in rollback
    assert 'DELETE FROM' not in rollback

    verification = VERIFY.read_text(encoding='utf-8')
    assert 'utf8mb4_unicode_ci' in verification
    assert "TABLE_NAME = 'security_sessoes_funcionarios'" in verification
    assert "ROUTINE_NAME = 'sp_admin_module_authorize'" in verification
    assert 'lembrete_show_grants_n8n' in verification


def test_all_workflows_are_inactive_sanitized_and_do_not_retain_data() -> None:
    for path in (UPLOAD, APURACAO, HONORARIOS, CND, MOTOR):
        workflow = _workflow(path)
        assert workflow['active'] is False
        assert all('credentials' not in node for node in workflow['nodes'])
        settings = workflow['settings']
        assert settings['saveDataErrorExecution'] == 'none'
        assert settings['saveDataSuccessExecution'] == 'none'
        assert settings['saveManualExecutions'] is False
        assert settings['saveExecutionProgress'] is False
        assert settings['availableInMCP'] is False


def test_upload_authorizes_before_client_lookup_drive_or_write() -> None:
    workflow = _workflow(UPLOAD)
    assert _targets(workflow, 'Receber XML') == [
        'Preparar Autorizacao',
        'Liberar Upload Autorizado',
    ]
    assert _connections(workflow, 'Receber XML')[1]['index'] == 0
    assert _targets(workflow, 'Preparar Autorizacao') == ['Autorizar Ferramenta IA']
    assert _targets(workflow, 'Autorizar Ferramenta IA') == ['Normalizar Autorizacao']
    assert _targets(workflow, 'Normalizar Autorizacao') == ['Autorizado?']
    assert _targets(workflow, 'Autorizado?', 0) == ['Cliente ID valido?']
    assert _targets(workflow, 'Autorizado?', 1) == ['Responder Autorizacao']
    assert _targets(workflow, 'Cliente ID valido?', 0) == ['Confirmar Cliente Existente']
    assert _targets(workflow, 'Cliente ID valido?', 1) == ['Responder Cliente Invalido']
    assert _targets(workflow, 'Cliente existe?', 0) == ['Liberar Upload Autorizado']
    assert _connections(workflow, 'Cliente existe?', 0)[0]['index'] == 1
    assert _targets(workflow, 'Cliente existe?', 1) == ['Responder Cliente Ausente']
    assert _targets(workflow, 'Liberar Upload Autorizado') == ['Separar XMLs']

    merge = _node(workflow, 'Liberar Upload Autorizado')
    assert merge['type'] == 'n8n-nodes-base.merge'
    assert merge['parameters'] == {
        'mode': 'chooseBranch',
        'numberInputs': 2,
        'chooseBranchMode': 'waitForAll',
        'output': 'specifiedInput',
        'useDataOfInput': 1,
    }
    assert 'cliente_id bruto' in merge['notes']
    assert '^[1-9][0-9]*$' in merge['notes']

    serialized = json.dumps(workflow, ensure_ascii=False)
    assert 'ferramentas_ia' in serialized
    assert 'criar' in serialized
    assert "result === 'forbidden' ? 403 : 401" in serialized
    assert "responseCode\":  400" in UPLOAD.read_text(encoding='utf-8')
    assert "responseCode\":  404" in UPLOAD.read_text(encoding='utf-8')


def test_apuracao_authorizes_before_file_drive_and_sheets() -> None:
    workflow = _workflow(APURACAO)
    assert _targets(workflow, 'Webhook Lovable') == [
        'Preparar Autorizacao',
        'Liberar Upload Autorizado',
    ]
    assert _connections(workflow, 'Webhook Lovable')[1]['index'] == 0
    assert _targets(workflow, 'Preparar Autorizacao') == ['Autorizar Ferramenta IA']
    assert _targets(workflow, 'Autorizar Ferramenta IA') == ['Normalizar Autorizacao']
    assert _targets(workflow, 'Normalizar Autorizacao') == ['Autorizado?']
    assert _targets(workflow, 'Autorizado?', 0) == ['Liberar Upload Autorizado']
    assert _connections(workflow, 'Autorizado?', 0)[0]['index'] == 1
    assert _targets(workflow, 'Autorizado?', 1) == ['Responder Autorizacao']
    assert _targets(workflow, 'Liberar Upload Autorizado') == [
        '1. Extrator e Consolidador',
    ]
    merge = _node(workflow, 'Liberar Upload Autorizado')
    assert merge['type'] == 'n8n-nodes-base.merge'
    assert merge['parameters'] == {
        'mode': 'chooseBranch',
        'numberInputs': 2,
        'chooseBranchMode': 'waitForAll',
        'output': 'specifiedInput',
        'useDataOfInput': 1,
    }
    auth_response = json.dumps(_node(workflow, 'Responder Autorizacao'))
    assert "forbidden' ? 403 : 401" in auth_response


def test_upload_code_nodes_do_not_restore_cross_node_binary_data() -> None:
    cross_node_binary = re.compile(r'\$\([^)]*\)(?:\.first\(\))?\.binary\b')

    for path in (UPLOAD, APURACAO):
        workflow = _workflow(path)
        assert all(node['name'] != 'Restaurar Upload Autorizado' for node in workflow['nodes'])
        for node in workflow['nodes']:
            if node['type'] != 'n8n-nodes-base.code':
                continue
            code = node['parameters']['jsCode']
            assert cross_node_binary.search(code) is None
            assert '.first().binary' not in code


def test_upload_accepts_single_and_indexed_xml_binary_fields() -> None:
    workflow = _workflow(UPLOAD)
    code = _node(workflow, 'Separar XMLs')['parameters']['jsCode']

    field_pattern = re.compile(r'^arquivos\d*$', re.IGNORECASE)
    assert '/^arquivos\\d*$/i.test(key)' in code
    assert field_pattern.fullmatch('arquivos')
    assert field_pattern.fullmatch('arquivos0')
    assert field_pattern.fullmatch('arquivos12')
    assert field_pattern.fullmatch('arquivo') is None
    assert field_pattern.fullmatch('arquivos12extra') is None


def test_all_changed_mysql_queries_bind_request_values() -> None:
    for path in (UPLOAD, APURACAO, HONORARIOS, CND):
        workflow = _workflow(path)
        for node in workflow['nodes']:
            if node['type'] != 'n8n-nodes-base.mySql':
                continue
            query = node['parameters']['query']
            assert '{{' not in query
            if '$' in query:
                assert 'queryReplacement' in node['parameters']['options']


def test_honorarios_rejects_revoked_session_and_uses_session_client() -> None:
    workflow = _workflow(HONORARIOS)
    validation = _node(workflow, 'SQL validar token')['parameters']
    assert 'revogado_em IS NULL' in validation['query']
    assert 'expira_em > UTC_TIMESTAMP()' in validation['query']
    assert validation['options']['queryReplacement'] == '={{ [$json._token] }}'

    history = _node(workflow, 'SQL historico parcelas')['parameters']
    next_invoice = _node(workflow, 'SQL proxima fatura')['parameters']
    assert 'cliente_id = $1' in history['query']
    assert history['options']['queryReplacement'] == '={{ [$json.cliente_id] }}'
    assert 'cliente_id = $1' in next_invoice['query']
    assert "$('SQL validar token').first().json.cliente_id" in (
        next_invoice['options']['queryReplacement']
    )


def test_cnd_uses_header_auth_and_bound_cnpj_string() -> None:
    workflow = _workflow(CND)
    webhook = _node(workflow, 'Webhook - Integracao Colab')
    assert webhook['parameters']['authentication'] == 'headerAuth'
    assert 'X-Serdial21-Integration-Secret' in webhook['notes']
    assert 'credentials' not in webhook
    assert _targets(workflow, 'Webhook - Integracao Colab') == [
        'Normalizar Entrada CND',
    ]
    normalizer = _node(workflow, 'Normalizar Entrada CND')['parameters']['jsCode']
    assert "String(body.cnpj" in normalizer
    assert 'Number(body.cnpj' not in normalizer
    lookup = _node(workflow, 'MySQL - Buscar Cliente por CNPJ')['parameters']
    assert 'cnpj_cpf = $1' in lookup['query']
    assert lookup['options']['queryReplacement'] == '={{ [$json.cnpj] }}'


def test_motor_diff_removes_only_webhook_and_export_metadata() -> None:
    baseline = _workflow(BASELINE_DIR / 'n8n_gerador_obrigacoes_auto_v1.json')
    hardened = _workflow(MOTOR)

    expected_nodes = []
    for original in baseline['nodes']:
        if original['name'] == 'Webhook - Executar Manual':
            continue
        node = copy.deepcopy(original)
        node.pop('credentials', None)
        expected_nodes.append(node)

    expected_connections = copy.deepcopy(baseline['connections'])
    expected_connections.pop('Webhook - Executar Manual')
    assert hardened['nodes'] == expected_nodes
    assert hardened['connections'] == expected_connections
    assert all(node['type'] != 'n8n-nodes-base.webhook' for node in hardened['nodes'])
    cron = _node(hardened, 'Cron - Diario 06:05')
    assert cron['parameters']['triggerTimes']['item'][0]['cronExpression'] == '5 6 * * *'


def test_cors_is_restricted_in_http_responses() -> None:
    for path in (UPLOAD, APURACAO, HONORARIOS):
        serialized = json.dumps(_workflow(path), ensure_ascii=False)
        assert 'Access-Control-Allow-Origin' in serialized
        assert '"value": "*"' not in serialized
        assert 'https://serdial21.com' in serialized


def test_lovable_prompt_and_colab_snippet_cover_security_contract() -> None:
    prompt = PROMPT.read_text(encoding='utf-8')
    for required in (
        'x-app-token', 'ferramentas_ia', '`401`', '`403`',
        'path + método', '404', 'proxy-file-upload',
        'proxy-document-download', 'listar-arquivos', 'HelpdeskTicketForm',
    ):
        assert required in prompt
    assert 'verify_jwt = false' in prompt
    assert 'sem fazer `fetch`' in prompt
    assert 'modulos.ferramentas_ia.criar === true' in prompt
    assert 'Não use `admin_user`, `localStorage`' in prompt
    assert 'método efetivamente encaminhado' in prompt
    assert '_method' in prompt
    assert 'um `POST` externo permitido não pode sair do proxy como `DELETE`' in prompt
    assert 'CORS de todas as Edge Functions' in prompt
    for origin in (
        'https://serdial21.com',
        'https://www.serdial21.com',
        'https://serdialconnect-hub.lovable.app',
    ):
        assert origin in prompt
    assert 'Vary: Origin' in prompt
    assert 'Para origem ausente ou fora da allowlist, não emita' in prompt
    assert 'Não use `*`' in prompt
    assert '`authorization`, `x-app-token`, `content-type`, `apikey`, `x-client-info`' in prompt
    assert 'Trate `OPTIONS` antes da lógica de negócio' in prompt
    assert 'configuração de CORS antes e depois' in prompt

    snippet = COLAB.read_text(encoding='utf-8')
    assert 'from google.colab import userdata' in snippet
    assert 'userdata.get("SERDIAL21_CND_INTEGRATION_SECRET")' in snippet
    assert '"X-Serdial21-Integration-Secret": integration_secret' in snippet
    assert 'timeout=30' in snippet

    runbook = RUNBOOK.read_text(encoding='utf-8')
    assert 'GENERIC_TIMEZONE' in runbook
    assert '005_down.sql' in runbook
    assert 'não carregam credenciais' in runbook
    assert 'secrets.token_urlsafe(32)' in runbook
    assert 'Administrador sem linha explícita `ferramentas_ia/criar` recebe `403`' in runbook
    assert 'Liberar Upload Autorizado' in runbook
    assert 'Input 1 Data' in runbook
    assert 'Save Failed Production Executions' in runbook
    assert 'execução `36819`' in runbook
    assert 'Sem essa execução real, o ajuste de binários não está aceito.' in runbook


def test_ci_validation_includes_migration_005() -> None:
    script = VALIDATION_SCRIPT.read_text(encoding='utf-8')
    assert 'apply_hardening_sql 005_up.sql' in script
    assert 'apply_hardening_sql 005_down.sql' in script
    assert 'WEBHOOK_HARDENING_AUTHORIZATION_TESTS=PASS' in script
    assert 'WEBHOOK_HARDENING_ROLLBACK=PASS' in script
    assert 'SyntheticAccentedRoleToken11' in script
    assert "acao='employee_module_action_forbidden';\" \"7\"" in script
