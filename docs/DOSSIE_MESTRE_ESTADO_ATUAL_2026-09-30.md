# Dossiê mestre — Serdial21 Contabilidade Inteligente

**Data de corte:** 30/09/2026  
**Fuso de referência:** America/Sao_Paulo  
**Repositório:** `Sistema-Contabilidade-Inteligente`  
**Branch observada:** `main`  
**Commit publicado no GitHub no momento do levantamento:** `d18f62a` (`docs: record System A client workflow cutover`)  
**Natureza do documento:** consolidação técnica, funcional, operacional, de segurança e de governança para continuidade do projeto.

---

## 1. Finalidade e forma correta de leitura

Este dossiê registra o estado conhecido do projeto Serdial21 até a data de corte. Ele foi escrito para permitir que uma nova sessão de trabalho retome o projeto sem depender da memória da conversa que originou as alterações.

O documento abrange:

- a visão do produto e seus limites de autoridade;
- a separação entre o portal legado, a nova plataforma contábil e os sistemas externos;
- as decisões aprovadas e os limites das autorizações concedidas;
- o estado do código, banco, migrations, frontend, infraestrutura e integrações;
- o pacote de segurança de administradores e clientes no Sistema A;
- a implantação interna e o piloto controlado do Sistema B;
- os workflows n8n publicados, substituídos, despublicados e preservados em backup;
- as evidências de testes e validações realizadas;
- incidentes, riscos residuais, lacunas e pendências;
- a sequência recomendada para a próxima etapa.

### 1.1 Hierarquia de autoridade documental

Em caso de conflito, use a seguinte ordem:

1. `AGENTS.md`, especialmente as regras de segurança, isolamento, auditoria e governança;
2. ADRs aprovados, porque registram decisões formais e seus limites;
3. este dossiê para o retrato operacional consolidado em 30/09/2026;
4. checkpoints e runbooks mais recentes relacionados ao assunto;
5. guias, relatórios e dossiês anteriores, tratados como evidência histórica.

Este documento não revoga ADRs e não amplia autorizações anteriores. Ele esclarece o estado atual quando documentos antigos ficaram desatualizados por implantações e aprovações posteriores.

### 1.2 Proteção de informações sensíveis

Embora o objetivo seja preservar todo o contexto relevante, este dossiê deliberadamente não reproduz:

- senhas, tokens, cookies, chaves ou segredos;
- valores de credenciais de banco, SMTP, Drive, Redis ou assinatura;
- dados pessoais desnecessários;
- identificadores internos de pessoas, sessões e empresas que não sejam necessários para compreender a arquitetura;
- conteúdo bruto de documentos de clientes;
- hashes de arquivos reais quando a simples referência à evidência é suficiente.

Os segredos continuam sob gestão operacional apropriada. Capturas ou registros antigos que possam conter tokens não devem ser copiados para novos documentos.

---

## 2. Resumo executivo

O Serdial21 é uma plataforma contábil inteligente, multi-tenant e orientada a escritórios contábeis. O projeto está dividido, na prática, em dois sistemas complementares:

- **Sistema A:** portal administrativo e portal de clientes já existente, construído com frontend React/Vite/Lovable, workflows n8n e banco MySQL/MariaDB hospedado. Nesta etapa, recebeu endurecimento do cadastro, edição, listagem e recuperação de senha de clientes e administradores.
- **Sistema B:** nova aplicação de inteligência contábil deste repositório, implementada como monólito modular em Python/FastAPI/SQLAlchemy, preparada para múltiplos tenants, empresas, documentos, regras, propostas, revisão humana, auditoria e integrações futuras.

O Sistema B já foi publicado para uso interno em:

- aplicação: `https://contabilidade.serdial21.com/app/`;
- prontidão da API: `https://contabilidade.serdial21.com/api/v1/health/ready`.

A ponte de login entre A e B foi validada em navegação real. Uma empresa real autorizada foi importada do Sistema A para o Sistema B por processo manual, mínimo, idempotente e auditável. Isso não significa que exista sincronização contínua de dados entre os sistemas.

No Sistema A, os novos fluxos seguros de clientes foram publicados e os fluxos antigos que disputavam os mesmos webhooks foram despublicados. O teste funcional de edição confirmou a persistência de CNPJ alfanumérico e mudança de status para `Lead`, com auditoria e revogação de sessões. Os backups posteriores foram confirmados.

O repositório está em `main`, sincronizado com o remoto no commit `d18f62a` antes da criação deste dossiê. A suíte local atual apresentou:

- **565 testes aprovados**;
- **20 testes ignorados** por dependerem de MariaDB real, homologação ou operações de restauração habilitadas explicitamente;
- **2 avisos de depreciação**;
- **51,03 segundos** de execução.

O head Alembic atual é `20260923_0016`.

O projeto não está pronto para declarar integração contábil externa completa, sincronização geral A→B, lançamento comercial amplo ou escrituração oficial. O sistema contábil externo continua sendo a autoridade dos números e registros oficiais.

---

## 3. Identidade, missão e limites do produto

### 3.1 Missão

O Serdial21 deve organizar e tornar auditável o processo contábil do escritório, reduzindo trabalho repetitivo sem retirar do profissional a responsabilidade e a decisão final.

### 3.2 Autoridades do domínio

O sistema contábil externo — atualmente o Domínio no contexto do escritório — permanece autoridade para:

- escrituração oficial;
- saldos oficiais;
- fechamentos;
- números contábeis definitivos;
- obrigações e efeitos que dependam do sistema oficial.

O Serdial21 é autoridade sobre:

- documentos e evidências recebidos e processados;
- dados canônicos próprios;
- regras determinísticas e suas versões;
- DE/PARA e mappings;
- propostas contábeis;
- estados de workflow;
- aprovações realizadas dentro do Serdial21;
- integrações e seus estados;
- explicações de IA;
- auditoria do próprio processo.

### 3.3 Regras inegociáveis

- Toda proposta com efeito contábil exige aprovação humana válida.
- A IA é assistiva; não aprova, publica regra, desbloqueia, exporta, efetiva escrituração ou altera permissão.
- IDs identificam recursos, mas nunca autorizam acesso.
- `tenant_id` e `company_id` do cliente não são confiáveis por si sós.
- Toda fronteira empresarial deve revalidar tenant, empresa, membership e `CompanyAccess`.
- Dados e operações críticas precisam de auditoria, idempotência e versões rastreáveis.
- O projeto não deve inventar regra, conta, tolerância ou tratamento contábil quando a decisão estiver ausente.

---

## 4. Mapa dos sistemas e responsabilidades

