# System A Security Gaps

Status baseado em evidência disponível, não em presunção de vulnerabilidade explorável. Sem source/runtime autenticado, controles não demonstrados falham o gate de prontidão.

## Reavaliação dos cinco bloqueadores de segurança

| ID | Bloqueador | Evidência 09B | Risco | Remediação mínima | Impacto |
| --- | --- | --- | --- | --- | --- |
| SG-01 | M2M auth/rotation/replay ausentes | nenhum mecanismo A fornecido | token browser reutilizado ou requests forjados | principal de serviço por ambiente/direção, HMAC, timestamp, replay cache, rotation/revoke | `CONFIRMED_BLOCKER` |
| SG-02 | Escopo tenant/company do service principal | auth A/B atual não demonstra contrato M2M | acesso cross-tenant/company | scopes explícitos, resolução server-side, testes negativos e negação opaca | `CONFIRMED_BLOCKER` de design/implementação |
| SG-03 | Guards/permissões/auditoria A não demonstrados fail-closed | dossiês relatam rotas cliente e fallback; source ausente | exposição de dados/efeitos sem autorização | guards em todas rotas, empty/unknown→deny, 401/403 seguros, audit write | `NOT_VERIFIABLE`, bloqueia produção e contratos A |
| SG-04 | Transporte Drive/SSRF/evidência | nenhuma geração de URL inspecionável | link permanente, exfiltração, conteúdo mutável | URL curta/objeto único, allowlist, hash, size/type/quarantine, download backend | `CONFIRMED_BLOCKER` documental |
| SG-05 | Separação de ambientes/secrets | nenhuma homologação/config apresentada | prod↔dev, segredo reutilizado, dados reais em teste | frontend/n8n/DB/Drive/logs/secrets HOM separados | `CONFIRMED_BLOCKER` |

`SECURITY BLOCKERS CONFIRMED: 4`; um (`SG-03`) permanece sem verificação atual, mas o gate continua reprovado até evidência positiva.

## Atualização 2026-09-21 — evidência de terceiros (relatório de varredura Lovable)

Fonte: `docs/integration-input/RELATORIO_VARREDURA_LOVABLE_20260921.md`, primeira evidência de nível código-fonte do Sistema A (frontend + três Supabase Edge Functions) disponível a este workspace. Classificação `DOCUMENTED_BY_THIRD_PARTY_SOURCE_REVIEW`: mais forte que dossiê, mais fraca que `VERIFIED_IN_AVAILABLE_CODE` (sem snapshot/tag inspecionável, sem cobertura do n8n/MySQL). Não altera a decisão de segurança ao final deste documento nem autoriza pular a ordem (homologação → verification package → repetir 09B).

| ID | Reclassificação | Evidência nova | Observação |
| --- | --- | --- | --- |
| `SG-03` | `NOT_VERIFIABLE` → `CONFIRMED_BLOCKER` | Relatório itens 1, 3, 7: `usePermissoes.ts:98-104,102,122`, `useClientPermissoes.ts:53-54,85-87`, `useCanAccess.ts:13-16`, `App.tsx:78-79` confirmam fail-*open* afirmativo (carregando, lista vazia, cargo ausente e erro 200-com-payload-de-erro todos liberam acesso); `AdminAuthContext.tsx:53,112` e `useAdminDashboard.ts:58`/`useClientes.ts:24-25` confirmam que o contrato `success/message/data` não é respeitado uniformemente | Deixa de ser ausência de evidência e passa a ser evidência positiva de defeito de design. `SECURITY BLOCKERS CONFIRMED` passa de 4 para 5. |
| `SG-04` | mantém `CONFIRMED_BLOCKER` (documental) | Relatório item 4: `supabase/config.toml:4-7` e `proxy-file-upload/index.ts:18-28` — função sem autenticação que repassa para qualquer destino informado pelo chamador, sem allowlist | Confirma o padrão SSRF/relay aberto já previsto como risco, agora com localização exata de código. Continua exigindo o mesmo pacote de verificação para fechar (URL curta/objeto único, allowlist, hash, quarentena). |

### SG-06 (novo) — Funções de nuvem abertas: incidente de produção independente da integração

