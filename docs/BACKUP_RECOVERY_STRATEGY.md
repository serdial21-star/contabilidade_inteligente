# Estratégia de backup e recuperação

## Inventário e objetivos

| Ativo | Proteção requerida | Recuperação |
|---|---|---|
| Banco MySQL/MariaDB | dump lógico consistente e backup gerenciado quando disponível | restore isolado + validação |
| Object storage documental | cópia versionada/imutável e inventário de hashes | restaurar objetos e reconciliar metadados |
| Configuração/segredos | provedor segregado, nunca dump/Git | reprovisionar por referência controlada |
| Código/migrations | release imutável e repositório | checkout do release compatível |
| Configuração de integração | backup cifrado e acesso mínimo quando existir | reconfiguração validada |

Git não é backup do banco. O alvo recomendado para o piloto é RPO de 24 horas
(backup lógico diário) e RTO de 4 horas incluindo detecção, decisão, obtenção do
artefato, restore, validação e reabertura. São objetivos técnicos, não SLA; não
estão provados em produção. O drill local comprova a orquestração, e a evidência
MariaDB histórica de 08/09/2026 não substitui novo ensaio no ambiente final.

## Política do artefato

- `mysqldump --single-transaction` para backup lógico do banco suportado;
- pelo menos sete cópias diárias e pontos semanais/mensais a definir com a
  política LGPD; legal hold prevalece sobre expurgo automático;
- criptografia em trânsito e em repouso com chave fora do host/artefato;
- cópia separada do host da aplicação, idealmente conta/failure domain distinto;
- acesso mínimo, registro de acesso e segregação entre execução e aprovação;
- `.backups/`, `*.sql` operacionais e metadados sensíveis nunca versionados.

Cada execução registra UTC, classe do banco, tamanho, SHA-256, exit status,
duração, versão da aplicação, migration head e ferramenta, sem URL, usuário ou
senha. Sucesso exige arquivo existente/não vazio, checksum, formato plausível e
metadado; recuperação só é comprovada por restore validado.

## Tooling

`scripts/backup_database.py` exige `--expected-database`, lê `DATABASE_URL` da
configuração aprovada, confirma `SELECT DATABASE()` e `alembic_version`, não
inclui senha na linha de comando, escreve primeiro `.partial` e recusa
sobrescrever. Exemplo, somente em ambiente autorizado:

```powershell
python scripts/backup_database.py --expected-database <db_exata> --output .backups/backup-<UTC>.sql
```

`scripts/local_recovery_drill.py` aceita somente caminhos explícitos e destinos
inexistentes para SQLite sintético. Ele valida SHA-256 antes do restore e
`PRAGMA integrity_check` depois. É validação de orquestração, não de MariaDB.

Falhas retornam status não zero, mensagem sanitizada e devem alimentar o alerta
BACKUP/RECOVERY CRITICAL no scheduler futuro. Artefato parcial é removido; o
último backup válido permanece intocado. Nenhum script executa migration 0012.

O procedimento MariaDB detalhado e os guards adicionais permanecem em
[BACKUP_RESTORE_RUNBOOK.md](BACKUP_RESTORE_RUNBOOK.md). Object storage ainda
precisa de backend/infra para snapshot e restore; isso é bloqueador antes de
dados reais.

## Privacidade, retenção e acesso ao backup

- acesso ao destino deve ser restrito, segregado e auditável;
- transporte e armazenamento cifrados são requisitos de produção, ainda
  dependentes de fornecedor e gestão de chaves comprovados;
- expiração deve seguir política aprovada e ser suspensa por Legal Hold
  aplicável; os períodos permanecem `LEGAL_REVIEW_REQUIRED`;
- não se faz mutação cirúrgica de backup histórico somente para atender uma
  ação sobre o dado ativo;
- a restauração nunca conclui uma ação de privacidade por si só: antes do
  cutover, devem ser reconciliados holds, decisões de retenção, tombstones e
  ações DSR posteriores ao ponto restaurado.

Não existe hoje um ledger externo durável capaz de reaplicar automaticamente
essas ações após um restore. Portanto,
`PRIVACY_RESTORE_RECONCILIATION_GAP = DOCUMENTED_GAP`; eliminação material
permanece desabilitada e dados reais continuam `NO_GO`.
