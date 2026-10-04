# Checkpoint de sessão — 03/10/2026

Registro de fim de dia. Não contém token, senha, credencial, ID de pasta, e-mail
ou dado de cliente. Detalhes e evidências de cada item estão nos arquivos das
tarefas em `docs/colaboracao/tarefas/`.

## 1. Concluído e publicado hoje

| Tarefa | O que mudou em produção |
|---|---|
| T-0003 | Migration `003` aplicada; listagem, edição e criação de clientes exigem permissão por módulo (D1) e só Administrador troca e-mail/documento (D2). Correção da linha vazia da listagem (`6ebaf54`). |
| T-0004 | Workflow de permissões do funcionário corrigido no n8n; menu do Operador volta a aparecer. |
| T-0005 | Migration `004` aplicada; "Sair" do painel e do portal revoga a sessão no servidor (workflows `admin/logout-v1` e `cliente/logout-v1`; frontend publicado pelo Lovable). |

## 2. T-0006 — publicação parcial (em andamento)

**Já em produção:**
- migration `005` aplicada (`sp_admin_module_authorize`, verificada `INVOKER`), com backup prévio;
- `portal/honorarios-v2` endurecido ativo; sessão revogada recusada (teste 200 → logout → 401);
- `admin/upload-xml` endurecido (versão com Merge) ativo: recusa sem login (401) e processa com login — arquivos chegaram ao Drive do cliente de teste;
- desativados: 4 workflows antigos sem autenticação (`portal/meus-documentos`, `portal/meus-chamados`, `admin/novo-cliente` V8, `portal/receber-arquivo` V5), `admin/tasks` e o workflow do Colab CND (`admin/integracao-cnd-v1`);
- retenção de execuções desligada no upload-xml e execuções com XML apagadas;
- credenciais expostas em workflows inativos: token da Meta já expirado; chave do Google excluída; valores removidos dos nós; cópia local da exportação apagada.

**Divergência entre produção e repositório (resolver primeiro):** no workflow ativo do upload-xml, o nó "Separar XMLs" foi editado à mão para aceitar `/^arquivos\d*$/i` (antes `\d+`). O arquivo `docs/integration/system_a_webhook_hardening/n8n_admin_upload_xml_v7_hardened.json` ainda tem `\d+`. O Codex deve aplicar a mesma troca e o teste correspondente.

**Ajuste do Codex salvo sem aceite:** a versão com Merge do upload-xml e da apuração, o runbook e os testes foram commitados como trabalho em andamento para não se perderem (ver mensagem do commit). Aceite depende do teste real e da revisão final.

**Ainda não publicado:** motor de obrigações só com cron (importado? ver pendência 2), `ferramentas-ia/apuracao-icms` endurecido, prompt do Lovable da T-0006 (`ai-analyst`, allowlist do `proxy-webhook`, Biblioteca legada, chamado sem login).

## 3. Pendências de verificação deixadas pelo usuário

1. **Banco do upload-xml:** confirmar as notas gravadas em `processamento_xml_nfe` para o cliente de teste (consulta na T-0006).
2. **Motor de obrigações:** o GET de teste em `admin-motor-obrigacoes-v1` respondeu **500**, não 404 — sinal de que algum workflow ainda atende o path. Conferir se o motor antigo está desativado e se houve execução nesse horário (pode ter disparado a geração de obrigações). **Prioridade alta.**
3. Push dos commits locais.

## 4. Agenda do próximo dia (em ordem)

1. **Push** e conferência do CI.
2. **Motor de obrigações** (pendência 2): verificar ativo/inativo e execuções; se o antigo rodou, conferir no banco se gerou obrigações indevidas antes de qualquer outra ação.
3. **Upload-xml:** consulta do banco (pendência 1); acionar o Codex para espelhar `\d*` no repositório; revisão e aceite.
4. **Apuração ICMS:** importar a versão com Merge, trocar pelo antigo, testar com e sem login.
5. **Lovable (T-0006):** aplicar `LOVABLE_PROMPT.md`, revisar o diff antes de publicar, testar todas as telas (allowlist do proxy pode bloquear chamada não inventariada).
6. **Fechar a T-0006** e registrar no QUADRO.
7. Abrir item novo na fila: Extrator Fiscal XML — arquivar em `01_FISCAL` (hoje grava na raiz da pasta do cliente), cópias duplicadas no Drive a cada envio e resumo da tela mostrando "0 nota(s)" (contrato de resposta). Defeitos anteriores à T-0006.
8. Decidir com o usuário a próxima tarefa da fila, priorizando o que destrava os **testes práticos de uso** (objetivo declarado do usuário).

## 5. Fila (ver `docs/colaboracao/QUADRO.md`)

Itens relevantes criados hoje: 16 (índice `token_hash`), 18 (endurecer workflow de permissões), 20 (endpoints chamados pelo site que não existem no n8n — funcionalidades quebradas), 21 (certidões por API oficial e certificado digital — adiado, exige ADR).

## 6. Rollback disponível

- Workflows substituídos foram renomeados com "(antigo 2026-10-03)" ou "(DESATIVADO 2026-10-03)", não apagados.
- Migrations: `003_down.sql`, `004_down.sql`, `005_down.sql` testados no CI.
- Backups do banco feitos pelo usuário antes de cada migration, guardados fora do repositório.
