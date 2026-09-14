# Accessibility Guidelines

Fundação orientada a WCAG AA quando aplicável, sem declaração de certificação. Escopo: [protótipo](../app/prototype.html), [tokens](../ui/tokens.css) e [estilos](../ui/foundation.css). A revisão no navegador/leitor de tela ainda deve ser feita; a sessão não dispõe de navegador conectado.

| Área | Implementação / critério de verificação |
| --- | --- |
| Teclado | Links e botões nativos; Tab/Shift+Tab; Enter/Space; nenhuma ação exige arrastar. Widgets possuem mover antes/depois e ampliar/reduzir. |
| Foco | `:focus-visible` com contorno de 3px; skip link; foco no main ao trocar rota e retorno ao acionador de dialog quando presente. |
| Navegação | `nav` rotulado, `aria-current`, nomes de botão, contexto/empresa com label e menu móvel em dialog. |
| Diálogos | `dialog.showModal()` nativo, `aria-labelledby`, botão Fechar e Escape nativo; verificar contenção/retorno de foco no navegador suportado. |
| Formulários | Labels associados por envolvimento; erro com `aria-invalid` e `aria-describedby`; estados disabled/read-only/success; seleção múltipla com instrução textual. |
| Status | Texto e ícone além de cor. SVG decorativo `aria-hidden`; ações críticas sempre rotuladas. |
| Alertas | Ícone, título e mensagem; aviso de resultado com `role=status`/aria-live; erro de período com `role=alert`. |
| Tabelas | Cabeçalho semântico, ordenação `aria-sort`, checkbox nomeado, paginação rotulada e região rolável acessível por teclado. |
| Carregamento | Skeleton decorativo com texto de estado; spinner com descrição; sem bloquear a aplicação inteira. |
| Contraste | Combinações medidas em [BRAND_COLOR_SPEC](BRAND_COLOR_SPEC.md). Ouro é acento, não texto claro sobre branco; borda de campo tem contraste próprio. |
| Motion | Animações limitadas a loading; `prefers-reduced-motion` remove animações/transições. |
| Imagens | Assets oficiais inteiros, proporção preservada e alt com nome do produto; sem texto importante só na imagem. |
| Erros/acesso | Mensagens uniformes, sem IDs de recursos protegidos, SQL, caminho interno, segredo ou stack trace. |

Verificação manual futura: desktop 1440/1280px, tablet 800px, mobile 390/320px; zoom 200% e reflow; operação completa só por teclado; foco após fechar drawer e remover widget; leitura de tabelas/erros; ausência de overflow da página (tabela pode rolar dentro da região). Leitores de tela e comportamento de dialog variam por navegador: testes VM não comprovam esses itens.

Densidade COMFORTABLE é o padrão. COMPACT aparece desabilitada como futura. Em mobile, widgets ficam em coluna única e sidebar vira drawer. Desktop preserva débito/crédito lado a lado; mobile empilha mantendo rótulos explícitos.
