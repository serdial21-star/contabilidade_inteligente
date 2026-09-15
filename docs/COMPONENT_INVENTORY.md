# Component Inventory

## Componentes Phase 07

| COMPONENT | PURPOSE | STATUS | ACCESSIBILITY / SECURITY |
|---|---|---|---|
| FiscalDocumentTable | Lista NF-e paginada e filtrada | READY | Headings semânticos; status textual; metadados escapados. |
| NFeImportPanel | Reusar import especializado NF-e | READY | File picker por teclado; campos rotulados; feedback `aria-live`. |
| FiscalDocumentDetail | Cabeçalho, tributos persistidos e itens | READY | XML não renderizado; receipt público; lista limitada. |
| BankStatementTable | Lista de extratos com conta minimizada | READY | Agência/conta mascaradas; valores legíveis. |
| OfxImportPanel | Reusar import especializado OFX | READY | Tipo restrito e feedback textual. |
| TransactionTable | Créditos/débitos e filtros | READY | Rótulo e sinal além de cor; valores tabulares. |
| IntelligenceService | Selecionar provider API ou sintético | READY | Sem fallback sintético em API; rede centralizada. |

## Componentes Phase 06

| COMPONENT | PURPOSE | STATUS | ACCESSIBILITY / SECURITY |
|---|---|---|---|
| CompanyTable | Empresas autorizadas, busca e detalhe | READY | Tabela semântica; fonte autorizada. |
| CompanyDetail | Resumo e navegação contextual | READY | `dl` rotulada; acesso revalidado. |
| DocumentInbox | Atenção inicial sem duplicar Fila | READY | Estado vazio textual. |
| DocumentTable | Metadados, status e paginação | READY | Região rolável; botões nomeados. |
| DocumentFilterBar | Nome, status, origem e datas | READY | Labels e submit deliberado. |
| DocumentDetail | Metadados/issues minimizados | READY | Filename escapado; sem storage. |
| OperationalState | Loading, empty, error, forbidden | READY | `aria-busy`, alert e retry. |

## Entrega da Phase 05

| COMPONENT | PURPOSE | VARIANTS | STATUS | USED_IN | ACCESSIBILITY NOTES |
| --- | --- | --- | --- | --- | --- |
| DashboardService | Centralizar catálogo, providers, estados e preferências | Synthetic / future API | READY | Minha Visão | Autoriza antes de consultar; falha isolada |
| MetricWidget | Resumir volume com significado explícito | Loading/ready/empty/error/unavailable | READY | W001/W002/W003/W005 | Heading próprio, valor e contexto textual |
| ListWidget | Mostrar até cinco prioridades | Lista / timeline / table preview | READY | W004/W007/W008/W009/W010 | Lista semântica, texto além de cor |
| StatusWidget | Mostrar atenção ou ausência contextual | Ready/empty/error | READY | W006 | Linguagem oficial e permissão de aprovação |
| DashboardCustomizer | Adicionar, remover, mover, ampliar e restaurar | Dialog + controles por widget | READY | Minha Visão | Teclado; nenhuma dependência de drag |
| CompanyDashboardContext | Alternar empresa ou todas autorizadas | Individual / interseção autorizada | READY | Topbar + dashboard | Sem entrada arbitrária de ID; estado anterior descartado |

Os componentes históricos abaixo permanecem como inventário da foundation da Phase 02.

READY = fundação de apresentação implementada; PROTOTYPE = comportamento local demonstrativo; PLANNED = contrato/integração futura. Não significa prontidão de produção. Implementação central em `app/foundation.js`, CSS em `ui/foundation.css`, tokens em `ui/tokens.css`; mocks em `app/mocks.js`.

