import json
import shutil
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
ASSET_DIR = ROOT / 'docs' / 'integration' / 'system_a_portal_detalhes'
UP = ASSET_DIR / '006_up.sql'
DOWN = ASSET_DIR / '006_down.sql'
VERIFY = ASSET_DIR / 'verify_006.sql'
RUNBOOK = ROOT / 'docs' / 'integration' / 'SYSTEM_A_PORTAL_DETAILS_RUNBOOK.md'
PROMPT = ASSET_DIR / 'LOVABLE_PROMPT.md'
ADMIN_PATCH = ASSET_DIR / 'ADMIN_DOCUMENTOS_V2_PATCH.md'
VALIDATOR = ROOT / 'scripts' / 'validate_system_a_portal_details.sh'
CI = ROOT / '.github' / 'workflows' / 'ci.yml'
WORKFLOWS = {
    'portal/detalhe-chamado': ASSET_DIR / 'n8n_portal_detalhe_chamado.json',
    'portal/complementar-chamado': ASSET_DIR / 'n8n_portal_complementar_chamado.json',
    'portal/detalhe-documento': ASSET_DIR / 'n8n_portal_detalhe_documento.json',
    'portal/complementar-documento': ASSET_DIR / 'n8n_portal_complementar_documento.json',
}


def _workflow(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding='utf-8'))


def _node(workflow: dict[str, object], name: str) -> dict[str, object]:
    return next(node for node in workflow['nodes'] if node['name'] == name)


def _targets(workflow: dict[str, object], source: str, output: int = 0) -> list[tuple[str, int]]:
    branches = workflow['connections'][source]['main']
    if len(branches) <= output or branches[output] is None:
        return []
    return [(item['node'], item['index']) for item in branches[output]]


def _procedure(name: str) -> str:
    migration = UP.read_text(encoding='utf-8')
    return migration.split(f'CREATE PROCEDURE {name}(', 1)[1].split('END$$', 1)[0]


def test_migration_is_additive_append_only_and_cross_client_safe() -> None:
    migration = UP.read_text(encoding='utf-8')
    assert 'ADD COLUMN IF NOT EXISTS anexo_nome VARCHAR(255) NULL' in migration
    assert 'CREATE TABLE IF NOT EXISTS inbox_documentos_complementos' in migration
    assert 'FOREIGN KEY (documento_id, cliente_id)' in migration
    assert 'REFERENCES inbox_documentos (id, cliente_id)' in migration
    assert 'ON DELETE RESTRICT' in migration
    assert 'UPDATE inbox_documentos_complementos' not in migration
    assert 'DELETE FROM inbox_documentos_complementos' not in migration


def test_four_procedures_use_live_session_and_session_client() -> None:
    for name, table, resource_id in (
        ('sp_portal_detalhe_chamado', 'tickets_master', 'p_ticket_id'),
        ('sp_portal_complementar_chamado', 'tickets_master', 'p_ticket_id'),
        ('sp_portal_detalhe_documento', 'inbox_documentos', 'p_documento_id'),
        ('sp_portal_complementar_documento', 'inbox_documentos', 'p_documento_id'),
    ):
        body = _procedure(name)
        assert 'SQL SECURITY INVOKER' in body
        assert "NOT REGEXP '^[0-9A-Za-z]{20,128}$'" in body
        assert 'FROM security_sessoes_clientes' in body
        assert 'expira_em > UTC_TIMESTAMP()' in body
        assert 'revogado_em IS NULL' in body
        assert f'FROM {table}' in body
        assert f'id = {resource_id}' in body
        assert 'cliente_id = v_cliente_id' in body
        assert 'p_cliente_id' not in body
        assert "'not_found' AS result" in body


