# Contrato de segurança do reverse proxy de produção

O proxy/plataforma é a terminação TLS autorizada entre internet e o processo ASGI. Este documento não provisiona infraestrutura.

## Requisitos obrigatórios

- servir somente TLS moderno e redirecionar HTTP para HTTPS antes da aplicação;
- encaminhar tráfego ao ASGI por rede privada e restringir acesso direto à porta interna;
- preservar `Host` original, que deve constar em `TRUSTED_HOSTS`;
- remover headers de forwarding recebidos do cliente e recriá-los somente no proxy confiável;
- não tornar `X-Forwarded-For` autoridade sem allowlist de proxies;
- impor os mesmos ou menores limites: JSON geral 1 MiB, NF-e 5 MiB e OFX 10 MiB, salvo valores explicitamente revisados;
- aplicar timeout de header/body/upstream e upload lento; não manter conexões ilimitadas;
- manter allowlist CORS no aplicativo e não adicionar wildcard no proxy;
- preservar CSP, `no-store`, `nosniff`, Referrer-Policy, Permissions-Policy e frame protection;
- preservar `X-Correlation-ID` e não registrar Authorization, cookies, query sensível ou body;
- limitar `/health/live` a resposta mínima; `/health/ready` não revela host/credenciais e deve ser usado por rede interna;
- manter rate limit distribuído compartilhado entre instâncias, com chave segura e política por classe de endpoint.

## HSTS

O aplicativo emite `Strict-Transport-Security: max-age=31536000; includeSubDomains` em production somente depois de a configuração afirmar HTTPS externo. O proxy não deve criar política divergente. `preload` permanece adiado até comprovação de HTTPS para todos os subdomínios, controle do domínio e aprovação operacional.

## Cliente real

O rate limit pré-autenticação usa somente o endereço de cliente já resolvido no escopo ASGI e nunca usa o Bearer ainda não verificado. O middleware ignora `X-Forwarded-For`; cabe ao servidor ASGI aceitá-lo exclusivamente do proxy autorizado, em rede privada. Na topologia de duas camadas, o Caddy público sanitiza a origem recebida da internet e o Caddy interno confia apenas em proxies de faixas privadas, em ordem estrita, antes de encaminhar ao ASGI. Nunca aceite uma cadeia de forwarding fornecida diretamente pela internet. Tokens distintos enviados pela mesma origem permanecem no mesmo limite.
