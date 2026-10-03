# Prompt para o Lovable — inventário completo do site (somente leitura)

Origem: T-0006 (webhooks sem autenticação). Objetivo: saber, a partir do código
do site, quem chama cada endpoint e como cada chamada se autentica. Cole no
Lovable o texto depois da linha `---`. O resultado volta para o Claude.

---

Preciso de um inventário completo e fiel do que existe neste projeto. **Não altere nenhum arquivo, não publique nada e não proponha correções** — apenas leia o código e descreva o que está implementado hoje. Se não tiver certeza de algo, escreva "não confirmado" em vez de supor.

**Regra de segurança da resposta:** nunca copie valores de tokens, senhas, chaves de API, anon keys, service role keys, URLs com credenciais ou dados de clientes. Quando houver um segredo, escreva apenas "[segredo presente em <arquivo>]".

Responda em Markdown, com as seções abaixo, nesta ordem.

### 1. Páginas e rotas
Tabela com: rota | página/componente | área (portal do cliente, painel administrativo, pública) | guarda de acesso aplicada (qual componente/hook, e o que acontece se o usuário não estiver logado ou não tiver permissão) | módulo/ação de permissão verificado (`usePermissoes`, `useCanAccess` etc.).

### 2. Todas as chamadas externas
Uma linha por chamada encontrada no código (fetch, axios, `supabase.functions.invoke`, upload, download). Tabela com:
- arquivo e função de origem;
- página/funcionalidade que a dispara;
- destino exato: URL base + path do webhook n8n (ex.: `admin/upload-xml`), ou nome da edge function do Supabase, ou tabela/bucket do Supabase;
- método HTTP;
- como o token é enviado: cabeçalho `Authorization: Bearer` com `admin_auth_token`, com `auth_token`, no corpo, na query string, ou **nenhum token**;
- campos enviados no corpo que identificam cliente, funcionário ou empresa (ex.: `cliente_id`, `funcionario_id`) — só os nomes dos campos;
- se passa pelo `proxy-webhook` ou chama o n8n diretamente.

Inclua obrigatoriamente, se existirem, as chamadas para: `admin/upload-xml`, `ferramentas-ia/apuracao-icms`, `admin/integracao-cnd-v1`, `admin/tasks`, `admin-motor-obrigacoes-v1`, `portal/honorarios-v2`, `portal/meus-documentos`, `portal/meus-chamados`, `admin/novo-cliente`, `portal/receber-arquivo` (com e sem sufixo `-v2`). Se alguma delas **não** for chamada em nenhum lugar do código, diga explicitamente "não encontrada no código".

### 3. Ferramentas IA
Para cada card da página Ferramentas IA ("Analista de Balanço IA", "Extrator Fiscal XML (NF-e)", "Análise de Apuração de ICMS e CMV", "Inteligência Fiscal"): o que a ferramenta faz, quais chamadas externas faz (referência à seção 2), se exige login, se envia token, e se usa algum modelo de IA (qual serviço e por qual caminho — edge function, n8n ou chamada direta).

### 4. Edge functions do Supabase
Para cada função em `supabase/functions/`: nome | o que faz | se exige JWT (`verify_jwt` no `config.toml` ou equivalente) | se valida o token do Serdial21 (`admin_auth_token`/`auth_token`) ou só repassa | para quais destinos encaminha (paths do n8n, APIs externas) | se há lista de paths permitidos no `proxy-webhook` (transcreva a lista) | quais variáveis de ambiente usa (só os nomes) | se repassa o cabeçalho `Authorization`.

### 5. Supabase: tabelas e armazenamento
Tabelas do Supabase acessadas pelo site (nome, operação, se RLS está ativo e quais políticas existem, conforme as migrations) e buckets de Storage (nome, público ou privado, quem envia e quem lê).

### 6. Autenticação e sessão no navegador
Chaves de `localStorage`/`sessionStorage` usadas (nomes) e para quê; como funcionam login e "Sair" no painel e no portal; o que acontece quando uma chamada retorna 401 ou 403.

### 7. Itens sem uso ou duplicados
Hooks, páginas ou chamadas que parecem antigos, duplicados ou não referenciados (ex.: `useFuncionarios` versus `admin/equipe-v2`).

No final, uma lista curta de **pontos que você não conseguiu confirmar** lendo o código.