def test_complements_validate_close_state_and_audit_atomically() -> None:
    migration = UP.read_text(encoding='utf-8')
    for name, action in (
        ('sp_portal_complementar_chamado', 'client_ticket_complement'),
        ('sp_portal_complementar_documento', 'client_document_complement'),
    ):
        body = _procedure(name)
        assert 'START TRANSACTION;' in body
        assert 'FOR UPDATE;' in body
        assert 'CHAR_LENGTH(v_mensagem) > 5000' in body
        assert "(v_mensagem = '' AND p_anexo_url IS NULL)" in body
        assert "'closed' AS result" in body
        assert f"'{action}'" in body
        assert "'request_id', v_request_id" in body
        assert "'has_attachment', p_anexo_url IS NOT NULL" in body
        audit = body.split('INSERT INTO logs_auditoria', 1)[1]
        assert 'p_mensagem' not in audit and 'v_mensagem' not in audit
        assert 'COMMIT;' in body and 'ROLLBACK;' in body
    assert "IN ('concluido', 'concluído')" in migration
    assert "'processado', 'concluido', 'concluído', 'rejeitado'" in migration


def test_guarded_rollback_and_preflight_are_scoped() -> None:
    rollback = DOWN.read_text(encoding='utf-8')
    assert 'inbox_documentos_complementos LIMIT 1' in rollback
    assert 'tickets_mensagens WHERE anexo_nome IS NOT NULL' in rollback
    assert "SIGNAL SQLSTATE '45000'" in rollback
    assert 'DELETE FROM' not in rollback
    assert 'DROP TABLE inbox_documentos_complementos' in rollback
    assert 'DROP COLUMN anexo_nome' in rollback
    verification = VERIFY.read_text(encoding='utf-8')
    assert "COLLATION_NAME" in verification
    assert "TABLE_NAME = 'security_sessoes_clientes'" in verification
    assert "SECURITY_TYPE" in verification
    for procedure in (
        'sp_portal_detalhe_chamado', 'sp_portal_complementar_chamado',
        'sp_portal_detalhe_documento', 'sp_portal_complementar_documento',
    ):
        assert procedure in verification


def test_workflows_are_inactive_sanitized_and_use_exact_paths() -> None:
    for path, file in WORKFLOWS.items():
        workflow = _workflow(file)
        serialized = json.dumps(workflow, ensure_ascii=False)
        assert workflow['active'] is False
        assert 'credentials' not in serialized
        assert workflow['settings']['saveDataErrorExecution'] == 'none'
        assert workflow['settings']['saveDataSuccessExecution'] == 'none'
        assert workflow['settings']['saveManualExecutions'] is False
        assert workflow['settings']['saveExecutionProgress'] is False
        assert workflow['settings']['availableInMCP'] is False
        webhooks = [node for node in workflow['nodes'] if node['type'] == 'n8n-nodes-base.webhook']
        assert {(node['parameters']['httpMethod'], node['parameters']['path']) for node in webhooks} == {
            ('POST', path), ('OPTIONS', path),
        }
        assert '"value": "*"' not in file.read_text(encoding='utf-8')
        assert 'https://serdial21.com' in serialized


def test_response_nodes_do_not_repeat_header_names() -> None:
    for workflow_file in WORKFLOWS.values():
        workflow = _workflow(workflow_file)
        for response in (
            node for node in workflow['nodes']
            if node['type'] == 'n8n-nodes-base.respondToWebhook'
        ):
            entries = response['parameters']['options']['responseHeaders']['entries']
            names = [entry['name'].casefold() for entry in entries]
            assert len(names) == len(set(names)), (
                f'{workflow_file.name} / {response["name"]} repete cabeçalho'
            )


def test_all_mysql_calls_are_parameterized_and_use_only_authorization_token() -> None:
    for workflow_file in WORKFLOWS.values():
        workflow = _workflow(workflow_file)
        serialized = json.dumps(workflow, ensure_ascii=False)
        for sql in (node for node in workflow['nodes'] if node['type'] == 'n8n-nodes-base.mySql'):
            query = sql['parameters']['query']
            assert '{{' not in query
            assert query.startswith('CALL sp_portal_')
            assert '$1' in query
            assert 'queryReplacement' in sql['parameters']['options']
        preparation = _node(
            workflow,
            'Preparar Entrada' if 'detalhe' in workflow_file.name else 'Validar Entrada',
        )['parameters']['jsCode']
        assert 'headers.authorization' in preparation
        assert r'/^Bearer\s+([A-Za-z0-9]{20,128})$/i' in preparation
        assert 'body.token' not in preparation
        assert 'cliente_id' not in preparation
        assert 'token_hash' not in serialized


