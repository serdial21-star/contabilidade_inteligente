# Checkpoint de sessao - 30/09/2026

## Escopo concluido

Cadastro, listagem, edicao e recuperacao de senha de clientes do Sistema A
foram endurecidos sem alterar os contratos publicos usados pelo frontend.
Este registro nao contem nome, e-mail, CPF/CNPJ, token, credencial, ID de pasta
ou payload de cliente.

## Banco do Sistema A

- backup anterior a alteracao confirmado pelo operador;
- `001_up.sql` aplicado e verificado;
- `002_up.sql` aplicado e verificado;
- identificador fiscal canonico possui indice unico;
- tabela segura de recuperacao de senha criada;
- tabela preexistente de sessoes foi preservada;
- coluna opcional `clientes.telefone` criada;
- procedures de criacao, vinculo de pasta, recuperacao e edicao usam
  `SQL SECURITY INVOKER`;
- a identidade administrativa da edicao vem do bearer token; o
  `funcionario_id` enviado pelo navegador nao e confiado;
- zero documentos fiscais canonicos duplicados no preflight.

## Workflows n8n

- `API - Admin - Novo Cliente V3 (Seguro)` configurado;
- `API - Admin - Lista Clientes V2.1 (Completa)` publicado;
- `API - Admin - Editar Cliente V1 (Seguro)` publicado;
- `[Auth] Gestao de Senhas Cliente v2 (Seguro)` configurado;
- listagem antiga foi despublicada antes da publicacao da substituta no mesmo
  path;
- credenciais foram associadas pela interface e nao registradas no
  repositorio;
- execucoes de sucesso, falha, manuais e progresso nao sao retidas;
- acesso MCP permanece desativado.

## Frontend

- versao aprovada publicada pelo Lovable;
- 15 testes do frontend aprovados;
- build de producao aprovado, somente com aviso de tamanho de bundle;
- dominio principal confirmou a nova tela de edicao;
- status `Ativo`, `Inativo` e `Lead` disponiveis;
- CPF, CNPJ numerico e CNPJ alfanumerico sao validados;
- token de redefinicao permanece somente no fragmento `#token=` e e removido
  da barra de endereco.

## Evidencias operacionais

- endpoints de listagem e edicao recusaram token sintetico invalido com HTTP
  401;
- listagem autenticada carregou pelo frontend;
- edicao positiva de cadastro sintetico persistiu CNPJ alfanumerico e status
  `Lead`;
- o resultado da procedure retornou `should_send=0` e nenhum e-mail foi
  enviado;
- verificacao no banco confirmou zero sessoes ativas, zero links pendentes e
  auditoria da transicao de status.

## Incidente contido durante a validacao

Uma execucao do n8n exibiu um bearer token administrativo nos dados salvos. A
sessao foi renovada, a execucao foi excluida e a retencao foi desativada nos
quatro workflows novos. Nao reproduzir o token em documento, issue, commit,
captura ou conversa.

## Riscos e pendencias restantes

- o login legado do cliente ainda usa geracao de token e SQL que precisam ser
  substituidos em uma entrega separada;
- a criacao de pastas no Google Drive continua sendo efeito externo posterior
  ao commit no banco e exige reconciliacao se falhar;
- revisar workflows legados fora deste pacote para impedir retencao de tokens
  e dados pessoais;
- executar nova verificacao de seguranca do frontend antes de divulgacao
  ampla;
- confirmar backup pos-liberacao antes da proxima mudanca de schema ou
  workflow.

## Proxima retomada

1. Ler `AGENTS.md`, este checkpoint e
   `docs/integration/SYSTEM_A_CLIENT_MANAGEMENT_RUNBOOK.md`.
2. Confirmar backup pos-liberacao do banco do Sistema A.
3. Auditar retencao e geracao de tokens nos workflows legados de login antes
   de iniciar outra funcionalidade.
4. Nao reexecutar migrations, nao reimportar workflows e nao alterar o
   cadastro sintetico usado no teste sem uma finalidade registrada.
