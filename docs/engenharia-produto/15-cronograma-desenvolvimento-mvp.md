# Serdial21 — Cronograma de Desenvolvimento do MVP

| Controle | Valor |
|---|---|
| Estado | **PROPOSTA EXECUTIVA PARA APROVAÇÃO** |
| Versão | 0.2 |
| Data-base | 03/09/2026 |
| Kickoff operacional | 08/09/2026 — 07/09 é feriado nacional |
| Baseline | DAT-01 a DAT-10, ARQ-01 a ARQ-10, modelo lógico, PY-01 a PY-08 e backlog S0–S8 aprovados |
| Escopo do piloto | NF-e 55, CT-e 57, NFS-e padrão nacional, OFX, CSV configurável e TXT Domínio Sistemas |
| Volumetria conhecida | Aproximadamente 1.000 documentos por mês |
| Previsão-base | 17 sprints quinzenais; release candidate em 30/04/2027; go/no-go em 28/05/2027 |

## 1. Resultado executivo

Há base suficiente para iniciar o aplicativo. O cronograma recomendado possui quatro marcos de valor:

1. fundação segura e onboarding até 16/10/2026;
2. primeira jornada NF-e ponta a ponta até 27/11/2026;
3. beta de todas as entradas do piloto até 05/02/2027;
4. integração Domínio reconciliada até 02/04/2027;
5. release candidate com IA assistiva até 30/04/2027;
6. operação paralela e decisão de go/no-go até 28/05/2027.

Esta é uma previsão de engenharia, não compromisso comercial. Ela será reestimada no Gate G0 com a equipe real, os arquivos reais e o ambiente de homologação. Produção será liberada por evidência de gate, não apenas pela data.

## 2. Escopo incorporado

| Decisão | Conteúdo incorporado |
|---|---|
| DEC-001 | NF-e 55 primeiro; depois CT-e 57 e NFS-e padrão nacional. Schemas, notas técnicas, parsers e canônicos versionados. |
| DEC-002 | OFX principal, famílias 1.x SGML-like e 2.x XML; CSV configurável em seguida. Open Finance e CNAB fora deste MVP. |
| DEC-003 | Domínio Sistemas como primeiro destino; TXT, importação manual e confirmação humana. API apenas após acesso, contrato e homologação. |
| DEC-010 | Aproximadamente 1.000 documentos/mês. Ainda faltam pico, tamanho, itens, transações, empresas, usuários simultâneos e SLA. |

O volume conhecido é baixo/moderado. Ele confirma monólito modular, banco relacional, object storage e workers com jobs/outbox. Não justifica microsserviços, Kubernetes, sharding, broker dedicado, cache distribuído ou particionamento antecipado.

## 3. Premissa de equipe

A previsão-base pressupõe dedicação semelhante a:

| Papel | Capacidade |
|---|---:|
| Product Owner / analista de produto | 1,0 FTE |
| Tech lead / arquiteto com atuação backend | 1,0 FTE |
| Engenharia backend de domínio e integrações | 2,0 FTE |
| Engenharia frontend / full-stack | 2,0 FTE |
| QA com automação | 1,0 FTE |
| DevSecOps / plataforma | 0,5 FTE |
| UX / Product Design | 0,5 FTE |
| Contador especialista e homologador | 0,5 FTE |
| Engenharia de IA a partir de S7 | 0,5 FTE |

Também pressupõe:

- decisão do Product Owner e contador em até dois dias úteis;
- corpus anonimizado e autorizado disponível nos gates;
- acesso a empresa de homologação e versão identificada do Domínio;
- trabalho fiscal, bancário, frontend e QA em paralelo depois de S1;
- IA sob feature flag e fora do caminho obrigatório de integridade;
- capacidade reduzida de 14/12/2026 a 08/01/2027, sem marco crítico.

Com somente quatro pessoas no núcleo, o plano deve ganhar de oito a dez sprints ou o primeiro piloto deve ser reduzido a NF-e + OFX + TXT Domínio.

## 4. Cronograma por sprint

