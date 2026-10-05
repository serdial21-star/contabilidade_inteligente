# Patch mínimo — `admin/documentos-v2`

O export original de **API - Admin - Listagens Gerais V2 (Corrigido)** não é
versionado neste repositório. Para não reconstruir nem alterar silenciosamente
o restante do workflow, aplique somente este acréscimo no `SELECT` que já lista
`inbox_documentos` (alias `d`):

```sql
COALESCE((
    SELECT JSON_ARRAYAGG(JSON_OBJECT(
        'id', x.id,
        'mensagem', x.mensagem,
        'arquivo_url', x.anexo_url,
        'arquivo_nome', x.anexo_nome,
        'criado_em', x.criado_em,
        'autor', x.remetente_tipo,
        'tipo', IF(x.remetente_tipo = 'Cliente', 'cliente', 'equipe')
    ) ORDER BY x.criado_em, x.id)
    FROM inbox_documentos_complementos AS x
    WHERE x.documento_id = d.id
      AND x.cliente_id = d.cliente_id
), JSON_ARRAY()) AS complementos
```

Regras do patch:

- preserve todos os demais campos, joins, filtros, autenticação e conexões;
- não concatene valores da requisição: mantenha `queryReplacement` em toda
  condição que use entrada do usuário;
- o nó de código que monta a resposta deve converter `complementos` de JSON
  textual para array quando necessário, sem remover os demais campos;
- a ordem é cronológica (`criado_em`, `id`);
- importe/publice o workflow inteiro somente depois de comparar o diff do
  export antes/depois e confirmar que esta foi a única mudança funcional;
- o endurecimento geral de `admin/documentos-v2` permanece no item 25.

Este patch é deliberadamente textual porque o baseline fornecido ao diagnóstico
não foi incorporado ao Git. Inventar um JSON completo criaria risco de remover
rotas e regras existentes do workflow multi-endpoint.
