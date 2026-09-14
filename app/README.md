# Protótipos da Phase 02

Abra [prototype.html](prototype.html) diretamente no navegador. Não requer build, servidor, instalação, credenciais ou dados reais. A entrada anterior `index.html` e seu `dashboard.js` foram preservados como prévia histórica.

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
