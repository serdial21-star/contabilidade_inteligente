# T-0007 — Apuração ICMS a partir de PDF com texto, com conferência obrigatória

| Campo | Valor |
|---|---|
| Estado | CONCLUÍDA — publicada em 04/10/2026 |
| Origem | QUADRO, fila item 23 (primeira etapa); pedido do usuário em 04/10/2026 |
| Sistema | Sistema A (workflow n8n `ferramentas-ia/apuracao-icms`, artefato versionado) |
| Exige ADR | não — decisões registradas aqui |
| Exige ação do usuário | sim — importar o workflow e testar com os arquivos reais |

---

## 1. Briefing (Claude)

### [2026-10-04] Claude — Briefing para o Codex

**Contexto.** A ferramenta "Análise de Apuração de ICMS e CMV" do painel envia um arquivo ao workflow `ferramentas-ia/apuracao-icms` (versão endurecida da T-0006: `docs/integration/system_a_webhook_hardening/n8n_ferramentas_ia_apuracao_icms_v9_hardened.json`). O nó "1. Extrator e Consolidador" lê **apenas CSV**; com PDF falha ("Nenhum dado valido foi consolidado"). O produto será comercializado: os relatórios virão de sistemas diferentes, todos derivados do mesmo livro oficial, e alguns sistemas exportam só PDF.

**Amostra analisada pelo Claude** (mesmo relatório, competência 01/2026, enviada pelo usuário em CSV e PDF; **não versionar** — usar apenas como referência de estrutura):
- Blocos: "ENTRADAS mm/aaaa" (CFOP | Vr. Contábil | Base de Cálculo | Imposto Creditado | Isentas/Não Tribut. | Outras), subtotais "1.00 do Estado", "2.00 de O. Estados", "3.00 do Exterior", "Total"; "SAÍDAS mm/aaaa" idem com "Imposto Debitado" e subtotais 5.00/6.00/7.00; "Resumo Apuração - ICMS mm/aaaa" com linhas 001–014 e as deduções detalhadas em 012.
- O texto extraído do PDF vem **fora de ordem** (títulos depois dos dados; cabeçalhos de entradas e saídas misturados). Cada linha de dados, porém, é autossuficiente: CFOP de 4 dígitos + 5 valores; o primeiro dígito do CFOP define o bloco (1/2/3 entradas; 5/6/7 saídas); o resumo usa códigos 001–014.
- **Não há identidade por linha** a exigir: na amostra, CFOP 5101 tem "Outras" maior que o valor contábil, e 1908 repete o valor em duas colunas. Conferência só por somas (abaixo).

**Referências normativas** (citar no artefato com versão e data de acesso):
- Livro Registro de Apuração do ICMS, modelo 9 — Convênio SINIEF s/nº, de 15/12/1970 (CONFAZ): https://www.confaz.fazenda.gov.br/legislacao/ajustes/sinief/cvsn_70
- Guia Prático da EFD ICMS/IPI, **versão 3.2.2** (vigência a partir de 01/2026), registro **E110** — Apuração do ICMS, operações próprias: https://www.gov.br/sped/pt-br/assuntos/escrituracoes-digitais/efd-icms-ipi/manuais-e-documentos-tecnicos/guia-pratico-da-efd-icms-ipi-3-2.2/@@display-file/file — o Codex deve conferir as fórmulas abaixo no texto oficial e citar a página/seção; se divergirem, prevalece o Guia e a divergência é registrada.

**Correspondência resumo → E110** (para nomear o modelo canônico): 001 `VL_TOT_DEBITOS`; 002 `VL_AJ_DEBITOS`/`VL_TOT_AJ_DEBITOS` (como agregado "outros débitos"); 003 `VL_ESTORNOS_CRED`; 005 `VL_TOT_CREDITOS`; 006 `VL_AJ_CREDITOS`/`VL_TOT_AJ_CREDITOS` ("outros créditos"); 007 `VL_ESTORNOS_DEB`; 009 `VL_SLD_CREDOR_ANT`; 011 `VL_SLD_APURADO`; 012 `VL_TOT_DED`; 013 `VL_ICMS_RECOLHER`; 014 `VL_SLD_CREDOR_TRANSPORTAR`.

**Decisões (delegadas pelo usuário ao Claude em 04/10/2026: "segue todas suas orientações").**
- D1. Implementar no n8n (Sistema A), com o modelo de dados bem definido para migrar ao Sistema B depois.
- D2. Etapa 1 (esta tarefa): CSV e **PDF com camada de texto**, sem IA. Etapa 2 (T-0008, futura): IA para PDF escaneado ou leiaute não reconhecido, somente depois de resolvida a política de uso de dados do provedor.
- D3. Conferência que não fecha **bloqueia** a geração da planilha e devolve as divergências.

**Objetivo.** O mesmo workflow aceita CSV ou PDF com texto, converte ambos para um modelo canônico único, confere as somas com regras do livro modelo 9/E110 e só gera a planilha quando tudo fecha; caso contrário, responde com as divergências.

