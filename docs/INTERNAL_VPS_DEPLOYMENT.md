# Publicação interna do Sistema B no VPS

## Status

Plano e artefatos locais preparados em 2026-09-25. Nenhum deploy, DNS,
container, migration ou alteração no Caddy do VPS foi executado por esta
entrega.

Decisão: [ADR 0015](adr/0015-publicacao-interna-e-wave-zero-connect-hub.md).

## Topologia confirmada

O VPS Hostinger KVM 2 usa Ubuntu 24.04.3 LTS e possui um projeto Compose em
`/root/n8n/n8n/docker-compose.yml` com:

- `n8n-caddy-1`, Caddy 2.10.2, portas públicas 80/443;
- `n8n-n8n-1`, n8n 2.6.4, publicado somente em `127.0.0.1:5678`;
- rede Docker `n8n_default` compartilhada pelos dois containers;
- volumes persistentes `n8n_caddy_config` e `n8n_caddy_data`;
- Caddy iniciado pelo comando simplificado `caddy reverse-proxy`, dedicado ao
  domínio do n8n, sem Caddyfile montado.

O servidor informou atualizações pendentes e reinicialização necessária. Não
atualizar, reiniciar, executar `docker pull`, `docker compose down` ou recriar o
projeto n8n antes de backup, export e janela operacional aprovados.

## Topologia alvo da primeira fatia

`deploy/compose.yaml` cria um projeto separado `serdial21-b`:

- `web`: Caddy interno sem TLS, serve somente `/app/*` e `/ui/*` e encaminha
  `/api/*` para a API;
- `api`: FastAPI como usuário não-root, sem porta publicada no host;
- `redis`: rate limit distribuído, somente TLS, sem porta publicada e sem
  persistência de dados empresariais;
- `storage-init`: prepara somente o volume privado de evidências;
- `migrate`: perfil opt-in para migration controlada, nunca executado no
  startup normal.

A rede interna `backend` isola API e Redis. A rede dedicada `egress`, usada
somente por `api` e `migrate`, permite resolver e acessar MySQL, issuer e JWKS
sem publicar portas no host. A rede externa `serdial21_proxy` permite somente
a entrada do Caddy público no serviço web. O container do n8n não entra nas
redes privadas do B.

## Fronteira de segredos

Credenciais não aparecem no Compose ou nas imagens. A API lê `DATABASE_URL` e
`RATE_LIMIT_BACKEND_URL` de Docker secrets em `/run/secrets`. Certificados,
chave TLS e ACL do Redis também são arquivos ignorados pelo Git. Nunca usar
`docker compose config` em saída compartilhada, pois ele pode materializar
configurações do ambiente.

Como o Compose local implementa secrets de arquivo com bind mounts, o host
reserva um grupo sem membros (`SERDIAL21_SECRETS_GID`, exemplo `19021`). Os
arquivos ficam `root:<gid>` em modo `0640`, e somente `api`, `migrate` e
`redis` recebem o grupo suplementar. Não tornar segredo world-readable para
contornar falha de permissão e não reutilizar um GID que possua membros no
host.

O frontend de deploy usa `authMode: 'bridge'` e `dataMode: 'real'` em arquivo
separado. O `app/config.js` padrão continua sintético para preservar a
demonstração local.

## Alteração futura do Caddy público

O modo `caddy reverse-proxy` atual aceita a rota única do n8n. Para adicionar o
B, será necessário migrar o container existente para um Caddyfile com duas
rotas. `deploy/host-caddy/Caddyfile.example` é apenas referência redigida; não
deve ser aplicado com os valores de exemplo.

A mudança exige, nesta ordem:

1. backup dos volumes e do Compose do n8n;
2. export dos workflows e confirmação de recuperação;
3. criação da rede externa `serdial21_proxy`;
4. conexão persistente do Caddy à rede nova sem conectar o n8n ao backend B;
5. Caddyfile real validado offline com `caddy validate`;
6. recriação somente do serviço Caddy em janela curta;
7. smoke do n8n antes de habilitar a rota do B;
8. rollback para o comando anterior se TLS ou proxy do n8n falhar.

## Gates ainda pendentes

- subdomínio confirmado: `contabilidade.serdial21.com`; DNS ainda não criado;
- banco `u621451815_s21_pilot` e usuário exclusivo
  `u621451815_s21_pilot_app` criados; acesso remoto limitado ao IPv4 do VPS;
  conectividade TCP com o host MariaDB confirmada; autenticação e preflight
  ainda pendentes;
- autorizar o corpus real que será carregado nesse banco;
- gerar CA, certificado, chave, ACL e senha Redis fora do Git;
- configurar backup externo do banco e do volume de evidências;
- validar restore;
- criar DNS somente depois do smoke privado;
- aplicar migrations até `20260923_0016` em janela controlada;
- executar a suíte completa, build das imagens e smoke autenticado;
- testar o clique real Sistema A → Sistema B;
- atualizar `VITE_SISTEMA_B_URL` somente após o endereço estar saudável.

## Identidade pública confirmada

Os valores públicos da ponte foram verificados em 2026-09-25 sem ler segredos:

- issuer: `https://lgohzjneyvdtonpeapvd.functions.supabase.co/sistema-b-bridge`;
- audience: `serdial21-sistema-b`;
- JWKS: `https://lgohzjneyvdtonpeapvd.functions.supabase.co/sistema-b-jwks`;
- chave publicada: `kid=sistema-b-bridge-1`, `alg=RS256`, `kty=RSA`.

O issuer também foi confirmado por consulta somente leitura aos registros de
identidade já provisionados no banco `_dev`. Nenhum nome, e-mail, subject,
token ou credencial foi consultado ou registrado.

Sincronização de cliente, documento ou outro dado de negócio A→B permanece
bloqueada. Esta publicação utiliza apenas a ponte de login já aprovada.

## Por que `_hom` não será reutilizado automaticamente

Após autorização condicional do usuário, uma inspeção estritamente somente
leitura confirmou que `u621451815_serdial21_hom` está em `20260907_0009` e
contém 33 tabelas, 16 tenants, 28 empresas, 32 usuários e 100 eventos de
auditoria. A conexão usa TLS.

Nenhuma migration ou escrita foi executada. O banco não é uma base limpa de
piloto: contém evidência e massa histórica/sintética. Não se deve misturar
corpus real com esse conteúdo nem apagá-lo para reaproveitar o nome. O banco
novo recomendado continua sendo um ambiente exclusivo de piloto; `_mig`
permanece laboratório descartável e `_dev` permanece desenvolvimento.
