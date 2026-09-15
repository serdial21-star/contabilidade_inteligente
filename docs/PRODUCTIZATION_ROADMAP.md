# Productization Roadmap

Plano de evolução após as Execuções 27–36 encerradas. Somente PHASE 01 é executada nesta entrega. As demais fases exigem solicitação própria; dependências permitem sobreposição de planejamento, não liberação automática. [Cronograma](PRODUCTIZATION_TIMELINE.md), [backlog](PRODUCT_BACKLOG.md) e [gates](PRODUCT_RELEASE_BASELINE.md) são complementares.

## PHASE 01 — Release / Architecture / Environments

- OBJECTIVE: estabelecer baseline verificável do produto.
- DEPENDENCIES: fechamento de engenharia e inventário local.
- DELIVERABLES: nove documentos de baseline, arquitetura, fluxo, ambientes, roadmap, cronograma, backlog e briefs.
- GATE: inventário completo, documentos prontos, gates preservados, nenhuma alteração destrutiva.
- OUT_OF_SCOPE: funcionalidades, deploy, migrations Runtime e reabertura das Execuções 27–36.

## PHASE 02 — Design System + UX

- OBJECTIVE: traduzir identidade e decisão profissional em sistema visual consistente.
- DEPENDENCIES: Phase 01; revisão da prévia existente e dos contratos.
- DELIVERABLES: tokens, tipografia, componentes, linguagem de status, navegação e protótipos acessíveis; resolução das divergências da prévia.
- GATE: aprovação de UX/identidade, acessibilidade e distinção automação/decisão; VISIBILITY <= AUTHORIZATION.
- OUT_OF_SCOPE: novas regras contábeis, autenticação fictícia e frontend completo.

## PHASE 03 — Marketing Website

- OBJECTIVE: comunicar valor e escopo de forma fiel.
- DEPENDENCIES: Phases 01/02; brief comercial; gates 11/13 antes de exposição/coleta.
- DELIVERABLES: páginas do brief, conteúdo e jornada de demonstração revisados.
- GATE: validação visual, acessibilidade e alegações; publicação depende de external exposure aprovado.
- OUT_OF_SCOPE: prometer Domínio homologado, dados reais autorizados ou funcionalidades apenas planejadas.

## PHASE 04 — Web App Shell + Authentication UX

- OBJECTIVE: oferecer navegação e sessão utilizáveis com identidade real.
- DEPENDENCIES: Phase 02, OIDC/backend existentes e contrato operacional; infraestrutura antes de exposição.
- DELIVERABLES: shell, seleção de empresa autorizada, login/logout, expiração e erros de acesso; decisão técnica frontend documentada.
- GATE: integração OIDC e testes negativos tenant/company, sessão e acesso.
- OUT_OF_SCOPE: novo IdP sem decisão, acesso por ID ou credenciais no navegador.

## PHASE 05 — Minha Visão

- OBJECTIVE: orientar ações e prioridades do profissional.
- DEPENDENCIES: Phase 04 e inventário de consultas/agregações autorizadas.
- DELIVERABLES: widgets, adicionar/remover/mover/redimensionar/salvar visão e estados vazio/erro/sem permissão.
- GATE: VISIBILITY <= AUTHORIZATION; agregados completos e corretos, sem apresentar página parcial como total.
- OUT_OF_SCOPE: concessão de acesso por personalização e aprovação automática.

## PHASE 06 — Clients + Documents

- OBJECTIVE: disponibilizar empresas e evidências nos limites existentes.
- DEPENDENCIES: Phase 04; access_control, intake e CompanyAccess.
- DELIVERABLES: jornadas de empresas/documentos, upload, deduplicação, processamento e rastreabilidade.
- GATE: contratos reutilizados; upload seguro, evidência imutável e isolamento comprovados.
- OUT_OF_SCOPE: CRM completo, sobrescrita de evidência e novos tipos documentais sem escopo.

## PHASE 07 — Fiscal + Financial

- OBJECTIVE: tornar NF-e/OFX e exceções utilizáveis.
- DEPENDENCIES: Phase 06; parsers e importadores existentes.
- DELIVERABLES: interfaces fiscal/financeira, erros e pendências; levantamento explícito dos gaps de conciliação.
- GATE: casos sintéticos/corpus autorizado e sinais/duplicidades corretos; conciliação só declarada pronta se o caminho operacional for implementado e validado em escopo aprovado.
- OUT_OF_SCOPE: pressupor conciliação completa, CT-e/NFS-e ou integração fiscal oficial.

## PHASE 08 — Accounting Intelligence

- OBJECTIVE: expor catálogo, regras e propostas com controle profissional.
- DEPENDENCIES: Phases 06/07; catálogo publicado, regras e workflow existentes.
- DELIVERABLES: interface de classificação/propostas/revisão/aprovação e versões; configuração sem inventar conteúdo.
- GATE: hash/revisão, segregação, alçada, imutabilidade, locks e idempotência comprovados na interface/API.
- OUT_OF_SCOPE: novas regras padrão, IA decisora e escrituração oficial.

## PHASE 09A — Integration Readiness

- OBJECTIVE: definir a integração entre o Serdial21 Operacional e o Contabilidade Inteligente sem implementar conexão.
- DEPENDENCIES: Phase 08, dossiês do Sistema A e baseline verificável do Sistema B.
- DELIVERABLES: ownership, camada anticorrupção, contratos/eventos propostos, segurança M2M, homologação, riscos, backlog P0 e ondas.
- GATE: `INTEGRATION: CONDITIONAL_GO`; nenhuma alteração de código, banco, workflow, credencial ou deploy.
- OUT_OF_SCOPE: implementar Connect Hub, conectar ambientes ou usar dados reais.