**Escopo — dentro** (artefatos em `docs/integration/system_a_icms_apuracao/`):
1. **Módulo JavaScript puro e testável** `raicms_parser.js` (sem dependências; executável no Code do n8n e no Node do CI): funções `parseCsv(texto)`, `parsePdfText(texto)`, `validate(modelo)`.
   - **Dinheiro em centavos inteiros** (`BigInt` ou inteiro seguro), convertidos de "1.234,56"; proibido `parseFloat`/`Number` para valores monetários (`AGENTS.md` 6.2). Zero tolerância: igualdade exata em centavos.
   - Modelo canônico: competência (mm/aaaa, lida do título; divergência entre títulos → erro), `entradas[]` e `saidas[]` com `cfop` (string de 4 dígitos) e os 5 valores, subtotais por grupo (1/2/3 e 5/6/7) e totais como **lidos do arquivo**, resumo 001–014 e deduções detalhadas, `origem` (`csv` | `pdf_texto`).
   - `parsePdfText`: classificar linha a linha, independente da ordem; CFOP deve ter 4 dígitos com primeiro dígito em {1,2,3,5,6,7} e exatamente 5 valores; linhas de subtotal/total pelos rótulos; resumo pelos códigos 001–014. CFOP repetido → erro. Linha não reconhecida que contenha números → registrar como "não interpretada" (não descartar em silêncio).
2. **Conferência (`validate`)**, retornando lista de divergências legíveis (campo, esperado, encontrado):
   - por bloco e por coluna: soma dos CFOPs do grupo = subtotal do grupo (1.00, 2.00, 3.00 / 5.00, 6.00, 7.00); Total = soma dos subtotais;
   - resumo: 004 = 001+002+003; 008 = 005+006+007; 010 = 008+009; se 004 > 010 então 011 = 004−010 e 014 = 0, senão 011 = 0 e 014 = 010−004; 013 = 011−012 (conferir no Guia 3.2.2);
   - cruzamentos: 001 = Total de Saídas "Imposto Debitado"; 005 = Total de Entradas "Imposto Creditado" — **confirmar no Guia/legislação se são igualdades obrigatórias**; se não forem, tratar como **alerta**, não bloqueio, e registrar a fonte.
3. **Workflow** (a partir da versão endurecida da T-0006, preservando autorização e Merge): detectar o tipo pelo conteúdo (assinatura `%PDF`) e não só pela extensão; PDF → nó nativo **Extract From File** (extração de texto) → `parsePdfText`; CSV → `parseCsv`; depois `validate`. Divergência ou PDF sem texto útil → resposta `422` com `success: false`, mensagem clara ("o arquivo não pôde ser conferido") e a lista de divergências, **sem** copiar planilha nem escrever no Sheets. Validado → fluxo atual de geração, acrescentando a origem dos dados na planilha se o modelo tiver campo apropriado (não alterar a planilha modelo sem decisão).
   - O nó Code deve conter exatamente o conteúdo de `raicms_parser.js` (teste que compare).
   - Manter `saveData* = none`, CORS restrito e todas as regras da T-0006.
4. **Testes**:
   - `node --test` sobre `raicms_parser.js` com **fixtures sintéticas** (valores inventados que respeitem a estrutura; nenhum dado real): CSV válido; texto de PDF fora de ordem válido; somas que não fecham (bloqueia); CFOP inválido; CFOP repetido; competência divergente; linha numérica não interpretada; valores com milhar e zero; saldo credor (004 < 010).
   - CI: acrescentar a execução de `node --test` ao `.github/workflows/ci.yml` (o runner Ubuntu já tem Node; registrar a versão usada).
   - Testes estáticos do JSON (como `tests/unit/test_system_a_*`): autorização antes de qualquer efeito; Extract From File no ramo PDF; nenhum efeito no Drive/Sheets no ramo de divergência; sem `parseFloat` no módulo.
5. **Frontend:** nenhuma mudança obrigatória. Se a tela não exibir a mensagem/divergências do `422`, registrar como pendência para um prompt do Lovable separado (não alterar nesta tarefa).

**Escopo — fora.** IA (T-0008); PDF escaneado; mudança na planilha modelo; pasta compartilhada (item 24); demais ferramentas.

**Restrições.** `AGENTS.md` 6.2 (Decimal/centavos, não inventar regra ou tolerância), 6.8 (determinístico primeiro), 6.9 (sem dado real em fixture, sem dado fiscal em log), 6.10; T-0006 (autorização, Merge, sem retenção).

**Critérios de aceite.**
1. O CSV real da amostra e o PDF real da amostra produzem **o mesmo modelo canônico** e geram a planilha (teste real do usuário).
2. Arquivo cujas somas não fecham não gera planilha e devolve divergências.
3. PDF sem texto útil não gera planilha e devolve mensagem orientando o uso de CSV (até a T-0008).
4. Nenhum valor monetário passa por ponto flutuante.
5. Testes `node --test` e estáticos passando no CI.

**Riscos.**
- Leiautes de outros sistemas podem rotular subtotais de forma diferente; o parser deve falhar fechado e listar o que não reconheceu (amostras futuras alimentam novos testes).
- A extração de texto do n8n pode quebrar linhas de forma diferente da amostra; o teste real com o PDF é obrigatório para o aceite.

**Ações do usuário.** Depois do CI verde e da revisão: importar o workflow, trocar pelo ativo (renomeando o anterior), testar com o CSV e o PDF da amostra e com um arquivo de somas alteradas.

---

## 2. Decisões do usuário

### [2026-10-04] Usuário
- "segue todas suas orientações" — implementar no n8n; conferência que não fecha bloqueia; provedor de IA a definir pelo Claude após verificar a política de dados. Sem outros modelos de relatório disponíveis; autorizado usar o leiaute do SPED Fiscal como referência.
- Briefing: pendente de aprovação.

