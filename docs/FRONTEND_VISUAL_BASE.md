# Base visual — Contabilidade Inteligente by Serdial21

## Atualização — Phase 02

A nova entrada é [app/prototype.html](../app/prototype.html): sete telas navegáveis,
galeria de componentes, tokens oficiais, widgets locais e dados sintéticos.
Ver [DESIGN_SYSTEM_SPEC](DESIGN_SYSTEM_SPEC.md) e [instruções](../app/README.md).
As quatro imagens oficiais fornecidas pelo usuário foram importadas para
`ui/assets/brand/`, sem edição. O site, `app/index.html`, `app/dashboard.js` e
`ui/design-system.css` anteriores permanecem preservados. As seções abaixo
descrevem essa prévia histórica, não a identidade/tokens vigentes da foundation.
VISUAL_BASE_REUSE = PARTIAL; não houve integração backend ou deploy.

## Execução local

Abra `site/index.html` no navegador para a landing page ou `app/index.html`
para o dashboard. Ambos funcionam sem build, instalação ou conexão externa.
Também podem ser abertos com Live Server no VS Code. Compartilham
`ui/design-system.css`; mantenha as três pastas no mesmo nível.

HTML, CSS e JavaScript nativos reduzem custo de manutenção e não adicionam
dependências estruturais ao backend. Não há fontes, scripts ou imagens de CDN.
O monograma tipográfico é provisório; nenhum arquivo de logo foi fornecido.

## Design System

- Azul profundo `#1A2B4C`: marca, sidebar e hierarquia.
- Dourado `#C8A97E`: assinatura, detalhes e indicador de revisão.
- Teal `#007B78`: ações principais e automação.
- Verde `#216C48`: aprovação humana; azul `#285D95`: processamento/sugestão.
- Âmbar `#865711`: revisão; cinza: inativo; vermelho `#AA3434`: bloqueio.
- Tokens CSS centralizados, espaçamento consistente, cards leves, tabelas
  legíveis e layout adaptativo. Status usam texto e símbolos, além de cor.
- Navegação por teclado, foco visível, link de salto, labels e diálogos nativos.

## O que funciona na prévia

Landing, mockup HTML, fluxo de sete etapas e módulos. Dashboard com seis
registros sintéticos, indicadores, busca, filtros por status/módulo, estado
vazio, detalhes rastreáveis e consulta ilustrativa de bloqueio.

Nenhum login é simulado como autenticação real. A identidade exibida é
ilustrativa. Aprovação e upload permanecem indisponíveis. Não há persistência,
fetch, localStorage, dado real ou efeito contábil. A revisão visual não é UAT
contábil nem aprovação de regras.

## Integração futura: preservar a arquitetura aprovada

Navegador → API FastAPI autenticada → casos de uso → MySQL/MariaDB.
O seletor de company nunca autoriza acesso. A API revalida identidade,
membership, CompanyAccess, permissão, revisão/hash, bloqueios e idempotência.
Contratos reais: `OPERATIONAL_API_MVP.md` (lista/detalhe, importação por bytes,
aprovação/rejeição, exceções e histórico). Os cards agregados precisam de um
contrato backend apropriado; não apresentar amostra paginada como total global.

Uma integração com Make.com exige contrato próprio autorizado no backend.
Não colocar webhook secreto no navegador, não fornecer acesso direto ao banco,
não delegar publicação de regras/aprovação ao Make e não criar banco duplicado.
Essa integração não está implementada nesta base visual.

Hostinger poderá servir os assets estáticos; a compatibilidade do plano com o
backend Python deve ser verificada antes de publicar. Não foi feito upload ou
deploy. Exposição externa, migração 0012 e dados reais mantêm seus gates em
`PILOT_GO_NO_GO.md`. Esta nova base visual deve ser revisada antes de integrar
o conjunto previamente preparado para RC1.
