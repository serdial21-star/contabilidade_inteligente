# Segredos locais de deploy

Este diretório nunca recebe valores reais no Git. No servidor, os arquivos
esperados por `deploy/compose.yaml` são:

- `database_url`;
- `rate_limit_backend_url`;
- `redis_ca_certificate.pem`;
- `redis_server_certificate.pem`;
- `redis_server_key.pem`;
- `redis-users.acl`.

Crie-os com permissão mínima no host. Nunca envie seu conteúdo em conversa,
log, issue, commit ou saída de `docker compose config`.
