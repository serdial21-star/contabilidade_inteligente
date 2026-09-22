# Relatório de Varredura — Portal do Cliente e Painel Admin Serdial21

Fonte: relatório de varredura estática gerado pela ferramenta Lovable (plataforma usada para construir o Sistema A) e fornecido pelo dono do produto em 2026-09-21. Primeira evidência de nível código-fonte do Sistema A disponível neste repositório; os documentos em `docs/integration/` produzidos na Phase 09A/09B usaram somente os três dossiês descritivos abaixo listados em `docs/integration-input/`. Classificação conforme `SERDIAL21_INTEGRATION_READINESS.md`: este relatório é `DOCUMENTED_BY_THIRD_PARTY_SOURCE_REVIEW` — mais forte que os dossiês (`DOCUMENTED`), mas não equivale a `VERIFIED_IN_AVAILABLE_CODE`, pois nem o snapshot do repositório nem o workflow n8n foram entregues a este workspace; cobre apenas frontend e três Edge Functions Supabase, não o backend n8n/MySQL.

Varredura de frontend, login, permissões, funções de nuvem, integrações n8n e registros de build/console/rede. Nenhum arquivo foi alterado. O sistema compila sem erros e os registros do navegador estão limpos. Foram encontradas 5 falhas graves, 3 altas, 3 médias e itens de limpeza.

## 1. GRAVE — Acesso liberado quando a permissão não chega

| Onde | Comportamento atual |
|---|---|
| `usePermissoes.ts:98-104` | Enquanto carrega, libera tudo |
| `usePermissoes.ts:102`, `:122` | Lista de permissões vazia = libera tudo |
| `useClientPermissoes.ts:85-87` | Mesmo padrão no portal do cliente |
| `useCanAccess.ts:13-16` | Cargo ausente = libera acesso |

Erro de rede, servidor fora do ar ou funcionário sem permissão cadastrada resultam em acesso total, inclusive Equipe e Configurações (`App.tsx:78-79`, protegidas por dois guardas que têm o mesmo fallback). Agravante: `usePermissoes.ts:59-61` e `useClientPermissoes.ts:53-54` aceitam a resposta sem verificar `success` — erro com 200 OK vira lista vazia, e lista vazia libera tudo.

## 2. GRAVE — Nenhuma chamada tem tempo limite

`apiClient.ts:28`, `useTasks.ts:142`, `useAgenda.ts:30`, `useClientes.ts:18`, `useTickets.ts:44/67/78/89/106`, `AdminAuthContext.tsx:101`. Se o n8n travar, a tela fica "carregando" para sempre, sem mensagem nem botão de tentar de novo.

## 3. GRAVE — Leitura da resposta pode quebrar a tela

`AdminAuthContext.tsx:53` (login) e `:112` (todas as chamadas admin) convertem a resposta sem proteção. Resposta em HTML (502, manutenção) quebra o fluxo em vez de mostrar erro amigável. O padrão correto já existe em `useTickets.ts:25-33` e `useListas.ts:52-58`.

## 4. GRAVE — Funções de nuvem abertas

`supabase/config.toml:4-7` — `ai-analyst` e `proxy-file-upload` sem verificação de autenticação. `proxy-file-upload/index.ts:18-28` aceita qualquer destino vindo da URL, sem lista de permitidos, e só repassa o cabeçalho de login. Quem tiver o endereço chama qualquer webhook do n8n e consome os créditos de IA sem estar logado. As três funções liberam qualquer origem.

## 5. GRAVE — Código antigo de tickets sem login

`src/hooks/useTickets.ts` chama `webhook/admin/tickets` **sem token**, incluindo criar, atualizar e excluir. A tela atual usa outro caminho (`AdminTickets.tsx`, `-v2`) — é código morto, mas continua funcional no projeto.

## 6. ALTO — Recarregamento em laço

