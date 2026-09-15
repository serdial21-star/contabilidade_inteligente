# Módulo Financeiro — Phase 07

## Escopo suportado

O módulo operacional suporta arquivos **OFX 1.x (SGML) e OFX 2.x (XML)** aceitos pelo `SafeOfxParser`. Não amplia formatos e não cria plataforma bancária. Os dados exibidos são evidência importada; não representam saldo oficial do banco ou do sistema contábil externo.

## Importação e deduplicação

O frontend reutiliza `POST /api/v1/operations/companies/{company_id}/imports/ofx` com bytes do arquivo, tipo permitido, `X-Filename` e `Idempotency-Key`. O caso de uso existente revalida autenticação, tenant, `CompanyAccess`, `journal.propose`, tamanho, tipo e conteúdo; persiste `BankStatement` e `BankTransaction` sem duplicar o importador.

O identificador FITID é preservado quando disponível; o fingerprint canônico é usado como alternativa. Reentrega idempotente não cria novo efeito e conteúdo divergente com a mesma chave gera conflito. A UI apresenta o resultado, mas não cria estado financeiro para representar retry.

## Extratos e transações

`GET .../bank-statements` lista extratos paginados. O detalhe `GET .../bank-statements/{id}` inclui transações paginadas e filtros por texto, crédito/débito e intervalo de lançamento. Instituição, tipo, período, moeda, saldos e instante de importação são projetados quando existem.

Agência e conta são mascaradas no serviço de aplicação. Identificadores completos, `artifact_id`, storage e conteúdo OFX não saem no contrato público. O vínculo `document_receipt_id` permite voltar à Central de Documentos.

## Semântica monetária

Valores continuam `Decimal` no backend. A política `OFX_TRNAMT_SIGN_PRESERVED_V1` preserva o sinal: crédito é positivo e débito é negativo. A apresentação usa simultaneamente rótulo textual e sinal, sem depender apenas de cor e sem reinterpretar o valor.

## Matching, sugestões e conciliação

O repositório possui apenas políticas puras de reconciliação; não há caso de uso persistente e autorizado para consultar ou gravar matched/unmatched, sugestão ou match manual. Logo, matching, sugestões determinísticas, conciliação e match manual permanecem **DEFERRED**. A UI declara essa fronteira e não oferece ação fictícia. W009 também permanece adiado.

## Autorização, exceções e gaps

Leitura exige `company.read`; importação preserva `journal.propose`. Todas as consultas e mutações são escopadas por tenant e empresa e revalidam `CompanyAccess`; IDs não autorizam acesso.

Falhas de parse/importação aparecem como erro seguro na Central de Documentos e podem alimentar W004 por projeção existente. Ainda não existe uma exceção financeira específica de unmatched, porque isso dependeria da persistência de conciliação. Upload em lote, malware scanning e reconciliação operacional são gaps conhecidos.