| Componente | Papel atual | Autoridade | Estado em 30/09/2026 |
|---|---|---|---|
| Sistema A | Portal administrativo e portal de clientes | Cadastro operacional legado, autenticação e experiência atual do portal | Produção; fluxos de clientes endurecidos |
| Sistema B | Plataforma de inteligência contábil | Evidências, dados canônicos, regras, propostas, revisão, workflow e auditoria próprios | Publicação interna e piloto controlado |
| n8n | Orquestração do Sistema A e integrações operacionais | Execução de workflows, não de regras contábeis soberanas | Produção; workflows novos publicados |
| MariaDB/MySQL do Sistema A | Persistência do portal existente | Dados operacionais do portal | Produção |
| MySQL do Sistema B | Persistência da plataforma nova | Estado transacional e auditável do Sistema B | Piloto interno |
| Google Drive | Armazenamento externo usado por fluxos do Sistema A | Arquivos externos; sujeito a reconciliação | Integrado aos fluxos aplicáveis |
| SMTP | Entrega de e-mails | Transporte externo, não confirmação de regra de negócio | Integrado aos fluxos aplicáveis |
| Domínio | Sistema contábil externo | Escrituração e números oficiais | Integração ampla ainda não ativada |
| Lovable | Desenvolvimento/publicação do frontend do Sistema A | Código e build do portal | Alterações publicadas |

### 4.1 O que a conexão A→B significa hoje

Existe:

- ponte de autenticação curta e controlada para funcionários;
- importação manual e offline de empresas autorizadas;
- referência externa para correlacionar registros sem assumir que os IDs dos sistemas são iguais;
- provisionamento explícito de usuário e acesso empresarial.

Não existe, de forma geral:

- sincronização contínua de clientes ou documentos;
- replicação automática de todas as alterações do Sistema A;
- barramento de eventos produtivo completo;
- outbox/inbox de negócio cobrindo todos os efeitos;
- DLQ operacional completa para integração A→B;
- envio oficial de lançamentos ao Domínio;
- autorização para importar indiscriminadamente toda a base do Sistema A.

---

## 5. Decisões, gates e evolução das autorizações

Documentos históricos registravam um `NO_GO` amplo para piloto e integração. Esse registro continua correto para o escopo geral que avaliava. Posteriormente, foram aprovadas exceções estreitas, com controles explícitos. Uma autorização pontual não converte o projeto inteiro em `GO`.

### 5.1 Leitura correta dos gates

| Tema | Estado | Interpretação |
|---|---|---|
| Desenvolvimento local e testes | Autorizado | Dentro das regras do repositório |
| Publicação interna do Sistema B | Autorizada e realizada | Uso interno controlado; não equivale a lançamento comercial |
| Ponte de login A→B | Autorizada e validada | Somente funcionários e escopo aprovado |
| Importação manual A→B | Autorizada e realizada de forma controlada | Uma empresa autorizada; processo offline e idempotente |
| Sincronização geral A→B | Não autorizada/implementada | Exige contrato e nova decisão |
| Piloto real amplo | Não concluído | Há apenas piloto controlado e evidência limitada |
| Integração produtiva com Domínio | Não autorizada | Sistema externo segue como autoridade |
| Lançamento comercial amplo | Não aprovado | Requer gates técnicos, operacionais, jurídicos e de suporte |

### 5.2 ADRs e decisões estruturantes

O conjunto de ADRs cobre, entre outros temas:

- arquitetura modular e fronteiras de domínio;
- tenancy, empresas e autorização;
- evidências imutáveis e trilha de auditoria;
- regras determinísticas, mappings e versionamento;
- propostas contábeis e aprovação humana;
- idempotência, locks e efeitos externos;
- identidade OIDC e segurança de autenticação;
- catálogo contábil de produção;
- privacidade e retenção;
- separação entre Sistema A e Sistema B;
- importação manual e controlada;
- ponte de login A→B;
- publicação interna e estabilização de contratos;
- recuperação segura de senha de administradores;
- ajustes de identificadores fiscais e cutover dos fluxos de clientes.

Para qualquer decisão material nova, deve-se criar ou atualizar o ADR correspondente em vez de apenas alterar código ou workflow.

---

## 6. Estado do repositório

### 6.1 Baseline observada

- Branch: `main`.
- Commit remoto confirmado: `d18f62a`.
- Arquivos rastreados: **982**.
- Arquivos Python em `src/serdial21`: **247**.
- Arquivos de teste `test_*.py`: **87**.
- Versão declarada do projeto: `0.1.0`.
- Python suportado: `>=3.12`.

### 6.2 Commits recentes relevantes

| Commit | Conteúdo resumido |
|---|---|
| `d18f62a` | Registro do cutover dos workflows de clientes do Sistema A |
| `49a315f` | Gestão segura de clientes no Sistema A |
| `c74311d` | Controles pós-importação do piloto |
| `b189951` | Onboarding da empresa piloto |
| `1c17d8a` | Validação de CPF e CNPJ alfanumérico |
| `97c85bc` | Validação produtiva da recuperação de senha admin |
| `d66f05b` | Versionamento da correção do workflow de recuperação |
| `1a0a085` | Rejeição de headers não confiáveis para rate limit |
| `c817ce2` | Normalização de resultados de procedures MariaDB no n8n |
| `2c28c01` | Preparação da recuperação segura de senha admin |
| `8d5d3f9` | Suporte ao tenant aprovado no bootstrap |
| `07ad9a6` | Endurecimento de logs e memória Redis |
| `6a13281` | Remoção de capability desnecessária do Caddy |
| `af8e1d6` | Rede de egress restrita para a API |
| `6176518` | Redis com identidade não-root explícita |
| `1f8bbe2` | Leitura controlada de secrets pelos serviços não-root |
| `bb16d10` | Preparação do deploy interno do Sistema B |

### 6.3 Estado local preservado

No momento da elaboração existiam alterações locais anteriores e não relacionadas a este dossiê:

- modificação em `docs/DOSSIE_SESSAO_2026-09-23.md`;
- diretório não rastreado `.claude/`;
- documento não rastreado `docs/DOSSIE_TECNICO_ESTADO_ATUAL_2026-09-25.md`.

Esses artefatos não foram sobrescritos nem incorporados automaticamente. Devem ser revisados pelo proprietário antes de qualquer commit que use `git add .`.

---

## 7. Stack e padrões técnicos

### 7.1 Backend do Sistema B

- Python 3.12 ou superior;
- FastAPI;
- SQLAlchemy 2.x;
- Alembic;
- MySQL com PyMySQL;
- Pydantic 2;
- Pydantic Settings;
- PyJWT com suporte criptográfico;
- Redis;
- Uvicorn;
- Pytest e HTTPX no ambiente de desenvolvimento.

### 7.2 Frontends e automação