`AdminAuthContext.tsx:74` recria a função de comunicação a cada render; `useAtalhos.ts:123` e `useFuncionarios.ts:14-28` dependem dela, podendo recarregar sem parar e sobrecarregar o n8n.

## 7. ALTO — Erros do servidor tratados como sucesso

`useAdminDashboard.ts:58` (`json.data || json` sem conferir `success`), `useClientes.ts:24-25` (erro vira lista vazia), `useOptionsAPI.ts:26-35`, `useTickets.ts:47-49`. O padrão correto existe em `useAtalhos.ts:80`.

## 8. ALTO — Saída forçada de dentro dos carregamentos

`useAdminDashboard.ts:54`, `useAgenda.ts:33`, `useTasks.ts:153/173/217`, `AdminAuthContext.tsx:107/118` recarregam a página inteira para voltar ao login — perdem o estado e podem disparar dois redirecionamentos juntos. A detecção de sessão expirada (`AdminAuthContext.tsx:116`) depende do texto exato "sessão expirada" vindo do n8n.

## 9. MÉDIO — Versões dos endereços n8n misturadas

- Impostos: `/admin/impostos` (`useImpostos.ts:110,145`) x `/admin/impostos-v2` (`AdminImpostos.tsx:191`)
- Tickets: `/admin/tickets` sem login x `/admin/tickets-v2` (`AdminTickets.tsx:88,136,151`)
- Kanban: `admin-kanban-v3` e `admin-delete-item-v3` junto de `admin-create-item-v5`/`admin-update-item-v5` (`useTasks.ts:94-97`)
- Fora do padrão: `listar-arquivos` (`Biblioteca.tsx:28`), `portal-serdial-v2` (`Login.tsx:28`)
- Ainda ausente no n8n: `/admin/upload-documento-cliente` (`AdminUploadDocumentosForm.tsx:183`)

## 10. MÉDIO — Dados sensíveis no registro do navegador

`AdminAuthContext.tsx:99,103,114` registra corpo e resposta completos. Também verboso em `useTasks.ts` (10 pontos), `kanbanContract.ts:189,243,288`, `ItemCreateModal.tsx`, `ItemEditDrawer.tsx`, `AdminUploadDocumentosForm.tsx`, `AdminHonorarios.tsx`, `AdminImpostos.tsx`.

## 11. MÉDIO — Sessão e rotas

Token sem validade nem renovação (`AdminAuthContext.tsx:59`, `apiClient.ts:9-11`). `ClientRouteGuard.tsx:16,51-54` é apenas visual. `/admin/entregas`, `/admin/tarefas`, `/admin/agenda` (`App.tsx:76,84,85`) redirecionam sem guarda. Não há página 404 dentro do painel. Regra de cargo repetida em 3+ arquivos.

## 12. BAIXO — Limpeza

50 ocorrências de `any`; cores fixas fora do tema em `AdminToolbar.tsx:129,132`, `TicketKanban.tsx:22`, `TicketTable.tsx:27`, `AnalystCharts.tsx:15`, `AdminConfiguracoes.tsx:29-31`. Nenhum `TODO`/`FIXME` pendente.

---

**Atenção original do relatório:** ativar "negar por padrão" antes de cadastrar as permissões no banco pode bloquear funcionários que hoje entram só pelo fallback permissivo. O ajuste no n8n/MySQL precisa acompanhar essa correção.

**Nota de escopo (Sistema B):** nenhum arquivo deste repositório foi alterado ao registrar este relatório. Achados 1–12 dizem respeito exclusivamente ao Sistema A (código fora deste workspace); ver `docs/integration/SYSTEM_A_SECURITY_GAPS.md`, `docs/integration/SYSTEM_A_RUNTIME_VERIFICATION.md` e `docs/integration/CONNECT_HUB_PREREQUISITES.md` para como esta evidência foi classificada e o que ela muda (e não muda) nos gates de integração já registrados.
