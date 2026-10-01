# T-0002 — CI verde: eliminar falsos positivos da varredura de segredos sem afrouxá-la

| Campo | Valor |
|---|---|
| Estado | CONCLUÍDA |
| Origem | Item 13 do QUADRO; confirmado com `gh` em 01/10/2026 |
| Sistema | Sistema B (CI, scripts e documentação) |
| Exige ADR | não — mas a abordagem toca a decisão registrada em `docs/SECURITY_GATE_EXECUTION_33.md` (ver "Restrições"); a aprovação deste briefing registra a escolha |
| Exige ação do usuário | sim — aprovar o briefing e, no fim, fazer o `push` |

---

## 1. Briefing (Claude)

### [2026-10-01] Claude — Briefing

**Problema.**

O CI do GitHub (`.github/workflows/ci.yml`) está vermelho em todos os pushes desde 22/09/2026; o último sucesso foi o commit `9f48be7`. Testes, `pip-audit` e checagem de head único do Alembic passam. Só falha a última etapa, `python scripts/verify_release_secrets.py`, por 6 achados, todos falsos positivos (conferido linha a linha pelo Claude):

> Notação: para não disparar a própria varredura, os exemplos desta tarefa são escritos como **chave ← valor** (a seta substitui o sinal de igual). Ver a correção de 01/10/2026 abaixo do briefing.

| Arquivo | Padrão | Conteúdo que dispara | Por que não é segredo |
|---|---|---|---|
| `scripts/dev_identity_provider.py:51` | `password-assignment` | `password` ← `None` | argumento da biblioteca `cryptography`: chave sem senha |
| `tests/unit/test_generate_bridge_keypair.py:36` | `password-assignment` | `password` ← `None` | idem |
| `scripts/validate_system_a_password_recovery.sh:38` e outras | `password-assignment` | `--password` ← `"${DB_PASSWORD}"` | referência a variável gerada por `openssl rand -hex 24` |
| `scripts/validate_system_a_client_management.sh:14, 19, 27…` | `password-assignment` | `synthetic-root-password` | senha fixa de contêiner descartável de teste |
| `docs/LOCAL_REAL_DATA_IMPORT.md:67` | `password-assignment` | `MARIADB_ROOT_PASSWORD` ← `ESCOLHA_UMA_SENHA` | placeholder de documentação |
| `docs/SISTEMA_A_BRIDGE_KEY_SETUP.md:41` | `private-key` | texto que cita os marcadores PEM de início e fim de chave privada | instrução, sem chave |

Efeito real: com o CI sempre vermelho, uma falha verdadeira (teste quebrado, dependência vulnerável, segredo real) passa despercebida. Foram 9 dias sem ninguém notar.

O script também não tem nenhum teste próprio e reporta só o arquivo, sem a linha.

**Objetivo.** O CI volta a ficar verde com a varredura **igualmente ou mais rigorosa** que hoje: nenhum segredo literal deixa de ser detectado e o canário continua obrigatório.

**Escopo.**
- Dentro:
  1. Refinar **somente** o padrão `password-assignment` para não disparar quando o valor, comprovadamente, não é um literal: `None` (Python) e referência a variável de shell/PowerShell (`$VAR`, `${VAR}`, `$(...)`, `$env:VAR`), com ou sem aspas.
  2. `scripts/validate_system_a_client_management.sh`: trocar a senha fixa por senha gerada em tempo de execução, como já faz `validate_system_a_password_recovery.sh` (`openssl rand -hex 24`).
  3. `docs/LOCAL_REAL_DATA_IMPORT.md`: trocar o placeholder literal por leitura de variável de ambiente que o próprio usuário define (ex.: `$env:SERDIAL21_LOCAL_DB_PASSWORD`), mantendo a orientação de que a senha não deve ser colada em conversa, arquivo ou log. Aplicar o mesmo nas linhas 58 e 78 do mesmo arquivo, se ficarem coerentes.
  4. `docs/SISTEMA_A_BRIDGE_KEY_SETUP.md`: reescrever a instrução sem reproduzir o marcador literal (ex.: "incluindo as linhas de início e de fim do bloco, que começam com cinco hífens").
  5. Reportar o **número da linha** de cada achado, sem nunca imprimir o valor encontrado.
  6. Criar testes para o script.
- Fora (não fazer nesta tarefa):
  - lista de exceções (allowlist) por arquivo, por linha ou por marcador;
  - novos padrões de detecção (ver item 14 da fila);
  - mudar outras etapas do CI ou a versão do Python do CI (item 10 da fila).

