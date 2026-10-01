# Mapa de referências normativas e técnicas

**Levantado em:** 01/10/2026, por varredura de `docs/`, `AGENTS.md`, `README.md` e comentários de `src/` (sem abrir `.env` nem `local_data/`).
**Uso:** ponto de partida da seção "Referências" de cada briefing (protocolo, seção 6). Este arquivo registra o que o repositório **já cita**; não substitui consultar a fonte vigente.
**Manutenção:** quem formalizar uma fonte acrescenta a linha aqui, com versão ou data.

## Conclusão do levantamento

O repositório cita pouquíssima fonte externa formal. A única decisão com fonte oficial citada é o CNPJ alfanumérico (`docs/adr/0017`, páginas da Receita Federal). Várias decisões fiscais, contábeis e de segurança foram tomadas **sem citar a norma**. Elas podem estar corretas, mas não são rastreáveis.

## 1. Referências já citadas

| Referência | Tema | Onde é citada | Implementada? |
|---|---|---|---|
| Receita Federal (páginas gov.br) — CNPJ alfanumérico | CPF/CNPJ, DV módulo 11 | `docs/adr/0017-identificador-fiscal-e-cnpj-alfanumerico.md` | Sim — `access_control/domain/tax_identifiers.py` (sem citar a fonte no código) |
| LGPD, arts. 16, 18 e 19 (sem número da lei) | Incidente, direitos do titular | `docs/PRIVACY_INCIDENT_PROCESS.md` | Não — `PENDING_HUMAN_LEGAL_APPROVAL` |
| Resolução CD/ANPD 15/2024 | Comunicação de incidente | `docs/PRIVACY_INCIDENT_PROCESS.md` | Não — só runbook |
| LGPD (genérica) | Governança, base legal, retenção | `docs/LGPD_DATA_GOVERNANCE.md`, `docs/legal/LGPD_LEGAL_REVIEW_CHECKLIST.md` | Parcial — estrutura de retenção sem prazos aprovados |
| Domínio Sistemas, solução 672 (leiaute com separador) | Exportação de lançamentos | `docs/specifications/dominio/` | Parcial, com gate até o golden file oficial |
| NF-e: namespace `portalfiscal.inf.br/nfe` e XSD oficial (sem versão) | Parser NF-e 55 | `docs/adr/0006-importador-nfe55.md` | Parcial — validação estrutural; XSD e XMLDSIG não implementados |
| OFX 1.x (SGML) e 2.x (XML) | Extrato bancário | `docs/FINANCIAL_MODULE_SPEC.md` | Sim — `banking/adapters/inbound/ofx.py` (especificação não citada) |
| OAuth 2.0 / OIDC, JWT RS256, JWKS, PKCE (sem RFC) | Identidade | `docs/AUTH_FRONTEND_INTEGRATION.md`, `docs/adr/0014` | Sim |
| Argon2id | Hash de senha | `docs/adr/0016` | Não — legado em SHA-256 |
| WCAG AA | Acessibilidade | `docs/ACCESSIBILITY_GUIDELINES.md` | Parcial |
| ISO 8601 | Datas e competência no contrato de integração | `docs/integration/CONNECT_HUB_ARCHITECTURE.md` | Parcial |

## 2. Fontes ausentes que deveriam ser formalizadas (com versão)

| Fonte | Para quê | Prioridade |
|---|---|---|
| Manual de Orientação do Contribuinte NF-e + Notas Técnicas vigentes + pacote XSD | DV da chave, códigos `cStat`, grupos de tributos, tipos numéricos | Alta (antes de ampliar o fiscal) |
| Instrução Normativa RFB do CNPJ alfanumérico | Citar a norma, não só a página | Média |
| Especificação OFX (1.x e 2.x) | Datas com fuso, sinal e casas decimais | Alta (afeta competência) |
| RFC 7519, RFC 7517, OpenID Connect Core 1.0, RFC 9700 | Identidade e ponte de login | Média |
| OWASP ASVS (nível alvo a definir) | Critério de aceite de segurança | Média |
| Prazos legais de guarda de documentos fiscais e contábeis | Matriz de retenção (`docs/DATA_RETENTION_MATRIX.md` está toda "A DEFINIR") | Alta — exige validação jurídica/contábil |
| NBC / ITG 2000 (escrituração contábil) | Base das regras de lançamento e partidas | Alta antes de qualquer regra contábil nova |
| Documento oficial completo da solução Domínio 672 + golden file | Liberar a serialização | Bloqueante da exportação |

