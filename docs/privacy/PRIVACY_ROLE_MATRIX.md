# Matriz técnica de papéis de privacidade

Nenhuma linha abaixo define juridicamente controlador, operador, suboperador ou encarregado. Todas as qualificações são `LEGAL_REVIEW_REQUIRED`.

| Parte | Fato técnico | Papel proposto para análise | Status |
|---|---|---|---|
| Escritório contábil (tenant) | decide usuários, empresas, documentos e operações do seu ambiente | controlador ou outra qualificação conforme contexto | LEGAL_REVIEW_REQUIRED |
| Cliente final do escritório | origina parte dos documentos/dados e pode ter autonomia própria | controlador conjunto/independente ou titular empresarial, conforme caso | LEGAL_REVIEW_REQUIRED |
| Serdial21 | fornece e opera a plataforma, controles e trilhas | operador e/ou controlador para finalidades próprias | LEGAL_REVIEW_REQUIRED |
| Usuário/titular | acessa a plataforma ou consta em documentos | titular/representante conforme contexto | LEGAL_REVIEW_REQUIRED |
| IdP de produção | autenticação e identidade federada | suboperador/fornecedor | PROVIDER_TO_CONFIRM + LEGAL_REVIEW_REQUIRED |
| Hospedagem, banco, storage, backup e monitoramento | infraestrutura quando contratada | suboperadores/fornecedores | PROVIDERS_TO_CONFIRM + LEGAL_REVIEW_REQUIRED |
| Provedor de IA | nenhum adaptador externo ativo | não aplicável ao fluxo atual | NONE; reavaliar antes de ativar |
| System A / Domínio / Connect Hub | integrações não ativas | futuro | DEFERRED/BLOCKED + LEGAL_REVIEW_REQUIRED |

O encarregado, canais, alçadas, instruções documentadas, subcontratação, cooperação em DSR/incidentes e responsabilidade contratual permanecem pendentes de nomeação e aprovação humana.