| COMPONENT | PURPOSE | VARIANTS | STATUS | USED_IN | ACCESSIBILITY NOTES |
| --- | --- | --- | --- | --- | --- |
| BrandAsset | Reutilizar marca oficial | Principal, vertical, simplificada | READY | Login, shell, galeria | Alt e proporção original |
| AppShell | Sidebar/topbar/content | Desktop, compacto, mobile drawer | READY | Todas as telas internas | Landmark, skip link, menu nomeado |
| Navigation | Organização em nove grupos | Atual, futuro, compacto | PROTOTYPE | Shell | aria-current; display-only |
| LoginUX | Mostrar acesso coerente com OIDC | Desabilitado, explorar protótipo | PROTOTYPE | Login | Não recebe senha, labels e aviso |
| Button | Ações consistentes | Primary, secondary, tertiary, ghost, danger; small/default/large | READY | Todas | Nome, foco, disabled; danger não substitui confirmação |
| Badge | Status sem ambiguidade | success, warning, danger, info, neutral, intelligent | READY | Cards/tabelas/revisão | Texto+ícone, ouro com texto escuro |
| Alert | Explicar resultado/condição | Info, success, warning, error | READY | Galeria, revisão, dialogs | Ícone+título+mensagem |
| Widget | Conteúdo reutilizável | METRIC, LIST, STATUS, TIMELINE, PROGRESS, TABLE_PREVIEW | PROTOTYPE | Minha Visão | Dez itens, títulos, sem drag obrigatório |
| WidgetControls | Organizar visão | Add/remove/move/resize/save | PROTOTYPE | Dashboard/settings | Botões nomeados, foco restaurado, apenas memória |
| PresetSelect | Cinco organizações | Executiva, Contábil, Fiscal, Operacional, Minha Visão | PROTOTYPE | Dashboard/settings | Não muda permissões |
| SmartQueue | Priorizar intervenção | Tipo/empresa/motivo/prioridade/data/responsável/ação | PROTOTYPE | Dashboard | Tabela e ação explícita |
| DataTable | Consulta sintética | Sort, seleção, paginação, status, ações, vazio | PROTOTYPE | Documentos/propostas | Região rolável, aria-sort, checkbox nomeado |
| FilterBar / FilterDrawer | Pesquisa consistente | Search/status/company/date range/responsible | PROTOTYPE | Listas | Labels, erro de período, limpar filtros |
| FormField | Entrada padronizada | Text/textarea/select/multi/date/currency/checkbox/radio/switch/file | READY | Galeria/dialogs | Default/focus/disabled/error/success/read-only; file desabilitado |
| InformationModal | Contexto adicional | Informação | READY | Galeria/login futuro | dialog nativo, fechar/Escape |
| FormModal | Exemplo de formulário | Nome de visão | PROTOTYPE | Galeria | Required, nenhuma persistência |
| ConfirmationModal | Ação deliberada | Confirmação/decisão | PROTOTYPE | Revisão/galeria | Conferência e confirmação explícitas |
| DestructiveConfirmation | Confirmar descarte local | Reset da visão em memória | PROTOTYPE | Settings/galeria | Checkbox explícito; não remove dados reais |
| Drawer | Contexto sem sair da tela | Detalhes/histórico/filtros/menu | READY | Listas e shell | Título, retorno de foco; validar em navegador |
| DecisionLine | Mostrar cadeia de evidência | NF-e e OFX, pendente/aprovado/rejeitado | PROTOTYPE | Página/drawer | Etapas textuais, mock de ator/data |
| ReviewDetail | Conferência profissional | Débito/crédito, balanceado, bloqueado, sem regra | PROTOTYPE | Revisão | Valores rotulados; sem conta/regra real |
| AccountLockNotice | Explicar impedimento | Escopo/motivo/ator/data sintéticos | PROTOTYPE | DOC-003 | Texto explícito e ações disabled |
| EmptyState | Orientar próximo passo | Lista filtrada, revisão vazia | READY | Listas/galeria | Título descritivo + CTA |
| LoadingState | Indicar espera | Skeleton/spinner | READY | Galeria | Texto de estado e reduced motion |
| ErrorState | Comunicar falhas sem vazamento | Page/inline/permission/not found/temporary | READY | Galeria/dialogs | Erro uniforme; não expõe existência protegida |
| NotificationCenter | Notificações reais | Transporte/contador/persistência | PLANNED | Topbar mostra só aviso | Sem badge real inventado |
| CompactDensity | Uso avançado | Compact | PLANNED | Settings | Desabilitado, não persistido |
