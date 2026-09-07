# Cobertura de regressão do MVP

Esta suíte é o gate de regressão antes do piloto real. Ela cobre somente as
fatias já implementadas; não certifica escrituração oficial nem habilita o
conector Domínio, que permanece bloqueado para homologação.

## Matriz de garantias

| Área | Garantia de regressão | Testes principais |
| --- | --- | --- |
| Tenant | IDs conhecidos de outro tenant/empresa não autorizam leitura nem mutação. | `tests/security/test_tenant_authorization.py`; `test_foreign_and_missing_exports_are_uniformly_unavailable` |
| Documento | Mesmo conteúdo gera evidência deduplicada, recebimentos distintos e leitura com hash conferido; evidência é imutável. | `tests/integration/test_document_intake.py`; `tests/unit/test_local_object_storage.py` |
| NF-e | XML NF-e 55 produz os campos canônicos previsíveis, `Decimal`, itens, tributos e linhagem; conteúdo inválido é quarentenado. | `tests/unit/test_nfe55_xml_parser.py`; `tests/integration/test_nfe55_importer.py` |
| OFX | `TRNAMT` negativo é preservado como débito e o mesmo `FITID` em extrato posterior não cria segunda transação. | `tests/unit/test_ofx_regression.py` |
| Plano | Conta sintética não é lançável; ciclos e código publicado sobreposto são recusados; versões publicadas são imutáveis. | `tests/unit/test_chart_of_accounts.py` |
| Regra / DE-PARA | Regra de maior prioridade vence de modo reproduzível; empate ou alvo inválido não escolhe conta arbitrariamente. | `tests/unit/test_accounting_rules.py`; `tests/unit/test_mapping_engine.py` |
| Lançamento | Revisão exige partidas balanceadas, contas lançáveis no escopo e vínculo de evidência. | `tests/unit/test_pre_ledger.py` |
| Workflow | Aprovação exige autorização, segregação, hash/revisão atual e prazo válido; nova revisão invalida a solicitação anterior. | `tests/unit/test_workflow_approvals.py`; `tests/integration/test_nfe_to_dominio_vertical.py` |
| Exportação | Retentativa mantém identidade; rota divergente conflita; sem aprovação/revisão atual o conector não é alcançado. | `test_export_retry_preserves_identity_and_conflicting_route_is_rejected`; `test_nonapproved_or_superseded_revision_never_reaches_connector` |
| Conciliação | Diferenças permanecem parciais, exceções bloqueiam aprovação e sugestões não criam match automaticamente. | `tests/unit/test_reconciliation.py` |
| Bloqueio | Todos os escopos e canais revalidam lock no instante do efeito; desbloqueio exige nova revisão. | `tests/unit/test_account_locks.py`; `test_every_lock_scope_blocks_the_critical_effect` |
| Auditoria | Eventos correlacionados preservam integridade, não aceitam XML/segredo bruto e permitem rastreio reverso até a evidência original. | `tests/unit/test_audit_service.py`; `test_vertical_all_internal_stages_and_reverse_trace_to_original_xml` |
| IA | Prompt injection, saída inválida, indisponibilidade e baixa confiança não produzem decisão; origem IA não pode aprovar efeito. | `tests/unit/test_ai_inference.py`; `test_invalid_human_decisions_have_no_effect[AI]` |

## Regressão encontrada e corrigida nesta execução

O primeiro cenário OFX revelou que `_transaction_fingerprint` aplicava
`dataclasses.asdict` a um dicionário, interrompendo toda importação OFX antes
da deduplicação. A função agora aceita tanto dataclass quanto mapping. O teste
novo reproduz uma segunda entrega com o mesmo `FITID` e verifica que apenas a
primeira transação é persistida.

## Execução

Use a suíte integral como gate local:

    .venv\Scripts\python.exe -m pytest -q

Antes do piloto, execute também as migrations contra o MySQL homologado. A
suíte de domínio usa SQLite em memória para velocidade; isso não substitui a
validação de upgrade/constraints no MySQL suportado.

## Limites conhecidos do gate

- Não há exportação efetiva ao Domínio: o teste prova o bloqueio de
  pré-homologação, não um arquivo oficial.
- Não há autenticação HTTP externa nem API de upload pública nesta fatia.
- IA é testada apenas como assistiva e sem autoridade crítica, conforme o
  contrato atual.
- Dados de teste são sintéticos e não constituem homologação fiscal.
