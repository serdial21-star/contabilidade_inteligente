# Lifecycle operacional de usuario

O procedimento detalhado e canonico esta em `RUNBOOK_ONBOARDING_OFFBOARDING.md`. Este documento e o resumo de plantao para o piloto.

## Onboarding

1. Receber solicitacao aprovada para tenant, companies, role e motivo.
2. Provisionar identidade no IdP e exigir MFA.
3. Criar membership, CompanyAccess e RoleBinding pelo boundary autenticado.
4. Conceder somente privilegio minimo; capacidades privacy e administrativas nao sao concedidas por padrao.
5. Verificar primeiro login, uma company permitida e uma negada; registrar referencia de auditoria e correlation id, nunca token.

## Offboarding e conta comprometida

1. Desabilitar/revogar a identidade no IdP imediatamente.
2. Revogar membership, CompanyAccess e RoleBinding no tenant tratado.
3. Confirmar negacao de token previamente emitido, revisar responsabilidades ativas e preservar AuditEvents.
4. Para suspeita de comprometimento, revisar acoes privilegiadas, tenants e companies atingidos; rotacionar credencial associada quando aplicavel e abrir incidente.

Revogacao de sessoes depende da capacidade do IdP e deve ser verificada com o fornecedor antes de exposicao externa. O sistema nao possui bypass para JWKS ou identidade inativa.
