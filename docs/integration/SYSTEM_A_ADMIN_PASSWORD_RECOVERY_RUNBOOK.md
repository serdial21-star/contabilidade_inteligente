# Recuperação administrativa de senha do Sistema A

Este runbook implementa a decisão do ADR 0016. Ele não autoriza copiar dados
do Sistema A para o Sistema B nem registrar senha, token ou hash em evidências.

## Gate 1 — preflight somente leitura

1. No phpMyAdmin, selecione o banco operacional do Sistema A.
2. Execute `SYSTEM_A_ADMIN_PASSWORD_RECOVERY_PREFLIGHT.sql`.
3. Confirme que `random_bytes_length` retorna `32`.
4. Preserve somente os resultados de estrutura. Não exporte linhas das
   tabelas e não compartilhe valores de e-mail, senha, token ou sessão.
5. Revise tipos, chaves, engine e collation antes de escrever a migration. Não
   invente a FK ou as colunas da auditoria a partir de documentação antiga.

Saída esperada do gate: versão real do servidor, suporte a `RANDOM_BYTES`,
timezone e `SHOW CREATE TABLE` das quatro tabelas relacionadas.

## Gate 2 — backup

Antes de DDL ou publicação:

1. gere um backup pelo mecanismo gerenciado da Hostinger para o banco inteiro;
2. registre data/hora, escopo e identificador do backup, sem copiar seu
   conteúdo para o repositório;
3. confirme que existe caminho documentado de restauração;
4. exporte os workflows atuais de login e recuperação do n8n;
5. calcule localmente o SHA-256 dos exports e registre somente os hashes.

O backup contém dados pessoais e hashes de senha. Ele não deve ser anexado à
conversa, versionado ou enviado ao Sistema B.

**Concluído em 2026-09-29 às 14:07**, conforme confirmação explícita do dono do
produto. O conteúdo do backup não foi fornecido ao repositório nem ao agente.

## Gate 3 — artefatos

Somente após os Gates 1 e 2:

1. criar migration reversível da tabela de tokens administrativos;
2. criar workflow inativo em homologação;
3. configurar CORS com a origem exata do Sistema A;
4. desativar persistência de dados de execução para o workflow, na extensão
   suportada pelo n8n;
5. criar a tela administrativa de redefinição sem reutilizar a rota de cliente;
6. testar com funcionário sintético antes de qualquer conta real.

Artefatos preparados:

- `system_a_admin_password_recovery/001_up.sql`;
- `system_a_admin_password_recovery/001_down.sql`;
- `system_a_admin_password_recovery/verify.sql`;
- `system_a_admin_password_recovery/n8n_admin_password_recovery.json`;
- `system_a_admin_password_recovery/AdminRedefinirSenha.tsx`.

O workflow é importado inativo e sem credenciais. Depois da importação, associe
manualmente a credencial MySQL já usada por `admin/login-v2` aos dois nós
MySQL e a credencial SMTP existente ao nó de e-mail. Não publique ainda.

No frontend do Sistema A:

1. copie `AdminRedefinirSenha.tsx` para `src/pages/admin/`;
2. importe o componente em `src/App.tsx`;
3. adicione a rota pública
   `<Route path="/admin/redefinir-senha" element={<AdminRedefinirSenha />} />`;
4. mantenha a chamada pelo `proxy-webhook`;
5. confirme que o link do e-mail usa `#token=`, não `?token=`.

O workflow aceita `X-Rate-Limit-Key` de um proxy confiável para o limite por
origem. Enquanto o proxy não fornecer uma chave confiável, ele usa `unknown` e
aplica um limite global conservador além do limite por identidade. Não aceite
um header enviado diretamente pela internet como identidade de origem.

Os nós MySQL do n8n podem representar o retorno de uma `PROCEDURE` MariaDB
como dois itens: o result set dentro de uma lista e, em seguida, metadados do
driver. Os nós `Normalizar Solicitacao` e `Normalizar Aplicacao` reduzem essa
saída a uma única linha identificada por `request_id` antes dos condicionais.
Não remova esses normalizadores nem conecte os condicionais diretamente aos
nós MySQL.

## Critérios obrigatórios

- token gerado pelo banco com `RANDOM_BYTES`, nunca por `Math.random`;
- somente o hash do token persiste;
- validade de 30 minutos e consumo único;
- nova solicitação revoga tokens anteriores do mesmo funcionário;
- resposta de solicitação sempre neutra;
- rate limiting por e-mail normalizado e origem, sem registrar o e-mail bruto;
- senha mínima validada antes do efeito;
- atualização da senha, consumo do token, revogação das sessões e auditoria
  executados atomicamente;
- nenhum log ou evento contém senha, token, hash ou payload bruto;
- testes negativos para token inválido, expirado, usado e concorrente;
- smoke final confirma login e invalidação das sessões antigas.

## Rollback

Se a homologação falhar, mantenha o workflow inativo e reverta somente a
migration nova. Não restaure `funcionarios` sobre dados mais recentes. Em caso
de efeito parcial em produção, interrompa a publicação e restaure pelo plano
aprovado, preservando a evidência do incidente.

## Homologação mínima

Use somente um funcionário sintético e uma caixa de e-mail controlada:

1. e-mail inexistente retorna a mesma mensagem neutra e não envia mensagem;
2. e-mail ativo envia um link com fragmento e validade de 30 minutos;
3. token inválido, expirado, revogado ou usado retorna erro genérico;
4. senha com menos de 12 caracteres é rejeitada sem efeito;
5. token válido altera uma vez, revoga sessões antigas e cria auditoria sem
   senha, token, hash ou e-mail;
6. segundo uso do mesmo token falha;
7. quarta solicitação para a mesma identidade em 15 minutos não envia e-mail;
8. nenhuma execução do workflow fica salva no n8n;
9. o login antigo continua funcionando com a nova senha;
10. somente depois desses testes execute smoke com a conta real autorizada.

## Registro de homologação

- 2026-09-29: migration validada isoladamente em MariaDB 11.8.9, incluindo
  upgrade, testes funcionais e rollback.
- 2026-09-29: migration aplicada ao banco operacional e verificada: tabela com
  12 colunas, duas procedures `SQL SECURITY INVOKER` e FK para `funcionarios`.
- 2026-09-29: solicitação com e-mail sintético inexistente retornou resposta
  neutra, `should_send = 0` e não acionou o nó SMTP. O teste revelou a forma
  aninhada do retorno de `CALL`, corrigida pelos normalizadores acima.
