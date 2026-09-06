# ADR 0007 — Importador CSV bancário configurável

## Status

Aceita na Execução 08, em 06/09/2026.

## Decisão

- O parser CSV é genérico e recebe um `CsvBankLayout`; não há adaptador ou
  condição baseada em banco.
- Um layout identifica colunas de data, descrição, documento, débito, crédito,
  valor, saldo e referência externa, além de delimitador, encoding, formato de
  data, cabeçalho e convenções numéricas.
- Layout publicado é imutável. Qualquer alteração material cria novo rascunho
  com versão incrementada, que deve ser publicado antes de uso.
- Preview exige layout publicado e produz transações válidas e issues por
  linha; não persiste extrato ou transação.
- `AMOUNT_PRESERVED` conserva literalmente o sinal da coluna de valor.
  `DEBIT_CREDIT_COLUMNS` calcula crédito menos débito conforme escolha
  declarada no layout. Não há inversão implícita de sinal.
- Valores são `Decimal` finitos com, no máximo, duas casas nesta fatia.

## Consequências

O preview é a etapa obrigatória para validar um arquivo e seu layout antes da
importação definitiva. A persistência do layout e a ligação de uma importação
definitiva ao `BankStatement` permanecem na fronteira de workflow posterior;
o parser já preserva a versão exata do layout no resultado do preview.
