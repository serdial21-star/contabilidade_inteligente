# ADR 0004 — Auditoria transversal inicial

## Status

Aceita na Execução 04, em 04/09/2026.

## Contexto

A Execução 03 criou persistência e autorização, mas não criou APIs ou casos
de uso de mutação. A arquitetura aprovada exige que efeito crítico e evento
mínimo sejam gravados no mesmo commit e prevê um commit hook de auditoria.

## Decisão

- audit é módulo próprio, com domínio puro, porta de repositório,
  AuditService e adaptador SQLAlchemy.
- AuditEvent registra escopo, ator, origem, ação, objeto, estados minimizados,
  motivo, correlação, causalidade, timestamp UTC e hash SHA-256 canônico.
- Consultas do repositório sempre exigem tenant_id.
- Eventos persistidos não podem ser atualizados ou excluídos pelo ORM.
- Não existe endpoint comum de alteração ou exclusão.
- Um commit hook observa criação e alteração de Tenant, Company,
  TenantMembership e RoleBinding.
- Essas mutações falham sem AuditContext. O evento e a mudança usam a mesma
  Session; commit e rollback abrangem ambos.
- Exclusão física das quatro entidades é recusada; correções usam transição
  de estado e novo evento.
- Before/after usa lista explícita de campos. Nome empresarial, identificador
  fiscal, e-mail e conteúdo bruto não são copiados.
- Campos com indício de senha, token, segredo, credencial, XML, documento
  bruto ou prompt são recusados.

## Consequências

A aplicação falha de forma segura se uma mutação coberta tentar ignorar a
auditoria. A proteção é append-only na aplicação e tem hash de detecção de
alteração. Proteção física adicional, retenção e encadeamento criptográfico
podem evoluir depois sem alterar o contrato básico.

Como ainda não há autenticação externa nem ExecutionContext HTTP completo,
esta execução não publica endpoint de leitura. A permissão audit.read já
existe e deverá ser aplicada quando a consulta autorizada for exposta.
