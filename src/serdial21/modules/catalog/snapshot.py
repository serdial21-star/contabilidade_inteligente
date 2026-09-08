'''Compilação e leitura determinísticas do snapshot de catálogo.'''

from datetime import date
from hashlib import sha256
import json
from typing import Any
from uuid import UUID, uuid4

from serdial21.modules.chart_of_accounts.domain.entities import (
    AccountVersion, Ledger, assert_hierarchy_acyclic, assert_unique_code,
)
from serdial21.modules.catalog.domain.entities import CatalogSpec
from serdial21.modules.rules.domain.entities import AccountingRuleVersion, RuleSetRelease
from serdial21.modules.workflow.application.journey import PostingPolicy, PreparationPlan
from serdial21.modules.workflow.domain.entities import WorkflowVersion


def snapshot_hash(content: dict[str, Any]) -> str:
    encoded = json.dumps(
        content, ensure_ascii=False, sort_keys=True, separators=(',', ':'),
    ).encode('utf-8')
    return sha256(encoded).hexdigest()


def compile_snapshot(
    spec: CatalogSpec, version_no: int, *, previous: dict[str, Any] | None = None,
) -> dict[str, Any]:
    _validate_spec(spec)
    previous_accounts = {
        item['key']: item for item in (previous or {}).get('accounts', [])
    }
    previous_rules = {
        item['key']: item for item in (previous or {}).get('rules', [])
    }
    account_roots = {
        item.key: str(previous_accounts.get(item.key, {}).get('account_id') or uuid4())
        for item in spec.accounts
    }
    account_versions = {item.key: str(uuid4()) for item in spec.accounts}

    accounts = []
    domain_accounts = []
    for item in spec.accounts:
        account = {
            'id': account_versions[item.key],
            'account_id': account_roots[item.key],
            'key': item.key,
            'version_no': version_no,
            'code': item.code,
            'name': item.name,
            'nature': item.nature,
            'normal_balance': item.normal_balance,
            'parent_account_id': account_roots.get(item.parent_key),
            'is_synthetic': item.is_synthetic,
            'is_postable': item.is_postable,
            'status': 'DRAFT',
            'valid_from': spec.valid_from.isoformat(),
            'valid_to': spec.valid_to.isoformat() if spec.valid_to else None,
        }
        accounts.append(account)
        domain_accounts.append(_account_domain(account, UUID(int=0), UUID(int=0)))
    for candidate in domain_accounts:
        candidate.validate()
        assert_unique_code(candidate, tuple(domain_accounts))
        assert_hierarchy_acyclic(candidate, tuple(domain_accounts))

    rules = []
    for item in spec.rules:
        rule_id = str(previous_rules.get(item.key, {}).get('rule_id') or uuid4())
        rules.append({
            'id': str(uuid4()), 'rule_id': rule_id, 'key': item.key,
            'version_no': version_no, 'name': item.name, 'scope': item.scope,
            'conditions': [list(condition) for condition in item.conditions],
            'priority': item.priority,
            'debit_account_version_id': account_versions[item.debit_account_key],
            'credit_account_version_id': account_versions[item.credit_account_key],
            'valid_from': spec.valid_from.isoformat(),
            'valid_to': spec.valid_to.isoformat() if spec.valid_to else None,
            'status': 'DRAFT', 'automation_level': item.automation_level,
            'approved': False, 'tests_passed': item.tests_passed,
        })

    prior = previous or {}
    workflow_prior = prior.get('workflow', {})
    mapping_prior = prior.get('mapping', {})
    ledger_prior = prior.get('ledger', {})
    chart_prior = prior.get('chart', {})
    content: dict[str, Any] = {
        'schema_version': 1,
        'ledger': {
            'id': str(uuid4()),
            'ledger_id': str(ledger_prior.get('ledger_id') or uuid4()),
            'version_no': version_no, 'name': spec.ledger_name,
            'currency_code': spec.currency_code, 'status': 'DRAFT',
            'valid_from': spec.valid_from.isoformat(),
            'valid_to': spec.valid_to.isoformat() if spec.valid_to else None,
        },
        'chart': {
            'id': str(uuid4()),
            'chart_id': str(chart_prior.get('chart_id') or uuid4()),
            'version_no': version_no, 'name': spec.chart_name, 'status': 'DRAFT',
        },
        'accounts': accounts,
        'rules': rules,
        'rule_release': {
            'id': str(uuid4()), 'version_no': version_no,
            'name': f'{spec.name} v{version_no}',
            'rule_version_ids': [item['id'] for item in rules], 'status': 'DRAFT',
        },
        'mapping': {
            'id': str(uuid4()),
            'mapping_set_id': str(mapping_prior.get('mapping_set_id') or uuid4()),
            'version_no': version_no, 'name': spec.mapping_name,
            'namespace': spec.mapping_namespace, 'status': 'DRAFT',
            'valid_from': spec.valid_from.isoformat(),
            'valid_to': spec.valid_to.isoformat() if spec.valid_to else None,
            'entries': [{
                'id': str(uuid4()), 'key': item.key, 'priority': item.priority,
                'external_code': item.external_code,
                'history_contains': item.history_contains,
                'dimension_code': item.dimension_code,
                'canonical_entity': item.canonical_entity,
                'target_account_version_id': account_versions[item.target_account_key],
                'valid_from': spec.valid_from.isoformat(),
                'valid_to': spec.valid_to.isoformat() if spec.valid_to else None,
            } for item in spec.mappings],
        },
        'workflow': {
            'id': str(uuid4()),
            'definition_id': str(workflow_prior.get('definition_id') or uuid4()),
            'version_no': version_no, 'name': spec.workflow.name,
            'approval_role': spec.workflow.approval_role,
            'responsible_role': spec.workflow.responsible_role,
            'status': 'DRAFT',
        },
        'posting': {
            'id': str(uuid4()), 'version_no': version_no, 'status': 'DRAFT',
            'amount_field': spec.amount_field,
            'decimal_places': spec.decimal_places,
        },
    }
    return content


