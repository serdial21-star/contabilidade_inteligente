# Segurança Fiscal e Financeira — Phase 07

## Controles aplicados

| Fronteira | Controle |
|---|---|
| Autenticação | Bearer JWT RS256 validado pela fundação OIDC existente. |
| Autorização | Leitura com `company.read`; importação com `journal.propose`; decisão sempre no servidor. |
| Isolamento | `tenant_id`, `company_id`, membership e `CompanyAccess` revalidados; consultas SQL usam ambos os escopos. |
| IDOR | Empresa, NF-e, extrato e transação de outro escopo retornam negação uniforme, sem confirmar existência. |
| Upload | Tipo, nome e tamanho validados no backend; pré-checagem de extensão no browser é apenas UX. |
| XML | Parser incremental com limite; DOCTYPE, entidade e referência externa rejeitados; sem `eval`/`exec`. |
| OFX | Limites de payload/campo, normalização controlada, erros de encoding/estrutura convertidos em falha segura. |
| Storage | Nenhum caminho, storage key, credencial ou `artifact_id` é retornado. O vínculo público usa o receipt autorizado. |
| Dados bancários | Agência e conta são mascaradas; valores mantêm `Decimal`; payload OFX não é renderizado. |
| XSS | Metadados, nomes, descrições, chaves e mensagens passam por escape antes de `innerHTML`; XML bruto não é exibido. |
| Erros e logs | Respostas não incluem traceback ou conteúdo bruto; logs/auditoria existentes não ganham payload documental. |
| Idempotência | Mesmo identificador e hash reutilizam efeito; conteúdo diferente conflita; deduplicação de domínio permanece autoridade. |

O `company_id` fornecido pelo frontend é sempre não confiável. Troca de contexto, logout e mudança de rota invalidam respostas assíncronas pendentes para impedir que uma projeção anterior reapareça no shell.

## Evidência de teste

Os testes sintéticos cobrem importação autorizada, negações cross-company e cross-tenant, IDOR de detalhe, parsing válido/inválido, XXE/DOCTYPE, limites, duplicidade, quarentena, sinais de transação, filtros e saída minimizada. Nenhum XML, OFX, empresa, conta ou identificador de cliente real é usado.

## Gaps preservados

- `MALWARE_SCANNING`: `INFRASTRUCTURE_GAP`;
- IdP de produção, exposição externa e dados reais: não habilitados;
- migration 0012: `PRE_DEPLOY_REQUIRED`, não executada;
- browser visual: gate manual quando não há browser no ambiente;
- permissão de importação: o contrato histórico usa `journal.propose`; criar uma capacidade especializada exige decisão e migration futura;
- conciliação persistente/manual: adiada, sem rota alternativa;
- rate limit distribuído e revogação de sessão: gates da fase de infraestrutura.
