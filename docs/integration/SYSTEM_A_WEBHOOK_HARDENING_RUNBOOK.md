# Runbook — T-0006, endurecimento de webhooks do Sistema A

## Escopo e artefatos

- migration `005`: `system_a_webhook_hardening/005_up.sql`, `005_down.sql`, `verify_005.sql`;
- workflows endurecidos, todos exportados inativos e sem credenciais;
- prompt do Lovable e trecho do Colab.

Não execute os passos contra produção antes de CI verde, revisão do Claude e aceite do usuário.

## 1. Pré-publicação

1. Confirme que `Serdial21 - Admin Tasks Kanban v1.0` está inativo e renomeado com `(DESATIVADO 2026-10-03)`.
2. Registre o resultado de `docker exec n8n-n8n-1 printenv GENERIC_TIMEZONE TZ` na T-0006. O workflow do motor não define timezone próprio. Se o valor estiver ausente ou divergir do timezone operacional decidido pelo usuário, pare e peça decisão; não altere silenciosamente.
3. Execute `verify_005.sql`. Exija `utf8mb4_unicode_ci` para `security_sessoes_funcionarios.token_hash` e confira tabelas, colunas e grants.
4. Faça backup do banco do Sistema A e exporte individualmente os cinco workflows ativos anteriores. Não apague os anteriores: renomeie-os como rollback.
5. Gere um segredo aleatório de alta entropia fora do repositório, na máquina do usuário, por exemplo com `python -c "import secrets; print(secrets.token_urlsafe(32))"`. Grave a saída diretamente no Secret do Colab e na credencial do n8n; não a cole em chat, arquivo versionado, tarefa ou log. Crie no n8n uma credencial Header Auth com nome do cabeçalho `X-Serdial21-Integration-Secret`.

## 2. Banco

1. Importe `005_up.sql` no phpMyAdmin.
2. Execute novamente `verify_005.sql`: `sp_admin_module_authorize` deve aparecer como `INVOKER`.
3. Não altere as procedures das migrations 001–004.

## 3. Importação dos workflows

Importe todos inicialmente **inativos**. Como os JSONs não carregam credenciais, reassocie manualmente:

- nós MySQL: credencial MySQL já usada pelo workflow anterior;
- nós Drive/Sheets: as mesmas credenciais Google do workflow anterior;
- webhook CND: a nova credencial Header Auth.

Para cada endpoint: confira path, método, conexões, credenciais e retenção; desative o workflow anterior; só então ative o novo. Não deixe dois workflows ativos com o mesmo path.

Ordem recomendada:

1. `portal/honorarios-v2`;
2. `admin/upload-xml`;
3. `ferramentas-ia/apuracao-icms`;
4. motor de obrigações somente com cron;
5. CND, coordenado com o Secret do Colab.

No CND, atualize o Secret do Colab e ative o workflow protegido na mesma janela. Uma falha intermediária é recuperável por reenvio; não desative a autenticação para contorná-la.

## 4. Testes de publicação

- Upload XML e Apuração: sem token, token malformado, expirado e revogado retornam `401`; funcionário sem `ferramentas_ia/criar` retorna `403`; nenhum nó de Drive/Sheets ou gravação deve aparecer nessas execuções.
- Upload XML: `cliente_id` inválido retorna `400`; inexistente retorna `404`; um cliente de teste autorizado percorre o fluxo normal.
- Honorários: token de cliente vivo retorna somente dados do próprio cliente; token revogado retorna `401`.
- CND: chamada sem cabeçalho e com valor incorreto é rejeitada pelo próprio Webhook antes do primeiro nó; chamada com o Secret correto mantém zeros iniciais do CNPJ e grava uma vez.
- Motor: confirme que só há o gatilho cron `5 6 * * *`; não execute manualmente contra produção apenas para testar.
- Lovable: teste todas as telas que usam `proxy-webhook`, as três ferramentas de IA, download de documento, Biblioteca e abertura de chamado. Path/método fora da allowlist deve retornar `404` sem encaminhamento.
- `ai-analyst`: confirme que um Administrador sem linha explícita `ferramentas_ia/criar` recebe `403` sem chamada ao gateway. Para este endpoint, não há autorização por cargo; a decisão usa somente `modulos.ferramentas_ia.criar` devolvido pelo servidor.

Não copie tokens, dados fiscais, XMLs ou respostas pessoais para a T-0006.

## 5. Rollback por peça

1. Desative somente o workflow novo com problema e reative sua exportação anterior renomeada.
2. No motor, reativar o anterior também restaura o webhook público; faça isso apenas se indispensável e registre o risco.
3. Reverta o Lovable pela publicação anterior se a allowlist bloquear um chamador legítimo; não amplie a lista sem identificar o call site exato.
4. Execute `005_down.sql` somente depois que nenhum workflow ou Edge Function depender de `sp_admin_module_authorize`. O downgrade remove apenas essa procedure; eventos de auditoria permanecem.

Referências de segurança consultadas em 03/10/2026: OWASP Authorization Cheat Sheet e OWASP Server Side Request Forgery Prevention Cheat Sheet.