- Sistema A: React, TypeScript, Vite e publicação pelo Lovable;
- Sistema B: aplicação web estática servida por Caddy;
- automações do Sistema A: n8n;
- proxy público: Caddy compartilhado de forma controlada;
- armazenamento externo: Google Drive quando previsto;
- e-mail: SMTP.

### 7.3 Diretriz arquitetural

O Sistema B é um **monólito modular orientado a domínios**. A aplicação não deve ser fragmentada em microsserviços sem justificativa mensurável e decisão aprovada.

As dependências devem apontar para dentro:

1. adaptadores dependem da aplicação;
2. aplicação depende do domínio e de portas;
3. domínio permanece Python puro sempre que possível;
4. FastAPI, SQLAlchemy, filas, storage e fornecedores não contaminam o núcleo do domínio.

---

## 8. Domínios implementados no Sistema B

Os módulos identificados em `src/serdial21/modules` são:

| Módulo | Responsabilidade principal |
|---|---|
| `identity` | Identidade, contexto autenticado e integração OIDC |
| `access_control` | Papéis, permissões, membership e acesso empresarial |
| `catalog` | Ciclo de vida do catálogo e versões publicadas |
| `chart_of_accounts` | Plano de contas e referências contábeis |
| `accounting` | Propostas contábeis, linhas, decisões e revisão |
| `rules` | Regras determinísticas versionadas |
| `mappings` | DE/PARA e mapeamentos explícitos |
| `intake_documents` | Ingestão, evidência e metadados documentais |
| `fiscal_documents` | Documentos fiscais, incluindo NF-e 55 |
| `banking` | Contas bancárias e importações financeiras |
| `reconciliation` | Conciliação e identificação de divergências |
| `workflow` | Estados, revisões, aprovações e transições |
| `locks` | Bloqueios empresariais e de período |
| `audit` | Eventos de auditoria append-oriented |
| `integrations` | Portas e contratos com sistemas externos |
| `privacy` | Retenção, legal hold e solicitações de titulares |
| `ai` | Funções assistivas de IA sob contratos restritos |
| `operations` | Fachadas e operações autorizadas da aplicação |

### 8.1 Estado funcional por capacidade

| Capacidade | Estado atual | Limitação principal |
|---|---|---|
| Tenancy e empresas | Implementada | Exige disciplina contínua em toda nova fronteira |
| RBAC e CompanyAccess | Implementados | Toda nova rota precisa de testes negativos cross-tenant |
| OIDC/bridge | Implementado e validado no escopo interno | Não inclui clientes do portal |
| Auditoria | Implementada, orientada a anexação | Integrações futuras devem preservar atomicidade |
| Evidência documental | Implementada | Fornecedores externos exigem reconciliação |
| NF-e modelo 55 | Implementada | CT-e e NFS-e não estão completos |
| OFX | Implementado | Cobertura de bancos e variações deve ser ampliada com evidência |
| CSV bancário | Configurável | Layouts reais precisam de homologação |
| Catálogo contábil | Implementado com estados e publicação | Publicação é imutável |
| Regras determinísticas | Implementadas | Lacunas geram pendência, não regra inventada |
| Mappings | Implementados e versionados | Mudanças materiais criam nova versão |
| Propostas contábeis | Implementadas | Não equivalem a escrituração oficial |
| Revisão humana | Implementada | Aprovação deve referenciar revisão/hash corretos |
| Locks | Implementados | Todos os canais de efeito precisam respeitá-los |
| Reconciliação | Parcial | Fluxos reais e exceções ainda precisam expansão |
| IA | Parcial/assistiva | Provedor e governança produtiva ainda não completos |
| Privacidade | Base técnica parcial | Validações jurídicas e operacionais ainda necessárias |
| Observabilidade | Saúde, logs sanitizados e métricas restritas | Agregação central e alertas reais ainda são lacunas |

---

## 9. Superfície de API do Sistema B

As rotas estão organizadas por contexto e devem permanecer finas: validar transporte, resolver o contexto autenticado, chamar casos de uso e mapear respostas.

### 9.1 Saúde

- `GET /health/live`;
- `GET /health/ready`.

Na publicação pública, a API é exposta sob `/api/v1`, incluindo `/api/v1/health/ready`.

### 9.2 Identidade e acesso

- obtenção da identidade atual;
- obtenção do contexto autenticado;
- onboarding e offboarding controlados;
- papéis, permissões e acesso por empresa;
- ponte OIDC/RS256 no escopo aprovado.

### 9.3 Catálogo

- criação de versão;
- avanço de estado;
- revisão;
- publicação imutável.

### 9.4 Operações por empresa

As rotas operacionais ficam sob o escopo equivalente a `/operations/companies/{company_id}` e incluem:

- dados da empresa;
- contas bancárias e mudança de status;
- listagem, resumo, detalhe e metadados de documentos;
- documentos fiscais;
- extratos bancários;
- importação de NF-e e OFX;
- processamento e reprocessamento autorizados;
- propostas contábeis, detalhe e atividade;
- plano/catálogo de contas e regras;
- classificação e decisão de itens;
- revisão, aprovação e rejeição;
- exceções;
- eventos de auditoria.

### 9.5 Métricas

A rota interna de métricas não deve ficar publicamente disponível em produção. A exposição pública de métricas sensíveis permanece desabilitada.

---

## 10. Modelo de dados e migrations do Sistema B

### 10.1 Estado Alembic

- Head atual: `20260923_0016`.
- Existe um único head conhecido.
- Migrations são o único mecanismo autorizado de evolução de schema.
- `create_all` e alterações manuais não substituem migration em produção.

### 10.2 Linha de evolução

| Revisão lógica | Conteúdo principal |
|---|---|
| `0001` | tenants |
| `0002` | controle de acesso |
| `0003` | auditoria |
| `0004` | documentos e evidências |
| `0005` | NF-e |
| `0006` | OFX |
| `0007` | workflow pré-homologação |
| `0008` | checkpoints da jornada NF-e |
| `0009` | locks de conta/período |
| `0010` | identidade OIDC |
| `0011` | catálogo produtivo |
| `0012` | controles de privacidade |
| `0013` | contas bancárias e metadados documentais por empresa |
| `0014` | núcleo de automação contábil |
| `0015` | referência externa de empresa |
| `0016` | equipe do escritório |

### 10.3 Invariantes importantes

- Todo dado de escritório carrega `tenant_id`.
- Todo dado de empresa carrega `tenant_id` e `company_id` quando aplicável.
- Relacionamentos devem impedir referência cross-tenant e cross-company.
- Dinheiro e valores de precisão definida usam `Decimal`/`DECIMAL`, nunca `float`.
- Versões publicadas são imutáveis.
- Correções materiais criam nova versão, revisão, ajuste ou evento relacionado.
- Idempotência compara chave e conteúdo; mesma chave com conteúdo diferente gera conflito.
- Auditoria de negócio não é substituída por log operacional.

