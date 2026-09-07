# Execução 22 — segurança e hardening

Revisão estática e por testes da superfície executável do MVP em 07/09/2026.
O MVP expõe somente os endpoints de saúde; entradas documentais e a jornada
contábil são, por ora, serviços internos. Esta limitação reduz a superfície
HTTP, mas não elimina os riscos da futura exposição desses serviços.

## Achados e correções

| Achado | Severidade | Exploração e impacto | Correção | Teste |
| --- | --- | --- | --- | --- |
| O `upload` gravava bytes no storage antes de confirmar que o `batch_id` existia no tenant e na empresa. | Alta | Um usuário já autorizado na empresa podia repetir IDs inexistentes e criar evidências órfãs, consumindo storage sem uma importação rastreável. | O lote agora é consultado no escopo tenant/company antes de hash ou escrita. | `test_invalid_batch_cannot_create_orphaned_storage_object` |
| O intake genérico não possuía teto de bytes. | Alta | Um chamador interno ou futuro endpoint podia persistir arquivos arbitrariamente grandes e exaurir disco; o limite da NF-e só ocorria depois de a evidência ser armazenada. | `DOCUMENT_MAX_UPLOAD_BYTES` (10 MiB por padrão, máximo configurável de 50 MiB) é validado antes de qualquer escrita. A NF-e acima do seu limite específico continua preservada e quarentenada quando ainda couber no limite genérico, mantendo a evidência exigida pela trilha de auditoria. | `test_upload_limit_rejects_content_before_storage_write`; teste de bootstrap da NF-e |
| O parser NF-e tinha limite de bytes e bloqueio de DTD/entidades, mas não limitava quantidade de elementos antes de construir a árvore. | Média | XML dentro do teto de bytes, porém com muitos nós, poderia elevar uso de CPU e memória. | `NFE_MAX_XML_ELEMENTS` (100.000 por padrão) interrompe o preflight em Expat antes de `ElementTree.fromstring`; versão do parser avançou para `1.2.0`. | `test_rejects_xml_with_too_many_elements_before_tree_construction` |
| Respostas HTTP não continham cabeçalhos defensivos. | Média | Um consumidor/browser poderia interpretar conteúdo indevidamente, carregar a API em frame ou manter respostas potencialmente sensíveis em cache. | Middleware global adiciona `Cache-Control: no-store`, CSP restritiva, `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `Referrer-Policy` e `Permissions-Policy`. | `test_liveness_contract` |

## Controles verificados, sem vulnerabilidade encontrada

| Superfície | Resultado da revisão |
| --- | --- |
| Tenant isolation, autorização e IDOR | Repositórios críticos recebem `tenant_id`/`company_id`; autorização revalida usuário ativo, membership, CompanyAccess, papel e permissão. Recursos externos retornam negação uniforme. Há testes cross-tenant, acesso revogado e rastreio de exportação. |
| SQL injection | Consultas usam SQLAlchemy parametrizado; a única SQL textual identificada é `SELECT 1` constante de readiness. Não há interpolação de entrada em SQL. |
| XML / XXE | DTD, entidades, entidades externas e UTF-32 são rejeitados antes do parse; tamanho e número de elementos agora possuem limite. |
| Path traversal | Nome do arquivo não aceita caminho; chaves locais são resolvidas sob a raiz e recusam caminho absoluto ou escape por `..`. |
| Mass assignment | Não há endpoints de mutação; comandos são dataclasses explícitas e ORM não é exposto como schema de API. |
| Secrets e logging | URL de banco usa `SecretStr`; `.env` está ignorado; não há logging de payloads, XML ou credenciais no código revisado. |
| Unsafe deserialization | Não foram encontrados `pickle`, `yaml.load`, `eval`, `exec` ou desserialização de objetos não confiáveis. |
| CORS | Não há middleware CORS; portanto nenhum origin externo recebe permissão implícita pelo backend. |
| Erros detalhados | `debug` é vedado em produção; readiness responde somente estado genérico, sem URL ou erro de banco. |
| Prompt injection e IA | A IA não executa efeito crítico e as decisões humanas/versões são conferidas na jornada. Conteúdo de documentos não é interpretado como instrução de sistema. |
| Background jobs e integrações | Não há jobs em background ou chamada efetiva a fornecedor no MVP. O conector Domínio permanece bloqueado para homologação. |

## Riscos remanescentes que exigem decisão de implantação

| Problema | Severidade | Exploração e impacto | Correção necessária | Teste a criar |
| --- | --- | --- | --- | --- |
| Não há rate limiting distribuído. | Média | Mesmo os endpoints públicos de saúde podem sofrer negação de serviço; futuros endpoints de upload ampliariam o impacto. | Definir no gateway/proxy a chave (IP, identidade e tenant), limites por rota e resposta `429`; não foi adicionado limitador in-process por não ser consistente entre réplicas nem ter identidade HTTP aprovada. | Integração no gateway com bursts, janela e isolamento por tenant. |
| TLS, HSTS e allowlist de hosts não são configurados pela aplicação. | Média | Uma implantação sem proxy corretamente configurado pode aceitar tráfego sem TLS ou host inesperado. | Formalizar proxy de borda, TLS obrigatório, HSTS após confirmação de domínio e allowlist de hosts. | Smoke test de produção no proxy. |
| Não existe análise CVE automatizada no repositório. | Média | Uma dependência com vulnerabilidade divulgada após o lockfile pode permanecer em uso. | Incluir scanner de dependências no CI com política de correção e exceções auditadas. Nesta execução, `pip check` valida apenas consistência de instalação, não CVEs. | Job de CI que falha em vulnerabilidade acima do limiar aprovado. |
| Limite de corpo HTTP na borda ainda não existe. | Média | Antes de o serviço aplicar `DOCUMENT_MAX_UPLOAD_BYTES`, um servidor ASGI pode já ter recebido bytes em memória. | Configurar limite no proxy/servidor e, ao criar rota de upload, aplicar streaming com limite coerente e resposta `413`. | Teste ASGI/integração que envia corpo sem `Content-Length` acima do teto. |

Não foram implementados CORS permissivo, rate limiter local, autenticação improvisada ou jobs novos: todos exigem decisões de produto/infraestrutura ainda não aprovadas.
