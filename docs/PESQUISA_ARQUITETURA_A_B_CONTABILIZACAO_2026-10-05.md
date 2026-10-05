# Pesquisa: Sistema A e Sistema B, separar ou unir; organização da contabilização; caminho do protótipo

**Data:** 04 e 05/10/2026.

**Pedido do proprietário (04/10/2026):** o Sistema B vai buscar no Sistema A as informações para contabilizar, organizadas em seis áreas:
1. caixa de entrada;
2. documentos (despesas, contratos, outros);
3. fiscal (NF-e, NFS-e, cupom fiscal, CT-e);
4. financeiro (OFX, PDF, CSV de extratos);
5. contábil (validação e aprovação, com correção de contas e histórico);
6. relatórios (diário, razão, balancetes, balanços, DRE).

Ele pediu ainda:
- conferir a legislação, o SPED Contábil, o SPED Fiscal e as normas contábeis;
- avaliar se o B fica à parte ou se agrupa ao A;
- chegar a um protótipo funcional o mais breve possível.

**Como foi feito:** rodadas de especialistas, conforme a [seção 7 do protocolo](colaboracao/README.md). As afirmações que sustentam decisão foram conferidas no código pelo Claude. Os resumos das rodadas estão na seção 11.
- **Rodada 1:** quatro especialistas em paralelo, somente leitura — arquitetura de software; legislação contábil e fiscal, com fontes oficiais; processo contábil de escritório; captura de documentos e integração.
- **Rodada 2:** revisão adversarial do consolidado. Ela corrigiu três pontos graves, já incorporados a este texto.

**O que este documento é:** pesquisa e recomendação. **Nada aqui está aprovado.** As decisões estão formalizadas na proposta de [ADR 0019](adr/0019-dois-runtimes-e-organizacao-da-contabilizacao.md), que só vale depois da aprovação do proprietário.

**Legenda das fontes:** [C] = confirmado em fonte oficial; [NC] = não confirmado; [Op] = opinião técnica, sem força normativa.

---

## 1. Resposta curta

1. **O B fica separado no código, no banco e na publicação. A união com o A acontece na experiência de uso** (opção O4, "um produto, dois runtimes"). Fundir os códigos agora, em qualquer direção, atrasa o protótipo em meses e destrói garantias que já funcionam.
2. **Toda inteligência fiscal ou contábil nova nasce no B.** O A continua dono do relacionamento com o cliente: portal, chamados, envio de arquivos, operação, honorários e publicações. As ferramentas fiscais que já existem no A recebem só correção e segurança.
3. **As seis áreas pedidas viram as seis áreas do B.** O menu do B já tem as cinco primeiras; falta "Relatórios".
4. **Só pode existir uma escrituração principal por empresa e período** (Manual da ECD, itens 1.7 e 1.9). Enquanto o Domínio for o livro oficial, o B emite **relatórios internos de conferência (prévias)**, nunca livros. **No piloto, as prévias não saem do escritório.** Tornar o B o sistema oficial (gerar a ECD) é outra decisão, para depois do piloto.
5. **O maior ganho prático depende da exportação ao Domínio.** Sem ela, a equipe faz o trabalho duas vezes: aprova no B e digita no Domínio. A exportação estava no MVP aprovado e está bloqueada à espera do leiaute oficial do Domínio (seção 5.3).
6. **Antes de dados reais:**
   - corrigir os defeitos da seção 3;
   - cumprir as seis condições formais de dados reais (seção 4), que hoje marcam `REAL DATA = NO_GO`.
7. **O protótipo começa sem integração.** O B funciona sozinho, com upload manual de documentos de duas empresas piloto. Depois vem o primeiro fluxo automático A→B, em que o B busca no A o XML da NF-e. Ele exigirá um ADR próprio.

---

## 2. Estado real do Sistema B (conferido no código em 04–05/10/2026)

### O que existe e funciona

