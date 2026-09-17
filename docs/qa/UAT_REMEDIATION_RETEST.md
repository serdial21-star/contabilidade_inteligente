# Phase 14 — Reteste humano impactado

Use somente dados sintéticos; não altere gates, Sistema A ou Domínio.

1. Abra `#financial`, `#fiscal`, `#accounting`, `#documents` e `#inbox`; use F5.
2. Provoque erro de arquivo NF-e, filtre e navegue para OFX; o alerta não cruza telas.
3. Importe NF-e com empresa emitente, destinatária, divergente e sem CNPJ cadastrado.
4. Teste múltiplos XML e pasta compatível; confira o resumo isolado por arquivo.
5. Deixe Data contábil vazia e confira a data do XML; teste override explícito.
6. Teste OFX com conta cadastrada, divergente, de outra empresa e sem cadastro.
7. Confira detalhe OFX, paginação, filtros e reset com identificadores mascarados.
8. Confira proposta: regra, origem, conta código+nome, linhas, valores, status e histórico.
9. Combine/limpe filtros em NF-e, OFX, contábil, documentos e inbox.
10. Confira ajuda contextual da data e expiração.
11. Confira Linha da Decisão horizontal no desktop e vertical em tela menor.
12. Confira grade 4/3/2/1; W004 abre inbox; W008/W009 não simulam destino.

Resultado esperado: `HUMAN UAT: RETEST_REQUIRED`; o signoff continua humano.

## Incremento operacional direcionado

13. Em Empresa, cadastre uma conta bancária, edite nome/apelido sem trocar o número, desative-a e confirme que OFX é colocado em quarentena; reative e repita o import.
14. Confirme máscara do número bancário e ausência de dados de outra empresa.
15. Em Documento, salve número, descrição e observação; recarregue a página e pesquise pelo número e pela descrição.
16. Na fila contábil, combine conta, origem, documento, regra, data contábil e status; limpe os filtros e confira paginação.
17. No plano de contas, pesquise por código, nome, natureza e status.
18. Confira a grade do dashboard em 4/3/2/1 colunas; apenas W010 e widgets ampliados ocupam duas colunas.

Resultado permanece `HUMAN UAT: RETEST_REQUIRED` até execução e signoff humanos.
