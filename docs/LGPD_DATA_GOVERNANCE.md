# Governança de dados e privacidade — MVP piloto

## Status e limites

Este documento é um inventário técnico e uma proposta de controles. Não define
base legal, prazo legal definitivo, controlador/operador, DPO/encarregado,
transferência internacional nem obrigações de comunicação. Esses pontos exigem
validação jurídica e a aprovação formal do escritório e do responsável pelo
produto antes de qualquer ingestão de dado real.

O sistema não deve apagar automaticamente dado fiscal, bancário, evidência ou
`AuditEvent`. Há política técnica, decisão, dry-run, legal hold e workflow DSR
sem entrega; exclusão, anonimização, busca/exportação DSR e expiração de backup
continuam indisponíveis e fail-closed. Veja `PRIVACY_TECHNICAL_CONTROLS.md`.

## Inventário técnico

| Categoria | Finalidade operacional | Origem | Armazenamento e acesso atual |
|---|---|---|---|
| Usuário e identidade | autenticar, vincular membership, aplicar papel e revogar acesso | IdP e onboarding autorizado | banco relacional; acesso pelo serviço de identidade e `identity.manage` quando aplicável |
| Dados cadastrais de empresa | delimitar escopo, empresa e dados fiscais da organização | escritório/onboarding | banco relacional tenant/company-aware; CompanyAccess e permissões |
| NF-e/XML e evidência | preservar prova de recebimento, reprocessar e gerar canônico | upload autorizado | bytes no object storage; hash/metadados, recebimento e linhagem no banco |
| Dados NF-e normalizados | regras, proposta e rastreabilidade | parser de XML | banco relacional: chave, emitente/destinatário, itens, tributos e totais; escopo tenant/company |
| OFX e extrato bancário | importação, conciliação e investigação de exceção | upload autorizado | bytes no object storage e derivados no banco: conta, saldos, FITID, referência, descrição e valor |
| Pré-lançamentos e propostas | revisão/decisão interna, sem escrituração oficial | regra determinística e decisão humana | checkpoints e estruturas de workflow no banco, vinculados a fontes/versionamento |
| Regras, plano, DE/PARA e workflow | reproduzir proposta e governar versões aprovadas | cadastro revisado pelo escritório | catálogo relacional versionado; leitura/escrita por permissões específicas |
| Exceções e linhagem | explicar falha/processamento e origem dos resultados | parsers e serviços | banco relacional; mensagens de validação podem conter contexto de negócio e exigem classificação |
| `AuditEvent` | provar ação e responsabilidade do processo | casos de uso e borda autenticada | banco relacional append-only com hash de integridade; leitura requer `audit.read` |
| Logs técnicos e métricas | diagnóstico técnico e segurança | aplicação/infraestrutura | stdout/coletor futuro; logs sanitizados e métricas agregadas locais |
| Backups | recuperação do banco e, no futuro, de evidências | operação de infraestrutura | dump protegido fora do Git; backup de object storage ainda não está comprovado |

Identificadores fiscais, nomes, e-mails, descrições de itens/transações e
números de conta podem ser dados pessoais ou dados empresariais sensíveis no
contexto concreto. A classificação final e o mapeamento de titulares exigem
validação jurídica.

## Controles técnicos existentes

- isolamento obrigatório por `tenant_id` e, para dado empresarial, `company_id`;
  `CompanyAccess`, papel e permissão são revalidados;
- IDs não autorizam acesso; negação cross-tenant é uniforme;
- evidência usa chave relativa protegida contra traversal, hash SHA-256 e escrita
  imutável `put_if_absent`;
- `AuditEvent` e evidências possuem proteção append-only/imutável;
- logs estruturados removem campos de segredo, token, XML, prompt e banco;
  erros registram classe sanitizada, não mensagem/corpo;
- a auditoria recusa estados com segredo, XML bruto ou campos proibidos e limita
  estados a 16 KiB;
- a API operacional expõe auditoria resumida, sem estados antes/depois.

Limitações relevantes: armazenamento local não prova criptografia em repouso,
logs não possuem coletor/retenção central, backups de evidência não estão
homologados e a classificação aplicada a `EvidenceArtifact.classification` não
é uma política LGPD executável.

## Mecanismos obrigatórios antes de dados reais

1. Criar política versionada por tenant e categoria: finalidade aprovada,
   retenção, gatilho de início, destino de backup, elegibilidade de eliminação
   e aprovador. Não aceitar prazo livre em endpoint.
2. Criar `LegalHold` append-only, escopado por tenant/company e sujeito (ou
   conjunto documentado), com motivo, origem autorizada, início, revisão e
   liberação. Somente papel específico, com dupla revisão definida pela política,
   pode criar/liberar hold; toda ação gera `AuditEvent`.
3. Criar job de retenção somente em modo *dry-run* inicialmente. Ele deve
   produzir lista tenant-aware de candidatos, verificar hold, dependências de
   linhagem, backup recuperável e aprovação humana. A execução material requer
   política publicada e evento de auditoria por lote/item.
4. Para eliminação permitida, separar: exclusão criptográfica/objeto, exclusão
   lógica de índice, tombstone mínimo e expiração de cópias. Nunca alterar
   `AuditEvent` nem reescrever histórico; registrar o evento de descarte com
   hash/identificador mínimo, sem copiar conteúdo eliminado.
5. Implementar retenção e expiração no destino de backup e object storage; um
   backup retido não torna possível declarar eliminação concluída. Legal hold
   deve suspender expiração tanto da produção quanto das cópias.
6. Exigir autorização, escopo e motivo para consulta/exportação de dados de
   privacidade; limitar resultado à categoria e empresa autorizadas.

O modelo físico, migrations, job e testes desses itens são trabalho posterior;
esta execução não os implementa para não criar regra de descarte sem aprovação.

## Atendimento ao titular (DSR)

Até o workflow existir, receber solicitação por canal controlado do escritório e
abrir ticket com ID opaco. Não anexar XML, OFX, token, dump ou dados completos ao
ticket. O operador deve: verificar identidade e poderes do solicitante por
processo aprovado; registrar tenant/empresa e escopo solicitado; encaminhar ao
responsável de privacidade; e manter prazo e decisão sob definição jurídica.

Após implementação, o serviço DSR deverá fazer descoberta somente por escopo
autorizado, gerar relatório mínimo de categorias/localização/estado de retenção,
e registrar cada acesso. Solicitações de correção devem criar versão ou
complemento, jamais alterar evidência ou auditoria. Solicitações de eliminação
devem consultar política, dependências, legal hold e cópias antes de propor a
execução; o resultado pode ser negação fundamentada, restrição ou eliminação
quando formalmente permitida. Não há endpoint DSR no MVP atual.

## Decisões humanas pendentes

- papéis de controlador, operador, suboperadores e encarregado;
- bases legais e hipóteses de tratamento por categoria/finalidade;
- prazos de retenção, gatilhos, descarte e suspensão; inclusive obrigação fiscal,
  contábil, trabalhista, contratual e defesa de direitos;
- escopo de dados de titulares, canal de DSR, prova de identidade, SLA e modelo
  de resposta;
- países/fornecedores de storage, criptografia, gestão de chaves e backups;
- autoridade e critérios para criar/liberar legal hold e para aprovar eliminação.

Consulte a matriz operacional em `DATA_RETENTION_MATRIX.md` e o processo de
incidente em `PRIVACY_INCIDENT_PROCESS.md`.
