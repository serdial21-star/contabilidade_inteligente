# Dossiê técnico de continuidade — Sistema B

**Produto:** Serdial21 Contabilidade Inteligente (Sistema B)  
**Data de corte:** 25 de setembro de 2026  
**Última validação operacional:** 29 de setembro de 2026  
**Ambiente descrito:** piloto interno no VPS da Hostinger  
**Branch de referência:** `main`  
**Commit implantado no VPS:** `8d5d3f9`  
**Estado geral:** HTTPS público saudável; liberação autenticada interna ainda pendente

## 1. Finalidade e autoridade deste documento

Este dossiê registra o que foi decidido, executado, validado e deixado pendente na preparação da primeira publicação interna do Sistema B. Ele foi escrito para permitir que uma pessoa ou outra inteligência artificial retome o trabalho sem depender do histórico desta conversa.

Para o estado operacional do deployment em 25/09/2026, este documento prevalece sobre trechos de status anteriores que entrem em conflito com ele. A documentação permanente de arquitetura, segurança e negócio continua válida, especialmente `AGENTS.md`, os ADRs, `docs/TECHNICAL_BASELINE.md` e `docs/INTERNAL_VPS_DEPLOYMENT.md`.

Este arquivo não contém senhas, frases-senha, chaves privadas, URLs com credenciais nem conteúdo de arquivos secretos. Esses valores permanecem somente nos locais operacionais autorizados.

## 2. Resumo para retomada em cinco minutos

1. O Sistema B está clonado em `/opt/serdial21-b` no VPS e executa no commit `8d5d3f9`.
2. API, Redis e Web estão em execução e saudáveis, sem portas do Sistema B publicadas diretamente no host.
3. O banco piloto foi migrado até `20260923_0016`; possui 48 tabelas, 22
   permissões semeadas e o tenant Serdial21 com o UUID fixo da ponte. Ainda não
   possui usuários, empresas ou corpus documental.
4. O acesso privado Web → API e os controles TLS/ACL/rate limit do Redis passaram nos testes de fumaça.
5. O n8n existente continua funcionando publicamente e não teve sua configuração de proxy alterada.
6. O DNS de `contabilidade.serdial21.com` foi criado e confirmado em
   resolvedores públicos em 29/09/2026; ainda faltam proxy reverso, TLS e teste
   autenticado do bridge.
7. O backup externo criptografado dos segredos do Sistema B foi confirmado pelo operador; antes da exposição pública, decidir os itens de endurecimento P1 registrados na seção 15.
8. Não executar `docker compose down`, reiniciar o VPS, atualizar o sistema operacional ou alterar o Caddy público sem janela aprovada e plano de rollback.
9. Em 29/09/2026, rotação de logs Docker e limites de memória do Redis foram aplicados seletivamente; API, Redis, Web e n8n permaneceram saudáveis.

## 3. Decisões de produto e arquitetura

### 3.1 Relação entre os sistemas

- O Sistema A já é um produto disponível em site próprio e é o ponto de origem do acesso do usuário.
- O Sistema B é um complemento contábil opcional, comercializável junto com o Sistema A, mas não obrigatório para clientes do Sistema A.
- A primeira publicação do Sistema B é interna, destinada à equipe da Serdial21 para trabalho e testes.
- O objetivo futuro é contabilizar, de forma automática e integrada, informações produzidas pelo Sistema A.
- A integração de dados empresariais A → B não foi autorizada para produção nesta etapa. A autorização atual cobre apenas infraestrutura, autenticação e preparação do piloto vazio.

### 3.2 Bancos separados

Os bancos dos Sistemas A e B permanecem separados. Essa é a opção recomendada e adotada porque preserva:

- isolamento de produto e de falhas;
- segurança e menor privilégio;
- evolução independente de schema;
- auditoria e rastreabilidade da integração;
- possibilidade de o Sistema B continuar opcional;
- fronteiras multi-tenant do Sistema B.

Não criar consultas diretas entre os bancos, tabelas compartilhadas ou credenciais comuns. A futura troca de dados deve ocorrer por contrato versionado, autenticação própria, idempotência, auditoria e reconciliação.

### 3.3 Autoridade contábil

