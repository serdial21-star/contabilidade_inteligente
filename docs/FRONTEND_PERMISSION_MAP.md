# Mapa de permissões do frontend

## Atualização Phase 07

| Área/ação | Permissão exata | Comportamento |
|---|---|---|
| Fiscal — lista/detalhe | `company.read` | Menu e consulta apenas em empresa autorizada. |
| Financeiro — extratos/transações | `company.read` | Conta mascarada e consulta company-scoped. |
| Importar NF-e/OFX | `journal.propose` | Controle oculto sem a capacidade; servidor revalida principal, tenant e `CompanyAccess`. |
| Conciliação/match manual | — | Não exposto: caso de uso operacional inexistente. |

`journal.propose` é reutilizado por compatibilidade com os imports existentes, mas é semanticamente mais amplo que “importar documento”. Uma permissão própria exigiria decisão de contrato e migration; a Phase 07 não a inventa.

## Atualização Phase 06

| Área/ação | Exibição | Autoridade backend |
|---|---|---|
| Lista de empresas | `company.read` projetado | `/identity/me` retorna somente CompanyAccess vigente. |
| Detalhe de empresa | `company.read` | Tenant + CompanyAccess + permissão revalidados. |
| Inbox/lista/detalhe/resumo documental | `company.read` | Queries tenant/company scoped. |
| Imports NF-e/OFX existentes | `journal.propose` | Expostos somente nos painéis especializados da Phase 07; não são upload genérico. |

Visibilidade de botão não autoriza. Nenhuma permissão nova foi introduzida.

Mapa de apresentação baseado exclusivamente nos códigos reais de `INITIAL_PERMISSION_CODES`. `GET /api/v1/identity/me` resolve capacidades tenant-wide e por empresa; o seletor recalcula a apresentação com a empresa ativa. Ocultar ou desabilitar um item é UX; o backend continua obrigatório em todas as operações.

| Área da UI | Ação | Permissão backend | Comportamento de exibição | Backend ainda aplica |
| --- | --- | --- | --- | --- |
| Minha Visão | abrir contexto empresarial | `company.read` | visível quando projetada | SIM |
| Operação | abrir placeholder | `company.read` | visível, desabilitado até fase do módulo | SIM |
| Fiscal | consultar/importar NF-e | `company.read` / `journal.propose` | leitura e import especializado integrados | NÃO |
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
