import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ASSET_DIR = ROOT / 'docs' / 'integration' / 'system_a_icms_apuracao'
PARSER = ASSET_DIR / 'raicms_parser.js'
WORKFLOW = ASSET_DIR / 'n8n_ferramentas_ia_apuracao_icms_v10_csv_pdf_texto.json'
CI = ROOT / '.github' / 'workflows' / 'ci.yml'


def _workflow() -> dict[str, object]:
    return json.loads(WORKFLOW.read_text(encoding='utf-8'))


def _node(workflow: dict[str, object], name: str) -> dict[str, object]:
    return next(node for node in workflow['nodes'] if node['name'] == name)


def _targets(workflow: dict[str, object], source: str, output: int = 0) -> list[str]:
    outputs = workflow['connections'][source]['main']
    if len(outputs) <= output or outputs[output] is None:
        return []
    return [connection['node'] for connection in outputs[output]]


def test_parser_is_exact_code_node_and_avoids_monetary_float_conversion() -> None:
    workflow = _workflow()
    parser = PARSER.read_text(encoding='utf-8')
    code = _node(workflow, '1. Extrator e Consolidador')['parameters']['jsCode']

    assert code == parser
    assert 'parseFloat' not in parser
    assert re.search(r'\bNumber\s*\(', parser) is None
    assert 'parseMoneyToCents' in parser
    assert '9007199254740991' in parser


def test_authorization_and_original_binary_precede_all_parsing() -> None:
    workflow = _workflow()
    assert _targets(workflow, 'Webhook Lovable') == [
        'Preparar Autorizacao',
        'Liberar Upload Autorizado',
    ]
    assert _targets(workflow, 'Autorizado?', 0) == ['Liberar Upload Autorizado']
    assert _targets(workflow, 'Autorizado?', 1) == ['Responder Autorizacao']
    assert _targets(workflow, 'Liberar Upload Autorizado') == ['Detectar Tipo de Arquivo']
    merge = _node(workflow, 'Liberar Upload Autorizado')
    assert merge['parameters']['mode'] == 'chooseBranch'
    assert merge['parameters']['useDataOfInput'] == 1


def test_pdf_is_detected_by_signature_and_uses_native_extractor() -> None:
    workflow = _workflow()
    detector = _node(workflow, 'Detectar Tipo de Arquivo')['parameters']['jsCode']
    assert "buffer.subarray(0, 5).toString('ascii') === '%PDF-'" in detector
    assert _targets(workflow, 'Arquivo PDF?', 0) == ['Extrair Texto do PDF']
    assert _targets(workflow, 'Arquivo PDF?', 1) == ['1. Extrator e Consolidador']

    extractor = _node(workflow, 'Extrair Texto do PDF')
    assert extractor['type'] == 'n8n-nodes-base.extractFromFile'
    assert extractor['parameters']['operation'] == 'pdf'
    assert extractor['parameters']['binaryPropertyName'] == '={{ $json.binary_key }}'
    assert extractor['parameters']['options']['joinPages'] is False
    assert 'maxPages' not in extractor['parameters']['options']
    assert extractor['onError'] == 'continueRegularOutput'
    assert _targets(workflow, 'Extrair Texto do PDF') == ['Preparar Texto do PDF']
    assert _targets(workflow, 'Preparar Texto do PDF') == ['1. Extrator e Consolidador']
    preparer = _node(workflow, 'Preparar Texto do PDF')['parameters']['jsCode']
    assert 'Array.isArray(item.json.text)' in preparer


def test_failed_validation_can_only_respond_422_without_effects() -> None:
    workflow = _workflow()
    assert _targets(workflow, '1. Extrator e Consolidador') == ['Conferencia valida?']
    assert _targets(workflow, 'Conferencia valida?', 0) == ['2. Copiar Planilha Modelo']
    assert _targets(workflow, 'Conferencia valida?', 1) == [
        'Responder Arquivo Nao Conferido',
    ]
    response = _node(workflow, 'Responder Arquivo Nao Conferido')
    assert response['type'] == 'n8n-nodes-base.respondToWebhook'
    assert '$json.semMovimentacao === true ? 200 : 422' in response['parameters']['options']['responseCode']
    assert 'divergencias' in response['parameters']['responseBody']
    assert 'O arquivo não pôde ser conferido' in response['parameters']['responseBody']
    condition = _node(workflow, 'Conferencia valida?')['parameters']['conditions']['boolean'][0]
    assert '$json.gerarPlanilha === true' in condition['value1']
    assert 'Responder Arquivo Nao Conferido' not in workflow['connections']


def test_workflow_remains_inactive_sanitized_and_non_retaining() -> None:
    workflow = _workflow()
    assert workflow['active'] is False
    assert all('credentials' not in node for node in workflow['nodes'])
    assert workflow['settings']['saveDataErrorExecution'] == 'none'
    assert workflow['settings']['saveDataSuccessExecution'] == 'none'
    assert workflow['settings']['saveManualExecutions'] is False
    assert workflow['settings']['saveExecutionProgress'] is False
    serialized = json.dumps(workflow, ensure_ascii=False)
    assert 'Access-Control-Allow-Origin' in serialized
    assert 'https://serdial21.com' in serialized
    assert '"value": "*"' not in serialized


def test_ci_runs_node_parser_tests_on_declared_runtime() -> None:
    ci = CI.read_text(encoding='utf-8')
    assert 'actions/setup-node@v4' in ci
    assert "node-version: '22'" in ci
    assert 'node --test docs/integration/system_a_icms_apuracao/raicms_parser.test.js' in ci