def transition_snapshot(
    source: dict[str, Any], expected: str, target: str,
) -> dict[str, Any]:
    allowed = {('DRAFT', 'REVIEW'), ('REVIEW', 'PUBLISHED')}
    if (expected, target) not in allowed:
        raise ValueError('transição de catálogo inválida')
    result = json.loads(json.dumps(source))
    sections = ('ledger', 'chart', 'rule_release', 'mapping', 'workflow', 'posting')
    items = [result[name] for name in sections] + result['accounts'] + result['rules']
    if any(item['status'] != expected for item in items):
        raise ValueError('snapshot possui estados divergentes')
    for item in items:
        item['status'] = target
    if target == 'PUBLISHED':
        if any(not rule['tests_passed'] for rule in result['rules']):
            raise ValueError('regra sem testes não pode ser publicada')
        for rule in result['rules']:
            rule['approved'] = True
    return result


def preparation_plan(
    content: dict[str, Any], tenant_id: UUID, company_id: UUID,
) -> PreparationPlan:
    if snapshot_hash(content) == '':
        raise ValueError('snapshot inválido')
    ledger_data = content['ledger']
    account_data = content['accounts']
    rule_data = content['rules']
    accounts = tuple(_account_domain(item, tenant_id, company_id) for item in account_data)
    rules = tuple(AccountingRuleVersion(
        UUID(item['id']), tenant_id, company_id, UUID(item['rule_id']),
        int(item['version_no']), item['scope'],
        tuple(tuple(condition) for condition in item['conditions']),
        int(item['priority']), UUID(item['debit_account_version_id']),
        UUID(item['credit_account_version_id']), date.fromisoformat(item['valid_from']),
        _date(item['valid_to']), item['status'], item['automation_level'],
        bool(item['approved']), bool(item['tests_passed']),
    ) for item in rule_data)
    release_data = content['rule_release']
    workflow_data = content['workflow']
    posting_data = content['posting']
    return PreparationPlan(
        RuleSetRelease(
            UUID(release_data['id']), tenant_id, company_id, release_data['name'],
            tuple(UUID(value) for value in release_data['rule_version_ids']),
            release_data['status'],
        ),
        rules,
        accounts,
        Ledger(
            UUID(ledger_data['id']), tenant_id, company_id, ledger_data['name'],
            ledger_data['currency_code'],
            'ACTIVE' if ledger_data['status'] == 'PUBLISHED' else ledger_data['status'],
            date.fromisoformat(ledger_data['valid_from']), _date(ledger_data['valid_to']),
        ),
        PostingPolicy(
            UUID(posting_data['id']), tenant_id, company_id, posting_data['status'],
            posting_data['amount_field'], int(posting_data['decimal_places']),
        ),
        WorkflowVersion(
            UUID(workflow_data['id']), UUID(workflow_data['definition_id']),
            int(workflow_data['version_no']), workflow_data['status'],
        ),
        _account_groups(accounts),
        workflow_data['approval_role'],
        workflow_data['responsible_role'],
    )