---

## 11. Frontend operacional do Sistema B

O frontend do Sistema B fica em `app/` e é servido pelo contêiner web/Caddy. A publicação interna usa configuração separada do desenvolvimento local.

### 11.1 Áreas disponíveis

- Minha Visão;
- seleção de empresa;
- documentos;
- documentos fiscais;
- visão financeira/bancária;
- propostas e operações contábeis;
- navegação associada ao acesso empresarial do usuário.

### 11.2 Configuração de publicação

- `apiBaseUrl`: `/api/v1`;
- modo de dados: real;
- autenticação: bridge;
- rótulo operacional: piloto interno.

O arquivo local `app/config.js` permanece voltado ao ambiente de desenvolvimento/sintético e não deve ser confundido com a configuração injetada na publicação.

### 11.3 Lacunas de produto a conferir antes de expansão

- completar a experiência de perfil contábil por empresa, se ainda não exposta integralmente;
- revisar permissões e mensagens de negação em todas as telas;
- ampliar estados vazios, erros operacionais e recuperação de falhas;
- validar usabilidade com usuários reais do escritório;
- confirmar que nenhuma tela sugere que uma proposta já é escrituração oficial.

---

## 12. Infraestrutura e publicação interna do Sistema B

### 12.1 Topologia de contêineres

O projeto Compose é `serdial21-b` e contém:

- `storage-init`;
- `redis`;
- `api`;
- `migrate`, executado de forma opt-in;
- `web`.

### 12.2 Redes e exposição

- o contêiner web serve internamente em 8080 e se conecta ao proxy externo compartilhado;
- a API não publica porta diretamente no host;
- a API usa rede de backend interna e rede de egress restrita;
- o Redis não publica porta no host;
- o n8n público existente foi preservado durante a inclusão do Sistema B.

### 12.3 Endurecimento

- sistemas de arquivos somente leitura onde aplicável;
- `cap_drop: ALL`;
- `no-new-privileges`;
- usuários não-root;
- limites de CPU e memória;
- logs JSON com rotação aproximada de 10 MB por arquivo e três arquivos;
- secrets montados por arquivo;
- acesso aos secrets por grupo controlado;
- Redis somente com TLS e ACL;
- Redis sem persistência, com limite de memória de 128 MB e política `noeviction`;
- volume de evidências dedicado: `serdial21_b_evidence`.

### 12.4 Cuidados operacionais

- Não executar `docker compose config` em saída compartilhada, pois a resolução de secrets pode expor informações.
- Não copiar dumps, tokens ou arquivos de evidência para logs de suporte.
- Rodar migrations separadamente e verificar o head antes de iniciar a aplicação.
- Preservar o proxy público e o n8n ao alterar o Caddy.
- Manter cópia externa de secrets e validar hash/recuperabilidade sem exibir conteúdo.

### 12.5 Evidências da implantação

Na validação de 29/30 de setembro:

- aplicação pública respondeu HTTP 200;
- readiness da API respondeu HTTP 200;
- API, web e Redis estavam em execução e saudáveis;
- não havia reinícios observados desses contêineres;
- os contêineres n8n permaneceram ativos;
- redirecionamento HTTP→HTTPS e HSTS foram verificados;
- certificado TLS válido foi observado no período do checkpoint.

---

## 13. Ambiente de piloto do Sistema B

### 13.1 Banco

- banco de piloto: `u621451815_s21_pilot`;
- head aplicado: `20260923_0016`;
- uma empresa ativa foi confirmada após a importação controlada;
- um `CompanyAccess` ativo foi confirmado para o usuário provisionado.

### 13.2 Importação controlada

Foi autorizado e executado um processo manual e offline:

1. selecionar apenas uma empresa real autorizada;
2. gerar arquivo mínimo com os campos necessários;
3. executar dry-run;
4. conferir canonicalização, tenant e correlação externa;
5. executar importação real;
6. repetir para comprovar idempotência;
7. confirmar auditoria e acesso;
8. remover o arquivo real da área ativa após o uso.

Um arquivo sintético com cinco linhas foi preservado apenas para referência de teste no VPS, em caminho de dados locais com permissão `0600`. Ele não foi importado e não deve ser reutilizado como se fosse dado real.

### 13.3 Referência externa

A correlação de empresas usa um triplo equivalente a:

- sistema externo;
- tipo externo;
- identificador externo.

Essa referência evita usar o ID do Sistema A como se fosse identidade ou autorização nativa do Sistema B.

---

## 14. Identidade, autorização e ponte A→B

### 14.1 Princípio

O Sistema A autentica o funcionário em seu contexto. Para entrada no Sistema B, uma ponte emite credencial curta, assinada e verificável. O Sistema B autentica essa credencial, mas ainda aplica suas próprias regras de tenant, usuário e `CompanyAccess`.

### 14.2 Fluxo aprovado

- Sistema A valida uma sessão vigente de funcionário;
- função de borda emite token curto RS256;
- chave pública/JWKS permite verificação pelo Sistema B;
- frontend recebe o token no fragmento da URL;
- token é removido da barra de endereço após o consumo;
- backend B resolve usuário, tenant e acessos provisionados;
- seleção de empresa só mostra acessos válidos.

### 14.3 Evidência

A navegação real pelo botão do Sistema A até o Sistema B foi testada. A tela do Sistema B apresentou a seleção de empresa esperada.

### 14.4 Limites

- a ponte atual é para funcionários, não para clientes do portal;
- tenant inicial é o tenant aprovado da Serdial21;
- usuário e acessos ainda precisam de provisionamento explícito;
- o token não transporta autoridade irrestrita;
- não se deve confiar em `tenant_id`, `company_id` ou função vindos apenas do frontend;
- a ponte não autoriza sincronização de dados de negócio.

---

## 15. Validação de CPF e CNPJ

O projeto passou a tratar identificadores fiscais como strings canônicas, preservando zeros à esquerda e permitindo o novo formato alfanumérico de CNPJ.

### 15.1 Regras implementadas

- CPF: formato canônico numérico e dígitos verificadores válidos;
- CNPJ numérico: módulo 11 e dígitos verificadores válidos;
- CNPJ alfanumérico: regra oficial de módulo 11, usando valor baseado no código ASCII menos 48;
- canonicalização: remoção de máscara e conversão de letras para maiúsculas;
- máscara: apenas apresentação;
- unicidade: aplicada no escopo de tenant apropriado;
- identificador fiscal não é usado como autorização.

### 15.2 Caso de referência testado

O valor alfanumérico de teste `12.ABC.345/01DE-35` foi reconhecido como válido e persistido em forma canônica sem máscara.

---

## 16. Sistema A — estado da base e do pacote de clientes

### 16.1 Ambiente