- Tenant, empresa, CompanyAccess, auditoria append-only, idempotência, locks e Decimal.
- Ponte de login do A.
- Publicação interna em `contabilidade.serdial21.com`.
- **NF-e modelo 55 de entrada:** importação, itens, tributos, classificação por item, proposta balanceada (débito = crédito, [entities.py:57-68](../src/serdial21/modules/accounting/domain/entities.py#L57-L68)), aprovação por hash com segregação e bloqueio.
- **OFX:** importação, lista e detalhe, com deduplicação por hash, FITID e fingerprint.
- Catálogo versionado com plano de contas, regras e DE/PARA.

### O que falta ou é parcial

| Lacuna | Evidência |
|---|---|
| **Livro em tabelas.** O pré-lançamento só existe dentro do JSON das jornadas de NF-e; nenhuma das 16 migrations cria lançamento, período ou saldo | [journeys.py:19-48](../src/serdial21/modules/workflow/adapters/outbound/persistence/journeys.py#L19-L48); `alembic/versions/` |
| **Histórico** no lançamento | [entities.py:20-30](../src/serdial21/modules/accounting/domain/entities.py#L20-L30), sem campo |
| **Número** de lançamento | Só UUID; `revision_no` é versão |
| **Período contábil.** O período vem do mês escolhido no navegador | [work-context.js:11-19](../app/work-context.js#L11-L19); `AccountingPeriod` (COA-203) não implementado |
| **Saldo de abertura** | Não encontrado |
| **Regime tributário** da empresa | Ausente em `companies` e em `company_accounting_profiles` |
| **NF-e de saída** no modo por item; as intenções são todas de compra | [classification.py:13-19](../src/serdial21/modules/accounting/domain/classification.py#L13-L19) |
| **Tributos em linhas próprias.** ICMS-ST fica de fora; o grupo IBS/CBS só gera aviso | [nfe55_xml.py:458-495](../src/serdial21/modules/fiscal_documents/adapters/inbound/nfe55_xml.py#L458-L495) |
| NFC-e (recusada), CT-e, NFS-e | [nfe55_xml.py:125-130](../src/serdial21/modules/fiscal_documents/adapters/inbound/nfe55_xml.py#L125-L130) |
| **Upload genérico** (a tela avisa "ainda não disponível") | [app.js:338](../app/app.js#L338) |
| CSV bancário sem rota; OFX não gera proposta; conciliação sem gravação | ADR 0007; [operations.py:827-848](../src/serdial21/modules/operations/application/services/operations.py#L827-L848) |
| **Edição de conta e histórico** (a tela diz "adiada") | [app.js:606](../app/app.js#L606) |
| **Reprocessamento** de jornada parada em `PENDING_RULE` ou `ACCOUNT_MAPPING_REQUIRED`. `supersede` não tem rota e recusa jornada sem revisão | [nfe_to_dominio.py:329-336](../src/serdial21/modules/workflow/application/services/nfe_to_dominio.py#L329-L336) |
| Tela para cadastrar o catálogo. O catálogo exige pelo menos uma regra | [api-client.js:72](../app/api-client.js#L72); [catalog.py:95](../src/serdial21/entrypoints/http/routes/catalog.py#L95) |
| Relatórios | Inexistentes; fora do escopo aprovado do MVP ([14-backlog-tecnico-mvp.md:27](engenharia-produto/14-backlog-tecnico-mvp.md#L27)) |
| Exportação ao Domínio | Bloqueada até o leiaute oficial e o golden file ([LAYOUT_STATUS.md](specifications/dominio/LAYOUT_STATUS.md)) |

**Leitura:** a fundação de governança do B está pronta. A parte contábil ainda é, na prática, NF-e de entrada → proposta → aprovação. O protótipo pedido exige principalmente **completar o livro** e **ampliar as entradas**.

---

## 3. Defeitos e riscos encontrados

### 3.1 A mesma NF-e pode gerar duas propostas (grave)

**O defeito:**
- A tela gera uma `Idempotency-Key` aleatória a cada envio ([api-client.js:61](../app/api-client.js#L61)).
- Quando o importador devolve `IDEMPOTENT_REDELIVERY`, a preparação segue e cria outra jornada ([nfe_to_dominio.py:115-160](../src/serdial21/modules/workflow/application/services/nfe_to_dominio.py#L115-L160)).
- Não há trava na aprovação, na exportação, no lote nem no banco: `nfe_journey_checkpoints` não tem unicidade por documento.
- O teste [test_nfe_to_dominio_vertical.py:255-267](../tests/integration/test_nfe_to_dominio_vertical.py#L255-L267) aceita o comportamento.
- A tela do documento mostra só a jornada mais recente, então a duplicata fica escondida.
- Hoje não há efeito contábil, porque a exportação está bloqueada e não existe livro. O efeito passa a existir assim que houver prévia ou exportação.
- O OFX não tem esse defeito: deduplica as transações e não gera proposta.

**A correção não é trivial.** Reimportar com chave nova é hoje o único jeito de reprocessar uma jornada parada. Além disso, a chave de repetição inclui a validade da aprovação, que muda todo dia. Por isso a correção precisa de quatro partes:
1. separar a repetição da mesma requisição (que devolve o resultado anterior, com hash sem campos que mudam a cada dia) da unicidade do efeito;
2. criar uma **tabela de reserva por (tenant, empresa, documento fiscal)** com restrição de unicidade, liberada só por rejeição ou `supersede`;
3. criar um caso de uso e uma rota de **reprocessamento** para `PENDING_RULE` e `ACCOUNT_MAPPING_REQUIRED`, e uma rota para `supersede`;
4. escrever testes de concorrência e de repetição.

### 3.2 Correção de lançamento já aprovado

O domínio permite criar nova revisão a partir de uma aprovada ([entities.py:25-27](../src/serdial21/modules/accounting/domain/entities.py#L25-L27)). Num livro com lançamentos aprovados e numerados, isso contraria:
- o DL 486/1969, art. 2º, §2º: "Os erros cometidos serão corrigidos por meio de lançamentos de estorno" [C];
- a ITG 2000 (R1), itens 31 a 36 [C].

**Regra proposta:** edição livre só antes da aprovação. Depois da aprovação, apenas estorno, transferência ou complemento, como lançamento novo com número próprio e vínculo ao original.

### 3.3 O B pode ser embutido em página de outro site (clickjacking)

- `frame-ancestors 'none'` está só na tag `<meta>` ([index.html:8](../app/index.html#L8)), e o navegador ignora essa diretiva ali.
- O Caddy do `/app/` não envia o cabeçalho ([Caddyfile:18-23](../deploy/web/Caddyfile#L18-L23)), e o modelo versionado do proxy público (`deploy/host-caddy/Caddyfile.example`) também não. O proxy real não foi conferido.
- A API está protegida.
- Gravidade moderada: o token do B fica só em memória, e uma moldura começa sem sessão. A correção é barata. Já está na fila como item 6.

### 3.4 Data contábil e fuso

- O UTC afeta só as listagens por data de recebimento.
- A data contábil da NF-e vem de `dhEmi`, com o fuso do próprio XML.
- A data do OFX é gravada sem hora nem fuso ([ofx.py:172-180](../src/serdial21/modules/banking/adapters/inbound/ofx.py#L172-L180)); isso passa a importar quando o OFX gerar proposta.
- **Decisão contábil pendente:** a entrada é contabilizada na data de **emissão** ou na de **entrada**? A ITG 2000 fala em "data em que o fato contábil ocorreu" (item 6(a)) [C]. Se o Domínio usa a data de entrada, a comparação vai divergir entre meses. A decisão é do contador, não do sistema.

---

## 4. Condições formais para dados reais

O baseline de release marca **`REAL DATA = NO_GO`**, com seis condições ([PRODUCT_RELEASE_BASELINE.md](PRODUCT_RELEASE_BASELINE.md)):

| Condição | Quem assina |
|---|---|
| `AUTHORIZED_REAL_CORPUS` — quais empresas, quais competências, para qual finalidade | Proprietário |
| `ACCOUNTANT_SIGNOFF` — conteúdo, alçadas e quem aprova | Contador responsável |
| `LEGAL_APPROVAL` — escopo jurídico e de privacidade | Proprietário ou assessoria jurídica |
| `MIGRATION_0012_VERIFIED` — backup, upgrade e verificação do banco do piloto | Operação (proprietário, com runbook) |
| `PRE_DEPLOY_BACKUP` — backup recente, com hash e restauração validável | Operação |
| `PRIVACY_OPERATIONAL_APPROVAL` — procedimentos e cópias | Proprietário |

Somam-se:
- **backup do armazenamento de evidências**, declarado "bloqueador antes de dados reais" ([BACKUP_RECOVERY_STRATEGY.md](BACKUP_RECOVERY_STRATEGY.md));
- **decisão provisória de retenção:** a [matriz](DATA_RETENTION_MATRIX.md) está toda "A DEFINIR". Basta registrar "nada é eliminado durante o piloto; guarda mínima conforme CTN arts. 173, 174 e 195".

Essas condições não são burocracia: são o que permite usar documentos reais de clientes sem risco jurídico. Várias são decisões do próprio proprietário e podem ser registradas rapidamente.

---

## 5. Decisões de arquitetura e de autoridade

### 5.1 Separar ou unir A e B

| Critério (nota 1 a 5) | O1 contrato + Hub | O2 B dentro do A | O3 A dentro do B | **O4 híbrido** | O5 B sem tela própria |
|---|---|---|---|---|---|
| Tempo até o protótipo | 2 | 1 | 1 | **5** | 2 |
| Modelo comercial (A, A+B, B sozinho, revenda) | 4 | 1 | 4 | **4** | 2 |
| Segurança e isolamento | 4 | 1 | 3 | **4** | 2 |
| Integridade contábil e auditoria | 5 | 1 | 5 | **5** | 4 |
| Manutenção por uma pessoa + IA | 2 | 1 | 2→4 | **3** | 2 |
| Reversibilidade | 4 | 1 | 2 | **5** | 3 |
| Aderência ao AGENTS.md e aos ADRs | 5 | 1 | 3 | **4** | 3 |

**O que é cada opção:**
- **O1:** B separado, integrado pelo Connect Hub completo (rumo atual).
- **O2:** contabilidade reimplementada em Lovable, n8n e MySQL do A.
- **O3:** portal reescrito na pilha do B.
- **O4:** B separado no código, banco e publicação, com experiência unificada (login pela ponte, menu, links diretos), ingestão A→B por API e convergência gradual só se o A for vendido a terceiros.
- **O5:** tela contábil feita no Lovable, consumindo a API do B.

**Por que não fundir:**
- **O2:**
  - joga fora cerca de 19,8 mil linhas e 529 funções de teste, com invariantes que hoje são restrição de banco ou teste: FKs contra referência entre tenants, aprovação por hash com segregação, Decimal, versões imutáveis e auditoria;
  - põe a contabilidade onde a T-0007 já mostrou o limite: o parser precisou sair do n8n para ser testado;
  - o A é single-tenant, e isso acaba com o "B sozinho para outros escritórios".
- **O3:** reescreve um portal em produção (cerca de 164 arquivos TS/TSX, 60 workflows, Drive, e-mail, WhatsApp e o endurecimento das T-0003 a T-0008) antes de entregar qualquer coisa contábil.
- **O5:** põe o token que aprova proposta no navegador do A. Um XSS no A viraria aprovação contábil indevida.

**O que o O4 muda em relação ao O1:**
1. O primeiro fluxo é um *pull* simples pelo B, que dispensa outbox e fila de falhas no A, porque quem tenta de novo é o B.
2. A experiência é unificada.
3. Fica registrado que inteligência fiscal ou contábil nova não se constrói no A.

O O4 desvia do desenho de transporte do [CONNECT_HUB_ARCHITECTURE.md](integration/CONNECT_HUB_ARCHITECTURE.md), que previa HMAC por direção e evento do A com URL curta. O desvio será declarado no ADR do fluxo A→B, conforme o AGENTS.md §1.

**Complementos:**
- **A caixa de entrada existe nos dois sistemas, com papéis distintos.**
  - No A, é a caixa do relacionamento: o cliente envia e o escritório pede complemento (T-0008).
  - No B, é a triagem contábil: reúne o que pode virar evidência (arquivos do A, upload direto e conectores futuros).
  - O A é dono do arquivo; o B é dono do processamento.
- **O cliente não vê nada do B no protótipo.**
- **Parecer um só produto sem fundir:**
  - login do A;
  - item de menu para os funcionários cadastrados no B (hoje só administrador; muda no Lovable);
  - links diretos com `returnTo` validado e `state`/nonce na ponte (fila, item 6);
  - **sem iframe**.
- **Interface do B:** `app/app.js` tem 133 KB e linhas acima de 2 mil caracteres. Antes de acrescentar seis áreas e relatórios, é preciso decidir a organização da interface. A recomendação [Op] é dividi-la em módulos por área, sem framework e sem dependência nova; isso é compatível com a CSP estrita e com os testes estáticos atuais.

### 5.2 Quem é o livro oficial

**O que a legislação exige** (fontes na seção 10):

- **Quem escritura.** Toda sociedade empresária deve escriturar; só o MEI é dispensado (CC art. 1.179, §2º; LC 123 art. 68) [C].
- **Forma do Diário.** Ordem cronológica, individuação do documento, sem rasuras (CC arts. 1.183 e 1.184) [C].
- **Correção.** Erros corrigidos por estorno (DL 486/1969 art. 2º, §2º) [C].
- **Conteúdo do lançamento** (ITG 2000 (R1), itens 6 e 7) [C]:
  - data do fato;
  - contas devedora e credora;
  - **histórico**, ou código padronizado em tabela;
  - valor;
  - identificação unívoca;
  - **número sequencial ligado ao documento de origem**.
- **Retificação.** Por estorno, transferência ou complementação, com motivo e referência ao lançamento original (ITG itens 31–36) [C].
- **Responsabilidade.** "A escrituração contábil e a emissão de relatórios, peças, análises, demonstrativos e demonstrações contábeis são de atribuição e de responsabilidade exclusivas do profissional da contabilidade legalmente habilitado" (ITG 2000, item 12) [C]. **Isso vale também para uma prévia.**
- **Uma só escrituração principal por período.** "As escriturações principais (G, R ou B) não podem coexistir" e "não podem existir, ao mesmo tempo, dois livros diários em relação ao mesmo período" (Manual da ECD, leiaute 9, jan/2026, itens 1.7 e 1.9) [C].
  - Daí se infere [Op] que só um sistema pode gerar o livro oficial de cada empresa e período.
  - O portal SPED registra uma atualização do manual em maio/2026, que não foi conferida [NC].
- **ECD (IN RFB 2.003/2021, art. 3º)** [C]:
  - obrigadas: todas as PJ com escrituração comercial;
  - dispensados: Simples Nacional e Lucro Presumido com livro-caixa;
  - a dispensa cai com aporte de investidor-anjo (§2º) e, no Presumido, ao distribuir lucro acima da presunção (§3º);
  - entrega até o último dia útil de junho;
  - assinatura ICP-Brasil do contador e de um responsável;
  - autenticação pelo recibo do SPED (Decreto 1.800/1996, art. 78-A).
- **Simples Nacional e Presumido.** Distribuir lucro acima da presunção sem tributação exige escrituração contábil que demonstre esse lucro:
  - Simples: LC 123 art. 14, §§1º e 2º [C, fonte secundária];
  - Presumido: IN 1.700/2017 art. 238, via Perguntas e Respostas PJ 2025 da RFB [C, indireto].
  - Desde jan/2026, há IRRF de 10% sobre lucros acima de R$ 50 mil por mês, da mesma PJ para a mesma pessoa física (Lei 15.270/2025) [C].
- **Pequenas empresas.** A ITG 1000 foi revogada. Para exercícios a partir de 2023 valem a NBC TG 1001 (pequenas) e a NBC TG 1002 (microentidades, até R$ 4,8 milhões) [C, notícia do CFC]. O conteúdo mínimo das demonstrações na NBC TG 1002 não foi conferido [NC].
- **Apresentação.** A NBC TG 26 (R5) foi revogada pela NBC TG 51 (IFRS 18), aprovada em 13/11/2025 [C]. A vigência provável é 2027 [NC].

**Opções:**

- **R1 — o Domínio continua oficial, e o B emite só relatórios internos de conferência.**
- **R2 — o B vira o sistema oficial de escrituração da empresa a partir de uma data de corte.**
  - Exige cumprir integralmente CC, DL 486, ITG 2000 e CTG 2001.
  - Exige gerar a ECD no leiaute 9, validável no PGE, com:
    - saldos coerentes com o último arquivo do Domínio;
    - encerramento do exercício;
    - plano de contas com no mínimo 4 níveis;
    - mapeamento referencial para a ECF;
    - termos de abertura e encerramento e assinaturas.
  - Riscos: multas da Lei 8.218, art. 12; arbitramento no lucro real (RIR art. 274); perda da distribuição isenta; responsabilidade do contador.
- **R3 — R1 agora, com o livro do B construído nos requisitos da ITG 2000.**
  - O livro segue desde já: número na aprovação, histórico obrigatório, data do fato, vínculo ao documento, período e correção por estorno depois da aprovação.
  - A decisão sobre R2 fica para depois do piloto.

**Recomendação: R3, com três regras:**
1. **No piloto, as prévias são internas:** é proibido entregá-las a clientes ou terceiros. Um BP ou DRE parcial usado para crédito ou distribuição de lucros divergiria do livro oficial, e nenhum rótulo resolve isso. A entrega a clientes exige decisão própria.
2. **Toda prévia é emitida por contador identificado** (ITG item 12) e leva:
   - o título "Prévia gerencial — não constitui escrituração contábil oficial";
   - a data de corte;
   - a base ("lançamentos aprovados internamente até…");
   - a fonte do saldo de abertura;
   - as pendências que ficaram de fora.
   
   As prévias não têm termos, assinatura nem arquivo em formato SPED.
3. **R3 reduz o retrabalho de uma eventual R2, mas não o elimina:** a ECD, o mapeamento referencial, o encerramento, os termos e as assinaturas continuam por fazer.

Relatórios no B estão fora do escopo aprovado do MVP. Incluí-los exige a aprovação do ADR 0019 (AGENTS.md §1).

### 5.3 Exportação ao Domínio: o ganho prático que está faltando

O MVP aprovado previa "exportar por layout genérico e primeiro conector estratégico" (backlog, resultado 9; S6; INT-909). O conector está pronto em estrutura, mas **bloqueado até o leiaute oficial e o golden file do Domínio**.

Enquanto o Domínio for o livro oficial e a exportação não existir:
- **a equipe faz o trabalho duas vezes**: aprova no B e lança no Domínio;
- a comparação com o Domínio é manual.

Com a exportação, o B passa a alimentar o Domínio, os relatórios oficiais continuam saindo do Domínio e a comparação fica automática.

**Recomendação:** pedir agora, ao suporte do Domínio, a documentação oficial de importação de lançamentos (leiaute com separador, registros 6000/6100) e gerar um arquivo-exemplo validado (golden file). Enquanto isso não chega, o piloto aceita o trabalho em dobro, limitado a poucas empresas e competências.

**Risco de produto [Op]:** o Domínio já importa XML de NF-e de entrada, então o primeiro teste escolhe o fluxo em que o B acrescenta menos. O valor do B está:
- na classificação por item com regras e histórico aprovado;
- na trilha de aprovação;
- no financeiro, onde há mais trabalho manual.

Por isso o financeiro vem logo em seguida (seção 8).

---

## 6. As seis áreas no B

| Área | Papel | Já existe | Falta |
|---|---|---|---|
| **1. Caixa de entrada** | Triagem: todo arquivo vira evidência imutável (hash, deduplicação, quarentena), classificada por empresa, competência, tipo e área | Evidência, deduplicação por hash, lista `/documents` | Upload genérico de vários arquivos (XML, OFX, CSV, PDF, JPG, PNG; tipo pela assinatura do arquivo); estados; encaminhamento; separar "importar" de "preparar proposta" |
| **2. Documentos** | Recibos, boletos, guias, folha, contratos: lançamento manual com o PDF como evidência (depois, IA extrai e a pessoa confere) | Metadados de documento | Lançamento manual com evidência; históricos padrão; contratos com cronograma |
| **3. Fiscal** | NF-e, NFC-e, CT-e, NFS-e → dados canônicos → proposta por regra | NF-e 55 de entrada | Em ordem: NF-e de saída; tributos em linhas e por regime; NFC-e; NFS-e nacional; CT-e. CF-e SAT só para períodos até 2025 (seção 7) |
| **4. Financeiro** | OFX e CSV → transações → proposta e conciliação; PDF depois | Importação de OFX | Proposta por transação via DE/PARA; importador CSV; transferências entre contas próprias; sugestão de conciliação |
| **5. Contábil** | Conferência por empresa e competência; corrigir conta e histórico **antes da aprovação** (nova revisão); depois da aprovação, só estorno ou complemento | Lista, detalhe, aprovar e rejeitar com hash e segregação; decisão por item | Livro em tabelas; edição; motivo de rejeição; lote; pendências e reprocessamento; lançamento manual |
| **6. Relatórios (prévia interna)** | Diário, Razão, Balancete, BP e DRE a partir de saldo de abertura importado mais lançamentos aprovados | — | Período; saldos de abertura; grupos de demonstração; fechamento interno; telas |

**Mudanças no modelo de dados**, todas por migration aditiva:
- lançamento, revisão, linha e vínculo com a origem em **tabelas** (ACC-601/602), com número na aprovação, histórico, data do fato, contraparte e motivo;
- reserva por documento (seção 3.1);
- `accounting_periods` (COA-203);
- históricos padrão versionados;
- saldos de abertura com fonte e hash, nunca como lançamento;
- grupos de demonstração e vínculo com o plano referencial;
- regime tributário da empresa, com vigência.

Uma migração do conteúdo das jornadas existentes para as tabelas precisa preservar os hashes de revisão já emitidos.

**Plano de contas e saldos de clientes existentes:**
- plano de contas pela exportação do Domínio;
- saldos pelo balancete do Domínio na data de corte (o último mês fechado);
- ECD do ano anterior como conferência, quando existir (o Simples é dispensado).

Isso exige amostras reais dos arquivos para definir o leiaute. Exige também decidir qual código identifica a conta (código reduzido ou classificação).

**Cobertura e comparação:** os balancetes do B e do Domínio só batem se o B cobrir todos os fluxos da empresa. Folha, impostos, depreciação e provisões não estão em nenhuma onda inicial. A comparação deve ser **restrita às contas cobertas** (fornecedores, despesas, bancos) até a cobertura crescer. A escolha das empresas piloto deve considerar essa cobertura.

---

## 7. Entrada de documentos e o primeiro fluxo A→B

| Tipo | Formato | Leitura | Quando |
|---|---|---|---|
| NF-e 55 de entrada e saída | XML (MOC 7.0; NT 2025.002-RTC v1.52) [C] | Determinística | Protótipo |
| Extrato OFX | OFX 1.x/2.x | Determinística | Protótipo |
| Extrato CSV | Sem padrão; layout versionado por banco | Determinística | Logo após |
| NFC-e 65 | XML | Determinística | Logo após |
| NFS-e nacional | XML (XSD v1.01; ADN) [C] | Determinística | Depois |
| CT-e 57 | XML (MOC 4.0) [C] | Determinística | Depois |
| Boleto e guias (DARF, DAS, GNRE) | Código de barras Febraban | Determinística | Depois |
| Extrato PDF, cupom em foto, recibo, contrato | Sem padrão | IA + controle determinístico + conferência humana | Depois, com ADR |

**CF-e SAT e MF-e** [C]: emissão vedada desde 01/01/2026 em SP (Portaria SRE 79/2024, art. 34-D) e no CE (Decreto 36.417/2025, art. 76-A). Interessam só para períodos até 2025.

**IBS/CBS** [C] (Ato Conjunto RFB/CGIBS 4/2026):
- datas de obrigatoriedade:
  - NF-e, NFC-e e CT-e: 03/08/2026;
  - NFS-e: 01/10/2026 na regra geral, e 01/12/2026 para alguns serviços;
  - Simples Nacional: 2027.
- O Ato Técnico Conjunto 1/2026 suspende até 31/12/2026 a rejeição de notas sem o grupo IBS/CBS [C, fonte secundária]. Por isso, **NF-e de 2026 podem vir com ou sem o grupo**, e o B precisa ler as duas formas.
- O **tratamento contábil de IBS/CBS não tem orientação CFC/CPC localizada** [NC]: é pendência para decisão do contador, não regra a inventar.
- A EFD ICMS/IPI não apura CBS, IBS nem IS (Guia Prático 3.2.3, seção 10) [C].

**Sequência:**

1. **Manual no B.** A equipe baixa do Drive e sobe no B, depois de corrigida a duplicidade.

2. **Primeiro fluxo automático:** o B busca no A o XML da NF-e (*pull*), acionado por um botão "Buscar no Sistema A". **Exige ADR próprio** como segunda exceção nomeada ao gate do Connect Hub (no molde do ADR 0014).

   **Endpoints:** o A expõe dois endpoints somente leitura e versionados: a lista, com cursor; e o download em stream, **só pelo id opaco do A**, nunca pelo id do arquivo no Drive.

   **Filtro imposto pelo A:**
   - só `01_FISCAL`;
   - só `.xml`;
   - só cliente mapeado e ativo;
   - limite de requisições;
   - registro de cada download.

   **Token do B:**
   - assinado com **chave assimétrica**, publicada no JWKS do B — a ponte do ADR 0014 ao contrário; o A não guarda segredo nem chave privada do B;
   - vida curta, até 60 s;
   - `aud` igual ao endpoint;
   - `jti` de uso único;
   - vínculo com a operação e com o cliente;
   - ator do B registrado na auditoria;
   - algoritmo fixo;
   - transporte só no cabeçalho.

   **Onde verificar o token:** numa **Edge Function** (Deno, Web Crypto), com o n8n atrás dela por Header Auth interno e **sem gravação de execuções**. O nó JWT do n8n não serve:
   - não lê JWKS;
   - a credencial PEM pede chave privada;
   - a credencial aceita o algoritmo `none`.

   **Do lado do B:**
   - confere hash e tamanho;
   - resolve a empresa pela referência externa;
   - grava evidência e auditoria com origem `INTEGRATION`;
   - segue para o importador.

   Chave de idempotência: `SERDIAL21_OPERATIONAL:DOCUMENT:<id>:v<n>` + sha256.

   **Lacunas que o ADR do fluxo precisa resolver:**
   - a preparação fixa a origem `HUMAN` e exige período e validade da aprovação, e o fluxo automático precisa definir quem informa isso;
   - os critérios concretos de homologação: endpoints de teste, pasta de teste no Drive, cliente de teste, credencial de homologação, testes de contrato no CI do B e testes negativos;
   - o limite de tamanho do stream nas Edge Functions [NC].

   **O B não lê o Google Drive diretamente:** o escopo seria amplo demais, alcançaria inclusive `02_PESSOAL`, e o núcleo do B ficaria acoplado ao Drive.

3. **Depois:** outros tipos, agendamento e status devolvido ao portal.

**Certificado digital** (fila, item 21):
- O certificado do escritório **com procuração não serve** para baixar NF-e, CT-e e NFS-e. Os serviços autenticam pelo **CNPJ base ou raiz** do próprio contribuinte (NT 2014.002 v1.40; Manual das APIs do ADN v1.0) [C].
- **`autXML`:** se o cliente puser o CNPJ do escritório no campo `autXML`, o escritório baixa as notas **emitidas pelo cliente** com o próprio certificado. Isso **não cobre as notas de entrada**, porque nelas quem preenche o campo é o fornecedor.
- **Notas de entrada:** exigem o envio pelo cliente ou o certificado do cliente.
- **Guardar o A1 do cliente:** a chave privada é de "exclusivo controle" do titular (MP 2.200-2/2001, art. 6º) [C]. Só com ADR, termo do cliente, cofre de chaves externo (o VPS não tem) e um processo isolado de uso.
- **Guias e tributos federais:** Integra Contador (SERPRO), com procuração e-CAC.

**IA na captura:**
- só para documentos sem padrão;
- saída estruturada e versionada, com o trecho e a página de origem de cada campo;
- validação determinística (somas, saldo inicial + movimentos = saldo final, dígitos verificadores);
- marcação "extraído por IA" e conferência humana obrigatória;
- uma chamada por documento, sem ferramentas;
- o B ainda não tem a finalidade `EXTRACT` nem adaptador de provedor: exige ADR.

**EFD e ECD como fonte:**
- servem para **conferência** (Presumido e Real) e **onboarding**, não como entrada principal;
- o Simples é dispensado da ECD e da EFD-Contribuições;
- na NF-e emitida pelo próprio contribuinte, a EFD não traz itens;
- o arquivo é mensal e entregue com atraso.

---

## 8. Caminho do protótipo

As durações são ordem de grandeza: dependem do ritmo do Codex e das ações manuais do proprietário. Até aqui, tarefas do mesmo porte levaram de horas a dois dias; o risco maior está nas decisões e nos insumos (regras, DE/PARA, arquivos do Domínio), não no código.

| Onda | Entrega | O que dá para testar | Ação do proprietário |
|---|---|---|---|
| **0 — fundação segura** (≈2–3 semanas) | ADR 0019 aprovado; condições de dados reais (seção 4); backup do banco e das evidências do piloto; retenção provisória; reserva por documento + reprocessamento + rota de `supersede`; restrição da correção depois da aprovação; cabeçalhos anti-iframe; organização da interface do B; cadastro das empresas piloto e dos usuários (aprovador ≠ quem importa); importador do plano de contas do Domínio; catálogo publicado com as regras e o DE/PARA do contador | **Primeiro contato com dados reais:** NF-e de entrada → proposta → aprovar ou rejeitar, no fluxo que já existe | Escolher as empresas; assinar as condições; enviar os arquivos do Domínio (plano e balancete) como **arquivo**, sem colar dados no chat; definir as regras com o contador; pedir o leiaute de importação ao suporte do Domínio |
| **1 — corte mínimo de conferência** (≈3–5 semanas) | Edição de conta e histórico antes da aprovação; livro em tabelas com número, histórico e data do fato; motivo de rejeição; **Diário e Razão internos em tela** (sem PDF) | **Primeiro teste útil:** NF-e reais → proposta → correção → aprovação → Diário e Razão | Usar com a equipe e registrar dúvidas e erros |
| **2 — financeiro e documentos** (≈2–3 semanas) | OFX e CSV → proposta por transação; transferências; sugestão de conciliação; caixa de entrada genérica; lançamento manual com evidência | Banco e despesas sem nota fiscal | Extratos OFX ou CSV das empresas piloto |
| **3 — exportação ou prévia completa** (≈2–3 semanas) | Se o leiaute do Domínio chegou: **exportação** (acaba o trabalho em dobro). Senão, ou em seguida: saldos de abertura; prévia interna de Balancete, BP e DRE; fechamento interno da competência; comparação com o Domínio nas contas cobertas | Comparação objetiva com o livro oficial | Conferir divergências |
| **4 — A→B** (≈2 semanas) | Pull da NF-e (ADR próprio e homologação) | Documentos do portal chegam ao B sem download manual | Publicar os endpoints e a Edge Function conforme o runbook |
| **5 — cobertura** | NF-e de saída e tributos por regime; NFC-e; NFS-e nacional; CT-e; menu do A para não administradores | Empresas de serviço e comércio completas | — |
| **6 — depois** | IA para PDF e foto; EFD para conferência; decisão sobre R2 | — | — |

**A ordem de 2 a 5 pode mudar** conforme o teste prático. A integração (onda 4) pode vir antes se o envio manual pesar demais.

**Continua em paralelo no A:**
- **T-0008:** já aprovada; não conflita.
- **Itens de segurança da fila:** 7 (login legado), 18 e 25.
- **Item 23 (apuração de ICMS por IA):** passa a ser futuro do B, se o ADR 0019 for aprovado.
- **Itens 22 e 24:** só correção; ficam no A.

---

## 9. Decisões que cabem ao proprietário

### Para começar (onda 0)

1. **Arquitetura O4:** B separado, experiência unificada. **Recomendado: sim.**
2. **Inteligência fiscal ou contábil nova só no B**; ferramentas do A só com correção. **Recomendado: sim.**
3. **R3:** Domínio oficial; prévias internas, emitidas por contador e nunca entregues a clientes no piloto; livro do B nos requisitos da ITG 2000; decisão sobre R2 depois do piloto. **Recomendado: sim.**
4. **Ordem do protótipo:** B sozinho com upload manual primeiro; integração na onda 4. **Recomendado: sim.**
5. **Condições de dados reais** (seção 4): quem assina cada uma, e a retenção provisória "nada é eliminado no piloto". **Recomendado: registrar já.**
6. **Empresas piloto:** duas, escolhidas pela cobertura, com uma competência já fechada no Domínio. Quais?
7. **Quem aprova no piloto.** A segregação (quem importa não aprova) exige **duas pessoas** com acesso ao B. Quem são?
8. **Exportação ao Domínio:** pedir o leiaute oficial de importação de lançamentos ao suporte do Domínio. **Recomendado: sim, já.**

### Técnicas (o Claude recomenda; o proprietário só confirma)

9. Um lançamento por documento, com linhas agregadas por conta.
10. Número atribuído na aprovação, por empresa e exercício.
11. Edição só antes da aprovação; depois, estorno ou complemento.
12. Interface do B dividida em módulos por área, sem framework.
13. Identidade da conta importada do Domínio: código reduzido ou classificação (decidir com a amostra).

### Do contador

14. **Data contábil da NF-e de entrada:** emissão ou entrada?
15. **Tratamento contábil de IBS/CBS em 2026–2027:** sem orientação oficial localizada; decidir antes de ativar regras.

### Para depois

16. Guarda do certificado do cliente: não agora. Caminho futuro: `autXML` para as notas emitidas e ADR próprio para as de entrada.
17. B como livro oficial (R2): depois do piloto, com critério de comparação.
18. IA de extração: com ADR.

---

## 10. Base normativa

| Requisito | Fonte | Implicação no B | Prévia | Oficial |
|---|---|---|---|---|
| Correção por estorno, transferência ou complementação | DL 486/1969 art. 2º §2º; ITG 2000 (R1) itens 31–36 [C] | Edição só antes da aprovação; depois, lançamento novo vinculado ao original | Recomendado | Obrigatório |
| Data do fato × data do registro (lançamento extemporâneo) | ITG itens 6(a) e 36; ECD DT_LCTO_EXT [C] | Dois campos de data | Recomendado | Obrigatório |
| Ordem cronológica e número sequencial | CC arts. 1.183–1.184; ITG itens 5 e 7 [C] | Número por empresa e exercício, na aprovação | Recomendado | Obrigatório |
| Histórico ou código padronizado | ITG itens 6, 8 e 11 [C] | Histórico obrigatório; tabela versionada | Obrigatório | Obrigatório |
| Vínculo ao documento | CC art. 1.184; Dec. 64.567/1969 art. 2º; RIR/2018 art. 273; ITG itens 7 e 14 [C] | Lançamento aponta para a evidência e seu hash | Obrigatório | Obrigatório |
| Plano com ≥ 4 níveis, natureza estável, mapeamento referencial | CTG 2001 (R3), via Manual da ECD; registros I050/I051 [C] | Plano versionado; mapeamento referencial versionado | Recomendado | Obrigatório |
| Saldos iniciais coerentes | Manual da ECD [C] | Abertura importada e conciliada | Obrigatório | Obrigatório |
| Encerramento e apuração do resultado | CC art. 1.179; Lei 6.404 arts. 176 e 187; ECD I350/I355 [C] | Lançamentos de encerramento identificados; bloqueio do período | Recomendado | Obrigatório |
| BP e DRE; DFC se PL ≥ R$ 2 milhões | Lei 6.404 arts. 176 §6º, 178 e 187 [C]; NBC TG 1002 [conteúdo NC] | Estrutura de aglutinação versionada | Recomendado | Obrigatório |
| Termos, assinatura e autenticação | Dec. 64.567 arts. 6º–7º; ITG itens 9–10; Dec. 1.800/1996 art. 78-A [C] | Só no livro oficial | **Proibido simular** | Obrigatório |
| Uma só escrituração principal por período | Manual da ECD, itens 1.7 e 1.9 [C]; aplicação a dois sistemas [Op] | B e Domínio não podem ser oficiais ao mesmo tempo | — | Obrigatório |
| Responsabilidade de profissional habilitado | ITG item 12; DL 9.295/1946 arts. 12 e 25 [C] | Emissão e aprovação por contador identificado; IA nunca aprova | Obrigatório | Obrigatório |
| Guarda | CTN arts. 173, 174 e 195 p.ú.; CC art. 1.194; Ajuste SINIEF 2/09 cl. 7ª [C] | Nada eliminado até a prescrição; matriz de retenção | Obrigatório | Obrigatório |
| Digitalização com valor legal | Lei 12.682 art. 2º-A; Dec. 10.278/2020 [C] | Só para descartar o papel; ICP-Brasil e metadados | Recomendado | Se descartar o original |
| Aquisição de NF-e | NT 2014.002 v1.40 [C] | CNPJ base; 90 dias; manifestação; `autXML` | Operacional | Operacional |
| IBS/CBS nos documentos | LC 214/2025 arts. 343, 346 e 348; LC 227/2026; Ato Conjunto RFB/CGIBS 4/2026 [C] | Ler notas com e sem o grupo; tratamento contábil é decisão do contador | Obrigatório | Obrigatório |
| NFS-e nacional ou compartilhamento com o ADN desde 01/01/2026 | LC 214/2025 art. 62 §1º [C, fonte secundária na revisão] | NFS-e em XML nacional como formato-alvo | — | — |
| Dados pessoais | Lei 13.709/2018 arts. 7º, 16, 37, 39 e 46 [C] | Base legal por finalidade; registro de operações; contrato operador/controlador | Obrigatório | Obrigatório |

**Não confirmado [NC]:**
- conteúdo da IN 2.142/2023 e da atualização de maio/2026 do Manual da ECD;
- ato de revogação da ITG 1000;
- conteúdo mínimo da NBC TG 1002;
- vigência da NBC TG 51;
- início do *split payment*;
- distribuição automática de NFC-e e de CT-e;
- exigência de ICP-Brasil no ADN;
- limite de stream das Edge Functions;
- verificação de JWT só com chave pública no n8n.

### Fontes (acessadas em 04 e 05/10/2026)

**Legislação federal (Planalto e Câmara):**
- Código Civil: https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm
- DL 486/1969: https://www.planalto.gov.br/ccivil_03/decreto-lei/del0486.htm
- Decreto 64.567/1969: https://www2.camara.leg.br/legin/fed/decret/1960-1969/decreto-64567-22-maio-1969-405971-publicacaooriginal-1-pe.html
- Lei 6.404/1976: https://www.planalto.gov.br/ccivil_03/leis/l6404consol.htm
- RIR/2018: https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/decreto/d9580.htm
- LC 123/2006: https://www.planalto.gov.br/ccivil_03/leis/lcp/lcp123.htm
- Lei 15.270/2025: https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2025/lei/l15270.htm
- DL 9.295/1946: https://www.planalto.gov.br/ccivil_03/decreto-lei/del9295.htm
- Decreto 1.800/1996: https://www.planalto.gov.br/ccivil_03/decreto/d1800.htm
- CTN: https://www.planalto.gov.br/ccivil_03/leis/l5172compilado.htm
- Lei 12.682/2012 e Decreto 10.278/2020: https://www.planalto.gov.br/ccivil_03/_ato2011-2014/2012/lei/l12682.htm ; https://www.planalto.gov.br/ccivil_03/_ato2019-2022/2020/decreto/d10278.htm
- MP 2.200-2/2001 e Lei 14.063/2020: https://www.planalto.gov.br/ccivil_03/mpv/antigas_2001/2200-2.htm ; https://www.planalto.gov.br/ccivil_03/_ato2019-2022/2020/lei/l14063.htm
- LGPD: https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709compilado.htm

**Normas do CFC:**
- ITG 2000 (R1): https://www1.cfc.org.br/sisweb/SRE/docs/ITG2000(R1).pdf
- Normas e notícias: https://cfc.org.br/tecnica/normas-brasileiras-de-contabilidade/normas-completas/ ; https://cfc.org.br/noticias/contador-conheca-as-normas-de-contabilidade-voltadas-para-as-micro-e-pequenas-empresas/ ; https://cfc.org.br/noticias/nbc-tg-51-e-publicada-no-diario-oficial-da-uniao/

**SPED:**
- Manual da ECD, leiaute 9 (jan/2026): https://www.gov.br/sped/pt-br/assuntos/escrituracoes-digitais/ecd/manuais-e-documentos-tecnicos/manual_de_orientacao_da_ecd_leiaute_9_janeiro_2026.pdf
- Manual da ECF, leiaute 12: https://www.gov.br/sped/pt-br/assuntos/escrituracoes-digitais/ecf/manuais-e-documentos-tecnicos/manual_ecf_leiaute_12_20_05_2026_ac_2025_sit_esp_2026.pdf
- Guia Prático EFD ICMS/IPI 3.2.3: https://www.gov.br/sped/pt-br/assuntos/escrituracoes-digitais/efd-icms-ipi/manuais-e-documentos-tecnicos/guia-pratico-efd-versao-3-2-3.pdf
- Guia Prático EFD-Contribuições 1.35: https://www.gov.br/sped/pt-br/assuntos/escrituracoes-digitais/efd-contribuicoes/manuais/guia_pratico_efd_contribuicoes_versao_1_35-18_06_2021.pdf
- Perguntas e Respostas PJ 2025 (RFB): https://www.gov.br/receitafederal/pt-br/centrais-de-conteudo/publicacoes/perguntas-e-respostas/ecf/perguntas-e-respostas-da-pessoa-juridica-2025.pdf

**Documentos fiscais eletrônicos:**
- Portal da NF-e (notas técnicas; NT 2014.002): https://www.nfe.fazenda.gov.br/portal/listaConteudo.aspx?tipoConteudo=04BIflQt1aY= ; https://www.nfe.fazenda.gov.br/portal/exibirArquivo.aspx?conteudo=uWO2d/gTuWg=
- Portal do CT-e: https://www.cte.fazenda.gov.br/portal/listaConteudo.aspx?tipoConteudo=YIi+H8VETH0=
- NFS-e nacional e Manual das APIs do ADN: https://www.gov.br/nfse/pt-br/biblioteca/documentacao-tecnica/documentacao-atual ; https://www.gov.br/nfse/pt-br/biblioteca/documentacao-tecnica/documentacao-atual/manual-contribuintes-apis-adn-sistema-nacional-nfse.pdf

**Reforma tributária:**
- LC 214/2025 e LC 227/2026: https://www.planalto.gov.br/ccivil_03/leis/lcp/lcp214.htm ; https://www.planalto.gov.br/ccivil_03/leis/lcp/lcp227.htm
- Ato Conjunto RFB/CGIBS 4/2026: https://www.cgibs.gov.br/upload/arquivos/202607/31091735-20260730-16h30-ato-conjunto-rfb-cgibs-na-c2-ba-4-260731-090909.pdf

**Legislação estadual:**
- Ajuste SINIEF 2/2009: https://www.confaz.fazenda.gov.br/legislacao/ajustes/2009/aj_002_09
- Portaria SRE 79/2024 (SP): https://legislacao.fazenda.sp.gov.br/Paginas/Portaria-SRE-79-de-2024.aspx
- Decreto 36.417/2025 (CE): https://sefazlegis.sefaz.ce.gov.br/api/openFile?id=8ede79ea-72c0-44bd-aeee-9a7d0d5b9428

**Bancos:**
- Resolução Conjunta 1/2020 (Open Finance): https://normativos.bcb.gov.br/Lists/Normativos/Attachments/51028/Res_Conj_0001_v7_L.pdf
- CNAB 240 Febraban v10.11: https://cmsarquivos.febraban.org.br/Arquivos/documentos/PDF/Layout%20padrao%20CNAB240%20V%2010%2011%20-%2021_08_2023.pdf

---

## 11. Resumo das rodadas

**Rodada 1 — arquitetura.**
- Recomendou O4 e o *pull* da NF-e como primeiro fluxo.
- Achou o clickjacking.
- Mostrou que a ponte descarta a rota pedida, o que impede links diretos.

**Rodada 1 — legislação.**
- Levantou a base normativa da seção 10, com fontes oficiais.
- Conclusões centrais:
  - só uma escrituração principal por período;
  - mesmo prévias são responsabilidade de contador;
  - gerar ECD significa assumir o livro oficial.

**Rodada 1 — processo contábil.**
- Desenhou o fluxo documento → triagem → proposta → conferência → livro → conciliação → fechamento → prévia.
- Descreveu a lógica típica por fonte em termos de intenções contábeis, sem inventar contas.
- Encontrou a ausência do livro em tabelas e a duplicidade de proposta.

**Rodada 1 — captura e integração.**
- Montou a matriz de captura por tipo de documento.
- Corrigiu a premissa sobre criptografia no n8n.
- Mostrou que a procuração não serve para a distribuição de documentos fiscais e que o `autXML` é a alternativa.

**Rodada 2 — revisão adversarial.** Corrigiu:
1. a correção proposta para a duplicidade quebraria o único reprocessamento existente;
2. o plano ignorava as seis condições de dados reais e o backup das evidências;
3. a exportação ao Domínio havia sumido sem ser dita;
4. o critério de comparação era inalcançável sem cobertura total;
5. a prévia só é segura se for interna;
6. havia contradição no modelo de correção depois da aprovação;
7. o contrato A→B tinha falhas: o nó JWT do n8n, `jti`/`aud`, a gravação de execuções e o desvio do Connect Hub não declarado;
8. o `autXML` não cobre as notas de entrada;
9. a data contábil da entrada é decisão do contador;
10. as ondas estavam subestimadas.

A revisão também corrigiu duas citações: o item do Manual da ECD (1.7 e 1.9) e o alcance do art. 3º da IN 2.003 (investidor-anjo).
