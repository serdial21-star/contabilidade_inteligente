# Security gate — Execução 33

## VERIFIED

OIDC RS256 deriva principal e tenant; `AuthorizationService` revalida usuário,
membership, CompanyAccess e permissão. A API operacional valida tipo, arquivo,
tamanho e correlação, e retorna erros uniformes. Headers de resposta incluem
CSP, no-store, nosniff, frame deny e referrer policy. Logs e AuditEvent são
sanitizados; SubjectLocator não é persistido/auditado. Retenção destrutiva é
negada e privacy usa dry-run/Legal Hold.

O CI GitHub Actions executa pytest local, `pip-audit`, gate de padrão de segredo
e validação de head único Alembic sem tocar no Runtime.

## RELEASE VERIFICATION - EXECUTION 36

O secret scanner executa `scripts/verify_release_secrets.py`. Ele varre
`git ls-files --cached --others --exclude-standard`, inclui arquivos novos nao
ignorados, cria/remove canario temporario e falha fechada se o canario nao for
detectado ou o release tiver finding. A fixture de redacao constroi o valor
sintetico em runtime, sem allowlist ou reducao de cobertura.

O `pip-audit` local encontrou sete advisories somente no `pip` 25.2 do
virtualenv de desenvolvimento; `pip` nao e dependencia runtime do projeto.
Atualizar o tooling para 25.3/26.x e hardening nao bloqueante.

### Refinamento da varredura — T-0002 (01/10/2026)

O padrão de atribuição de senha passou a ignorar somente o valor Python `None`
inteiro e referências inteiras de shell ou PowerShell, com ou sem aspas. A
varredura continua cobrindo todos os arquivos candidatos e não possui
allowlist. Achados informam rótulo, caminho e linha sem expor o valor.

Limites conhecidos e aceitos nesta tarefa: substituição de comando pode conter
um literal sem que o scanner o diferencie do comando autorizado; um literal
iniciado por cifrão e seguido de letras é indistinguível de uma variável shell;
e credenciais inseridas em URLs nunca foram cobertas por este padrão. A
cobertura de URLs permanece registrada no item 14 do quadro de tarefas.

## INFRASTRUCTURE_PENDING

CORS permanece fail-closed sem frontend/origem configurada. HSTS/host allowlist
são responsabilidade do reverse proxy HTTPS. Rate limiting distribuído, coletor
central, alertas e métricas distribuídas dependem de infraestrutura. Migration
0012 MariaDB permanece `PRE_DEPLOY_GATE`.
