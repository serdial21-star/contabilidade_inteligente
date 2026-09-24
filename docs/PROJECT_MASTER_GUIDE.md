# Guia Mestre do Projeto — Serdial21 Contabilidade Inteligente

Última atualização: 2026-09-23.

## 1. Para que serve este documento

Este é o ponto de entrada único do projeto. Serve para que o projeto não se
perca entre sessões, entre ferramentas (Claude Code, Codex) e entre o tempo
que passa. Se você (Sergio) ou qualquer IA abrir uma sessão nova sem lembrar
de nada, a leitura de três arquivos resolve o problema:

1. `AGENTS.md` — as regras obrigatórias. Governam tudo; este guia nunca pode
   contradizê-las.
2. Este arquivo — onde o projeto está agora e o que vem a seguir.
3. `README.md` — como rodar e testar localmente.

Mantenha este arquivo atualizado sempre que uma fatia de trabalho fechar.
Isso é parte de terminar o trabalho, não um extra.

## 2. O que é o Serdial21, em poucas linhas

O Serdial21 é, na verdade, **dois sistemas que vão se conectar**:

- **Sistema A** — o Serdial21 original (React/Vite + n8n + MySQL na
  Hostinger). É o portal operacional e de relacionamento com o cliente:
  clientes, honorários, tickets, documentos, login de cliente/admin. Já
  existe e roda separadamente. O material de referência sobre ele está em
  `docs/integration-input/` (não é lixo nem sistema alheio — é o outro lado
  da integração). O código-fonte real (frontend Lovable/React + Edge
  Functions Supabase) está disponível localmente em
  `C:\Projetos\Sistema escritório\serdialconnect-hub-main` — **não é um
  repositório git** (é um snapshot exportado do Lovable), então editar
  arquivos ali não muda o sistema publicado. Para corrigir algo lá, o
  caminho comprovado é: ler o código nesse caminho para diagnosticar com
  precisão, gerar um prompt exato (arquivo/linha) e o Sergio cola no editor
  do Lovable. Todo esse acompanhamento vive no painel
  [Ponte Serdial21](https://claude.ai/artifact/LjQX5XMa72tcDCQF7qTH36).
- **Sistema B** — **é este repositório** (Python/FastAPI). É o motor de
  inteligência contábil: recebe documentos fiscais e bancários, classifica,
  propõe lançamentos, exige decisão humana, audita tudo. O sistema contábil
  externo (Domínio) continua sendo a autoridade da escrituração oficial;
  este sistema é autoridade sobre evidências, regras, propostas, workflow e
  auditoria do próprio processo.

Regra permanente: IA aqui é assistiva. Ela propõe e classifica; nunca aprova,
nunca escritura, nunca decide sozinha. Enquanto não houver aprovação
explícita para dados reais, **tudo é sintético** — não existe cliente real,
documento real nem exposição pública autorizada.

## 3. Estado atual — o que já está pronto

Em 2026-09-23 foi concluída uma preparação estritamente local para a futura
correlação com o Sistema A: `Company` no Sistema B agora pode guardar e ler a
tripla técnica opcional `external_system + external_type + external_id`. A
migration `20260923_0015` é aditiva e foi validada no Migration Lab MariaDB em
ciclo completo. A referência é única dentro do tenant e a leitura permanece
protegida por tenant, empresa e `CompanyAccess`. CNPJ não autoriza acesso.

Este incremento não inicia a Fase 10/10A: não existe conector, identidade M2M,
chamada de rede, sincronização, correlação automática por CNPJ nem dado real.
O gate formal de integração continua `NO_GO` pelos bloqueios restantes.

**Atualização posterior no mesmo dia (ADR 0013):** o usuário aprovou um import
**manual, offline e idempotente** de dados reais do Sistema A (empresas de
`clientes` e equipe interna de `funcionarios`), sem conexão ao vivo — o gate
`NO_GO` do Connect Hub não foi alterado. Isso incluiu a migration
`20260923_0016` (`office_team_members`, `company_team_assignments`, validada no
Migration Lab), os scripts `scripts/bootstrap_tenant.py`,
`scripts/import_sistema_a_companies.py` e `scripts/import_sistema_a_team.py`
(com `--dry-run`; nunca leem senha) e o roteiro
[LOCAL_REAL_DATA_IMPORT.md](LOCAL_REAL_DATA_IMPORT.md). O banco de
desenvolvimento `u621451815_serdial21_dev` foi recriado do zero e recebeu
1 tenant, 3 empresas e 7 membros da equipe. O shell do app também ganhou
sidebar recolhível e menu do usuário no rodapé. Pendências: login OIDC real
(sem provedor definido), vínculo membro↔login e padronização de CPF/CNPJ no
cadastro de clientes do Sistema A.

Fundação (autenticação OIDC, tenant/empresa, catálogo operacional, auditoria
transversal, importador de NF-e modelo 55) mais 14 fases numeradas concluídas
e commitadas, cobrindo: shell autenticado do app, Minha Visão, empresas e
Central de Documentos, módulos Fiscal e Financeiro, Inteligência Contábil
(propostas e revisão), arquitetura de integração com o Sistema A (fases 09A e
09B, só documental), Linha da Decisão, infraestrutura de segurança,
observabilidade e recuperação, privacidade/LGPD, e QA/UAT integrada.

Depois da fase 14, um incremento adicional — **Accounting Automation Core** —
foi fechado nesta semana: classificação determinística por item (não só por
documento), com evidências, confiança, histórico reutilizável, mapeamento
para propostas mistas. Isso incluiu:

- migration `20260916_0014` — **validada em MariaDB real** (11.8.9), ciclo
  completo `upgrade → downgrade → upgrade` sem erro;
- API HTTP de revisão por item (`/item-classifications` e `/decide`);
- UI da fila de revisão no app (aba "Itens pendentes" em Contábil);
- testes automatizados cobrindo tudo isso.

Suíte de testes local: **483 passed**, 20 skipped (só os que exigem MariaDB
real com opt-in explícito — e esses agora também passam quando habilitados).

O que ainda falta **dentro** dessa fatia, sem virar fase nova: UI de cadastro
de `CompanyAccountingProfile`/CNAE (hoje só existe por seed direto no banco)
e vincular a permissão `accounting.classification.review` a um papel real —
isso só faz sentido depois de existir um IdP real (item 5).

## 4. O que vem a seguir, segundo o roadmap já aprovado

O projeto tem dois documentos de planejamento diferentes; o que reflete a
realidade do que foi construído é `docs/PRODUCT_BACKLOG.md` +
`docs/PRODUCTIZATION_ROADMAP.md` (o outro, `docs/engenharia-produto/14-*`,
é um plano metodológico anterior, útil como referência de princípios, não
como rastreador vivo).

A sequência aprovada é: 01→02→03→04→05→06→07→08→09A→09→10→10A→11→12→13→14→
15→16. Tudo até 09B e 11–14 está feito. **A próxima fase numerada ainda não
iniciada é a Fase 10 — Portal & Operations Integration**, seguida da Fase
10A — Connect Hub MVP: conectar de fato o Sistema A e o Sistema B, reusando
o portal do Sistema A em vez de construir um segundo portal.

Importante, e é regra do próprio projeto, não invenção minha: **terminar
uma fase nunca autoriza a próxima automaticamente**. Cada fase exige pedido
explícito seu.

**Atualização de 2026-09-23**: a Fase 10A (Connect Hub) já tem trabalho real
em andamento, fora deste repositório — correções de segurança no Sistema A
(login sem senha, acesso liberado por padrão, funções sem autenticação) já
aplicadas, backend n8n revisado. O acompanhamento dia a dia disso vive num
painel próprio, não neste repositório:
[Ponte Serdial21](https://claude.ai/artifact/LjQX5XMa72tcDCQF7qTH36) — abra
esse link para ver o checklist completo e o estado exato de cada item.

Mas o gate formal continua **NO_GO**: `docs/integration/SYSTEM_A_INTEGRATION_READINESS_GATE.md`
diz literalmente "Não iniciar Connect Hub, Phase 10 ou conexão com o Sistema
B". Seis bloqueios confirmados (nenhum é código do Sistema B): contratos do
n8n não congelados, nenhuma credencial própria entre os dois sistemas,
documentos do Drive com link permanente em vez de temporário, idempotência
de reenvio não demonstrada, nenhum ambiente de homologação isolado, e um
achado sensível — o Sistema A grava o corpo completo de requisições de
honorários/impostos/tarefas/documentos em log. Não vou escrever código de
Connect Hub até isso fechar; detalhes e ordem sugerida no item "2-2" do
painel acima.

## 5. Os bloqueios reais para produção não são de código

Isso é o ponto mais importante deste guia. Mesmo terminando a Fase 10, o
projeto **não pode** ir para piloto com dado real nem exposição externa sem
quatro decisões que só você pode tomar, mais infraestrutura que precisa ser
provisionada:

1. **IdP real** — hoje não existe nenhum provedor de login configurado
   (`docs/OIDC_CONFIGURATION.md` é explícito: "Nenhum IdP está configurado
   no repositório"). É preciso escolher um (ex.: Auth0, Keycloak, Microsoft
   Entra ID) — decisão com custo e implicações, não vou escolher por você.
2. **Aprovação do responsável pelo produto** para autorizar corpus real
   (`AUTHORIZED_REAL_CORPUS`).
3. **Aprovação de um contador responsável** revisando o motor determinístico
   (`ACCOUNTANT_SIGNOFF`).
4. **Aprovação jurídica/privacidade** (`LEGAL_APPROVAL`) — ainda não há base
   legal nem prazo de retenção aprovados para dado real.

Além disso: exposição externa exige HTTPS/reverse proxy real, rate limit
distribuído, alertas de verdade; a integração com o Domínio Sistemas
continua bloqueada até homologação com arquivo padrão real; CT-e e NFS-e
ainda não foram implementados (só NF-e modelo 55 existe hoje).

Veredito hoje, conforme `docs/PILOT_GO_NO_GO.md`: piloto interno **sintético
é GO**; piloto com dado real é **NO_GO**; exposição externa é **NO_GO**. Note
que esse documento é de antes do incremento desta semana — vale a pena
atualizá-lo, mas o veredito de fundo (sintético sim, real não, externo não)
continua valendo.

## 6. Como o trabalho funciona: você + duas IAs

Você é dono do produto **e** desenvolvedor solo — não existe "escritório"
pedindo aprovação separada. Toda vez que o `AGENTS.md` pede "aprovação
explícita", essa aprovação é sua. Em troca, toda ação manual (SQL, painel de
hospedagem, configuração de infraestrutura) precisa vir de mim com passo a
passo numerado e literal — nunca vou assumir que você sabe o próximo clique.

Duas ferramentas de IA disponíveis, e as duas leem o `AGENTS.md` deste
repositório como regra obrigatória, então não se contradizem mesmo em
sessões separadas:

- **Claude Code** (esta sessão) — quem já tem o contexto completo da
  conversa, fez a maior parte do trabalho recente, e pode rodar
  `/code-review ultra` (revisão multi-agente na nuvem) antes de qualquer
  mudança arriscada.
- **Codex** (CLI da OpenAI) — útil como segunda opinião independente: pedir
  para revisar um diff que o Claude Code fez, ou tocar um módulo isolado em
  paralelo enquanto o Claude Code cuida de outro.

Padrão recomendado para você, sozinho e sem tempo de orquestrar duas IAs a
fundo: use **uma ferramenta por vez como responsável principal** de cada
fatia de trabalho (normalmente esta sessão, já que o contexto já está aqui).
Peça à outra uma revisão independente antes de aprovar algo importante —
custa poucos minutos e pega erro que uma sessão sozinha não veria.

## 7. Prompt mestre — para colar numa sessão nova (Claude ou Codex)

Use isto sempre que abrir uma sessão nova e ela não tiver este histórico:

```text
Você está trabalhando no repositório Serdial21 Contabilidade Inteligente
(C:\Projetos\Sistema-Contabilidade-Inteligente). Antes de qualquer coisa:

1. Leia AGENTS.md na raiz — regras obrigatórias, não podem ser enfraquecidas.
2. Leia docs/PROJECT_MASTER_GUIDE.md — estado atual e o que vem a seguir.
3. Leia README.md — como rodar e testar localmente.

O responsável pelo projeto é o Sergio: dono do produto E desenvolvedor solo,
sem formação técnica profunda. Ele aprova tudo sozinho (não existe
"escritório" separado pedindo aprovação), mas precisa de explicações simples
e passo a passo/clique a clique para qualquer ação manual fora do código
(SQL, painel de hospedagem, configuração de infraestrutura) — nunca assuma
que ele sabe o próximo passo sem explicação.

Regras de trabalho: implemente a menor mudança suficiente para a tarefa
pedida, não avance para fase ou fatia seguinte sem pedido explícito dele,
rode os testes relacionados e a suíte completa quando viável, e ao concluir
liste arquivos criados/alterados, testes rodados (aprovados/ignorados/
falhas), decisões técnicas tomadas e pendências — processo completo no
AGENTS.md §7.

Tarefa desta sessão: <descreva aqui o que você quer>
```

## 8. Como ver o sistema funcionando agora mesmo

Não precisa de banco, login nem internet. Passo a passo:

1. Abra a pasta do projeto no Explorador de Arquivos do Windows.
2. Dê dois cliques em `INICIAR_SERDIAL21.cmd`.
3. Uma janela preta (terminal) abre; em poucos segundos o navegador abre
   sozinho em `http://127.0.0.1:8080/app/`. Se não abrir sozinho, copie esse
   endereço e cole no navegador.
4. Na tela inicial, clique em **"Abrir demonstração sintética"**.
5. No menu lateral, clique em **Contábil**.
6. Clique na aba **Itens pendentes** — é a fila de revisão por item que
   fechamos nesta semana.
7. Para encerrar: feche a janela preta ou pressione `Ctrl+C` nela.

Tudo aqui é fictício (identidade, empresas, documentos). Nenhum dado é
persistido, nenhuma API real é chamada. É o caminho padrão para validar
interface e fluxo até existir IdP real.

## 9. Como decidimos o próximo passo concreto a partir de agora

Não vou empilhar decisões grandes sem te consultar. A cada fatia fechada,
volto com no máximo 2–3 opções concretas (não uma lista aberta) e um
próximo passo pequeno e seguro já pronto para rodar. Prioridades sugeridas,
da mais barata/segura para a mais cara, para você escolher:

- **Barato e seguro**: atualizar `docs/PILOT_READINESS.md` e
  `docs/PILOT_GO_NO_GO.md` para refletir o incremento desta semana (são só
  documentos, zero risco).
- **Fecha a fatia atual de vez**: UI de cadastro de `CompanyAccountingProfile`
  (hoje só existe via seed direto no banco) — sem isso, a fila de
  classificação nunca tem empresa configurada fora de teste.
- **Decisão sua antes de qualquer código**: escolher um provedor de IdP,
  para destravar homologação real e, mais adiante, qualquer piloto.
- **Fase nova, precisa de conversa de escopo antes**: Fase 10 (Portal &
  Operations Integration) — depende de acesso e entendimento do Sistema A.

Este guia deve ser atualizado toda vez que fecharmos uma fatia. Se algo
aqui estiver desatualizado, isso é bug — me avise ou eu mesmo corrijo ao
concluir a próxima tarefa.
