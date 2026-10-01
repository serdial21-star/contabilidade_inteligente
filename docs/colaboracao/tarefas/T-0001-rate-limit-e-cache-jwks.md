# T-0001 — Limite de requisições por origem confiável e cache JWKS com validade

| Campo | Valor |
|---|---|
| Estado | CONCLUÍDA |
| Origem | Auditoria de segurança `cacador-de-bugs` de 01/10/2026, achados #1 e #2 |
| Sistema | Sistema B |
| Exige ADR | não — corrige defeito dentro das decisões vigentes (`docs/SECURITY_INFRASTRUCTURE_SPEC.md`, `docs/OIDC_CONFIGURATION.md`) |
| Exige ação do usuário | sim, depois do aceite — redeploy na VPS (ver seção 1) |

> Observação de rastreabilidade: o Codex começou esta implementação antes de o protocolo existir, a partir do relatório da auditoria. O briefing abaixo foi escrito depois, para registrar os critérios pelos quais a entrega será revisada.

---

## 1. Briefing (Claude)

### [2026-10-01] Claude — Briefing (retroativo)

**Problema.**

1. `src/serdial21/entrypoints/http/middleware/rate_limit.py` (`_safe_identity`, versão do commit `d18f62a`): a identidade do balde era `sha256(Authorization)`, calculada antes de o token ser verificado. Um cliente não autenticado que envia um `Authorization` diferente a cada requisição ganha um balde novo a cada vez. Reproduzido: limite 5, 50 requisições passaram. No Redis (`maxmemory 128mb`, `noeviction`), as chaves aleatórias podem esgotar a memória e fazer a API inteira responder 503.
2. `src/serdial21/modules/identity/adapters/inbound/oidc.py` (versão do commit `d18f62a`): `PyJWKClient(cache_keys=True)` aplica `lru_cache` sem prazo à resolução de chave. Efeitos: (a) uma chave removida do JWKS continua aceita até o processo reiniciar; (b) um `kid` desconhecido força um novo download do JWKS a cada requisição, sem cache negativo.

**Objetivo.** O limite de requisições não pode ser contornado por dado não verificado, e a API deve deixar de aceitar uma chave de assinatura retirada do JWKS dentro de um prazo configurado, sem que tokens com `kid` desconhecido gerem downloads ilimitados.

**Escopo.**
- Dentro: identidade do rate limit; cache e renovação do JWKS; configurações tipadas novas; Caddy interno preservando a origem já sanitizada pelo proxy público; testes; atualização dos documentos de segurança afetados.
- Fora: rate limit por usuário autenticado depois da verificação do token (pode virar tarefa futura); mudanças no Sistema A ou na Edge Function; alteração de limites numéricos já aprovados.

**Referências.**
- Consultadas e aplicáveis: RFC 7517 (JWK/JWKS — o conjunto de chaves publicado é a fonte de verdade das chaves válidas); RFC 7519 (JWT); OpenID Connect Core 1.0, seção 10.1.1 (rotação de chaves de assinatura: o consumidor deve buscar o JWKS quando encontrar `kid` desconhecido); documentação do PyJWT `PyJWKClient` (`cache_keys`, `lifespan`); Caddy `trusted_proxies` e `trusted_proxies_strict`; Uvicorn `--proxy-headers`/`--forwarded-allow-ips`.
- Procuradas e não encontradas: nenhuma norma fixa o prazo de cache do JWKS ou o intervalo mínimo entre downloads; os valores padrão (300 s e 60 s) são decisão técnica e ficam configuráveis com limites.
- Documentos internos: `AGENTS.md` 6.4 e 6.9; `docs/SECURITY_INFRASTRUCTURE_SPEC.md`; `docs/PRODUCTION_REVERSE_PROXY_SECURITY.md`; `docs/THREAT_MODEL.md`; `docs/adr/0014-ponte-login-sistema-a.md`.

**Restrições.**
- O backend distribuído indisponível continua falhando fechado (503); não criar fallback que libere tráfego.
- Nenhum token, claim ou `kid` em log; o evento de segurança registra só o motivo.
- Configuração nova via Pydantic Settings com limites mínimo e máximo; `.env.example` só com valores fictícios.
- Só RS256, issuer e audience fixos, como hoje.