### [2026-10-04] Usuário
- "aprovo o briefing da T-0007".

---

## 3. Implementação (Codex)

(aguardando "execute a tarefa T-0007")

### [2026-10-04] Codex — Implementação entregue para revisão

**Resultado.** Implementei a etapa determinística CSV/PDF com texto em artefatos isolados de `docs/integration/system_a_icms_apuracao/`. O módulo `raicms_parser.js` produz um modelo canônico único, usa centavos inteiros seguros sem `parseFloat`/`Number` para dinheiro, valida subtotais, totais, resumo 001–014, deduções detalhadas e linhas numéricas não interpretadas, e distingue divergências bloqueantes de alertas. As fixtures são sintéticas.

O workflow v10 parte do artefato endurecido da T-0006 e preserva Webhook → autorização → Merge antes de qualquer leitura. Depois da autorização, detecta `%PDF` pelo conteúdo; PDF passa pelo nó nativo `Extract From File`, CSV é decodificado diretamente, e ambos convergem no Code cujo `jsCode` é byte a byte o conteúdo do módulo. Somente `Conferencia valida? = true` alcança a cópia no Drive e o Sheets; o ramo falso responde `422` com `success: false`, mensagem, divergências e alertas. Falha de extração ou PDF sem texto também termina nesse ramo. O JSON permanece inativo, sem credenciais e sem retenção de execução.

**Decisão normativa aplicada.** Conferi o registro E110 no Guia Prático EFD-ICMS/IPI 3.2.2, atualização de 11/02/2026, páginas 223–225 do PDF (páginas impressas 224–226), em 04/10/2026. O briefing simplificava `013 = 011 - 012` e calculava 014 antes das deduções. O Guia prevalece: `013 = max(011 - 012, 0)` e `014 = max(010 + 012 - 004, 0)`. A divergência foi documentada no README. Os cruzamentos 001/005 com o imposto total agregado por CFOP são alertas, não bloqueios, porque o próprio Guia prevê inclusões/exclusões documentais e tratamento específico de CFOP 1605/5605 que este relatório agregado não permite reconstruir. O Livro modelo 9 foi referenciado pelo Convênio SINIEF s/nº de 15/12/1970. A definição oficial do nó `Extract From File` também foi consultada; por evidência do código do n8n, `maxPages: 0` não é enviado explicitamente, pois impediria a leitura das páginas.

**Arquivos criados.**

- `docs/integration/system_a_icms_apuracao/README.md`;
- `docs/integration/system_a_icms_apuracao/raicms_parser.js`;
- `docs/integration/system_a_icms_apuracao/raicms_parser.test.js`;
- `docs/integration/system_a_icms_apuracao/fixtures/raicms_valido.csv`;
- `docs/integration/system_a_icms_apuracao/fixtures/raicms_pdf_texto_valido.txt`;
- `docs/integration/system_a_icms_apuracao/n8n_ferramentas_ia_apuracao_icms_v10_csv_pdf_texto.json`;
- `tests/unit/test_system_a_icms_apuracao_assets.py`.

**Arquivos alterados.** `.github/workflows/ci.yml` ganhou Node 22 e `node --test`; `docs/colaboracao/QUADRO.md` foi movido para revisão; este relatório foi acrescentado. Nenhuma migration foi criada.

**Testes.** Node.js oficial v22.23.3 portátil, com SHA-256 conferido e removido depois do teste: `10 passed`; testes relacionados do Sistema A: `69 passed`; suíte Python completa: `646 passed, 20 skipped`, com dois avisos preexistentes de depreciação em FastAPI/Starlette; `git diff --check`: aprovado; varredura final: `SECRET_SCANNER_CANARY_DETECTION: PASS` e `RELEASE_SECRET_SCAN: PASS`. A primeira varredura encontrou somente falsos positivos dentro da distribuição temporária do Node; depois da remoção validada da pasta temporária, a varredura final passou.

**Limitações e pendências.** Não executei banco, API, n8n, Drive, Sheets, Supabase, Lovable ou arquivos fiscais reais. O parser foi validado apenas com fixtures sintéticas; o aceite continua dependente da importação e dos três testes reais descritos no briefing. A origem não foi acrescentada à planilha porque o modelo atual não possui campo apropriado e o briefing proíbe alterar a planilha sem nova decisão. Ainda é necessário verificar no teste real se a tela exibe mensagem e divergências do `422`; se não exibir, isso vira prompt separado do Lovable. PDF escaneado/IA, pasta compartilhada e mudança da planilha permanecem fora do escopo.

### [2026-10-04] Usuário (registrado pelo Claude)
- Lovable: opção "Use my Lovable content for model training" desligada em Account settings → Preferences ("Your content won't be used to train Lovable's AI models"). Relevante para a T-0008.

---

## 4. Revisão (Claude)

### [2026-10-04] Claude — Revisão da implementação

Verificado: autorização e Merge da T-0006 preservados; detecção do tipo pelo conteúdo; ramo PDF com `Extract From File` (`operation: pdf`); divergência → `422` sem tocar Drive/Sheets; centavos inteiros sem `parseFloat`; nó "1. Extrator e Consolidador" idêntico a `raicms_parser.js`; `node --test` acrescentado ao CI (Node 22); workflow inativo, sem retenção. O Claude não tem Node local; os testes JS não foram executados por ele (ficam para o CI). Para suprir isso, o Claude simulou à mão o parser sobre o CSV e o texto do PDF reais da amostra (não versionados) e comparou com o baseline `n8n_ferramentas_ia_apuracao_icms_v9.json`.