- O sistema contábil externo continua sendo a autoridade sobre escrituração, números oficiais, saldos e fechamento.
- O Sistema B é autoridade sobre documentos/evidências processados, dados canônicos, regras, DE/PARA, propostas, workflow, aprovações, explicações de IA e sua própria auditoria.
- Toda proposta com efeito contábil exige aprovação humana válida.
- IA é assistiva; não substitui regras determinísticas nem assume autoridade profissional.

## 4. Repositório e baseline implantada

### 4.1 Repositório

- Origem: `https://github.com/serdial21-star/contabilidade_inteligente.git`
- Diretório local no VPS: `/opt/serdial21-b`
- Branch: `main`
- Commit no VPS: `07ad9a6`
- Projeto Docker Compose: `serdial21-b`
- Arquivo principal de deployment: `deploy/compose.yaml`
- Arquivo de ambiente real: `deploy/.env` — não versionado, modo `600`

O worktree local no Windows estava alinhado com `origin/main` na data de corte. A pasta não rastreada `.claude/` já existia e não faz parte deste trabalho; não removê-la ou versioná-la sem análise e autorização.

### 4.2 Commits que formam a implantação atual

| Commit | Finalidade |
|---|---|
| `bb16d10` | preparação do deployment interno do Sistema B |
| `1f8bbe2` | leitura segura de secrets pelos serviços não-root |
| `6176518` | execução explícita do Redis com identidade não-root |
| `af8e1d6` | rede de saída para API e migrations |
| `4b0bb93` | healthcheck da API com host confiável |
| `6a13281` | remoção da file capability desnecessária do Caddy da imagem Web |
| `07ad9a6` | rotação limitada de logs e `maxmemory`/`noeviction` do Redis |

Não reverter isoladamente um desses commits: eles corrigem falhas observadas no runtime e dependem uns dos outros.

## 5. Topologia atual

```text
Internet
   |
   +-- n8n.serdial21.com:443
           |
           +-- n8n-caddy-1 (80/443 publicados)
                    |
                    +-- n8n-n8n-1:5678, rede n8n_default

Sistema B — ainda privado
   |
   +-- serdial21-b-web-1:8080
           | redes: backend + serdial21_proxy
           |
           +-- serdial21-b-api-1
                    | redes: backend + egress
                    +-- MySQL remoto Hostinger, TLS
                    +-- serdial21-b-redis-1:6379, TLS/ACL

Volumes locais do Sistema B
   +-- evidências: serdial21_b_evidence
   +-- dados temporários do Redis: tmpfs; persistência desabilitada
```

O proxy público do n8n ainda não está conectado à rede externa `serdial21_proxy`. Portanto, a presença do serviço Web nessa rede não o torna acessível pela Internet.

## 6. Infraestrutura do VPS

### 6.1 Sistema e capacidade observada

- Ubuntu 24.04.3 LTS;
- Docker e Docker Compose v5.0.2;
- disco raiz de aproximadamente 96 GB, com cerca de 90 GB livres no levantamento;
- memória de 7,8 GiB, com cerca de 6,7 GiB disponíveis no levantamento;
- swap desabilitado.

O sistema informou 58 atualizações disponíveis, uma delas de segurança padrão, e necessidade de reinicialização. Atualização e reinicialização não foram realizadas porque exigem janela operacional separada.

### 6.2 n8n preexistente

- Compose: `/root/n8n/n8n/docker-compose.yml`;
- projeto/rede: `n8n` / `n8n_default`;
- `n8n-n8n-1`: n8n `2.6.4`, porta `5678` ligada apenas a `127.0.0.1`;
- `n8n-caddy-1`: Caddy `2.10.2`, portas `80` e `443` publicadas;
- volumes: `n8n_n8n_data`, `n8n_caddy_config` e `n8n_caddy_data`;
- endpoint público do n8n respondeu HTTP `200` após o backup e reinício controlado.

O Caddy atual foi criado com comando de proxy reverso de um único domínio, sem `Caddyfile` persistente montado. Ele continua inalterado. A publicação do Sistema B exigirá converter essa configuração para dois hosts, preservando o n8n.

## 7. Banco de dados do Sistema B