**Critérios de aceite.**
1. O rate limit não usa nenhum cabeçalho enviado pelo cliente para formar a identidade antes da autenticação; a identidade é a origem resolvida pela cadeia de proxies confiáveis.
2. A origem só é confiável quando passa pelo proxy público, que sanitiza `X-Forwarded-For`; um `X-Forwarded-For` forjado por um cliente externo não altera a identidade.
3. Uma chave removida do JWKS deixa de ser aceita em no máximo `OIDC_JWKS_CACHE_LIFESPAN_SECONDS` mais o tempo de um download.
4. Um token com `kid` desconhecido provoca no máximo um download do JWKS por `OIDC_UNKNOWN_KID_REFRESH_COOLDOWN_SECONDS`, mesmo com requisições concorrentes.
5. A rotação legítima de chave continua funcionando: um token com o `kid` novo é aceito depois de um único download.
6. `kid` ausente, vazio, não textual ou com mais de 255 caracteres é negado sem download.
7. A suíte padrão passa sem falhas e sem reduzir testes existentes.

**Testes exigidos.**
1. N requisições do mesmo cliente com `Authorization` aleatório: a partir de `limite + 1`, resposta 429.
2. Clientes de origens diferentes têm baldes independentes.
3. JWKS sem a chave antiga e relógio além do prazo: token com a chave antiga é negado.
4. 50 tokens com `kid` aleatório dentro do intervalo mínimo: exatamente 1 download; depois do intervalo, mais 1.
5. Token com `kid` novo legítimo: aceito com 1 download.
6. `kid` ausente ou com 256 caracteres: negado, 0 download.
7. Teste de deployment exigindo `trusted_proxies` no Caddy interno e as variáveis novas no `.env.example`.

**Riscos e pontos de atenção.**
- `deploy/api/Dockerfile` usa `--forwarded-allow-ips "*"`. Isso só é seguro se a porta 8000 da API não estiver exposta fora da rede Docker e se o Caddy interno só receber tráfego do proxy público. A revisão vai conferir `deploy/compose.yaml`.
- Atrás de NAT corporativo, vários usuários legítimos compartilham o mesmo IP e o mesmo balde; os limites atuais precisam comportar isso no piloto.
- `_jwks_refresh_lock` é por processo; com 2 workers Uvicorn o pior caso é 2 downloads por intervalo, o que é aceitável.

**Ações do usuário.** Depois do aceite e do commit: atualizar a VPS (`git pull` e rebuild dos contêineres `api` e `web`, conforme `docs/DEPLOY_RUNBOOK.md`) e confirmar `https://contabilidade.serdial21.com/api/v1/health/ready`. Claude escreverá o passo a passo exato no encerramento.

---

## 2. Decisões do usuário

### [2026-10-01] Usuário
- Escolheu começar pelos achados #1 e #2 da auditoria (registrado a partir do encaminhamento do relatório ao Codex).

### [2026-10-01] Usuário (decisão delegada ao Claude)
- Sobre o limite compartilhado por IP (Revisão 1, item 6), o usuário disse não saber avaliar. Decisão adotada por recomendação do Claude: **aceitar no piloto** o limite por IP, inclusive para usuários autenticados. Motivo: poucas pessoas no escritório; os limites (1000 gerais, 120 sensíveis e 30 uploads por minuto por IP) comportam o uso atual. O limite adicional por usuário autenticado vai para a fila (item 11) e deve ser feito antes de ampliar o número de usuários.

---

## 3. Implementação (Codex)

### [2026-10-01] Codex — Implementação (transcrita pelo Claude a partir do chat)

> O Codex entregou este relatório no chat, antes de conhecer o protocolo. Transcrição fiel, resumida.