**Referências.**
- Consultadas e aplicáveis: `docs/SECURITY_GATE_EXECUTION_33.md`, seção "RELEASE VERIFICATION - EXECUTION 36" (intenção da varredura: falha fechada, canário obrigatório, **sem allowlist ou redução de cobertura**); `AGENTS.md` 6.9 (segredos fora do código, `.env` não versionado) e 8 ("não reduza guardrails para fazer um teste passar"); assinatura `cryptography.hazmat.primitives.serialization.load_pem_private_key(data, password, ...)`, onde `password` ← `None` significa chave não cifrada.
- Procuradas e não encontradas: nenhuma norma legal se aplica a esta tarefa. Ferramentas de mercado (gitleaks, detect-secrets) usam allowlist; **não** adotá-las aqui, porque a decisão interna documentada exclui allowlist e acrescentar dependência exige justificativa (`AGENTS.md` 3).
- Documentos internos lidos: `.github/workflows/ci.yml`, `scripts/verify_release_secrets.py`, os 6 arquivos acima, `docs/SECURITY_GATE_EXECUTION_33.md`.

**Restrições.**
- **Decisão existente:** a varredura foi documentada como "sem allowlist ou redução de cobertura". Esta tarefa a respeita: não cria allowlist e o refinamento do item 1 exclui apenas valores que não podem ser segredo literal. Se o Codex entender que algum caso exige allowlist, deve **parar e contestar** no arquivo da tarefa, não implementar.
- Os padrões `private-key` e `aws-access-key` não mudam.
- O canário continua obrigatório e a varredura continua cobrindo arquivos versionados e arquivos novos não ignorados.
- A saída nunca imprime o trecho encontrado, só rótulo, arquivo e linha.
- Não alterar o comportamento dos scripts de validação além da origem da senha.

**Critérios de aceite.**
1. `python scripts/verify_release_secrets.py` termina com código 0 e imprime `SECRET_SCANNER_CANARY_DETECTION: PASS` e `RELEASE_SECRET_SCAN: PASS`.
2. Um literal continua detectado em todas as formas (sinal de igual no lugar da seta): `password` ← `hunter2`; `PASSWORD` ␠←␠ `"abc123"` (com espaços); `password` ← `'x'`; `--password` ← `literal`; `MARIADB_ROOT_PASSWORD` ← `literal`.
3. Não disparam: `password` ← `None`; `password` ␠←␠ `None`; `--password` ← `"${DB_PASSWORD}"`; `password` ← `$DB_PASSWORD`; `password` ← `$(openssl rand -hex 24)`; `password` ← `$env:SERDIAL21_LOCAL_DB_PASSWORD`.
4. Casos de fronteira continuam detectados: `password` ← `None123`; `password` ← `Nonexistent`; `password` ← `$` sozinho; `password` ← `${}` vazio. Se algum desses não fizer sentido, justificar no relatório.
5. `private-key` e `aws-access-key` continuam detectando exatamente o que detectavam.
6. Cada achado sai como `rótulo: caminho:linha`; o valor nunca aparece na saída.
7. `validate_system_a_client_management.sh` não contém senha fixa.
8. Suíte padrão sem falhas e sem redução do número de testes.
9. **CI verde no GitHub** após o push — verificado pelo Claude com `gh`.

**Testes exigidos** (novo arquivo, ex.: `tests/unit/test_verify_release_secrets.py`, chamando as funções do script sobre arquivos temporários; sem depender de `git`).
1. Cada caso dos critérios 2, 3 e 4, com o resultado esperado.
2. O canário AWS é detectado.
3. Um arquivo com o cabeçalho PEM de chave privada RSA (montado em tempo de execução no teste) é detectado como `private-key`.
4. A saída de um achado contém arquivo e linha e **não** contém o valor.
5. Arquivo binário ou ilegível não derruba silenciosamente a varredura: ou é varrido como bytes, como hoje, ou falha fechado.

**Riscos e pontos de atenção.**
- A expressão regular refinada é o coração da tarefa. Cuidado para que `None` só seja aceito como valor **inteiro** (seguido de fim, espaço, vírgula ou parêntese), não como prefixo.
- Referências a variável só são aceitas se começarem pela variável; `password` ← `abc$VAR` continua sendo literal.
- Passar a varrer por linha muda o custo da varredura; o repositório é pequeno, mas o teste não deve depender do tamanho.