### 7.1 Instância piloto

- banco lógico: `u621451815_s21_pilot`;
- usuário de aplicação: `u621451815_s21_pilot_app`;
- servidor: MariaDB gerenciado pela Hostinger;
- acesso remoto permitido somente a partir do IPv4 do VPS, sem curinga público;
- credencial consumida pelo container via `deploy/secrets/database_url`;
- arquivo secreto no VPS: proprietário `root`, grupo `serdial21-secrets` (`GID 19021`), modo `640`.

Não registrar neste repositório a senha nem o conteúdo de `database_url`.

### 7.2 Verificações realizadas

- autenticação: OK;
- destino/banco esperado: OK;
- versão observada: MariaDB `11.8.9-log`;
- timezone: UTC;
- charset: `utf8mb4`;
- TLS: ativo, cifra observada `TLS_AES_256_GCM_SHA384`;
- conectividade inicial TCP: OK.

A primeira tentativa de autenticação falhou por senha divergente. A senha do usuário foi redefinida no painel e o secret do VPS foi atualizado; o preflight seguinte passou.

### 7.3 Schema atual

- revisão Alembic: `20260923_0016 (head)`;
- tabelas: 48;
- tabelas obrigatórias: OK;
- permissões semeadas: 22;
- tenant Serdial21 criado em 29/09/2026 com o UUID fixo aprovado pela ponte;
- primeira identidade interna provisionada: `funcionario:3`, ativa, sem e-mail
  armazenado e com permissões mínimas de leitura/auditoria;
- empresas de negócio: zero;
- corpus real importado: nenhum.

As migrations MariaDB utilizam DDL não transacional. Não tentar rollback automático ou alteração manual de schema. Toda evolução deve ocorrer por migration Alembic revisada, com backup e estratégia de recuperação quando houver dados.

### 7.4 Banco de homologação anterior

O banco `_hom` foi apenas inspecionado em modo leitura. Naquele levantamento ele tinha migration `0009`, 33 tabelas, 16 tenants, 28 empresas, 32 usuários e 100 eventos de auditoria. Ele não foi reutilizado para o piloto e não deve ser tratado como fonte autorizada sem nova decisão.

## 8. Serviços do Sistema B

| Serviço | Imagem | Identidade | Redes | Estado validado | Porta no host |
|---|---|---|---|---|---|
| API | `serdial21-b-api:local-review` | `10001:10001` | `backend`, `egress` | running/healthy | nenhuma |
| Redis | `redis:8.2.9-alpine` | `999:1000` + grupo `19021` | `backend` | running/healthy | nenhuma |
| Web | `serdial21-b-web:local-review` | UID `1000` | `backend`, `serdial21_proxy` | running/healthy, 0 restarts | nenhuma |
| migrate | imagem da API | efêmero | `backend`, `egress` | executado com sucesso | nenhuma |
| storage-init | BusyBox | efêmero | conforme Compose | volume inicializado | nenhuma |

### 8.1 API

- roda como usuário não-root;
- filesystem raiz somente leitura e privilégios reduzidos conforme o Compose;
- healthcheck passou após enviar um valor aceito por `TRUSTED_HOSTS`;
- usa rede `backend` para Redis/Web e `egress` para banco e integrações externas;
- não possui porta publicada diretamente.

### 8.2 Redis

- TLS obrigatório;
- ACL dedicada e privilégio mínimo para rate limit;
- sem porta publicada no host;
- persistência desabilitada: os dados são operacionais/efêmeros, não fonte de verdade;
- diretório `/data` em `tmpfs`, proprietário efetivo `999:1000`, modo `0700`;
- teste TLS/autenticação passou;
- teste de ACL passou;
- teste de rate limit permitiu a primeira requisição e bloqueou a segunda.

Desde o commit `07ad9a6`, o Redis usa `maxmemory=128mb` e política
`noeviction`, preservando margem dentro do limite de 192 MiB do container e
recusando novas gravações em vez de apagar silenciosamente chaves de rate
limit. O kernel ainda alertou que `vm.overcommit_memory=1` não está ativo; essa
mudança permanece condicionada a janela apropriada.

### 8.3 Web

