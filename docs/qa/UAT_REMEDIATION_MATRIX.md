# Phase 14 — Matriz de remediação do Human UAT

Esta matriz registra a análise dos 20 achados sem alterar os gates da Phase 14.

| ID | Comportamento atual / causa raiz | Comportamento esperado | Severidade | Agora | Schema | Teste |
|---|---|---|---|---|---|---|
| H01 | bootstrap sintético descartava o hash | preservar rota suportada/autorizada | DEFECT_P1 | sim | não | frontend |
| H02 | expiração sem contexto | ajuda curta e acessível | UX_P2 | sim | não | UI |
| H03 | um XML por interação | múltiplos isolados e pasta progressiva; ZIP seguro | ENHANCEMENT | parcial | não | frontend/API |
| H04 | data contábil manual obrigatória | derivar `issued_at`, override opcional | DEFECT_P1 | sim | não | API |
| H05 | alerta NF-e sobrevivia ao filtro | limpar alerta transitório | DEFECT_P1 | sim | não | frontend |
| H06 | alerta global | feedback por módulo | DEFECT_P1 | sim | não | frontend |
| H07 | revisão OFX pouco explícita | extrato/saldos/transações paginados | DEFECT_P1 | sim | não | API/UI |
| H08 | histórico contábil não era carregado | detalhe profissional e histórico | DEFECT_P1 | sim | não | API/UI |
| H09 | somente status | status e intervalo de registro server-side | DEFECT_P1 | sim | não | API/UI |
| H10 | intake genérico não guarda os campos pedidos | expor apenas dados persistidos | DOMAIN_GAP | não | sim | inspeção |
| H11 | inbox básico | reutilizar metadados seguros disponíveis | UX_P2 | sim | não | frontend |
| H12 | inbox sem controles | filtros server-side e reset | DEFECT_P1 | sim | não | frontend |
| H13 | cronologia vertical | horizontal largo, vertical estreito | UX_P2 | sim | não | CSS |
| H14 | espaçamento excessivo | maior densidade acessível | UX_P2 | sim | não | CSS |
| H15 | resets inconsistentes | limpar todos os grupos complexos | DEFECT_P1 | sim | não | frontend |
| H16 | grade 3/2/1 | grade 4/3/2/1 flexível | UX_P2 | sim | não | CSS |
| H17 | affordance sem destino | W004 abre inbox; W008/W009 desabilitados | DEFECT_P1 | sim | não | frontend |
| H18 | company da rota era suficiente | validar CNPJ autoritativo e direção | DEFECT_P0 | sim | não | API |
| H19 | OFX criava conta implicitamente | exigir conta do mesmo tenant/company | DEFECT_P0 | sim | não | unit/API |
| H20 | Company mínimo; Supplier ausente | documentar e planejar incremento | DOMAIN_GAP | backlog | sim | inspeção |

## Decisões

- ZIP: `FOLLOW_UP_ENHANCEMENT`, pois requer limites de entradas e bytes,
  proteção contra traversal e zip bomb.
- W004: `FIXED` (Caixa de entrada). W008 e W009: `SUMMARY_ONLY`.
- Company: nome legal/fantasia, CNPJ, timezone e moeda `READY`; IE/IM, endereço e
  contatos `MISSING`; contas bancárias `PARTIAL` (persistência sem manutenção UI).
- Supplier master: `NEW_DOMAIN_REQUIRED`.