**Ajustes exigidos.**

1. **(ALTA — erro do briefing, não do Codex) Regressão: relatórios com vários meses.** O baseline ("CSV Fiscal FLEX (Anual/Mensal)") percorre várias seções "ENTRADAS/SAÍDAS mm/aaaa", acumula o valor contábil por CFOP em cada mês e só rejeita anos diferentes. O briefing pediu "competência divergente → erro", o que faz um CSV anual ser recusado. Corrigir: o modelo passa a ser uma lista de períodos do **mesmo ano**; cada período é conferido separadamente (blocos, subtotais, totais e resumo do próprio mês, quando presentes); anos diferentes → erro (como o baseline); CFOP repetido só é erro **dentro do mesmo período**; a planilha recebe cada mês na sua coluna. No texto do PDF fora de ordem, associar linhas ao período só quando isso for determinável; se um PDF trouxer mais de um período e a associação não for inequívoca, falhar fechado com mensagem.
2. **(ALTA) A amostra real seria bloqueada.** As linhas de detalhamento sob 012 — "Adicional relativo ao fundo de combate a pobreza" e "Dedução relativa ao incentivo a cultura" — chegam com espaços à esquerda (PDF) e com `;` à esquerda (CSV); não casam com `^(012...|DEDUCAO)` e caem em `nao_interpretadas`, que bloqueia. Corrigir: (a) normalizar a linha removendo delimitadores e espaços à esquerda antes de classificar; (b) reconhecer esses dois rótulos como **detalhamento informativo** da linha 012; (c) **remover a exigência** "soma do detalhamento = 012" (sem fonte normativa encontrada) — no máximo um alerta. Acrescentar fixtures sintéticas que reproduzam a estrutura completa do relatório real, inclusive cabeçalhos ("Operações com Crédito do Imposto…", "Débito do Imposto Coluna Auxiliar Somas", "Valores", linhas "****") e os dois detalhamentos, nos dois formatos.
3. **(MÉDIA) Tipo do valor na planilha.** O baseline envia números ao Sheets; a nova versão envia texto (`'1234.56'`), que numa planilha pt-BR pode virar texto. Manter números: converter centavos para número **só na fronteira de saída** para o Sheets, documentando que o domínio permanece em centavos inteiros.

**Veredito: AJUSTES PEDIDOS.** Depois: nova revisão, commit, push, CI com `node --test` verde e teste real do usuário com o CSV e o PDF da amostra.

### [2026-10-04] Claude — Complemento da revisão: amostra anual (CSV e PDF, competências 01–12/2025)

O usuário enviou um relatório anual real nos dois formatos (não versionar; usar só a estrutura abaixo para fixtures sintéticas). O relatório pode ter um mês ou vários. Achados que **substituem e ampliam o ajuste 1**:

1. **Vários resumos por período.** Além de "Resumo Apuração - ICMS mm/aaaa" (operações próprias), cada mês pode trazer "Resumo Apuração do ICMS - Substituição Tributária - Dentro do Estado mm/aaaa" e "Resumo Apuração do ICMS - Substituição Tributária - Fora do Estado mm/aaaa", cada um com os códigos 001–014. Os blocos de ST são opcionais por mês (no CSV, 04, 05 e 07/2025 não têm). O modelo deve guardar o resumo por **(período, tipo)**, com tipo ∈ {`proprio`, `st_dentro`, `st_fora`}; código repetido só é erro dentro do mesmo (período, tipo). Título de resumo não reconhecido → falhar fechado listando o título.
2. **Conferência dos resumos de ST.** As igualdades internas do formulário (004 = 001+002+003; 008 = 005+006+007; 010 = 008+009; saldo devedor/credor; 013 = 011−012) fecham na amostra (conferido em um mês com saldo credor de ST). Aplicar as mesmas igualdades aos blocos de ST somente depois de conferir, no Guia Prático 3.2.2, o registro **E210** (apuração do ICMS-ST) e citar a seção; se o E210 não sustentar alguma igualdade para ST, ela vira alerta. Os cruzamentos 001/005 × totais de CFOP valem só para o resumo `proprio`.
3. **Períodos sem movimentação.** Blocos "**** SEM MOVIMENTAÇÃO ****" não têm linhas de CFOP; trazem subtotais e totais zerados. Isso é válido. Se o arquivo inteiro não tiver nenhum CFOP (caso da amostra anual), responder com mensagem clara "Sem movimentação de CFOP no período informado" (não como divergência), sem gerar planilha — o baseline também não gera nada nesse caso, mas devolvia erro genérico.
4. **PDF com vários períodos.** Cada página da amostra contém um único bloco (movimento do mês; resumo próprio; ST dentro; ST fora) e o título vem **no fim do texto da página**. Com `joinPages: true` as páginas se misturam e não é possível atribuir linhas ao período. Corrigir: extrair **por página** (`joinPages: false` ou equivalente) e associar as linhas de cada página ao período e ao tipo indicados pelos títulos da própria página; página com títulos de períodos diferentes, ou com linhas numéricas e nenhum título → falhar fechado com mensagem. Confirmar no nó Extract From File do n8n 2.6.4 a forma de saída por página e registrar.
5. **CSV com vários períodos.** O CSV é sequencial: o título ("ENTRADAS mm/aaaa", "SAÍDAS mm/aaaa", "Resumo Apuração - ICMS mm/aaaa", "Resumo … Substituição Tributária - Dentro/Fora do Estado mm/aaaa") define o período e a seção até o próximo título.
6. **Fixtures sintéticas obrigatórias**, além das já pedidas: (a) arquivo de vários meses com movimento em alguns e "SEM MOVIMENTAÇÃO" em outros; (b) meses com e sem blocos de ST; (c) arquivo inteiro sem movimentação; (d) texto de PDF por página, com o título no fim, para dois ou mais meses; (e) anos diferentes → erro; nos dois formatos quando aplicável.

