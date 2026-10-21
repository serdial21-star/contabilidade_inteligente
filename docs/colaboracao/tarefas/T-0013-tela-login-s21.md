# T-0013 — Tela do login S21: erro em destaque e F5 sem cair na ponte (M-115 do Financeiro)

| Campo | Valor |
|---|---|
| Estado | IMPLEMENTADA — aguardando publicação na VPS e conferência do usuário |
| Origem | Publicação da T-0012 em 2026-10-21 (S-035 do Sistema C): Sérgio não viu a mensagem de erro ("os dois se apagam… sem mensagem") e o F5 levou à ponte do S21 Administrativo. Pendência M-115 do C |
| Sistema | Sistema B (só a tela; servidor sem mudança) |
| Exige ADR | não: ajuste de tela dentro do ADR 0021 do B; a marca da aba está registrada abaixo |
| Exige ação do usuário | sim: aprovar ("conforme sua orientação", 2026-10-21) e publicar na VPS (comandos preparados pelo Claude) |

---

## 1. Briefing (Claude)

### Problema

1. O erro do login S21 aparecia no quadro azul "Ambiente controlado", no lugar do texto de sempre, e o formulário era redesenhado vazio (inclusive o e-mail). Parecia que nada tinha acontecido.
2. A tela apagava o `#entrar` do endereço. F5 na tela do login S21, ou dentro do Contábil depois de entrar pelo login S21, caía na re-entrada da ponte (T-0010) e mandava a pessoa ao S21 Administrativo.

### Escopo

1. Erro do login S21 em quadro de erro (`alert error`, `role="alert"`), com título "Não foi possível entrar" (o texto distingue o estado, não só a cor).
2. E-mail digitado mantido no formulário (a senha não); foco no campo da senha depois do erro; ao sair, o e-mail é esquecido.
3. A tela do login S21 mantém `#entrar` no endereço (F5 fica nela).
4. Quem entrou pelo login S21 volta a ele no F5 dentro do Contábil e, depois do código, para a mesma tela (mesma lista de parâmetros da T-0010). Para lembrar sem Web Storage nem passe no navegador, a aba recebe uma marca de texto fixo em `window.name` (`s21-contabil:login-s21`). Chegar com crachá da ponte apaga a marca; sem marca e sem `#entrar`, a re-entrada pela ponte (T-0010) continua igual.

### Fora do escopo

Servidor, regras do passe, ponte do A, Caddy do host (M-116 do C).

## 2. Aprovação

2026-10-21: Sérgio, "conforme sua orientação" (corrigir a M-115 antes da etapa 2 do ADR 0025).

## 3. Resultado (Claude)

- `app/app.js`: `renderLogin(message, tone)` com tom de erro; `s21Email` no formulário; foco na senha; `#entrar` mantido; `S21_TAB_MARK` em `window.name` (gravada ao entrar pelo login S21, apagada na chegada pela ponte); `s21Return` com `safeReturnHash`; "Sair" deixa a tela em `#entrar` e esquece o e-mail.
- Por que `window.name`: sobrevive ao F5 na mesma aba, não é Web Storage, não vai ao servidor e guarda só um texto fixo (nunca passe, e-mail ou dado da pessoa). Os navegadores atuais o apagam em navegação para outro site.
- Testes: `tests/frontend/test_app_shell.py::test_t0013_…` (contrato da tela); pytest sem MariaDB 687/0; node 30/5 (as mesmas 5 falhas antigas listadas na T-0012); verificação em Edge sem interface, com a tela servida do repositório e API/serviço de login simulados: 12/12 (abre e mantém `#entrar`; F5 fica; senha errada → quadro de erro, e-mail mantido, senha vazia, foco na senha; senha certa → código → entra e marca a aba; F5 em `#documents?company=…` → login S21 → volta à mesma tela; Sair → `#entrar`; crachá da ponte apaga a marca; sem marca → ponte; nenhuma exceção).