**Ações do usuário.** Aprovar este briefing. No fim, fazer o `push`; o Claude confere o CI.

### [2026-10-01] Claude — Correção do briefing (exceção registrada ao append-only)

- **Erro do Claude:** o briefing original trazia os exemplos de critério literalmente (atribuições de senha e o marcador PEM de chave privada). Como este arquivo é versionado, a própria varredura passou a acusá-lo: 20 achados, todos no briefing. O Codex identificou o conflito, não contornou a varredura e parou para perguntar, como o protocolo exige.
- **Correção aplicada pelo autor do briefing:** os exemplos foram reescritos na notação chave ← valor e o marcador PEM foi descrito em palavras. O significado de cada critério ficou idêntico. Nada foi excluído da varredura.
- **Por que reescrever em vez de acrescentar:** uma entrada nova não removeria o texto que dispara a varredura. A exceção é limitada a esta finalidade, foi feita pelo próprio autor da entrada e o arquivo ainda não tinha sido commitado.
- **Regra acrescentada ao protocolo (seção 2):** exemplos que disparariam a varredura de segredos são sempre escritos em notação segura.

---

## 2. Decisões do usuário

### [2026-10-01] Usuário
- Aprovou o briefing ("aprovado T-0002"), incluindo a abordagem **sem allowlist**, que mantém a decisão registrada em `docs/SECURITY_GATE_EXECUTION_33.md` (execução 36), e o refinamento restrito do padrão `password-assignment` a valores que não podem ser literais (`None` e referência a variável).

---

## 3. Implementação (Codex)

### [2026-10-01] Codex — Implementação interrompida por conflito no briefing

**Implementado.**

- `scripts/verify_release_secrets.py`: varredura por linha em bytes, número da
  linha no achado e exclusão restrita a `None` inteiro ou referência inteira de
  shell/PowerShell, inclusive quando delimitada por aspas. Os padrões estáticos
  de chave privada e AWS foram preservados.
- `scripts/validate_system_a_client_management.sh`: a senha fixa do MariaDB foi
  substituída por valor aleatório gerado em runtime com OpenSSL; os comandos
  obrigatórios são verificados antes do uso.
- `docs/LOCAL_REAL_DATA_IMPORT.md`: os exemplos agora leem a senha de forma
  oculta, armazenam-na somente no ambiente do processo e a referenciam nos
  comandos.
- `docs/SISTEMA_A_BRIDGE_KEY_SETUP.md`: a instrução não reproduz mais os
  marcadores literais da chave privada.
- `tests/unit/test_verify_release_secrets.py`: 21 testes cobrem literais,
  referências válidas, fronteiras inválidas, canário AWS, chave privada, bytes
  não textuais e saída sanitizada com caminho e linha.

**Validação.**

- Teste específico: `21 passed`.
- Suíte completa: `597 passed, 20 skipped`; os 20 testes MariaDB permaneceram
  ignorados por exigirem opt-in/ambiente real. Houve 2 avisos de depreciação de
  dependências já existentes.
- `git diff --check`: sem erro; somente avisos de normalização LF/CRLF.
- Sintaxe shell via WSL: não executada, pois a instalação disponível não possui
  `/bin/bash`. O script funcional com Docker não foi executado, em respeito à
  proibição de acessar serviços reais e à ausência de ambiente descartável
  autorizado.
- Migration: nenhuma.

**Impasse bloqueante descoberto.**

A varredura real detecta 20 achados somente neste próprio arquivo da T-0002:
18 ocorrências do padrão de atribuição e 2 marcadores de chave privada, todos
presentes no briefing aprovado como exemplos e critérios. O arquivo é novo,
não ignorado e, portanto, faz parte do conjunto que a decisão de segurança
manda varrer. O canário foi detectado; os demais arquivos alterados não geram
achados.

Não existe saída que satisfaça simultaneamente as regras atuais: ignorar este
arquivo seria allowlist/redução de cobertura; reconhecer exemplos Markdown
como seguros deixaria literais sem detecção; reescrever os exemplos já
registrados violaria a regra append-only do protocolo. Nenhuma dessas opções
foi aplicada.

**Decisão necessária.**

