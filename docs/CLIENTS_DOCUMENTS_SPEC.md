# Empresas e Central de Documentos — Phase 06

## Integração Phase 07

Detalhes canônicos de NF-e e extratos OFX agora retornam o `document_receipt_id` autorizado, enquanto o detalhe da Central projeta o ID fiscal ou financeiro relacionado. A UI navega com segurança nos dois sentidos. Duplicidade, quarentena e falha continuam pertencendo ao intake/documento existente; os módulos Fiscal e Financeiro não criam evidência paralela. A rastreabilidade melhora até o receipt e suas issues, mas a Linha da Decisão completa permanece na Phase 09.

## Terminologia e mapa de implementação

“Clientes” é linguagem comercial. No produto autenticado, o recurso técnico é
`Company`, pertencente a um `Tenant` (o escritório contábil). A visibilidade de
cada empresa depende de `CompanyAccess` vigente para a membership autenticada.
Não existe entidade `Client`, tabela paralela ou CRM nesta fase.

| Área | Fonte existente reutilizada | Contrato Phase 06 |
|---|---|---|
| Empresas autorizadas | `AuthorizationService.project_application_access` | `GET /api/v1/identity/me` |
| Detalhe da empresa | `CompanyModel`, após revalidação de `company.read` | `GET /api/v1/operations/companies/{company_id}` |
| Lista de documentos | Recebimento, evidência, lote, item e transformação do intake | `GET .../{company_id}/documents` |
| Detalhe documental | Mesma projeção + validation issues seguras | `GET .../{company_id}/documents/{document_id}` |
| Agregado | Contagens de recebimentos, transformações completas e exceções | `GET .../{company_id}/documents/summary` |

Nenhum contrato aceita `tenant_id`, permissões ou empresas declaradas pelo
frontend. `company_id` é seletor e sempre é revalidado no servidor.

## Empresas

A tela Empresas parte exclusivamente da lista autorizada retornada por
`/identity/me`. A busca local opera somente sobre essa projeção, nunca sobre o
cadastro completo do tenant. O detalhe revalida CompanyAccess e `company.read`
e apresenta nome empresarial, nome fantasia, identificador fiscal, status,
timezone e moeda. A escrita de empresa é `DEFERRED`: o domínio não possui um
workflow de cadastro/edição maduro no escopo desta fase.

Selecionar uma empresa atualiza o contexto já criado nas Phases 04/05. A troca
incrementa a identidade da requisição, descarta o modelo operacional e ignora
respostas atrasadas. “Todas as empresas autorizadas” permanece útil no
dashboard; a Central pede uma empresa específica para preservar paginação.

## Caixa de entrada e documentos

Caixa de entrada é uma visão curta de recebimentos recentes em processamento,
duplicados, falhos ou em quarentena. Central de Documentos é o arquivo paginado.
Não substituem a Fila Inteligente, que continua sendo a fila transversal.

A lista expõe apenas: ID opaco do recebimento, empresa, lote, nome exibível,
media type, tamanho, origem, canal, resultado, estado de transformação, código
de erro seguro e instante. Não expõe bytes, XML/OFX, hash, `artifact_id`, storage
key, stack trace ou auditoria bruta.

Filtros reais: nome do arquivo, status, origem e intervalo de recebimento. A
paginação é server-side com `offset` e `limit` (1–100). O detalhe apresenta os
mesmos metadados e validation issues minimizadas. Status: `ACCEPTED`/`RECEIVED`
→ Recebido; `STARTED` → Processando; `COMPLETED` → Processado; `FAILED` →
Exceção; `QUARANTINED` → Em quarentena; `DUPLICATE` → Duplicado. “Processado”
não significa aprovado nem escriturado.

## Upload, storage, duplicidade e rastreabilidade

`DOCUMENT_UPLOAD = BACKEND_GAP` para entrada documental genérica. Os writes
existentes são imports especializados de NF-e e OFX, com parâmetros e jornadas
próprios; ligá-los como upload genérico inventaria semântica e atravessaria a
Phase 07. A interface declara o adiamento e não simula sucesso operacional.

`DOCUMENT_DOWNLOAD = DEFERRED`. A leitura autorizada de evidência existe no
serviço, mas não há contrato HTTP aprovado. Nenhuma URL pública ou caminho de
storage foi criado. A deduplicação SHA-256 existente continua autoritativa no
servidor; a UI apenas exibe `DUPLICATE`. Quarentena deriva das transformações e
issues existentes.

`DOCUMENT_TRACEABILITY = PARTIAL`: o detalhe mostra exceções contextuais. O
endpoint resumido de auditoria já existe com `audit.read`, mas não há projeção
segura documento→eventos para “Ver histórico”.

## Dashboard e gaps

Em modo API, W001 usa recebimentos, W002 usa transformações `COMPLETED` e W007
conta somente empresas autorizadas com issues documentais não resolvidas. Os
três passaram para fonte `REAL`. Em `DATA_MODE=SYNTHETIC`, continuam explícita
e exclusivamente sintéticos.

- cadastro/edição de empresa: `DEFERRED`;
- upload genérico: `REAL_BACKEND_GAP`;
- download HTTP e histórico por documento: `DEFERRED`;
- malware scanning: `INFRASTRUCTURE_GAP`;
- paginação conjunta “todas as empresas”: `DEFERRED`; a UI exige empresa;
- QA visual em navegador real: gate manual quando indisponível.

## Rastreabilidade da Fase 09

O detalhe documental oferece Linha da Decisão quando há `company.read + audit.read`. A raiz usa o recibo e o artefato para localizar correlações escopadas; conteúdo original, hashes e storage continuam ocultos. Nem todo documento possui etapa contábil.
