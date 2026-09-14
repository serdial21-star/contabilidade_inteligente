# Site comercial — Phase 03

Abra `site/index.html` diretamente no navegador. A página é estática e funciona sem build, instalação, servidor, rede ou backend. `legal.html` contém placeholders jurídicos explícitos.

## Arquitetura

- `index.html`: Home one-page e metadata.
- `marketing.css`: extensão do Design System compartilhado.
- `marketing.js`: menu mobile, ano e simulação local do formulário.
- `legal.html`: Política/Termos pendentes de aprovação.
- `robots.txt`: bloqueio preventivo de indexação pré-publicação.
- `tests/smoke.cjs`: dez smoke tests focados.

O site reutiliza `../ui/tokens.css`, `../ui/foundation.css` e os assets oficiais em `../ui/assets/brand/`. O formulário não possui action, fetch, endpoint ou persistência; CSP bloqueia conexões e envio. Dados e indicadores são sintéticos.

SITE_EXISTING_BASE = REUSE. Classificação da base anterior: `index.html` REUSE/REFINE; `ui/design-system.css` LEGACY para o site e preservado para a prévia histórica; app Phase 02 REUSE como referência visual; assets oficiais REUSE; conteúdo jurídico REVIEW_REQUIRED.

BUILD = NOT_APPLICABLE. MARKETING_SITE_DEPLOYMENT = NOT_AUTHORIZED. Antes de publicar, seguir `docs/MARKETING_SITE_PRE_PUBLISH_CHECKLIST.md`, definir domínio/canonical, substituir bloqueios de indexação e textos jurídicos, escolher o destino do formulário e executar QA visual, screen reader e performance.