| Sprint | Datas | Slice | Resultado demonstrável | Gate principal |
|---|---:|---|---|---|
| 01 | 08–18/09/2026 | S0-A | Repositório, CI, módulos, value objects, contexto e primeira API/comando | Comando carrega tenant, empresa, ator, correlação e chave idempotente |
| 02 | 21/09–02/10 | S0-B | Autorização, transação, inbox/outbox, auditoria, logs e testes de isolamento | Retry retorna mesmo resultado; revogação funciona; zero acesso cross-tenant |
| 03 | 05–16/10 | S1 | Tenant, empresa, usuários, CompanyAccess, plano, período e DE/PARA mínimo | Escritório prepara empresa; analista vê apenas empresas autorizadas |
| 04 | 19–30/10 | S2-A / S4 paralelo | Upload, evidência imutável, lote, hash; detecção NF-e e fundação OFX | Original, origem, hash, schema e parser existem antes de qualquer derivação |
| 05 | 02–13/11 | S2-B / S4 paralelo | NF-e canônica, itens, tributos, linhagem, regra inicial e proposta balanceada | Cada NF-e vira proposta ou pendência acionável; toda linha possui origem |
| 06 | 16–27/11 | S2-C | M19, aprovação por revisão/hash, telas de revisão e arquivo genérico | NF-e → proposta → aprovação → arquivo; sem aprovação não há efeito exportável |
| 07 | 30/11–11/12 | S3-A / S4-A | Quarentena, duplicidade, conflito, dry-run e reprocesso; OFX 1.x/2.x canônico | Entrada hostil não produz efeito; reimportação não duplica |
| — | 14/12–08/01 | Estabilização | Fixtures, correções, documentação e segurança com capacidade reduzida | Nenhum marco crítico depende desta janela |
| 08 | 11–22/01/2027 | S3-B / S4-B | CT-e 57 e primeira conciliação manual OFX | CT-e é validado por versão; movimento conserva sinal, moeda, datas e origem |
| 09 | 25/01–05/02 | S3-C / S4-C | NFS-e nacional, CSV configurável e conciliação 1:1, divisão e agrupamento | Layout CSV é reutilizável; ambiguidade vira M19; sem sobre-alocação |
| 10 | 08–19/02 | S5-A | DE/PARA e regras versionadas; testar, revisar, aprovar e publicar | Release publicada é imutável e apenas perfil autorizado a promove |
| 11 | 22/02–05/03 | S5-B | Trace, precedência, conflitos, simulação, diff e níveis N0–N2 | Mesma entrada e versões produzem o mesmo resultado; empate vira pendência |
| 12 | 08–19/03 | S6-A | AccountLock, lotes imutáveis, manifesto, hash e gerador TXT Domínio | Lock vale em todo canal; arquivo confere empresa, contas e totais |
| 13 | 22/03–02/04 | S6-B | Importação real Domínio, confirmação, rejeição, parcialidade e UNKNOWN | Retry conserva identidade; resultado incerto é reconciliado antes de reenvio |
| 14 | 05–16/04 | S7-A | IA em tarefa estreita, com saída estruturada, evidência e confiança | IA só sugere; resposta inválida vira pendência |
| 15 | 19–30/04 | S7-B | Feedback, avaliação, privacidade, redaction e fallback determinístico | Indisponibilidade de IA não interrompe o fluxo; isolamento passa |
| 16 | 03–14/05 | S8-A | Início da operação paralela, carga, restore, retenção, segurança, dashboards, alertas e runbooks | Lote mensal e margem funcionam sem perda, mistura ou duplicidade |
| 17 | 17–28/05 | S8-B | Operação paralela, reconciliação contábil, treinamento e correções | Aceite formal e decisão go/no-go |

Reserva recomendada: 31/05 a 11/06/2027 para contingência de defeito crítico, mudança de schema ou atraso de homologação. A reserva não deve ser consumida para expansão de escopo.

## 5. Marcos e gates

