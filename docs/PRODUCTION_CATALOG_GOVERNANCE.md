# Governança do catálogo de produção

Data da decisão: 08/09/2026

## Objetivo

O catálogo operacional substitui, na composição de produção, o
`SyntheticCatalog` usado pela jornada vertical. O catálogo sintético permanece
nos testes como double explícito e não é carregado pelo bootstrap de produção.

Não foram criadas regras, contas ou tratamentos contábeis padrão. Todo conteúdo
deve ser informado e revisado pelo escritório responsável.

## Inventário anterior

Antes desta execução estavam somente em memória:

- `Ledger`, plano e `AccountVersion`;
- `AccountingRuleVersion` e `RuleSetRelease`;
- `MappingVersion` e `MappingEntry`;
- `WorkflowVersion` usado para preparar a aprovação;
- `PostingPolicy` da jornada;
- a composição `PreparationPlan` entregue por `SyntheticCatalog`.

A jornada e seus checkpoints já eram persistidos, mas recebiam essas versões de
uma fixture. AccountLock e AuditEvent já possuíam persistência própria.

## Decisão de persistência

O catálogo é um agregado publicado atomicamente em duas tabelas:

- `production_catalogs`: identidade estável, tenant, empresa e nome;
- `production_catalog_versions`: versão, estado, vigência, snapshot JSON
  completo, SHA-256, predecessor e responsáveis por criação/revisão/publicação.

O snapshot JSON é tipado e validado pela aplicação. Ele contém IDs e números de
versão independentes para:

- ledger e plano de contas;
- contas e suas versões/hierarquia;
- regras, condições DSL e versões;
- release de regras e membros exatos;
- mapping, versão e entradas DE/PARA;
- workflow, versão, papel aprovador e papel responsável;
- política versionada de valor e precisão.

Esse formato preserva uma fotografia autocontida e canônica do conjunto que foi
revisado. A publicação não pode misturar componentes de momentos diferentes. O
hash SHA-256 é verificado antes de o snapshot ser entregue à jornada.

As colunas relacionais mantêm FKs compostas `(tenant_id, company_id)`, um único
catálogo raiz por empresa, cadeia de supersessão, unicidade do número e índice por
tenant/empresa/estado/vigência. O conteúdo não substitui esses guards de escopo.

## Estados e transições

```text
DRAFT -> REVIEW -> PUBLISHED
```

- `DRAFT`: editável somente pela criação de uma versão ainda não publicada;
- `REVIEW`: conteúdo congelado para conferência independente;
- `PUBLISHED`: imutável e elegível para uma jornada na sua vigência.

Não existe transição de PUBLISHED para DRAFT. Uma alteração usa
`create_next_draft`, cria novos IDs de versão para todos os componentes,
incrementa `version_no` e referencia `supersedes_version_id`. A versão publicada
anterior permanece consultável e não é reescrita ou removida.

Um listener ORM recusa update de versão já publicada e qualquer delete de
histórico. Concorrência também é protegida por lock pessimista e UNIQUE do número
da versão; conflito exige rollback e releitura.

## Validações determinísticas

Antes de persistir um draft são verificados:

- moeda e vigência;
- chaves e códigos de contas;
- natureza, saldo normal, conta sintética/lançável;
- existência e ausência de ciclos na hierarquia;
- referências de débito/crédito;
- operadores permitidos da DSL (`EQ` e `CONTAINS`);
- evidência explícita de testes da regra antes da publicação;
- colisão exata de regra com mesma prioridade e condições;
- alvos das entradas de mapping;
- responsáveis do workflow;
- política explícita de valor e casas decimais suportada pela jornada atual.

Nenhuma expressão arbitrária, `eval` ou código configurável é executado.

## Autorização e segregação

Os comandos usam o `AuthorizationService` existente:

- `catalog.manage`: criar draft, criar nova versão e submeter para revisão;
- `catalog.review`: publicar.

O tenant vem exclusivamente da identidade OIDC. `company_id` do request é
seletor e exige CompanyAccess, RoleBinding e permissão ativos. O autor da versão
não pode publicá-la, mesmo que receba por engano as duas permissões.

Os responsáveis ficam registrados em `created_by`, `reviewed_by` e
`published_by`. O workflow publicado também registra o papel responsável e o
papel aprovador; a jornada usa esses papéis para WorkItem, ApprovalStep e a
revalidação da decisão humana.

## API operacional

- `POST /api/v1/catalogs`: cria a versão 1 em DRAFT;
- `POST /api/v1/catalogs/versions/{id}/next`: cria nova versão a partir de uma
  versão publicada;
- `POST /api/v1/catalogs/versions/{id}/review`: DRAFT para REVIEW;
- `POST /api/v1/catalogs/versions/{id}/publish`: REVIEW para PUBLISHED.

Todos exigem Bearer token válido. IDs de catálogo/empresa nunca concedem acesso.
Escopo inexistente ou não autorizado retorna negação uniforme; conflitos de
estado/versão retornam conflito sem expor conteúdo do outro tenant.

## Uso pela jornada

`create_nfe_to_dominio_runtime` usa `SqlAlchemyJourneyCatalog` quando nenhum
catálogo é injetado. O adaptador seleciona, pela data contábil, a versão
PUBLISHED vigente mais nova do tenant/empresa, verifica o hash e reconstrói o
`PreparationPlan`.

A jornada persiste novamente esse plano dentro do checkpoint, preservando as
versões exatas usadas pelo documento. Uma publicação futura não altera jornada
ou aprovação histórica.

Mappings são parte do snapshot governado, embora a jornada NF-e atual use a
regra publicada com alvos explícitos de conta. Não foi criada uma etapa contábil
nova para forçar o uso do mapping onde ele não existia.

## Auditoria

As ações abaixo geram AuditEvent na mesma unidade de trabalho:

- `catalog.draft.created`;
- `catalog.review.requested`;
- `catalog.version.created`;
- `catalog.published`.

O evento contém somente estado, número da versão e hash. O snapshot completo,
nomes e condições não são copiados para auditoria.

## Evidência E2E

O teste `test_production_catalog_e2e.py` comprova:

1. configuração real em DRAFT;
2. passagem para REVIEW;
3. negação da autopublicação;
4. publicação por segundo responsável;
5. seleção do catálogo persistido por uma NF-e;
6. criação da versão 2 com regra alterada;
7. nova revisão e publicação;
8. novo documento usando versão 2;
9. versões 1 e 2 preservadas com hashes, responsáveis e componentes próprios;
10. integridade dos AuditEvents;
11. negação cross-tenant.

O E2E instancia o runtime sem `SyntheticCatalog`, comprovando a composição de
produção. Os testes sintéticos anteriores continuam executando como regressão.

## Migration e operação

A revision `20260908_0011` cria as tabelas e as permissões `catalog.manage` e
`catalog.review`. Ela deve ser ensaiada no Migration Lab e aplicada por upgrade
forward-only após backup. O Runtime não deve receber downgrade.

Antes do piloto ainda é necessário cadastrar conteúdo aprovado do escritório,
conceder os novos papéis sob revisão e executar UAT contábil. A existência do
mecanismo não equivale à aprovação de um plano ou regra real.
