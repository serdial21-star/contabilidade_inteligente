# Lacunas de dados do frontend

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