- schema: `u621451815_serdial21`;
- engine: MariaDB/MySQL hospedado;
- versão observada durante a etapa: MariaDB 11.8.9;
- tabela central legada: `clientes`.

### 16.2 Estruturas confirmadas

- `clientes`;
- `clientes_emails_autorizados`;
- `security_sessoes_clientes`;
- `security_password_reset_clientes`;
- coluna gerada `documento_fiscal_canonico`;
- índice único `uq_clientes_documento_fiscal_canonico`;
- coluna `telefone VARCHAR(20) NULL`.

### 16.3 Procedures confirmadas

- `sp_admin_cliente_create`;
- `sp_admin_cliente_set_folder`;
- `sp_cliente_password_reset_request`;
- `sp_cliente_password_reset_apply`;
- `sp_admin_cliente_update`.

As procedures novas usam `SQL SECURITY INVOKER`, parâmetros explícitos, validações e transações conforme o caso.

### 16.4 Observação sobre collation

Foi observada diferença histórica de collation entre tabelas existentes e novas. Ela não impediu a etapa validada, mas futuras joins, índices e comparações devem declarar compatibilidade e ser testadas na versão real do MariaDB.

---

## 17. Sistema A — workflows de clientes

### 17.1 Workflows seguros publicados

| Workflow | Função | Estado |
|---|---|---|
| `API - Admin - Novo Cliente V3 (Seguro)` | Cadastro seguro de cliente | Publicado |
| `API - Admin - Lista Clientes V2.1 (Completa)` | Listagem com status e campos atualizados | Publicado |
| `API - Admin - Editar Cliente V1 (Seguro)` | Edição segura, logo e eventual ativação | Publicado |
| `[Auth] Gestao de Senhas Cliente v2 (Seguro)` | Solicitação e aplicação de nova senha | Publicado |

### 17.2 Workflows antigos substituídos

Foram exportados para backup e despublicados:

- workflow antigo de novo cliente V2;
- workflow antigo da lista de clientes;
- workflow antigo de gestão de senhas por Magic Link.

A despublicação foi necessária para evitar dois workflows disputando o mesmo path de produção.

### 17.3 Endpoints preservados

- `POST /admin/novo-cliente-v2`;
- `GET /admin/clientes-v2`;
- `POST /admin/editar-cliente-v2`;
- `POST /portal/solicitar-senha`;
- `POST /portal/redefinir-senha`.

O frontend não precisou trocar os contratos públicos para receber o endurecimento do backend.

### 17.4 Contrato de edição

O frontend envia `POST multipart/form-data` para `/admin/editar-cliente-v2`, com:

- `acao`;
- `cliente_id`;
- `funcionario_id` legado no corpo;
- `nome_cliente`;
- `cnpj_cpf` normalizado;
- `status`;
- `email`;
- `whatsapp`;
- `telefone`;
- `file` opcional para logo.

O backend deve extrair a identidade administrativa do bearer token e não confiar no `funcionario_id` recebido no corpo.

### 17.5 Regras funcionais

- status permitidos: `Ativo`, `Inativo` e `Lead`;
- `Lead` pode ficar sem documento;
- `Ativo` e `Inativo` exigem documento fiscal válido;
- e-mail é normalizado em minúsculas e validado para unicidade;
- CNPJ alfanumérico é aceito;
- mudança que reduz acesso revoga sessões conforme a política;
- mudança material gera auditoria;
- criação de pasta e envio de e-mail são efeitos externos e não devem mascarar o resultado transacional.

---

## 18. Sistema A — frontend de clientes

### 18.1 Arquivos modificados e publicados no projeto Lovable

- `src/lib/documentoFiscal.ts` — novo;
- `src/pages/admin/AdminClientes.tsx`;
- `src/pages/RedefinirSenha.tsx`;
- `src/test/documentoFiscal.test.ts` — novo.

`src/pages/EsqueciSenha.tsx` não precisou ser alterado porque já enviava para o endpoint correto, mostrava resposta neutra e não registrava o e-mail.

### 18.2 Comportamento da tela de clientes

- campo `Status` com `Ativo`, `Inativo` e `Lead`;
- listagem usa o status retornado pela API;
- ausência de status aparece como `—`, sem presumir `Ativo`;
- letras do CNPJ são preservadas durante a entrada;
- documento enviado à API vai canonicalizado;
- mensagens do backend continuam visíveis ao usuário;
- edição permite logo, dados cadastrais, contatos e status.

### 18.3 Comportamento da redefinição de senha

- token aceito somente em `#token=`;
- token removido da barra imediatamente após leitura;
- `?token=` antigo deixa de funcionar;
- senha de 12 a 128 caracteres;
- exige pelo menos uma letra e um número;
- sem token, informa link inválido e oferece solicitar novo link;
- troca só é considerada concluída quando a API responde `success: true`.

### 18.4 Publicação

- URL padrão Lovable registrada: `https://serdialconnect-hub.lovable.app`;
- URL principal verificada no uso: `https://serdial21.com`;
- página operacional validada: `/admin/clientes`.

---

## 19. Sistema A — recuperação de senha de clientes

### 19.1 Solicitação

- recebe o e-mail;
- normaliza a identidade;
- responde de forma neutra independentemente da existência da conta;
- aplica controles de abuso no banco;
- gera token aleatório de 256 bits no banco;
- armazena somente o hash do token;
- registra `request_id` para correlação;
- envia e-mail apenas quando as condições são satisfeitas.

### 19.2 Aplicação

- valida formato do token e da nova senha;
- compara hash;
- exige token não expirado, não usado e não revogado;
- aplica senha dentro de transação;
- marca o token como usado;
- revoga sessões do cliente;
- impede reutilização;
- retorna mensagem segura sem vazar detalhes indevidos.

### 19.3 Política do link

- validade de 30 minutos;
- uso único;
- token no fragmento da URL;
- hash no banco;
- nenhuma exposição deliberada em logs ou auditoria.

---

## 20. Sistema A — recuperação de senha de administradores

Foi criada e validada uma trilha separada para funcionários/administradores.

### 20.1 Workflow atual

- `[Auth] Recuperacao de Senha Admin v1.1` está publicado;
- a versão anterior permaneceu como histórico não publicado;
- endpoints: `/admin/solicitar-senha` e `/admin/redefinir-senha`.

### 20.2 Controles

- token aleatório emitido pelo banco com `RANDOM_BYTES()`;
- somente hash persistido;
- resposta neutra;
- rate limit baseado em sinais confiáveis;
- headers fornecidos livremente pelo cliente não são aceitos como identidade de origem;
- troca atômica de senha;
- revogação de sessões;
- auditoria;
- CORS restrito ao domínio aprovado.

### 20.3 Compatibilidade n8n/MariaDB

