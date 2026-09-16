# Mapa técnico de fluxos de dados

**Status:** `TECHNICAL_INPUT_ONLY`; não determina papéis LGPD ou transferência internacional.

| Fluxo atual | Dados | Controles / destino | Estado |
|---|---|---|---|
| Navegador → IdP → API | credenciais somente no IdP; JWT, subject e claims na API | OIDC PKCE/JWT RS256, issuer/audience/JWKS; token em memória | fornecedor de produção pendente |
| Navegador → API | comandos e consultas autorizadas | TLS requerido em produção, escopo tenant/company e permissões | implementado; exposição externa bloqueada |
| Upload NF-e/OFX → object storage + banco | arquivo bruto, hash, metadados e dados canônicos | chave protegida, escrita imutável, hash, linhagem | storage local no desenvolvimento; produção pendente |
| API/casos de uso → banco | identidade, empresa, configuração, propostas, privacidade | SQLAlchemy, transação, filtros de escopo | migration 0012 não aplicada |
| Aplicação → auditoria | IDs, ator, ação, estados permitidos, correlação | append-oriented, sanitização e limite de estado | implementado |
| Aplicação → logs/métricas | fatos técnicos sanitizados e contagens | sem conteúdo bruto e sem labels tenant/company | coletor externo não configurado |
| Banco/storage → backup → restore | cópia operacional | checksum, destino protegido e drill; object storage não homologado | reconciliação de ações de privacidade pendente |
| DSR interno → USERS/manual sources → relatório em memória | referências e resumo mínimo | autorização, CompanyAccess, identidade verificada, auditoria | parcial; sem endpoint público |

## Fluxos inexistentes ou futuros

- **IA externa:** `NONE`. Existe porta abstrata de inferência, sem adaptador de rede/provedor ativo; nenhum envio externo está autorizado.
- **System A:** `DEFERRED`; nenhum fluxo existe.
- **Domínio:** `BLOCKED`; não há exportação/posting.
- **Connect Hub, analytics e marketing lead:** não conectados.

```text
Navegador ──OIDC──> IdP (a selecionar)
    │ JWT/comandos
    v
API ──> casos de uso ──> banco relacional
 │              ├──────> object storage local
 ├──> auditoria ├──────> logs sanitizados
 └──> métricas agregadas

banco/storage ──> backup protegido ──> restore isolado
                              └─ reconciliação privacy: PENDENTE
```

Qualquer novo destino, país, suboperador ou fluxo de dados real exige atualização deste mapa e revisão jurídica/segurança antes da ativação.
