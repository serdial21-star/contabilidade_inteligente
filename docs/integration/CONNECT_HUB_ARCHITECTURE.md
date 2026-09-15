# Connect Hub Architecture

## Decisão arquitetural

O alvo é `CORE + INTEGRATION PORT + SERDIAL21 CONNECTOR`. O core do Contabilidade Inteligente não conhece tabelas, IDs, pastas Drive, endpoints administrativos ou nomes de workflows do Serdial21 Operacional. O conector traduz contratos canônicos; o n8n/Connect Hub valida envelopes, roteia, coordena retries e notificações. Ele não decide contabilidade, não autoriza usuários do Sistema B e não persiste um segundo domínio contábil.

```
CLIENTE
  |
  v
[Portal/Admin A] -> [Aplicação A] -> [DB A + Google Drive]
                         |
                     outbox/API
                         v
                [Connect Hub / n8n]
                 validate | route | retry | DLQ
                    /                 \
        [Serdial21 connector]      [notifications]
                    |
                    v
          [/api/integrations/v1]
                    |
             [Application B]
                    |
       [DB B + evidence storage B]
```

## Limites de responsabilidade

| Componente | Faz | Não faz |
| --- | --- | --- |
| Sistema A | Relação/cadastro operacional, portal, tarefas, publicações, Drive | Escrever tabelas do B; aprovar proposta contábil |
| Connect Hub | Validar versão/envelope, autenticar origem, traduzir no conector, rotear, retry/DLQ, correlação | Regra contábil, autorização paralela, autoridade de estado |
| Sistema B | Ingestão/evidência, processamento, regras, propostas, decisão humana, locks, auditoria | Escrever DB A; assumir lifecycle operacional |

## Fluxos

### Dados, comandos e eventos

```
A commit + outbox -> evento A -> Hub -> comando/API B -> commit B + inbox/audit
B commit + outbox -> evento B -> Hub -> comando/API A -> commit A + inbox/audit
```

Eventos anunciam fatos; comandos pedem um efeito ao sistema dono. Um callback operacional nunca muda aprovação, lock ou regra no B. Cada sistema confirma apenas após persistir seu efeito e recibo idempotente.

### Autenticação

```
emissor backend -> TLS + key-id + timestamp + request-id + HMAC(body)
receptor -> allowlist opcional -> janela/replay -> assinatura -> escopo -> idempotência
```

No MVP, cada direção usa credencial própria, armazenada em secret store/backend, com rotação e revogação. Futuro: OAuth2 Client Credentials; mTLS em ambientes que suportem operação de certificados. Tokens de browser são proibidos.

### Cliente/empresa

1. A confirma criação/alteração/desativação e publica evento versionado.
2. Hub normaliza transporte, não altera semântica empresarial.
3. B correlaciona `external_system + external_type + external_id`; CNPJ com 14 dígitos é business key auxiliar.
4. Zero matches permite onboarding conforme política aprovada; múltiplos matches ou CNPJ divergente vão para revisão manual.
5. `CLIENT_DISABLED` não apaga dados do B e não contorna retenção/legal hold.

### Documento

```
cliente -> Portal A -> Drive A + metadata A -> DOCUMENT_RECEIVED
 -> Hub -> B solicita URL curta -> baixa por TLS -> valida tamanho/hash/tipo
 -> quarentena/intake B -> evidência imutável B -> NF-e/OFX/outro
```

Recomendação: **short-lived URL para secure pull**. A segue dono do arquivo operacional; B mantém sua própria cópia imutável somente quando necessária como evidência reproduzível do processamento. A URL é de uso único/curta, escopada ao objeto, sem credenciais Drive no payload. Fallback para stream backend-to-backend é aceitável para provedores sem URL assinada. Processar diretamente um link Drive mutável não atende auditoria; copiar toda a árvore Drive é duplicação indevida.

O idempotency key é estável, por exemplo `SERDIAL21_OPERATIONAL:DOCUMENT:<external_id>:v1`, associado ao hash. Mesma chave+hash retorna o resultado existente; mesma chave+conteúdo diferente produz conflito e revisão.

### Tarefas

```
B: exception/review -> TASK_REQUIRED -> Hub -> A cria tarefa
A -> TASK_CREATED/ack com external mapping -> B registra vínculo
```

A é dono do lifecycle da tarefa (`a_fazer`, andamento, concluída). O payload contém empresa, categoria, prioridade, resumo minimizado e referência/deep link do B — nunca XML/OFX, proposta completa ou segredo. Concluir tarefa no A não aprova proposta no B. A aprovação ocorre no B por profissional autorizado e apenas gera status operacional de retorno.

### Decisão e publicação

B produz `ACCOUNTING_PROPOSAL_APPROVED` ou `REJECTED`; A consome uma projeção minimizada para visibilidade. A não se torna autoridade contábil. Para publicação futura, B solicita/disponibiliza artefato e A, dono do portal/publicação, decide e registra `DOCUMENT_PUBLISHED`. Cliente não recebe poder de aprovação contábil.

### Falha e retry

```
timeout/429/5xx -> retry exponencial com jitter (máx. 5)
4xx de validação/auth -> sem retry automático -> DLQ/revisão
duplicate -> resposta idempotente 200/202
tentativas esgotadas -> DLQ + alerta + reconciliação pelo owner
```

Timeout após envio é estado desconhecido: consultar por idempotency key antes de reenviar. Payload e IDs são preservados. Sem loops ilimitados. Observabilidade técnica e auditoria de negócio são distintas.

## Contrato semântico

- Envelope: `event_id`, `event_type`, `event_version`, `occurred_at` UTC, `source_system`, `correlation_id`, `idempotency_key`, `company_external_reference`, `payload`.
- Resposta do Hub: `success`, `request_id`, `data`; erro: `success=false`, `request_id`, `error.code` estável e `error.message` seguro.
- `competence`: `YYYY-MM`; data de negócio: ISO `YYYY-MM-DD`; timestamp técnico: ISO 8601 UTC.
- Dinheiro: string decimal (`"1234.56"`), moeda ISO separada; nunca float autoritativo.
- Status continuam enums dos respectivos domínios; mapeiam-se apenas efeitos necessários.

## Homologação

```
[A HOM] <-> [HUB HOM] <-> [B HOM]
 DB A HOM     secrets HOM     DB/storage B HOM
 Drive HOM    logs/DLQ HOM    IdP/service client HOM
```

URLs, credenciais, bancos, pastas Drive, logs, filas/DLQ e chaves são separados por ambiente. São proibidos `PROD A -> DEV B`, `DEV A -> PROD B` e segredo de produção em homologação. O teste E2E usa tenant/empresa e documentos sintéticos.

## Independência comercial

O port canônico do B aceita conectores futuros de outros portais, ERPs e bancos. Apenas o `SERDIAL21 CONNECTOR` conhece `cliente_id`, `tasks_master`, versões legadas ou estrutura Drive. Essa separação preserva a venda do produto a outros escritórios.
