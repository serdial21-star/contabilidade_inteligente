# Threat model prático

| Ameaça | Controles atuais | Risco residual / próxima mitigação |
|---|---|---|
| Roubo de credencial/token | IdP externo, PKCE, token em memória, TLS obrigatório | MFA, sessão curta e resposta a incidente dependem do IdP |
| Token forjado/replay | RS256 fixo, iss/aud/exp/iat, JWKS e membership revalidado | revogação global provider-dependent; rate limit distribuído pendente |
| Cross-tenant/IDOR | tenant do token, CompanyAccess, queries compostas e negação uniforme | regressão obrigatória a cada nova fronteira |
| Arquivo malicioso | limites, extensão/mídia, parser XML sem DTD/entidade, parser OFX limitado | malware scanning para binários genéricos é gap de infraestrutura |
| XSS | escape de texto, CSP same-origin/no-inline e sem payload bruto | QA integrado de browser na Phase 14 |
| Brute force/API abuse | autenticação no IdP e rate limit por classes | backend distribuído/monitoramento ainda requer infraestrutura |
| Exfiltração/cache | DTOs minimizados, `no-store`, logs sem body/query/auth | controles de egress e SIEM pertencem ao ambiente/Phase 12 |
| Alteração de decisão | permissão, segregação, revisão/hash, idempotência, AccountLock e auditoria atômica | UAT e alçadas reais pendentes |
| Alteração de auditoria | modelo append-only, listeners contra update/delete e hash | proteção/backup do banco requer infraestrutura |
| Misconfiguration | validação fail-closed de hom/prod, hosts/origins/HTTPS/debug | revisão do manifesto e evidência do deploy continuam obrigatórias |
| Vazamento de segredo | SecretStr, env/provedor, exemplos fictícios, scan e logs sanitizados | rotação e ACL do provedor ainda não configuradas |

O sistema contábil externo continua autoridade oficial. Aprovação no Serdial21 não equivale a escrituração ou fechamento.
