# Checkpoint de sessão — 29/09/2026

## Objetivo deste registro

Ponto de retomada operacional após a publicação da validação fiscal e o
primeiro onboarding real de empresa no piloto. Este arquivo não contém nome,
e-mail, CPF/CNPJ, token, credencial ou conteúdo do CSV.

## Estado confirmado ao encerrar

- Repositório remoto em `main`, commit `1c17d8a` (`feat: validate CPF and
  alphanumeric CNPJ`).
- `api` e `web` reconstruídos seletivamente no VPS a partir desse commit.
- API e Web confirmados `running/healthy`, zero reinícios.
- `https://contabilidade.serdial21.com/app/` respondeu `200`.
- `https://contabilidade.serdial21.com/api/v1/health/ready` respondeu `200`.
- Redis e n8n não foram recriados nem alterados nesta entrega.
- Nenhuma migration foi necessária: `companies.tax_identifier` já comporta o
  formato canônico alfanumérico.
- CPF passou a exigir 11 dígitos e dígitos verificadores válidos.
- CNPJ numérico e alfanumérico passou a exigir 14 posições, últimas duas
  numéricas e dígitos verificadores oficiais válidos.
- Documento é persistido sem máscara e em maiúsculas; máscara existe apenas
  na apresentação.
- E-mail continua sendo identidade de acesso; CPF/CNPJ continua sendo
  identidade fiscal única por tenant. Um e-mail não substitui o documento.

## Importação de empresa

- O lote inicial de cinco registros foi confirmado pelo operador como
  integralmente sintético e não foi importado.
- O CSV sintético foi retirado da fila ativa e preservado no VPS como
  `/opt/serdial21-b/local_data/clientes.test-only-20260929.csv`, modo `0600`.
- Um novo CSV mínimo, contendo somente um cliente real autorizado, foi
  exportado do Sistema A com cabeçalho e uma linha de dados.
- Arquivo ativo no VPS: `/opt/serdial21-b/local_data/clientes.csv`.
- Controle confirmado: modo `0640`, proprietário
  `root:serdial21-secrets`, duas linhas, 173 bytes.
- SHA-256 observado:
  `675fba6ac7283223fb950d53206ca7e358fa132cca97e2bdd63eaba15aa060b3`.
- Dry-run: `total_rows=1`, `created=1`, `unchanged=0`, sem conflitos e sem
  registros pulados; rollback confirmado pelo modo de execução.
- Após autorização explícita, o import real repetiu o mesmo resultado com
  `dry_run=false` e criou uma empresa auditada no tenant piloto.

## Identidade e CompanyAccess

- Tenant piloto: `5463ce7c-31b5-471d-97aa-89f043292ebb`.
- Identidade externa reutilizada: `funcionario:3`.
- Usuário interno reutilizado: `b4321acd-2c48-4471-bc4b-b0eb8ff5d477`.
- Membership reutilizada: `325c863a-6772-4abb-b983-d9362b090daa`.
- Papel reutilizado: `940b8076-1c71-473c-8621-dd3b47bb47b0`.
- Permissões: `company.read`, `journal.read`, `audit.read`.
- Bootstrap idempotente concedeu `CompanyAccess` para uma empresa ativa.
- O operador saiu, entrou novamente pela ponte Sistema A → Sistema B e
  confirmou visualmente que a empresa aparece no seletor. Jornada aprovada.

## Evidência de qualidade

- 240 testes unitários aprovados.
- 199 testes de frontend e integração aprovados.
- 20 testes de arquitetura, segurança e recuperação aprovados.
- Suíte de API chegou a 100% sem falhas na execução isolada.
- `git diff --check` aprovado antes do commit funcional.
- ADR criado: `docs/adr/0017-identificador-fiscal-e-cnpj-alfanumerico.md`.

## Sistema A — estado e pendências

- Cadastro real foi criado no Sistema A com `id=28`; nenhum documento fiscal
  foi reproduzido neste registro.
- A tela `src/pages/admin/AdminClientes.tsx` mantém status visual fixo e a
  função atual `maskCnpjCpf()` remove letras, portanto ainda não suporta CNPJ
  alfanumérico na entrada.
- A listagem mostrou traços nos campos CNPJ/CPF, e-mail e telefone. É preciso
  verificar se o endpoint `/admin/clientes-v2` não projeta esses campos ou se
  a escrita não os preencheu; não inferir a causa.
- A validação autoritativa deve ser adicionada ao workflow n8n de
  `POST /admin/novo-cliente-v2` antes de qualquer criação no Google Drive ou
  escrita no banco. Frontend sozinho não é controle suficiente.
- Antes de alterar o MariaDB do Sistema A, obter `SHOW CREATE TABLE` e índices
  de `clientes` e da tabela de e-mails autorizados.
- Registros sintéticos não devem receber documento fiscal inventado. A solução
  futura deve ser ambiente separado ou classificação explícita `is_test`, não
  sobrecarga silenciosa do status comercial.

## Controles pendentes para a primeira ação da próxima sessão

1. Preservar o CSV sintético fora da fila; decidir retenção/eliminação em vez
   de reativá-lo.
2. Iniciar a correção do Sistema A: obter o JSON do workflow n8n e o
   schema/índices reais, implementar validação server-side e depois ajustar o
   Lovable/frontend.

## Retomada em 30/09/2026

- Backup pós-importação do banco `u621451815_s21_pilot` confirmado pelo
  operador em 30/09/2026 às 09:19.
- Conferência somente leitura confirmou:
  `DATABASE=u621451815_s21_pilot`, `ALEMBIC=20260923_0016`, uma empresa ativa
  e um CompanyAccess ativo para a membership esperada.
- `api`, `redis` e `web` permaneceram `running/healthy`, com zero reinícios.
- `n8n-caddy-1` e `n8n-n8n-1` permaneceram ativos e não foram recriados.
- Após autorização explícita, o CSV real temporário
  `/opt/serdial21-b/local_data/clientes.csv`, cujo hash estava previamente
  conferido, foi removido definitivamente do VPS. O dado permanece no Sistema
  A, no banco piloto e no backup pós-importação.
- O CSV sintético arquivado não foi removido nem reativado.

## Proibições na retomada

- Não reimportar `clientes.test-only-20260929.csv`.
- Não executar o import real novamente antes de um dry-run; embora idempotente,
  toda execução precisa de propósito e evidência.
- Não inventar CPF/CNPJ para massa de teste.
- Não alterar status, schema ou workflow do Sistema A somente pela interface
  sem validação equivalente no backend.
- Não registrar documento, e-mail, nome do cliente ou conteúdo do CSV em log,
  commit ou conversa.
- Não executar `docker compose down`, apagar volumes, reiniciar o VPS ou
  recriar n8n/Redis como parte desta retomada.

## Ordem de leitura amanhã

1. `AGENTS.md`.
2. Este checkpoint.
3. `docs/adr/0017-identificador-fiscal-e-cnpj-alfanumerico.md`.
4. `docs/LOCAL_REAL_DATA_IMPORT.md`.
5. `docs/INTERNAL_VPS_DEPLOYMENT.md`.
6. `scripts/import_sistema_a_companies.py` e
   `scripts/bootstrap_user_access.py`.