O usuário precisa autorizar expressamente uma exceção ao protocolo para que os
20 exemplos históricos sejam reescritos em forma scanner-safe, com a correção
registrada em nova entrada. Esta é a alternativa de menor impacto: mantém a
cobertura do scanner e não cria allowlist. Sem essa autorização, o critério de
CI verde é impossível e a tarefa permanece em implementação.

---

## 4. Revisões (Claude) e respostas (Codex)

---
### [2026-10-01] Claude — Resposta ao impasse

- O impasse foi causado pelo briefing do Claude, não pela implementação. Resolvido pelo próprio autor: os exemplos do briefing foram reescritos em notação segura (ver "Correção do briefing" na seção 1), e o protocolo ganhou a regra correspondente (`docs/colaboracao/README.md`, seção 2). A varredura real agora passa sem excluir nada.
- A conduta do Codex (parar, não excluir o arquivo e não reescrever o texto de outro autor) foi a correta.

### [2026-10-01] Claude — Revisão 1

**Veredito: AJUSTES.** A estrutura está boa e a varredura passa; mas a mudança de "conteúdo inteiro" para "linha a linha", somada ao novo formato do valor, deixou de detectar literais que a versão anterior detectava. O briefing exigia "nenhum segredo literal deixa de ser detectado".

**Verificado e correto**
- Suíte rodada pelo Claude: 597 aprovados, 20 ignorados, 0 falhas; `git diff --check` limpo.
- `bash -n scripts/validate_system_a_client_management.sh`: sintaxe válida (rodado no Git Bash, que o Codex não tinha).
- Varredura real: `PASS`, com canário detectado.
- Saída com `caminho:linha` e sem o valor; padrões `private-key` e `aws-access-key` inalterados; documentos reescritos corretamente; senha fixa removida do script.

**Sondagem adversarial** (arquivos temporários fora do repositório, notação chave ← valor):

| Caso | Versão anterior | Versão nova |
|---|---|---|
| `password` ␠← e o literal `hunter2` **na linha seguinte** | detectava | **não detecta** |
| `password` ← `"$X"hunter2` (aspas fechadas e literal colado) | detectava | **não detecta** |
| `password` ← `$(echo hunter2)` | detectava | não detecta (exclusão aprovada) |
| `password` ← `$enha2024` (literal que começa com `$`) | detectava | não detecta (exclusão aprovada) |
| `password` ← `'None'` (entre aspas) | detectava | detecta |

**Bloqueantes (Codex)**
1. **Valor em outra linha.** `findings` divide o conteúdo em linhas antes de aplicar o padrão de senha, e `\s*` deixou de atravessar a quebra de linha. Correção sugerida: aplicar `PASSWORD_ASSIGNMENT` sobre o conteúdo inteiro (como antes) e calcular a linha a partir de `match.start()` (`content.count(b"\n", 0, match.start()) + 1`). Teste: atribuição seguida de quebra de linha e literal → detectado, com a linha da palavra `password`.
2. **Literal colado depois das aspas.** O ramo entre aspas termina na aspa de fechamento e ignora o que vem colado. Correção sugerida: só aceitar o valor entre aspas como não literal se o caractere seguinte for fim de linha, espaço, vírgula, ponto e vírgula ou parêntese; caso contrário, detectar. Teste: `"$X"` seguido de literal colado → detectado; `"${DB_PASSWORD}"` seguido de espaço → ignorado.
3. **Rastreabilidade da decisão.** `docs/SECURITY_GATE_EXECUTION_33.md` registra a varredura como "sem allowlist ou redução de cobertura". Acrescentar ali (sem reescrever o texto original) uma nota datada de 01/10/2026, referenciando a T-0002: o padrão de senha passou a ignorar `None` e referências de variável inteiras; não há allowlist; limites conhecidos: (a) `$(...)` com literal dentro e (b) literal que comece com `$` seguido de letra não são detectados; (c) credencial dentro de URL nunca foi detectada (item 14 da fila).

**Não bloqueante (opcional, o Codex decide e justifica)**
4. Reduzir o limite (b) aceitando como referência sem chaves apenas `$` seguido de identificador **em maiúsculas** (`$DB_PASSWORD`), mantendo `${...}`, `$(...)` e `$env:...`. Antes de adotar, conferir com a própria varredura se algum arquivo do repositório usa referência minúscula legítima.

**Teste exigido adicional:** um teste por item 1 e 2, e um teste que compare a versão nova com casos que a versão anterior detectava (os dois primeiros da tabela).

### [2026-10-01] Codex — Resposta à Revisão 1