Os ajustes 2 (detalhamento da linha 012 e remoção da regra de soma) e 3 (números na planilha) continuam valendo.

### [2026-10-04] Codex — Resposta aos ajustes da revisão

**Resultado.** Implementei os ajustes das duas entradas de revisão. O modelo canônico agora mantém `resumos` por competência e tipo (`proprio`, `st_dentro`, `st_fora`), permite que o mesmo código 001–014 apareça em tipos distintos e aplica a cada resumo as igualdades internas sustentadas por E110/E210. Os cruzamentos entre 001/005 e totais de CFOP permanecem alertas e são executados somente no resumo próprio. Blocos ST continuam opcionais.

O CSV usa o título como contexto sequencial. O PDF passa a ser extraído com `joinPages: false`; o workflow preserva o array de textos retornado pelo n8n e o parser associa cada página ao período/tipo indicado pelos títulos da própria página, inclusive quando o título está no fim. Página numérica sem título, dois períodos na mesma página, título ST desconhecido e anos diferentes falham fechado.

Períodos “SEM MOVIMENTAÇÃO” com subtotais e totais zerados são válidos. Um arquivo inteiro sem CFOP não é divergência: responde `200`, `success: true`, mensagem “Sem movimentação de CFOP no período informado.” e não alcança Drive/Sheets. O IF do workflow agora decide a geração pelo campo `gerarPlanilha`, mantendo falhas de conferência no `422`. Os valores enviados ao Sheets continuam numéricos somente na fronteira de saída; o domínio permanece em centavos inteiros.

**Base normativa/técnica.** Além do E110 já registrado, conferi o E210 no Guia Prático EFD-ICMS/IPI 3.2.2, páginas 229–232 do PDF (impressas 230–233): os campos de saldo devedor, deduções, imposto a recolher e saldo credor transportado sustentam as mesmas relações internas usadas pelo formulário ST. No código oficial do n8n consultado em 04/10/2026, a operação PDF com `joinPages: false` entrega `text` como lista de páginas; isso foi documentado no README.

**Arquivos criados nesta rodada.** Fixtures sintéticas `raicms_anual_misto.csv`, `raicms_sem_movimentacao.csv` e `raicms_pdf_paginas.json`.

**Arquivos alterados nesta rodada.** `raicms_parser.js`, `raicms_parser.test.js`, `README.md`, o workflow v10, `tests/unit/test_system_a_icms_apuracao_assets.py`, `docs/colaboracao/QUADRO.md` e este registro. Os demais arquivos da implementação inicial permanecem como parte da T-0007. Nenhuma migration foi criada.

**Testes.** Node.js oficial v22.23.3 portátil, com SHA-256 conferido e removido após o uso: `17 passed`. Teste estático específico: `6 passed`. Suíte Python completa: `646 passed, 20 skipped`, com dois avisos preexistentes de depreciação FastAPI/Starlette. A primeira tentativa da suíte parou na coleta porque a dependência `redis`, já declarada no `pyproject.toml`, não estava instalada no ambiente local; instalei `redis 8.1.0` e a repetição passou. `git diff --check`, canário do scanner e varredura de segredos: aprovados.

**Limitações e pendências.** Não executei serviço real, n8n, Drive, Sheets, banco, Lovable nem arquivos fiscais reais. O aceite ainda depende da revisão do diff pelo Claude e do teste manual do usuário com as amostras reais, conforme o briefing. PDF escaneado/IA continua fora do escopo desta tarefa.

### [2026-10-04] Claude — Segunda revisão, com execução real do parser

O usuário instalou o Node.js 22.23.3. O Claude executou `node --test` (17 aprovados), `tests/unit/test_system_a_icms_apuracao_assets.py` (6 aprovados) e um script local, **fora do repositório**, que roda `parseCsv`/`parsePdfText`/`validate`/`spreadsheetRows`/`runN8n` sobre a estrutura dos três arquivos reais do usuário (mês 01/2026 em CSV e PDF por página; anual 01–12/2025 em CSV e PDF por página, com resumos de ST):

| Caso | Resultado |
|---|---|
| Mês, CSV | válido; 12 CFOPs; planilha com números (`JANEIRO: 33458.18`) |
| Mês, PDF | válido; **modelo idêntico ao do CSV** (critério de aceite 1) |
| Anual, CSV | válido; 12 períodos; resumos próprio e ST conferidos; resposta "Sem movimentação de CFOP no período informado", sem planilha |
| Anual, PDF | **inválido — 48 divergências** |

Também conferido: nó "1. Extrator e Consolidador" idêntico ao módulo; `joinPages: false`; "Conferencia valida?" usa `gerarPlanilha`; sem movimentação → 200 com mensagem, divergência → 422; ajustes 2 (detalhamento da 012) e 3 (números) atendidos.

