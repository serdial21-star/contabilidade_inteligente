# Runbook — detalhes e complementos do portal (T-0008)

Estes artefatos são para o Sistema A. Nenhum comando deste documento deve ser
executado contra produção sem backup, janela aprovada e conferência humana. O
Codex não executou banco, n8n, Drive, Supabase ou Lovable reais.

## Limite de arquivo

O limite funcional é **10 MiB binários**. Base64 acrescenta aproximadamente
4/3, portanto o maior arquivo gera cerca de 13,34 MiB antes do envelope JSON.
Em 05/10/2026, a documentação oficial do n8n informa limite padrão de 16 MiB
para webhooks (`N8N_PAYLOAD_SIZE_MAX`). A documentação oficial de limites das
Supabase Edge Functions não publica teto de corpo, mas publica 256 MB de memória.
O teste real pelo `proxy-webhook` continua obrigatório: se a configuração do
projeto tiver limite menor, reduza o limite na tela e no workflow em conjunto;
nunca eleve infraestrutura sem análise própria.

Fontes consultadas:

- n8n, *Endpoints environment variables*:
  https://docs.n8n.io/hosting/configuration/environment-variables/endpoints/
- n8n, *Webhook node — maximum payload*:
  https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.webhook/
- Supabase, *Edge Functions limits*:
  https://supabase.com/docs/guides/functions/limits

## Pré-publicação

1. Exporte e guarde fora do repositório os workflows atuais:
   **API - Portal - Consultas V2 (Robusto)** e
   **API - Admin - Listagens Gerais V2 (Corrigido)**. Não inclua credenciais.
2. Antes da 006, execute somente estas consultas de inventário de status:

   ```sql
   SELECT status, COUNT(*)
   FROM tickets_master
   GROUP BY status
   ORDER BY status;

   SELECT status, COUNT(*)
   FROM inbox_documentos
   GROUP BY status
   ORDER BY status;
   ```

   A lista de rótulos terminais implementada é:

   - chamados: `concluido`, `concluído`;
   - documentos: `processado`, `concluido`, `concluído`, `rejeitado`.

   A comparação no código ignora maiúsculas/minúsculas e espaços externos. As
   consultas também mostrarão estados ativos; não classifique um rótulo
   desconhecido por inferência. **Pare e reporte** se existir rótulo terminal
   fora da lista acima (por exemplo, `Resolvido`, `Finalizado` ou `Cancelado`),
   ou se não for possível confirmar com segurança se um rótulo é ativo ou
   terminal. Qualquer ajuste da lista exige decisão registrada na tarefa e
   alteração sincronizada nas procedures, nos dois workflows e nos testes.
3. Faça backup do banco e execute `verify_006.sql` somente para leitura. Pare se
   tipos ou collation de `security_sessoes_clientes.token_hash` divergirem.
4. Confirme `SHOW GRANTS FOR CURRENT_USER` para o usuário do n8n.
5. Aplique `006_up.sql`. Execute `verify_006.sql` novamente: tabela, coluna e
   quatro procedures devem existir, todas `SQL SECURITY INVOKER`.
6. Importe, ainda inativos, os quatro arquivos `n8n_portal_*.json`. Reassocie
   manualmente as credenciais MySQL e Google Drive; os JSONs não as carregam.
7. Em cada workflow, confira **Save successful production executions = Do not
   save**, **Save failed production executions = Do not save**, progresso e
   execuções manuais desabilitados.
8. Confirme os paths exatos e o CORS restrito. Não mantenha workflow antigo no
   mesmo método/path.
9. Aplique somente o acréscimo de `ADMIN_DOCUMENTOS_V2_PATCH.md` no workflow
   administrativo existente e compare o export antes/depois.
10. Aplique `LOVABLE_PROMPT.md`, revise o diff e publique só as mudanças listadas.

## Teste real obrigatório

Use dois clientes sintéticos A e B e nenhum documento real:

1. A abre detalhe do próprio chamado/documento e vê histórico cronológico;
2. A não consegue abrir ou complementar ids de B; ausente e cross-client
   retornam a mesma resposta 404;
3. sessão expirada e revogada retornam 401 sem Drive nem banco;
4. mensagem somente e anexo somente funcionam; o status não muda;
5. PDF, JPEG e PNG válidos funcionam; XML funciona somente em documento;
6. extensão/MIME divergente, assinatura inválida, XML com `DOCTYPE`, arquivo
   vazio e arquivo acima de 10 MiB retornam 422 sem upload;
7. itens fechados retornam 409 sem upload nem complemento;
8. force falha do upload: não pode existir registro no banco;
9. force falha do banco após upload: registre o arquivo órfão para remoção
   manual; não repita automaticamente o efeito desconhecido;
10. a equipe vê complementos de documento no painel e anexos abrem;
11. `logs_auditoria` contém ação, ids técnicos, `request_id` e indicador de
    anexo, mas não mensagem, token, hash nem base64;
12. apague execuções de teste que tenham sido salvas por engano.

## Rollback

Desative os quatro workflows novos e reverta o frontend antes do banco. A
`006_down.sql` recusa execução se houver complementos de documento ou nomes de
anexo de chamado: exporte/preserve conscientemente esses dados antes de qualquer
downgrade. Auditoria e timestamps já produzidos permanecem históricos.
