# Design System Specification — Phase 02

Fundação de design e UX de **Serdial21 Contabilidade Inteligente**, 14/09/2026. Entrada: [app/prototype.html](../app/prototype.html), sem build ou servidor. [Instruções de navegação](../app/README.md), [inventário de componentes](COMPONENT_INVENTORY.md), [fluxos e gaps](UX_FLOWS.md).

## Inspeção e reaproveitamento

| Item existente | Classificação | Decisão |
| --- | --- | --- |
| `app/index.html` / `app/dashboard.js` | PROTOTYPE_ONLY / LEGACY | Prévia de seis registros preservada byte a byte; nova entrada `prototype.html` para a foundation. |
| `ui/design-system.css` | REUSE / REFINE | Reaproveitados padrões de cards, botões, tabela, diálogo, foco e responsividade; nova folha de foundation incorpora a identidade oficial sem mudar o CSS compartilhado pelo site. |
| `site/index.html` | PROTOTYPE_ONLY / REVIEW_REQUIRED | INSPECTED; preservado para Phase 03, inclusive sua identidade anterior. |
| `docs/FRONTEND_VISUAL_BASE.md` | REFINE | Registro histórico preservado com apontamento para esta nova fundação. |
| Assets oficiais recebidos nesta fase | REUSE | Quatro PNGs copiados integralmente; hashes iguais aos originais. |

VISUAL_BASE_REUSE = PARTIAL. Estrutura leve, linguagem operacional e padrões acessíveis são reutilizados; teal como ação principal, monograma provisório e “Visão geral” como nome principal não são aplicados na nova foundation. A entrada separada protege a prévia e evita alterar o site fora da fase autorizada.

FRONTEND_FRAMEWORK = HTML + CSS + JavaScript nativos. BUILD_TOOL = NONE. CSS_STRATEGY = custom properties + folha central por foundation. COMPONENT_LIBRARY = funções reutilizáveis locais. ICON_LIBRARY = coleção única local de SVGs geométricos de UI, stroke 1.7/viewBox 24; não são símbolos de marca. STATE_MANAGEMENT = memória JavaScript. ROUTER = hash nativo. TEST_TOOLING = smoke tests Node com módulos nativos; não havia testes/build/lint/typecheck frontend anteriores. Não foram encontrados manifests/configurações React/Vue/Next/Vite/Tailwind ou `public/` de frontend. `src/` continua backend Python.

## Brand / colors

OFFICIAL_BRAND_ASSET = IMPORTED_USER_SUPPLIED. Usar apenas imagens oficiais, sem reconstrução, crop ou recoloração. Prancha e variantes em [assets/brand](../ui/assets/brand/README.md). Slogan: **Inteligência para automatizar. Controle para decidir.** Personalidade profissional, precisa, confiável e moderna; sem robôs, cérebros, circuitos, 3D ornamental ou aparência de ERP antigo.

Paleta oficial e contrastes em [BRAND_COLOR_SPEC](BRAND_COLOR_SPEC.md). Azul organiza operação; ouro destaca inteligência; vermelho integra marca e criticidade pertinente; verde comunica sucesso/decisão humana, âmbar comunica atenção. Tokens semânticos de UI são provisórios, explicitamente distintos dos hex institucionais.

## Typography

A prancha indica Manrope para marketing/títulos e Inter para sistema/interface. Os stacks refletem essa direção; arquivos dessas fontes não foram fornecidos/empacotados. Sem disponibilidade local, utiliza-se Segoe UI/Arial, equivalentes já usados pela prévia. Nenhuma fonte remota, CDN ou nova dependência foi acrescentada. Empacotamento licenciado das fontes exatas é uma pendência de fidelidade tipográfica, não um novo contrato backend.

