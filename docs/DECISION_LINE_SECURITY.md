# Segurança da Linha da Decisão

## Autorização e isolamento

A leitura exige duas decisões positivas:

1. permissão do recurso (`company.read` para documento/NF-e/extrato; `journal.read` para proposta/revisão) e `CompanyAccess` vigente;
2. `audit.read` no mesmo tenant e empresa.

O recurso é resolvido por `tenant_id + company_id + id`. Consultas de correlação, auditoria, atores e locks repetem o escopo. Um ID nunca autoriza acesso. Ausente e fora do escopo não revelam dados; falta de permissão resulta em negação antes da projeção.

## Minimização e conteúdo não confiável

O DTO não expõe `tenant_id`, `actor_id`, e-mail, claims OIDC, correlação, causação, `before/after`, reason bruto, hash, chave de acesso, conteúdo XML/OFX ou storage. Textos semânticos vêm de mapa controlado. Nome de exibição é o único dado do ator e apenas para ação profissional; a UI o codifica com `escapeHtml`, assim como todos os demais campos.

Evento com integridade inválida é substituído por aviso genérico e seu conteúdo não é projetado. Ações desconhecidas usam fallback controlado, sem repetir nomes técnicos ou payload.

## Consultas e abuso

O limite HTTP é `1..100`; a descoberta aceita no máximo oito correlações. Atores são consultados em lote e não há varredura tenant-wide nem N+1 por evento. Os índices atuais por tenant/sujeito e tenant/correlação sustentam a descoberta. O índice composto ideal com empresa está registrado como gap pré-deploy, sem migration nesta fase.

Não há método POST/PUT/PATCH/DELETE da Linha da Decisão. A projeção não emite auditoria decorativa e não duplica decisão em retry idempotente.

## Semântica de autoridade

`APPROVAL` significa decisão interna humana sobre revisão/hash exatos. Não significa lançamento, exportação, escrituração ou confirmação pelo sistema contábil externo. Bloqueio derivado significa estado vigente; tentativa frustrada só poderia ser mostrada se auditada, o que não é inferido.
