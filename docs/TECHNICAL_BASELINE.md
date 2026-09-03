# Serdial21 — Technical Baseline

| Controle | Valor |
|---|---|
| Execução | 01 — Auditoria da Base Atual |
| Data da auditoria | 03/09/2026 |
| Diretório auditado | Raiz do projeto Serdial21 Contabilidade Inteligente |
| Estado encontrado | **Base exclusivamente documental; aplicação ainda não implementada** |
| Alteração funcional nesta execução | Nenhuma |

## 1. Conclusão executiva

O diretório atual ainda não contém uma aplicação executável nem um repositório Git inicializado. A base é composta pelo AGENTS.md e por sete documentos de engenharia de produto.

Não existem código Python, FastAPI, configuração, manifestos de dependências, models SQLAlchemy, schemas Pydantic, rotas, migrations Alembic, testes, arquivo de ambiente de exemplo, configuração do VS Code ou infraestrutura local do MySQL.

Portanto:

- não há funcionalidade de aplicação disponível para iniciar ou preservar;
- não há regressão funcional identificável;
- não é possível executar suíte Pytest ou teste de inicialização;
- criar a aplicação nesta execução ultrapassaria o escopo de auditoria e iniciaria uma fase posterior;
- nenhuma correção funcional foi realizada.

A documentação aprovada fornece uma base de produto e arquitetura forte, mas ainda precisa ser transformada em uma fundação técnica reproduzível antes dos módulos de negócio.

## 2. Escopo e método da auditoria

Foram verificados:

- instruções permanentes em AGENTS.md;
- todos os arquivos existentes sob docs;
- estrutura e arquivos ocultos da raiz;
- existência de README, Git, manifests, ambiente, configuração e VS Code;
- existência de código Python, FastAPI, SQLAlchemy, models, Pydantic e rotas;
- existência de Alembic, migrations e SQL;
- existência de testes;
- ferramentas e dependências instaladas no ambiente local;
- consistência básica da documentação, links relativos e blocos Markdown;
- divergências entre decisões documentadas e a stack agora definida.

Nenhum arquivo de código foi encontrado. Não houve banco, serviço ou endpoint que pudesse ser inspecionado em execução.

## 3. Estrutura atual

Estrutura observada:

~~~text
/
├── AGENTS.md
└── docs/
    └── engenharia-produto/
        ├── 00-indice-e-rastreabilidade.md
        ├── 01-fase-visao-e-escopo.md
        ├── 02-03-arquitetura-macro-e-dominios.md
        ├── 04-modelo-dados-conceitual-logico.md
        ├── 10-arquitetura-modular-python.md
        ├── 14-backlog-tecnico-mvp.md
        └── 15-cronograma-desenvolvimento-mvp.md
~~~

Inventário:

| Artefato | Situação |
|---|---|
| AGENTS.md | Presente; instruções permanentes da stack, arquitetura, segurança e processo |
| Documentação de engenharia | Presente; sete arquivos, 2.547 linhas no total antes deste baseline |
| README.md | Ausente |
| Repositório Git local | Ausente; o diretório não possui .git |
| pyproject.toml | Ausente |
| requirements.txt / requirements-dev.txt | Ausentes |
| Arquivo de lock de dependências | Ausente |
| .python-version | Ausente |
| Ambiente virtual do projeto | Não identificado |
| .gitignore | Ausente |
| .env | Ausente, como esperado |
| .env.example | Ausente |
| .vscode | Ausente |
| src ou app | Ausentes |
| tests | Ausente |
| alembic.ini | Ausente |
| alembic ou migrations | Ausentes |
| Dockerfile / Compose | Ausentes |
| Arquivos Python | 0 |
| Arquivos SQL | 0 |
| Arquivos TOML/INI/YAML/JSON | 0 |

## 4. Ambiente local observado

