# Status do leiaute — Domínio Sistemas com Separador

## Informações oficiais incorporadas

- Fonte oficial registrada em `SOURCE_REGISTRY.md`.
- O leiaute usa o separador `|`.
- Registros de lançamentos em lote identificados:
  - `6000` — Lançamentos em Lote;
  - `6100` — Lançamentos em Lote – Lançamentos;
  - `6110` — Lançamentos em Lote – Lançamentos – Centro de Custos;
  - `6130` — Lançamentos em Lote – Lançamentos – DFC.

## Não incorporado / não aprovado

- arquivo ou modelo oficial aplicável ao piloto;
- golden file oficial e resultado esperado;
- versão exata do produto Domínio homologada para o piloto;
- campos completos, ordem, obrigatoriedade, tipo, formato e semântica de cada
  registro utilizado;
- regras de codificação, escape, linhas, terminadores e validação;
- mapping canônico → Domínio revisado e aprovado;
- mapeamento das contas internas para os códigos reduzidos aplicáveis no
  destino.

`PENDÊNCIA: GOLDEN FILE OFICIAL DOMÍNIO NECESSÁRIO`.

Enquanto qualquer item desta seção estiver pendente, o `DominioConnector` deve
recusar configuração, geração e disponibilização de exportação.