O runtime n8n 2.6.4 não disponibilizou `require('crypto')` nem Web Crypto nos Code nodes usados. A geração segura foi movida para o MariaDB. O driver MySQL do n8n também retorna `CALL` com conjunto de resultados aninhado e metadados; por isso foram adicionados normalizadores explícitos.

### 20.4 Verificações adicionais recomendadas

Mesmo com o fluxo ponta a ponta aprovado, convém manter testes independentes para:

- reutilização do mesmo token;
- token expirado;
- senha fora da política;
- revogação efetiva de sessão anterior;
- resposta neutra para usuário inexistente;
- retenção desativada em novas cópias do workflow.

---

## 21. Evidências funcionais do pacote de clientes

### 21.1 Segurança de autenticação

- listagem com bearer falso retornou HTTP 401;
- edição com bearer falso retornou HTTP 401;
- criação com bearer falso retornou HTTP 401;
- sessão administrativa foi renovada antes do teste real.

### 21.2 Recuperação de senha

- solicitação para identidade sintética inexistente retornou HTTP 200 neutro;
- tentativa com token inválido retornou HTTP 400;
- paths de produção ficaram disponíveis somente após publicação correta do workflow.

### 21.3 Edição real controlada

- cliente sintético foi editado pela interface;
- CNPJ alfanumérico válido foi salvo;
- status mudou de `Ativo` para `Lead`;
- interface exibiu confirmação de sucesso;
- banco confirmou valor canônico e novo status;
- sessões ativas do cliente ficaram em zero;
- links de redefinição pendentes ficaram em zero;
- auditoria confirmou status anterior e novo;
- ramo de envio de ativação não foi executado nessa mudança.

### 21.4 Lista

- listagem autenticada foi carregada na interface;
- status retornados foram exibidos;
- máscara de CNPJ alfanumérico apareceu corretamente.

---

## 22. Retenção de execuções n8n e incidente contido

Durante a validação, uma execução salva no n8n exibiu no painel um bearer token administrativo recebido pelo workflow. O incidente foi contido:

1. a sessão administrativa foi renovada;
2. a execução afetada foi removida;
3. a retenção de execuções foi desativada explicitamente nos quatro workflows do pacote de clientes;
4. o acesso MCP permaneceu desativado.

### 22.1 Configuração esperada nos quatro workflows

- não salvar execuções de produção com sucesso;
- não salvar execuções de produção com falha;
- não salvar execuções manuais, quando a política do workflow exigir proteção máxima;
- não salvar progresso de execução;
- MCP desativado.

### 22.2 Estado confirmado

Foi registrada desativação de retenção em:

- edição de clientes;
- novo cliente;
- lista de clientes;
- gestão de senhas de clientes.

### 22.3 Lição operacional

Toda cópia ou novo workflow que recebe `Authorization`, token de reset, e-mail, documento fiscal ou conteúdo de cliente deve ter a retenção revisada antes de ser publicado. A política não pode depender apenas de uma configuração global presumida.

---

## 23. Backups e capacidade de recuperação

### 23.1 Backups confirmados do pacote de clientes

Em 30/09/2026 às 15:58, foram confirmados:

- backup do banco do Sistema A após a etapa;
- backup geral do n8n após a etapa;
- exportação individual do workflow de edição;
- exportação individual da lista nova;
- exportação individual do novo cliente seguro;
- exportação individual da gestão segura de senhas;
- exportação das versões antigas da lista;
- exportação do workflow antigo de novo cliente;
- exportação do workflow antigo de senha/Magic Link.

### 23.2 Sistema B

Existem runbooks e scripts para:

- backup do MySQL;
- backup de evidências;
- verificação de artefatos;
- restauração controlada;
- drill de disaster recovery;
- cópia externa de secrets.

Uma cópia externa dos secrets do Sistema B foi registrada e verificada sem exposição do conteúdo.

### 23.3 Regras

- backup só é considerado suficiente quando a restauração é testável;
- arquivos criptografados devem ter chave de recuperação fora do mesmo domínio de falha;
- dumps não devem conter secrets em nomes, logs ou comandos compartilhados;
- restauração deve ser feita em ambiente isolado antes de qualquer substituição produtiva;
- workflows antigos devem permanecer despublicados, ainda que estejam preservados em backup.

---

## 24. Testes e qualidade

### 24.1 Suíte do repositório

Resultado medido em 30/09/2026:

```text
565 passed, 20 skipped, 2 warnings in 51.03s
```

### 24.2 Testes ignorados

Os testes ignorados dependem de condições opt-in, como:

- MariaDB real;
- migrations em banco compatível;
- ambiente de homologação;
- restauração ou disaster recovery autorizados;
- credenciais e serviços externos.

O texto de motivo de um skip antigo menciona revisões anteriores e pode estar historicamente desatualizado. O estado de migrations deve ser determinado pelo head Alembic e pelo banco-alvo, não por essa mensagem isolada.

### 24.3 Avisos

- depreciação na integração Starlette/HTTPX;
- depreciação relacionada ao `BlockingPortal` do AnyIO.

Não são falhas atuais, mas devem entrar no backlog de manutenção para evitar quebra futura ao atualizar dependências.

### 24.4 Testes do frontend do Sistema A

Foram reportados **15 testes aprovados**, cobrindo:

- CPF válido e inválido;
- CNPJ numérico válido e inválido;
- CNPJ alfanumérico válido e inválido;
- preservação de letras e máscara de exibição;
- `Lead` sem documento;
- rejeição de `Ativo`/`Inativo` sem documento;
- reconhecimento dos três status;
- leitura do token em fragmento e remoção da URL.

O build de produção terminou sem erros, com apenas aviso de tamanho de bundle.

### 24.5 Limite das evidências

Teste local não substitui:

- teste de migration em MariaDB suportado;
- restore drill;
- validação de rede e proxy;
- teste de SMTP/Drive;
- testes cross-tenant em cada nova fronteira;
- aceite operacional de usuários;
- homologação com o sistema contábil externo.

---

## 25. Segurança, privacidade e auditoria

### 25.1 Controles presentes

- autenticação e contexto de acesso explícitos;
- `CompanyAccess` para fronteira empresarial;
- isolamento por tenant e empresa;
- CORS restrito nos workflows tratados;
- SQL parametrizado nos fluxos novos;
- tokens aleatórios e hash-only para recuperação;
- revogação de sessões;
- auditoria append-oriented;
- logs sanitizados;
- secrets fora do código;
- containers com mínimo privilégio;
- Redis protegido;
- versões publicadas imutáveis;
- validação de identificadores fiscais;
- resposta neutra contra enumeração de contas.

### 25.2 Obrigações para todo desenvolvimento futuro