| Componente | Situação observada | Avaliação |
|---|---|---|
| Python | 3.13.14 | Compatível com a regra Python 3.12+, mas a versão do projeto não está fixada |
| pip | 26.1.2 | Disponível no Python global/WindowsApps; não prova ambiente isolado |
| Git | 2.53.0.windows.2 | Ferramenta instalada, porém o diretório não é repositório |
| VS Code | 1.136.0, x64 | Instalado |
| Cliente mysql | Não encontrado no PATH | Servidor, cliente e versão de MySQL não puderam ser validados |
| FastAPI | Não instalado | Dependência e aplicação ausentes |
| SQLAlchemy | Não instalado | Dependência, sessão, engine e models ausentes |
| Alembic | Não instalado | Dependência e ambiente de migrations ausentes |
| PyMySQL | Não instalado | Driver MySQL ausente |
| Pydantic | Não instalado | Contratos de dados ausentes |
| Pydantic Settings | Não instalado | Configuração tipada ausente |
| Pytest | Não instalado | Suíte e runner ausentes |

O ambiente global não deve ser tratado como ambiente do projeto. As versões precisam ser declaradas e instaladas de modo reproduzível em ambiente virtual antes da primeira implementação.

## 5. Funcionalidades existentes

### 5.1 Funcionalidades executáveis

Nenhuma.

Não existem:

- processo FastAPI;
- endpoint de saúde;
- configuração carregável;
- conexão MySQL;
- model ou tabela;
- migration;
- comando de aplicação;
- autenticação ou autorização;
- processamento tenant-aware;
- teste automatizado.

### 5.2 Capacidades documentadas

A documentação já define:

- visão e fronteira do MVP como camada inteligente integrada;
- sistema contábil externo como autoridade da escrituração oficial;
- Serdial21 como autoridade de documentos, canônico, regras, propostas, workflow, integrações e auditoria;
- monólito modular com portas e adaptadores;
- modelo lógico, entidades, estados, versionamento e invariantes;
- isolamento tenant e company;
- pré-ledger canônico;
- M19 — Workflow, Pendências e Aprovações;
- auditoria atômica/append-oriented, inbox e outbox;
- regras determinísticas e IA consultiva;
- backlog S0–S8;
- escopo NF-e, CT-e, NFS-e nacional, OFX, CSV e Domínio;
- cronograma proposto;
- instruções permanentes de desenvolvimento.

Essas capacidades são especificações; nenhuma está implementada.

## 6. Estado por camada técnica

| Camada | Estado | Evidência ou lacuna |
|---|---|---|
| Empacotamento Python | Inexistente | Sem pyproject.toml, package ou versão de distribuição |
| FastAPI | Inexistente | Sem app factory, lifespan, middleware, dependencies ou rotas |
| Configuração | Inexistente | Sem Settings, profiles, .env.example ou validação |
| SQLAlchemy | Inexistente | Sem registry/base, engine, session, repositories ou models |
| MySQL | Não verificável | Cliente ausente; sem URL, container, schema ou política de versão |
| Alembic | Inexistente | Sem alembic.ini, env.py ou revisions |
| Domínio | Apenas documentado | Sem entidades, value objects, políticas ou serviços |
| Schemas Pydantic | Inexistentes | Sem contratos de API/comandos/eventos |
| Rotas/API | Inexistentes | Sem endpoints ou OpenAPI |
| Segurança | Apenas documentada | Sem identidade, ExecutionContext, CompanyAccess ou testes |
| Auditoria | Apenas documentada | Sem persistência ou comportamento append-oriented executável |
| Testes | Inexistentes | Sem tests e sem Pytest instalado |
| Observabilidade | Inexistente | Sem logs estruturados, métricas ou correlação executável |
| CI/CD | Inexistente | Sem configuração de pipeline |
| Documentação operacional | Inexistente | Sem README, setup, comandos, runbook ou troubleshooting |

## 7. Inconsistências entre documentação e base atual

### 7.1 Stack definida versus decisões tecnológicas pendentes

O AGENTS.md agora fixa:

- Python 3.12+;
- FastAPI;
- SQLAlchemy 2.x;
- Alembic;
- MySQL;
- PyMySQL;
- Pydantic 2;
- Pydantic Settings;
- Pytest.

