# Insumo técnico para registro das operações de tratamento (ROPA)

**Não é um ROPA aprovado.** Controlador/operador, bases, prazos, destinatários e transferências requerem validação jurídica.

| Operação | Titulares/categorias possíveis | Finalidade e sistemas | Compartilhamento | Salvaguardas | Pendências |
|---|---|---|---|---|---|
| identidade e acesso | usuários; identidade, vínculo e eventos | autenticar/autorizar; IdP/API/banco | IdP a selecionar | PKCE/JWT, RBAC, CompanyAccess, auditoria | papel, base, prazo, fornecedor |
| documentos fiscais | pessoas em NF-e; XML e derivados | evidência, normalização e proposta | nenhum externo atual | tenant/company, hash, storage imutável | prazo, base, storage/backup |
| dados bancários | titulares em OFX; conta/transações | importar e conciliar | nenhum externo atual | escopo, linhagem, permissões | prazo, base e minimização final |
| processo contábil | usuários/representantes; propostas e decisões | revisão assistida | nenhum externo atual | regra determinística, aprovação humana | responsabilidade e prazo |
| segurança/auditoria | usuários; identificadores e ações | integridade, investigação e recuperação | fornecedores futuros | append-oriented, sanitização, acesso mínimo | base, prazo e coletores |
| DSR/retenção | solicitante; hash e referências | localizar, relatar e controlar retenção | operação interna | identidade, permissões, hold, auditoria | canal, alçada, SLA jurídico |

Anexos técnicos: `DATA_INVENTORY.md`, `DATA_FLOW_MAP.md`, `PRIVACY_ROLE_MATRIX.md`, `LAWFUL_BASIS_REVIEW_MATRIX.md` e `SUBPROCESSOR_TECHNICAL_REGISTER.md`.

Para converter este insumo em registro formal, cada atividade deve receber
owner nominal, papel jurídico aprovado, base, destinatários efetivos, período e
gatilho de retenção, localização dos fornecedores, medidas contratuais e data de
revisão. Enquanto esses campos não forem aprovados, o status de todas as linhas
é `LEGAL_REVIEW_REQUIRED`; os owners indicados são somente áreas técnicas ou de
negócio, não pessoas formalmente designadas.