| Role | Token / tamanho | Peso / linha |
| --- | --- | --- |
| Display | `--font-display`, 2.75rem | 700 / 1.2 |
| H1 | `--font-h1`, 2rem | 700 / 1.2 |
| H2 | `--font-h2`, 1.25rem | 700 / 1.2 |
| H3 | `--font-h3`, 1rem | 700 / 1.2 |
| Body | `--font-body`, .9375rem | 400 / 1.6 |
| Small | `--font-small`, .8125rem | 400–600 / 1.6 |
| Caption | `--font-caption`, .75rem | 400–600 / 1.6 |
| Table | `--font-small` | 400, cabeçalho 600 / 1.6 |
| Metric | `--font-metric`, 2rem | 700 / 1.2 |

## Spacing / layout

Escala central: 4, 8, 12, 16, 20, 24, 32, 40, 48px. Radius: 6/10/16px. Shadow: leve para card, elevada para overlay. Pesos: 400/500/600/700. Z-index: header 10, sidebar 20, toast 40; dialog usa top layer nativa. Densidade COMFORTABLE; COMPACT futura/desabilitada.

Sidebar 240px (92px recolhida), topbar com empresa/contexto/notificações/perfil, conteúdo até 1440px e drawer até 560px. Grid de widgets três colunas em desktop, duas em larguras intermediárias e uma no mobile pequeno. Cards ampliados ocupam duas colunas quando houver espaço. Tabelas preservam a comparação desktop e rolam internamente no mobile. Débito e crédito têm títulos textuais próprios.

## Components / states

Botões primary/secondary/tertiary/ghost/danger, três tamanhos; badges success/warning/danger/info/neutral/intelligent; alertas info/success/warning/error. Campos text, textarea, select, multi-select, date, currency-text, checkbox, radio, switch e file desabilitado; estados default/focus/disabled/error/success/read-only. Modais de informação/formulário/confirmação/confirmação destrutiva; drawers de detalhes/histórico/filtros/menu. Empty state com próximo passo, skeleton, spinner e erros uniformes estão na galeria.

Os dez widgets usam seis renderizações genéricas: METRIC, LIST, STATUS, TIMELINE, PROGRESS, TABLE_PREVIEW. A personalização permite adicionar/remover/mover/redimensionar e salvar em memória. Cinco presets: Visão Executiva, Visão Contábil, Visão Fiscal, Visão Operacional, Minha Visão. Nenhum preset é papel ou permissão.

Tabelas locais demonstram pesquisa, filtro de status, empresa, intervalo de datas, responsável, ordenação por documento, seleção e paginação de quatro itens. “Limpar” restaura filtros. A Fila Inteligente reúne tipo, empresa, motivo, prioridade, recebido em, responsável e ação. Os mocks de indicadores globais são explicitamente distinguidos da fila filtrada por empresa.

## Status / intelligence / professional decision

[UX_STATUS_LANGUAGE](UX_STATUS_LANGUAGE.md) mapeia contratos reais e identifica chaves estritamente demonstrativas. Sugestão inteligente = ícone + acento ouro + rótulo; nunca significa aprovado. APROVADO POR/REJEITADO POR identificam ator e instante fictícios no cenário. REVISADO POR da timeline é mock e não afirma existência de evento backend de leitura. Uma confirmação simulada não modifica o histórico original.

AccountLock ACTIVE é projetado como impedimento visual: escopo, motivo, criado por/data e botões desabilitados. Liberação de lock não foi implementada. Sem regra aplicável não há proposta inventada. Contas sintéticas não usam códigos contábeis nem alimentam catálogo/regra.

## Traceability

Linha da Decisão em página e drawer: SOURCE → PROCESSING → RULE → PROPOSAL → REVIEW → APPROVAL, adaptada ao cenário. Links em detalhes/tabelas/revisão/atividade. OFX tem apenas sua trilha demonstrativa de importação; não herda aprovação contábil NF-e. Os dados faltantes estão em [UX_FLOWS](UX_FLOWS.md), sem alteração de AuditEvent.

## Accessibility / responsive