- testes positivos e negativos de autorização;
- testes cross-tenant e de `CompanyAccess`;
- revalidação no instante do efeito crítico;
- nenhuma confiança em IDs do body como prova de acesso;
- nenhuma credencial em fixture, snapshot, log ou auditoria;
- conteúdo externo tratado como dado não confiável;
- nenhuma execução de código arbitrário, `eval` ou equivalente;
- IA sem autoridade crítica;
- auditoria e mutação atômicas quando pertencem ao mesmo banco;
- reconciliação antes de repetir efeito externo de estado desconhecido.

### 25.3 Privacidade

A base técnica contempla retenção, legal hold e solicitações de titulares, mas a operação produtiva ampla ainda requer validação jurídica e definição formal de:

- bases legais e finalidades;
- prazos de retenção por classe de dado;
- responsáveis e aprovadores;
- política de incidentes;
- fornecedores e suboperadores;
- descarte verificável;
- separação entre inferência, logs, melhoria e treinamento.

Dados de tenant não devem ser usados para treinamento por padrão.

---

## 26. Riscos residuais conhecidos

### 26.1 Prioridade crítica antes de ampliar o uso do Sistema A

1. **Login legado de clientes:** há registro de geração com `Math.random` e SQL interpolado em fluxo legado. Deve ser substituído por geração criptográfica e queries parametrizadas.
2. **Auditoria da retenção n8n:** outros workflows legados podem salvar tokens, documentos e PII. É necessário inventário e política explícita por workflow.
3. **Hash legado de senha administrativa:** existe contexto histórico de SHA-256. Planejar migração compatível para algoritmo moderno de senha, como Argon2id, sem quebra de usuários.
4. **Efeitos externos após commit:** criação de pasta no Drive e envio de e-mail podem falhar depois do banco confirmar a transação. Falta uma estratégia geral de outbox/reconciliação.

### 26.2 Prioridade alta no Sistema B

1. executar migrations 0013–0016 em ciclo real de upgrade e restore no MariaDB suportado sempre que o ambiente mudar;
2. ampliar testes reais de autorização e isolamento em toda nova rota;
3. fechar observabilidade centralizada e transporte real de alertas;
4. validar backup/restauração em cadência regular;
5. completar governança de privacidade;
6. validar o uso piloto com procedimentos operacionais e responsáveis;
7. manter clara a distinção entre proposta Serdial21 e registro oficial do Domínio.

### 26.3 Integrações

1. não há sincronização geral A→B;
2. não há outbox/inbox e DLQ completas para eventos empresariais;
3. não há cadeia completa de homologação com o Domínio;
4. não há exportação/escrituração oficial autorizada;
5. Google Drive e SMTP precisam de monitoramento, idempotência e reconciliação de falha parcial.

### 26.4 Produto e operação

1. piloto ainda tem amostra pequena;
2. suporte, SLA, incidentes e plantão precisam de definição antes de lançamento amplo;
3. treinamento de usuários e documentação operacional precisam acompanhar cada capacidade ativada;
4. funcionalidades como obrigações completas, faturamento, relatórios avançados e mobile não devem ser presumidas.

---

## 27. O que não está concluído ou não deve ser alegado

Não declarar que o projeto já possui:

- escrituração contábil oficial pelo Serdial21;
- fechamento oficial;
- sincronização automática completa entre A e B;
- integração produtiva ampla com Domínio;
- IA autônoma capaz de aprovar ou lançar;
- cobertura completa de CT-e e NFS-e;
- conciliação universal para todos os bancos e layouts;
- governança jurídica de privacidade integralmente aprovada;
- lançamento comercial irrestrito;
- alta disponibilidade ou disaster recovery comprovados para qualquer cenário;
- eliminação de todos os riscos dos workflows legados;
- multi-tenant produtivo do Sistema A.

O Sistema A continua essencialmente no modelo atual do escritório. Qualquer evolução dele para múltiplos escritórios é uma iniciativa separada, que exige arquitetura, migration, autorização e testes próprios.

---

## 28. Divergências documentais conhecidas

Alguns documentos anteriores ainda contêm informações corretas para a data em que foram escritos, mas superadas operacionalmente, por exemplo:

- Sistema B ainda sem endereço público;
- DNS ou certificado pendente;
- publicação interna não realizada;
- contagens antigas de testes;
- head Alembic anterior;
- `NO_GO` sem mencionar as exceções estreitas posteriormente aprovadas;
- workflows antigos ainda publicados.

Esses documentos devem ser mantidos como histórico. Para estado atual, usar este dossiê junto dos checkpoints de 29 e 30 de setembro e dos ADRs correspondentes.

Não se deve editar o passado para fazê-lo parecer sempre coerente com o presente. A rastreabilidade da mudança é parte da governança.

---

## 29. Inventário documental para retomada

### 29.1 Documentos-base

- `AGENTS.md`;
- `README.md`;
- `docs/PROJECT_MASTER_GUIDE.md`;
- `docs/PRODUCTIZATION_ROADMAP.md`;
- `docs/PILOT_GO_NO_GO.md`;
- `docs/PILOT_READINESS.md`.

### 29.2 Arquitetura e decisões

- diretório `docs/adr/`;
- ADR da importação manual A→B;
- ADR da ponte de login;
- ADR da publicação interna/contratos;
- ADR da recuperação de senha admin;
- registros de cutover dos workflows de clientes.

### 29.3 Operação e deploy

- `docs/INTERNAL_VPS_DEPLOYMENT.md`;
- runbooks de deploy, backup, restore e disaster recovery;
- arquivos em `deploy/`;
- checkpoints de implantação e piloto;
- scripts operacionais em `scripts/`.

### 29.4 Sistema A

- pacotes SQL do cadastro e edição de clientes;
- workflows JSON/versionados quando presentes no repositório;
- documentação de endpoints e validações;
- checklists de backup, cutover e retenção.

### 29.5 Testes

- `tests/`;
- testes de domínio, aplicação, adaptadores e contratos;
- testes opt-in de MariaDB;
- testes de deployment e segurança;
- testes do frontend do Sistema A no projeto Lovable.

---

## 30. Linha do tempo resumida da etapa recente

1. O Sistema B foi preparado para implantação interna segura.
2. Rede, secrets, Redis, Caddy, healthcheck e logging foram endurecidos.
3. Migrations avançaram até equipe do escritório e referência externa.
4. A ponte de login A→B foi aprovada e implementada.
5. O Sistema B foi publicado em `contabilidade.serdial21.com`.
6. A navegação real A→B foi validada.
7. Uma empresa real autorizada foi importada de forma manual, idempotente e auditável.
8. A validação de CPF/CNPJ foi ampliada, incluindo CNPJ alfanumérico.
9. A recuperação de senha admin foi redesenhada e validada em produção.
10. O pacote seguro de clientes do Sistema A foi aplicado ao banco.
11. Foram criados os workflows seguros de novo cliente, lista, edição e senhas.
12. O frontend foi adaptado para status, CNPJ alfanumérico e token em fragmento.
13. Testes locais, build e testes de produção controlados foram executados.
14. Foi identificado e contido o armazenamento de bearer token em execução n8n.
15. Retenção foi desativada nos quatro workflows novos.
16. Workflows antigos conflitantes foram exportados e despublicados.
17. Backups do banco, n8n e workflows foram confirmados.
18. Commits foram enviados ao GitHub até `d18f62a`.