- Caddy interno atende na porta não privilegiada `8080`;
- usuário não-root, `cap_drop: ALL`, `no-new-privileges`, filesystem raiz somente leitura e `tmpfs` para diretórios graváveis;
- nenhuma file capability permaneceu no binário (`CADDY_FILE_CAPS=NONE`);
- configuração Caddy validada;
- healthcheck saudável, sem reinícios após a correção;
- encaminhamento privado para API validado.

### 8.4 Armazenamento de evidências

O volume `serdial21_b_evidence` foi inicializado. Ele ainda não contém corpus real e não possui backup externo/restore drill próprio. Não importar documentos reais antes de implantar essa proteção e obter autorização explícita.

## 9. Identidade e bridge Sistema A → Sistema B

### 9.1 Contrato aprovado

- issuer: `https://lgohzjneyvdtonpeapvd.functions.supabase.co/sistema-b-bridge`;
- audience: `serdial21-sistema-b`;
- JWKS: `https://lgohzjneyvdtonpeapvd.functions.supabase.co/sistema-b-jwks`;
- algoritmo: RS256/RSA;
- `kid`: `sistema-b-bridge-1`.

O Sistema A deve iniciar o acesso e o Sistema B deve validar assinatura, issuer, audience, expiração, tenant e autorizações. Um identificador isolado nunca constitui autorização.

### 9.2 Estado atual

- URL publicada: `https://contabilidade.serdial21.com`;
- DNS: registro A criado e confirmado publicamente em 29/09/2026, TTL 300;
- HTTPS público: configurado e validado em 29/09/2026, com certificado Let's
  Encrypt válido e redirecionamento HTTP `308`;
- teste autenticado do bridge: ainda não executado no ambiente público;
- `VITE_SISTEMA_B_URL` do Sistema A: identidade mínima já provisionada; alterar
  para a URL pública e executar o teste autenticado com clique real.

## 10. Backups e capacidade de recuperação

### 10.1 n8n — concluído e validado

- diretório de trabalho do backup: `/root/backups/n8n/20260925T171030Z`;
- workflows exportados: 138;
- credenciais exportadas: 14, mantidas protegidas;
- backup consistente do volume realizado com parada curta e aprovada do n8n;
- configuração e dados do Caddy incluídos;
- pacote criptografado: `/root/backups/n8n-predeploy-20260925T171030Z.tar.gz.enc`;
- tamanho: `25.961.808` bytes;
- modo: `600`;
- SHA-256: `a67e20f90e48e76b0b02ed52e4345dfc94bcad5e8de166b0aab57bf9dfed8c3e`;
- cópia externa confirmada no Google Drive;
- hash da cópia local conferido;
- restauração isolada validada: manifesto, configuração, SQLite `quick_check`, 138 workflows e 14 credenciais.

A frase-senha do arquivo não está neste repositório.

### 10.2 Segredos de deployment do Sistema B — backup externo confirmado

- pacote criptografado no VPS: `/root/backups/serdial21-b-secrets-20260925T195322Z.tar.gz.enc`;
- tamanho: `7.360` bytes;
- modo: `600`;
- SHA-256: `e510636e5e7d2ad8265e041d099b29e017a48cc15b121c7b4eca3cf474183f16`;
- criação e validação local no VPS: OK;
- cópia externa: confirmada pelo operador com `BACKUP_EXTERNO_SISTEMA_B=OK` em 25/09/2026;
- comparação do hash da cópia externa: confirmada em 29/09/2026; o SHA-256
  informado pelo operador coincide exatamente com o valor registrado acima.

O backup está registrado como externo. A frase-senha deve permanecer guardada separadamente do arquivo criptografado.

### 10.3 Banco e evidências — pendente antes de dados reais

O schema vazio pode ser recriado pelas migrations, mas ainda não há política operacional comprovada de backup/restore para:

- dados empresariais do banco piloto;
- documentos do volume `serdial21_b_evidence`.

Configurar e testar recuperação antes da importação do primeiro corpus real.

## 11. Segredos e acesso administrativo

### 11.1 Grupo de leitura de secrets

