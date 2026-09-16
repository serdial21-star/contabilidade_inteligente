# Phase 14 — Plano de UAT integrado

## Escopo

Homologação técnica integrada do produto atual com dados exclusivamente
sintéticos: autenticação/contexto, Minha Visão, empresas, documentos, NF-e,
propostas contábeis, decisões, AccountLock, OFX, Linha da Decisão, privacidade,
segurança, observabilidade e health/readiness.

## Fora do escopo

Dados reais, produção, IdP real, migration 0012, Domínio externo, System A,
Connect Hub, posting contábil, OFX para contabilidade, nova funcionalidade,
aprovação jurídica/contratual e aceite humano antecipado.

## Ambiente e fixtures

- commit-base: `6583a69` (`feat: complete phase 13 privacy and legal technical gates`);
- aplicação FastAPI/TestClient, SQLite temporário e providers sintéticos;
- `tests/fixtures/nfe55/valid_minimal.xml`, XMLs inválidos produzidos pelos
  testes e OFX fictício embutido;
- UUIDs, usuários, tenants e empresas gerados por fixture a cada teste;
- sem CNPJ, conta, identidade, documento ou credencial real;
- runtime Node/browser indisponível; validação visual segue checklist manual.

## Estratégia

1. smoke integrado de APIs, persistência, E2E e contratos frontend;
2. cenários complementares para regras, idempotência, segurança, privacidade e
   observabilidade;
3. browser real quando disponível; caso contrário, signoff manual obrigatório;
4. corrigir somente defeitos P0/P1 comprovados;
5. uma única regressão completa no encerramento.

## Severidade

| Grau | Critério |
|---|---|
| P0 | isolamento, corrupção, integridade contábil, decisão não autorizada ou aplicação inutilizável |
| P1 | fluxo central quebrado sem workaround ou contrato/estado contábil incorreto |
| P2 | problema importante com workaround e sem perda de integridade |
| P3 | cosmético, texto, espaçamento ou impacto baixo |

## Aceite e saída

- todos os cenários automatizáveis executados, sem P0/P1 aberto;
- NF-e golden/duplicada/inválida/no-rule/conflito de regras aprovados;
- Decimal, idempotência, auditoria e isolamento preservados;
- regressão final e scanner de segredos aprovados;
- banco/schema inalterados e migration 0012 não executada;
- browser igual a `PASS` ou `MANUAL_SIGNOFF_REQUIRED` com checklist pronto.

UAT humano, jurídico, contrato e infraestrutura continuam gates independentes.
