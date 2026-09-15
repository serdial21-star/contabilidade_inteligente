# Modelo de segurança documental — Phase 06

Todas as rotas exigem bearer OIDC RS256. O tenant vem do principal verificado;
nunca da rota ou corpo. Antes da consulta, `AuthorizationService` revalida
usuário, membership, empresa ativa, CompanyAccess e a permissão `company.read`.
Empresa inexistente, cross-tenant, sem acesso e ID arbitrário recebem a mesma
negação 403. Documento inexistente no escopo recebe 404 genérico; a query sempre
inclui `tenant_id + company_id + id`.

Os uploads especializados continuam exigindo `journal.propose` e revalidam
company scope no efeito. A Phase 06 não criou write alternativo.

## Minimização e conteúdo não confiável

Nome, origem, status e códigos são dados não confiáveis. O backend não constrói
paths a partir do nome; a borda de import rejeita nomes com caminho. O frontend
aplica `escapeHtml` antes dos templates. Um filename sintético hostil faz parte
dos testes e permanece texto. A CSP same-origin continua ativa, sem script
inline.

A projeção não devolve `storage_key`, hash, `artifact_id`, bytes, mensagem
interna de issue, estados brutos de auditoria ou credenciais. O storage local
existente usa chaves geradas no servidor. Download não recebeu URL pública; o
serviço de leitura existente confere vínculo empresa–recebimento e integridade
SHA-256, mas ainda não está exposto por HTTP.

Deduplicação é feita no backend por SHA-256; a UI apenas apresenta o resultado.
Filtros têm tamanho limitado, paginação máxima 100 e datas tipadas; intervalo
invertido retorna 422 seguro. Testes cobrem autenticação, cross-tenant,
CompanyAccess, document IDOR, minimização, filename hostil e upload company IDOR
nos endpoints especializados.

## Gaps declarados

- `MALWARE_SCANNING = INFRASTRUCTURE_GAP`; nenhum antivírus é alegado;
- `DOCUMENT_DOWNLOAD = DEFERRED`; nenhuma URL assinada/pública existe;
- `DOCUMENT_UPLOAD = BACKEND_GAP` para upload genérico;
- histórico por documento requer projeção auditável específica;
- object storage cloud e política de retenção continuam gates posteriores;
- browser/assistive technology QA é gate manual nesta execução.