---

## 31. Situação final desta etapa

### 31.1 Concluído

- base arquitetural do Sistema B;
- módulos principais do MVP em diferentes graus de maturidade;
- suíte ampla de testes locais;
- migrations até `0016`;
- implantação interna endurecida;
- URL pública interna com HTTPS;
- autenticação bridge A→B;
- primeiro onboarding real controlado;
- validação fiscal atualizada;
- recuperação segura de senha admin;
- recuperação segura de senha cliente;
- cadastro, lista e edição segura de clientes;
- frontend de clientes publicado;
- cutover dos workflows novos;
- despublicação dos legados conflitantes;
- retenção sensível desativada;
- backups pós-etapa confirmados;
- documentação e commits enviados ao remoto.

### 31.2 Parcial

- piloto real, ainda restrito;
- privacidade operacional;
- observabilidade central;
- reconciliação;
- uso de IA;
- cobertura de documentos fiscais além de NF-e 55;
- integração com fornecedores externos;
- experiência completa de configuração contábil por empresa.

### 31.3 Não iniciado ou não autorizado em produção ampla

- sincronização geral A→B;
- integração oficial de escrituração com Domínio;
- ondas completas do Connect Hub;
- lançamento comercial amplo;
- expansão do Sistema A para multi-tenant;
- automação contábil sem revisão humana.

---

## 32. Próxima etapa recomendada

A próxima etapa mais segura é um **ciclo de saneamento de segurança e operação do legado do Sistema A**, antes de ampliar dados reais ou conectar novas automações.

### 32.1 Objetivo sugerido

Eliminar os riscos conhecidos do login legado de clientes e criar uma política verificável de retenção e tratamento de dados para todos os workflows n8n que processam autenticação, documentos fiscais, dados pessoais ou segredos.

### 32.2 Escopo proposto

1. inventariar workflows publicados e paths;
2. identificar duplicidade de webhooks;
3. classificar dados sensíveis recebidos por cada workflow;
4. revisar configurações de retenção;
5. localizar `Math.random`, tokens previsíveis e SQL interpolado;
6. substituir o login legado de clientes com contrato compatível e plano de rollback;
7. parametrizar queries;
8. manter resposta neutra e revogação de sessão;
9. executar testes negativos e positivos;
10. exportar backup antes do cutover;
11. registrar ADR/checkpoint;
12. somente então avaliar expansão do piloto do Sistema B.

### 32.3 Gate de saída sugerido

- nenhum workflow de autenticação salva bearer, senha ou token;
- nenhum token de segurança usa RNG não criptográfico;
- nenhuma query de autenticação concatena entrada do usuário;
- caminhos de produção possuem apenas um workflow publicado responsável;
- backups e rollback foram testados;
- sessões antigas são invalidadas conforme a política;
- testes de enumeração, repetição, expiração e rate limit passam;
- auditoria registra efeitos sem armazenar segredos.

Esta recomendação não autoriza a implementação automaticamente. A próxima tarefa deve ser explicitamente escolhida e limitada.

---

## 33. Checklist de retomada para uma nova sessão

Antes de alterar qualquer coisa:

1. ler `AGENTS.md` integralmente;
2. ler este dossiê;
3. localizar o ADR e o runbook do tema escolhido;
4. executar `git status --short --branch`;
5. preservar as alterações locais existentes;
6. confirmar branch e commit remoto;
7. identificar se a tarefa pertence ao Sistema A, B ou à ponte;
8. declarar o que está e o que não está autorizado;
9. levantar impacto em tenant, empresa, auditoria, idempotência, backup e rollback;
10. procurar implementação equivalente antes de criar nova;
11. implementar a menor alteração suficiente;
12. executar testes relacionados e, quando viável, a suíte completa;
13. atualizar documentação e checkpoint;
14. não publicar, migrar banco real ou alterar workflow produtivo sem autorização explícita;
15. parar ao concluir a fase solicitada.

### 33.1 Comandos locais seguros de diagnóstico

```powershell
git status --short --branch
git log --oneline -20
python -m pytest
python -m alembic heads
```

Para testes opt-in de MariaDB, restore ou homologação, usar apenas o runbook correspondente e credenciais do ambiente, sem colocá-las na linha de comando compartilhada.

---

## 34. Critérios permanentes para decisões futuras

Toda nova capacidade deve responder claramente:

1. Quem é a autoridade do dado?
2. Qual tenant e empresa são afetados?
3. Como o acesso é comprovado e revalidado?
4. Qual é a chave de idempotência?
5. Qual versão de entrada, parser, regra e mapping foi usada?
6. Qual evento de auditoria acompanha o efeito?
7. O que acontece em timeout ou estado externo desconhecido?
8. Como a operação é reconciliada?
9. Como o backup e o rollback funcionam?
10. Quais dados sensíveis aparecem em logs, filas, e-mails ou execuções?
11. A IA está apenas sugerindo ou recebeu autoridade indevida?
12. A interface deixa claro o que é proposta e o que é oficial?
13. Existem testes negativos cross-tenant?
14. Uma versão publicada está sendo preservada?
15. A mudança pertence realmente à fase solicitada?

---

## 35. Declaração de encerramento da etapa

Com base nas evidências disponíveis, a etapa de endurecimento e cutover da gestão de clientes do Sistema A, somada à publicação interna e ao onboarding inicial do Sistema B, pode ser considerada concluída no escopo autorizado.

Essa conclusão significa:

- os artefatos previstos nesta etapa foram implementados e testados;
- os fluxos novos relevantes estão publicados;
- os fluxos antigos conflitantes foram despublicados;
- backups foram feitos;
- evidências técnicas e operacionais foram registradas;
- o código e a documentação recente foram enviados ao repositório remoto.

Ela não significa:

- aprovação de lançamento comercial amplo;
- autorização de sincronização geral entre sistemas;
- conclusão de integração com o sistema contábil externo;
- eliminação dos riscos legados;
- dispensa de aprovação humana em efeitos contábeis;
- encerramento do trabalho de segurança, privacidade, observabilidade e recuperação.

O ponto de retomada recomendado é escolher explicitamente uma única próxima frente, registrar seu escopo e seus gates, e avançar sem misturar fases.