## 3. Decisões normativas no código sem fonte citada (revisar)

**Possíveis defeitos de competência — verificados no código em 01/10/2026:**

- `src/serdial21/modules/operations/adapters/outbound/persistence/repositories.py:217-219` — filtros de período usam a virada do dia em **UTC**, não no fuso da empresa. Um documento recebido às 22h de 31/01 em São Paulo (01h de 01/02 UTC) cai no mês seguinte. O `AGENTS.md` 6.5 proíbe inferir competência pelo fuso do servidor.
- `src/serdial21/modules/banking/adapters/inbound/ofx.py:172-180` — a data OFX descarta hora e fuso (`[..]`). Uma transação perto da meia-noite pode mudar de dia e de competência.

**Sem fonte citada, a confirmar contra a norma:**

- DV da chave de acesso NF-e e posição do modelo — `fiscal_documents/adapters/inbound/nfe55_xml.py:131, 826-834`.
- `cStat 100` tratado como autorizada — `nfe55_xml.py:236-240`, `docs/adr/0006`.
- Subconjunto de grupos de tributos e CST/CSOSN — `nfe55_xml.py:458-468, 512`.
- Precisões NUMERIC (20,2; 20,6; 20,10; 12,6) — `docs/adr/0006`, sem relação declarada com os tipos do XSD.
- OFX com no máximo 2 casas e sinal preservado — `ofx.py:157, 167`.
- Pesos de evidência na classificação (NCM 10, CFOP 5) — `accounting/domain/classification.py:181-183`.
- Partidas compostas e `balanced` — `docs/ACCOUNTING_INTELLIGENCE_SPEC.md:20`.
- Escopo de competência/exercício nos bloqueios — `locks/domain/entities.py:59, 129-135`.
- Fuso `America/Sao_Paulo` e moeda `BRL` fixos no import de empresa — `company_import.py:23-24`, `docs/adr/0013`.
- Tolerância de relógio OIDC de 30 s — `bootstrap/settings.py`.

**Decisões formalmente em aberto:** DEC-005 (precisão, arredondamento, tolerância), DEC-002 e DEC-008 — `docs/engenharia-produto/14-backlog-tecnico-mvp.md`.

## 4. Documentos internos de maior autoridade por domínio

| Domínio | Documento |
|---|---|
| Regras gerais | `AGENTS.md` |
| Visão e fases | `docs/PROJECT_MASTER_GUIDE.md` |
| Estado atual | `docs/DOSSIE_MESTRE_ESTADO_ATUAL_2026-09-30.md` |
| Identidade e segurança | `docs/IDENTITY_AND_TENANT_SECURITY.md`, `docs/SECURITY_CONFIGURATION_MATRIX.md`, `docs/THREAT_MODEL.md` |
| Fiscal / NF-e | `docs/adr/0006-importador-nfe55.md`, `docs/FISCAL_MODULE_SPEC.md` |
| Identificador fiscal | `docs/adr/0017-identificador-fiscal-e-cnpj-alfanumerico.md` |
| Contábil e regras | `docs/ACCOUNTING_INTELLIGENCE_SPEC.md`, `docs/adr/0011-accounting-automation-core.md`, `docs/accounting/` |
| Decisões contábeis em aberto | `docs/engenharia-produto/14-backlog-tecnico-mvp.md` |
| Integração Domínio | `docs/specifications/dominio/` |
| Integração Sistema A / Connect Hub | `docs/integration/CONNECT_HUB_ARCHITECTURE.md`, `docs/integration/INTEGRATION_CONTRACT_MATRIX.md` |
| Fluxo NF-e → Domínio | `docs/e2e/NF_E_TO_DOMINIO_PRE_HOMOLOGATION.md` |
| LGPD | `docs/LGPD_DATA_GOVERNANCE.md`, `docs/DATA_RETENTION_MATRIX.md`, `docs/PRIVACY_INCIDENT_PROCESS.md` |
| Deploy | `docs/DEPLOY_RUNBOOK.md`, `docs/INTERNAL_VPS_DEPLOYMENT.md`, `docs/PRODUCTION_SECURITY_CHECKLIST.md` |
