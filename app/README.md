# Aplicativo web

## Contábil — Phase 08

`accounting-service.js` seleciona provider API ou sintético. A rota `#accounting` oferece propostas/revisão; `#accounting?view=rules` oferece catálogo publicado read-only quando `catalog.review` estiver presente. Decisões exigem confirmação e usam os comandos reais de review; `423` é apresentado como bloqueio. O frontend não recalcula balanceamento e não oferece posting/exportação.

A entrada atual é [index.html](index.html), com o shell autenticado, Minha Visão, Empresas/Documentos e os módulos Fiscal NF-e e Financeiro OFX. Abra-a por servidor estático local. A configuração versionada habilita explicitamente o modo sintético; não autentica nem chama a API. O cliente OIDC Authorization Code + PKCE e o bootstrap por `/api/v1/identity/me` estão implementados, mas o provedor e seus valores públicos permanecem pendentes de homologação. Consulte [MY_VIEW_SPEC](../docs/MY_VIEW_SPEC.md), [FISCAL_MODULE_SPEC](../docs/FISCAL_MODULE_SPEC.md), [FINANCIAL_MODULE_SPEC](../docs/FINANCIAL_MODULE_SPEC.md) e [OIDC_CONFIGURATION](../docs/OIDC_CONFIGURATION.md).

Arquitetura nativa: `config.js` (configuração pública), `core.js` (sessão), `oidc-client.js` (OIDC/PKCE), `api-client.js` (rede centralizada), `mock-provider.js` (fonte sintética), `dashboard-service.js` (Minha Visão), `operational-service.js` (Empresas/Documentos), `intelligence-service.js` (Fiscal/Financeiro) e `app.js` (bootstrap/shell). Nenhuma senha é recebida. O access token permanece somente em memória; `sessionStorage` guarda apenas state/verifier PKCE efêmeros e os remove no callback. `localStorage` contém somente preset, IDs, ordem e tamanho de widgets, sempre revalidados contra a permissão atual.

Testes focados:

```text
node --test app/tests/shell-smoke.cjs
node --test app/tests/dashboard-smoke.cjs
node --test app/tests/operational-smoke.cjs
node --test app/tests/intelligence-smoke.cjs
```

No modo sintético, use **Abrir demonstração sintética**. A Minha Visão permite alternar entre as empresas fictícias autorizadas, selecionar `Todas as empresas autorizadas`, aplicar cinco presets, atualizar sob demanda e personalizar widgets. A primeira empresa fictícia demonstra NF-e/OFX e feedback sintético explícito; nenhum arquivo é enviado ou persistido. Conciliação, matching e workflow contábil permanecem indisponíveis.

## Protótipo preservado da Phase 02

Abra [prototype.html](prototype.html) diretamente no navegador. Não requer build, servidor, instalação, credenciais ou dados reais. O arquivo `dashboard.js` permanece como parte da prévia histórica anterior.

| Tela | Endereço local |
| --- | --- |
| Login UX | `prototype.html#login` |
| Minha Visão | `prototype.html#dashboard` |
| Documentos / caixa de entrada | `prototype.html#documents` |
| Propostas contábeis | `prototype.html#proposals` |
| Revisão | `prototype.html#review` |
| Linha da Decisão | `prototype.html#timeline` |
| Personalização | `prototype.html#settings` |
| Biblioteca de componentes | `prototype.html#components` |

Em Minha Visão, Personalizar habilita adicionar, remover, mover por botões e redimensionar widgets. Os cinco presets só organizam widgets. Salvar visão mantém uma cópia em memória; recarregar descarta tudo. Em Documentos, use pesquisa/status/filtros avançados, seleção, ordenação e paginação. DOC-001 demonstra confirmação de decisão; DOC-002 demonstra ausência de regra; DOC-003 demonstra AccountLock; DOC-004 tem histórico humano fictício. OFX não ganha uma jornada contábil NF-e fictícia.

Login e upload estão desabilitados. As confirmações de revisão não alteram os mocks, não criam AuditEvent e não chamam API. Nenhuma decisão ou credencial é persistida. As imagens oficiais foram copiadas sem edição; o site anterior não foi alterado.

Fontes declaradas: Inter (UI) e Manrope (títulos), com fallback Segoe UI/Arial. Não há downloads/CDN/fontes empacotadas: sem instalação local dessas famílias, o navegador usa fallback. Ver [especificação](../docs/DESIGN_SYSTEM_SPEC.md).

Smoke tests sem dependências, quando Node 18+ estiver disponível:

```text
node --test app/tests/smoke.cjs
```

Nesta sessão, os seis callbacks foram executados pelo runtime Node disponível via ferramenta, usando os mesmos arquivos e assertions. São smoke tests de renderização/string e eventos com DOM mínimo simulado: não substituem navegador, layout, leitor de tela ou E2E. BUILD = NOT_APPLICABLE.
