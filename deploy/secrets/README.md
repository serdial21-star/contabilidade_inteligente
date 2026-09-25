# Segredos locais de deploy

Este diretório nunca recebe valores reais no Git. No servidor, os arquivos
esperados por `deploy/compose.yaml` são:

- `database_url`;
- `rate_limit_backend_url`;
- `redis_ca_certificate.pem`;
- `redis_server_certificate.pem`;
- `redis_server_key.pem`;
- `redis-users.acl`.

O Compose local entrega segredos de arquivo por bind mount e não remapeia
`uid`, `gid` ou `mode`. Reserve no host o grupo sem membros configurado por
`SERDIAL21_SECRETS_GID` (exemplo: `19021`), atribua todos os arquivos a
`root:<gid>` e use modo `0640`. Os serviços `api`, `migrate` e `redis` recebem
somente esse grupo suplementar e continuam executando como usuários não-root.
O Redis Alpine fixado executa explicitamente como `999:1000`, os mesmos IDs do
`tmpfs` privado `/data`; não dependa da troca de usuário do entrypoint quando
todas as capabilities estiverem removidas.

Antes de criar o grupo, confirme que o GID escolhido está livre. Não adicione
usuários do host ao grupo e mantenha o diretório de segredos fora de backup ou
saída não cifrada. Nunca envie o conteúdo dos arquivos em conversa, log,
issue, commit ou saída de `docker compose config`.
