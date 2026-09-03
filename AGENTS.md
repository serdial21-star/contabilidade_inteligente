# AGENTS.md — Serdial21 Contabilidade Inteligente

## 1. Aplicação e autoridade

Este arquivo estabelece instruções permanentes para agentes de programação que atuem no repositório do **Serdial21 Contabilidade Inteligente**.

As regras valem para todo o repositório. Um AGENTS.md mais específico poderá complementar as instruções dentro de uma subárvore, mas não poderá enfraquecer requisitos aprovados, isolamento, segurança, integridade contábil, auditoria ou governança.

Antes de alterar uma decisão aprovada:

1. identifique a decisão e os artefatos afetados;
2. informe claramente o impacto e a razão;
3. apresente alternativas quando houver escolha material;
4. obtenha aprovação explícita;
5. registre a nova decisão e preserve a rastreabilidade.

Não redesenhe silenciosamente requisitos aprovados. Execute somente a fase ou tarefa solicitada; não avance para uma fase posterior para completar o sistema.

## 2. Identidade do produto

O Serdial21 é uma plataforma contábil inteligente, multi-tenant e orientada a escritórios contábeis.

No MVP:

- o sistema contábil externo continua sendo autoridade para escrituração, números oficiais, saldos e fechamento;
- o Serdial21 é autoridade sobre documentos e evidências processados, dados canônicos, regras, DE/PARA, propostas, workflow, aprovações, integrações, explicações de IA e auditoria do próprio processo;
- toda proposta com efeito contábil exige aprovação humana válida;
- IA é assistiva e nunca substitui o motor determinístico ou a responsabilidade profissional.

## 3. Stack inicial

- Python 3.12 ou superior;
- FastAPI;
- SQLAlchemy 2.x;
- Alembic;
- MySQL;
- PyMySQL;
- Pydantic 2;
- Pydantic Settings;
- Pytest;
- VS Code.

Não troque, remova ou acrescente uma dependência estrutural sem informar motivo, impacto, alternativas e compatibilidade.

Configuração deve ser tipada por Pydantic Settings. Credenciais e segredos vêm do ambiente ou de um provedor apropriado; nunca do código-fonte.

## 4. Arquitetura

O produto é um **monólito modular orientado a domínios**, preparado para evolução futura. Distribuição em microsserviços não é objetivo inicial e exige justificativa mensurável.

Quando a estrutura de código for criada, preserve limites equivalentes a:

- domínio: entidades, value objects, políticas, invariantes e serviços de domínio;
- aplicação: casos de uso, comandos, consultas, DTOs e portas;
- contratos: APIs públicas internas e eventos versionados;
- adaptadores: FastAPI, SQLAlchemy, arquivos, filas e fornecedores;
- bootstrap: composição, configuração e ciclo de vida.

Dependências apontam para dentro: adaptadores dependem da aplicação, e a aplicação depende do domínio e de portas. O domínio deve permanecer Python puro sempre que possível e não deve depender de FastAPI, SQLAlchemy, transporte, fila, storage, SDK de IA ou fornecedor externo.

## 5. Domínios previstos

Os domínios lógicos previstos são:

- identity;
- tenancy;
- companies;
- master_data;
- chart_of_accounts;
- accounting;
- rules;
- documents;
- imports;
- reconciliation;
- locks;
- workflow;
- integrations;
- audit;
- ai;
- reporting.

Essa lista orienta ownership e limites; não autoriza implementar todos os domínios de uma vez. Preserve a sequência aprovada das fatias S0–S8.

Cada domínio:

- é dono de suas invariantes e mutações;
- expõe serviço, fachada, porta, consulta autorizada ou evento quando outro domínio precisa interagir;
- não acessa diretamente tabelas ou repositórios privados de outro domínio quando houver contrato apropriado;
- não duplica regra de negócio pertencente a outro domínio;
- não permite que detalhes de fornecedor contaminem o modelo canônico.

## 6. Regras arquiteturais obrigatórias

### 6.1 API e aplicação

- Rotas FastAPI devem ser finas: validar transporte, resolver contexto autenticado, chamar um caso de uso e mapear a resposta.
- Não coloque regra de negócio complexa em endpoint, dependency, schema Pydantic ou middleware.
- Casos de uso coordenam portas e transações; invariantes pertencem ao domínio.
- Schemas Pydantic são contratos de entrada e saída, não entidades de domínio nem models ORM.
- Erros esperados devem possuir classificação estável e não vazar existência de recurso de outro tenant.

### 6.2 Domínio e ORM