- grupo no host: `serdial21-secrets`;
- GID: `19021`;
- não há usuários humanos membros;
- serviços recebem o grupo suplementar pelo Compose;
- `deploy/.env` contém `SERDIAL21_SECRETS_GID=19021`;
- arquivos consumidos por containers usam `root:19021` e modo `640`, salvo chave de CA que permanece `root:root` e modo `600`.

Secrets existentes incluem a URL do banco, URL TLS/ACL do rate limit, certificados, chave privada do servidor Redis e arquivo ACL. Não mostrar seu conteúdo em logs ou comandos compartilhados.

### 11.2 Chave SSH dedicada

- caminho local esperado: `C:\Users\Sergio\.ssh\serdial21_vps_backup_ed25519`;
- fingerprint: `SHA256:wp0XzjaRQ5wjSZMdoLVGEUCUeGrtdTTNfAfXFaNphkM`;
- autenticação por chave testada: OK;
- chave pública válida adicionada a `/root/.ssh/authorized_keys`.

Houve tentativas de transferência da chave pública com formatação inválida. Pode existir uma linha inválida em `authorized_keys`, o arquivo candidato `/root/.ssh/serdial21_vps_backup_ed25519.pub.candidate` e um arquivo Base64 temporário no Windows. Fazer a limpeza somente após abrir uma segunda sessão SSH com a chave válida e manter a primeira sessão aberta para rollback.

Nunca excluir a chave válida, divulgar a chave privada ou registrar sua frase-senha.

## 12. Problemas encontrados e correções aplicadas

### 12.1 Secrets ilegíveis por serviços não-root

**Sintoma:** `PermissionError: [Errno 13] Permission denied: '/run/secrets/database_url'`.  
**Causa:** arquivo `root:root 600` montado como secret, enquanto a API executava com UID não-root.  
**Correção:** grupo dedicado `19021`, arquivos `root:19021 640` e `group_add` no Compose.  
**Commit:** `1f8bbe2`.

### 12.2 Redis reiniciando por permissão em `/data`

**Sintoma:** falha ao abrir `dump.rdb`, Redis unhealthy/restarting.  
**Causa:** identidade efetiva e proprietário do `tmpfs` incompatíveis após redução de capabilities.  
**Correção:** usuário explícito `999:1000`, grupo suplementar de secrets e `tmpfs` com dono/modo compatíveis.  
**Commit:** `6176518`.

### 12.3 API sem resolução/saída para o banco remoto

**Sintoma:** falha temporária de resolução de `srv1183.hstgr.io`.  
**Causa:** a API estava apenas em rede Docker interna.  
**Correção:** rede `egress` ligada apenas a API e migration.  
**Commit:** `af8e1d6`.  
**Limitação:** `egress` é uma bridge com saída ampla; não constitui allowlist de firewall.

### 12.4 Healthcheck da API retornando HTTP 400

**Sintoma:** processo ativo, container unhealthy.  
**Causa:** o healthcheck usava `Host: 127.0.0.1`, recusado pelo middleware de hosts confiáveis.  
**Correção:** healthcheck passou a enviar um host derivado de `TRUSTED_HOSTS`.  
**Commit:** `4b0bb93`.

### 12.5 Web/Caddy falhando com `operation not permitted`

**Sintoma:** `exec /usr/bin/caddy: operation not permitted`, reinício contínuo.  
**Causa:** a imagem oficial trazia `cap_net_bind_service=ep` no binário e o container removia todas as capabilities; o conflito impedia o `exec`, mesmo usando porta 8080.  
**Correção:** remover a file capability durante o build, preservar `cap_drop: ALL`, reconstruir sem cache e adicionar/verificar healthcheck.  
**Commit:** `6a13281`.

Esses incidentes foram diagnosticados com revisão paralela de Compose, runtime e Caddy. O estado final saudável foi confirmado no VPS.

## 13. Evidências de validação

### 13.1 Testes de código

- baseline anterior ao deployment: 509 aprovados, 20 ignorados, 2 warnings, 0 falhas;
- suíte direcionada aos assets de deployment do commit `07ad9a6`: 7 aprovados;
- suíte completa em 29/09/2026: 511 aprovados, 20 ignorados, 2 warnings e 0 falhas.

### 13.2 Testes de runtime no VPS

