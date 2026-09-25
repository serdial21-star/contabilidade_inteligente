# ADR 0015 — Publicação interna do Sistema B e reabertura limitada da Wave 0

## Status

Aceita por decisão explícita do usuário em 2026-09-25.

Esta decisão autoriza preparar a primeira publicação interna do Sistema B e
reabre o gate do Connect Hub **somente para a Wave 0 de estabilização,
levantamento e congelamento de contratos**. Não autoriza ainda tráfego de dados
de negócio entre os sistemas.

## Contexto

O Sistema A já possui site próprio e permanece como sistema operacional do
escritório. O Sistema B será um complemento comercial opcional: inicialmente
será usado pela equipe Serdial21, com entrada pelo Sistema A por meio da ponte
de login aprovada no ADR 0014; futuramente poderá ser vendido a outros
escritórios, inclusive sem o Sistema A.

O ambiente disponível possui:

- Hostinger Premium Web Hosting para o Sistema A e bancos já existentes;
- VPS Hostinger KVM 2 com Docker em execução;
- n8n em Docker, acessível internamente pela porta 5678;
- Caddy atendendo HTTP/HTTPS nas portas 80 e 443;
- nenhum MySQL/MariaDB identificado no VPS.

O usuário decidiu publicar primeiro o que já está estruturado no Sistema B e
deixar a integração contábil automática para fatias posteriores. A senha do
usuário de banco `_app` do ambiente `_dev` ainda precisa ser rotacionada antes
de qualquer publicação.

## Decisão

1. **Primeiro público:** a primeira publicação é interna, destinada à equipe
   Serdial21. Não constitui ainda lançamento comercial para outros escritórios.
2. **Entrada:** o acesso parte do Sistema A e reutiliza exclusivamente a ponte
   de identidade aprovada no ADR 0014.
3. **Hospedagem da aplicação:** a preparação de deploy reutilizará Docker e o
   Caddy já existentes no VPS KVM 2. Não será instalado Nginx ou Apache sem uma
   nova necessidade comprovada.
4. **Isolamento operacional:** a implantação do B não poderá interromper,
   reconfigurar silenciosamente nem compartilhar segredos com o n8n existente.
   Portas internas, redes, volumes, health checks e limites de recursos serão
   explícitos.
5. **Banco separado:** A e B mantêm bancos, usuários, credenciais, migrations,
   backups e recuperação separados. O B não consulta tabelas privadas do A e
   não cria foreign keys ou queries cross-database.
6. **Banco de desenvolvimento não é produção:** `_dev` não será promovido ou
   renomeado como banco de produção. O alvo de publicação será provisionado e
   confirmado separadamente antes de migrations ou carga de dados.
7. **Evolução do schema:** toda mudança estrutural continua sendo feita por
   migration Alembic revisável. Alteração manual direta de schema permanece
   proibida. Dados empresariais entram por caso de uso, API ou importador
   auditável e idempotente, salvo operação excepcional aprovada e registrada.
8. **Fronteira de dados:** o Sistema A será a autoridade dos dados operacionais
   que futuramente fornecer ao B; o Sistema B preservará sua própria evidência,
   estado canônico, regras, propostas, aprovações e auditoria. Sincronização
   significa contrato/API/evento, nunca banco compartilhado.
9. **Wave 0 autorizada:** ficam autorizados inventário runtime redigido,
   definição de ownership, congelamento de contratos versionados, desenho de
   autenticação M2M, idempotência, retry/DLQ, transporte documental e plano de
   homologação.
10. **Integração runtime ainda bloqueada:** nenhum cliente, documento, tarefa,
    honorário, imposto ou outro dado de negócio será transmitido automaticamente
    até que o primeiro fluxo seja escolhido, os contratos sejam aprovados e os
    testes de homologação correspondentes passem.