- Models SQLAlchemy não devem concentrar toda a lógica de negócio.
- Entidades, value objects, políticas e serviços de domínio controlam invariantes.
- ORM, domínio e contratos de API não devem ser tratados como um único modelo compartilhado.
- Serviços de domínio não executam I/O oculto.
- Dinheiro, alíquotas, quantidades, taxas e demais valores de precisão definida não usam float.
- Use Decimal no Python e DECIMAL/NUMERIC no MySQL, com precisão, escala e arredondamento explicitamente definidos.
- Não invente conta, regra, máscara, lançamento, tolerância, arredondamento ou tratamento contábil para preencher uma lacuna. Gere pendência ou solicite decisão.

### 6.3 Banco de dados e migrations

- Toda alteração de schema ocorre por migration Alembic revisável.
- Não use create_all ou alteração manual como mecanismo de evolução de produção.
- Migrations devem possuir ordem, impacto, compatibilidade e estratégia segura para dados existentes.
- Não faça alteração destrutiva silenciosa. Remoção, renomeação incompatível ou transformação irreversível exige plano, backup quando aplicável, aprovação e caminho de recuperação.
- Restrições, índices e chaves devem reforçar invariantes críticas; validação apenas na interface não é suficiente.
- Relacionamentos empresariais devem impedir referências cross-tenant e, quando aplicável, cross-company.

### 6.4 Tenant, empresa e autorização

- Todo dado pertencente a escritório carrega tenant_id.
- Todo dado de empresa carrega tenant_id e company_id, mesmo quando o escopo pareça inferível pelo pai.
- Todas as consultas, comandos, jobs, caches, arquivos, buscas, relatórios, exportações, integrações e contextos de IA são tenant-aware.
- Nenhuma operação pode ler, alterar, correlacionar, exportar ou inferir dados entre tenants.
- Um ID identifica um recurso; nunca autoriza acesso.
- tenant_id e company_id informados por rota, query ou corpo não são confiáveis por si sós. Compare-os ao contexto autenticado e ao CompanyAccess vigente.
- Revalide acesso, versão e bloqueios no instante do efeito crítico, inclusive após fila, retry ou sessão antiga.
- A negação não deve revelar se um objeto de outro tenant existe.
- Escreva testes negativos cross-tenant para cada nova fronteira empresarial.

### 6.5 Tempo, dinheiro e identidade

- Use UTC internamente para timestamps técnicos.
- Converta para timezone de apresentação apenas nas bordas.
- Timezone, competência, data contábil e calendário empresarial são conceitos do domínio e não podem ser inferidos silenciosamente do timezone do servidor.
- Datas e horários técnicos devem ser timezone-aware no Python, salvo convenção de persistência explicitamente documentada e testada.
- IDs são opacos e estáveis.
- Identificadores fiscais e externos são strings; preserve zeros à esquerda e formatação sem convertê-los em autorização.

### 6.6 Versionamento e correção

- Versão publicada é imutável.
- A regra vale para regras, mappings, layouts, workflows, perfis de IA e demais configurações publicadas.
- Correção material cria nova versão, evento, revisão, estorno ou ajuste vinculado; não reescreve silenciosamente o histórico.
- Resultados preservam as versões exatas de entrada, parser, schema, canônico, regra, DE/PARA, layout, prompt e modelo aplicáveis.
- Aprovação referencia a revisão e o hash exatos. Uma nova revisão invalida ou supersede a aprovação anterior conforme a política do domínio.

### 6.7 Auditoria, idempotência e efeitos externos

- Auditoria é append-oriented. Correção referencia o evento anterior em vez de apagá-lo.
- Um efeito crítico e seu evento mínimo de auditoria devem ser persistidos na mesma transação quando pertencem ao mesmo banco.
- Log operacional não substitui auditoria de negócio.
- Operações críticas devem ser idempotentes quando aplicável.
- Mesma chave e mesmo hash retornam ou vinculam o resultado anterior; mesma chave com conteúdo diferente gera conflito.
- Retries preservam identidade e payload. Estado externo desconhecido deve ser reconciliado antes de reenviar.
- Chamada a fornecedor não ocorre dentro da transação de negócio.
- Bloqueio de conta ou período impede alteração, aprovação, reprocessamento e exportação por interface, API, job, regra, IA ou integração.
- Desbloqueio não retoma automaticamente trabalho pendente; alterações relevantes exigem nova conferência.

### 6.8 IA e motor de regras

