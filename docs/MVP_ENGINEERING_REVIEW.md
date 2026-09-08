# Revisão final de engenharia do MVP

Revisão em 07/09/2026. Escopo: código, migrations, testes, configurações e
documentação presentes no repositório. Não foi realizada homologação externa,
teste de carga, DAST, backup/restore ou execução em MySQL real.

## Conclusão

**O MVP não está liberado para piloto com escritório real.** A base é adequada
para continuar a preparação controlada, mas faltam pré-condições operacionais
e fluxos reais que não podem ser substituídos por fixtures ou dados sintéticos.

## Avaliação por área

| Área | Avaliação | Evidência |
| --- | --- | --- |
| Arquitetura e módulos | Boa base modular: domínio, aplicação, portas e adaptadores estão separados na maior parte dos módulos. | `src/serdial21/modules/*`; testes de fronteira de acesso. |
| Dependências | Stack é pequena e compatível com a decisão aprovada; há lockfile. | `pyproject.toml`, `requirements.lock`. |
| Banco e migrations | Configuração MySQL, UTC, UTF-8 e Alembic estão presentes; há oito revisions. | `bootstrap/database.py`, `alembic/env.py`, `alembic/versions`. |
| Tenant e autorização | Filtros tenant/company, CompanyAccess e negação uniforme são bem cobertos no domínio e repositórios. | `test_tenant_authorization.py`, E2E vertical. |
| Invariantes contábeis | `Decimal`, lançamentos balanceados, conta lançável, vigência, versões e segregação são testados. | testes de pré-ledger, plano, regras, mapping e workflow. |
| Idempotência e auditoria | Há chaves/hash, conflitos, eventos append-oriented e rastreio reverso. | operações críticas, intake e E2E vertical. |
| Segurança | XML/OFX, uploads, path traversal, logs sanitizados e headers receberam hardening. | `SECURITY_REVIEW_EXECUTION_22.md`. |
| Observabilidade | Há logs técnicos JSON, correlação e métricas locais, separados de `AuditEvent`. | `OBSERVABILITY_MVP.md`. |
| Testes | Cobertura unitária/integrada ampla, incluindo 235 testes locais aprovados na última execução. | `TEST_COVERAGE_MVP.md`. |

## BLOQUEADORES

| Problema | Por que impede o piloto | Ação exigida |
| --- | --- | --- |
| Sem autenticação externa e contexto HTTP confiável | Usuário, tenant e empresa não podem ser derivados de uma identidade autenticada em produção. IDs não podem ser tratados como autorização. | Escolher/provisionar IdP, implementar autenticação, sessão/token validado e onboarding/offboarding. |
| Catálogo real de regras/plano/workflow não existe na composição de produção | A jornada vertical usa `JourneyCatalog` sintético; não há operação persistida e governada para o escritório configurar plano, regras e workflow publicados. | Implementar/configurar o catálogo real, publicação versionada e revisão contábil antes de receber documentos do escritório. |
| MySQL real não homologado | As migrations e constraints são exercitadas em SQLite; isso não prova compatibilidade de dialect, índice, FK, concorrência ou upgrade no SGBD alvo. | Definir versão suportada e executar upgrade/replay/carga em MySQL homologado. |
| Backup, restore e rollback operacional ausentes | Não há prova de recuperação de banco e evidências, nem RPO/RTO ou runbook de incidente. | Criar política, automação, backup pré-migration e ensaio de restore isolado por tenant. |
| Privacidade e retenção não definidas | O piloto manipulará dados fiscais e bancários, mas não há política de retenção, base legal, DSR, legal hold ou inventário de dados. | Aprovar governança LGPD e seus controles antes de ingestão de dados reais. |
| Sem canal operacional para o fluxo humano | A API expõe apenas health checks; não há endpoint/interface autenticada para importação, revisão, aprovação ou consulta controlada. | Definir e implementar a borda operacional mínima, com contratos, autorização e testes. |
| Domínio não homologado | O conector está corretamente fail-closed, mas não gera nem entrega arquivo oficial. | Obter layout/versão, golden files e homologação; manter bloqueado até confirmação. |

## ALTO RISCO

| Problema | Risco | Correção recomendada antes do piloto |
| --- | --- | --- |
| Segurança de borda incompleta | Não há rate limiting distribuído, TLS/HSTS/host allowlist documentados, limite de corpo no proxy ou scanner CVE no CI. | Formalizar proxy/gateway e pipeline de segurança. |
| Storage e banco não têm protocolo de recuperação conjunto | A escrita da evidência ocorre fora da transação do banco; uma falha posterior pode deixar objeto órfão. | Criar reconciliação/garbage collection auditável e testar falha parcial antes de operação real. |
| Observabilidade não é distribuída | Métricas são locais ao processo, sem coletor, alertas, retenção ou dashboards. | Exportar métricas/logs para infraestrutura central e validar alertas operacionais. |
| NF-e/OFX sem corpus real homologado | Parsers e deduplicação foram testados com fixtures sintéticas, não com documentos autorizados do escritório. | Montar corpus anonimizado/autorizado e executar UAT contábil. |
| Sem CI obrigatório | O repositório não demonstra pipeline que imponha testes, análise de dependências, lint, tipos e migrations. | Criar gate de CI antes de qualquer release piloto. |

## MELHORIAS

- Expor métricas somente por coletor autenticado, após decisão de infraestrutura.
- Adicionar testes de carga, concorrência real MySQL, DAST e testes de contrato de API quando a borda existir.
- Evoluir cobertura de XML para XSD/XMLDSIG se isso entrar no escopo formal da NF-e.
- Criar dashboards por SLO e runbooks de alerta depois da escolha do coletor.
- Adicionar suporte a novos documentos fiscais somente por fatia aprovada; CT-e e NFS-e continuam fora do MVP atual.

## DÍVIDA TÉCNICA CONSCIENTE

| Dívida | Justificativa atual | Limite de segurança |
| --- | --- | --- |
| Conector Domínio fail-closed | Não há layout/golden file homologado. | Nenhuma serialização, entrega ou declaração de efeito oficial. |
| Métricas em memória | Suficiente para a composição técnica local inicial. | Não usar como evidência operacional em múltiplas réplicas. |
| SQLite nos testes de integração | Mantém execução rápida e reproduzível localmente. | Não considerar como homologação de MySQL. |
| OFX/NF-e com fixtures sintéticas | Permite testar contratos sem dados sensíveis. | Não substituir corpus autorizado nem UAT contábil. |
| Borda HTTP mínima | Evita expor comandos críticos sem autenticação aprovada. | Não disponibilizar importação/aprovação real por endpoint até a identidade existir. |

## Próximo gate objetivo

O próximo gate não é uma nova funcionalidade contábil. É a comprovação dos
bloqueadores: identidade, catálogo real governado, MySQL, recuperação,
privacidade, borda autenticada e — caso o piloto inclua exportação —
homologação do Domínio. Somente evidências verificáveis desses itens permitem
reclassificar o MVP para piloto.