- Arquivos criados: nenhum.
- Arquivos alterados: `src/serdial21/entrypoints/http/middleware/rate_limit.py`, `src/serdial21/modules/identity/adapters/inbound/oidc.py`, `src/serdial21/bootstrap/settings.py`, `src/serdial21/bootstrap/identity.py`, `deploy/web/Caddyfile`, `.env.example`, `deploy/.env.example`, `tests/api/test_security_infrastructure.py`, `tests/api/test_identity_security.py`, `tests/unit/test_deployment_assets.py`, `docs/PRODUCTION_REVERSE_PROXY_SECURITY.md`, `docs/SECURITY_CONFIGURATION_MATRIX.md`, `docs/SECURITY_INFRASTRUCTURE_SPEC.md`, `docs/THREAT_MODEL.md`.
- Resumo: o rate limit antes da autenticação usa só o IP resolvido pelo ASGI; o Caddy interno preserva a origem sanitizada pelo proxy público; o cache individual de chaves sem validade foi desabilitado; um `kid` desconhecido causa no máximo um download por cooldown (60 s) por processo; TTL e cooldown configuráveis.
- Testes: 569 aprovados, 20 ignorados, 0 falhas, 2 avisos preexistentes; validação de deploy 7 aprovados; `git diff --check` limpo.
- Migrations: nenhuma. ADR: nenhum.
- Pendência apontada: publicar, reiniciar `web` e `api` e verificar que clientes distintos chegam com IPs distintos.

### [2026-10-01] Codex — Implementação complementar após o briefing e a Revisão 1

- Arquivos criados: nenhum.
- Arquivos alterados nesta rodada: `tests/api/test_identity_security.py`, `tests/api/test_security_infrastructure.py`, `tests/unit/test_deployment_assets.py`; este arquivo e `docs/colaboracao/QUADRO.md` somente para comunicação e estado.
- Resumo da implementação:
  - acrescentado teste HTTP que comprova baldes independentes para duas origens distintas;
  - acrescentado teste comportamental com `JWKSetCache` real, relógio controlado e mudança do conjunto publicado, comprovando que a chave removida é negada depois do `lifespan`;
  - o teste de 50 `kid`s aleatórios passou a executar requisições concorrentes e mantém exatamente um refresh dentro do cooldown e mais um após o intervalo;
  - acrescentados testes para `kid` ausente, vazio, não textual e com 256 caracteres, todos negados antes de qualquer lookup/download;
  - o teste de deployment passou a exigir também as duas variáveis JWKS no `deploy/.env.example`.
- Testes executados e resultado (aprovados / ignorados / falhas):
  - testes direcionados finais: `45 passed`, `0 skipped`, `0 failed`, 2 avisos de depreciação preexistentes;
  - suíte padrão final: `575 passed`, `20 skipped`, `0 failed`, 2 avisos de depreciação preexistentes;
  - os 20 testes ignorados são os testes MariaDB/homologação sujeitos aos opt-ins existentes.
- Migrations: nenhuma.
- Decisões técnicas tomadas: os testes usam o cache real do PyJWT para a expiração, um cliente JWKS determinístico para rotação/cooldown e `ThreadPoolExecutor` para exercer a contenção concorrente sem rede externa.
- Dúvidas, desvios do briefing e pendências:
  - os 7 critérios de aceite e os 7 testes exigidos estão cobertos; nenhuma contestação;
  - a contenção de tentativas repetidas quando o próprio JWKS expirou e o endpoint está indisponível, levantada como recomendação não bloqueante na Revisão 1, não foi incluída por não pertencer aos critérios aprovados; recomenda-se abrir tarefa própria para desenhar o comportamento de disponibilidade sem ampliar silenciosamente a T-0001;
  - permanecem as ações e decisões do usuário registradas na Revisão 1 sobre o Caddy público, Cloudflare e aceitação do balde compartilhado por NAT.

---

## 4. Revisões (Claude) e respostas (Codex)

### [2026-10-01] Claude — Revisão 1

**Veredito: AJUSTES** (dois itens pequenos de teste; o código está correto no que se propõe).

