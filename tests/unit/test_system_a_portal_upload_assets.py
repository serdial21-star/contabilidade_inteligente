import json
from pathlib import Path

BASE = Path(__file__).resolve().parents[2] / 'docs/integration/system_a_portal_upload'


def _load(name: str) -> dict:
    return json.loads((BASE / name).read_text(encoding='utf-8'))


def test_upload_patch_changes_only_preparation_and_insert() -> None:
    before = {n['name']: n['parameters'] for n in _load('baseline/n8n_portal_receber_arquivo_v2.json')['nodes']}
    patched = _load('n8n_portal_receber_arquivo_v2_observacao.json')
    after = {n['name']: n['parameters'] for n in patched['nodes']}
    assert set(before) == set(after)
    assert sorted(name for name in before if before[name] != after[name]) == ['3.5. Preparar Anexo', '5. Registar Documento']
    assert patched['active'] is False
    assert patched['settings']['saveDataSuccessExecution'] == 'none'
    assert patched['settings']['saveDataErrorExecution'] == 'none'


def test_insert_is_parameterized_and_stores_observation() -> None:
    nodes = {n['name']: n['parameters'] for n in _load('n8n_portal_receber_arquivo_v2_observacao.json')['nodes']}
    insert = nodes['5. Registar Documento']
    # Nenhum valor vindo do cliente é concatenado no SQL (antes: titulo, area e nome do arquivo interpolados).
    assert '{{' not in insert['query']
    assert 'observacao_cliente' in insert['query']
    assert all(f'${i}' in insert['query'] for i in range(1, 9))
    assert insert['options']['queryReplacement'].count('Formatador Binário') == 7
    assert '.item.json' in insert['options']['queryReplacement']
    code = nodes['3.5. Preparar Anexo']['jsCode']
    assert 'observacao_cliente: observacao' in code
    assert 'slice(0, 2000)' in code