Diretrizes em [ACCESSIBILITY_GUIDELINES](ACCESSIBILITY_GUIDELINES.md). Sem ação exclusiva por drag, status não depende só de cor, foco visível, labels, mensagens mínimas e dialog nativo. Breakpoints 1200/800/480px são literais documentados: CSS custom properties não são usadas como condição de media query. Sidebar móvel em drawer, widgets em coluna única até 480px e tabelas em região rolável. Motion limitado a loading e respeita reduced motion.

## Do / Don't

| DO | DON'T |
| --- | --- |
| Usar logo oficial inteira e tokens | Recriar símbolo, distorcer proporção ou alterar o site da Phase 03 |
| Distinguir preparação e decisão humana | Pintar sugestão de verde com rótulo aprovado |
| Oferecer próximo passo válido | Habilitar aprovação de cenário bloqueado/sem proposta |
| Mostrar apenas contexto permitido | Tratar menu oculto ou layout salvo como autorização |
| Expor revisão/hash pelo contrato futuro correto | Inferir permissão por ID ou copiar before/after irrestritos |
| Identificar mock e limitações | Apresentar estatística da prancha como dado real |
| Preservar erros uniformes | Mostrar SQL, stack trace, segredos ou existência cross-tenant |

## Verificação e gate

BUILD = NOT_APPLICABLE: arquivos estáticos, sem compilação/build preexistente. Sintaxe JavaScript validada. Smoke tests em `app/tests/smoke.cjs`: **6 PASS**, callbacks executados em runtime Node com assert/VM e DOM mínimo simulado. Cobrem sete rotas, ausência de coleta/transmissão, widgets, filtros/paginação/ordenação, confirmação deliberada/bloqueio e ausência de proposta inventada para regra faltante/OFX. Não são testes de browser/layout.

Contrast ratios medidos para onze pares; contraste de ouro/branco insuficiente para texto pequeno tratado com texto escuro. Links locais e referências de assets verificados. Browser conectado e módulos Playwright/DOM não disponíveis nesta sessão: SCREENSHOT/PREVIEW_CAPTURE = NOT_REQUIRED; revisão visual renderizada, responsividade em dispositivo e leitor de tela = NOT_EXECUTED. Não há claim de WCAG certificado. Nenhuma infraestrutura pesada foi instalada.

| Gate Phase 02 | Resultado |
| --- | --- |
| EXISTING FRONTEND | INSPECTED |
| DESIGN TOKENS / BRAND APPLICATION / TYPOGRAPHY | READY (fontes com fallback documentado) |
| LAYOUT / NAVIGATION / LOGIN UX | READY como foundation |
| MINHA VISÃO / WIDGET FOUNDATION / SMART QUEUE | READY como protótipo local |
| STATUS / AUTOMATION / PROFESSIONAL DECISION LANGUAGE | READY |
| LINHA DA DECISÃO / TABLE / FORM / EMPTY-LOADING-ERROR | READY como foundation/protótipo |
| RESPONSIVE / ACCESSIBILITY FOUNDATION | READY em código; QA browser pendente |
| PROTOTYPE PAGES | READY, sete telas + galeria |
| BUILD | NOT_APPLICABLE |
| NO BACKEND CONTRACT CHANGE / NO REAL DATA / NO DESTRUCTIVE CHANGE | PASS |

REPOSITORY_HYGIENE_DEBT = TRACKED_LEGACY_VENV_FILES, NON_BLOCKING / SEPARATE_MAINTENANCE. STAGING_CONFIG = PENDING_ENVIRONMENT_PHASE. SYNTHETIC PILOT = GO; REAL DATA = NO_GO; EXTERNAL EXPOSURE = NO_GO; MIGRATION 0012 = PRE_DEPLOY_REQUIRED; DOMINIO_EXPORT = BLOCKED_FOR_HOMOLOGATION. Nenhuma migration ou dependência estrutural criada. Phase 03 não iniciada.
