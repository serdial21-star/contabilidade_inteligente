# Marketing Site Specification — Phase 03

Site institucional B2B estático em `site/index.html`, com página jurídica placeholder em `site/legal.html`. SITE_EXISTING_BASE = REUSE: a one-page anterior, sua linguagem operacional e caminhos locais foram refinados no mesmo arquivo. Arquivos úteis das Phases 01/02 foram preservados. MARKETING_SITE_DEPLOYMENT = NOT_AUTHORIZED.

## Posicionamento, audiência e arquitetura

Serdial21 Contabilidade Inteligente é uma plataforma de inteligência operacional para escritórios contábeis brasileiros. Comprador principal: sócio, proprietário ou gestor. Usuários: contadores, analistas contábeis/fiscais, financeiro, gestores e equipe administrativa. Mensagem central: automação aumenta capacidade; revisão e decisão permanecem com o profissional.

Arquitetura one-page: Home/hero → problema → solução/fluxo → seis famílias → contabilidade inteligente → automação versus decisão → Minha Visão/Fila Inteligente → Linha da Decisão → segurança/AccountLock → público/benefícios → sobre → demonstração. Header usa anchors; footer conecta seções e `legal.html`. Copy e classificação: [MARKETING_COPY](MARKETING_COPY.md).

## Linguagem visual e conteúdo

DESIGN SYSTEM REUSE = PASS. `ui/tokens.css` e `ui/foundation.css` fornecem cores, tipografia, espaçamento, botões, inputs, foco e reduced motion; `site/marketing.css` estende composição e narrativa sem duplicar tokens institucionais. Azul estrutura hero/navegação; ouro destaca inteligência; vermelho tem uso estratégico; verde/âmbar mantêm aprovação/revisão.

Manrope/Inter são declaradas com fallback Segoe UI/Arial, sem download externo. A alternância entre mockup operacional no hero, fluxo modular e Linha da Decisão em fundo azul mantém a aparência do app. Motion é um reveal único desativado por reduced motion. Nenhuma foto genérica ou ilustração externa.

Os mockups são HTML sem dados reais: Minha Visão, Fila Inteligente, proposta e Linha da Decisão usam Empresa Alfa/Beta, contas/regras sintéticas e avisos. A marca usa somente os PNG oficiais em `ui/assets/brand/`.

## CTA, formulário e analytics

Hero: Conhecer a plataforma e Solicitar demonstração. Navegação e CTA final levam ao formulário. DEMO_FORM_DELIVERY = DEFERRED: sem `action`, fetch, endpoint, banco ou CRM; CSP bloqueia conexão/form submission. A validação local exige campos essenciais e ciência de que nada será transmitido, exibe sucesso e limpa o formulário.

ANALYTICS_INTEGRATION = DEFERRED; não há script ou cookie. Eventos futuros documentados: `page_view`, `cta_demo_click`, `platform_section_view`, `demo_form_start`, `demo_form_submit`.

## SEO e structured data

Title/description específicos; headings/landmarks; Open Graph e Twitter textuais; favicon oficial; JSON-LD `SoftwareApplication` com provider `Organization`, sem preço, rating, clientes, reviews ou awards. Canonical depende do domínio aprovado e está ausente. Social image não foi solicitada. `robots.txt` e meta robots usam noindex/disallow como proteção pré-publicação; sitemap depende do URL canônico. Alterar apenas no gate de lançamento.

## Acessibilidade e responsividade

HTML semântico, skip link, labels, alt/dimensões de imagens, `aria-live`, menu com `aria-expanded`/`aria-controls`, foco visível e informação além de cor. Breakpoints 1050/800/480px. No mobile: menu expansível, grids em coluna, fluxo vertical e CTAs em largura útil. FOUNDATION READY não é certificação WCAG; browser e leitor de tela são gates manuais.

## Performance, segurança e privacidade

HTML/CSS/JS nativos, sem framework, CDN, analytics, fonte, API ou dependência nova. JavaScript cobre menu, ano e simulação. Imagens têm dimensões; os PNGs oficiais somam cerca de 4,1 MiB e foram preservados. Derivados web otimizados, revisados e sem substituir originais são recomendação pré-publicação.

CSP local fecha conexões e envio; paths são relativos. Secret scanner cobre tracked/untracked não ignorados. LEGAL_CONTENT = PENDING_LEGAL_APPROVAL: `legal.html` é placeholder explícito. Não há endereço, telefone, CNPJ ou e-mail institucional inventado.

Antes de publicar: aprovar conteúdo/marca/legal/privacidade/destino do formulário, canonical/indexação/sitemap, domínio/DNS/HTTPS, visual QA, screen reader, performance, secrets e links. APPLICATION EXTERNAL EXPOSURE = NO_GO continua inalterado. [Checklist](MARKETING_SITE_PRE_PUBLISH_CHECKLIST.md).

## Validação

`site/tests/smoke.cjs` contém dez verificações: estrutura, hero/CTAs, assets, navegação/seções, links, claims, paths/segredos, formulário/legal, SEO/structured data e responsividade/sintaxe JS. Build = NOT_APPLICABLE. Nenhum backend, migration, banco ou contrato foi alterado.