- API: running/healthy, nenhuma porta publicada;
- Redis: running/healthy, nenhuma porta publicada;
- Web: running/healthy, zero reinícios, nenhuma porta publicada;
- `WEB_APP=OK`;
- `WEB_CONFIG=OK`;
- `API_READY_VIA_WEB=OK`;
- `REDIS_TLS_AUTH=OK`;
- `REDIS_ACL=OK`;
- `RATE_LIMIT_FIRST=ALLOWED`;
- `RATE_LIMIT_SECOND=BLOCKED`;
- `CADDY_FILE_CAPS=NONE`;
- rotação `json-file` com `max-size=10m` e `max-file=3` confirmada em API,
  Redis e Web;
- Redis confirmado com `maxmemory=128mb` e `maxmemory-policy=noeviction`;
- configuração Caddy interna válida;
- migration atual: `20260923_0016`;
- tabelas obrigatórias: OK;
- tenant Serdial21: ativo e auditado;
- usuários, empresas e corpus documental: vazios.

## 14. Estado de exposição pública

O Sistema B está publicado em HTTPS desde 29/09/2026, mas ainda não foi
liberado como fluxo autenticado interno pelo Sistema A. A publicação preserva
o n8n e expõe somente o Caddy público; API, Redis e Web continuam sem portas
publicadas diretamente no host.

Concluído em 29/09/2026:

- DNS, Caddyfile persistente e certificado TLS;
- Caddy público conectado a `n8n_default` e `serdial21_proxy`;
- n8n preservado com HTTP 200;
- aplicação, live e ready com HTTP 200;
- HSTS, CSP, `no-store`, `nosniff`, Referrer-Policy, Permissions-Policy e
  proteção contra frames confirmados publicamente;
- rollback do Compose e do Caddyfile preservado por cópias e hashes.

Ainda faltam:

- tenant fixo e primeira identidade interna criados e auditados;
- executar o teste autenticado do bridge A → B;
- somente então alterar a URL do Sistema B no Sistema A.

Não publicar API, Redis ou MySQL diretamente.

## 15. Pendências e riscos conhecidos

### 15.1 Prioridade P0 — antes da publicação

- SHA-256 da cópia externa do backup de secrets reconfirmado em 29/09/2026;
- DNS criado e validado em 29/09/2026;
- configuração Caddy de dois hosts validada offline e aplicada;
- rollback do Caddy/n8n preservado e n8n confirmado com HTTP 200;
- smoke público de aplicação, live e ready aprovado;
- headers HTTP públicos revisados e aprovados;
- smoke autenticado continua pendente.

### 15.2 Prioridade P1 — antes de carga ou dados sensíveis

- rotação de logs Docker concluída em 29/09/2026;
- `maxmemory=128mb` e `noeviction` do Redis concluídos em 29/09/2026;
- decidir e aplicar `vm.overcommit_memory=1` em janela apropriada;
- transformar a rede `egress` em controle real por firewall/allowlist; a bridge atual não restringe destinos;
- endurecer o serviço `storage-init`, que ainda merece revisão de usuário, rede e capabilities;
- configurar backup/restore do banco piloto e do volume de evidências;
- adicionar testes de runtime Docker no CI para Redis e Web;
- avaliar pinagem de imagens por digest, não apenas por tag;
- repetir a suíte completa após consolidar as mudanças.

### 15.3 Governança de dados

- nenhum dado real deve ser importado sem autorização explícita;
- definir o primeiro contrato de integração A → B na Wave 0;
- manter idempotência, auditoria, versionamento, tenant/company scope e reconciliação;
- não copiar dados entre bancos manualmente como solução permanente.

## 16. Sequência segura de retomada

### Etapa 1 — confirmar baseline sem alterar estado

No VPS:

```bash
cd /opt/serdial21-b
git rev-parse --short HEAD
docker compose --env-file deploy/.env -f deploy/compose.yaml ps
docker inspect serdial21-b-api-1 --format 'API={{.State.Status}}/{{.State.Health.Status}}'
docker inspect serdial21-b-redis-1 --format 'REDIS={{.State.Status}}/{{.State.Health.Status}}'
docker inspect serdial21-b-web-1 --format 'WEB={{.State.Status}}/{{.State.Health.Status}} RESTARTS={{.RestartCount}}'
```

