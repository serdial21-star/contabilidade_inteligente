# T-0011 — Entrada no S21 Contábil só para quem é cadastrado nele (M-111)

| Campo | Valor |
|---|---|
| Estado | CONCLUÍDA — teste automático acrescentado em 2026-10-20 (sem mudança de comportamento; nada a publicar) |
| Origem | M-111 do Sistema C; decisão D-099 do Sistema C (Sérgio, 2026-10-20 17:21): "Só quem é cadastrado" |
| Sistema | Sistema B |
| Exige ADR | não (confirma a regra já vigente do ADR 0014; nenhum contrato, rota, dado ou permissão muda) |
| Exige ação do usuário | não |

## Problema

Segundo o Lovable (pedido A-01, 2026-10-19), a ponte de login do portal (Sistema A) confere só "funcionário ativo", não "administrador"; o menu do portal esconde o item dos não administradores. A tela não é proteção: a pergunta era se um funcionário comum, com um token válido da ponte, entra no S21 Contábil.

## Achado (Claude, 2026-10-20 17:21)

Não entra. O servidor do B só aceita identidade **vinculada** a um usuário cadastrado no próprio B (`IdentityContextService.principal` → `IdentityNotLinkedError` → 403 `access denied`, em `src/serdial21/entrypoints/http/dependencies/identity.py`). O cadastro é feito por `scripts/bootstrap_user_access.py`, só por nós. Faltava um teste que provasse isso para o caso da ponte.

## Feito

- `tests/api/test_identity_security.py::test_valid_portal_token_without_registration_in_b_is_denied`: token com emissor, audiência e assinatura corretos, de funcionário sem cadastro no B → 403 `access denied` em `/api/v1/identity/me` e `/api/v1/identity/context`.
- Resultado: `tests/api/test_identity_security.py` 22/0.

## Regra (D-099)

Entra no S21 Contábil só quem é cadastrado nele. Para dar acesso a alguém, o cadastro é feito no B (comando de provisionamento); o menu do portal continua visível só para administradores, mas não é a proteção.
