# Lacunas de dados do frontend

## Reclassificação Phase 08

| Gap | Classificação | Resultado / destino |
|---|---|---|
| Lista/detalhe/regra/evidência/linhas da proposta | RESOLVED_PHASE08 | Projeções reais tenant/company-aware. |
| Aprovação e rejeição | RESOLVED_PHASE08 | Comandos existentes com revisão/hash, idempotência, SOD e lock. |
| Edição de proposta e motivo persistido de rejeição | REAL_BACKEND_GAP | Sem caso de uso/campo seguro; nenhuma migration. |
| Escrita granular de regra/mapping | REAL_BACKEND_GAP | Governança atual opera versão completa; somente leitura exposta. |
| Contabilidade a partir de OFX/BankTransaction | DEFERRED_LATER | Nenhuma regra/caso de uso inventado. |
| Linha da Decisão completa | DEFERRED_PHASE09 | Prévia contextual existe; timeline profunda não foi iniciada. |

## Reclassificação Phase 07

| Gap | Classificação | Resultado / destino |
|---|---|---|
| NF-e import/list/detail/items | RESOLVED_PHASE07 | Contratos reais especializados e projeções tenant/company-aware. |
| OFX import/statement/transactions | RESOLVED_PHASE07 | Contratos reais, máscara de conta e sinal preservado. |
| Exceção fiscal no próprio detalhe | REAL_BACKEND_GAP | Disponível na Central/W004, ainda não agregada no detalhe fiscal. |
| Matching, sugestão e conciliação persistente | REAL_BACKEND_GAP | Sem caso de uso/repositório; permanece DEFERRED. |
| Revisão/edição/aprovação contábil | DEFERRED_PHASE08 | Nenhuma ação exposta nesta fase. |
| Linha da Decisão completa | DEFERRED_PHASE09 | Receipt/documento disponível; cadeia integral ainda parcial. |
| Upload fiscal/financeiro em lote | REAL_BACKEND_GAP | Endpoints atuais recebem um arquivo por requisição. |
| Malware scanning | INFRASTRUCTURE_GAP | Nenhum scanner fictício foi criado. |

## Reclassificação Phase 06

| Gap | Status após Phase 06 |
|---|---|
| Empresas autorizadas e detalhe seguro | RESOLVED_PHASE06 |
| Inbox/lista/filtros/paginação/detalhe documental | RESOLVED_PHASE06 |
| W001/W002/W007 em modo API | RESOLVED_PHASE06 |
| Upload documental genérico | REAL_BACKEND_GAP |
| Imports especializados NF-e/OFX na UI | DEFERRED_PHASE07 |
| Download original e histórico por documento | DEFERRED_LATER |
| Malware scanning | INFRASTRUCTURE_GAP |
| Preferências de dashboard server-side | DEFERRED_LATER |

Reclassificação após a Phase 05.

| ID | Necessidade | Classificação | Estado |
| --- | --- | --- | --- |
| FD-01 | sessão e identidade de apresentação | RESOLVED_PHASE04B | OIDC adapter, store em memória, `/identity/me` e estados integrados |
| FD-02 | permissões, tenant e empresas autorizadas | RESOLVED_PHASE04B | projeção backend por Membership/CompanyAccess/RoleBinding pronta |
| FD-03 | agregados da Minha Visão | RESOLVED_PHASE05 | serviço central, catálogo e estados por widget; fontes reais parciais mapeadas sem uso nesta fase |
| FD-04 | preferências de widgets | RESOLVED_PHASE05_LOCAL | somente preset, IDs, ordem e tamanho no navegador; revalidação por permissão |
| FD-05 | Fila Inteligente agregada | RESOLVED_PHASE05 | provider sintético isolado e contrato real de exceções preparado para modo API futuro |
| FD-06 | filtros, contagem e paginação operacional | DEFERRED_LATER | contratos incompletos |
| FD-07 | edição e nova revisão de proposta | DEFERRED_LATER | nenhuma mutação fictícia criada |
| FD-08 | Linha da Decisão autorizada | DEFERRED_LATER | timeline permanece referência |
| FD-09 | notificações | DEFERRED_LATER | integração omitida |
| FD-10 | obrigações, conciliação e clientes agregados | REAL_BACKEND_GAP | obrigações sem fonte; conciliação sem consulta; empresas sem agregado eficiente |

Contagem: `RESOLVED_PHASE04B=2`, `RESOLVED_PHASE05=2`, `RESOLVED_PHASE05_LOCAL=1`, `DEFERRED_LATER=4`, `REAL_BACKEND_GAP=1`.