## PHASE 09 — Linha da Decisão

- OBJECTIVE: tornar a origem e a decisão rastreáveis visualmente.
- DEPENDENCIES: Phase 08 e mapa de dados/gaps em PRODUCT_FLOW.
- DELIVERABLES: timeline SOURCE → PROCESSING → RULE → PROPOSAL → REVIEW → APPROVAL; projeção mínima autorizada quando necessária.
- GATE: fidelidade aos eventos/snapshots, versões exatas, dados mínimos e testes de permissão.
- OUT_OF_SCOPE: histórico inventado, reescrita de auditoria e inferir leitura profissional por abrir tela.

## PHASE 10 — Portal & Operations Integration

- OBJECTIVE: reutilizar o Portal/Operações do Sistema A e congelar como capacidades do Sistema B serão expostas sem criar um segundo portal.
- DEPENDENCIES: Phases 09A/09; estabilização runtime do Sistema A e contratos dedicados propostos.
- DELIVERABLES: journeys integradas, deep links, projeções operacionais e contratos aprovados para cliente, documento, tarefa e decisão.
- GATE: ownership preservado, ausência de poder contábil no portal, contratos v1 e P0 de Wave 0 resolvidos.
- OUT_OF_SCOPE: conexão de produção, duplicar portal, usar API admin/browser como M2M ou conceder aprovação contábil ao cliente.

## PHASE 10A — Connect Hub MVP

- OBJECTIVE: implementar, em solicitação futura própria, Waves 1–5 do Hub e conector Serdial21 em homologação.
- DEPENDENCIES: Phase 10; contract freeze; identidade M2M; referências externas; topologia HOM isolada.
- DELIVERABLES: client sync, document intake, processing result, task required e decision visibility, com inbox/outbox, idempotência, retry/DLQ e observabilidade.
- GATE: E2E integralmente sintético, testes de falha e segurança, sem cross-system write e sem dados reais.
- OUT_OF_SCOPE: produção, publicação/obrigações Wave 6, Domínio e outros conectores.

## PHASE 11 — Security Infrastructure

- OBJECTIVE: completar condições técnicas para exposição externa.
- DEPENDENCIES: estratégia de ambientes, serviço/fornecedores e execução autorizados.
- DELIVERABLES: CORS_ALLOWLIST, HTTPS_REVERSE_PROXY, HSTS, DISTRIBUTED_RATE_LIMIT, CENTRAL_METRICS, ALERT_TRANSPORT e IDP_SESSION_REVOCATION em coordenação com Phase 12.
- GATE: cada controle com evidência operacional; revisão explícita de external exposure.
- OUT_OF_SCOPE: marcar pronto pela mera existência de configuração ou liberar dados reais.

## PHASE 12 — Observability + Recovery

- OBJECTIVE: operar, detectar falhas e recuperar banco/evidências.
- DEPENDENCIES: Phases 01/11; métricas locais e runbooks existentes.
- DELIVERABLES: coleta/alertas centrais, backups de banco/storage, restore e drills; objetivos RPO/RTO revisados.
- GATE: alertas entregues e recuperação demonstrada; backup pre-deploy/hash e migration 0012 verificada em tarefa operacional aprovada.
- OUT_OF_SCOPE: downgrade operacional, prometer SLA sem medição ou tratar logs como auditoria.

## PHASE 13 — LGPD + Legal Gates

- OBJECTIVE: aprovar finalidades, corpus e procedimentos de privacidade.
- DEPENDENCIES: controles privacy existentes, responsáveis humanos e evidências de fornecedores/operação.
- DELIVERABLES: decisões jurídicas, corpus autorizado, retenção/legal hold/DSR/backup e PRIVACY_OPERATIONAL_APPROVAL.
- GATE: LEGAL_APPROVAL e aprovações aplicáveis com evidência humana; destruição não é liberada por este plano.
- OUT_OF_SCOPE: inventar base/prazo legal ou considerar anonimização autoautorização.

## PHASE 14 — Integrated QA + UAT

- OBJECTIVE: verificar produto integrado e uso profissional.
- DEPENDENCIES: entregas selecionadas das Phases 04–13 e corpus permitido.
- DELIVERABLES: QA de interfaces/contratos/segurança, casos críticos e UAT contábil documentado.
- GATE: defeitos críticos resolvidos, evidências atualizadas e ACCOUNTANT_SIGNOFF humano.
- OUT_OF_SCOPE: substituir UAT por demo visual ou reaproveitar PASS histórico como novo resultado.

## PHASE 15 — Controlled Real Pilot

- OBJECTIVE: validar operação real em escopo restrito aprovado.
- DEPENDENCIES: Phase 14; todos os seis gates real data; external exposure aprovado se houver acesso externo.
- DELIVERABLES: plano de piloto, participantes/corpus autorizados, observação, incidentes e critérios de parada/recuperação.
- GATE: decisão humana GO específica, revisão de resultados e ausência de bloqueios críticos.
- OUT_OF_SCOPE: piloto real antes dos gates, ampliar tenants/corpus sem autorização e Domínio sem homologação.

## PHASE 16 — Commercial Launch Readiness

- OBJECTIVE: decidir prontidão comercial com evidência.
- DEPENDENCIES: Phase 15, operação/suporte, onboarding, termos e definição de SaaS/billing.
- DELIVERABLES: checklist de lançamento, escopo comercial, suporte, onboarding e decisão sobre modelo de cobrança/operação.
- GATE: launch readiness formal; GO não equivale a deploy/publicação automática.
- OUT_OF_SCOPE: cobrar/publicar automaticamente, prometer escala ilimitada ou iniciar funcionalidades futuras.