`supabase/config.toml:4-7` expõe `ai-analyst` e `proxy-file-upload` sem checagem de autenticação e com CORS liberado para qualquer origem; `proxy-file-upload` aceita destino arbitrário vindo da própria requisição (relatório item 4). Isso é explorável hoje, em produção, por qualquer pessoa que conheça o endereço — independente de qualquer decisão de integração com o Sistema B. Classificação: `PRODUCTION_INCIDENT_OUT_OF_SCOPE_B` — não é um item do Connect Hub nem do roadmap deste repositório; deve ser escalado ao dono/operador do Sistema A imediatamente, fora do ritmo das fases 09A/09B. Não bloqueia nem desbloqueia nenhum gate deste repositório; é registrado aqui apenas porque a evidência que o revelou é a mesma usada para reclassificar `SG-03`/`SG-04`.

Nenhum código, credencial, middleware, endpoint ou teste foi criado neste repositório para reagir a esta atualização, conforme a "Decisão de segurança" abaixo, que permanece válida.

## Atualização 2026-09-21 (parte 2) — código-fonte real inspecionado

O dono do produto disponibilizou o código-fonte real do frontend do Sistema A (fora deste repositório, em `C:\Projetos\Sistema escritório\serdialconnect-hub-main`; `.env` presente e **não lido**, nenhum segredo acessado, nenhuma alteração feita). Detalhe completo em `SYSTEM_A_RUNTIME_VERIFICATION.md`. Resumo relevante a este documento:

- `SG-03` sobe de `CONFIRMED_BLOCKER` (evidência de terceiros) para `VERIFIED_IN_AVAILABLE_CODE`: o fallback permissivo está no código-fonte real (`usePermissoes.ts:98-104`, comentário do próprio autor `// permissive fallback`; `useClientPermissoes.ts:85-88`; `useCanAccess.ts:13-16`) e `AdminRouteGuard.tsx` não faz nenhuma validação de sessão no servidor — decide localmente a partir desse mesmo fallback. **Achado novo, mais sério que o já registrado:** `PROMPT_PERMISSOES_N8N_MYSQL.md` (especificação de backend do próprio Sistema A) documenta esse "sem registro = acesso a todos" como comportamento **pretendido** do banco (linha 120), não apenas um atalho do frontend — se implementado como especificado, a origem do problema é de política de backend, não só de código React.
- `SG-04` mantém `CONFIRMED_BLOCKER`, com uma correção de escopo: `proxy-file-upload/index.ts:19,28` mostra que o destino controlado pelo chamador é um *path* sob um host fixo (`n8n.serdial21.com/webhook`), não uma URL arbitrária de qualquer host. Ainda é um relay não autenticado para qualquer webhook desse host — risco real — mas não é SSRF irrestrito à internet.
- `SG-06` (funções de nuvem abertas) precisa de uma correção: apenas `ai-analyst` e `proxy-file-upload` têm `verify_jwt = false` em `supabase/config.toml`. `proxy-webhook` (usada por dashboard, impostos e outros) não está nesse arquivo e portanto segue o padrão do Supabase de exigir um JWT válido — uma sessão Supabase autenticada é necessária para invocá-la, ainda que não vinculada à autorização própria do painel Serdial21. A classificação `PRODUCTION_INCIDENT_OUT_OF_SCOPE_B` permanece, mas restrita às duas funções realmente sem `verify_jwt`.

Uma especificação de schema MySQL pretendido para permissões (`permissoes_funcionario_modulos`, `permissoes_funcionario_clientes`, `permissoes_cliente_portal`) foi encontrada em `PROMPT_PERMISSOES_N8N_MYSQL.md` — é desenho documentado pelo próprio Sistema A, não schema de banco em produção; avança CHP-04 parcialmente, não o resolve.

## Atualização 2026-09-22 — pacote de verificação real (n8n + MySQL)

Fonte: 60 exports de workflows n8n e 30 exports de schema MySQL (estrutura apenas; ver nota de segurança abaixo), fornecidos pelo dono do produto a partir de pastas locais. Isto é `VERIFIED_IN_AVAILABLE_CODE` — não mais inferência de terceiros — cobrindo pela primeira vez o lado servidor (antes só o frontend havia sido inspecionado). Nenhum workflow, credencial, banco ou deploy foi alterado; MySQL e Google Drive são referenciados por ID de credencial n8n, nunca por valor, em todos os 60 arquivos.

