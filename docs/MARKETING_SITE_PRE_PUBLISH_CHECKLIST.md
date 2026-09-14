# Marketing Site — Pre-publish Checklist

Nenhum item humano/externo é aprovado pela Phase 03. MARKETING_SITE_DEPLOYMENT = NOT_AUTHORIZED.

| Gate | Estado atual | Evidência / ação antes de publicar |
| --- | --- | --- |
| Brand approval | PENDING_HUMAN_APPROVAL | Conferir uso/proporção dos PNGs e consistência com a prancha. |
| Copy approval | PENDING_HUMAN_APPROVAL | Revisar [copy](MARKETING_COPY.md), especialmente REVIEW_RECOMMENDED. |
| Desktop visual QA | MANUAL_PRE_PUBLISH_GATE | Verificar 1440/1280px, hero, mockups, ritmo e footer. |
| Tablet/mobile visual QA | MANUAL_PRE_PUBLISH_GATE | Verificar 800/390/320px, menu, fluxo, formulário e overflow. |
| Screen-reader review | MANUAL_PRE_PUBLISH_GATE | Testar landmarks, headings, menu, imagens, formulário e status. |
| Accessibility review | PENDING_REVIEW | Teclado, foco, zoom 200%, reflow, contraste e mensagens. |
| Legal content | PENDING_LEGAL_APPROVAL | Substituir placeholders por Política e Termos aprovados. |
| Privacy review | PENDING_LEGAL_APPROVAL | Aprovar campos, finalidade, base, retenção, contato e fornecedores. |
| Demo form destination | DEFERRED | Escolher destino público aprovado e contrato; remover simulação somente depois. |
| SEO metadata | FOUNDATION_READY | Aprovar metadata; definir canonical e indexação. |
| Favicon | READY_FOR_REVIEW | Asset oficial simplificado referenciado sem alteração. |
| Social preview image | NOT_REQUESTED | Criar apenas com autorização específica. |
| Analytics decision | DEFERRED | Decidir necessidade, fornecedor e consentimento. |
| Cookies | NONE | Manter ausentes ou aprovar política antes de instalar tracking. |
| Domain / DNS | PENDING | Definir domínio; alteração externa não autorizada. |
| HTTPS/HSTS | PENDING_EXTERNAL_INFRASTRUCTURE | Validar certificado, redirect, hosts e HSTS. |
| robots/indexing | BLOCKED_FOR_LAUNCH | Atualmente `noindex,nofollow` e `Disallow: /`; revisar no gate de publicação. |
| Sitemap | PENDING_CANONICAL_DOMAIN | Gerar com URLs aprovadas. |
| Secret scan | READY_FOR_LOCAL_CHECK | Executar scanner existente em cada candidato. |
| Broken links | READY_FOR_LOCAL_CHECK | Smoke testa anchors, páginas e assets; repetir no artefato final. |
| Performance review | PENDING_REVIEW | Medir; criar derivados otimizados dos PNGs sem alterar originais. |
| Browser compatibility | MANUAL_PRE_PUBLISH_GATE | Chrome/Edge/Firefox/Safari conforme matriz futura. |
| Claims/product availability | PENDING_HUMAN_APPROVAL | Confirmar capacidades e estágio no momento da publicação. |
| Domínio ERP claim | BLOCKED_FOR_HOMOLOGATION | Não adicionar integração, exportação, parceria ou logo Domínio. |
| Marketing deployment | NOT_AUTHORIZED | Exige decisão explícita após os gates aplicáveis. |

Sequência: fechar conteúdo/jurídico → definir formulário/analytics → otimizar assets → configurar domínio/canonical/sitemap → QA visual/acessibilidade/performance → secret/link scan → revisar HTTPS → decisão formal. Nenhuma etapa executa migration 0012 ou expõe o aplicativo operacional.
