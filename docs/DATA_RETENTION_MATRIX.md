# Matriz de retenção de dados — proposta sujeita a aprovação

**Estado:** nenhum prazo abaixo está aprovado ou automatizado. `A DEFINIR` não
autoriza exclusão. A matriz existe para registrar a decisão necessária antes do
piloto e deve ser versionada quando validada por jurídico/contabilidade.

| Categoria | Retenção proposta | Eliminação/expiração proposta | Backup | Legal hold | Aprovação necessária |
|---|---|---|---|---|---|
| Usuário, membership, papel e acesso | A DEFINIR por contrato, segurança e obrigações aplicáveis | desativar acesso primeiro; anonimizar/eliminar apenas se política permitir e sem dependência de auditoria | incluir em backup relacional; testar restauração | sim, se ligado a disputa/investigação | jurídica + segurança |
| Cadastro de empresa/estabelecimento | A DEFINIR conforme finalidade e dever contábil/fiscal | não apagar enquanto sustentar escopo, histórico ou obrigação | backup relacional | sim | jurídica + contábil |
| NF-e/XML bruto e evidência | A DEFINIR; não apagar automaticamente | somente após política, análise de linhagem, backup e aprovação; tombstone mínimo | backup de object storage é bloqueio atual | sim | jurídica + contábil |
| NF-e normalizada, itens e tributos | A DEFINIR; ligada à evidência e proposta | somente em conjunto coerente com evidência/linhagem e política | backup relacional | sim | jurídica + contábil |
| OFX bruto e evidência | A DEFINIR; dado financeiro de alta sensibilidade | somente após política, análise de conciliação/linhagem e aprovação | backup de object storage é bloqueio atual | sim | jurídica + contábil |
| OFX normalizado, contas e transações | A DEFINIR | somente após dependências, política e aprovação | backup relacional | sim | jurídica + contábil |
| Pré-lançamento, revisão, aprovação e linhagem | A DEFINIR; preservar enquanto for prova do processo | sem exclusão automática; correção por nova versão | backup relacional | sim | jurídica + contábil |
| Regras, plano, mapping e workflow | A DEFINIR; versões publicadas exigem rastreabilidade | arquivamento, não sobrescrita; eliminação somente se formalmente permitida | backup relacional | quando ligado a litígio/auditoria | jurídica + governança contábil |
| Exceção e mensagem de validação | A DEFINIR; revisar se mensagem contém dado excessivo | expirar apenas com política e sem quebrar investigação/linhagem | backup relacional | sim, quando vinculada | jurídica + segurança |
| `AuditEvent` | A DEFINIR; não é elegível a deleção automática | append-only; eventual arquivamento/eliminaçao depende de regra formal específica | backup relacional | sim | jurídica + auditoria/contábil |
| Logs técnicos | prazo curto A DEFINIR, minimizado | rotação no coletor aprovado; não registrar conteúdo bruto | backup somente se política aprovar | somente por determinação formal | jurídica + segurança/infra |
| Métricas agregadas | A DEFINIR; sem labels pessoais | expiração no coletor futuro, quando houver | conforme ferramenta aprovada | normalmente não, salvo investigação | segurança/infra |
| Dumps de banco | janela operacional aprovada; atualmente há orientação de sete backups, não política LGPD definitiva | remoção manual auditada após prazo/hold; cópias devem acompanhar | destino externo criptografado a aprovar | sim | jurídica + infraestrutura |

## Regras de execução

- O início da contagem, prazo, exceções e fundamento não podem ser inferidos pelo
  servidor nem pelo job.
- Antes de qualquer expiração, o job deve validar política publicada, escopo
  tenant/company, legal hold, dependências de origem/linhagem, cópia de backup e
  autorização humana. Falha em qualquer verificação bloqueia o descarte.
- Retenção em backup e em object storage deve ser rastreável por lote; a
  eliminação de produção não autoriza afirmar que cópias expiraram.
- Eventos de retenção devem conter somente IDs, versão de política, decisão,
  executor, correlação e hash quando necessário; nunca XML, OFX ou segredo.
- A aprovação futura deve registrar versão, data de vigência, aprovadores,
  exceções e plano de migração para dados já armazenados.
