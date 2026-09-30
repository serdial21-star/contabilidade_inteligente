# Cadastro e acesso seguro de clientes do Sistema A

Este pacote corrige os workflows de cadastro e listagem de clientes e substitui
o fluxo legado de senha compartilhada/token em texto puro. Ele nao altera o
Sistema B e nao deve ser aplicado sem backup do banco operacional do Sistema A.

## Estado verificado em 30/09/2026

- backup operacional confirmado as 10:27;
- nenhum grupo de CPF/CNPJ canonico duplicado;
- nenhum grupo de e-mail normalizado duplicado;
- `tokens_recuperacao` inexistente;
- `security_sessoes_clientes` preexistente; a primeira consulta retornou vazio
  porque usou `DATABASE()` sob o contexto incorreto de `information_schema`;
- MariaDB 11.8.9, InnoDB e `RANDOM_BYTES(32)` disponiveis.

Nenhum nome, e-mail, CPF/CNPJ, senha ou token real e registrado neste pacote.

## Artefatos

- `SYSTEM_A_CLIENT_MANAGEMENT_PREFLIGHT.sql`;
- `system_a_client_management/001_up.sql`;
- `system_a_client_management/001_down.sql`;
- `system_a_client_management/002_up.sql`;
- `system_a_client_management/002_down.sql`;
- `system_a_client_management/verify.sql`;
- `system_a_client_management/n8n_admin_client_create_v3.json`;
- `system_a_client_management/n8n_admin_client_list_v2.json`;
- `system_a_client_management/n8n_client_password_recovery_v2.json`;
- `system_a_client_management/n8n_admin_client_update_v1.json`;
- `system_a_client_management/LOVABLE_PROMPT.md`.

## Ordem obrigatoria

1. Execute `SYSTEM_A_CLIENT_MANAGEMENT_PREFLIGHT.sql` e confirme zeros nos
   quatro contadores de inconsistencias.
2. Importe os quatro JSONs no n8n. Eles entram inativos e sem credenciais.
3. Nao publique ainda e nao desative os workflows atuais.
4. No workflow de cadastro, substitua `CONFIGURE_ROOT_FOLDER_ID` pelo ID da
   pasta raiz atualmente usada pelo workflow antigo.
5. Associe a credencial MySQL existente a todos os nos MySQL.
6. Associe a credencial Google Drive existente aos nos de pasta.
7. Associe a credencial SMTP existente aos nos de e-mail.
8. Confirme que nenhum workflow salva dados de execucao.
9. Aplique `001_up.sql` pelo phpMyAdmin, sem editar o arquivo.
10. Execute `verify.sql`. O esperado e: a tabela nova de reset, quatro
   procedures `INVOKER`, indice fiscal unico e zero duplicidades. A tabela
   preexistente de sessoes nao e recriada.
11. Aplique `002_up.sql`, que adiciona `clientes.telefone` e a procedure
    `sp_admin_cliente_update`. O arquivo deve ser aplicado somente depois do
    `001_up.sql`.
12. No workflow de edicao, associe as credenciais MySQL, Google Drive e SMTP.
13. Use o prompt do Lovable e revise o diff antes de publicar o frontend.
14. Em modo de teste do n8n, valide primeiro com cadastro inteiramente
    sintetico e dominio de e-mail controlado.
15. Somente depois desative os workflows antigos, publique os novos e faca o
    smoke de producao autorizado.

Dois workflows nao podem publicar simultaneamente o mesmo path. A troca deve
ser coordenada: deixe os novos configurados e inativos, desative o antigo e
publique o substituto imediatamente.

## Contratos preservados

- `POST /admin/novo-cliente-v2`;
- `GET /admin/clientes-v2`;
- `POST /admin/editar-cliente-v2` (multipart/form-data);
- `POST /portal/solicitar-senha`;
- `POST /portal/redefinir-senha`;
- corpo da redefinicao: `{ token, nova_senha }`.

## Mudancas intencionais

