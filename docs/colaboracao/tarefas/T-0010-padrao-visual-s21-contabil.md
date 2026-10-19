# T-0010 — S21 Contábil no padrão visual S21 (marca, menu, temas claro e escuro)

| Campo | Valor |
|---|---|
| Estado | IMPLEMENTADA — aguardando publicação |
| Origem | Pedido do usuário em 2026-10-19 ("logo marca do contábil está errada"; "padrão do menu … padronizar todos"; tema claro e escuro); decisão D-093 do Sistema C (marca e paleta oficiais) e `Serdial-Financeiro/Docs/painel-sp/PADRAO-VISUAL-S21.md` |
| Sistema | Sistema B |
| Exige ADR | não (só apresentação; nenhum contrato, rota, dado ou permissão muda) |
| Exige ação do usuário | sim: aprovar; depois, publicar na VPS (comandos preparados pelo Claude) |

---

## 1. Briefing (Claude)

### [2026-10-19] Claude — Briefing

#### Problema

1. **Marca errada e nome antigo visível.** O app usa `S21 assinatura principal.png` (S21 | SERDIAL21 · CONTABILIDADE INTELIGENTE) na barra lateral (`app/app.js:751`), `S21 assinatura vertical.png` no login (`app/app.js:142`) e textos "Serdial21 Contabilidade Inteligente" / "Aplicativo Serdial21" / "Serdial21" visíveis (`app/index.html:9,30`; `app/app.js:163,724,751` rodapé). D-093 do C: o produto se chama **S21 Contábil**, com o selo `s21_contabil.jpg`; nenhum "Serdial21" visível.
2. **Paleta diferente da oficial.** `ui/tokens.css` usa `--brand-primary:#17295b`, `--brand-gold:#daa84f`, `--brand-red:#d8232a`. Oficial (D-093): marinho **#09265B**, dourado **#D6A928**, vermelho **#C8102E**.
3. **Sem tema escuro.** `app/index.html:6` declara `color-scheme: light`; não há tokens escuros nem botão.
4. **Menu diferente dos outros S21.** Os outros sistemas têm: selo com nome no alto, menu marinho, item ativo com barra dourada, rodapé com usuário, botão de tema e "Sair" em vermelho; nenhuma marca na barra de cima.

#### Escopo

**Dentro (só `app/` e `ui/`, aplicativo autenticado `app/index.html` + `app/app.js` + `app/app-shell.css`):**

