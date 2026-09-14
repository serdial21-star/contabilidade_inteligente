# Minha Visão — Phase 05

## Propósito e limite

`Minha Visão` é a home operacional da aplicação autenticada. Ela prioriza o que aconteceu, o que exige atenção e qual é o próximo passo possível. A implementação reutiliza o shell, a identidade oficial e o Design System das Phases 02 e 04; não cria módulos Fiscal, Financeiro ou Contábil completos.

Nesta fase, `DATA_MODE=SYNTHETIC`. Os números e itens exibidos são fixtures explícitas e separadas por empresa fictícia. Nenhum dado real, escrita contábil, aprovação, upload, notificação ou exposição externa foi habilitado.

## Experiência

Após o bootstrap de identidade, tenant, empresas autorizadas e permissões, a rota padrão `#overview` apresenta:

- saudação com o nome de exibição e o escritório;
- empresa atual ou `Todas as empresas autorizadas`;
- atualização manual, sem polling;
- seletor entre cinco presets de apresentação;
- grade de widgets orientados a ação;
- personalização acessível por controles de adicionar, remover, mover e redimensionar;
- informação de atualização e indicação explícita da fonte sintética.

Os CTAs cujo destino operacional ainda não existe permanecem desabilitados e explicam o motivo. Não há navegação falsa.

## Presets

`Visão Executiva`, `Visão Contábil`, `Visão Fiscal`, `Visão Operacional` e `Minha Visão` apenas organizam o layout. Antes de renderizar, o conteúdo do preset é intersectado com o catálogo autorizado. Preset e preferência nunca concedem permissão.

## Catálogo e autorização

O catálogo possui dez widgets, W001–W010, descritos em [DASHBOARD_DATA_MAP.md](DASHBOARD_DATA_MAP.md). Cada item declara uma ou mais permissões exatas. `VISIBILITY <= AUTHORIZATION`: um widget não autorizado é removido antes de consultar o provider e não é renderizado.

Para uma empresa específica, a UI combina permissões tenant-wide com as permissões projetadas para aquela empresa. Em `Todas as empresas autorizadas`, permissões empresariais precisam estar presentes em todas as empresas selecionadas; permissões tenant-wide continuam válidas. Essa escolha conservadora impede que uma agregação amplie visibilidade.

O backend permanece autoridade. A lista de empresas vem exclusivamente de `GET /api/v1/identity/me`; não existe entrada livre de `company_id`.

## Dados e contratos

`dashboard-service.js` centraliza `loadSummary()` e `loadWidget()`. Widgets não fazem `fetch` diretamente. Em modo sintético, o provider usa somente as empresas autorizadas do contexto atual. No futuro modo API, são reutilizados apenas contratos read-only existentes:

- `GET /api/v1/operations/companies/{company_id}/reviews`;
- `GET /api/v1/operations/companies/{company_id}/exceptions`;
- `GET /api/v1/operations/companies/{company_id}/audit-events`.

A atividade recente projeta apenas ação, módulo e horário retornados pelo contrato seguro; não lê `before_state`, `after_state`, motivo ou payload bruto. Fontes inexistentes retornam indisponibilidade explícita, nunca um total artificial em resposta real.

## Estados e falhas

Cada widget suporta `LOADING`, `READY`, `EMPTY`, `ERROR`, `FORBIDDEN` e `UNAVAILABLE`. `loadSummary()` captura falhas individualmente: um erro não remove os demais widgets. `401` continua acionando o fluxo de sessão expirada da Phase 04; `403` não apresenta conteúdo nem detalhe protegido.

Ao trocar empresa, a geração de requisição é invalidada, o modelo anterior é descartado e o novo contexto é carregado. Respostas atrasadas não podem repor dados do contexto anterior.

## Preferências

`DASHBOARD_PREFERENCES_PERSISTENCE=LOCAL_ONLY`. O navegador armazena somente `preset`, IDs/ordem dos widgets e IDs de widgets ampliados. Antes do uso, os valores são validados contra o catálogo e as permissões atuais. Não são armazenados dados contábeis, valores financeiros, documentos, token, permissões, tenant ou empresa.

Persistência server-side exigiria um contrato e possivelmente migration; por isso permanece `BACKEND_GAP`, sem migration nesta fase.

## Responsividade e acessibilidade

A grade usa três colunas no desktop, duas no tablet e uma em telas menores. Widgets ampliados voltam a uma coluna no mobile. A personalização usa `dialog` nativo, checkboxes e botões nomeados; arrastar não é obrigatório. Há headings por widget, região com `aria-busy`, anúncio de atualização, foco visível, estados em texto e suporte a redução de movimento herdado da foundation.

Browser visual QA e leitor de tela permanecem gate manual quando o navegador automatizado não está disponível. A fundação de código não equivale a certificação WCAG.

## Gaps conhecidos

- agregados de documentos, processamento e empresas com pendência precisam de projeção read-only eficiente antes de `DATA_MODE=API` completo;
- obrigações não possuem fonte de domínio aprovada;
- conciliação possui domínio, mas não possui contrato de consulta operacional para o dashboard;
- persistência server-side de preferências está adiada;
- destinos dos CTAs pertencem às fases dos módulos operacionais;
- IdP de produção, exposição externa, migration 0012 e exportação Domínio permanecem bloqueados pelos gates existentes.

## Decisão técnica

Foi escolhido um serviço frontend central com providers sintético/API porque o repositório já possui um frontend nativo, um cliente HTTP único e contratos read-only parciais. Nenhum endpoint monolítico, nova consulta SQL, dependência estrutural ou migration foi criado. A escolha preserva a arquitetura atual e permite integrar agregados reais posteriormente sem acoplar widgets ao transporte.
