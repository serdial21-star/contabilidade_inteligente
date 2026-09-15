# Integration Risk Register

| ID | Sistema | Descrição | Evidência | Severidade | Probabilidade | Impacto na integração | Mitigação | Bloqueia MVP? | Owner |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| R-01 | A | Endpoints v1/v2/v3/v5 e namespaces conflitantes | 3 dossiês | Alta | Alta | contrato quebra/rota errada | inventário runtime + freeze dedicado | Sim | Owner A |
| R-02 | A | Kanban pode retornar sucesso sem persistir | dossiê recente | Alta | Alta | tarefas perdidas/falso sucesso | corrigir, teste write/read/idempotência | Wave 4 | A Operations |
| R-03 | A | Upload admin→cliente ausente | dossiê recente | Alta | Alta | publicação impossível | contrato/implementação auditada | Wave 6 | A Documents |
| R-04 | A | Rotas cliente sem guards/fallback permissivo | dossiê técnico | Crítica | Média | exposição de produção | fail-closed e testes negativos | Produção, não protocolo HOM | A Security |
| R-05 | A | Tokens browser localStorage/logout sem revogação | dossiês | Alta | Alta | sequestro de sessão; tentação de reuso | hardening separado; proibir em M2M | Produção | A Security |
| R-06 | A | CORS incompleto | dossiês | Média | Média | UX Portal/Admin falha | allowlist testada | Não M2M; sim portal prod | A Frontend/Platform |
| R-07 | A | Auditoria e E2E não comprovados | dossiês | Alta | Alta | efeitos não demonstráveis | audit trail e suíte HOM | Sim para piloto | A QA/Operations |
| R-08 | A/B | Sem credenciais externas M2M | dossiê/repo | Crítica | Alta | conexão insegura/inviável | HMAC, scopes, rotation, secrets | Sim | Security A+B |
| R-09 | B | Referência externa genérica ausente | inspeção repo | Alta | Alta | vínculo errado/duplicado | mapping tenant-aware + revisão | Sim | B Master Data |
| R-10 | A/B | CNPJ tratado como ID único imutável | risco arquitetural | Alta | Média | matriz/filial/correção errada | CNPJ + external ref; não FK | Sim | Architecture |
| R-11 | A/B | Drive mutável/credencial vazada ou SSRF | ownership documentado | Crítica | Média | exfiltração/evidência não reproduzível | URL curta, allowlist, hash, storage B | Sim | Documents/Security |
| R-12 | Hub | n8n virar regra/autoridade | arquitetura proposta | Alta | Média | domínio duplicado e bypass | Hub apenas orquestra; consumidor autoriza | Sim | Integration Architecture |
| R-13 | Hub/A/B | At-least-once sem inbox/outbox/idempotência | capacidade não comprovada | Crítica | Alta | perda/duplicidade contábil | IDs estáveis, hash, DLQ/reconciliação | Sim | Platform/Domain owners |
| R-14 | B | Service principal escapar tenant/company | auth atual é user-centric | Crítica | Média | cross-tenant | scopes, mapping e testes negativos | Sim | B Security |
| R-15 | A/B | Status unificados indevidamente | vocabulários distintos | Média | Média | tarefa muda decisão contábil | mapeamentos semânticos mínimos | Sim Wave 4 | Domain owners |
| R-16 | A/B | Logs/eventos carregarem XML/OFX/PII | dados sensíveis nos fluxos | Alta | Média | incidente LGPD | minimização/redação/retention | Sim real data | Privacy/Security |
| R-17 | A/B | Exclusão/desativação propagada destrutivamente | soft delete A e legal hold B | Crítica | Baixa | perda de evidência | `CLIENT_DISABLED`; workflow privacy futuro | Sim real data | Privacy/Legal |
| R-18 | Ambientes | PROD conectado a DEV ou segredo reutilizado | topologia ainda não montada | Crítica | Média | vazamento/corrupção | homologações e secrets separados | Sim | Platform |
| R-19 | B | IdP produção, upload/download genérico e Domínio pendentes | docs repo | Alta | Média | exposição/fluxos parciais | gates existentes; Domínio fora do MVP | Parcial | Owners B |
| R-20 | Produto | Core B acoplado a Serdial21/n8n/Drive | risco estratégico | Alta | Média | produto não vendável a terceiros | port canônico + connector A | Sim | Product Architecture |
| R-21 | Dossiês | `drive_folder_id` vs `id_pasta_raiz`; sessões e tasks com tabelas divergentes | fontes conflitantes | Alta | Alta | adapter usa schema incorreto | verificar schema HOM; nunca DB direto | Sim freeze | Owner A |
| R-22 | Dossiês | impostos, equipe e portal têm rotas/nomenclaturas incompatíveis | fontes conflitantes | Média | Alta | later integrations frágeis | APIs dedicadas versionadas | Não MVP-1..5 | Owner A |

O risco residual é incompatível com conexão runtime imediata, mas compatível com `CONDITIONAL_GO` para planejamento e estabilização. Nenhum risco é aceito silenciosamente: owners devem ser nomeados como pessoas/equipes no início da Wave 0.