1. **Ativos:** copiar byte a byte, com SHA-256 conferido e registrado em `ui/assets/brand/README.md`, a partir de `C:\Projetos\S21-Site-pacote\assets\identidade\`: `s21_contabil.jpg` (selo com nome) e `logo.jpg` (selo mestre). Sem recorte, recoloração ou otimização. Os arquivos antigos **ficam** (o teste `test_prototype_brand_assets_and_required_specs_are_preserved` e o protótipo os usam).
2. **Uso:** menu aberto e tela de login → selo com nome; menu recolhido, tela de carregamento e favicon → selo mestre. Proporção original (`width` + `height:auto`).
3. **Textos visíveis:** "Serdial21 Contabilidade Inteligente", "Aplicativo Serdial21" e o `alt="Serdial21"` → "S21 Contábil" (título da aba: "S21 Contábil"). Rodapé: "S21 Contábil · A automação prepara. O profissional decide." **Não mudar:** nomes de tenant e de empresa (são dados), identificadores internos, `S21Core`, domínio.
4. **Paleta:** trocar os três tokens de marca pelos oficiais; conferir contraste AA dos pares texto/fundo afetados (registrar no relatório).
5. **Tema escuro:** tokens escuros sob `html[data-theme="dark"]`; botão "Tema escuro" / "Tema claro" no rodapé do menu; preferência guardada em `localStorage` (com `try/catch`, sem quebrar se o armazenamento falhar); primeira visita segue `prefers-color-scheme`. `color-scheme` passa a `light dark`.
6. **Menu:** fundo marinho, texto branco, item ativo com fundo mais claro **e** barra dourada à esquerda; rodapé na ordem: usuário · papel, botão de tema, "Sair" em vermelho com ícone (hoje "Sair" está dentro do popover do perfil: trazê-lo para o rodapé, mantendo o popover para "Contexto e preferências"). Barra de cima sem marca.

**Fora:** protótipo (`app/foundation.js`, `prototype.html`, `mocks.js`), `site/`, API, rotas, permissões, login/ponte OIDC, CSP (exceto o necessário para nada — nenhuma origem nova), backend.

#### Critérios de aceite

- Nenhum texto visível "Serdial21" no aplicativo autenticado, salvo dados (nome de tenant/empresa).
- Login, menu aberto/recolhido e carregamento com os selos corretos, sem distorção.
- Temas claro e escuro com contraste AA; escolha persiste após recarregar.
- `pytest tests/frontend` e `node app/tests/*.cjs` aprovados; testes novos: favicon/selo mestre, ausência de "Serdial21" visível em `index.html`/`app.js` (exceto dados), presença do botão de tema e do `data-theme`.
- CSP de `app/index.html` inalterada.

#### Publicação (depois do aceite)

Só a imagem `web` muda. Roteiro a preparar pelo Claude: atualizar o código em `/opt/serdial21-b` na VPS `187.127.63.78`, construir a imagem `web` com tag nova, reaproveitar a imagem `api:229271b` com a mesma tag nova, `docker compose up -d web`, conferir. Volta: tag anterior. Antes: o repositório B tem 2 commits locais não enviados (`daa6025`, `b3bf950`) e arquivos não rastreados do usuário — preservar.

---

### [2026-10-19] Usuário — Aprovação

"Aprovo, Claude implementa" (Codex sem crédito; implementação pelo Claude, registrada aqui).

## 2. Resultado (Claude)

### [2026-10-19] Claude — Implementação

**Criados:** `app/theme.js`; `ui/assets/brand/S21 Contabil selo.png` e `ui/assets/brand/S21 selo mestre.png` (cópias byte a byte; SHA-256 no README dos ativos; os originais `.jpg` são PNG).
**Alterados:** `app/index.html` (título "S21 Contábil", favicon com o selo com nome, `color-scheme: light dark`, `theme.js` no `<head>`, selo mestre no carregamento; **CSP inalterada**); `app/app.js` (selos no login, no menu aberto/recolhido e nos estados; "S21 Contábil" no lugar de "Serdial21"; "S21 Administrativo" no lugar de "Sistema A" nas mensagens da ponte; botão de tema e "Sair" no rodapé do menu — "Sair" saiu do popover do perfil, que mantém "Contexto e preferências"; ação `toggle-theme` com anúncio acessível); `app/app-shell.css` (tamanho dos selos, botões do rodapé, ajustes do tema escuro); `ui/tokens.css` (paleta oficial #09265b/#d6a928/#c8102e, `--sidebar-bg`, tokens do tema escuro); `ui/foundation.css` (menu e login com `--sidebar-bg`; textos de 10 px passaram a 12 px; itens do menu de 13 para 15 px); `ui/assets/brand/README.md`; `tests/frontend/test_app_shell.py` (3 testes novos).
**Fora do escopo, intocados:** protótipo, `site/`, API, ponte, permissões, CSP, backend. Nomes de tenant/empresa continuam (são dados).
**Tema:** preferência só no `localStorage` (`s21.theme`), com `try/catch`; primeira visita segue `prefers-color-scheme`.

**Testes:**
- `pytest tests/frontend`: **82 aprovados**, 0 falhas.
- `node app/tests/*.cjs`: 5 subtestes falham **antes e depois** da tarefa (conferido em cópia limpa do HEAD `b3bf950`): dashboard 1 e 2, intelligence 2, operational 1, shell 11 (falha em "Clientes"). Pré-existentes, não causados pela T-0010; o shell 11 continua exigindo "Sair do aplicativo", presente no `title` do botão novo. Pendência registrada para o projeto B.
- Conferência visual (Edge sem interface, modo de demonstração sintético, servidor local): login, menu aberto, rodapé com usuário · papel, "Tema escuro" e "Sair" em vermelho, nos temas claro e escuro.
- Suíte completa do backend não rodada (nenhum arquivo do backend mudou).

**Riscos/limitações:** os selos têm ~1,1 MB cada e o `/app` e `/ui` usam `Cache-Control: no-store` (baixados a cada carga); otimizar exige derivado revisado (README dos ativos). Contraste AA conferido nas combinações principais (branco sobre #09265b ≈ 13:1; #09265b sobre #d6a928 ≈ 6,5:1; branco sobre #c8102e ≈ 5,9:1; tema escuro: #e6ebf5 sobre #111d33 ≈ 14:1).
