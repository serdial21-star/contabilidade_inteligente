# Especificação: ponte de login Sistema A → Sistema B

**Status: implementada e verificada de ponta a ponta em 2026-09-24.** Este
documento passa a ser referência histórica/de manutenção — não é mais um
roteiro de "a construir". Resumo do que existe hoje:

| Peça | Onde | Status |
| --- | --- | --- |
| `sistema-b-jwks` (Edge Function) | Supabase, projeto `lgohzjneyvdtonpeapvd` | no ar, retorna a chave pública |
| `sistema-b-bridge-token` (Edge Function) | idem | no ar, emite token RS256 após validar a sessão |
| `[SECURITY] Validar Sessão de Funcionário` (n8n) | `n8n.serdial21.com/webhook/security/validar-sessao-funcionario` | ativo, reaproveita a consulta do workflow de permissões |
| `authMode: 'bridge'` | `app/app.js` (Sistema B) | testado com sessão real |
| Chaves RS256 | segredos do Supabase (`SISTEMA_B_BRIDGE_PRIVATE_KEY_PEM`/`..._PUBLIC_JWK`) | configuradas |

Base de decisão: [ADR 0014](../adr/0014-ponte-login-sistema-a.md) (exceção
pontual e nomeada ao gate do Connect Hub, só para identidade de login).
Isto é uma especificação técnica para o lado do **Sistema A**, que eu não
posso executar (só leitura nesse repositório). O lado do Sistema B já está
pronto e testado — ver seção 5.

## 1. Achado importante: onde NÃO assinar o token

O item **0b-3** do painel Ponte Serdial21 já registrou que o ambiente n8n do
Sistema A roda em modo restrito de execução de código: bloqueia tanto
`require('crypto')` quanto o `crypto` global do JavaScript moderno. Isso
derrubou uma tentativa anterior de gerar token mais forte, duas vezes.

Assinar RS256 exige exatamente esses recursos de criptografia. **Não tente
assinar o token dentro de um node de código do n8n** — vai esbarrar na mesma
trava. O lugar certo é uma **Supabase Edge Function** (Deno), que roda num
runtime sem essa restrição e já é o padrão usado nas outras funções de
segurança do projeto (`proxy-document-download`, etc.).

## 2. Contrato exato que o Sistema B espera

| Claim/campo | Valor | Observação |
| --- | --- | --- |
| `iss` | uma URL fixa e estável, ex.: `https://<project-ref>.functions.supabase.co/sistema-b-bridge` | não pode mudar depois; usuários já cadastrados no B ficam presos a este valor |
| `aud` | `serdial21-sistema-b` | fixo |
| `sub` | `funcionario:<id>` (nunca o e-mail, que pode mudar) | precisa ser cadastrado no Sistema B com este valor exato |
| `tenant_id` | `5463ce7c-31b5-471d-97aa-89f043292ebb` | tenant único do Serdial21 no Sistema B (ADR 0014); só vale para o banco `_dev` usado nos testes — confirmar o id certo se o alvo for outro banco |
| `iat`, `exp` | emissão e expiração (recomendado 15–60 min) | token de vida curta |
| algoritmo | RS256 | chave privada só existe no lado do Sistema A |

## 3. Duas peças novas no Sistema A (Supabase Edge Functions)

### 3.1 `supabase/functions/sistema-b-jwks/index.ts` — pública, sem `verify_jwt`

Serve só a chave pública. Nunca expõe a privada.

```typescript
import { corsHeaders } from '../_shared/cors.ts'; // ajuste ao padrão real do projeto

const JWK = JSON.parse(Deno.env.get('SISTEMA_B_BRIDGE_PUBLIC_JWK')!); // gerado uma vez, ver seção 4

Deno.serve((req) => {
  if (req.method === 'OPTIONS') return new Response(null, { headers: corsHeaders });
  return new Response(JSON.stringify({ keys: [JWK] }), {
    headers: { ...corsHeaders, 'Content-Type': 'application/json' },
  });
});
```

`config.toml`: `[functions.sistema-b-jwks]` com `verify_jwt = false` (é
pública por natureza, como um JWKS de qualquer IdP real).

### 3.2 `supabase/functions/sistema-b-bridge-token/index.ts` — autenticada

Recebe a sessão já validada do funcionário (mesmo padrão dos outros proxies:
`x-app-token` com o token de sessão atual, porque `verify_jwt=true` consome
o cabeçalho `Authorization` para o JWT do próprio Supabase). Confere a sessão
chamando o mesmo caminho que já valida sessão de funcionário hoje (reaproveitar
a lógica existente, não duplicar SQL) e, só se válida, assina o token.