**Verificado e correto**
- Suíte padrão rodada pelo Claude: 569 aprovados, 20 ignorados, 0 falhas.
- Critério 1: `_safe_identity` usa só `scope['client']`; teste `test_http_rate_limit_uses_asgi_client_not_forwarded_or_authorization` cobre `Authorization` e `X-Forwarded-For` forjados no ASGI.
- Critério 4 e 5: lock + nova verificação dentro do lock + cooldown em `oidc.py:_resolve_signing_key`; testes de rotação (1 download) e de 50 `kid` desconhecidos (1 download, mais 1 após o cooldown).
- Critério 3 no código: com `cache_keys=False`, a resolução passa sempre por `JWKSetCache`, que expira em `lifespan` (conferido em `.venv/Lib/site-packages/jwt/jwk_set_cache.py:25-31`). Uma chave removida deixa de valer no próximo download após o prazo.
- `deploy/compose.yaml`: a API está só nas redes `backend` (interna) e `egress`, sem `ports`. O risco do `--forwarded-allow-ips "*"` apontado no briefing fica restrito a quem está dentro da rede `backend`.
- Documentação atualizada de forma coerente com o código.

**Bloqueantes (Codex)**
1. **Falta o teste exigido nº 3** (critério 3): JWKS sem a chave antiga e relógio além do `lifespan` → token com a chave antiga negado. Hoje só há `test_oidc_disables_indefinite_per_key_cache`, que verifica um detalhe interno (`cache_info`) e não o comportamento. Sugestão: um cliente JWKS falso cujo conjunto muda, mais o controle do tempo de expiração (ex.: `lifespan` mínimo com `monkeypatch` de `time.monotonic` em `jwt.jwk_set_cache`).
2. **Falta o teste exigido nº 6** (critério 6): `kid` ausente e `kid` com 256 caracteres → `AuthenticationError` e **zero** downloads.

**Não bloqueantes (recomendação; o Codex pode fazer agora ou virar tarefa)**
3. `oidc.py:_match_cached_key` — quando o conjunto JWKS expira e o download falha (Edge Function fora do ar), **cada requisição** tenta baixar de novo, com até 5 s de espera, sem lock nem cooldown (o cooldown só protege o caminho de `kid` desconhecido). Antes da mudança, as chaves já conhecidas sobreviviam à queda. Negar é o comportamento correto (fail-closed), mas a repetição ocupa o threadpool. Correção sugerida: passar também a renovação do conjunto expirado pelo mesmo lock e aplicar um intervalo mínimo entre tentativas que falharam. Teste: endpoint falhando + 20 requisições → no máximo 1 tentativa por intervalo.
4. Uvicorn com `--forwarded-allow-ips "*"` usa a **primeira** entrada do `X-Forwarded-For` (`uvicorn/middleware/proxy_headers.py:176-177`). A cadeia só é segura se o Caddy público (do host) **substituir** o `X-Forwarded-For` vindo da internet. O Caddyfile real do host não está no repositório (só `deploy/host-caddy/Caddyfile.example`, que não declara `trusted_proxies` e, portanto, sanitiza). Ver ações do usuário.
5. Qualquer contêiner na rede externa `serdial21_proxy` (o exemplo mostra o n8n nela) alcança `web:8080` diretamente e pode forjar `X-Forwarded-For`, porque o Caddy interno confia em todas as faixas privadas. Impacto baixo (exige comprometer outro contêiner do host). Registrar como risco conhecido.

**Mudança de comportamento que precisa de decisão do usuário**
6. Antes, cada usuário autenticado tinha seu próprio limite (por token). Agora **todos que saem pelo mesmo IP dividem o mesmo limite**, inclusive autenticados. Limites atuais por IP e por minuto: 1000 gerais, 120 sensíveis (`/identity/*`, aprovar e rejeitar), 30 uploads. Para o piloto, com poucas pessoas no escritório, isso é suficiente. Com muitos usuários atrás do mesmo IP, a equipe inteira passa a dividir 30 uploads por minuto. A solução definitiva (um segundo limite por usuário, aplicado depois de verificar o token) ficou fora do escopo desta tarefa.

**Ações do usuário (antes de publicar)**
- Na VPS, abrir o Caddyfile do Caddy público (o que atende `contabilidade.serdial21.com`) e confirmar que **não** existe `trusted_proxies` no bloco global `servers`.
- Confirmar se o domínio `contabilidade.serdial21.com` passa por Cloudflare com o proxy ativado (nuvem laranja). Se passar, todos os usuários chegariam com IPs da Cloudflare e dividiriam o mesmo limite; nesse caso, avisar antes de publicar.

### [2026-10-01] Codex — Resposta à Revisão 1