**Ajuste exigido (ALTA).** Em página de mês sem movimentação, o PDF traz duas linhas "Total" zeradas (entradas e saídas) sem rótulo de lado. `classifyTotals` só atribui quando o valor casa com **um** lado; como os dois lados somam igual, as duas linhas caem em `nao_interpretadas` e faltam `totais.entradas`/`totais.saidas`. Corrigir: quando um candidato casar com os dois lados, atribuí-lo ao primeiro lado ainda vazio (os valores são idênticos, não há perda de informação); só restar em `nao_interpretadas` se ambos os lados já estiverem preenchidos ou se não casar com nenhum. Acrescentar fixture sintética de PDF por página com mês sem movimentação (duas linhas "Total" zeradas, título no fim) e com dois ou mais meses.

**Ponto de atenção para o teste real:** no caso sem movimentação a resposta é `200` com `success: true` e sem `url`; verificar no teste real como a tela do Lovable reage. Se tentar abrir link inexistente, registrar para um prompt do Lovable separado.

### [2026-10-04] Codex — Resposta à segunda revisão

**Resultado.** Corrigi exclusivamente a ambiguidade apontada em `classifyTotals`. Quando uma linha `Total` sem indicação de lado coincide com as somas de entradas e saídas, ela agora ocupa o primeiro lado compatível ainda vazio: a primeira linha preenche entradas e a segunda preenche saídas. Se ambos os lados já estiverem preenchidos, ou se o valor não coincidir com nenhum deles, a linha continua em `nao_interpretadas` e bloqueia a conferência.

**Arquivos criados nesta rodada.** Fixture sintética `fixtures/raicms_pdf_sem_movimentacao_multiperiodo.json`, com dois meses e uma página sem movimentação contendo dois totais zerados e títulos no fim.

**Arquivos alterados nesta rodada.** `raicms_parser.js`, `raicms_parser.test.js`, `README.md`, o código idêntico do nó “1. Extrator e Consolidador” no workflow v10, `docs/colaboracao/QUADRO.md` e este registro. Nenhuma migration foi criada.

**Testes.** `node --test`: 18 aprovados; teste estático do workflow: 6 aprovados; suíte Python de `tests/unit`, `tests/integration` e `tests/api`: 546 aprovados, com dois avisos preexistentes de depreciação FastAPI/Starlette. O novo teste comprova que os dois totais idênticos são preservados, não geram linha não interpretada e validam o período sem movimentação.

**Limitações e pendências.** Não executei n8n, Drive, Sheets, banco, Lovable nem arquivos fiscais reais. Permanecem o teste real do usuário e a verificação da reação do Lovable à resposta `200` sem `url`, exatamente como registrado na segunda revisão.

### [2026-10-04] Claude — Correção de conteúdo (exceção ao append-only, autor da entrada)

Na entrada "Complemento da revisão: amostra anual", o Claude havia citado três valores reais do relatório do usuário como exemplo; eles foram reproduzidos na fixture `raicms_anual_misto.csv`. O Claude retirou os valores da própria entrada e, como revisor, trocou-os na fixture por valores inventados coerentes (001/004 = 20,00; 006/008/010 = 1.500,00; 014 = 1.480,00). Nenhum outro arquivo continha valores da amostra (busca por todos os valores da amostra mensal e anual).

### [2026-10-04] Claude — Terceira revisão e aceite de código

- `classifyTotals`: candidato que casa com os dois lados vai para o primeiro lado vazio; só sobra em `nao_interpretadas` se ambos já estiverem preenchidos ou se não casar com nenhum. Atendido.
- Execução real (Node 22.23.3): `node --test` 18/18; `tests/unit/test_system_a_icms_apuracao_assets.py` 6/6; `tests/unit` 323 aprovados; varredura de segredos `PASS`. Script local sobre a estrutura dos arquivos reais: **mês CSV, mês PDF, anual CSV e anual PDF válidos**, sem divergências; CSV e PDF do mês produzem o mesmo modelo.
- Correção feita pelo Claude como revisor: valores da amostra real retirados da fixture `raicms_anual_misto.csv` e da asserção correspondente em `raicms_parser.test.js` (2393 → 2000), por valores inventados coerentes (ver entrada anterior).
- **Veredito: ACEITO o código.** Aceite final da tarefa depende de: CI verde (inclui `node --test`) e teste real do usuário no n8n com os três arquivos (mês CSV, mês PDF, anual) e um arquivo com soma alterada; observar a reação da tela à resposta "sem movimentação" (200 sem `url`).

### [2026-10-04] Claude — Teste real no n8n e ajuste pedido

Workflow v10 importado e ativo; testes do usuário pela tela (Administrador):

| Arquivo | Resultado |
|---|---|
| mês, CSV | planilha gerada |
| mês, PDF | primeira tentativa recusada; segunda gerou planilha (200 com `url`) — causa da primeira recusa não identificada; repetir após o ajuste |
| anual, CSV | parser correto (sem movimentação), mas a tela exibiu "Resposta inesperada da API": recebeu `200`, `success: true`, sem `url` |
| anual, PDF | `422`; divergências por período (resposta copiada do navegador pelo usuário) |