Entretanto, documentos anteriores ainda registram framework web, ORM, migrations e SGBD como decisões pendentes:

- 02-03-arquitetura-macro-e-dominios.md, seções 1 e 12;
- 04-modelo-dados-conceitual-logico.md, seções 2, 9 e 10;
- 10-arquitetura-modular-python.md, seção 11;
- 00-indice-e-rastreabilidade.md e 15-cronograma-desenvolvimento-mvp.md, referências à DEC-011/G0.

Interpretação recomendada: a instrução mais recente selecionou a stack de aplicação, mas a DEC-011 está apenas parcialmente resolvida. Ainda faltam, entre outros:

- versão suportada do MySQL;
- estratégia física de isolamento tenant;
- storage de artefatos;
- execução de jobs/outbox;
- identidade e secrets;
- observabilidade;
- deploy e ambientes;
- provedor e política de IA.

Os documentos aprovados não foram alterados nesta auditoria.

### 7.2 Nomes dos domínios

O AGENTS.md determina os domínios previstos identity, tenancy, companies, master_data, chart_of_accounts, accounting, rules, documents, imports, reconciliation, locks, workflow, integrations, audit, ai e reporting.

A arquitetura aprovada usa nomes e recortes diferentes, por exemplo access_control, company_registry, intake_documents, fiscal_documents, banking, accounting_rules, accounting_core, accounting_controls, workflow_m19, integration_hub, audit_governance e operations.

Isso não é necessariamente conflito conceitual, mas é uma ambiguidade de ownership e nomenclatura que deve ser resolvida antes do scaffold. É necessário publicar um mapa um-para-um ou aprovar uma convenção única, sem perder os bounded contexts aprovados.

### 7.3 Estado histórico da autorização

Alguns documentos mantêm rótulos históricos como “sem código de produção” ou “não autoriza código”. O índice registra autorização posterior para iniciar o aplicativo em 03/09/2026, e a solicitação atual inicia apenas a auditoria.

Os textos históricos podem permanecer como registro da fase, mas um README futuro deve indicar claramente qual baseline está vigente para evitar interpretações contraditórias.

### 7.4 Cronograma e dependências de gate

O cronograma v0.2 fornece previsão condicionada, enquanto o backlog informa que estimativas dependem das decisões DEC-001 a DEC-010 e da equipe.

Não há contradição se o cronograma for tratado como cenário, mas faltam evidências atuais sobre:

- equipe executora;
- empresas e usuários do piloto;
- pico e tamanho dos lotes;
- volume de transações bancárias;
- corpus autorizado;
- layout/golden file Domínio;
- precisão, tolerância, alçadas, retenção, RPO e RTO.

## 8. Dívida técnica identificada

Como ainda não há código, a dívida é predominantemente de fundação.

| Prioridade | Dívida/lacuna | Consequência |
|---|---|---|
| Crítica | Diretório sem Git | Sem histórico, revisão, branch, recuperação ou atribuição confiável de mudanças |
| Crítica | Aplicação e testes inexistentes | Não existe baseline executável nem mecanismo de regressão |
| Alta | Sem manifesto/lock de dependências | Ambiente não reproduzível e risco de versões incompatíveis |
| Alta | Sem convenção única de domínios/pacotes | Risco de scaffold incompatível com a arquitetura aprovada |
| Alta | Estratégia MySQL tenant-aware não definida | Risco de confiar apenas em filtros de aplicação |
| Alta | Sem configuração tipada e política de secrets | Risco de credencial em código ou configuração inconsistente |
| Alta | Sem Alembic e migrations iniciais | Schema não reproduzível e risco de alteração manual |
| Alta | Sem CI e quality gates | Falhas arquiteturais, de teste e segurança não bloqueiam mudança |
| Alta | Sem README e comandos operacionais | Setup não repetível para novo desenvolvedor/agente |
| Média | Python local 3.13 sem versão do projeto | Compatibilidade mínima 3.12 não é testada |
| Média | MySQL não disponível/validado | Integração, dialect e migrations não podem ser testados |
| Média | Sem .gitignore e .env.example | Risco de versionar artefatos e segredos quando Git for iniciado |
| Média | Sem configuração do VS Code | Experiência local e comandos não são padronizados |

