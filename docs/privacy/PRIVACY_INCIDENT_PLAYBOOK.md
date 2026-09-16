# Playbook técnico de incidente de privacidade

**Status:** técnico. A existência, o prazo, os destinatários e o conteúdo de qualquer notificação são `LEGAL_REVIEW_REQUIRED`.

1. **Abrir e preservar:** ID opaco, UTC, detector, correlação e evidência mínima; nunca copiar documento bruto, segredo ou lista integral de titulares ao ticket.
2. **Conter:** suspender credencial, rota, integração ou job afetado; restringir storage/backup; preservar auditoria e aplicar hold quando autorizado.
3. **Delimitar:** confirmar categorias, tenants/empresas, período, atores, destinatários, cópias e integridade. Investigação cross-tenant requer autorização documentada e resultado segregado.
4. **Escalonar:** engenharia entrega fatos; segurança coordena contenção; responsável do escritório fornece contexto; encarregado/jurídico decide qualificação e comunicação.
5. **Erradicar e recuperar:** corrigir causa, rotacionar segredos, testar isolamento, restaurar pelo runbook e reconciliar holds/ações de privacidade posteriores ao backup.
6. **Validar e encerrar:** regressão, auditoria, ações corretivas, aprovação dos responsáveis e exercício de lições aprendidas.

## Pacote factual para decisão humana

- linha do tempo em UTC e nível de confiança;
- sistemas, fornecedores e ambientes envolvidos;
- categorias e volume estimado, sem anexar conteúdo excessivo;
- tenants/empresas afetados, mantidos segregados;
- medidas de contenção, risco residual e recuperação;
- incertezas, evidências preservadas e contatos operacionais.

Não contatar autoridade, titulares, imprensa, cliente ou fornecedor em nome da organização sem autoridade operacional e aprovação jurídica apropriadas. Todo prazo de escalonamento interno ou externo permanece `LEGAL_REVIEW_REQUIRED` até ser formalmente aprovado.

## Tabletop: suspeita de exposição cross-tenant

Evidência esperada do exercício: registrar ID e UTC; conter a rota/credencial;
preservar logs, AuditEvents e hashes; identificar separadamente os tenants,
empresas, período e objetos potencialmente afetados; revogar ou proteger o
acesso; classificar tecnicamente o incidente; e entregar o pacote factual ao
responsável por Privacy/Security e ao jurídico. Não se acessa conteúdo de outro
tenant para “confirmar” sem autorização investigativa, e nenhuma notificação
real é feita no tabletop.
