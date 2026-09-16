# Inventário técnico de dados

**Status:** `TECHNICAL_INPUT_ONLY` — classificação jurídica, base legal e prazo exigem revisão humana.

| Categoria / exemplos | Origem e finalidade técnica | Local / acesso | Classe técnica | Retenção / DSR |
|---|---|---|---|---|
| Identidade: nome, e-mail, identificador do IdP, membership, papéis | IdP/onboarding; autenticação e autorização | banco relacional; identity/access control | CONFIDENTIAL | `A DEFINIR`; descoberta automatizada de usuário |
| Empresa: razão social, identificadores fiscais, estabelecimentos | escritório; escopo operacional | banco relacional tenant/company-aware | CONFIDENTIAL | `A DEFINIR`; avaliar caso concreto |
| NF-e/XML, emitente, destinatário, itens, tributos | upload autorizado; evidência e normalização | object storage + banco | RESTRICTED | `A DEFINIR`; fonte documental manual no DSR |
| OFX, conta, FITID, descrição e valores | upload autorizado; importação e conciliação | object storage + banco | RESTRICTED | `A DEFINIR`; fonte documental manual no DSR |
| Dados contábeis derivados, propostas e aprovações | regras e ação humana; workflow | banco relacional | RESTRICTED | `A DEFINIR`; preservar linhagem e versões |
| Configuração: plano, DE/PARA, regras, workflow | cadastro autorizado; processamento reproduzível | banco relacional versionado | CONFIDENTIAL | `A DEFINIR`; não sobrescrever versão publicada |
| Auditoria: ator, ação, recurso, correlação, hashes | aplicação; prova do processo | banco append-oriented | RESTRICTED | tratamento especial; nunca eliminação automática |
| Privacidade: hash do identificador, estado DSR, holds, decisões | operação interna; direitos e retenção | banco relacional após migration 0012 | RESTRICTED | política pendente; hold prevalece |
| Logs sanitizados e métricas agregadas | aplicação; diagnóstico e segurança | stdout/coletor futuro | INTERNAL | `A DEFINIR`; sem payload bruto ou labels pessoais |
| Backups | infraestrutura; recuperação | destino externo ainda a homologar | RESTRICTED | `A DEFINIR`; expiração e reconciliação pendentes |
| Preferências visuais do navegador | usuário; layout | `localStorage` | INTERNAL | removível no navegador; não é cookie |

Não há analytics, publicidade comportamental ou cookies implementados. O token do cliente web fica em memória; estado transitório OIDC PKCE usa `sessionStorage`. O formulário público é somente simulação local e não envia nem persiste os campos.

Dados de menores não são um caso de uso alvo (`NOT_A_TARGET_USE_CASE`), sem mecanismo técnico para inferir idade. Dados pessoais podem aparecer em documentos fiscais/financeiros; portanto, minimização, acesso por escopo e revisão humana continuam obrigatórios.

## Limites

- Busca DSR cobre `USERS`; `DOCUMENT_STORAGE` é `MANUAL_SOURCE` e o relatório é apenas em memória.
- A migration 0012 continua `PRE_DEPLOY_REQUIRED`; não foi executada.
- Não há eliminação ou anonimização material. `dry_run=False` é negado.
- O inventário deve ser revalidado quando fornecedor, integração ou nova categoria entrar em operação.

## Responsabilidade, acesso e relevância DSR

| Categoria | Responsável técnico pela retenção | Perfil de acesso | Relevância para DSR/exportação |
|---|---|---|---|
| identidade e perfil | Identity + Privacy | operador com permissão e CompanyAccess | descoberta USERS automatizada; resposta revisada |
| empresa e identificadores fiscais | Tenancy/Companies | usuário autorizado da empresa | avaliação contextual/manual |
| NF-e/OFX e documentos | Documents/Fiscal/Banking | perfis operacionais por empresa | fonte manual; nunca exportação ampla automática |
| propostas, lançamentos e configuração | Accounting/Rules/Workflow | perfis contábeis segregados | avaliação manual com preservação de linhagem |
| auditoria e segurança | Audit/Security | permissão específica; projeção mínima | tratamento especial; não apagar automaticamente |
| DSR, Legal Hold e retenção | Privacy | operador de privacidade autorizado | registro do próprio processo, conteúdo minimizado |
| logs, métricas e backups | Operations/Infrastructure | acesso operacional restrito | busca manual quando aplicável; retenção coordenada |

As classes `PUBLIC`, `INTERNAL`, `CONFIDENTIAL` e `RESTRICTED` são classificações
de engenharia: respectivamente conteúdo publicável aprovado; operação interna;
dado de negócio com acesso limitado; e dado cujo vazamento ou alteração produz
alto impacto. Elas não afirmam classificação jurídica de dado pessoal ou
sensível, que permanece `LEGAL_REVIEW_REQUIRED`.
