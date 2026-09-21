# Especificação do shell do aplicativo

## Arquitetura

O frontend permanece HTML/CSS/JavaScript nativo. `app/index.html` é a entrada; `config.js` declara modos e configuração pública; `core.js` controla sessão; `oidc-client.js` isola OAuth/OIDC; `api-client.js` centraliza a API; `mock-provider.js` isola dados sintéticos; `app.js` compõe bootstrap e shell. Tokens, componentes e marca continuam em `ui/`. `prototype.html` permanece referência histórica.

FRONTEND_ARCHITECTURE_DECISION=KEEP_NATIVE. Não existe justificativa material para migração de framework nesta fase.

## Bootstrap

Em `AUTH_MODE=OIDC`, configuração ausente apresenta “Autenticação não configurada neste ambiente” e não abre modo sintético. Após callback válido, o access token ainda não libera a interface: primeiro é chamado `GET /api/v1/identity/me`. Somente resposta 200 cria a sessão e renderiza o shell.

```text
TOKEN VALID + /ME SUCCESS = AUTHENTICATED APPLICATION
401 -> SESSION_EXPIRED -> LOGIN
403 -> FORBIDDEN
NETWORK/5XX -> SAFE ERROR STATE
```

Em `AUTH_MODE=SYNTHETIC`, habilitado explicitamente no arquivo público de development, a UI mostra “AMBIENTE DE DESENVOLVIMENTO” e “DADOS SINTÉTICOS”. O provider sintético nunca produz token ou chama a API.

## Sessão e token

Estados: `BOOTING`, `UNAUTHENTICATED`, `AUTHENTICATING`, `AUTHENTICATED`, `SESSION_EXPIRED`, `FORBIDDEN`, `NETWORK_ERROR` e `SERVER_ERROR`. Access token fica apenas em memória e não aparece no snapshot da UI. O frontend não solicita refresh token; expiração exige nova autenticação. Logout limpa sessão, contexto e transação PKCE. Logout remoto é executado somente se metadata e configuração explícita o permitirem.

## Contexto e navegação

O shell contém sidebar, topbar, conteúdo, escritório/tenant atual, seletor de
empresas autorizadas, competência de trabalho e menu do usuário. Na entrada, o
usuário pode confirmar empresa, competência mensal, quantidade de dias para a
revisão e se o prazo parte da data da importação ou do fim do período. A data da
importação é o padrão seguro para competências históricas. Uma preferência
permite não abrir novamente esse diálogo; o contexto continua acessível no topo
e no menu do usuário.

Somente o ID opaco da empresa, `YYYY-MM`, a opção de abertura e a quantidade de
dias são mantidos localmente. Empresa salva é sempre intersectada com as
empresas retornadas pelo contexto autenticado. Nenhum nome, CNPJ, XML, valor,
token ou permissão é persistido. Essa conveniência preenche formulários, mas
não concede acesso nem cria regra oficial: cada operação envia datas explícitas
e o backend revalida período, bloqueios, `CompanyAccess` e permissões. Cada
empresa traz permissões resolvidas pelo backend; trocar empresa recalcula a
navegação com a projeção daquela empresa. IDs na UI não concedem acesso.
`UI VISIBILITY != SECURITY AUTHORIZATION` permanece regra obrigatória.

Minha Visão, Operação, Fiscal, Financeiro, Contábil, Clientes, Obrigações, Governança e Administração usam o mapa de permissões aprovado. Módulos posteriores permanecem desabilitados ou em placeholder controlado. Agregados reais não foram implementados.

## API e fronteiras

`api-client.js` é a única fonte de chamadas autenticadas do aplicativo e normaliza 401, 403, rede e 5xx. O bootstrap usa `/identity/me`; a rota antiga de contexto continua disponível para operações específicas. Mock e API nunca são misturados por falha automática.

O backend continua responsável por JWT, usuário ativo, Membership, tenant, CompanyAccess, RoleBinding e Permission. CORS não foi enfraquecido. CSP, callbacks e origens do IdP deverão ser gerados/permitidos de forma específica no ambiente homologado; a configuração local atual permanece fechada em `'self'`.

## Responsividade e acessibilidade

Sidebar persistente no desktop e drawer abaixo de 800px. Há link de salto, landmarks, labels, foco visível, `aria-live`, `aria-expanded`, mensagens sem detalhe interno e navegação por teclado. WCAG AA é a fundação; browser e leitor de tela permanecem gates manuais.

## Limites preservados

- nenhum provedor ou callback público foi inventado;
- IDP global revocation e staging permanecem pendentes;
- dados de negócio continuam sintéticos;
- Phase 05, notifications, search e módulos operacionais não foram iniciados;
- site, banco e migrations não foram alterados.

PROTOTYPE_REUSE=PARTIAL. APPLICATION_SHELL=READY_FOR_PRODUCT_INTEGRATION com configuração de produção ainda pendente.
