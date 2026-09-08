# Pilot readiness — primeiro escritório

Avaliação técnica atualizada em 08/09/2026, limitada ao código, documentação e testes do
workspace. **O projeto não está pronto para receber um escritório piloto.**
Há bloqueios críticos de operação, recuperação, identidade e homologação da
integração externa.

| Item | Status | Evidência atual | Condição para avanço / ação necessária |
| --- | --- | --- | --- |
| Segurança | PARTIAL | Limites de upload/XML, headers, isolamento de storage e revisão de segurança estão em `SECURITY_REVIEW_EXECUTION_22.md`. | Fechar rate limiting distribuído, TLS/HSTS, allowlist de hosts, limite de corpo na borda e scanner de CVEs no CI. |
| Tenant | READY_FOR_PILOT | Filtros tenant/company e FKs compostas foram comprovados no MariaDB; a borda OIDC agora deriva o tenant do token e revalida membership e CompanyAccess internamente. | Provisionar o IdP real, configurar o claim `tenant_id` e executar UAT antes de uso externo. |
| Backup | READY_FOR_PILOT | Backup lógico transacional do Runtime MariaDB foi criado, validado por tamanho/hash e protegido fora do Git; RPO técnico alvo de 24 horas documentado. | Automatizar agenda, criptografia externa aprovada e monitoração antes de ampliar o piloto. O backup de object storage continua como gate separado. |
| Restore | READY_FOR_PILOT | Restore real no Lab separado foi concluído e validado por HEAD, schema, constraints, contagens, AuditEvent, AccountLock e leitura ORM. RTO técnico alvo de 4 horas documentado. | Repetir periodicamente o ensaio e incorporar transferência/cutover ao runbook operacional antes de produção ampliada. |
| Banco | READY_FOR_PILOT | MariaDB 11.8.8 homologado via `mysql+pymysql`; Runtime separado, em revision 0009, UTC e `utf8mb4`. | Ensaiar e aplicar a nova revision 0010 pelo processo forward-only antes do deploy da identidade. |
| Migrations | PARTIAL | Migrations 0001–0009 foram comprovadas no MariaDB; as novas 0010/0011 passaram `base -> head -> base` local e Alembic `check`, mas ainda não foram aplicadas no Lab/Runtime. | Ensaiar 0010/0011 no Migration Lab após backup e então executar somente upgrade no Runtime. Nunca fazer downgrade no Runtime. |
| Usuários | PARTIAL | Access token OIDC RS256, vínculo `(issuer, subject)`, onboarding, offboarding, revogação e AuditEvent passaram em testes automatizados. | Provisionar/homologar o IdP, executar bootstrap controlado do primeiro administrador e UAT do escritório. |
| Permissões | PARTIAL | A identidade autenticada foi integrada ao serviço central; tenant, membership, CompanyAccess, RoleBinding e permissão são revalidados, com testes negativos uniformes. | Conceder `identity.manage` sob revisão e testar as alçadas reais do escritório no IdP/Runtime. |
| NF-e | PARTIAL | Parser seguro de NF-e 55, quarentena, deduplicação, evidência e testes determinísticos. | Validar com corpus autorizado do piloto, XSD/XMLDSIG conforme escopo aprovado e MySQL real; CT-e/NFS-e continuam fora do escopo. |
| OFX | PARTIAL | Parser OFX, preservação de sinal e deduplicação por FITID possuem regressão. | Validar layouts/bancos reais autorizados, dados de borda e persistência MySQL antes de ingestão do piloto. |
| Regras | PARTIAL | Catálogo persistente versiona plano, regras, releases, mappings e workflow; o E2E prova DRAFT, REVIEW, publicação, nova versão e uso por documento sem catálogo sintético. | Cadastrar e publicar conteúdo revisado do escritório, executar UAT e aplicar a migration 0011 no MariaDB. |
| Proposta | PARTIAL | A jornada usa automaticamente o catálogo PUBLISHED persistente e preserva seu snapshot no checkpoint; proposta e pré-lançamento permanecem determinísticos. | Homologar o conteúdo real e o canal humano completo antes de receber documentos do piloto. |
| Aprovação | PARTIAL | O workflow publicado fornece papel responsável/aprovador; hash, revisão, segregação e permissão são revalidados, inclusive negação de autopublicação do catálogo. | Homologar alçadas reais e disponibilizar o canal operacional de decisão contábil antes de uso humano. |
| Domínio | BLOCKED | O conector permanece em `BLOCKED_FOR_HOMOLOGATION`; não há serialização/entrega real. | Obter versão/layout oficial, golden files, homologação e confirmação humana do destino; manter bloqueado até então. |
| Conciliação | PARTIAL | Regras de diferença, exceção, match e aprovação existem no domínio. | Criar caso de uso/persistência e validação operacional com extratos reais autorizados. |
| Bloqueios | READY_FOR_PILOT | AccountLock persistido, guard, isolamento tenant/company, autorização, auditoria, rollback e unicidade concorrente foram comprovados. | `WORKFLOW_AFTER_UNLOCK` não pertence ao escopo do piloto e não pode ser prometido por API/borda futura. |
| Auditoria | PARTIAL | AuditEvent append-oriented, atomicidade, restore de 100 eventos e leitura JSON foram comprovados no MariaDB; a consulta operacional exige `audit.read` e não expõe estados completos. | Aprovar retenção definitiva, implementar legal hold/arquivamento e backup de evidências, e monitorar adulteração. |
| Observabilidade | PARTIAL | Logs JSON sanitizados, correlação, eventos técnicos e métricas locais foram implementados. | Integrar coletor central, alertas, retenção, dashboards e métricas distribuídas; registry local não atende múltiplas réplicas. |
| Testes | PARTIAL | Foram aprovados 255 testes, incluindo identidade, catálogo persistente, isolamento e migrations locais, com 16 testes MariaDB opt-in ignorados; o restore permanece documentado separadamente. | Executar no CI; ensaiar as revisions 0010/0011 no Lab e adicionar carga, DAST, UAT contábil e corpus autorizado. |
| Documentação | PARTIAL | ADRs, E2E, segurança, regressão, observabilidade, backup/restore, identidade, catálogo e processo inicial de incidente/privacidade estão documentados. | Criar runbooks de deploy, rotação de segredos e rollback operacional completo; exercitar incidente de privacidade. |
| Privacidade | BLOCKED_PENDING_LEGAL_APPROVAL | Para piloto sintético, política/decisão de retenção, dry-run, legal hold, DSR sem entrega, isolamento e auditoria estão implementados; destruição está desabilitada. Para dados reais, não há prazo/base legal aprovada, busca/export DSR, backup de object storage ou eliminação autorizada. | Aprovar finalidade, bases legais, prazos, papéis, legal hold, DSR, fornecedores e backups; implementar busca/export DSR e controles de cópias antes de dados reais. |
| Rollback | BLOCKED | A UoW faz rollback transacional em falha; não existe rollback operacional de release/migration/dados. | Definir estratégia de deploy reversível, backup pré-migration, critérios de abortar piloto e ensaio de recuperação. |

