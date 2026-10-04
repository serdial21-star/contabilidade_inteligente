# Prompt para o Lovable — detalhe e complemento de chamados e documentos (somente leitura)

Origem: T-0008 (diagnóstico). Cole no Lovable o texto depois da linha `---`. O resultado volta para o Claude.

---

Preciso de uma descrição exata, a partir do código atual, de quatro funcionalidades do **portal do cliente**. **Não altere nenhum arquivo, não publique nada e não proponha correções.** Se algo não puder ser confirmado lendo o código, escreva "não confirmado".

**Regra de segurança da resposta:** não copie tokens, chaves, senhas, e-mails reais nem dados de clientes. Use nomes de campos e tipos, nunca valores reais.

As funcionalidades são as chamadas feitas pelo `proxy-webhook` para:
1. `POST /portal/detalhe-chamado` (TicketDetailDrawer do portal);
2. `POST /portal/complementar-chamado` (TicketDetailDrawer do portal);
3. `POST /portal/detalhe-documento` (DocumentDetailDrawer);
4. `POST /portal/complementar-documento` (DocumentDetailDrawer).

Para **cada uma**, responda em Markdown:

### A. Quando é disparada
Tela, componente, ação do usuário (clique em quê) e quais dados da **lista** anterior são usados para abrir o detalhe (por exemplo, de `/portal/meus-chamados-v2` ou `/portal/meus-documentos-v2`): nome e tipo de cada campo.

### B. Requisição enviada
- cabeçalhos (só os nomes, ex.: `Authorization: Bearer auth_token`);
- formato do corpo (JSON ou multipart);
- **todos os campos do corpo**, com nome exato, tipo e obrigatoriedade;
- para envio de arquivos: nome do campo de arquivo, se aceita vários, tipos e tamanho máximo verificados na tela.

### C. Resposta esperada
- a **estrutura completa** que o código lê (`success`, `data`, listas, objetos aninhados), com nome exato e tipo de cada campo, e quais campos são exibidos e onde;
- o que acontece com resposta vazia, `success: false`, 401, 403, 404, 422 e 500;
- se há paginação, ordenação ou filtro.

### D. Texto e estados da tela
Mensagens exibidas (carregando, vazio, erro, sucesso) e se a tela recarrega a lista depois de complementar.

### E. Tipos e interfaces TypeScript
Transcreva as interfaces/tipos usados nessas quatro chamadas (somente a definição dos tipos, sem dados).

### F. Lado administrativo correspondente
Se o painel administrativo mostra as mesmas mensagens/complementos (por exemplo, em AdminTickets com `/admin/responder-ticket-v2` ou em AdminDocumentos), descreva os campos que o painel lê e envia, para que o portal e o painel usem o mesmo modelo.

No final, liste os pontos que você não conseguiu confirmar.