| Gate | Data-alvo | Evidência de saída |
|---|---:|---|
| G0 — Pronto para construir | 18/09/2026 | Equipe, stack, ambientes, decisões críticas, corpus e rota Domínio confirmados |
| G1 — Fundação segura | 02/10/2026 | Primeiro efeito tenant-aware, autorizado, idempotente e auditado |
| G2 — Onboarding | 16/10/2026 | Empresa, acessos, plano, período e DE/PARA prontos |
| G3 — Alpha NF-e | 27/11/2026 | Jornada NF-e completa com M19 e arquivo genérico |
| G4 — Beta de entradas | 05/02/2027 | NF-e, CT-e, NFS-e nacional, OFX e CSV aprovados no corpus |
| G5 — Beta determinística | 05/03/2027 | Regras, DE/PARA, trace, simulação e pré-ledger governados |
| G6 — Beta Domínio | 02/04/2027 | TXT importado e reconciliado sem duplicidade |
| G7 — Release candidate | 30/04/2027 | IA assistiva com fallback e sem autoridade de efeito |
| G8 — Go/no-go | 28/05/2027 | Ciclo paralelo, segurança, recuperação e aceite contábil concluídos |

### G0 — decisões e insumos obrigatórios

Até 18/09/2026:

- selecionar tecnologias e estratégia física de isolamento — DEC-011;
- fechar granularidade de lançamento — DEC-004;
- fechar precisão, arredondamento, moeda e tolerância — DEC-005;
- aprovar papéis, alçadas, quórum e segregação — DEC-007;
- aprovar retenção, legal hold e offboarding — DEC-008;
- aprovar SLA, RPO, RTO e frequência de restauração — DEC-009;
- medir pico por lote/dia, tamanho máximo, itens, transações, empresas e usuários;
- obter corpus fiscal/bancário anonimizado e autorizado;
- identificar versão do Domínio e obter layout, dataset e arquivos golden aplicáveis.

A validação documental encontrou três fluxos TXT diferentes no Domínio: o leiaute externo com separador, o conjunto de dados de planilha/CSV e o round-trip de TXT exportado pelo próprio sistema. O G0 deve escolher um deles explicitamente; formatos, campos e garantias não podem ser misturados.

Se o layout exato não estiver disponível, o exportador configurável pode ser desenvolvido, mas não poderá ser declarado homologado.

## 6. Entregas por área

### Backend e dados

- tenancy e autorização em profundidade;
- evidência imutável, hash, receipts, staging e quarentena;
- modelo canônico fiscal, bancário e pré-ledger;
- regras e DE/PARA versionados;
- M19, aprovação por revisão/hash e AuthorizedEffect;
- jobs, inbox/outbox, auditoria e idempotência;
- layout e conector com manifesto, retry e UNKNOWN.

### APIs

- identidade, contexto e autorização;
- tenant, membership, company e CompanyAccess;
- empresa, plano, conta, período e mappings;
- uploads, batches, evidências, documentos, issues e reprocesso;
- propostas, revisões, M19, decisões e locks;
- extratos, movimentos, candidatos e conciliações;
- layouts, export batches, downloads e confirmações;
- sugestões de IA e feedback, sem endpoint privilegiado de efeito.

### Telas

- login, seleção de escritório/empresa e administração de acesso;
- onboarding, plano de contas, período e DE/PARA;
- central de importações, progresso, quarentena e reprocesso;
- documento fiscal e extrato com linhagem;
- proposta contábil e comparação com evidência;
- M19: fila, pendência, atribuição, aprovação, rejeição e retrabalho;
- conciliação bancária, divisão, agrupamento e exceções;
- bloqueios, lotes, prévia TXT, download e confirmação Domínio;
- auditoria, métricas, falhas, UNKNOWN, alertas e suporte.

## 7. Paralelização

Depois de G2:

| Trilha | Sequência |
|---|---|
| Fiscal | NF-e → robustez/eventos → CT-e → NFS-e nacional |
| Bancária | OFX → conciliação → CSV configurável |
| Core e UX | regras → pré-ledger → M19 → locks → IA |
| Integração e qualidade | contrato/layout Domínio → golden files → homologação; segurança e testes contínuos |

O motor de regras, o pré-ledger e o M19 são únicos e compartilhados pelos canônicos fiscal e bancário; não serão duplicados por trilha.

## 8. Caminho crítico

G0 insumos e decisões → S0 segurança/transação → S1 empresa/plano/DE-PARA → S2 NF-e/proposta/M19 → S5 regras/pré-ledger → S6 TXT Domínio homologado → S8 recuperação/segurança/operação → ciclo paralelo → G8.

OFX corre em paralelo, mas integra o caminho crítico do escopo completo na conciliação. CT-e, NFS-e e CSV não bloqueiam a primeira demonstração; bloqueiam a declaração de piloto completo.