def _validate_spec(spec: CatalogSpec) -> None:
    if not all((spec.name.strip(), spec.ledger_name.strip(), spec.chart_name.strip())):
        raise ValueError('identificação do catálogo é obrigatória')
    if len(spec.currency_code) != 3 or spec.currency_code != spec.currency_code.upper():
        raise ValueError('moeda do catálogo inválida')
    if spec.valid_to is not None and spec.valid_to < spec.valid_from:
        raise ValueError('vigência do catálogo inválida')
    if spec.amount_field != 'invoice_total' or not 0 <= spec.decimal_places <= 6:
        raise ValueError('política de valor não suportada')
    if not spec.workflow.approval_role.strip() or not spec.workflow.responsible_role.strip():
        raise ValueError('responsáveis do workflow são obrigatórios')
    account_keys = [item.key for item in spec.accounts]
    if len(account_keys) != len(set(account_keys)) or any(not key.strip() for key in account_keys):
        raise ValueError('chaves de conta inválidas ou duplicadas')
    for account in spec.accounts:
        if account.parent_key is not None and account.parent_key not in account_keys:
            raise ValueError('pai de conta inexistente')
    rule_keys = [item.key for item in spec.rules]
    if len(rule_keys) != len(set(rule_keys)) or any(not key.strip() for key in rule_keys):
        raise ValueError('chaves de regra inválidas ou duplicadas')
    collisions: set[tuple[int, tuple[tuple[str, str, str], ...]]] = set()
    for rule in spec.rules:
        if rule.debit_account_key not in account_keys or rule.credit_account_key not in account_keys:
            raise ValueError('regra referencia conta inexistente')
        if any(operator not in {'EQ', 'CONTAINS'} for _, operator, _ in rule.conditions):
            raise ValueError('operador DSL não permitido')
        signature = (rule.priority, rule.conditions)
        if signature in collisions:
            raise ValueError('regras ambíguas com mesma prioridade e condições')
        collisions.add(signature)
    mapping_keys = [item.key for item in spec.mappings]
    if len(mapping_keys) != len(set(mapping_keys)):
        raise ValueError('chaves de mapping duplicadas')
    if any(item.target_account_key not in account_keys for item in spec.mappings):
        raise ValueError('mapping referencia conta inexistente')


def _account_domain(item: dict[str, Any], tenant_id: UUID, company_id: UUID) -> AccountVersion:
    return AccountVersion(
        UUID(item['id']), tenant_id, company_id, UUID(item['account_id']),
        int(item['version_no']), item['code'], item['name'], item['nature'],
        item['normal_balance'],
        UUID(item['parent_account_id']) if item['parent_account_id'] else None,
        bool(item['is_synthetic']), bool(item['is_postable']), item['status'],
        date.fromisoformat(item['valid_from']), _date(item['valid_to']),
    )


def _account_groups(accounts: tuple[AccountVersion, ...]) -> tuple[tuple[UUID, tuple[UUID, ...]], ...]:
    by_id = {item.account_id: item for item in accounts}
    result = []
    for account in accounts:
        ancestors = []
        parent_id = account.parent_account_id
        while parent_id is not None:
            ancestors.append(parent_id)
            parent = by_id.get(parent_id)
            parent_id = parent.parent_account_id if parent else None
        result.append((account.account_id, tuple(ancestors)))
    return tuple(result)


def _date(value: str | None) -> date | None:
    return date.fromisoformat(value) if value else None
