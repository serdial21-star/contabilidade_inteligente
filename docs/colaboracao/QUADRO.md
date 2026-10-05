# Quadro de tarefas

Protocolo: [README.md](README.md). Atualizado por quem mudar o estado de uma tarefa.

## Em andamento

| ID | Título | Estado | Com quem | Arquivo |
|---|---|---|---|---|
| T-0009 | Onda 0: uma proposta por documento, reprocessamento explícito, correção só por estorno e anti-iframe (itens 26, 27 e parte do 6) | APROVADA — aguardando implementação | Codex | [T-0009](tarefas/T-0009-onda0-proposta-unica-por-documento.md) |
| ADR 0019 | Separar ou unir A e B; organização da contabilização em seis áreas; caminho do protótipo (pesquisa com especialistas, 04–05/10/2026) | ACEITA em 05/10/2026 — três pontos em aberto (piloto, exportação, data de entrada) | Proprietário | [Pesquisa](../PESQUISA_ARQUITETURA_A_B_CONTABILIZACAO_2026-10-05.md), [ADR 0019](../adr/0019-dois-runtimes-e-organizacao-da-contabilizacao.md) |

## Fila (ainda sem briefing; ordem sugerida, sujeita à decisão do usuário)

| Ordem | Tema | Origem | Sistema | Observação |
|---|---|---|---|---|
| 2 | Retenção, CORS e SQL parametrizado no workflow "[SECURITY] Validar Sessão de Funcionário" | Auditoria #7 | Sistema A | Ação do usuário no n8n |
| 3 | Onboarding não sobrescreve nome e e-mail do usuário compartilhado entre tenants | Auditoria #5 | Sistema B | Isolamento multi-tenant |
| 4 | Limite global da recuperação de senha não contar tentativas já bloqueadas; alerta | Auditoria #6 | Sistema A | — |
| 5 | Plano de migração de SHA-256 para Argon2id nas senhas | Auditoria #4; dossiê 26.1 | Sistema A | Exige ADR; depende do login do Sistema A |
| 6 | `state`/nonce na ponte de login e cabeçalhos anti-framing no Caddy | Auditoria #8 e #9 | A e B | — |
| 7 | Login legado de clientes (`Math.random`, SQL interpolado) | Dossiê mestre 26.1 e 32 | Sistema A | Exige ADR |
| 8 | Competência pelo fuso da empresa: filtros de período em UTC e data OFX sem fuso | [REFERENCIAS.md](REFERENCIAS.md), seção 3 | Sistema B | Possível defeito contábil; exige decisão sobre o fuso de referência |
| 9 | Formalizar fontes normativas versionadas (MOC/NT/XSD NF-e, OFX, IN RFB) e citá-las no código e nos ADRs | [REFERENCIAS.md](REFERENCIAS.md), seção 2 | Sistema B | Parte depende de você obter os documentos oficiais |
| 10 | Qualidade automática: adotar Ruff e verificador de tipos (mypy ou pyright) como dependência de desenvolvimento e no CI; alinhar o Python do CI (3.12) ao de produção (3.14) | Análise de ferramentas, 01/10/2026 | Sistema B | Muda dependências: exige justificativa conforme `AGENTS.md` seção 3 |
| 11 | Segundo limite de requisições por usuário autenticado, aplicado depois da verificação do token | T-0001, decisão de 01/10/2026 | Sistema B | Fazer antes de ampliar o número de usuários atrás do mesmo IP |
| 14 | Varredura de segredos não detecta credencial dentro de URL (`DATABASE_URL=mysql+pymysql://usuario:senha@host`), o tipo de vazamento mais provável neste projeto | Briefing da T-0002 | Sistema B | Exige tratar os placeholders existentes (`replace_me`, `SUA_SENHA`) sem allowlist |
| 16 | Índice em `security_sessoes_funcionarios.token_hash` (a autorização da T-0003 varre e trava a tabela) | Pré-publicação da T-0003 | Sistema A | Migration própria; impacto atual desprezível |
| 18 | Endurecer o workflow de permissões de funcionário: CORS `*`, `NOW()` em vez de UTC, SQL interpolado, gravação sem transação nem auditoria, leitura que ignora `funcionario_id`, fallback por cargo (SG-19) | T-0004, 03/10/2026 | Sistema A | Artefato já versionado em `docs/integration/system_a_permissions/` |
| 20 | Endpoints chamados pelo site que não existem no n8n: detalhe/complemento de chamados e documentos, abas Certidões/Livros/Obrigações da Biblioteca e `admin/fiscal/*` (Inteligência Fiscal) | Inventário do Lovable, T-0006, 03/10/2026 | Sistema A | Funcionalidades quebradas; não é falha de segurança |
| 21 | Obtenção automática de certidões (CND federal, FGTS, trabalhista) por API oficial, substituindo o Colab; extração e gravação dentro do sistema | Decisão do usuário, T-0006, 03/10/2026 | A ou B | Adiado: não atrasar os testes práticos. Pesquisar serviço oficial (candidato: SERPRO Integra Contador) e citar documentação/versão antes de implementar. Sugestão do usuário (03/10): campo para o certificado digital do cliente. Exige ADR antes de qualquer código: guardar certificado A1 de cliente (chave privada) é o dado mais sensível do sistema; avaliar como alternativa o certificado do próprio escritório com procuração eletrônica dos clientes, se o serviço oficial aceitar |
| 22 | Extrator Fiscal XML: arquivar o XML em `01_FISCAL` (hoje vai para a raiz da pasta do cliente), evitar cópia nova no Drive a cada envio e corrigir a tela que mostra "0 nota(s) processada(s)" (contrato da resposta) | Teste da T-0006, 03/10/2026 | Sistema A | Defeitos anteriores à T-0006; o processamento e a gravação no banco funcionam |
| 23 | Apuração ICMS a partir de PDF interpretado por IA (hoje o workflow só lê CSV): saída estruturada e validada, marcada como extraída por IA, conferida por pessoa; CSV continua como caminho determinístico | Pedido do usuário, 04/10/2026 | Sistema A | Etapa 1 (PDF com texto, sem IA) = T-0007, concluída. Etapa 2 (IA) = tarefa futura, após resolver uso de dados do provedor: Lovable Free/Pro pode treinar com conteúdo desde 09/09/2026 salvo opt-out (Account settings → Preferences → AI model training) |
| 24 | Planilhas da Apuração ICMS geradas numa pasta compartilhada com a equipe (opção C): cópia editável por geração, modelo inalterado; acaba o pedido de acesso ao administrador | Decisão do usuário, 04/10/2026 | Sistema A | Pequena; depois da publicação da apuração |
| 25 | Endurecer workflows de chamados e documentos (portal e painel): CORS `*`, SQL interpolado, `NOW()`, permissão de módulo ausente em "Listagens Gerais V2" e "Responder Ticket", número de ticket com `Math.random`; abertura de chamado aceita anexo acima de 10 MB (UAT T-0008, 05/10) | Diagnóstico da T-0008, 04/10/2026 | Sistema A | Padrão da T-0006; prioridade maior após T-0008 (painel expõe complementos sem permissão de módulo) |
| 26 | A mesma NF-e gera duas propostas: chave aleatória por envio (`app/api-client.js:61`) e preparação sem unicidade por documento (`nfe_to_dominio.py:115-160`). A correção precisa de reserva única por documento, rota de reprocessamento para `PENDING_RULE`/`ACCOUNT_MAPPING_REQUIRED`, rota de `supersede` e hash de repetição sem campos que mudam por dia | Pesquisa A/B, 05/10/2026 (seção 3.1) | Sistema B | Sem efeito hoje (exportação bloqueada, sem livro); obrigatório antes de dados reais ou prévia |
| 27 | `JournalEntryRevision.correct()` cria revisão a partir de lançamento já aprovado; num livro numerado, isso contraria o DL 486/1969, art. 2º, §2º, e a ITG 2000, itens 31–36 (correção por estorno) | Pesquisa A/B, 05/10/2026 (seção 3.2) | Sistema B | Resolver junto com o livro em tabelas (ADR 0019) |