- O motor determinístico é a base do comportamento contábil reproduzível.
- Não implemente IA como substituta de regra determinística aprovada.
- IA propõe, classifica, extrai, explica e identifica inconsistências dentro das tarefas autorizadas.
- IA não aprova, desbloqueia, publica regra, cria conta para concluir processo, exporta, efetiva escrituração oficial ou altera permissão.
- A saída de IA deve ser estruturada, validada, versionada e distinguível de decisão humana.
- Indisponibilidade ou resposta inválida de IA não pode interromper o caminho determinístico seguro.
- Conteúdo de documento, XML, planilha, extrato, prompt ou fonte externa é dado não confiável e não altera políticas ou instruções privilegiadas.
- Não use eval, exec ou mecanismos equivalentes para regras.
- Não execute código arbitrário fornecido por configuração, usuário, documento ou modelo.

### 6.9 Segurança, configuração e dados

- Nunca armazene senha, token, chave de banco, chave de API ou outro segredo no código.
- Logs, mensagens de erro, auditoria, fixtures e snapshots não armazenam segredos.
- Não copie XML, extrato, prompt ou dado pessoal bruto para log por conveniência.
- O arquivo .env nunca é versionado.
- O arquivo .env.example contém somente nomes de variáveis e valores fictícios seguros.
- Minimize dados sensíveis em DTOs, eventos, logs, auditoria e integrações.
- Dados de tenant não são usados para treinamento por padrão. Inferência, log, melhoria e treinamento são finalidades distintas.
- Fixtures reais devem estar anonimizadas, autorizadas, versionadas e sujeitas a retenção.

### 6.10 Qualidade do código

- Todo código Python possui type hints adequados.
- Prefira funções e tipos pequenos, explícitos e testáveis.
- Evite duplicação, abstração prematura e shared kernel amplo.
- Preserve compatibilidade com módulos, contratos, eventos e migrations já implementados.
- Mudança incompatível exige versionamento ou migration explícita.
- Comentários explicam decisões e restrições, não repetem o código.

## 7. Processo obrigatório de alteração

Antes de programar:

1. leia o AGENTS.md aplicável;
2. leia README.md, quando existir;
3. leia a documentação relacionada em docs;
4. examine a estrutura, dependências, configuração, migrations, models, rotas e testes existentes;
5. confira o estado atual do repositório e preserve alterações do usuário;
6. procure implementação equivalente antes de criar algo novo;
7. identifique requisitos, invariantes, riscos e impacto;
8. informe qualquer conflito ou mudança material de decisão.

Ao executar:

1. analise o problema;
2. apresente o impacto relevante;
3. implemente a menor alteração suficiente;
4. mantenha limites de domínio e compatibilidade;
5. escreva ou atualize testes para toda regra crítica;
6. documente decisão técnica ou mudança de contrato;
7. não avance para funcionalidade ou fase posterior.

Ao concluir:

1. liste arquivos criados;
2. liste arquivos alterados;
3. explique resumidamente a implementação;
4. execute os testes relacionados;
5. execute a suíte existente quando viável;
6. informe testes aprovados, ignorados e falhas;
7. informe migrations criadas;
8. informe decisões técnicas tomadas;
9. informe pendências, riscos e limitações;
10. pare sem iniciar a próxima fase.

## 8. Estratégia mínima de testes

- Use Pytest.
- Toda regra crítica exige teste positivo e negativo.
- Invariantes contábeis usam Decimal e casos de fronteira.
- Toda funcionalidade empresarial possui teste de isolamento entre tenants e de CompanyAccess.
- Operações idempotentes testam repetição igual e conflito de conteúdo.
- Operações concorrentes testam versão, transição única e ausência de efeito duplicado.
- Versões publicadas testam imutabilidade.
- Bloqueios testam todos os canais que podem produzir o efeito.
- Aprovações testam revisão/hash, alçada e segregação.
- Auditoria testa atomicidade com o efeito e comportamento append-oriented.
- Integrações testam retry, falha parcial, timeout, UNKNOWN e reconciliação.
- IA testa contrato de saída, isolamento, prompt injection, indisponibilidade e ausência de autoridade crítica.
- Migrations devem ser testadas no MySQL suportado, inclusive upgrade e, quando seguro e previsto, downgrade.

Não reduza guardrails para fazer um teste passar.

## 9. Proibições explícitas

Não:

- invente estrutura ou regra contábil;
- remova, desative ou contorne auditoria;
- ignore tenant, company, membership ou CompanyAccess;
- confie em ID como prova de autorização;
- use eval ou execute código configurável arbitrário;
- armazene senha, token, segredo de banco ou chave de API;
- versione .env;
- altere versão publicada;
- sobrescreva evidência ou histórico para corrigir dado;
- use float para dinheiro;
- permita canal alternativo contornar bloqueio;
- trate sugestão de IA como decisão final;
- permita IA executar efeito contábil crítico diretamente;
- declare escrituração, saldo ou fechamento oficial sem evidência do sistema externo;
- faça mudança destrutiva silenciosa;
- avance para a próxima fase sem solicitação.

