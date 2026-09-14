# Design System Brief

Brief da Phase 01 atualizado pela execução autorizada da Phase 02. A foundation navegável está em [app/prototype.html](../app/prototype.html), com especificação em [DESIGN_SYSTEM_SPEC](DESIGN_SYSTEM_SPEC.md). Fontes de identidade: solicitação aprovada e quatro imagens oficiais fornecidas pelo usuário durante a Phase 02.

| Item | Diretriz |
| --- | --- |
| PRODUCT | Serdial21 Contabilidade Inteligente |
| BRAND | Serdial21 |
| CATEGORY | Plataforma de inteligência operacional para escritórios contábeis |
| MARKET | SaaS B2B para escritórios contábeis |
| SLOGAN | Inteligência para automatizar. Controle para decidir. |
| BRAND COLORS | Azul Serdial21, Ouro Serdial21, Vermelho Serdial21, Branco |
| CONCEPTS | Inteligência, automação, controle, confiança, rastreabilidade |

A Phase 02 recebeu logo principal, vertical, simplificada e prancha oficial. OFFICIAL_BRAND_ASSET = IMPORTED_USER_SUPPLIED. Azul `#17295B`, Ouro `#DAA84F`, Vermelho `#D8232A`, Branco `#FFFFFF`, Cinza `#F3F4F6`: valores oficiais escritos na prancha. Tipografia: Manrope para títulos e Inter para interface, com fallback local documentado. Os tokens semânticos derivados permanecem provisórios; [especificação de cores e contraste](BRAND_COLOR_SPEC.md).

A [prévia anterior](FRONTEND_VISUAL_BASE.md), com teal e monograma provisório, permanece preservada. A nova foundation usa os assets oficiais, ação primária azul, acento inteligente ouro e nome Minha Visão. O site anterior será tratado na Phase 03.

## UX principles

1. Automation != Professional Decision: automação prepara/classifica/propõe; humano revisa, decide e aprova.
2. Action-oriented dashboards: mostrar pendências e próximos passos válidos, com contexto suficiente.
3. Traceability always accessible: oferecer rastreabilidade dentro das permissões do usuário.
4. Permissions constrain customization: personalização não concede dados ou ações adicionais.
5. Client portal simpler than internal app: tarefas objetivas, linguagem simples e privilégio mínimo.
6. Desktop-first responsive web application: priorizar trabalho contábil desktop com adaptação responsiva.
7. Accessibility: navegação por teclado, foco visível, labels, contraste, mensagens compreensíveis e estados não dependentes só de cor; critérios verificáveis na Phase 02.
8. Consistent status language: mapear status reais para rótulos claros, distinguindo sugestão, revisão, aprovação humana, rejeição, pendência e bloqueio.

A plataforma não substitui o contador. Não usar “aprovado” para regra executada, sugestão de IA ou revisão apenas aberta. Não chamar pré-lançamento de escrituração oficial.

## Arquitetura conceitual de navegação

| Grupo | Módulos previstos |
| --- | --- |
| INÍCIO | Minha Visão |
| OPERAÇÃO | Caixa de entrada, Documentos, Tarefas, Agenda |
| FISCAL | NF-e, XML, Documentos fiscais |
| FINANCEIRO | Bancos, OFX, Conciliação |
| CONTÁBIL | Regras, Classificação, Propostas, Revisão, Aprovação |
| CLIENTES | Empresas, Relacionamento |
| PORTAL | Área externa do cliente |
| OBRIGAÇÕES | Impostos, Vencimentos |
| GOVERNANÇA | AccountLock, Auditoria, Privacidade |
| ADMINISTRAÇÃO | Usuários, Permissões, Configurações |

Este mapa organiza evolução, não afirma que todos os módulos existem. [Arquitetura atual](CURRENT_SYSTEM_ARCHITECTURE.md) determina reuso; [roadmap](PRODUCTIZATION_ROADMAP.md) determina fases. Fluxo orientador: receber → validar → interpretar → aplicar regras → gerar proposta → identificar exceções → revisar → aprovar → registrar → acompanhar.

## Minha Visão

DASHBOARD NAME: **Minha Visão**. Capacidades demonstradas localmente na Phase 02: ADD WIDGET, REMOVE WIDGET, MOVE WIDGET, RESIZE WIDGET, SAVE VIEW. Persistência somente em memória; DASHBOARD_PERSISTENCE = DEFERRED_TO_PRODUCT_PHASE.

**VISIBILITY <= AUTHORIZATION**. Layout salvo registra preferências, não direitos. Ao abrir/restaurar visão, aplicar permissões vigentes; revogação de CompanyAccess remove acesso independentemente do layout. Esconder botão não substitui negação na API. Widgets agregados exigem consulta autorizada que represente o total correto; não somar uma página de resultados como total global. Não há persistência de visão implementada na prévia atual.

## Linha da Decisão

Nome oficial: **Linha da Decisão**. SOURCE → PROCESSING → RULE → PROPOSAL → REVIEW → APPROVAL. O [mapa de AuditEvent e gaps](PRODUCT_FLOW.md) é a referência técnica. Diferenciar autor, origem do processamento, versão de regra, revisão/hash e decisão humana; nunca inventar evento ausente.

## Saídas esperadas da Phase 02

Tokens/componentes e protótipos dos fluxos prioritários entregues com linguagem de status ligada aos contratos, estados vazio/carregamento/erro/sem acesso e regras de acessibilidade. HTML/CSS/JavaScript nativos preservados. Não houve alteração de APIs/regras/gates. Inspeção visual renderizada e leitor de tela permanecem pendentes por indisponibilidade de navegador nesta sessão; limites e evidências em DESIGN_SYSTEM_SPEC.