- Achado bloqueante 1: corrigido. `test_oidc_removed_key_is_rejected_after_jwks_lifespan` usa `JWKSetCache`, controla `time.monotonic`, troca o JWKS publicado e comprova aceitação antes do prazo e negação depois dele.
- Achado bloqueante 2: corrigido. `test_oidc_invalid_kid_is_rejected_without_jwks_lookup` cobre `kid` ausente e com 256 caracteres, além de vazio e não textual, comprovando zero lookup e zero refresh.
- Teste exigido 2, não apontado como bloqueante: completado com duas origens HTTP e baldes independentes.
- Critério 4: reforçado; os 50 `kid`s diferentes agora são verificados concorrentemente e continuam produzindo um único refresh no intervalo.
- Recomendação não bloqueante 3: não implementada nesta tarefa; é uma política adicional para indisponibilidade após expiração e deve ser especificada separadamente para não ampliar o escopo aprovado. Não contesto o risco técnico.
- Recomendações 4 e 5: riscos reconhecidos e preservados no relatório; dependem da conferência operacional indicada ao usuário.
- Item 6: nenhuma decisão presumida. A aceitação dos limites compartilhados por NAT continua pendente do usuário; o segundo limite por usuário autenticado permanece fora do escopo do briefing.
- Verificação final: `575 passed`, `20 skipped`, `0 failed`.

### [2026-10-01] Claude — Revisão 2

**Veredito: ACEITA tecnicamente** (aguardando a confirmação do usuário para o commit).

- Suíte rodada pelo Claude: 575 aprovados, 20 ignorados, 0 falhas; `git diff --check` limpo.
- `test_oidc_removed_key_is_rejected_after_jwks_lifespan` usa o `PyJWKClient` real com o `JWKSetCache` real e controla `time.monotonic`: aceita em 299 s e nega em 301 s. Cobre o critério 3 pelo comportamento.
- `test_oidc_invalid_kid_is_rejected_without_jwks_lookup` cobre `None`, vazio, não textual e 256 caracteres com zero consultas. Cobre o critério 6.
- O teste de 50 `kid` desconhecidos agora roda em 10 threads e mantém 1 download. O teste de origens distintas cobre o teste exigido nº 2.

**Sobre a recusa do item 3.** O argumento de escopo do Codex é defensável pelo protocolo. Registro, porém, que a mudança desta tarefa troca um comportamento: antes, uma chave já conhecida sobrevivia à queda da Edge Function; agora, depois de 300 s de queda, toda autenticação falha (correto, fail-closed) e cada requisição espera até 5 s por uma nova tentativa (degradação nova). Vira o item 12 da fila. Não bloqueia a publicação, porque o limite por IP contém o volume.

**Conferências operacionais feitas pelo Claude (somente leitura, de fora):**
- `contabilidade.serdial21.com` resolve direto para o IP da VPS; a resposta não traz `cf-ray` nem `server: cloudflare`, e mostra `Via: 1.1 Caddy` duas vezes. **Não há Cloudflare na frente.** Risco de todos os usuários dividirem IPs de CDN: descartado.
- O Caddyfile do Caddy público (`n8n-caddy-1`) é persistente na VPS e não está versionado; não dá para conferir de fora. Fica como ação do usuário antes do deploy (ver Encerramento).

---

## 5. Encerramento

### [2026-10-01] Claude — Encerramento

- Aceite do usuário: 01/10/2026 ("aceito o commit").
- Commit: `14f3450` — `security: key rate limit on trusted origin and bound JWKS caching (T-0001)`.
- Push: pendente, a cargo do usuário.
- Deploy na VPS: pendente. Antes de publicar, o usuário confere no Caddy público que não há `trusted_proxies`:
  `docker exec n8n-caddy-1 sh -c 'grep -rn trusted_proxies /etc/caddy/ || echo NENHUM'` — o esperado é `NENHUM`.
- Pendências que viraram fila: itens 11 (limite por usuário autenticado) e 12 (renovação do JWKS expirado após falha).
- Observação: `scripts/verify_release_secrets.py` falha com 6 falsos positivos já existentes antes desta tarefa (nenhum arquivo desta tarefa). Item 13 da fila.