```typescript
import { corsHeaders } from '../_shared/cors.ts';

const ISSUER = 'https://<project-ref>.functions.supabase.co/sistema-b-bridge';
const AUDIENCE = 'serdial21-sistema-b';
const TENANT_ID = '5463ce7c-31b5-471d-97aa-89f043292ebb';
const TTL_SECONDS = 30 * 60;

async function importPrivateKey(): Promise<CryptoKey> {
  const pem = Deno.env.get('SISTEMA_B_BRIDGE_PRIVATE_KEY_PEM')!; // ver seção 4
  const body = pem.replace(/-----[^-]+-----/g, '').replace(/\s+/g, '');
  const der = Uint8Array.from(atob(body), (c) => c.charCodeAt(0));
  return crypto.subtle.importKey(
    'pkcs8', der, { name: 'RSASSA-PKCS1-v1_5', hash: 'SHA-256' }, false, ['sign'],
  );
}

function base64url(bytes: ArrayBuffer | Uint8Array): string {
  const arr = bytes instanceof Uint8Array ? bytes : new Uint8Array(bytes);
  return btoa(String.fromCharCode(...arr)).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

async function signBridgeToken(funcionarioId: string): Promise<string> {
  const header = { alg: 'RS256', typ: 'JWT', kid: 'sistema-b-bridge-1' };
  const now = Math.floor(Date.now() / 1000);
  const payload = {
    iss: ISSUER, aud: AUDIENCE, sub: `funcionario:${funcionarioId}`,
    tenant_id: TENANT_ID, iat: now, exp: now + TTL_SECONDS,
  };
  const encoder = new TextEncoder();
  const signingInput = `${base64url(encoder.encode(JSON.stringify(header)))}.${base64url(encoder.encode(JSON.stringify(payload)))}`;
  const key = await importPrivateKey();
  const signature = await crypto.subtle.sign(
    { name: 'RSASSA-PKCS1-v1_5' }, key, encoder.encode(signingInput),
  );
  return `${signingInput}.${base64url(signature)}`;
}

Deno.serve(async (req) => {
  if (req.method === 'OPTIONS') return new Response(null, { headers: corsHeaders });
  const sessionToken = req.headers.get('x-app-token');
  if (!sessionToken) {
    return new Response(JSON.stringify({ error: 'missing session' }), { status: 401, headers: corsHeaders });
  }
  // Reaproveitar a MESMA validação de sessão de funcionário já usada em
  // outras rotas autenticadas (SHA2 contra security_sessoes_funcionarios,
  // conferindo expira_em e revogado_em) — chamar o webhook n8n existente
  // de validação, não reimplementar a query aqui.
  const validation = await fetch('https://n8n.serdial21.com/webhook/validar-sessao-funcionario', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ token: sessionToken }),
  });
  if (!validation.ok) {
    return new Response(JSON.stringify({ error: 'invalid session' }), { status: 401, headers: corsHeaders });
  }
  const { funcionario_id, status } = await validation.json();
  if (!funcionario_id || status !== 'Ativo') {
    return new Response(JSON.stringify({ error: 'inactive' }), { status: 403, headers: corsHeaders });
  }
  const token = await signBridgeToken(String(funcionario_id));
  return new Response(JSON.stringify({ access_token: token, expires_in: TTL_SECONDS }), {
    headers: { ...corsHeaders, 'Content-Type': 'application/json' },
  });
});
```

**Ponto em aberto real:** não sei se já existe um webhook n8n que só valida
sessão de funcionário e devolve `funcionario_id`/`status` sem fazer mais
nada. Se não existir, é preciso criar um pequeno workflow novo para isso
(reaproveitando a mesma query SHA2 já usada no login), porque a Edge Function
não deve acessar o MySQL diretamente (padrão do projeto: Edge Function proxya
n8n, nunca fala direto com o banco).

## 4. Gerar o par de chaves (uma vez, fora do código)

Rodar localmente (não no n8n, não em produção), guardar a privada só como
segredo do Supabase, nunca no código nem no git:

```bash
openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:2048 -out sistema_b_bridge_private.pem
openssl rsa -pubout -in sistema_b_bridge_private.pem -out sistema_b_bridge_public.pem
```

Depois converter a chave pública para o formato JWK (posso gerar esse JSON se
você me passar a chave pública — ela não é secreta). Guardar:
- `SISTEMA_B_BRIDGE_PRIVATE_KEY_PEM` — segredo do Supabase (nunca no código).
- `SISTEMA_B_BRIDGE_PUBLIC_JWK` — pode ficar até em variável de ambiente
  normal, não é sensível.

## 5. Lado do Sistema B (já pronto e testado em 2026-09-24)

- `OidcJwtVerifier` já valida qualquer emissor configurado — só falta apontar
  `.env`: `OIDC_ISSUER`, `OIDC_AUDIENCE=serdial21-sistema-b`,
  `OIDC_JWKS_URL=https://<project-ref>.functions.supabase.co/sistema-b-jwks`
  quando a função existir.
- `app/app.js`: novo modo `authMode: 'bridge'` — lê o token de
  `#overview?bridge=<token>`, nunca de armazenamento do navegador, some com a
  URL antes de qualquer outra coisa. Testado (`tests/frontend/test_bridge_login.py`).
- `scripts/bootstrap_user_access.py`: cadastra o funcionário no Sistema B
  (idempotente). Já rodado para `dev-sergio` como teste; para o funcionário
  real, rodar de novo com `--subject funcionario:<id>` e o `--issuer` real.
- Testado de ponta a ponta em 2026-09-24 com o provedor de desenvolvimento
  (`scripts/dev_identity_provider.py`) fazendo o papel do Sistema A: API real
  respondeu com as 3 empresas reais do tenant. Falta só trocar o emissor de
  teste pelo real quando as duas funções acima existirem.

## 6. O que esta ponte NÃO faz (fora de escopo, ADR 0014)

Não sincroniza cliente, documento, tarefa, honorário ou imposto. Não cria
usuário automaticamente a partir de qualquer login — cada funcionário
autorizado a usar o Sistema B precisa ser cadastrado explicitamente com
`bootstrap_user_access.py`. Não decide o provedor de identidade definitivo da
Fase 11.