**Nota de segurança do processo:** os 30 exports de banco vieram inicialmente com dados reais (linhas de `clientes`, `funcionarios`, `logs_auditoria` etc.), não só estrutura como solicitado. Antes de qualquer leitura de conteúdo, os blocos de dados foram removidos programaticamente (mantendo só `CREATE TABLE`/índices/triggers); nenhuma linha de dado real de cliente, funcionário ou log foi lida ou registrada neste repositório.

### Reclassificação de SG-03 — de CONFIRMED_BLOCKER para CONFIRMED_BLOCKER (evidência de backend, mais grave)

O workflow `[Permissões] Admin - Consultar Cliente` (`admin/permissoes/cliente`) constrói a resposta assim: define TODOS os módulos como `permitido: true` por padrão (`MODULOS_PADRAO.forEach(m => modulos[m] = true)`) e só sobrescreve com o valor real se existir uma linha em `permissoes_cliente`. **O fail-open não é um atalho do frontend — é a lógica do próprio backend n8n.** O trigger `trg_cliente_permissoes_padrao` (schema `clientes.sql`) reforça o mesmo padrão: ao cadastrar um cliente, cria automaticamente 7 linhas de permissão com `permitido = 1` (tudo liberado) para o portal.

### Novos achados (não estavam em nenhuma evidência anterior)

| ID | Achado | Evidência | Severidade |
| --- | --- | --- | --- |
| SG-07 | Senha de funcionário/cliente com hash fraco | `API - Admin - Login V2.1...json`: `WHERE senha = SHA2('{{ senha }}', 256)`; coluna `funcionarios.senha varchar(64)` (tamanho exato de um hex SHA-256) — sem salt, sem custo computacional (bcrypt/argon2/scrypt) | GRAVE — hash rápido e sem sal é quebrável em escala por força bruta/rainbow table se o banco vazar |
| SG-08 | Token de sessão gerado sem gerador criptográfico | Mesmo workflow: `Math.random().toString(36)` × 4 + timestamp, não `crypto.randomBytes`/equivalente | ALTO — tokens de sessão previsíveis em tese, ainda que hasheados com SHA-256 antes de gravar |
| SG-09 | Consultas SQL construídas por concatenação de texto, não parametrizadas | Padrão presente em praticamente todos os workflows lidos (login, permissões, update de item, upload de documento) — usam uma função `esc()` de escape manual em vez do recurso de parâmetros do node MySQL do n8n | GRAVE como padrão — escape manual é frágil; não foi *provado* explorável, mas é o tipo de padrão que causa injeção de SQL quando um caso não coberto aparece |
| SG-10 | Revogação de sessão (`revogado_em`) checada de forma inconsistente | `admin/permissoes/cliente` NÃO checa `revogado_em`; `admin-update-item-v5` e `admin/upload-documento-cliente` checam corretamente `AND s.revogado_em IS NULL` | MODERADO — um logout/revogação pode não valer para todos os endpoints |
| SG-11 | Cobertura de auditoria incompleta em ações sensíveis | `logs_auditoria` é escrita por 18 dos 60 workflows (cadastro de cliente, edição de funcionário, impostos, resposta de ticket, honorários); **não** é escrita pelo login, pela consulta/gravação de permissões, pelo update de item do Kanban nem pelo upload de documento | MODERADO — as ações mais sensíveis (quem logou, quem mudou uma tarefa, quem enviou um documento) não deixam rastro na auditoria |
| SG-12 | Todos os 60 workflows exportados estão `active: true`, incluindo versões antigas/duplicadas | Ex.: `API - Admin Delete Item v1.json` e `...v3 (Unificado)...json` ambos ativos; o workflow legado de tickets sem token (`SG-antigo`, achado 5 do relatório de 2026-09-21) está confirmado **ativo e chamável hoje**, não apenas "código morto" | Eleva a severidade do achado antigo: não é limpeza de código, é uma porta aberta em produção |
| SG-13 (positivo) | `admin/upload-documento-cliente` existe e funciona | Workflow `API - Admin - Upload Documento Cliente v1 (Corrigido).json` implementado: sessão validada com `revogado_em` checado, valida `cliente_id`/competência/valor, envia ao Drive, grava em `inbox_documentos`/`entregas_master`/`impostos_obrigacoes`/`honorarios_parcelas` | Resolve o bloqueador antigo "upload ausente" (CHP-17/IR-P0-09) |
| SG-14 (positivo) | Expiração de sessão é checada no backend | Todos os workflows autenticados lidos fazem `s.expira_em > NOW()` | Contradiz parcialmente a leitura anterior "sessão sem validade" — a validade existe e é aplicada; o gap real é revogação (SG-10), não expiração |
| SG-15 (positivo) | `logs_auditoria` existe e está em uso real | Schema confirma tabela populada (`AUTO_INCREMENT=1171`); FK para `funcionarios`; 18 workflows escrevem nela | Resolve `AUDIT: UNKNOWN` para "existe e é usada" — cobertura incompleta continua (SG-11) |

