# ADR 0013 — Importação manual de empresas e equipe interna a partir do Sistema A

## Status

Aceita por decisão explícita do usuário em 2026-09-23. Amplia o limite fixado
pelo [ADR 0012](0012-referencia-externa-company.md), que era só estrutura
aditiva sem correlação real. Import de `companies` (item 1 da Decisão)
implementado em 2026-09-23: `src/serdial21/modules/access_control/application/
services/company_import.py`, repositório em `adapters/outbound/persistence/
repositories.py` (`SqlAlchemyCompanyImportRepository`), script operador em
`scripts/import_sistema_a_companies.py`, testes em `tests/integration/
test_company_import.py`. Item 2 (equipe interna) implementado em 2026-09-23
(seção abaixo), migration `20260923_0016`.

## Contexto

O usuário pediu dados reais para testes mais realistas do Sistema B: (1)
popular `companies` com empresas/clientes reais do Sistema A, usando a tripla
`external_system + external_type + external_id` já preparada pelo ADR 0012, e
(2) criar o conceito de "equipe interna do escritório" — quem no Serdial21 é
responsável por cada empresa/cliente — a partir dos dados reais de
funcionários do Sistema A.

O gate de integração (`docs/integration/SYSTEM_A_INTEGRATION_READINESS_GATE.md`)
mantém veredito `NO_GO` para o Connect Hub. Esse gate trata exclusivamente de
tráfego automático/ao vivo entre sistemas (webhook, M2M, sincronização
contínua). Ele não autoriza nem proíbe um import manual e pontual, executado
por um operador autorizado, para preencher dados de teste. Este ADR preenche
essa lacuna explicitamente, para não avançar por omissão.

## Decisão

1. É aceito um script de import **manual, offline, idempotente**, executado
   sob demanda por um operador autorizado, que lê um extrato dos dados reais
   do Sistema A (export ou consulta direta ao banco do Sistema A feita pelo
   operador) e grava em `companies` do Sistema B: `legal_name`, `trade_name`,
   `tax_identifier`, e a tripla `external_system='sistema_a'`,
   `external_type` (a definir conforme o tipo de registro), `external_id`
   (chave primária do registro no Sistema A).
2. É criado um novo conceito de "equipe interna do escritório": um
   funcionário/colaborador do Serdial21 responsável por uma ou mais empresas
   clientes. A fonte de dados também é um import manual e pontual do cadastro
   real de funcionários do Sistema A (não uma sincronização contínua).
3. Nenhuma das duas importações cria endpoint público, credencial M2M,
   webhook, conector automático ou qualquer caminho de sincronização
   contínua. O Connect Hub permanece `NO_GO` e não é alterado por este ADR.
4. O script de import roda fora da transação de negócio da API, é
   revisável, e cada execução gera evidência de auditoria (quem rodou, quando,
   quantos registros, hash do lote) — não escreve em `companies` por fora do
   caminho de persistência já existente do domínio `access_control`.
5. Dados sensíveis de clientes reais (CNPJ, nomes, e-mails) usados no import
   não são logados em texto livre; apenas contagens e identificadores opacos
   aparecem em logs/auditoria, conforme a seção 6.9 do AGENTS.md.
6. Fica fora de escopo deste ADR: login real (OIDC) do frontend contra a API.
   Esse ponto exige a escolha de um provedor de identidade real — decisão
   material própria, ainda em aberto, tratada separadamente.

## Mapeamento confirmado (item 1 — `clientes` → `companies`)

Estrutura real de `clientes` obtida via `SHOW COLUMNS` em 2026-09-23. Mapeamento:

