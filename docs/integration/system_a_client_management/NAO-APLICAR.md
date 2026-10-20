# NÃO APLICAR — substituído pelo login único S21

**Registrado em:** 2026-10-20 17:41, por Claude Code. **Decisão:** D-100 do Sistema C (ADR 0025 do Financeiro, "login único S21", aceito por Sérgio).

Os procedimentos desta pasta gravam a senha do Sistema A como `SHA2(senha, 256)` sem sal (ex.: `system_a_admin_password_recovery/001_up.sql:265`, `sp_admin_password_reset_apply`). Esse formato é fraco (OWASP Password Storage Cheat Sheet; achado F2 do painel `Serdial-Financeiro/Docs/painel-login-a/rodada-1/L1-seguranca.md`).

Com o ADR 0025, o login da equipe e dos clientes do Sistema A passa para o provedor de login único S21 (Supabase do Financeiro, bcrypt, código no celular), e a redefinição de senha passa a ser a dele. **Não aplicar estes arquivos na produção.** Se já tiverem sido aplicados, avisar o Claude: o login antigo será desligado na etapa 3 do ADR 0025.

Ficam no repositório só como histórico e referência (geração de token com `RANDOM_BYTES`, prazo e tentativas).