def test_detail_contract_has_chronological_complements_and_opening_attachment() -> None:
    migration = UP.read_text(encoding='utf-8')
    assert ') ORDER BY m.criado_em, m.id)' in migration
    assert ') ORDER BY x.criado_em, x.id)' in migration
    assert 'FROM evidencias_protocolos AS e' in migration
    ticket = _workflow(WORKFLOWS['portal/detalhe-chamado'])
    normalizer = _node(ticket, 'Normalizar Detalhe')['parameters']['jsCode']
    assert 'complementos: parseList(row.complementos)' in normalizer
    assert 'anexos_abertura: parseList(row.anexos_abertura)' in normalizer
    assert _node(ticket, 'Responder Detalhe')['parameters']['responseBody'] == (
        '={{ { success: true, data: $json.data } }}'
    )


def test_complement_workflows_validate_binary_before_drive_and_database() -> None:
    for kind in ('chamado', 'documento'):
        workflow = _workflow(WORKFLOWS[f'portal/complementar-{kind}'])
        code = _node(workflow, 'Validar Entrada')['parameters']['jsCode']
        assert 'message.length > 5000' in code
        assert 'bytes.length > 10 * 1024 * 1024' in code
        assert "'%PDF-'" in code
        assert "magic.startsWith('ffd8ff')" in code
        assert "magic === '89504e470d0a1a0a'" in code
        assert "originalName.replace" in code
        if kind == 'documento':
            assert "'application/xml'" in code and "!/< !DOCTYPE" not in code
            assert '!/<!DOCTYPE/i.test(textStart)' in code
        else:
            assert "const allowed = ['application/pdf', 'image/jpeg', 'image/png'];" in code
        assert _targets(workflow, 'Validar Entrada') == [
            ('Entrada valida?', 0), ('Liberar Entrada Autorizada', 0),
        ]
        assert _targets(workflow, 'Entrada valida?', 0) == [('Autorizar Recurso', 0)]
        assert _targets(workflow, 'Recurso aberto?', 0) == [('Liberar Entrada Autorizada', 1)]
        assert _targets(workflow, 'Liberar Entrada Autorizada') == [('Mapear Subpasta', 0)]
        assert _targets(workflow, 'Tem anexo?', 0) == [
            ('Buscar Subpasta Drive', 0), ('Liberar Upload', 0),
        ]
        assert _targets(workflow, 'Subpasta encontrada?', 0) == [('Liberar Upload', 1)]
        search = _node(workflow, 'Buscar Subpasta Drive')['parameters']
        assert search['returnAll'] is False and search['limit'] == 1
        folder_conditions = _node(workflow, 'Subpasta encontrada?')['parameters']['conditions']['string']
        assert folder_conditions[1] == {
            'value1': '={{ $json.name }}',
            'operation': 'equal',
            'value2': "={{ $('Mapear Subpasta').first().json.subpasta }}",
        }
        assert _targets(workflow, 'Liberar Upload') == [('Enviar Anexo ao Drive', 0)]
        assert _targets(workflow, 'Enviar Anexo ao Drive') == [('Preparar Registro com Anexo', 0)]
        assert _targets(workflow, 'Preparar Registro com Anexo') == [('Gravar Complemento', 0)]
        query = _node(workflow, 'Gravar Complemento')['parameters']['query']
        assert query == f'CALL sp_portal_complementar_{kind}($1, $2, $3, $4, $5);'
        folder_code = _node(workflow, 'Mapear Subpasta')['parameters']['jsCode']
        for folder in ('01_FISCAL', '02_PESSOAL', '03_CONTABIL', '04_SOCIETARIO', '99_DIVERSOS'):
            assert folder in folder_code


