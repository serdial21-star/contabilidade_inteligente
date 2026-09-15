# System A Security Gaps

Status baseado em evidência disponível, não em presunção de vulnerabilidade explorável. Sem source/runtime autenticado, controles não demonstrados falham o gate de prontidão.

## Reavaliação dos cinco bloqueadores de segurança

| ID | Bloqueador | Evidência 09B | Risco | Remediação mínima | Impacto |
| --- | --- | --- | --- | --- | --- |
| SG-01 | M2M auth/rotation/replay ausentes | nenhum mecanismo A fornecido | token browser reutilizado ou requests forjados | principal de serviço por ambiente/direção, HMAC, timestamp, replay cache, rotation/revoke | `CONFIRMED_BLOCKER` |
| SG-02 | Escopo tenant/company do service principal | auth A/B atual não demonstra contrato M2M | acesso cross-tenant/company | scopes explícitos, resolução server-side, testes negativos e negação opaca | `CONFIRMED_BLOCKER` de design/implementação |
| SG-03 | Guards/permissões/auditoria A não demonstrados fail-closed | dossiês relatam rotas cliente e fallback; source ausente | exposição de dados/efeitos sem autorização | guards em todas rotas, empty/unknown→deny, 401/403 seguros, audit write | `NOT_VERIFIABLE`, bloqueia produção e contratos A |
| SG-04 | Transporte Drive/SSRF/evidência | nenhuma geração de URL inspecionável | link permanente, exfiltração, conteúdo mutável | URL curta/objeto único, allowlist, hash, size/type/quarantine, download backend | `CONFIRMED_BLOCKER` documental |
| SG-05 | Separação de ambientes/secrets | nenhuma homologação/config apresentada | prod↔dev, segredo reutilizado, dados reais em teste | frontend/n8n/DB/Drive/logs/secrets HOM separados | `CONFIRMED_BLOCKER` |

`SECURITY BLOCKERS CONFIRMED: 4`; um (`SG-03`) permanece sem verificação atual, mas o gate continua reprovado até evidência positiva.

## Browser e sessão

- armazenamento em `localStorage` de `auth_token`/`admin_auth_token`: documentado, não verificado no source atual;
- revogação de logout server-side: `GAP` até prova contrária;
- missing/invalid/expired token → 401: `NOT_TESTED`;
- rotas cliente com guard equivalente a `ClientRouteGuard`: `PARTIAL/NOT_VERIFIABLE`;
- permissões vazias, indefinidas ou módulo desconhecido devem negar; não existe teste disponível;
- CORS deve usar allowlist e responder preflight por contrato de browser; wildcard não é correção permanente.

Esses itens não autorizam um redesign amplo de auth em 09B. Precisam de source+HOM e escopo de remediação próprio.

## n8n

O host público responde e expõe no HTML o release n8n 2.6.4. Workflows não foram acessados; portanto permanecem desconhecidos:

- status active/inactive/duplicate;
- `Respond to Webhook` versus `lastNode`;
- tratamento de OPTIONS/CORS;
- SQL parametrizado versus concatenação;
- sanitização de erros e logs;
- segredo/credential store e acessos administrativos.

Não foram testados webhooks funcionais para evitar efeitos em produção. A avaliação de versão/patches deve usar inventário do owner e changelog oficial numa tarefa de infraestrutura, sem upgrade automático.

## Auditoria e logging

`logs_auditoria` é documental. Para aprovação, operações de cliente, permissões, documentos e Central de Operações devem demonstrar ator/principal, request ID, recurso, resultado, timestamp UTC e alteração mínima, sem token/payload bruto. Log operacional do n8n não substitui auditoria de negócio.

## Decisão de segurança

Não criar credenciais, middleware HMAC ou endpoints nesta fase. A ordem segura é: homologação isolada → verification package → repetir testes 09B → aprovar remediações pequenas → somente então planejar implementação do Hub.
