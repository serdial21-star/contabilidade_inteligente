# T-0007 — Apuração ICMS a partir de PDF com texto, com conferência obrigatória

| Campo | Valor |
|---|---|
| Estado | BRIEFING — aguardando aprovação do usuário |
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
