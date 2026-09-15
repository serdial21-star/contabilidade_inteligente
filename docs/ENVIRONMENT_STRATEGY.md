# Environment Strategy

## Modelo explícito da Phase 11

| Ambiente de produto | Literal técnico | Política |
|---|---|---|
| LOCAL | `development` | defaults seguros, sem exposição; configuração externa opcional e completa |
| TEST | `test` | fixtures sintéticas, SQLite permitido, serviços determinísticos |
| HOMOLOGATION | `homologation` | isolado e production-like; exige banco, OIDC HTTPS, origem, hosts, HTTPS e rate limit distribuído |
| PRODUCTION | `production` | mesmas exigências fail-closed, HSTS, debug/docs desativados por padrão e gates operacionais |

Esta tabela substitui a correspondência histórica que tratava STAGING apenas como ambiente lógico. `homologation` agora é um perfil validado; nenhum ambiente herda silenciosamente comportamento de produção.

Estratégia conceitual de 14/09/2026. Não provisiona cloud, banco, IdP ou deploy. [Gates oficiais desta baseline](PRODUCT_RELEASE_BASELINE.md) permanecem vigentes. PRODUCTION_REAL_DATA = NOT_AUTHORIZED.

| Aspecto | DEVELOPMENT | STAGING | PRODUCTION |
| --- | --- | --- | --- |
| purpose | Desenvolvimento isolado e testes sintéticos | Homologação próxima de produção | Operação comercial somente após gates |
| database | Banco local/dedicado MySQL compatível; SQLite só no modo test | Banco dedicado compatível com alvo aprovado; nunca banco Production | Banco exclusivo, alvo/serviço aprovados e acesso mínimo |
| data classification | Sintético e fixtures de teste | Sintético; corpus anonimizado/teste somente com autorização documentada | Dados reais somente no escopo formalmente aprovado |
| allowed data | Fixtures e dados gerados; dados de clientes sem autorização proibidos | Agora somente sintético; autorização de corpus não dispensa gates real data aplicáveis | Atualmente nenhum dado real autorizado |
| secrets | Ambiente/configuração local ignorada; exemplos fictícios | Segredos segregados e identidade de serviço própria | Provedor/ambiente aprovado, rotação, acesso mínimo e auditoria |
| deploy method | Instalação local conforme README | Release identificado, CI e janela controlada conforme runbook | Release aprovado, revisão operacional e procedimento de abort/recuperação |
| migration policy | Alembic revisável; testes isolados não são rollback operacional | Ensaio upgrade forward-only após backup | Upgrade forward-only em janela autorizada com verificação |
| backup requirement | Proteger dados locais relevantes antes de ensaios; não versionar dumps | Backup pré-deploy e ensaio de restore; evidências de banco e storage | Backup recente/hash, política aprovada de banco/storage e recuperação demonstrada |
| external integrations | Simuladores/contratos sintéticos isolados | Sandboxes autorizados; Domínio segue bloqueado | Somente provedores homologados e gates aprovados |

## Correspondência com configuração existente

`src/serdial21/bootstrap/settings.py` aceita `development`, `test`, `homologation` e `production`. O termo histórico STAGING corresponde agora a HOMOLOGATION; não existe literal `staging`. Homologação não concede autorização para dados reais.

`DATABASE_URL` usa `mysql+pymysql`; `sqlite+pysqlite` só em `test`. O perfil `production` exige banco, OIDC HTTPS e debug desativado. Variáveis relevantes incluem `SERDIAL21_ENVIRONMENT`, `OIDC_ISSUER`, `OIDC_AUDIENCE`, `OIDC_JWKS_URL`, `OBJECT_STORAGE_PATH` e limites de upload. Valores de segredos, URLs privadas e conteúdo de `.env` não fazem parte desta documentação.

Runtime, Migration Lab e homologação mencionados em runbooks históricos não comprovam que os três ambientes acima já foram provisionados. A revision Runtime atual deve ser consultada apenas em tarefa operacional autorizada; o head fonte não a substitui.

## Migration e recuperação

DATABASE MIGRATION = FORWARD_ONLY.

Migration atual: `20260908_0012` (`20260908_0012_privacy_controls.py`), status PRE_DEPLOY_REQUIRED. Nenhuma migration criada ou executada nesta fase. Antes de deploy futuro, seguir [Deploy Runbook](DEPLOY_RUNBOOK.md) e [checklist do RC](PILOT_RELEASE_CANDIDATE.md): CI, revision Runtime, backup/hash, autorização da janela, revisão de toda a cadeia faltante, upgrade controlado, schema/constraints/índices, revision final, health, smoke e auditoria aplicável.

Downgrade operacional não é estratégia de rollback. Reversão da aplicação depende da compatibilidade com schema vigente; correção de banco é forward fix. Recuperação de dados segue [Backup/Restore Runbook](BACKUP_RESTORE_RUNBOOK.md), com destino e corte controlados. Ensaios históricos de downgrade em Lab não autorizam downgrade Runtime.

## Condições de operação

STAGING/PRODUCTION externos exigem os sete gates de external exposure; uso real exige os seis gates real data da baseline. Agendamento de backup, cópias de object storage, fornecedores/localização, retenção e revogação IdP precisam de evidência operacional. Nenhum deles recebe PASS por existir este plano. DEVELOPMENT não é exceção à autorização de corpus nem ao isolamento tenant/company.
