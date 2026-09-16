# Matriz para revisão de bases legais

**Regra:** esta matriz não escolhe base legal. `LEGITIMATE_INTEREST`, consentimento, obrigação legal, contrato e demais hipóteses são alternativas para análise jurídica, nunca conclusões técnicas.

| Tratamento/finalidade técnica | Categorias | Necessidade/minimização técnica | Base legal | Evidência humana pendente |
|---|---|---|---|---|
| Autenticar e autorizar | identidade, membership, logs de segurança | necessária ao acesso; claims mínimos | LEGAL_REVIEW_REQUIRED | contrato, relação com usuário e aviso |
| Cadastrar empresa | dados empresariais/fiscais | necessária ao isolamento e operação | LEGAL_REVIEW_REQUIRED | contexto escritório–cliente |
| Processar NF-e/OFX | documentos fiscais/financeiros e derivados | conteúdo limitado ao caso de uso | LEGAL_REVIEW_REQUIRED | instrução, obrigação aplicável e contrato |
| Gerar propostas/workflow | dados contábeis e decisões humanas | linhagem e versão mínimas | LEGAL_REVIEW_REQUIRED | finalidade e responsabilidades |
| Auditar e proteger | IDs, ações, hashes, eventos | sem payload bruto; acesso restrito | LEGAL_REVIEW_REQUIRED | necessidade, prazo e proporcionalidade |
| Backup e recuperação | cópias das categorias operacionais | acesso mínimo e expiração coordenada | LEGAL_REVIEW_REQUIRED | prazo, localização e fornecedores |
| Atender DSR | hash de identificador, referências e relatório | relatório mínimo; identidade antes da busca | LEGAL_REVIEW_REQUIRED | canal, prova de identidade e resposta |
| Comunicar produto/marketing | formulário atual não envia dados | tratamento inexistente hoje | NOT_APPLICABLE_CURRENTLY | definir antes de ativar coleta |
| IA externa | fluxo inexistente | nenhum envio atual | NOT_APPLICABLE_CURRENTLY | nova análise antes de adaptador externo |

Consentimento não deve ser usado como padrão técnico. Se futuramente selecionado pelo jurídico, serão necessários registro de versão, finalidade granular, retirada tão simples quanto concessão, prova e propagação da revogação.

## Responsáveis e estado do gate

| Grupo de tratamento | Opções para avaliação jurídica | Motivo da revisão | Legal owner | Status |
|---|---|---|---|---|
| identidade e contrato de serviço | contrato, obrigação aplicável, legítimo interesse ou outra hipótese válida | relações entre plataforma, escritório e usuário não estão qualificadas | Jurídico/Privacidade | LEGAL_REVIEW_REQUIRED |
| fiscal, financeiro e contábil | obrigação aplicável, execução contratual ou instrução documentada | depende do papel das partes e do caso concreto | Jurídico + responsável contábil | LEGAL_REVIEW_REQUIRED |
| auditoria, segurança e backup | obrigação, legítimo interesse ou exercício de direitos | proporcionalidade e prazo precisam ser aprovados | Jurídico/Security | LEGAL_REVIEW_REQUIRED |
| DSR e incidente | cumprimento de obrigação ou outra hipótese aplicável | identidade, canal, registro e comunicações dependem de procedimento | Encarregado/Jurídico | LEGAL_REVIEW_REQUIRED |

Nenhuma opção acima está escolhida ou aprovada pelo software.
