# Registro técnico de fornecedores e potenciais suboperadores

| Categoria | Fornecedor atual comprovado | Dados/serviço | Localização/transferência | Estado |
|---|---|---|---|---|
| IdP de produção | TO_CONFIRM | identidade e autenticação | TO_CONFIRM | configuração suportada, contratação pendente |
| Hospedagem/API | TO_CONFIRM | dados operacionais | TO_CONFIRM | sem deploy externo autorizado |
| Banco gerenciado | TO_CONFIRM | dados relacionais | TO_CONFIRM | desenvolvimento local |
| Object storage | NONE_EXTERNAL | evidências NF-e/OFX | local no desenvolvimento | produção pendente |
| Backup externo | TO_CONFIRM | cópia de dados | TO_CONFIRM | estratégia, sem destino homologado |
| Logs/monitoramento | NONE_EXTERNAL | logs sanitizados/métricas | local/stdout | agregador futuro |
| E-mail/suporte | NONE_CONNECTED | potencial comunicação | TO_CONFIRM | não conectado |
| IA externa | NONE | nenhum fluxo | não aplicável | sem adaptador/provedor ativo |
| System A / Domínio / Connect Hub | NONE_ACTIVE | integrações futuras | TO_CONFIRM | deferred/blocked |

Antes de ativação: proprietário, contrato/DPA, finalidade, categorias, regiões, subcontratação, controles, retenção/exclusão, incidente, continuidade, saída e aprovação jurídica. Marcas citadas em documentação histórica não provam contratação vigente.

## Campos obrigatórios antes da contratação

Para cada linha `TO_CONFIRM`, registrar separadamente: serviço e fornecedor
legal; finalidade; categorias; ambiente; região/localização; potencial de
transferência internacional; DPA/contrato; revisão de segurança; suboperadores;
retenção/eliminação; incidente/continuidade; owner; e aprovação jurídica.

No estado atual, `DPA_CONTRACT_STATUS = TO_CONFIRM`,
`SECURITY_REVIEW = TO_CONFIRM` e `LEGAL_REVIEW = REQUIRED` para todo provedor de
produção. Não se presume geografia a partir de marca ou documentação técnica.