## 9. Qualidade e homologação

Corpus mínimo:

- pelo menos 100 NF-e válidas e autorizadas, anonimizadas, cobrindo versões e operações observadas;
- pelo menos 25 casos fiscais negativos: XSD, namespace, modelo, chave, assinatura, truncamento, encoding, DTD/entidade, tamanho, duplicata e conflito;
- pelo menos 30 OFX de três bancos/exportadores, famílias 1.x e 2.x, somando no mínimo 1.000 transações;
- amostras positivas e negativas de CT-e, NFS-e nacional e layouts CSV;
- arquivos golden Domínio para lançamentos simples/multilinhas, históricos, centro de custo, competência, caracteres, decimais, limites e erros.

Validação XML deve separar:

1. XML bem-formado e seguro;
2. validade no XSD exato;
3. validade criptográfica XMLDSIG;
4. protocolo/status fiscal observado.

Uma validação não substitui as outras.

Cadência:

- a cada commit: unitários, propriedades, contratos, arquitetura, SAST, dependências e secrets;
- diariamente: integrações, migrations, corpus completo, tenancy, replay e idempotência;
- por slice: jornada positiva, negativa, concorrente, falha intermediária, retry, lock e auditoria;
- por release: regressão, DAST, carga, restore, UAT contábil e teste focal de segurança.

## 10. Critérios absolutos de go-live

1. zero vazamento entre tenants;
2. zero proposta aprovada desbalanceada;
3. zero efeito externo sem aprovação humana válida;
4. zero duplicidade externa provocada por retry;
5. 100% das linhas contábeis com proveniência e versões;
6. 100% das ações materiais auditáveis;
7. entradas hostis em quarentena, sem efeito parcial;
8. TXT Domínio reconciliado por empresa, período, quantidade, débitos, créditos, contas e centros de custo;
9. restore sem mistura de tenants e RPO/RTO comprovados;
10. nenhum defeito crítico ou alto aberto;
11. operação paralela aceita formalmente pelo contador, produto, segurança e operação.

## 11. Principais riscos

| Risco | Impacto | Tratamento |
|---|---|---|
| Layout/versão Domínio indisponível | Bloqueia G6 | Resolver no G0; iniciar homologação cedo; não inventar campos |
| Corpus real insuficiente | Cobertura falsa | Coletar por schema/banco, anonimizar, versionar e obter autorização |
| Decisão contábil lenta | Bloqueia regra e aceite | Contador com agenda fixa e SLA de dois dias úteis |
| Mudança de schema fiscal | Regressão/reprocesso | Catálogo versionado, ativação por feature flag e diff |
| NFS-e municipal fora do padrão | Expansão de escopo | Rejeitar de modo explicado; adapter municipal vira backlog próprio |
| Variação OFX por banco | Parser incompleto | Corpus por exportador, limites e quarentena |
| Crescimento para API/Open Finance/CNAB | Atraso geral | Manter explicitamente fora deste release |
| Volume bancário/pico desconhecido | SLO incompleto | Medir no G0 e testar mês inteiro com margem de dez vezes |

## 12. Primeiros dez dias úteis

1. nomear equipe e responsáveis;
2. aprovar DEC-011 e ADRs da stack;
3. criar repositório, proteção de branch, CI e ambientes;
4. criar scaffold do monólito modular e testes de arquitetura;
5. criar migrations iniciais de tenant, company, membership e CompanyAccess;
6. implementar ExecutionContext e primeiro comando autorizado;
7. criar auditoria atômica, idempotência e outbox mínimas;
8. provisionar storage de evidências e política de secrets;
9. catalogar fixtures e bundles XSD com hashes;
10. obter e validar layout, dataset, versão e golden files do Domínio;
11. demonstrar G0 e reestimar o restante com a equipe real.

## 13. Acompanhamento

- demonstração quinzenal por jornada funcional;
- relatório semanal de caminho crítico, decisões, defeitos e riscos;
- nenhuma porcentagem de conclusão sem evidência executável;
- reestimativa formal em G0, G3, G6 e antes do piloto;
- mudança de escopo altera a previsão por registro de decisão;
- feature flags liberam cada formato por empresa somente após seu gate.