Esperado: commit `07ad9a6` e os três serviços `running/healthy`.

### Etapa 2 — verificar proteção do backup de secrets

1. a cópia externa já foi confirmada pelo operador;
2. calcular novamente o SHA-256 na cópia externa quando ela for usada ou auditada;
3. comparar com `e510636e5e7d2ad8265e041d099b29e017a48cc15b121c7b4eca3cf474183f16`;
4. confirmar que arquivo e frase-senha estão guardados separadamente;
5. registrar apenas o resultado, nunca a frase-senha.

Etapa concluída em 29/09/2026: o hash da cópia externa coincidiu exatamente
com o SHA-256 registrado, sem exposição da frase-senha.

### Etapa 3 — decidir os itens P1 que precederão a publicação

A recomendação mínima é aplicar rotação de logs e limites do Redis antes do tráfego público. Restrição real de egress e backup de evidências devem existir antes de dados sensíveis.

O mínimo recomendado foi aplicado em 29/09/2026 pelo commit `07ad9a6`, com
recriação seletiva de Redis, API e Web, sem `docker compose down`. O smoke
privado confirmou `WEB_APP=OK`, `API_READY_VIA_WEB=OK`, zero reinícios, nenhuma
porta publicada e preservação do n8n.

Qualquer alteração no repositório deve obedecer a: análise, menor mudança suficiente, teste direcionado, revisão do diff, commit separado e atualização deste dossiê.

### Etapa 4 — preparar DNS e proxy sem tocar o n8n

1. registro A para `contabilidade.serdial21.com` criado em 29/09/2026;
2. resolução confirmada em resolvedores públicos, com TTL 300;
3. preparar `Caddyfile` persistente com:
   - `n8n.serdial21.com` → `n8n:5678`;
   - `contabilidade.serdial21.com` → `serdial21-web:8080`;
4. validar a configuração Caddy offline;
5. preparar rollback para o comando/configuração original do n8n;
6. solicitar janela de mudança.

### Etapa 5 — mudança pública controlada

Durante a janela:

1. conectar o Caddy público a `serdial21_proxy` de forma persistente no Compose do n8n;
2. montar o `Caddyfile` persistente;
3. recriar **somente** o container Caddy;
4. testar imediatamente `n8n.serdial21.com`;
5. se o n8n falhar, executar rollback antes de prosseguir;
6. testar o Sistema B em HTTPS;
7. verificar live, ready, assets, headers e logs sanitizados;
8. acompanhar reinícios e consumo de recursos.

Não executar `docker compose down` no projeto n8n nem no Sistema B para essa mudança.

### Etapa 6 — identidade e liberação interna

1. executar login real no Sistema A;
2. abrir o Sistema B pelo bridge;
3. confirmar assinatura/issuer/audience/expiração, tenant e permissões;
4. testar negações sem vazamento cross-tenant;
5. alterar `VITE_SISTEMA_B_URL` somente após todos os testes passarem;
6. registrar evidência e critério de rollback.

### Etapa 7 — somente depois: dados e integração

1. configurar e testar backup/restore do banco e das evidências;
2. obter aprovação para o primeiro corpus real;
3. escolher um fluxo estreito da Wave 0;
4. documentar contrato, chave idempotente, versões, auditoria e reconciliação;
5. manter o sistema contábil externo como autoridade oficial.

## 17. Critérios de conclusão do piloto interno publicável

O ambiente estará pronto para uso interno público somente quando todos forem verdadeiros:

- DNS e TLS válidos;
- n8n preservado e saudável após a mudança do proxy;
- Sistema B Web/API/Redis saudáveis;
- nenhuma porta interna publicada indevidamente;
- backup externo dos secrets confirmado;
- smoke público live/ready/assets aprovado;
- bridge autenticado A → B aprovado;
- logs sem segredo ou dado pessoal bruto;
- rollback testável e documentado;
- responsáveis cientes das limitações P1;
- nenhuma importação real feita sem autorização.

