# Segurança da decisão contábil

## Fronteira de confiança

O bearer OIDC identifica o usuário vinculado localmente. O `tenant_id` vem da identidade validada; `company_id`, journey, regra e conta são apenas seletores opacos. Cada consulta/comando revalida Membership, CompanyAccess e permissão. Recurso fora do tenant/empresa não é revelado: empresa negada retorna erro uniforme, e ID ausente dentro do escopo retorna recurso indisponível. A data efetiva do catálogo é obrigatória na consulta, nunca inferida do timezone do servidor.

As projeções minimizam dados: não retornam XML/OFX bruto, storage key, artifact hash, payload de auditoria ou modelos ORM. Fonte aberta pela proposta volta a passar pelas rotas company-scoped do documento fiscal/receipt.

## Guardas da decisão

Aprovação e rejeição entram no caso de uso já existente. Antes do efeito ele exige:

1. origem `HUMAN`, `journal.approve`, papel aprovador e CompanyAccess vigentes;
2. segregação entre proponente e decisor;
3. estado `PENDING_APPROVAL`, versão otimista e revisão/hash exatos;
4. revisão válida, contas publicadas/postáveis e débitos iguais a créditos em `Decimal`;
5. `AccountLock` aplicável ao módulo, competência, período ou conta;
6. chave idempotente vinculada ao ator, decisão e payload.

Mesma chave/payload devolve o resultado anterior; conteúdo divergente ou decisão concorrente gera conflito. Apenas uma transição terminal vence. Uma revisão posterior invalida a aprovação anterior conforme o domínio. Estado externo não é acionado: aprovação é interna e não posta/exporta.

## Auditoria e atomicidade

Decisão e AuditEvent mínimo são persistidos na mesma transação. A auditoria é append-oriented, contém ator, tenant, empresa, ação, entidade, versão, correlação e timestamp, e tem verificação de integridade. Falha antes do commit reverte ambos. O histórico contextual exposto exige `audit.read` e não substitui a Linha da Decisão da Fase 09.

## Erros seguros

- `401`: autenticação inválida/expirada.
- `403`: acesso, papel, segregação ou permissão negada.
- `404`: recurso indisponível no escopo autorizado.
- `409`: estado, versão, revisão ou idempotência em conflito.
- `423`: operação bloqueada por `AccountLock`, sem revelar internals.
- `422`: contrato/invariante inválido.

O frontend nunca é camada de autorização. Botões ocultos, confirmação obrigatória e mensagens de bloqueio são somente UX; todas as guardas são repetidas no backend.

## Lacunas preservadas

Não existe edição segura de proposta nem persistência de motivo de rejeição. Não há release de lock na UI, proposta oriunda de financeiro, posting externo ou regra editável. Migration 0012 não foi executada; dados reais e exposição externa permanecem `NO_GO`.
