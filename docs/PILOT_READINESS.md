# Pilot readiness — primeiro escritório

Avaliação técnica em 07/09/2026, limitada ao código, documentação e testes do
workspace. **O projeto não está pronto para receber um escritório piloto.**
Há bloqueios críticos de operação, recuperação, identidade e homologação da
integração externa.

| Item | Status | Evidência atual | Condição para avanço / ação necessária |
| --- | --- | --- | --- |
| Segurança | PARTIAL | Limites de upload/XML, headers, isolamento de storage e revisão de segurança estão em `SECURITY_REVIEW_EXECUTION_22.md`. | Fechar rate limiting distribuído, TLS/HSTS, allowlist de hosts, limite de corpo na borda e scanner de CVEs no CI. |
| Tenant | PARTIAL | Filtros tenant/company, FKs compostas e testes negativos existem. | Executar as garantias no MySQL homologado; não há identidade HTTP real que estabeleça o contexto confiável. |
| Backup | BLOCKED | Não existe política, automação, retenção ou evidência de backup do banco e do object storage. | Definir RPO/RTO, destino criptografado, retenção, dono operacional, monitoração e teste de backup para MySQL e evidências. |
| Restore | BLOCKED | Não há runbook nem teste de restauração isolada por tenant. | Executar restore cronometrado em ambiente descartável, provar integridade de auditoria/evidência e ausência de mistura de tenants. |
| Banco | PARTIAL | MySQL/PyMySQL, UTF-8, UTC, pool e timeouts estão configurados. | Formalizar versão MySQL suportada, provisionar ambiente homologado e testar carga, conexão, failover e permissões mínimas. |
| Migrations | PARTIAL | Oito revisions Alembic existem e são testadas em SQLite. | Rodar upgrade em MySQL suportado sobre cópia representativa; documentar rollback compatível e validar constraints/índices reais. |
| Usuários | BLOCKED | Há entidades de usuário, membership e CompanyAccess, mas não há autenticação externa, provisionamento ou fluxo de desativação operacional. | Escolher provedor de identidade, implementar contexto autenticado e processo de onboarding/offboarding do escritório piloto. |
| Permissões | PARTIAL | Serviço central revalida usuário, membership, CompanyAccess, papel e permissão. | Vincular a autenticação real, sem confiar em IDs de rota/corpo; testar alçadas reais do escritório. |
| NF-e | PARTIAL | Parser seguro de NF-e 55, quarentena, deduplicação, evidência e testes determinísticos. | Validar com corpus autorizado do piloto, XSD/XMLDSIG conforme escopo aprovado e MySQL real; CT-e/NFS-e continuam fora do escopo. |
| OFX | PARTIAL | Parser OFX, preservação de sinal e deduplicação por FITID possuem regressão. | Validar layouts/bancos reais autorizados, dados de borda e persistência MySQL antes de ingestão do piloto. |
| Regras | PARTIAL | Motor determinístico e versionamento existem; E2E usa catálogo sintético. | Cadastrar e publicar regras revisadas do escritório, com responsável contábil e dados de teste reais anonimizados. |
| Proposta | PARTIAL | Proposta e pré-lançamento balanceado são exercitados na jornada vertical. | Implementar/provar gestão persistente do catálogo real e fluxo operacional de revisão. |
| Aprovação | PARTIAL | Hash/revisão, segregação e papel Contador são verificados no domínio. | Conectar ator autenticado, alçadas reais e interface/canal de decisão antes de qualquer uso humano. |
| Domínio | BLOCKED | O conector permanece em `BLOCKED_FOR_HOMOLOGATION`; não há serialização/entrega real. | Obter versão/layout oficial, golden files, homologação e confirmação humana do destino; manter bloqueado até então. |
| Conciliação | PARTIAL | Regras de diferença, exceção, match e aprovação existem no domínio. | Criar caso de uso/persistência e validação operacional com extratos reais autorizados. |
| Bloqueios | PARTIAL | Escopos e canais são testados na jornada; desbloqueio exige nova revisão. | Persistir e operar catálogo de locks real, incluindo revalidação em todos os jobs/canais futuros. |
| Auditoria | PARTIAL | AuditEvent append-oriented, hash de integridade e atomicidade com efeito são testados. | Validar retenção, consulta autorizada, backup/restore, monitoramento de adulteração e banco MySQL. |
| Observabilidade | PARTIAL | Logs JSON sanitizados, correlação, eventos técnicos e métricas locais foram implementados. | Integrar coletor central, alertas, retenção, dashboards e métricas distribuídas; registry local não atende múltiplas réplicas. |
| Testes | PARTIAL | Suíte local registra 235 testes aprovados, incluindo E2E e regressão OFX. | Executar no CI e em MySQL homologado; adicionar carga, DAST, restore, UAT contábil e testes com corpus autorizado. |
| Documentação | PARTIAL | ADRs, E2E, segurança, regressão e observabilidade estão documentados. | Criar runbooks de deploy, incidente, backup/restore, rotação de segredos, onboarding e rollback operacional. |
| Privacidade | BLOCKED | Há minimização em logs/auditoria, mas não há política de retenção, base legal, DSR, legal hold ou inventário de dados. | Aprovar governança LGPD, retenção por tipo/finalidade, processo de incidente e controles de acesso/eliminação. |
| Rollback | BLOCKED | A UoW faz rollback transacional em falha; não existe rollback operacional de release/migration/dados. | Definir estratégia de deploy reversível, backup pré-migration, critérios de abortar piloto e ensaio de recuperação. |

## Bloqueios que impedem o piloto

1. Backup e restore comprovados para MySQL e object storage.
2. Autenticação/provisionamento real de usuários e contexto tenant confiável.
3. MySQL homologado com migrations e constraints exercitados fora do SQLite.
4. Governança de privacidade e retenção aprovada.
5. Runbook de rollback e operação de incidente.

O bloqueio do Domínio não impede, por si só, um piloto estritamente interno e
sem exportação oficial, mas impede qualquer promessa de entrega/escrituração no
sistema externo. O status deve ser reavaliado depois que todos os bloqueios
acima tiverem evidência verificável.