Em 29/09/2026, todos os itens acima estavam aprovados exceto o bridge
autenticado A → B. A primeira identidade foi autorizada, provisionada e
auditada; ainda falta o clique real iniciado pelo Sistema A.

## 18. Comandos e ações proibidas sem nova autorização

- não executar `docker compose down`;
- não apagar volumes ou containers com dados;
- não reiniciar o VPS ou atualizar pacotes do sistema;
- não substituir a configuração pública do Caddy sem backup, validação e rollback;
- não expor API, Redis ou MySQL em portas públicas;
- não mostrar conteúdos de `deploy/.env` ou `deploy/secrets/*`;
- não versionar `.env`, chaves, certificados privados ou backups;
- não executar migration destrutiva ou downgrade automático;
- não importar dados reais;
- não unificar bancos dos Sistemas A e B;
- não avançar da infraestrutura para integração empresarial sem solicitação.

## 19. Índice de artefatos para a próxima inteligência

Ler nesta ordem:

1. `AGENTS.md` — regras obrigatórias do repositório;
2. este dossiê — estado operacional atual;
3. `docs/INTERNAL_VPS_DEPLOYMENT.md` — procedimentos de deployment;
4. `deploy/compose.yaml` e `deploy/.env.example` — topologia e contrato de configuração;
5. `tests/unit/test_deployment_assets.py` — guardrails estáticos do deployment;
6. `docs/adr/0015-publicacao-interna-e-wave-zero-connect-hub.md` — decisão de publicação interna e contrato do bridge;
7. `docs/SISTEMA_A_BRIDGE_KEY_SETUP.md` — configuração das chaves do bridge;
8. `docs/DOSSIE_SESSAO_2026-09-23.md` — histórico amplo anterior;
9. `docs/BACKUP_RESTORE_RUNBOOK.md` e `docs/RECOVERY_RUNBOOK.md` — recuperação;
10. `docs/PRODUCTION_REVERSE_PROXY_SECURITY.md` — requisitos do proxy público.

Antes de editar, conferir `git status`, commits após `07ad9a6`, containers em execução e documentação que possa ter sido atualizada.

## 20. Registro de handoff

Na data de corte:

- o runtime privado estava saudável;
- o schema piloto estava atualizado e vazio;
- os principais erros de permissions, redes, healthcheck e Caddy estavam corrigidos;
- o n8n público estava preservado;
- o backup do n8n estava criptografado, copiado externamente e restaurado em teste;
- o backup criptografado dos secrets do Sistema B existia no VPS e sua cópia externa foi confirmada pelo operador; naquele corte, a saída da comparação de hash externa ainda não havia sido anexada;
- a publicação pública e o teste autenticado ainda não haviam começado.

Atualização de 29/09/2026:

- commit `07ad9a6` implantado por fast-forward;
- Redis, API e Web recriados seletivamente e confirmados `running/healthy`,
  todos com zero reinícios;
- rotação de logs `json-file` limitada a três arquivos de 10 MiB confirmada;
- Redis confirmado com `maxmemory=128mb` e `noeviction`;
- `WEB_APP=OK` e `API_READY_VIA_WEB=OK`;
- `PORT_BINDINGS={}` nos três serviços;
- n8n público preservado e ativo;
- SHA-256 da cópia externa do backup de secrets reconfirmado e coincidente;
- DNS, Caddy público e HTTPS confirmados;
- certificado Let's Encrypt válido de 29/09/2026 a 28/12/2026;
- redirecionamento HTTP `308`, HSTS e headers de segurança confirmados;
- n8n, API, Redis e Web preservados e saudáveis após a mudança;
- teste autenticado da ponte continua pendente.
- tenant Serdial21 criado no banco piloto pelo bootstrap idempotente do commit
  `8d5d3f9`; a validação imediatamente após a criação confirmou UUID, timezone,
  moeda, status ativo, zero empresas e um evento de auditoria.
- `funcionario:3` provisionado sem e-mail, com membership e role binding ativos,
  permissões `audit.read`, `company.read` e `journal.read`, zero CompanyAccess e
  trilha de auditoria presente.

O próximo operador deve começar pela seção 16 e atualizar este documento ao fim de cada mudança material, registrando data, commit, evidência, resultado e pendências — nunca valores secretos.
