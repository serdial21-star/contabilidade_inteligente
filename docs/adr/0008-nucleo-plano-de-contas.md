# ADR 0008 — Núcleo do plano de contas

## Decisão

`Account` é somente uma identidade estável no plano. Código, nome, natureza,
saldo normal, pai, capacidade de lançamento, status e vigência pertencem a
`AccountVersion`. A versão publicada é congelada; correções usam uma nova
versão em rascunho.

O domínio rejeita ciclos, referências de pai fora do tenant/empresa, contas
sintéticas lançáveis, vigência inválida e o mesmo código publicado em vigências
sobrepostas no mesmo tenant/empresa. Não há criação automática de conta por IA.
