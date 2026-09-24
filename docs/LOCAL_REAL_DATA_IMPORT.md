# Roteiro: import de dados reais do Sistema A em banco local

Base de decisão: [ADR 0013](adr/0013-importacao-manual-dados-sistema-a.md).
Dados reais de clientes ficam **somente** na máquina do operador: nunca no
`_hom` (auditoria imutável), nunca no `_mig` (descartável), nunca no git
(`local_data/` está no `.gitignore`).

## 1. Exportar do Sistema A (phpMyAdmin) — sem a coluna `senha`

Execute cada consulta abaixo, use **Exportar → CSV** sobre o resultado e salve
em `local_data/clientes.csv` e `local_data/funcionarios.csv`:

```sql
SELECT id, nome_cliente, nome_fantasia, cnpj_cpf, cnpj, status, responsavel FROM clientes;
SELECT id, nome_funcionario, email, cargo, status FROM funcionarios;
```

Selecionar só essas colunas garante que nenhuma senha, telefone, endereço ou
contrato saia do Sistema A.

## 2. Banco de destino

**Sem Docker:** use um banco exclusivo do Sistema B e de desenvolvimento —
`u621451815_serdial21_dev` (usuário `u621451815_serdial21_app`) — depois de
conferir o estado dele com as consultas somente-leitura abaixo, no phpMyAdmin
do `_dev`. **Nunca** aponte para `u621451815_serdial21` (Sistema A em
produção), `_hml` (Sistema A, homologação antiga), `_hom` ou `_mig`.

```sql
SHOW TABLES;
SELECT version_num FROM alembic_version;
SELECT COUNT(*) FROM audit_events;   -- se a tabela existir
SELECT COUNT(*) FROM companies;      -- se a tabela existir
```

Eventos de auditoria já gravados no banco não podem ser apagados; se o `_dev`
tiver lixo de testes antigos que você não quer misturar com dados reais,
crie outro banco novo em vez de limpar este.

Estado conferido em 2026-09-23: `_dev` está em `20260904_0005`, com
`audit_events = 0` e `companies = 0` (limpo, só precisa de `alembic upgrade head`).

**Opção mais simples:** crie o arquivo `.env` na raiz do projeto (o git o
ignora; nunca o abra em conversa) com duas linhas — se a senha tiver caracteres
especiais (`@ : / # % ?`), codifique-os (ex.: `@` vira `%40`):

```
SERDIAL21_ENVIRONMENT=development
DATABASE_URL=mysql+pymysql://u621451815_serdial21_app:SUA_SENHA@srv1183.hstgr.io:3306/u621451815_serdial21_dev
```

Alternativa, definindo a URL só na sessão do terminal, sem digitar a senha em
histórico ou chat (PowerShell):

```powershell
$s = Read-Host "Senha do banco _dev" -AsSecureString
$p = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($s))
$env:DATABASE_URL = "mysql+pymysql://u621451815_serdial21_app:$([uri]::EscapeDataString($p))@srv1183.hstgr.io:3306/u621451815_serdial21_dev"
```

Se a conexão falhar, o IP do seu computador provavelmente não está liberado em
hPanel → Bancos de dados → MySQL remoto.

**Com Docker (opcional)** — MariaDB local descartável, Docker Desktop aberto:

```powershell
docker run --name serdial21-local-db -e MARIADB_ROOT_PASSWORD=ESCOLHA_UMA_SENHA `
  -e MARIADB_DATABASE=serdial21_local -p 127.0.0.1:3307:3306 `
  -v serdial21_local_data:/var/lib/mysql -d mariadb:11.8
```

A senha é sua e não deve ser colada em conversa, arquivo versionado ou log.
O banco escuta só em `127.0.0.1`.

## 3. Rodar (mesmo terminal PowerShell, na raiz do projeto)

```powershell
$env:DATABASE_URL = "mysql+pymysql://root:ESCOLHA_UMA_SENHA@127.0.0.1:3307/serdial21_local"
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe scripts\bootstrap_tenant.py --name "Serdial21"
# copie o tenant_id impresso:
$T = "COLE_O_TENANT_ID"
.\.venv\Scripts\python.exe scripts\import_sistema_a_companies.py --input local_data\clientes.csv --tenant-id $T --dry-run
.\.venv\Scripts\python.exe scripts\import_sistema_a_companies.py --input local_data\clientes.csv --tenant-id $T
.\.venv\Scripts\python.exe scripts\import_sistema_a_team.py --funcionarios local_data\funcionarios.csv --clientes local_data\clientes.csv --tenant-id $T --dry-run
.\.venv\Scripts\python.exe scripts\import_sistema_a_team.py --funcionarios local_data\funcionarios.csv --clientes local_data\clientes.csv --tenant-id $T
```

Sempre rode `--dry-run` antes: ele executa tudo, mostra o relatório e desfaz.
Ordem obrigatória: empresas primeiro, equipe depois.

## 4. Como ler o relatório

- `skipped` — `status_nao_mapeado:Lead` (não é cliente ainda) ou
  `sem_identificador_fiscal` (sem CNPJ/CPF): nada foi inventado.
- `conflicts` — `conteudo_divergente` ou `identificador_fiscal_em_uso`/
  `email_em_uso`: o registro já existe diferente; nada foi sobrescrito.
- `assignments` — `ambiguous` (homônimos), `unmatched` (nome não bate
  exatamente), `inactive_member`, `company_missing`: **não foram vinculados**;
  resolva o cadastro na origem ou vincule manualmente depois.

## 5. Descartar

```powershell
docker rm -f serdial21-local-db; docker volume rm serdial21_local_data
```
