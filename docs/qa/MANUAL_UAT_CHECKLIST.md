# Phase 14 — Checklist manual executável

## Preparação segura

1. Usar build do commit registrado no signoff em ambiente local/homologação
   isolado, `authMode=synthetic` e `dataMode=synthetic`.
2. Confirmar que não há IdP, System A, Domínio ou dado real conectado.
3. Abrir DevTools somente para confirmar viewport/overflow e erros; não alterar
   storage ou autorização para forçar resultado.
4. Executar em 1440×900, 1280×800, 768×1024 e 390×844.

## Navegação, contexto e estados

1. Abrir o shell; confirmar marca, estado autenticado sintético, usuário e
   empresas autorizadas.
2. Percorrer Minha Visão, Empresas, Documentos, Fiscal, Financeiro, Contábil,
   Revisões e detalhes com Linha da Decisão.
3. Em Minha Visão confirmar W003, W004, W005, W006 e W010; observar loading,
   vazio, erro e conteúdo sem confundir esses estados.
4. Abrir Empresa A, Documentos/Fiscal/Financeiro/Contábil; trocar para Empresa B
   e confirmar que nenhum nome, linha, valor, documento ou timeline de A sobra.
5. Recarregar uma rota suportada e abrir deep link; confirmar autorização e
   fallback compreensível, sem depender de conteúdo anterior em memória.

## Golden NF-e e decisão profissional

1. Usar somente o XML sintético aprovado; importar e observar feedback.
2. Confirmar documento, detalhe fiscal, regra aplicável e proposta.
3. Conferir evidência, explicação, débitos/créditos, totais iguais e status.
4. Confirmar que “sugestão automatizada” é visual/textualmente distinta de
   “decisão profissional”.
5. Aprovar com perfil autorizado; verificar status e Linha da Decisão.
6. Repetir ação apenas conforme cenário controlado e confirmar ausência de
   efeito duplicado.
7. Em cenário separado, rejeitar; não inventar motivo ausente no schema.
8. Exercitar duplicata, XML inválido e NF-e sem regra; não deve surgir proposta
   fabricada ou detalhe interno do parser.

## OFX

1. Importar OFX sintético; conferir statement, datas, sinais, descrições seguras
   e conta mascarada.
2. Abrir transações/traceabilidade disponíveis.
3. Importar OFX inválido; confirmar erro seguro e ausência de conjunto parcial.
4. Confirmar que nenhuma proposta contábil é criada a partir do OFX.

## Responsividade e visual

Em cada viewport, verificar ausência de overflow horizontal, sobreposição,
ação escondida, tabela ilegível, valor crítico truncado ou drawer inacessível.
Conferir azul estrutural, ouro como inteligência, vermelho reservado, estados
com texto/ícone além de cor, tipografia, espaçamento, cartões, tabelas, botões e
forms. Não modificar assets oficiais.

## Teclado e acessibilidade

1. Recarregar e usar somente `Tab`, `Shift+Tab`, `Enter`, `Space` e `Escape`.
2. Navegar sidebar/menu, abrir detalhe, fechar drawer/dialog, acessar revisão e
   executar decisão em cenário sintético autorizado.
3. Confirmar foco sempre visível, ordem lógica e ausência de keyboard trap.
4. Verificar labels, nomes acessíveis, `aria-expanded`/estado, headings em ordem,
   tabelas semânticas e mensagens anunciáveis.
5. Registrar limitações factuais; não declarar certificação WCAG.

## Erros e signoff

Exercitar estados representativos 401, 403, 404, 409, 413, 422, 429 e erro 500
seguro pelo harness autorizado. A UI não pode mostrar stack trace, JSON bruto,
SQL ou exceção interna. Registrar cada resultado em `UAT_SIGNOFF.md`, anexar
evidências e abrir apenas defeitos realmente observados.
