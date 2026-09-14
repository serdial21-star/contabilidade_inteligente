# Mapa de permissões do frontend

Mapa de apresentação baseado exclusivamente nos códigos reais de `INITIAL_PERMISSION_CODES`. `GET /api/v1/identity/me` resolve capacidades tenant-wide e por empresa; o seletor recalcula a apresentação com a empresa ativa. Ocultar ou desabilitar um item é UX; o backend continua obrigatório em todas as operações.

| Área da UI | Ação | Permissão backend | Comportamento de exibição | Backend ainda aplica |
| --- | --- | --- | --- | --- |
| Minha Visão | abrir contexto empresarial | `company.read` | visível quando projetada | SIM |
| Operação | abrir placeholder | `company.read` | visível, desabilitado até fase do módulo | SIM |
| Fiscal | abrir placeholder | `company.read` | visível, desabilitado até integração | SIM |
| Financeiro | abrir placeholder | `reconciliation.manage` | visível, desabilitado até integração | SIM |
| Contábil | consultar área | `journal.read` | visível; conteúdo operacional ainda não conectado | SIM |
| Clientes | abrir placeholder | `company.read` | visível, desabilitado | SIM |
| Obrigações | abrir módulo futuro | SEM CONTRATO | mostrado desabilitado; nenhuma permissão foi inventada | SIM |
| Governança | consultar controles | `audit.read` OU `lock.manage` | visível com pelo menos uma capacidade | SIM |
| Administração | administrar identidade/catálogo | `identity.manage` OU `catalog.manage` | oculto sem capacidade; funcionalidade não conectada | SIM |
| Proposta | propor lançamento | `journal.propose` | não implementado na Phase 04 | SIM |
| Proposta | aprovar lançamento | `journal.approve` | não implementado na Phase 04 | SIM |
| Exportação | executar exportação | `export.execute` | não implementado; Domínio segue bloqueado | SIM |

Identificadores segmentados, como `privacy.dsr.search`, devem permanecer completos. Não há prefixos implícitos, curingas ou simplificação por primeiro segmento.

Invariante verificada: `VISIBLE_COMPANIES ⊆ BACKEND_AUTHORIZED_COMPANIES`. A projeção não aceita permissões, papéis, tenant ou empresas informados pelo frontend.
