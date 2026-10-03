import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = (
    ROOT / 'docs' / 'integration' / 'system_a_permissions'
    / 'n8n_admin_permissoes_funcionario_v2_2.json'
)


def _nodes() -> dict[str, dict[str, object]]:
    workflow = json.loads(WORKFLOW.read_text(encoding='utf-8'))
    return {node['name']: node for node in workflow['nodes']}


def test_client_access_query_runs_once_against_the_single_session_item() -> None:
    # "Buscar Módulos" devolve uma linha por permissão; sem executeOnce o nó
    # seguinte rodava por linha e pedia o item N de "Validar Sessão", que só
    # tem um item (ExpressionError em produção, 03/10/2026).
    node = _nodes()['Buscar Clientes Acesso']
    query = node['parameters']['query']
    assert node.get('executeOnce') is True
    assert "$('Validar Sessão').first().json.id" in query
    assert "$node['Validar Sessão']" not in query


def test_permission_queries_keep_flowing_when_employee_has_no_rows() -> None:
    # Sem linha de permissão o MySQL não devolve item e o fluxo parava sem
    # responder: corpo vazio e menu vazio no frontend.
    nodes = _nodes()
    assert nodes['Buscar Módulos'].get('alwaysOutputData') is True
    assert nodes['Buscar Clientes Acesso'].get('alwaysOutputData') is True
    code = nodes['Montar Permissões']['parameters']['jsCode']
    assert 'if (!modulo || !acao) continue;' in code
    assert 'if (r.cliente_id == null) continue;' in code


def test_build_permissions_code_has_balanced_braces() -> None:
    # O código não tem chaves dentro de strings, então a contagem simples
    # detecta a função fallbackPorCargo sem fechamento encontrada em produção.
    code = _nodes()['Montar Permissões']['parameters']['jsCode']
    assert code.count('{') == code.count('}')
    assert '    listas: { visualizar: true }\n  };\n}\n\nif (!hasModulos) {' in code