## Execucao 36 - final pilot gate

O release candidate consolidado passou a regressao local que o CI executara:
260 PASS, 0 FAIL, 0 ERROR, 0 SKIPPED e 2 warnings de deprecacao. O grafo
Alembic possui um unico head em `20260908_0012`.

O piloto interno sintetico e `GO`: a fixture sintetica de redacao passou a
construir seu valor em runtime, sem allowlist, e o scanner fail-closed detectou
o canario temporario e aprovou o conjunto completo do release candidate. O
`pip-audit` local encontrou advisories somente em `pip` do virtualenv de tooling;
isso e hardening nao bloqueante. Dados reais e exposicao externa continuam
bloqueados por seus gates proprios. A decisao detalhada esta em
`PILOT_GO_NO_GO.md`.

## Execucao 35 - operational readiness

Os procedimentos de deploy/abort, rollback forward-only, backup/restore,
incidente, lifecycle, rotacao de segredos e AccountLock foram consolidados e
simulados por tabletop ou evidencia automatizada em `OPERATIONAL_RUNBOOK.md` e
`INCIDENT_DRILL_REPORT.md`.

| Escopo | Estado | Condicao |
| --- | --- | --- |
| Piloto interno sintetico | READY | Usar o checklist operacional e os runbooks, sem dados reais. |
| Dados reais | BLOCKED_PENDING_REQUIRED_HUMAN_GATES | Corpus autorizado, accountant signoff, legal approval e migration 0012 pre-deploy. |
| Exposicao externa | BLOCKED_PENDING_INFRASTRUCTURE | CORS allowlist, HSTS/proxy, rate limit distribuido, metricas centrais, alertas e validacao IdP. |

## Bloqueios que impedem o piloto

1. Backup e restore do object storage; banco MariaDB já comprovado.
2. Provisionamento do IdP real, bootstrap controlado do primeiro administrador e UAT das alçadas; a implementação OIDC e o contexto tenant já possuem prova automatizada.
3. Governança de privacidade e retenção aprovada e seus controles executáveis (legal hold, DSR, retenção e backup de evidências) implementados.
4. Runbook de rollback e operação de incidente.

O bloqueio do Domínio não impede, por si só, um piloto estritamente interno e
sem exportação oficial, mas impede qualquer promessa de entrega/escrituração no
sistema externo. O status deve ser reavaliado depois que todos os bloqueios
acima tiverem evidência verificável.