- CPF/CNPJ e normalizado sem mascara e validado antes de qualquer efeito;
- CNPJ alfanumerico segue 12 posicoes alfanumericas e dois DVs numericos;
- `Lead` pode ficar sem documento; `Ativo` e `Inativo` exigem documento valido;
- e-mail e normalizado em minusculas;
- listagem retorna todos os status e os campos exibidos pela tela;
- edicao ignora `funcionario_id` do formulario e identifica o administrador
  exclusivamente pelo bearer token valido;
- edicao grava `telefone`, atualiza o primeiro e-mail autorizado e preserva
  eventuais e-mails autorizados adicionais;
- ao tornar um cliente inativo ou lead, sessoes e links pendentes sao
  revogados; ao reativar cliente sem senha, um novo link e emitido;
- novo cliente ativo recebe link de ativacao, nunca senha provisoria;
- o token tem 256 bits, dura 30 minutos, e consumido uma vez e persiste apenas
  como SHA-256;
- redefinir a senha revoga sessoes anteriores;
- respostas de recuperacao nao revelam se o e-mail existe;
- CORS fica limitado a `https://serdial21.com`.

## Limites conhecidos

A criacao no banco e atomica, mas o Google Drive e externo. Se a criacao de
pastas falhar depois do commit, o cliente existira sem `id_pasta_raiz`. Nao
repita o cadastro: registre o incidente e vincule uma pasta apos reconciliar o
estado. Uma outbox transacional e recomendada em evolucao futura, mas nao faz
parte desta correcao.

O workflow legado de login do cliente ainda gera token de sessao com
`Math.random` e usa interpolacao SQL. A nova tabela de sessoes e compativel com
o contrato atual, mas a substituicao segura do login e uma entrega separada e
continua pendente. Nao confundir a correcao de cadastro/senha com a eliminacao
desse risco residual.

## Rollback

Use `002_down.sql` antes de `001_down.sql` para reverter a extensao de edicao,
e somente antes de liberar o fluxo a usuarios. Depois que
existirem tokens reais, a remocao da tabela de reset apaga estado de seguranca
e exige plano especifico. O rollback nunca remove a tabela preexistente
`security_sessoes_clientes`, nem clientes, e-mails ou auditoria.

## Evidencia de liberacao em 30/09/2026

- `001_up.sql` e `002_up.sql` aplicados no schema operacional do Sistema A;
- coluna `clientes.telefone` confirmada como `VARCHAR(20) NULL`;
- procedures do pacote confirmadas como `SQL SECURITY INVOKER`;
- workflows seguros de cadastro, listagem, edicao e recuperacao configurados
  e publicados nos paths preservados;
- workflows antigos de cadastro, listagem e recuperacao de senha foram
  exportados e despublicados antes da publicacao de seus substitutos;
- frontend publicado e confirmado no dominio principal;
- teste negativo de edicao recusou bearer token invalido com HTTP 401;
- teste negativo de cadastro recusou bearer token invalido com HTTP 401;
- solicitacao de senha para identidade sintetica inexistente respondeu de
  forma neutra com HTTP 200;
- aplicacao com token sintetico invalido respondeu HTTP 400;
- teste positivo alterou somente um cadastro sintetico e confirmou CNPJ
  alfanumerico, status, resposta de sucesso e atualizacao da listagem;
- transicao para `Lead` revogou sessoes e links pendentes e gerou auditoria;
- o ramo de e-mail nao foi executado nessa transicao;
- retencao de execucoes de sucesso, falha, manuais e progresso foi desativada
  nos quatro workflows novos; acesso MCP permaneceu desativado.

Durante o teste, uma execucao salva exibiu um bearer token administrativo. A
sessao foi imediatamente renovada, a execucao foi removida e a retencao foi
explicitamente desativada antes de continuar. Nenhum token e reproduzido neste
registro.

Backups pos-liberacao do banco do Sistema A e do n8n, alem das exportacoes
individuais dos workflows novos e substituidos, foram confirmados pelo
operador em 30/09/2026 as 15:58 (America/Sao_Paulo).
