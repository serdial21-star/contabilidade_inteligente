# ADR 0016 — Recuperação administrativa de senha no Sistema A

## Status

Aceita por decisão explícita do usuário em 2026-09-29, depois de apresentado o
conflito com a regra anterior que proibia ler ou gravar `funcionarios.senha`.

Esta decisão cria uma exceção estreita para recuperar o acesso administrativo
do Sistema A. Ela não autoriza importar, copiar, sincronizar, registrar ou
expor senhas, hashes ou tokens ao Sistema B.

## Contexto

O frontend do Sistema A chama `POST /admin/solicitar-senha`, mas não existe
workflow ativo para esse caminho. O workflow ativo `POST /admin/login-v2`
consulta `funcionarios`, exige `status = 'Ativo'` e compara a senha pelo hash
SHA-256 legado. O cadastro do funcionário diagnosticado está ativo, possui
e-mail normalizado e um hash hexadecimal de 64 caracteres. A credencial MySQL
do workflow aponta para o banco operacional correto e a conexão foi testada
com sucesso.

O fluxo existente de recuperação atende somente clientes, usa caminhos
`/portal/*` e não deve ser reaproveitado para funcionários. Além da separação
de público, ele usa token produzido por `Math.random()`, SQL interpolado e
outros controles insuficientes.

O n8n 2.6.4 desse ambiente também não disponibiliza `require('crypto')` nem o
global Web Crypto nos nós Code. A tentativa anterior de usar esses recursos
interrompeu os logins e precisou ser revertida. Portanto, o token de
recuperação não pode ser gerado por JavaScript nesse runtime.

## Decisão

1. Criar fluxo administrativo separado, sem compartilhar tabelas, caminhos ou
   regras com o Portal do Cliente.
2. Expor somente:
   - `POST /admin/solicitar-senha`;
   - `POST /admin/redefinir-senha`.
3. Gerar o token com `RANDOM_BYTES()` no MySQL, condicionado a um preflight que
   confirme o suporte real do servidor. Não usar `Math.random()`.
4. Persistir somente o hash do token. O token em claro pode existir apenas na
   memória transitória necessária para compor o link enviado ao destinatário.
5. Aplicar validade de 30 minutos, uso único, revogação dos tokens anteriores e
   limite de solicitações/tentativas.
6. Responder à solicitação de forma neutra, sem revelar se o e-mail existe ou
   se a conta está ativa.
7. A nova senha pode transitar somente no corpo HTTPS da redefinição. Não pode
   ser enviada para logs, auditoria, dados de execução persistidos ou Sistema B.
8. Enquanto o login legado ainda exigir SHA-256, a redefinição grava somente o
   hash compatível já esperado por `admin/login-v2`. A migração para Argon2id
   ou equivalente é uma decisão posterior e deve atualizar login e redefinição
   de forma coordenada.
9. A troca de senha, o consumo do token, a revogação das sessões existentes e
   o evento mínimo de auditoria devem formar um efeito atômico. Se isso não for
   possível com os nós MySQL atuais, o fluxo não será publicado até existir um
   mecanismo transacional verificável.
10. Auditoria registra apenas identificador opaco do funcionário, tipo do
    evento, resultado, request ID e timestamp. E-mail, senha, hash da senha,
    token e hash do token ficam proibidos.
11. CORS deve aceitar somente a origem publicada do Sistema A. `*` não é
    permitido nesses endpoints.
12. Antes de qualquer DDL ou publicação: exportar o workflow atual, gerar
    backup verificável do schema/tabelas afetadas e executar o preflight
    somente leitura.

## Limites da exceção

- Não altera a autoridade do Sistema A sobre sua autenticação.
- Não autoriza o Sistema B a consultar ou gravar `funcionarios.senha`.
- Não autoriza reset de senha de clientes.
- Não autoriza registrar credenciais em arquivos, comandos, screenshots,
  fixtures, logs ou documentos.
- Não autoriza aplicar DDL sem o schema real das tabelas envolvidas.
- Não resolve por si só os demais achados de segurança do Sistema A.

## Alternativas consideradas

1. **Alteração manual no phpMyAdmin:** rejeitada como caminho normal porque
   pode deixar senha em histórico SQL e não produz auditoria adequada.
2. **Reaproveitar o workflow do Portal do Cliente:** rejeitada por misturar
   identidades, tabelas e contratos diferentes e por preservar controles
   inseguros conhecidos.
3. **Gerar token em nó Code do n8n:** rejeitada porque não há fonte de
   aleatoriedade criptográfica disponível no task runner atual.
4. **Migrar imediatamente todo o login para Argon2id:** adiada por ser uma
   alteração maior, com impacto em todos os funcionários e no workflow de
   login. Deve ser executada como fatia própria, com rollout compatível.

## Consequências

- O levantamento de schema e a criação dos artefatos de recuperação ficam
  autorizados dentro dos limites acima.
- A implantação permanece bloqueada até backup e preflight aprovados.
- O primeiro login bem-sucedido após a recuperação deverá ser usado para
  validar a ponte Sistema A → Sistema B; não autoriza sincronização de dados de
  negócio.

## Registro operacional

- 2026-09-29 14:07: backup do banco operacional confirmado pelo dono do
  produto. Nenhum conteúdo do backup foi anexado, lido ou versionado.
- 2026-09-29: migration validada em MariaDB 11.8.9 e aplicada ao banco
  operacional; tabela, procedures com `SQL SECURITY INVOKER` e chave
  estrangeira foram verificadas por consultas somente leitura.
- 2026-09-29: o primeiro teste sintético confirmou a resposta neutra e a
  ausência de envio para identidade inexistente. Como o driver MySQL do n8n
  retorna o result set de `CALL` aninhado junto dos metadados, a integração
  passou a normalizar explicitamente essa saída antes das decisões do fluxo.
- 2026-09-29: a versão v1.1 foi publicada e o dono do produto confirmou a
  conclusão do fluxo real de recuperação administrativa. A evidência registra
  somente o resultado operacional, sem e-mail, senha, link ou token.
