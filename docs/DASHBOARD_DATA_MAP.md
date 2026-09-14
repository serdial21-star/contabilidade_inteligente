# Mapa de dados da Minha Visão

Inventário da Phase 05. `CURRENT AVAILABILITY` descreve o backend existente; `STATUS` descreve a entrega no modo atual. Todos os contratos reais partem do principal autenticado e revalidam tenant, `CompanyAccess` e permissão no serviço de aplicação.

| ID | Display name | Purpose | Required permission | Source module | Source contract | Tenant filter | Company filter | Aggregation | Current availability | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| W001 | Documentos recebidos | Volume recebido no contexto | `company.read` | `intake_documents` | Sem endpoint agregado | Obrigatório | Empresa autorizada | `COUNT` de receipts no período a definir | DERIVABLE_FROM_EXISTING_SOURCE | SYNTHETIC |
| W002 | Processados | Itens cuja transformação terminou em estado real definido | `company.read` | `intake_documents` / `workflow` | `processing/{resource_id}` é unitário; sem agregado | Obrigatório | Empresa autorizada | Status terminal precisa de projeção agregada | DERIVABLE_FROM_EXISTING_SOURCE | SYNTHETIC |
| W003 | Pendentes de revisão | Trabalho que exige conferência | `journal.read` | `operations` / `workflow` | `GET .../{company_id}/reviews` | Derivado do principal | Revalidado no backend | Filtrar `PENDING_APPROVAL` | REAL_SOURCE_AVAILABLE | READY |
| W004 | Fila Inteligente | Exceções prioritárias explicadas | `company.read` | `operations` / `intake_documents` | `GET .../{company_id}/exceptions` | Derivado do principal | Revalidado no backend | Contar e limitar a cinco itens | REAL_SOURCE_AVAILABLE | READY |
| W005 | Propostas contábeis | Propostas disponíveis para consulta | `journal.read` | `operations` / `workflow` | `GET .../{company_id}/reviews` | Derivado do principal | Revalidado no backend | Contagem de jornadas com revisão | REAL_SOURCE_AVAILABLE | READY |
| W006 | Aprovações pendentes | Itens dentro da alçada de aprovação | `journal.approve` | `operations` / `workflow` | `GET .../{company_id}/reviews` | Derivado do principal | Revalidado no backend | Filtrar `PENDING_APPROVAL`; catálogo também exige capacidade | REAL_SOURCE_AVAILABLE | READY |
| W007 | Empresas com pendências | Empresas autorizadas que exigem atenção | `company.read` | `identity` + `operations` | `/identity/me` + fontes por empresa; sem agregado eficiente | Derivado do principal | Somente lista de `/identity/me` | Contagem por empresa, server-side futura | DERIVABLE_FROM_EXISTING_SOURCE | SYNTHETIC |
| W008 | Obrigações próximas | Compromissos operacionais próximos | `company.read` apenas para exibição sintética | Nenhum módulo aprovado | Nenhum | Não aplicável | Não aplicável | Não definida | SYNTHETIC_ONLY | SYNTHETIC |
| W009 | Conciliações pendentes | Conferências financeiras aguardando ação | `reconciliation.manage` | `reconciliation` | Sem endpoint read-only de dashboard | Obrigatório no futuro | Obrigatório no futuro | Estado real a projetar | DEFERRED | DEFERRED |
| W010 | Atividade recente | Eventos seguros e compreensíveis | `audit.read` | `operations` / `audit` | `GET .../{company_id}/audit-events` | Derivado do principal | Revalidado no backend | Ordenação decrescente, máximo cinco | REAL_SOURCE_AVAILABLE | READY |

## Resumo

- `REAL_SOURCE_AVAILABLE`: 5
- `DERIVABLE_FROM_EXISTING_SOURCE`: 3
- `SYNTHETIC_ONLY`: 1
- `DEFERRED`: 1

O modo desta fase continua integralmente sintético. `READY` indica que o caminho read-only futuro pode reutilizar um contrato existente; não indica uso de dados reais no piloto atual. W008 não cria calendário tributário, e W009 não cria uma semântica de conciliação que o backend ainda não expõe.

`Todas as empresas autorizadas` é calculado somente sobre empresas retornadas por `/identity/me`. No provider API futuro, chamadas continuam por empresa e por permissão; uma projeção server-side consolidada deverá ser avaliada antes de escala para evitar chamadas excessivas, sem consultar o tenant inteiro para filtrar no navegador.
