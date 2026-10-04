# T-0006 — endurecimento das Edge Functions e remoção de fallbacks inseguros

Implemente somente as mudanças abaixo. Não publique antes de mostrar o diff completo. Não crie endpoints, permissões, e-mails ou regras alternativas.

## 1. `ai-analyst`: sessão e permissão antes do custo de IA

1. No chamador de `ai-analyst`, leia `admin_auth_token` e envie-o no cabeçalho `x-app-token`, seguindo o padrão já usado por `sistema-b-bridge-token`.
2. Sem token, responda `401` e não chame o Lovable AI Gateway.
3. Na Edge Function, extraia `x-app-token` sem registrá-lo e valide a sessão Serdial21 no servidor seguindo o padrão de `client-logo`: chame `admin/permissoes/funcionario` com `Authorization: Bearer <token>`.
4. Resposta inválida, falha de rede, `success` diferente de `true`, sessão expirada/revogada ou funcionário inativo: `401`, sem chamada ao gateway.
5. Autorize **somente** quando a resposta do servidor tiver `success === true` e `modulos.ferramentas_ia.criar === true`. Qualquer outro valor, propriedade ausente ou permissão falsa: `403`, sem chamada ao gateway. Não use `admin_user`, `localStorage`, cargo declarado no navegador nem qualquer outro dado do cliente para decidir autorização. A resposta atual de `admin/permissoes/funcionario` não contém cargo. Os Administradores atuais passam porque possuem a linha explícita `ferramentas_ia`/`criar`; um Administrador sem essa linha deve receber `403` neste endpoint.
6. Preserve o contrato de streaming somente depois da autorização. Nunca exponha o token em log ou resposta.

## 2. `proxy-webhook`: allowlist exata de path + método

Substitua o destino livre por um mapa imutável de combinações exatas `método + path`. Derive e confira o mapa contra todos os call sites atuais. O inventário de 03/10/2026 identificou pelo proxy, no mínimo:

- `POST /cliente/logout-v1`
- `POST /portal-serdial-v2`
- `POST /portal/solicitar-senha`
- `POST /portal/redefinir-senha`
- `POST /admin/solicitar-senha`
- `POST /admin/redefinir-senha`
- `POST /portal/me-v2`
- `POST /portal/impostos-v2`
- `POST /portal/meus-chamados-v2`
- `POST /portal/detalhe-chamado`
- `POST /portal/complementar-chamado`
- `POST /portal/meus-documentos-v2`
- `POST /portal/detalhe-documento`
- `POST /portal/complementar-documento`
- `POST /portal/certidoes-v2`
- `POST /portal/livros-contabeis-v2`
- `POST /portal/obrigacoes-v2`
- `POST /portal/honorarios-v2`
- `POST /permissoes/cliente`
- `GET /admin-dashboard-v2`
- `GET /admin-clientes-options-v1`
- `GET /admin-funcionarios-options-v1`
- as combinações literais realmente produzidas por `useListas`
- `POST /admin/impostos`

Não use prefixo, regex ampla, `includes`, URL fornecida pelo cliente nem fallback para path desconhecido. Normalize apenas uma barra inicial e rejeite path com query, fragmento, barras duplicadas, `..`, codificação ambígua ou método não listado.

Determine primeiro o **método efetivamente encaminhado**, aplicando a regra existente de `_method`. Normalize-o para maiúsculas e compare a allowlist usando esse método efetivo, não apenas o método HTTP externo da chamada à Edge Function. `_method` só pode ser uma string cujo valor esteja explicitamente permitido para aquele path; valor ausente, inválido ou diferente da combinação listada retorna `404` sem encaminhar. O método usado no `fetch` ao n8n deve ser exatamente o método já validado. Assim, um `POST` externo permitido não pode sair do proxy como `DELETE`, `PATCH` ou outro método não autorizado.

Destino deve ser montado no servidor como `N8N_BASE_URL` constante + path selecionado do mapa. Desabilite redirects no encaminhamento. Qualquer combinação ausente retorna `404` sem fazer `fetch` ao n8n.

Mantenha `verify_jwt = false`: o cabeçalho `Authorization` transporta o token opaco do Serdial21, não um JWT de sessão do Supabase. Documente essa justificativa ao lado da configuração. Continue apenas repassando o `Authorization`; a autorização final permanece no endpoint n8n.

## 3. Proxies especializados

Verifique `proxy-file-upload` e `proxy-document-download`. Eles devem aceitar somente:

- `POST /ferramentas-ia/apuracao-icms` em `proxy-file-upload`;
- `POST /security/download-documento` em `proxy-document-download`.

O destino deve ser base constante + path escolhido no servidor. Não aceite URL completa, host, esquema, porta ou método do cliente. Ajuste somente se o código atual não cumprir integralmente essas regras.

## 4. Frontend

- Remova `handleBuscarBiblioteca` e toda chamada legada a `listar-arquivos`, inclusive o e-mail fixo e controles que existam apenas para esse fluxo. Não substitua por outro identificador. Preserve as abas e chamadas autenticadas atuais.
- Em `HelpdeskTicketForm`, elimine o fallback de e-mail. Sem usuário autenticado e e-mail da sessão, bloqueie o envio, mostre mensagem para entrar novamente e não faça requisição.

## 5. Verificação antes de publicar

Mostre no relatório:

- arquivos alterados e diff resumido;
- lista final exata de path + método do `proxy-webhook` e o call site de cada entrada;
- evidência de que path/método desconhecido não executa `fetch`;
- evidência de que `_method` inválido ou não permitido para o path não executa `fetch` e de que a allowlist usa o método efetivamente encaminhado;
- evidência de `401`/`403` em `ai-analyst` antes da chamada ao gateway;
- evidência de que `admin_user`, cargo e `localStorage` não participam da autorização do `ai-analyst`;
- confirmação de que nenhum segredo, token ou e-mail fixo foi adicionado.

Referências consultadas em 03/10/2026: OWASP Authorization Cheat Sheet e OWASP Server Side Request Forgery Prevention Cheat Sheet. A autorização é verificada no servidor a cada requisição; destinos conhecidos usam allowlist e URL construída no servidor.
