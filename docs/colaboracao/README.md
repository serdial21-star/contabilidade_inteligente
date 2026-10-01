# Protocolo de colaboração — Usuário, Claude e Codex

**Vigência:** a partir de 01/10/2026.
**Escopo:** todo trabalho de desenvolvimento neste repositório conduzido em conjunto por Claude (Claude Code) e Codex.
**Autoridade:** subordinado ao `AGENTS.md`. Este protocolo organiza o trabalho; não amplia autorizações, não dispensa ADR e não enfraquece nenhuma regra de segurança, isolamento, auditoria ou governança.

---

## 1. Papéis

| Papel | Quem | Faz | Não faz |
|---|---|---|---|
| **Dono do produto e decisor** | Usuário | Escolhe prioridades; aprova o briefing antes da codificação; decide impasses; executa ações fora do repositório (Sistema A/Lovable, n8n, Supabase, phpMyAdmin, VPS, deploy); faz o `push`. | Não precisa escrever código. |
| **Arquiteto e revisor** | Claude | Lê a documentação e o código; escreve o briefing da tarefa (problema, referências, critérios de aceite, testes exigidos); redige ADRs quando necessários; convoca rodadas de especialistas; revisa o que o Codex entregou; faz o commit local depois do aceite. | Não implementa código de produção enquanto houver tarefa atribuída ao Codex; não edita arquivos que o Codex esteja alterando. |
| **Implementador** | Codex | Lê o briefing; implementa a menor alteração suficiente; escreve os testes; roda a suíte; registra o relatório de implementação no arquivo da tarefa; responde às revisões. | Não muda o escopo sem registrar; não commita; não faz `push`; não executa nada contra banco, API ou serviço real. |

## 2. Canal de comunicação: o arquivo da tarefa

Claude e Codex **não conversam em tempo real**. Cada um só age quando o usuário o aciona. A conversa acontece por escrito, dentro de um arquivo por tarefa:

```
docs/colaboracao/
├── README.md            ← este protocolo
├── QUADRO.md            ← painel com todas as tarefas e o estado de cada uma
├── REFERENCIAS.md       ← normas e fontes já citadas, ausentes e decisões sem fonte
├── _MODELO_TAREFA.md    ← modelo usado para abrir uma tarefa nova
└── tarefas/
    └── T-NNNN-titulo-curto.md   ← briefing, implementação, revisões e decisões
```

Regras do arquivo da tarefa:

- **Só acrescentar, nunca reescrever.** Cada agente escreve na sua seção e acrescenta novas rodadas abaixo das anteriores. Correção de algo já escrito é feita com uma nova entrada que referencia a anterior.
- Cada entrada começa com `### [AAAA-MM-DD] Autor — tipo` (Briefing, Implementação, Revisão, Resposta, Decisão do usuário).
- O que o usuário disser no chat que seja decisão é transcrito por quem estiver atendendo na seção **Decisões do usuário**, com a data.
- Nada de segredos, tokens, senhas, CPF/CNPJ reais ou dados pessoais no arquivo.
- Exemplos que disparariam a varredura de segredos (`scripts/verify_release_secrets.py`) — atribuição de senha, marcador PEM de chave privada, chave AWS — são escritos em notação segura: **chave ← valor** no lugar do sinal de igual, e marcadores descritos em palavras. Os arquivos de tarefa são versionados e varridos como qualquer outro.
- Exceção ao append-only: somente o autor de uma entrada pode reescrevê-la, e somente para retirar conteúdo que dispare a varredura ou que seja sensível, registrando a correção numa entrada nova logo abaixo.
- O histórico de commits (`git log`) é o registro do código; o arquivo da tarefa é o registro do raciocínio.

## 3. Ciclo de uma tarefa

```
RASCUNHO ──(usuário aprova)──► APROVADA ──(Codex inicia)──► EM_IMPLEMENTAÇÃO
   ▲                                                              │
   │                                                              ▼
CANCELADA                    AJUSTES ◄──(Claude reprova)── EM_REVISÃO
                                │                                 │
                                └──(Codex corrige)──► EM_REVISÃO  │
                                                                  ▼
                                    CONCLUÍDA ◄──(commit)── ACEITA (Claude + usuário)
```

1. **RASCUNHO** — Claude escreve o briefing. Se a tarefa cruza decisão já aprovada (ADR, gate, produção), o ADR é redigido aqui, antes de qualquer código.
2. **APROVADA** — o usuário lê o briefing e diz "aprovado". Sem isso o Codex não começa.
3. **EM_IMPLEMENTAÇÃO** — o Codex implementa e preenche o relatório (arquivos, testes, decisões, dúvidas).
4. **EM_REVISÃO** — Claude revisa o diff real (não o relatório), roda os testes, aplica o agente `cacador-de-bugs` quando o risco justificar e registra os achados.
5. **AJUSTES** — se houver achado bloqueante, volta ao Codex. O Codex pode **contestar** um achado com evidência; impasse vai ao usuário.
6. **ACEITA** — Claude aprova tecnicamente e o usuário confirma.
7. **CONCLUÍDA** — imediatamente antes do commit, Claude relê o diff completo do código de produção (não só os pontos da revisão anterior) e confere que nada mudou desde o aceite. Depois, Claude faz o commit local (uma tarefa por commit, ou commits pequenos e coesos), atualiza o QUADRO e informa; o usuário faz o `push`.