def test_admin_patch_prompt_and_runbook_cover_handoff() -> None:
    patch = ADMIN_PATCH.read_text(encoding='utf-8')
    assert 'JSON_ARRAYAGG' in patch
    assert 'x.documento_id = d.id' in patch
    assert 'x.cliente_id = d.cliente_id' in patch
    assert 'ORDER BY x.criado_em, x.id' in patch
    assert 'queryReplacement' in patch
    prompt = PROMPT.read_text(encoding='utf-8')
    for required in (
        '/portal/detalhe-chamado', '/portal/complementar-chamado',
        '/portal/detalhe-documento', '/portal/complementar-documento',
        '10 MiB', '5000', 'AdminDocumentos', '401', '404', '409', '422',
    ):
        assert required in prompt
    runbook = RUNBOOK.read_text(encoding='utf-8')
    assert '16 MiB' in runbook and '13,34 MiB' in runbook
    assert '256 MB' in runbook
    assert 'dois clientes sintéticos A e B' in runbook
    assert 'Save successful production executions' in runbook
    assert '006_down.sql' in runbook
    assert 'SELECT status, COUNT(*)\n   FROM tickets_master' in runbook
    assert 'SELECT status, COUNT(*)\n   FROM inbox_documentos' in runbook
    assert '**Pare e reporte**' in runbook
    assert 'Qualquer ajuste da lista exige decisão registrada' in runbook


def test_ci_runs_mariadb_validator_with_required_scenarios() -> None:
    validator = VALIDATOR.read_text(encoding='utf-8')
    for required in (
        'mariadb:11.8.9', 'SyntheticPortalExpiredToken03',
        'SyntheticPortalRevokedToken04', 'cross-client', 'REPEAT(\'x\',5001)',
        'synthetic audit failure', '006_down.sql',
        'PORTAL_DETAILS_ISOLATION_TESTS=PASS',
        'PORTAL_DETAILS_AUDIT_ATOMICITY=PASS',
        'PORTAL_DETAILS_ROLLBACK=PASS',
    ):
        assert required in validator
    assert 'bash scripts/validate_system_a_portal_details.sh' in CI.read_text(encoding='utf-8')


@pytest.mark.skipif(shutil.which('node') is None, reason='Node.js is not installed')
def test_embedded_n8n_code_nodes_compile_in_node() -> None:
    for workflow_file in WORKFLOWS.values():
        workflow = _workflow(workflow_file)
        for code_node in (node for node in workflow['nodes'] if node['type'] == 'n8n-nodes-base.code'):
            subprocess.run(
                ['node', '-e', 'new Function(process.argv[1])', code_node['parameters']['jsCode']],
                check=True,
                capture_output=True,
                text=True,
                # Sem herdar o stdin do pai: no Windows, um stdin inválido gera WinError 6 intermitente.
                stdin=subprocess.DEVNULL,
            )


def test_admin_documentos_patch_changes_only_documents_branch() -> None:
    base_dir = Path(__file__).resolve().parents[2] / 'docs/integration/system_a_portal_detalhes'
    baseline = json.loads((base_dir / 'baseline/n8n_admin_listagens_gerais_v2.json').read_text(encoding='utf-8'))
    patched = json.loads((base_dir / 'n8n_admin_listagens_gerais_v2_t0008.json').read_text(encoding='utf-8'))
    before = {node['name']: node['parameters'] for node in baseline['nodes']}
    after = {node['name']: node['parameters'] for node in patched['nodes']}
    changed = sorted(name for name in before if before[name] != after.get(name))
    assert changed == ['Buscar Todos os Documentos']
    assert sorted(set(after) - set(before)) == ['Converter Complementos']
    query = after['Buscar Todos os Documentos']['query']
    assert 'inbox_documentos_complementos' in query
    assert 'x.cliente_id = d.cliente_id' in query
    assert patched['active'] is False
    assert patched['settings']['saveDataSuccessExecution'] == 'none'
    assert patched['settings']['saveDataErrorExecution'] == 'none'
