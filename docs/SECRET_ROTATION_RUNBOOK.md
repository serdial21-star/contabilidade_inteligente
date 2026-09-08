# Rotacao de segredos

## Principios

Nunca registrar valor de segredo em ticket, terminal compartilhado, log, AuditEvent, documento ou Git. Registrar apenas tipo, ambiente, horario, operadores, correlation id e resultado de validacao.

| Tipo existente | Owner | Local | Gatilho e procedimento |
| --- | --- | --- | --- |
| Credencial MariaDB | Database Operator | ambiente/provedor de segredo | suspeita, desligamento ou ciclo aprovado: criar credencial minima, atualizar referencia protegida, validar leitura, trocar aplicacao e revogar a anterior. |
| Configuracao OIDC | administrador IdP | IdP e configuracao de deploy | suspeita ou troca de issuer/audience/JWKS: rotacionar no IdP, validar discovery/JWKS e token novo, atualizar referencia e invalidar material anterior conforme o IdP. |
| Credencial externa | owner da integracao | ambiente/provedor de segredo | emitir nova, atualizar consumidor, validar chamada minima e revogar a anterior. Object storage nao esta integrado hoje. |

## Exposicao suspeita

1. Nao repetir nem copiar o valor exposto.
2. Conter consumidor, identificar ambiente/dependencias por referencias tecnicas e abrir incidente.
3. Rotacionar, atualizar configuracao protegida e validar health.
4. Revogar valor anterior e revisar logs, CI e historico Git com acesso restrito. Segredo realmente versionado e `REAL_SECRET_INCIDENT`; nao remover silenciosamente o historico.
5. Registrar resultado sanitizado e acao preventiva.

O scanner de segredo do CI complementa, mas nao substitui, rotacao e resposta humana.