11. **Autoridade contábil preservada:** automação no B produz proposta
    determinística sujeita a revisão e aprovação humana. O sistema contábil
    externo continua autoridade sobre escrituração, saldos e fechamento
    oficiais.

## Primeira fatia de publicação

A primeira fatia deve publicar apenas as capacidades já existentes do B, sem
criar integração de negócio nova:

- frontend e API na mesma origem HTTPS;
- autenticação pela ponte do Sistema A;
- banco exclusivo do B;
- storage privado e persistente;
- rate limiting distribuído;
- backup, health, logs sanitizados e verificação operacional;
- acesso limitado a funcionários explicitamente provisionados.

O subdomínio público foi confirmado pelo usuário em 2026-09-25 como
`contabilidade.serdial21.com`. A confirmação do nome não cria registro DNS nem
autoriza apontá-lo antes do smoke privado.

## Pré-condições para exposição

Antes de liberar tráfego externo:

1. rotacionar a senha `_app` de `_dev` e atualizar somente os ambientes que a
   utilizam;
2. identificar de forma redigida a configuração, as redes e os recursos do
   Docker/Caddy/n8n existentes;
3. implementar e testar o adaptador de rate limit distribuído exigido pela
   configuração de homologação/produção;
4. provisionar banco e credencial exclusivos do ambiente alvo;
5. ensaiar migrations até o head real da cadeia;
6. configurar storage persistente, backup externo e restore verificável;
7. configurar HTTPS, hosts, origens, issuer, audience e JWKS exatos;
8. executar testes automatizados, smoke autenticado e teste de clique real
   Sistema A → Sistema B;
9. obter autorização explícita do corpus real que será colocado no novo
   ambiente; dados existentes em `_dev` não migram automaticamente.

## Consequências

- O gate geral deixa de bloquear planejamento da Wave 0 e preparação da
  publicação interna.
- O gate continua `NO_GO` para sincronização runtime de dados de negócio até
  nova decisão de saída da Wave 0.
- A integração será construída por fatias começando por um tipo de entrada
  contábil explicitamente escolhido; não haverá integração genérica com o
  banco A.
- A futura oferta do B sem o A continua possível, pois identidade, dados e
  regras do B não ficam acoplados ao schema do Sistema A.

## Inspeção do banco `_hom` após autorização condicional

Em 2026-09-25, o usuário autorizou considerar a reclassificação do banco
`u621451815_serdial21_hom` como piloto ativo, condicionada a uma inspeção
somente leitura antes de qualquer migration. A inspeção confirmou:

- MariaDB 11.8.9 com TLS ativo;
- revision `20260907_0009`;
- 33 tabelas;
- 16 tenants, 28 empresas, 32 usuários e 100 eventos de auditoria.

Essas contagens demonstram que `_hom` contém massa histórica/sintética e
evidência de validações anteriores. A reclassificação **não foi executada**.
Misturar dados reais nessa base criaria ambiguidade operacional; limpar a base
apagaria evidência append-oriented. A recomendação técnica passa a ser criar
um banco limpo e exclusivo para o piloto. `_hom` permanece preservado até nova
decisão explícita.

Em seguida, o usuário criou em 2026-09-25 o alvo limpo do piloto:

- banco `u621451815_s21_pilot`;
- usuário exclusivo `u621451815_s21_pilot_app`.

A criação do banco não autoriza migration ou carga de dados. Acesso remoto,
confirmação do host, backup inicial e guard de alvo ainda precedem qualquer
escrita.

O acesso remoto do banco do piloto foi limitado no hPanel ao IPv4 específico
do VPS em 2026-09-25. Não foi configurado wildcard e nenhum outro banco teve a
regra alterada. A regra de rede, por si só, ainda não comprova autenticação,
TLS, banco vazio ou permissão mínima.

Um teste TCP executado no VPS confirmou conectividade com o host MariaDB na
porta 3306. O teste não utilizou credencial, não autenticou e não acessou ou
alterou tabelas.