### CHP-12 (persistência do Kanban) — causa raiz identificada

O workflow `API - Admin Update Item v5 (Debug Estruturado) (Com Sessão, gravação corrigida)` monta um `UPDATE {tabela} SET ... WHERE id = X LIMIT 1` e considera sucesso sempre que a query não retorna erro SQL — **sem checar quantas linhas foram de fato alteradas** (`affectedRows`). Um `UPDATE` com `WHERE id` que não bate com nenhuma linha não é erro em MySQL, só afeta zero linhas — e essa resposta seria reportada como `{"success": true, "updated": true}` mesmo sem gravar nada. Isso explica precisamente o comportamento já relatado ("diz sucesso sem salvar"), apesar do nome do arquivo dizer "gravação corrigida". `CHP-12` passa de `CONFIRMED_BLOCKER` (sem prova) para `CONFIRMED_BLOCKER` com causa raiz identificada e corrigível (checar `affectedRows > 0` antes de responder sucesso).

## Atualização 2026-09-22 (parte 2) — achados adicionais e correção de um achado anterior

Ao localizar o workflow correspondente ao caminho não versionado `admin/tickets` (achado do relatório de 2026-09-21, item 5) para desativação, nenhum dos 60 workflows exportados registra webhook nesse path exato — só existem `admin/tickets-v2` e `admin/responder-ticket-v2`. **SG-12 é corrigido nesta parte**: o caminho antigo de tickets sem token não tem workflow ativo nesta exportação; não é mais tratado como exposição confirmada. Se o dono do Sistema A souber de um workflow nesse path fora desta exportação, isso precisa ser reavaliado.

| ID | Achado | Evidência | Severidade |
| --- | --- | --- | --- |
| SG-16 | Injeção de SQL sem nenhuma proteção em login administrativo legado, ainda ativo | `[Auth] Login Painel Interno.json`, path `admin/login` (sem `-v2`), consulta `SELECT id, nome, email, perfil FROM funcionarios WHERE email = '{{ $json.body.email }}' AND senha = '{{ $json.body.senha }}' AND status = 'Ativo';` — email e senha vão direto para dentro do SQL, sem nenhuma função de escape (diferente de todos os outros workflows lidos, que ao menos tentam escapar manualmente) | **GRAVE, ação imediata recomendada**: é um endpoint de login (não exige autenticação prévia por definição), ativo em produção, com injeção de SQL clássica no próprio campo de senha — risco de bypass de login e/ou extração de dados via `UNION SELECT`. Compara a senha em texto puro, sem `SHA2`, o que também é inconsistente com o restante do sistema |
| SG-17 | ~~Nenhum workflow exportado consulta ou salva `permissoes_funcionario_modulos`~~ — **RESOLVIDO 2026-09-22**: o workflow existe, não fazia parte da exportação original | `API - Admin - Permissões (Funcionários) v2.2 (Token + Fallback) (Com Sessão, leitura corrigida).json`, fornecido posteriormente pelo dono do Sistema A | Fechado — ver SG-19 para o achado real que ele revela |
| SG-19 | Sem nenhuma permissão configurada, funcionário recebe acesso por padrão do cargo — inclusive `operador` | Nó "Montar Permissões" do workflow acima: se `permissoes_funcionario_modulos` não tem linha para o funcionário, aplica `fallbackPorCargo(cargo)`. `administrador` recebe tudo; `auditor` só visualização; qualquer outro cargo (`operador`, padrão) já recebe visualizar/criar/editar (não excluir) em clientes, tickets, entregas, inbox e evidências, sem nenhuma configuração explícita | MODERADO — mais defensável que "libera tudo" cego (é diferenciado por cargo, e `auditor` já é restrito), mas ainda é "ausência de configuração = acesso amplo por padrão" em vez de negado; é uma decisão de produto que o dono do Sistema A deve confirmar conscientemente, não uma correção automática |
| SG-20 | Salvar permissões de funcionário apaga e recria em várias instruções SQL sem transação | Nó "Gerar SQL Otimizado": monta `DELETE; DELETE; INSERT; INSERT; ...` como uma string só, sem `START TRANSACTION`/`COMMIT`/`ROLLBACK` | BAIXO/MODERADO — risco de integridade, não de segurança: se uma instrução do meio falhar, o funcionário pode ficar com permissões parcialmente apagadas e não totalmente recriadas |
| SG-09 (correção) | Nem todo SQL montado por concatenação de texto no sistema é inseguro | O mesmo workflow acima valida `modulo`/`acao` com uma lista de caracteres permitidos (`/^[A-Za-z0-9_]{1,50}$/`) antes de montar a query, e `funcionario_id`/`cliente_id` são forçados a número — este caso específico está protegido contra injeção | Ajusta SG-09: o padrão geral (escape manual em vez de parâmetros) continua um risco a evitar, mas nem toda ocorrência é uma vulnerabilidade provada; o achado realmente crítico continua sendo SG-16 (login sem nenhuma proteção) |
| SG-18 | Login administrativo sem limite de tentativas | Diferente do login do portal do cliente (`[Auth] Login Portal Cliente - V2`, que bloqueia após 5 tentativas em 15 min via `log_tentativas_login`), nenhum dos dois logins administrativos (`admin/login-v2`, `admin/login`) tem proteção equivalente | MODERADO — permite tentativas de senha sem limite contra contas de funcionário |

