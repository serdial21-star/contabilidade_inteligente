# Apuração de ICMS determinística — CSV e PDF com texto

Artefatos da T-0007 para o workflow `ferramentas-ia/apuracao-icms`. Esta etapa não usa IA, OCR nem dados reais. O workflow permanece inativo no arquivo versionado e precisa de revisão, importação e teste manual antes da publicação.

## Contrato canônico

`raicms_parser.js` expõe `parseCsv(texto)`, `parsePdfText(textoOuPaginas)` e `validate(modelo)`. Os dois parsers produzem o mesmo modelo, salvo `origem` (`csv` ou `pdf_texto`): ano e `periodos[]`, cada qual com competência, CFOPs e cinco colunas monetárias de entradas/saídas, subtotais 1/2/3 e 5/6/7, totais lidos e `resumos` 001–014 por tipo (`proprio`, `st_dentro`, `st_fora`). Cada resumo preserva deduções detalhadas e nomes normativos E110/E210.

Valores monetários são centavos inteiros seguros. Não há tolerância nem conversão por `parseFloat` ou `Number` no domínio. A única conversão decimal ocorre em `spreadsheetRows`, na fronteira de saída para o Google Sheets, para preservar o contrato numérico do workflow anterior e as fórmulas da planilha.

CSV aceita um ou vários meses do mesmo ano e usa cada título como contexto sequencial. CFOP pode reaparecer em meses diferentes, mas não dentro do mesmo período. O PDF é extraído com `joinPages: false`: cada página é associada à competência e ao tipo indicados pelo próprio título, mesmo quando ele vem no fim. Antes da classificação, espaços são normalizados e uma linha formada por exatamente duas cópias idênticas é reduzida a uma única cópia; isso trata o negrito simulado por sobreposição no gerador do relatório sem aceitar repetições diferentes. Depois, cada linha é tokenizada em valores monetários e rótulo normalizado; o rótulo pode vir antes ou depois dos valores e pode estar grudado ao primeiro ou ao último valor, como ocorre na saída real do `Extract From File` do n8n 2.6.4. Página numérica sem título, títulos de competências distintas na mesma página e anos distintos falham fechado.

Blocos ST são opcionais. Períodos marcados “SEM MOVIMENTAÇÃO”, com subtotais e totais zerados, são válidos. Quando o PDF omite o lado e os dois totais têm o mesmo valor, os candidatos são atribuídos, na ordem, ao primeiro lado compatível ainda vazio; candidatos excedentes continuam não interpretados e bloqueiam a conferência. Se o arquivo inteiro não contiver CFOP, não há planilha a gerar: o workflow responde `422`, `success: false`, mensagem “Sem movimentação de CFOP no período informado” e lista de divergências vazia. Nesse caso, `422` comunica “nada a gerar” à tela atual, não falha de conferência.

## Conferências bloqueantes

- soma dos CFOPs por grupo e coluna igual ao subtotal lido;
- soma dos subtotais igual ao total lido;
- `004 = 001 + 002 + 003`;
- `008 = 005 + 006 + 007`;
- `010 = 008 + 009`;
- `011 = max(004 - 010, 0)`;
- `013 = max(011 - 012, 0)`;
- `014 = max(010 + 012 - 004, 0)`;
- toda linha numérica precisa ser interpretada.

O briefing simplificava 013 como `011 - 012` e 014 como o saldo credor antes das deduções. O Guia 3.2.2 prevalece: 013 não pode ser negativo e o excesso de deduções integra 014. Essa correção está implementada acima.

As igualdades internas também são aplicadas aos resumos ST, conforme o E210. Os cruzamentos 001 com o imposto total das saídas e 005 com o imposto total das entradas são exclusivos do resumo próprio e geram alerta, não bloqueio. O Guia determina inclusões e exclusões que não podem ser reconstruídas com segurança a partir deste relatório agregado.

Os rótulos “Adicional relativo ao fundo de combate a pobreza” e “Dedução relativa ao incentivo a cultura” são preservados como detalhamento informativo de 012. Não foi encontrada fonte normativa que obrigue a soma dessas duas linhas a ser igual a 012; eventual diferença gera alerta, nunca bloqueio.

## Falha fechada

CFOP inválido ou repetido, competência divergente, valor fora do contrato, PDF sem texto útil, campo obrigatório ausente e linha numérica não reconhecida impedem Drive e Sheets. O workflow responde `422` com `success: false` e divergências. PDF é identificado pela assinatura `%PDF`, não pela extensão.

## Referências oficiais

- CONFAZ, Convênio SINIEF s/nº, de 15/12/1970, Livro Registro de Apuração do ICMS modelo 9, acesso em 04/10/2026: https://www.confaz.fazenda.gov.br/legislacao/ajustes/sinief/cvsn_70
- SPED, Guia Prático EFD-ICMS/IPI versão 3.2.2, atualização de 11/02/2026, registro E110, páginas 223–225 do PDF (páginas impressas 224–226), acesso em 04/10/2026: https://www.gov.br/sped/pt-br/assuntos/escrituracoes-digitais/efd-icms-ipi/manuais-e-documentos-tecnicos/guia-pratico-da-efd-icms-ipi-3-2.2/@@display-file/file
- SPED, mesmo Guia, registro E210, páginas 229–232 do PDF (páginas impressas 230–233), acesso em 04/10/2026.
- n8n, nó `Extract From File` v1, operação PDF e campo binário de entrada, código oficial consultado em 04/10/2026: https://github.com/n8n-io/n8n/blob/master/packages/nodes-base/nodes/Files/ExtractFromFile/actions/pdf.operation.ts

No código oficial do n8n consultado, `joinPages: false` entrega `text` como uma lista de textos, um por página. O workflow preserva essa lista até `parsePdfText`.

## Validação local/CI

```text
node --test docs/integration/system_a_icms_apuracao/raicms_parser.test.js
python -m pytest tests/unit/test_system_a_icms_apuracao_assets.py
```

As fixtures são integralmente sintéticas. Não substituir por exportação fiscal real.