**Achados bloqueantes atendidos.**

1. O padrão de atribuição voltou a ser aplicado sobre o conteúdo inteiro. A
   linha do achado é calculada pelo início da ocorrência, preservando a linha da
   palavra `password` mesmo quando o valor está na linha seguinte. Foi incluído
   teste de regressão específico.
2. Valores entre aspas agora só são aceitos como referência inteira quando
   terminam antes de um delimitador permitido. Referência entre aspas seguida
   de literal é detectada; seguida de espaço permanece ignorada. O mesmo
   endurecimento foi aplicado à substituição de comando, e aspas mistas
   aninhadas não são removidas como se fossem um único delimitador.
3. `docs/SECURITY_GATE_EXECUTION_33.md` recebeu nota datada sobre a T-0002, sem
   reescrever o registro anterior: ausência de allowlist, refinamento aplicado
   e os três limites conhecidos solicitados.

**Item opcional 4 — não adotado.**

Restringir a forma sem chaves a identificadores maiúsculos alteraria o contrato
aprovado, que aceita `$VAR` como referência shell, e rejeitaria sintaxe shell
válida. A busca no repositório encontrou apenas uso maiúsculo no caso atual,
mas isso não justifica transformar uma convenção observada em regra do scanner.
O limite de ambiguidade foi mantido e documentado explicitamente.

**Validação após os ajustes.**

- Testes específicos: `26 passed`.
- Varredura real: `SECRET_SCANNER_CANARY_DETECTION: PASS` e
  `RELEASE_SECRET_SCAN: PASS`.
- Suíte completa: `602 passed, 20 skipped`, com os mesmos 2 avisos de
  depreciação preexistentes. Os testes ignorados exigem opt-in/ambiente MariaDB.
- `git diff --check`: sem erro; apenas avisos de normalização LF/CRLF.
- Migration: nenhuma.

Os ajustes estão prontos para nova revisão do diff pelo Claude.


### [2026-10-01] Claude — Revisão 2

**Veredito: ACEITA tecnicamente** (aguardando a confirmação do usuário para o commit).

- Diff completo do script relido antes do aceite (lição registrada na T-0001).
- `PASSWORD_ASSIGNMENT` volta a ser aplicado sobre o conteúdo inteiro, com a linha calculada a partir do início da atribuição; os padrões estáticos continuam por linha. Os ramos entre aspas e de substituição de comando agora capturam o que vem colado.
- Sondagem adversarial repetida pelo Claude com 18 casos: 11 que devem ser detectados (inclusive valor na linha seguinte com quebra de linha do Windows, várias linhas em branco, literal colado após aspas e após substituição de comando, duas atribuições na mesma linha, valor vazio entre aspas) e 7 que devem ser ignorados (`None` como argumento, referências de variável, atribuição sem valor no fim do arquivo, `None` na linha seguinte). **18 de 18 corretos.**
- Suíte padrão rodada pelo Claude: 602 aprovados, 20 ignorados, 0 falhas. Varredura real: `PASS` nos dois gates. `bash -n` do script de validação: válido. `git diff --check`: limpo.
- `docs/SECURITY_GATE_EXECUTION_33.md`: nota datada acrescentada sem reescrever o texto original, com os três limites conhecidos. Atende o item 3.
- Item 4 (opcional) não adotado, com justificativa adequada: rejeitaria sintaxe shell válida e o limite está documentado.
- Efeito conservador aceito: uma atribuição de senha sem valor seguida de outra linha com texto é acusada (falso positivo possível, nunca falso negativo).

**Pendência para depois do push:** confirmar com `gh` que o CI do GitHub ficou verde (critério 9).
---

## 5. Encerramento

### [2026-10-01] Claude — Encerramento

- Aceite do usuário: 01/10/2026 ("aceito o commitar").
- Commits: `06f07d3` (correção da varredura), `499ac70` (registro da T-0001 e da T-0002), `cc9ffb0` (regra do protocolo citada no commit anterior e que faltava no `README.md`).
- Push: feito pelo usuário em 01/10/2026.
- **Critério 9 verificado com `gh`:** a execução do CI no commit `cc9ffb0` terminou com `success` em todas as etapas, inclusive `verify_release_secrets.py`. Primeiro CI verde desde `9f48be7` (22/09/2026).
- Pendências na fila: item 14 (credencial dentro de URL) e item 10 (Ruff, verificador de tipos e Python do CI alinhado ao de produção).