**Texto real produzido pelo nó Extract From File (n8n 2.6.4, `joinPages: false`) nas páginas sem movimentação** — formas observadas, literalmente:
- `0,00 0,00 0,00 0,00 0,001.00 do Estado` (e `2.00 de O. Estados`, `3.00 do Exterior`, `5.00 do Estado`, `6.00 de O. Estados`, `7.00 do Exterior`): **valores antes do rótulo e o rótulo grudado no último valor, sem espaço**;
- `0,00 0,00 0,00 0,00 0,00Total`: idem para o total;
- `Total 0,00 0,00 0,00 0,00 0,00`: na mesma página, outra linha em ordem normal.
O parser só reconhece rótulos no início da linha (`^([123567])\.00`, `TOTAL`), então subtotais e totais ficam ausentes. Na página com movimento do relatório mensal a ordem veio normal, mas nada garante isso em outros sistemas.

**Ajustes exigidos ao Codex.**
1. **(ALTA) Tokenização independente de ordem e de espaço.** Separar cada linha em valores monetários (padrão já existente) e rótulo (o texto restante, com espaços normalizados), aceitando o rótulo antes **ou** depois dos valores e **grudado** no primeiro/último valor. Classificar o rótulo: CFOP (exatamente 4 dígitos, primeiro em {1,2,3,5,6,7}); grupo `N.00` com "do Estado"/"de O. Estados"/"do Exterior"; "Total"; código de resumo 001–014 seguido de texto; detalhamentos da 012. Garantir que um valor grudado num rótulo numérico não seja mal lido (ex.: `21.249,241102` → valor `21.249,24` e CFOP `1102`; `6,29001 Por saídas…` → valor `6,29` e código `001`). Rótulo ambíguo ou linha com quantidade inesperada de valores → `nao_interpretadas` (continua bloqueando).
2. **Fixtures sintéticas com as formas reais acima**, para entradas, saídas, subtotais, total, CFOP com valores antes e grudado, e resumo com valor antes do código; nos testes, a página sem movimentação no formato do n8n (duas linhas "Total" em ordens diferentes).
3. **(MÉDIA) Resposta "sem movimentação".** A tela só exibe `message` quando a resposta é de falha; com `200`/`success: true` sem `url` mostra "Resposta inesperada da API". Responder `422` com `success: false` e `message: "Sem movimentação de CFOP no período informado."` (sem divergências), documentando que 422 aqui significa "nada a gerar", não erro de conferência.

### [2026-10-04] Codex — Resposta ao ajuste do teste real no n8n

**Resultado.** Implementei a tokenização das linhas antes da classificação. Cada linha agora é separada em valores monetários e rótulo normalizado, independentemente de o rótulo vir antes ou depois dos valores ou estar grudado ao primeiro/último valor. CFOP, grupos, totais, códigos 001–014 e detalhamentos da 012 são classificados a partir do rótulo separado. CFOP/código numérico grudado ao primeiro valor é desambiguado antes da extração monetária; rótulo não único ou quantidade inesperada de valores continua em `nao_interpretadas` e bloqueia a conferência.

O caso integralmente sem CFOP agora mantém a conferência determinística válida internamente, mas o contrato HTTP retorna `success: false`, `semMovimentacao: true`, mensagem “Sem movimentação de CFOP no período informado.” e divergências vazias. O nó de resposta usa sempre `422` nesse ramo; aqui o status significa “nada a gerar” para compatibilidade com a tela, não erro nas somas.

**Arquivo criado nesta rodada.** `fixtures/raicms_pdf_n8n_rotulos_grudados.json`, integralmente sintético, com rótulos antes/depois dos valores, concatenação sem espaço, CFOP e resumo numéricos grudados, dois períodos e página sem movimentação com os dois formatos de `Total` observados.

**Arquivos alterados nesta rodada.** `raicms_parser.js`, `raicms_parser.test.js`, `README.md`, o código idêntico do nó “1. Extrator e Consolidador” e o nó “Responder Arquivo Nao Conferido” no workflow v10, `tests/unit/test_system_a_icms_apuracao_assets.py`, `docs/colaboracao/QUADRO.md` e este registro. Nenhuma migration foi criada.

**Testes.** `node --test`: 20 aprovados; teste estático específico: 6 aprovados; suíte Python de `tests/unit`, `tests/integration` e `tests/api`: 546 aprovados, com dois avisos preexistentes de depreciação FastAPI/Starlette.

**Limitações e pendências.** Não executei n8n, Drive, Sheets, banco, Lovable nem arquivos fiscais reais. O workflow precisa ser reimportado/substituído no n8n e os quatro testes reais da entrada anterior devem ser repetidos pelo usuário, inclusive o PDF mensal cuja primeira recusa não teve causa identificada.

### [2026-10-04] Claude — Quarta revisão (texto real do n8n)

- `node --test` 20/20; `tests/unit/test_system_a_icms_apuracao_assets.py` 6/6; `tests/unit` 323; varredura `PASS`; nó Code idêntico ao módulo; "sem movimentação" e divergência → `422` com `success: false` e `message`; sem retenção; nenhum valor da amostra real nas fixtures.
- Simulação local (fora do repositório) com a estrutura dos arquivos reais, agora incluindo o formato literal observado no Extract From File: **seis cenários válidos** — mês CSV; mês PDF; anual CSV; anual PDF; anual PDF no formato do n8n (valores antes, rótulos grudados, duas linhas "Total" em ordens diferentes); mês PDF com CFOP e resumo invertidos e grudados (`…21.249,241102`, `6,29001 Por saídas…`), que produz o mesmo modelo do CSV.
- **Veredito: ACEITO o código.** Aceite final da tarefa: reimportar o workflow e repetir os quatro arquivos pela tela (mês CSV e PDF → planilha; anual CSV e PDF → mensagem de sem movimentação) e um CSV com valor alterado (→ divergências).