**Uma tarefa em implementação por vez** na mesma árvore de trabalho, para que o diff de uma não se misture com o de outra.

## 4. O que o usuário faz (e só isso)

| Momento | Ação do usuário | Frase sugerida |
|---|---|---|
| Escolher o próximo trabalho | Dizer ao Claude o que quer, ou aceitar a sugestão | "Claude, abra a tarefa para X" |
| Aprovar o briefing | Ler a seção Briefing e aprovar ou pedir mudança | "Claude, aprovado T-0002" |
| Acionar o Codex | Colar no Codex | `Execute a tarefa T-0002 conforme docs/colaboracao/README.md` |
| Pedir revisão | Avisar o Claude quando o Codex terminar | "Claude, revise a T-0002" |
| Devolver ajustes ao Codex | Colar no Codex | `Atenda a revisão mais recente da T-0002` |
| Desempatar | Escolher quando Claude e Codex discordam | resposta livre |
| Aceitar e publicar | Confirmar o aceite; depois fazer `git push` | "Claude, aceito T-0002, pode commitar" |
| Ações externas | Executar o que o briefing marcar como **[AÇÃO DO USUÁRIO]** (Lovable, n8n, phpMyAdmin, VPS) | — |

Quando uma tarefa exigir algo do usuário, o briefing terá uma seção **Ações do usuário** com passo a passo, onde clicar e o que conferir. Se essa seção estiver vazia, o usuário só aprova e repassa.

## 5. Regras de postura (valem para Claude e Codex)

1. **Sem elogio protocolar.** Não abrir resposta com "ótimo trabalho", "excelente ideia" ou equivalente. Reconhecer acerto só quando for informação útil (ex.: "esta parte foi verificada e está correta").
2. **Crítica direta e fundamentada.** Se o pedido, o briefing ou o código estiver errado, incompleto ou arriscado, dizer isso claramente, com o motivo e a alternativa. Isso vale também para pedidos do usuário e para o trabalho do outro agente.
3. **Discordar é obrigatório quando houver evidência.** Concordar para evitar atrito é falha. A discordância é registrada no arquivo da tarefa e decidida com base em evidência ou pelo usuário.
4. **Evidência antes de afirmação.** Ler o código, o schema ou a documentação antes de afirmar como algo funciona. Quando não for possível verificar, declarar a incerteza.
5. **Qualidade acima de velocidade.** Tarefa pequena, testada e revisada vale mais que tarefa grande entregue de uma vez.

## 6. Regra de referências normativas: consultar antes de criar

Antes de definir qualquer regra de negócio, validação, cálculo, leiaute, prazo, retenção ou controle de segurança:

1. **Procurar a fonte existente**, nesta ordem:
   - legislação e normas oficiais (ex.: LGPD — Lei 13.709/2018; Instruções Normativas da RFB; Ajustes SINIEF/CONFAZ; NBC/CPC/ITG do CFC);
   - manuais e especificações oficiais (ex.: Manual de Orientação do Contribuinte da NF-e e Notas Técnicas; leiautes SPED; especificação OFX; leiaute de importação do sistema contábil externo);
   - padrões técnicos reconhecidos (ex.: RFC 7519/7517 para JWT/JWKS, OpenID Connect Core, OWASP ASVS);
   - decisões e documentos internos já aprovados (`AGENTS.md`, `docs/adr/`, especificações em `docs/`).
2. **Se a fonte existe, segui-la e citá-la** no briefing e, quando útil, no código ou no teste (norma, artigo/seção, versão). Não reinventar o que já está definido.
3. **Se nenhuma fonte for encontrada, não inventar.** Registrar "sem referência encontrada", descrever a lacuna e levá-la ao usuário como decisão ou pendência. Isso é especialmente obrigatório para regra contábil e fiscal (`AGENTS.md`, seções 6.2 e 9).
4. **Versão importa.** Normas fiscais mudam (ex.: Notas Técnicas da NF-e). Registrar a versão ou a data da fonte usada; se a versão vigente não puder ser confirmada, declarar isso.

Todo briefing tem uma seção **Referências** com o que foi consultado e o que não foi encontrado.

## 7. Rodadas de especialistas

Claude pode convocar especialistas (subagentes) quando o risco justificar:

- **no briefing:** arquitetura, segurança, fiscal/contábil, dados — para revisar o plano antes da codificação;
- **na revisão:** o agente `cacador-de-bugs` (`.claude/agents/cacador-de-bugs.md`) sobre o diff;
- **revisão cruzada:** em tarefa crítica, o relatório de achados do Claude vai ao Codex com o pedido "tente refutar cada achado lendo o código", e vice-versa. O que sobreviver às duas leituras é tratado como defeito real.

O resultado de cada rodada é resumido no arquivo da tarefa (não colado na íntegra).

## 8. Limites que nenhum dos dois agentes ultrapassa

- Nunca abrir, imprimir ou copiar `.env`, `.env.*` (exceto `.env.example`) nem `local_data/`.
- Nunca executar comando contra banco, API, n8n, Supabase ou VPS reais. Quando a tarefa precisar disso, vira **[AÇÃO DO USUÁRIO]** com instruções.
- Nunca fazer `push`, `reset`, `checkout` de arquivos alheios, `stash` ou reescrita de histórico.
- Não avançar para a próxima tarefa ou fase sem pedido do usuário.
- Mudanças em decisão aprovada seguem a seção 1 do `AGENTS.md` (impacto, alternativas, aprovação, ADR).