## 9. Riscos

### 9.1 Riscos imediatos

1. **Perda ou sobrescrita de trabalho:** não há controle de versão no diretório.
2. **Falsa sensação de implementação:** a documentação é extensa, mas nenhuma capacidade está executável.
3. **Deriva arquitetural:** os dois conjuntos de nomes de domínio podem produzir módulos duplicados ou ownership ambíguo.
4. **Dependências não reproduzíveis:** instalar pacotes globalmente criaria uma base difícil de repetir.
5. **Isolamento incompleto:** MySQL foi selecionado, mas ainda não existe desenho físico tenant/company nem suíte negativa.
6. **Migração manual:** sem Alembic, o primeiro schema pode nascer fora do processo obrigatório.
7. **Exposição de segredo:** sem Settings, .env.example e .gitignore, a futura configuração pode ser tratada de forma insegura.
8. **Cronograma sem capacidade confirmada:** equipe, fixtures e fornecedor ainda podem alterar as datas.

### 9.2 Riscos que não devem ser “resolvidos” por atalhos

- usar SQLite e assumir compatibilidade com MySQL;
- usar create_all como migration;
- criar filtros tenant ad hoc por endpoint;
- misturar ORM, schemas de API e entidades de domínio;
- instalar dependências sem manifesto e política de versão;
- criar todos os domínios previstos antes da primeira fatia;
- implementar IA antes do fluxo determinístico;
- inventar regra contábil para produzir uma demonstração;
- declarar conector Domínio sem layout e golden file homologados.

## 10. Dependências ausentes

Dependências obrigatórias declaradas e não instaladas:

| Dependência | Estado |
|---|---|
| FastAPI | Ausente |
| SQLAlchemy | Ausente |
| Alembic | Ausente |
| PyMySQL | Ausente |
| Pydantic | Ausente |
| Pydantic Settings | Ausente |
| Pytest | Ausente |

Também não há manifesto que determine faixas ou versões. A auditoria não instalou pacotes nem consultou índices externos.

Antes da instalação, deve ser decidido:

- ferramenta de empacotamento e lock;
- faixas de versão;
- separação entre dependências de runtime e desenvolvimento;
- política de atualização e vulnerabilidades;
- compatibilidade testada em Python 3.12 e 3.13;
- versão do MySQL suportada.

## 11. Itens que precisam ser corrigidos antes da evolução

### Bloqueadores da primeira aplicação executável

1. inicializar ou associar o diretório a um repositório Git;
2. aprovar a convenção de nomes e o mapa entre domínios;
3. registrar ADR da stack agora selecionada e pendências restantes da DEC-011;
4. criar README com setup, comandos, arquitetura e estado real;
5. criar pyproject.toml e lock reproduzível;
6. definir versões Python/MySQL suportadas;
7. criar .gitignore antes de qualquer segredo ou ambiente virtual;
8. criar .env.example sem valores reais;
9. criar o scaffold mínimo do monólito modular, sem antecipar módulos;
10. criar Settings tipado e validação fail-fast;
11. criar FastAPI por application factory/lifespan e endpoint de health;
12. criar engine/session SQLAlchemy 2.x com limites transacionais claros;
13. inicializar Alembic antes do primeiro model/tabela;
14. preparar MySQL de desenvolvimento/teste;
15. criar Pytest, testes de arquitetura e primeiro teste de inicialização;
16. configurar CI para executar lint/type-check/test/migrations conforme ferramentas aprovadas.

### Decisões ainda necessárias

- ID interno e representação no MySQL;
- precisão/escala monetária e arredondamento;
- convenção de timestamps UTC no MySQL;
- estratégia de chave/FK composta tenant/company;
- isolamento de testes e banco por ambiente;
- storage dos artefatos imutáveis;
- jobs/outbox sem antecipar broker desnecessário;
- autenticação, autorização e secrets;
- padrão de logs estruturados, correlation_id e minimização;
- política de versionamento dos contratos internos e eventos.