| Campo em `companies` | Origem em `clientes` | Observação |
| --- | --- | --- |
| `legal_name` | `nome_cliente` | obrigatório |
| `trade_name` | `nome_fantasia` | opcional |
| `tax_identifier` | `cnpj`, com fallback para `cnpj_cpf` | guardado em forma canônica: **só dígitos, como texto** (zeros à esquerda preservados), pois o Sistema B já compara documentos fiscais só pelos dígitos e assim o mesmo documento com pontuações diferentes é detectado como duplicado. Linha sem nenhum dos dois é **pulada**; tamanho diferente de 11 (CPF) ou 14 (CNPJ) também é **pulado** (`identificador_fiscal_invalido`); dígito verificador não é validado (não inventar regra) |
| `status` | `status` ('Ativo'→'active', 'Inativo'→'inactive') | `'Lead'` é **pulado**: ainda não é cliente real, não deve virar `Company` |
| `external_system` | constante `'sistema_a'` | |
| `external_type` | constante `'cliente'` | |
| `external_id` | `id` (convertido para string) | chave de idempotência |
| `timezone` | constante `'America/Sao_Paulo'` | Sistema A não guarda por cliente |
| `currency_code` | constante `'BRL'` | idem |
| `valid_from` | horário do import | não é a data de início de contrato |

Campos de `clientes` explicitamente **não importados**: `senha` (nunca, sob
nenhuma hipótese), `id_pasta_inbox`/`id_pasta_raiz` (Google Drive, fora de
escopo), `whatsapp`, `valor_contrato`, `vencimento_contrato`,
`inicio_prestacao_servicos`, `aceita_notificacao_*`, `codigo_sistema` — nenhum
desses tem um lugar correspondente no modelo `Company` hoje; importar exigiria
inventar estrutura, o que a seção 6.2 do AGENTS.md proíbe.

O campo `responsavel` (texto livre com o nome de quem atende o cliente) é a
ponte natural para o item 2 (equipe interna), mas **não foi usado ainda**: é
texto livre, sem chave para `funcionarios`, e uma tentativa automática de
casamento por nome arriscaria vincular o cliente errado à pessoa errada. Fica
para quando o item 2 for desenhado.

Re-execução do script é idempotente: linha já importada com conteúdo idêntico
não gera nova escrita; conteúdo diferente ou colisão de `tax_identifier` gera
conflito reportado, nunca sobrescrita silenciosa.

## Equipe interna (item 2)

Migration `20260923_0016` cria duas tabelas, ambas com `tenant_id` e FKs
compostas que impedem referência cross-tenant:

- `office_team_members`: `display_name`, `email` (único por tenant),
  `job_title`, `status`, tripla externa (única por tenant), `valid_from`.
  **Não** tem vínculo com `users`/`tenant_memberships`: a pessoa existe como
  cadastro descritivo; ligar a um login real depende da decisão de identidade
  (OIDC), ainda em aberto.
- `company_team_assignments`: empresa ↔ membro com `role_label` (hoje só
  `'responsavel'`), `status`, `valid_from/valid_until`; única por
  (tenant, empresa, membro, papel).

Mapeamento `funcionarios` → `office_team_members`: `nome_funcionario` →
`display_name`, `email` → `email` (minúsculo), `cargo` → `job_title`, `status`
('Ativo'→'active', 'Inativo'→'inactive'), `id` → `external_id` com
`external_type='funcionario'`. **Nunca lidos:** `senha`, `endereco`,
`telefone`, `contato_emergencia`, `observacao`, `matricula`, datas de
admissão/demissão, `ultimo_acesso` (minimização, seção 6.9). A trilha de
auditoria dos dois cadastros não grava nome nem e-mail.

Vínculo empresa → responsável (a partir de `clientes.responsavel`, texto
livre): somente correspondência **exata** do nome normalizado (sem acento,
caixa e espaços). Sem correspondência, homônimos (ambíguo), membro inativo,
empresa não importada ou responsável vazio são **reportados e não vinculados**
— nunca aproximados. Vínculo e criação são idempotentes e auditados
(`origin=IMPORT`). Script: `scripts/import_sistema_a_team.py`; testes:
`tests/integration/test_team_import.py` e `tests/mariadb/test_migration_0016.py`.

Definição de qual `tenant_id` recebe os dados continua a critério do operador
(`--tenant-id`), não fixado neste ADR.