## Concluídas

| ID | Título | Commit | Data |
|---|---|---|---|
| T-0001 | Rate limit por origem confiável e cache JWKS com validade | `14f3450` | 01/10/2026 |
| T-0002 | CI verde: falsos positivos da varredura de segredos sem allowlist | `06f07d3`, `499ac70`, `cc9ffb0` | 01/10/2026 |
| T-0003 | Exigir permissão nas operações administrativas de clientes do Sistema A (publicada em 03/10/2026) | `9b2c079`, `4dbca5c`, `7c92dea`, `6ebaf54` | 03/10/2026 |
| T-0004 | Menu do Operador vazio: leitura de permissões do funcionário no n8n (aplicada em 03/10/2026) | `080322b`, `1672aae` | 03/10/2026 |
| T-0005 | "Sair" revoga a sessão no servidor, funcionários e clientes (publicada em 03/10/2026) | `3ba048d`, `afb257b` | 03/10/2026 |
| T-0006 | Webhooks sem autenticação, proxy aberto, IA sem sessão e CORS do Supabase (publicada em 03–04/10/2026) | `db66ac4`, `7322960`, `458d999` | 04/10/2026 |
| T-0007 | Apuração ICMS a partir de CSV ou PDF com texto, com conferência obrigatória (publicada em 04/10/2026) | `b52f92d`, `634d952`, `c5eba50` | 04/10/2026 |
| T-0008 | Portal do cliente: detalhe e complemento de chamados e documentos; painel com anexos e complementos (publicada em 05/10/2026) | `a5008ac`, `2733512` e seguintes | 05/10/2026 |
