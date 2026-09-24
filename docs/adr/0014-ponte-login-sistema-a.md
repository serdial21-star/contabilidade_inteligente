# ADR 0014 — Exceção pontual ao gate do Connect Hub: ponte de login do Sistema A

## Status

Aceita por decisão explícita do usuário em 2026-09-24, depois de eu apresentar
o conflito com o gate e as duas alternativas. Abre uma exceção **estreita e
nomeada** ao veredito `NO_GO` de
`docs/integration/SYSTEM_A_INTEGRATION_READINESS_GATE.md`; não revoga o gate
para mais nada.

**Lado do Sistema B implementado e testado em 2026-09-24**: modo de login
`authMode: 'bridge'` em `app/app.js` (handoff via `#overview?bridge=<token>`,
nunca por armazenamento do navegador), `scripts/bootstrap_user_access.py`
(provisionamento idempotente de usuário/papel/acesso), 8 testes automatizados
novos. Testado de ponta a ponta contra a API real e o banco `_dev` usando o
provedor de desenvolvimento no papel do emissor — retornou as 3 empresas reais
do tenant. **Lado do Sistema A ainda não implementado**: especificação
completa (incluindo o achado de que a assinatura RS256 não pode acontecer em
node de código do n8n — trava já conhecida do item 0b-3) em
`docs/integration/SISTEMA_A_LOGIN_BRIDGE_SPEC.md`.

## Contexto

O usuário pediu para o Sistema B parar de usar dados sintéticos e ficar
testável pelo site de verdade, entrando pelo login do Sistema A (sem duplicar
login). Isso exige que o Sistema B confie, em tempo real, numa identidade
emitida pelo Sistema A — ou seja, tráfego automático entre os dois sistemas
toda vez que alguém abre o Sistema B. É exatamente o tipo de coisa que o gate
do Connect Hub existe para controlar (item 2-2 do painel Ponte Serdial21:
contratos do n8n não congelados, nenhuma credencial M2M ainda, sem
confirmação de entrega, sem ambiente de homologação separado).

Perguntado, o usuário decidiu explicitamente abrir uma exceção pontual para
essa peça específica, não para o Connect Hub inteiro.

## Decisão

1. **O que esta exceção autoriza:** uma ponte de **identidade de login**
   (Sistema A confere a sessão já existente do funcionário e emite um token
   assinado; o Sistema B verifica esse token pelo mecanismo OIDC que já existe
   — `OidcJwtVerifier`, sem código novo de verificação). Só isso.
2. **O que esta exceção NÃO autoriza:** sincronização de dados de negócio,
   envio/recebimento de clientes, documentos, tarefas, honorários ou impostos
   entre os sistemas, congelamento de workflows do n8n, ou qualquer outro item
   do gate. O veredito geral do Connect Hub continua `NO_GO`.
3. **Escopo do tenant:** um único tenant fixo no Sistema B (Serdial21,
   `5463ce7c-31b5-471d-97aa-89f043292ebb`), porque o Sistema A de hoje não tem
   conceito de escritório/tenant (confirmado por grep no código-fonte em
   2026-09-24 — nenhuma coluna `tenant_id`/`escritorio_id` em `clientes` ou
   `funcionarios`). Vender o Sistema A para outros escritórios é um projeto à
   parte, muito maior (reescrever o Sistema A para multi-tenant), tratado como
   iniciativa futura separada — não é escopo deste ADR nem da ponte de login.
4. **Escopo de pessoas:** somente funcionários (`funcionarios`), não clientes
   do portal (`clientes`) — o Sistema B é ferramenta de trabalho da equipe
   contábil, não uma tela do cliente final.
5. **Contrato técnico da ponte** (para o Sistema A implementar do lado dele):
   - Emissor (`iss`) fixo e estável, ex.: `https://sistemaa.serdial21.com`
     (ou o domínio real equivalente — não pode mudar depois sem invalidar
     usuários já cadastrados no B).
   - Audiência (`aud`) fixa, ex.: `serdial21-sistema-b`.
   - `sub` estável e único por funcionário — recomendado `funcionario:<id>`
     (nunca o e-mail, que pode mudar).
   - `tenant_id` sempre o UUID fixo do Serdial21 acima.
   - Assinatura RS256, chave privada só no lado do Sistema A, endpoint JWKS
     público (sem dado sensível) para o Sistema B buscar a chave pública.
   - Token de vida curta (recomendado 15–60 min); revogação real não existe
     ainda (mesma limitação já registrada em `docs/OIDC_CONFIGURATION.md`).
6. **Nunca circula senha nem token de sessão do Sistema A** para o navegador
   do Sistema B; o handoff usa o token OIDC novo, de vida curta, específico
   desta ponte.
7. Cada pessoa que for autorizada a usar o Sistema B precisa ser cadastrada
   explicitamente lá (`users` + `tenant_memberships` + `role_bindings` +
   `company_accesses`) — o token provar identidade não basta para dar acesso;
   a autorização granular continua sendo decidida dentro do Sistema B, como já
   acontece hoje para qualquer usuário.

## Consequências

- `docs/integration/SYSTEM_A_INTEGRATION_READINESS_GATE.md` ganha uma nota
  explícita desta exceção, sem mudar o veredito geral.
- O provedor OIDC de desenvolvimento (`scripts/dev_identity_provider.py`,
  ADR implícito no seu próprio código) continua existindo e sendo útil para
  testes locais sem depender do Sistema A estar no ar — a ponte real é para
  quando o funcionário realmente entra pelo Sistema A.
- Quando o Sistema A migrar para multi-tenant (projeto futuro, fora de
  escopo), este ADR precisa ser revisitado: o `tenant_id` fixo vira um
  `tenant_id` por escritório, informado pela própria ponte.