### [2026-10-04] Claude — Novo teste real: linhas em negrito duplicadas

Workflow com a versão `634d952` reimportado. Teste do usuário pela tela com dois relatórios anuais em PDF (2025, sem movimentação; e um segundo de 2026, sem CFOP e com resumos de ST com valores): ambos `422`. As páginas de movimento **passaram** (nenhuma divergência de subtotal/total de CFOP). Divergências restantes, em todos os períodos e tipos de resumo, apenas nas linhas 008 e 010, que no PDF estão em **negrito**. Texto literal entregue pelo Extract From File:
- `008 Subtotal 0,00008 Subtotal 0,00`
- `010 Total 0,00010 Total 0,00`
O gerador do relatório simula negrito desenhando o texto duas vezes; a extração devolve as duas cópias grudadas. A versão anterior do parser aceitava por acaso (usava o último valor); a tokenização nova exige um valor por código e recusa. O PDF mensal tem as mesmas linhas em negrito e provavelmente passa a falhar.

**Ajuste exigido ao Codex (ALTA).** Antes de tokenizar, se a linha (com espaços normalizados) for exatamente a concatenação de duas cópias idênticas de um mesmo texto — com ou sem espaço entre elas — usar uma única cópia. Só aplicar quando as duas metades forem idênticas caractere a caractere; qualquer outra repetição continua sendo tratada normalmente. Fixtures sintéticas com linhas de resumo duplicadas nas duas formas (com e sem espaço) e em blocos `proprio`, `st_dentro` e `st_fora`.

### [2026-10-04] Codex — Resposta ao ajuste das linhas em negrito duplicadas

**Resultado.** Acrescentei uma normalização anterior à tokenização que reduz a linha a uma cópia somente quando, depois de normalizar espaços, ela é formada por duas metades exatamente iguais. São aceitas as formas com as cópias grudadas ou separadas por um único espaço normalizado. Se qualquer caractere ou valor diferir, a linha permanece intacta e segue para a classificação normal, continuando bloqueante quando não puder ser interpretada.

**Arquivo criado nesta rodada.** `fixtures/raicms_pdf_resumos_negrito_duplicados.json`, integralmente sintético, com linhas 008 e 010 duplicadas nas duas formas nos resumos `proprio`, `st_dentro` e `st_fora`.

**Arquivos alterados nesta rodada.** `raicms_parser.js`, `raicms_parser.test.js`, `README.md`, o código idêntico do nó “1. Extrator e Consolidador” no workflow v10, `docs/colaboracao/QUADRO.md` e este registro. Nenhuma migration foi criada.

**Testes.** `node --test`: 22 aprovados; teste estático específico: 6 aprovados; suíte Python de `tests/unit`, `tests/integration` e `tests/api`: 546 aprovados, com dois avisos preexistentes de depreciação FastAPI/Starlette. O teste negativo confirma que duas cópias com valores diferentes não são reduzidas.

**Limitações e pendências.** Não executei n8n, Drive, Sheets, banco, Lovable nem arquivos fiscais reais. O workflow precisa ser reimportado/substituído e os PDFs anual e mensal devem ser repetidos pela tela para confirmar o comportamento do `Extract From File` no ambiente real.

### [2026-10-04] Claude — Quinta revisão (negrito duplicado)

- `collapseExactDuplicateLine`: usa uma cópia só quando a linha normalizada é exatamente `x + x` ou `x + ' ' + x`; nenhum outro caso é alterado. `node --test` 22/22; `tests/unit` 323; varredura `PASS`; nó Code idêntico ao módulo; nenhum valor das amostras reais nas fixtures.
- Simulação local (fora do repositório): nove cenários válidos, incluindo anual no formato do n8n com 008/010 duplicadas, mensal com 008/010 duplicadas (mesmo modelo do CSV) e mensal invertido com duplicação separada por espaço.
- **Veredito: ACEITO o código.** Aceite final: reimportar e repetir pela tela os cinco arquivos (mês CSV e PDF → planilha; anual 2025 PDF e anual 2026 PDF → "Sem movimentação de CFOP no período informado"; CSV com valor alterado → divergências).

### [2026-10-04] Claude — Teste real final e encerramento

Workflow `c5eba50` reimportado e ativo; anterior renomeado. Testes do usuário pela tela (Network conferido):
- três envios → `200`, "Planilha Gerada com Sucesso!" (mês CSV, mês PDF e anual 2026 com movimento, conforme o usuário: "deu certo todos");
- `icms anual.pdf` (2025, sem CFOP) → `422`, tela exibe "Sem movimentação de CFOP no período informado.";
- CSV com valor alterado → `422`, "O arquivo não pôde ser conferido.".
Critérios de aceite 1–5 atendidos (1 também pela simulação local: CSV e PDF do mês produzem o mesmo modelo).

A simulação local com a estrutura dos arquivos reais foi apagada da pasta temporária do Claude.

**Pendências que não reabrem a tarefa:** PDF escaneado / IA (T-0008, item 23); planilhas em pasta compartilhada (item 24); a tela não lista as divergências (só a mensagem) — eventual prompt do Lovable; conferir visualmente, quando conveniente, que a planilha do PDF mensal tem os mesmos valores da do CSV.

**Estado: CONCLUÍDA.**