## 12. Plano incremental recomendado

O próximo trabalho deve continuar em fatias e não iniciar módulos contábeis.

### Etapa A — Fundação do repositório

- Git, .gitignore e estratégia de branches;
- README;
- pyproject e lock;
- ambiente virtual;
- ferramentas de qualidade;
- configuração VS Code opcional e sem preferências pessoais invasivas;
- CI mínima.

**Saída:** checkout limpo e setup reproduzível.

### Etapa B — Contratos arquiteturais mínimos

- mapa dos domínios;
- estrutura de pacotes;
- shared kernel mínimo;
- testes que proíbem dependências indevidas;
- Settings e composição da aplicação.

**Saída:** módulos vazios possuem limites verificáveis, sem lógica contábil inventada.

### Etapa C — Aplicação inicial

- FastAPI com application factory/lifespan;
- health/readiness;
- tratamento de erro e correlation_id;
- configuração segura e logs minimizados.

**Saída:** aplicação inicia e encerra de modo testável sem banco real obrigatório no import.

### Etapa D — Persistência e migration zero

- SQLAlchemy 2.x;
- session/unit of work;
- MySQL local de desenvolvimento/teste;
- Alembic;
- migration inicial apenas das entidades da primeira fatia;
- testes de upgrade e isolamento.

**Saída:** schema reproduzível sem create_all como mecanismo operacional.

### Etapa E — Primeiro walking skeleton S0

- ExecutionContext;
- tenant/company/ator/correlação;
- autorização mínima;
- comando idempotente;
- auditoria mínima e outbox no mesmo commit;
- teste cross-tenant negativo.

**Saída:** primeiro comando tenant-aware, autorizado, idempotente e auditado.

Somente depois dessa saída deve começar S1. NF-e, OFX, Domínio e IA não pertencem à correção da base atual.

## 13. Testes e verificações executados

### Verificações aprovadas

- inventário recursivo de arquivos;
- ausência/presença dos artefatos técnicos esperados;
- versões locais de Python, pip, Git e VS Code;
- presença das dependências obrigatórias;
- contagem de arquivos Python, SQL e configuração;
- links Markdown relativos: nenhum quebrado;
- blocos Markdown: nenhum arquivo com quantidade ímpar de delimitadores;
- leitura da documentação e busca por decisões tecnológicas pendentes.

### Testes não executáveis

- Pytest: pacote não instalado e diretório tests ausente;
- inicialização FastAPI: aplicação ausente;
- migrations Alembic: ambiente e revisions ausentes;
- integração MySQL: cliente/configuração/schema ausentes;
- testes de domínio, API, isolamento e segurança: código e fixtures ausentes.

## 14. Correções realizadas

Nenhuma correção de aplicação foi realizada.

A ausência da aplicação não é um defeito pequeno de inicialização; corrigi-la exigiria criar a fundação do produto, o que pertence à próxima execução autorizada.

## 15. Decisões técnicas registradas por esta auditoria

1. A stack informada no AGENTS.md passa a ser o alvo técnico observado desta baseline.
2. A DEC-011 permanece parcialmente aberta para componentes e políticas não selecionados.
3. O ambiente Python global não será considerado ambiente reproduzível do projeto.
4. A nomenclatura dos domínios precisa de mapa ou decisão antes do scaffold.
5. Não foi adotada solução provisória para banco, migrations, tenancy ou IA.
6. Nenhum requisito de domínio aprovado foi alterado.

## 16. Avaliação do critério de aceite

| Critério | Resultado |
|---|---|
| Retrato confiável do diretório atual | Atendido |
| Estrutura, dependências, configuração, models, schemas, rotas e testes verificados | Atendido; todos os itens ausentes foram registrados |
| Inconsistências entre documentação e código registradas | Atendido; não existe código e foram registradas inconsistências internas de baseline |
| Aplicação atual continua funcionando | Não aplicável; não existe aplicação executável |
| Novos módulos não implementados | Atendido |
| Modelo de domínio aprovado preservado | Atendido |

