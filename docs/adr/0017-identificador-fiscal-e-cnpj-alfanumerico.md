# ADR 0017 — Identificador fiscal canônico e CNPJ alfanumérico

## Status

Aceita por solicitação explícita do usuário em 2026-09-29. Esta decisão
complementa o [ADR 0013](0013-importacao-manual-dados-sistema-a.md) e substitui
a regra anterior que aceitava CPF/CNPJ apenas pelo tamanho.

## Contexto

O lote piloto revelou dois cadastros com nomes diferentes e o mesmo CPF. O
e-mail usado no login identifica uma conta de acesso, mas não identifica uma
pessoa ou empresa para fins fiscais. Permitir duas `companies` do mesmo tenant
com o mesmo CPF/CNPJ criaria duas representações concorrentes da mesma pessoa
fiscal e tornaria ambígua a associação de documentos.

A Receita Federal introduziu o CNPJ alfanumérico mantendo 14 posições: as
primeiras 12 aceitam letras maiúsculas ASCII e números, e as duas últimas
continuam numéricas e calculadas por módulo 11. CNPJs numéricos existentes
continuam válidos. Fontes oficiais:

- <https://www.gov.br/receitafederal/pt-br/acesso-a-informacao/acoes-e-programas/programas-e-atividades/cnpj-alfanumerico>
- <https://www.gov.br/receitafederal/pt-br/centrais-de-conteudo/publicacoes/documentos-tecnicos/cnpj>
- <https://www.gov.br/receitafederal/pt-br/assuntos/noticias/2026/julho/receita-federal-gera-o-primeiro-cnpj-em-formato-alfanumerico>

## Decisão

1. E-mail e identificador fiscal têm responsabilidades diferentes. O e-mail
   normalizado identifica o acesso; CPF/CNPJ identifica a pessoa fiscal.
2. Dentro de um tenant, um CPF/CNPJ canônico continua único. Nomes diferentes
   com o mesmo documento não criam duas `companies`: o cadastro de origem deve
   ser corrigido ou os diferentes contatos/serviços devem se relacionar à
   mesma empresa.
3. Persistimos CPF/CNPJ sem máscara, em maiúsculas ASCII. Pontos, barra, hífen
   e espaços são aceitos apenas como separadores de entrada e a máscara é
   aplicada somente na apresentação.
4. CPF válido contém 11 dígitos e passa pelos dois dígitos verificadores. CNPJ
   válido contém 14 posições, aceita `[0-9A-Z]` nas 12 primeiras posições,
   exige dois dígitos nas posições finais e passa pelo cálculo oficial de
   dígitos verificadores.
5. Caracteres fora do alfabeto canônico, comprimento incorreto, documentos de
   dígitos repetidos e dígitos verificadores incorretos são rejeitados.
6. A validação local confirma estrutura e dígitos verificadores; ela não prova
   existência, titularidade nem situação cadastral na Receita Federal. Uma
   consulta oficial futura exigirá integração e decisão próprias.
7. Registros inválidos são pulados com motivo explícito. O importador não
   corrige, inventa nem sobrescreve identificadores.
8. Registros de teste não recebem CPF/CNPJ válido inventado em produção. Devem
   ser classificados como `Lead` para ficarem fora do import, corrigidos com o
   documento real autorizado ou mantidos em ambiente sintético separado.

## Compatibilidade e impacto

`companies.tax_identifier` já é `VARCHAR(32)`, portanto nenhuma migration é
necessária. A comparação de CNPJ em NF-e passa a usar a mesma forma canônica,
sem remover letras. A mudança afeta novos imports; não reescreve registros
existentes e não altera histórico de auditoria.

O Sistema A precisa aplicar a mesma regra na interface e no fluxo de escrita
do n8n. Alterar apenas a máscara do frontend não é suficiente. Essa adaptação
depende da revisão do workflow `/admin/novo-cliente-v2` e não é feita
silenciosamente neste repositório.

## Motivos estáveis do relatório

- `sem_identificador_fiscal`;
- `formato_identificador_fiscal_invalido`;
- `cpf_digito_verificador_invalido`;
- `cnpj_digito_verificador_invalido`;
- `identificador_fiscal_em_uso`.
