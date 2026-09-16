# Política técnica de retenção

**Status:** mecanismos técnicos presentes; períodos e fundamentos `PENDING_HUMAN_APPROVAL`. `A DEFINIR` nunca autoriza descarte.

| Categoria | Início/prazo/destino | Controle atual |
|---|---|---|
| identidade e acesso | A DEFINIR | avaliação por política versionada; acesso pode ser desativado |
| cadastros empresariais | A DEFINIR | manter escopo e histórico |
| NF-e/OFX bruto e normalizado | A DEFINIR | dependência de evidência/linhagem; storage manual no DSR |
| propostas, regras e versões | A DEFINIR | versão publicada imutável; correção por nova versão |
| auditoria | A DEFINIR | nunca candidata a destruição automática |
| logs e métricas | A DEFINIR | minimização; expiração depende do coletor futuro |
| backups | A DEFINIR | destino/expiração/hold/reconciliação ainda não homologados |

## Enforcement

- `RetentionPolicy` exige categoria, gatilho, período e aprovação persistida.
- Sem política aprovada: `PENDING_POLICY_APPROVAL`.
- `LegalHold` ativo prevalece e gera `LEGAL_HOLD`.
- `RetentionRunner` opera apenas em dry-run; execução destrutiva falha fechada.
- Toda avaliação, criação/liberação de hold e transição DSR é auditada.
- Escopo tenant/company é revalidado; ID não autoriza acesso.
- Eliminação, anonimização, expiração de object storage e backup não estão implementadas.

Antes de ativar descarte: aprovação jurídica/contábil, migration 0012 validada, política publicada, segregação de alçada, dependências de linhagem, backup/restore, propagação a cópias, tombstone mínimo, idempotência e testes de recuperação. A restauração precisa reaplicar/reconciliar holds e ações de privacidade posteriores ao ponto restaurado; este mecanismo ainda é uma lacuna bloqueante para eliminação material.

## Matriz de enforcement e revisão

| Tipo de dado | Regra atual | Enforcement técnico | Legal Hold | Backup | Status | Revisão legal |
|---|---|---|---|---|---|---|
| identidade/empresa | prazo não aprovado | política ausente falha fechada | prevalece | incluído no dump | PARTIAL | REQUIRED |
| documento NF-e/OFX | prazo não aprovado | evidência imutável; sem destruição | prevalece | object storage não homologado | PARTIAL | REQUIRED |
| contábil/configuração | versão e linhagem preservadas | published imutável | prevalece quando aplicável | banco | READY_SAFE | REQUIRED para prazo |
| auditoria | tratamento especial | nunca candidato automático | preservado | banco | READY_SAFE | REQUIRED para prazo |
| privacidade/DSR | prazo não aprovado | transições e auditoria | prevalece | banco após 0012 | PARTIAL | REQUIRED |
| logs/métricas | coletor não selecionado | sanitização/schema fechado | procedimento manual | fornecedor futuro | PARTIAL | REQUIRED |
| backup | expiração não aprovada | sem expurgo automatizado | deve suspender expiração | próprio ativo | DOCUMENTED_GAP | REQUIRED |
