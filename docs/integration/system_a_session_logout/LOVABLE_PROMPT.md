# Prompt para o Lovable — "Sair" revoga a sessão no servidor (T-0005)

Cole o texto abaixo no Lovable. Antes de publicar, revise o diff: ele deve tocar
apenas as funções de logout do painel administrativo e do portal do cliente.

---

Altere somente o comportamento de "Sair" (logout) do painel administrativo e do
portal do cliente. Não altere login, rotas, guardas, permissões, layout nem
qualquer outra chamada.

1. Painel administrativo (onde hoje o logout remove `admin_auth_token` e
   `admin_user` do `localStorage`, provavelmente em `AdminAuthContext`):
   - leia o token atual (`admin_auth_token`) ANTES de limpar o estado;
   - se houver token, faça `POST` para o webhook `admin/logout-v1`, usando a
     mesma URL base e o mesmo mecanismo das demais chamadas administrativas
     autenticadas, com o cabeçalho `Authorization: Bearer <token>` e corpo `{}`;
   - limite a espera a 5 segundos (`AbortController`);
   - em `finally`, independentemente de sucesso, erro, timeout ou status HTTP:
     remova `admin_auth_token` e `admin_user`, limpe o estado do contexto e
     redirecione para a tela de login administrativa, como já acontece hoje.

2. Portal do cliente (onde hoje o logout remove `auth_token` e `client_user`):
   - mesmo procedimento, com o token `auth_token` e o webhook `cliente/logout-v1`;
   - use exatamente o mesmo mecanismo das demais chamadas autenticadas do
     cliente (por exemplo, se elas passam pelo `proxy-webhook` do Supabase,
     use-o com o path `/cliente/logout-v1`), preservando o cabeçalho
     `Authorization: Bearer <token>`.

Regras:
- O logout local NUNCA pode depender da resposta do servidor: falha de rede não
  pode manter o usuário logado.
- Não registre o token em `console`, toast, log ou mensagem de erro.
- Não exiba erro ao usuário se a chamada falhar; apenas conclua o logout local.
- Não adicione dependência nova.