### Arquivos corrigidos preparados (não aplicados em produção)

Para os itens SG-01/03 (fail-open, agora com correção pronta), SG-08 (token) e a causa raiz do CHP-12 (checagem de `affectedRows`), foram preparadas versões corrigidas de 6 workflows, prontas para importar no n8n — nenhuma foi enviada ao Sistema A, nenhuma credencial foi tocada. Uma está em `H:\Meu Drive\Projetos\Serdial21 Aplicativo Escritório\n8n CORRIGIDOS 2026-09-22\` (a primeira, antes de um bloqueio de segurança da ferramenta impedir gravação direta nessa pasta compartilhada); as outras 5 e um script SQL de backfill de permissões estão no ambiente local do agente, a serem copiadas pelo dono do produto. Detalhe e instruções de importação foram fornecidos diretamente ao dono do produto na conversa, não neste documento (evita duplicar instruções operacionais fora do contexto técnico).

## Atualização 2026-09-22 (parte 3) — correções aplicadas em produção pelo dono do Sistema A

O dono do Sistema A importou as correções preparadas e testou em produção. Registro do que aconteceu, incluindo um incidente e sua causa raiz:

| Item | Resultado | Evidência |
| --- | --- | --- |
| SG-16 (login `admin/login` com injeção de SQL) | **RESOLVIDO** — workflow `[Auth] Login Painel Interno` desativado | confirmado pelo dono do produto |
| SG-03 / CHP-06 (fail-open nas permissões) | **RESOLVIDO** — 3 workflows de permissões substituídos (default passa a negar; `revogado_em` passa a ser checado nos 3) | arquivos importados; sem relato de problema após o login voltar |
| CHP-12 (Kanban "sucesso" sem persistir) | **RESOLVIDO E VERIFICADO EM PRODUÇÃO** — a correção inicial (checar `affectedRows`) não funcionou porque esta versão do node MySQL do n8n só devolve `{"success": true}`, sem `affectedRows`, mesmo com efeito real. Corrigido substituindo a checagem por uma releitura do item no banco logo após o update (confirma existência antes de declarar sucesso). Testado movendo cartões reais no quadro, sem mais aviso de "não encontrado" | execução real em 2026-09-22, confirmada pelo dono do produto |
| SG-08 (token de sessão gerado sem gerador criptográfico) | **NÃO RESOLVIDO — tentativa revertida** | ver incidente abaixo |

### Incidente: tentativa de corrigir SG-08 derrubou login de admin e de cliente

Ao trocar `Math.random()` por `require('crypto')` nos dois workflows de login (`admin/login-v2` e `portal-serdial-v2`), ambos pararam de autenticar. Causa raiz confirmada pelo log de execução do n8n: **`Error: Module 'crypto' is disallowed`** — este n8n (versão 2.6.4, self-hosted) executa nós de código através de um `@n8n/task-runner` externo que bloqueia `require(...)` de módulos nativos do Node por política de segurança.

Uma segunda tentativa usou o objeto global `crypto` (Web Crypto API, sem `require`) — também falhou: **`ReferenceError: crypto is not defined`**. O sandbox deste task runner não expõe esse global. Ou seja, **nenhuma fonte de aleatoriedade criptográfica está disponível dentro de um nó de código deste n8n**, nem via `require` nem via global.

**Ação tomada:** os dois workflows de login foram revertidos para a versão original (`Math.random()`), restaurando o acesso. Login voltou a funcionar normalmente.

**Conclusão para SG-08:** não é corrigível só editando o workflow. Precisaria de uma mudança de configuração do próprio n8n (variável de ambiente que libera módulos específicos para o task runner, ex. `NODE_FUNCTION_ALLOW_BUILTIN`), o que é uma decisão de infraestrutura do dono do Sistema A, fora do escopo de um ajuste de workflow. SG-08 permanece `CONFIRMED_BLOCKER`, sem correção disponível no momento; risco inalterado (token de sessão previsível em tese, mitigado parcialmente por ser hasheado com SHA-256 antes de gravar no banco).

**Lição operacional registrada:** qualquer futura correção neste n8n que dependa de módulos nativos do Node (crypto, fs, path etc.) ou de globals não padrão do JavaScript deve ser assumida como bloqueada até prova em contrário. Testar em horário de baixo uso, nunca durante expediente com usuários ativos.

## Decisão de segurança (mantida)

Nenhuma credencial, workflow ou schema de produção foi alterado nesta atualização. A ordem seguinte é: o dono do Sistema A revisa e importa os arquivos corrigidos preparados, roda o backfill de permissões antes de ativar a correção do fail-open, desativa `[Auth] Login Painel Interno]` imediatamente (SG-16, não depende de arquivo corrigido), e esclarece o paradeiro dos workflows de permissão de funcionário (SG-17). Qualquer teste de write real deve ocorrer com item sintético claramente identificado, nunca dado de cliente.

## Browser e sessão

- armazenamento em `localStorage` de `auth_token`/`admin_auth_token`: documentado, não verificado no source atual;
- revogação de logout server-side: `GAP` até prova contrária;
- missing/invalid/expired token → 401: `NOT_TESTED`;
- rotas cliente com guard equivalente a `ClientRouteGuard`: `PARTIAL/NOT_VERIFIABLE`;
- permissões vazias, indefinidas ou módulo desconhecido devem negar; não existe teste disponível;
- CORS deve usar allowlist e responder preflight por contrato de browser; wildcard não é correção permanente.

Esses itens não autorizam um redesign amplo de auth em 09B. Precisam de source+HOM e escopo de remediação próprio.

## n8n

O host público responde e expõe no HTML o release n8n 2.6.4. Workflows não foram acessados; portanto permanecem desconhecidos:

- status active/inactive/duplicate;
- `Respond to Webhook` versus `lastNode`;
- tratamento de OPTIONS/CORS;
- SQL parametrizado versus concatenação;
- sanitização de erros e logs;
- segredo/credential store e acessos administrativos.

Não foram testados webhooks funcionais para evitar efeitos em produção. A avaliação de versão/patches deve usar inventário do owner e changelog oficial numa tarefa de infraestrutura, sem upgrade automático.

## Auditoria e logging

`logs_auditoria` é documental. Para aprovação, operações de cliente, permissões, documentos e Central de Operações devem demonstrar ator/principal, request ID, recurso, resultado, timestamp UTC e alteração mínima, sem token/payload bruto. Log operacional do n8n não substitui auditoria de negócio.

## Decisão de segurança

Não criar credenciais, middleware HMAC ou endpoints nesta fase. A ordem segura é: homologação isolada → verification package → repetir testes 09B → aprovar remediações pequenas → somente então planejar implementação do Hub.
