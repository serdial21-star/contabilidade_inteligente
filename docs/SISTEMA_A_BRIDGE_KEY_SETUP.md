# Roteiro: gerar e configurar as chaves da ponte de login

Para quando o Lovable já tiver criado as duas funções (`sistema-b-jwks` e
`sistema-b-bridge-token`) do prompt de `docs/integration/SISTEMA_A_LOGIN_BRIDGE_SPEC.md`.
Não precisa saber criptografia — é copiar e colar, na ordem abaixo.

## 0. Antes de começar

Confirme com o Lovable duas coisas que ele te deve devolver ao terminar:
1. Qual endpoint ele usou/criou para validar a sessão do funcionário.
2. O domínio real do projeto Supabase (algo como `abcdefgh.functions.supabase.co`).

Com o domínio em mãos, peça para ele trocar `<project-ref>` pelo valor real
no código (na constante `ISSUER`, dentro de `sistema-b-bridge-token/index.ts`).
Guarde esse endereço completo — você vai precisar dele nos passos 3 e 4.

## 1. Gerar as chaves (no seu computador)

No terminal do VS Code, na pasta do projeto:

```powershell
.\.venv\Scripts\python.exe scripts\generate_bridge_keypair.py
```

Isso imprime dois blocos na tela: um rotulado **CHAVE PRIVADA** e outro
**CHAVE PÚBLICA (JWK)**. Deixe essa janela do terminal aberta — você vai
copiar os dois blocos dela nos próximos passos.

**Nunca cole o bloco da chave privada de volta nesta conversa.** O bloco da
chave pública pode ser colado sem problema, se precisar me mostrar algo.

## 2. Onde colar cada bloco no Supabase

No painel do Supabase do projeto (Sistema A):

- Vá em **Project Settings → Edge Functions → Secrets** (o caminho exato pode
  variar um pouco conforme a versão do painel; procure por "Secrets" ou
  "Environment Variables" dentro de Edge Functions).
- Crie dois segredos:
  - `SISTEMA_B_BRIDGE_PRIVATE_KEY_PEM` → cole o bloco **CHAVE PRIVADA**
    inteiro, incluindo as linhas `-----BEGIN PRIVATE KEY-----` e
    `-----END PRIVATE KEY-----`.
  - `SISTEMA_B_BRIDGE_PUBLIC_JWK` → cole o bloco **CHAVE PÚBLICA (JWK)**
    inteiro (é uma linha só de JSON).

Alternativa, se preferir pelo terminal (precisa da Supabase CLI instalada e
logada no projeto):

```powershell
supabase secrets set SISTEMA_B_BRIDGE_PRIVATE_KEY_PEM="$(Get-Content local_data\sistema_a_bridge\private_key.pem -Raw)"
```

(o JWK público, por ser uma linha só, pode ser colado direto no painel sem
precisar desse comando).

## 3. Confirmar que a função pública responde

Depois que o Lovable publicar as funções e você configurar os segredos, abra
no navegador:

```
https://<domínio-real-do-projeto>/sistema-b-jwks
```

Deve aparecer um JSON parecido com `{"keys":[{"kty":"RSA", ...}]}`. Se der
erro, o mais provável é a função ainda não estar publicada ou o segredo
`SISTEMA_B_BRIDGE_PUBLIC_JWK` não ter sido salvo certo.

## 4. Me avise

Quando o passo 3 funcionar, me diga o domínio real completo. Eu atualizo o
`.env` do Sistema B (`OIDC_ISSUER`, `OIDC_JWKS_URL`) e testamos o login de
verdade, de ponta a ponta.

## Se precisar gerar uma chave nova depois

Rodar o script de novo não sobrescreve nada — ele avisa e para, se já existir
uma chave em `local_data/sistema_a_bridge/private_key.pem`. Para gerar outra
(por exemplo, se a antiga vazar), apague esse arquivo manualmente antes de
rodar de novo, e repita os passos 1 a 4 — a chave antiga para de funcionar
assim que você trocar o segredo no Supabase.
