# API operacional MVP

Esta é a borda HTTP mínima para o escritório piloto importar documentos,
acompanhar o processamento, revisar propostas e registrar decisão humana. Ela
não efetiva escrituração oficial nem exporta para o sistema contábil externo.

Base: `/api/v1/operations/companies/{company_id}`.

## Autenticação e autorização

Todas as rotas exigem `Authorization: Bearer <OIDC access token>`. O token é
validado como JWT RS256 contra issuer, audience e JWKS configurados. A
identidade vinculada localmente determina tenant e membership; `company_id` é
somente um seletor e sempre é revalidado contra `CompanyAccess`, papel e a
permissão atômica no instante da operação.

| Operação | Método e rota | Permissão |
|---|---|---|
| Importar NF-e | `POST /imports/nfe` | `journal.propose` |
| Importar OFX | `POST /imports/ofx` | `journal.propose` |
| Consultar processamento | `GET /processing/{resource_id}` | `company.read` |
| Listar/consultar revisões | `GET /reviews`, `GET /reviews/{journey_id}` | `journal.read` |
| Aprovar/rejeitar revisão | `POST /reviews/{journey_id}/approve`, `POST /reviews/{journey_id}/reject` | `journal.approve` e papel aprovador do workflow |
| Consultar exceções | `GET /exceptions` | `company.read` |
| Consultar auditoria | `GET /audit-events` | `audit.read` |

O acesso a empresa inexistente, de outro tenant ou sem acesso retorna o mesmo
`403 {"detail":"access denied"}`. Recurso ausente dentro do escopo retorna
`404 {"detail":"resource unavailable"}`. Nenhuma resposta revela a
existência de dados de outro tenant.

## Importação

As importações recebem bytes puros no corpo, não multipart. São obrigatórios:

- `Content-Type`: `application/xml` ou `text/xml` para NF-e; `application/x-ofx`,
  `application/ofx` ou `text/plain` para OFX.
- `X-Filename`: nome simples com extensão `.xml` ou `.ofx`; caminhos são recusados.
- `Idempotency-Key`: 1 a 128 caracteres.

NF-e também exige os parâmetros `accounting_date`, `period_start`, `period_end`
e `approval_expires_at` (timestamp com timezone). O limite de NF-e é
`NFE_MAX_XML_BYTES` (padrão 5 MiB); OFX usa `DOCUMENT_MAX_UPLOAD_BYTES` (padrão
10 MiB). O corpo é lido em streaming e interrompido ao exceder o limite.

Resposta `202` contém `resource_id`, `resource_kind` (`JOURNEY` ou `BATCH`),
status e indicadores mínimos de duplicidade. A mesma chave com o mesmo
conteúdo devolve o recurso anterior; com conteúdo diferente retorna `409`.

## Revisão e decisão

`GET /reviews` aceita `limit` entre 1 e 100. A revisão detalhada retorna a
versão, hash e linhas que devem ser apresentados de volta na decisão:

```json
{
  "expected_version": 8,
  "revision_id": "UUID",
  "revision_hash": "sha256 hexadecimal de 64 caracteres"
}
```

`approve` e `reject` também exigem `Idempotency-Key`. A chave é vinculada ao
ator, jornada, versão, revisão, hash e decisão no checkpoint imutável. Repetir
exatamente a mesma decisão retorna a decisão já registrada; reutilizar a chave
com outro conteúdo, ou tentar nova decisão após a conclusão, retorna `409`.
A segregação entre proponente e aprovador, a validade da revisão, bloqueios e o
papel aprovado pelo workflow são aplicados pelo caso de uso de domínio.

## Erros, rastreabilidade e privacidade

Erros de borda usam somente mensagens estáveis:

| Status | Significado |
|---|---|
| 401 | token ausente, inválido ou expirado |
| 403 | acesso, papel ou permissão negados |
| 404 | recurso indisponível no escopo autorizado |
| 409 | conflito de versão, estado ou idempotência |
| 413 | payload acima do limite |
| 415 | tipo de mídia não suportado |
| 422 | contrato, arquivo ou comando inválido |
| 503 | identidade não configurada/disponível |

Cada resposta retorna `X-Correlation-ID`. O cliente pode enviar um UUID nesse
cabeçalho; caso contrário a API gera um. O valor é propagado para a auditoria.
Logs técnicos registram método, caminho, status e duração, sem corpo, query,
cabeçalhos de autenticação, XML, OFX ou stack trace para o cliente. A consulta
de auditoria é deliberadamente resumida e não expõe estados antes/depois,
motivos ou conteúdo de documentos.
