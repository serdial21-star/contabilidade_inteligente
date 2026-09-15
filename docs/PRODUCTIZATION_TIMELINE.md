# Productization Timeline

Horizonte aproximado de 16 semanas, contado do início de productização a ser organizado pelo projeto. É planejamento, não promessa fixa nem autorização de execução. Capacidade da equipe, aprovações humanas e dependências externas podem deslocar datas. [Roadmap](PRODUCTIZATION_ROADMAP.md) define gates; [backlog](PRODUCT_BACKLOG.md) define trabalho.

| Janela | Frente | Fases relacionadas | Dependência / saída esperada |
| --- | --- | --- | --- |
| Weeks 1–2 | Baseline / architecture | 01 | Inventário, RC documental, ambientes e planejamento. |
| Weeks 1–4 | Design System / UX | 02 | Baseline utilizável e identidade/UX revisadas. |
| Weeks 2–6 | Marketing site | 03 | Brief/tokens; publicação aguarda gates externos/jurídicos. |
| Weeks 3–10 | Web application | 04–09 | Shell antes das telas; contratos reais e permissões em cada entrega. |
| Gate relativo | Integration readiness | 09A | Auditoria documental, ownership e arquitetura; concluída sem conexão runtime. |
| Após contract freeze | Portal & Operations Integration | 10 | Reuso do portal A, jornadas e contratos; depende da estabilização Wave 0. |
| Após Phase 10 | Connect Hub MVP em homologação | 10A | Waves 1–5; estimativa relativa XL, sem compromisso de datas. |
| Weeks 2–10 | Security | 11 | Infraestrutura/IdP aprovados; sete gates externos com evidências. |
| Weeks 5–9 | Observability / privacy | 12–13 | Coleta, recuperação e procedimentos; aprovações podem ultrapassar a janela. |
| Janela a replanejar | Integrations | 09A, 10, 10A, 11–12 | A HOM ↔ Hub HOM ↔ B HOM; duração depende dos P0 do Sistema A. Domínio segue bloqueado. |
| Weeks 10–13 | QA / UAT | 14 | Produto integrado, testes críticos e signoff profissional. |
| Weeks 13–15 | Controlled pilot | 15 | Seis gates real data e gates externos aplicáveis aprovados. |
| Weeks 14–16 | Commercial readiness | 16 | Resultados do piloto, suporte, onboarding e termos. |
| Week 16 | Launch readiness gate | 16 | Decisão formal GO/NO_GO; não publicação automática. |

As fases são pacotes de trabalho, não uma fase por semana. Preparação de frentes pode se sobrepor; testes e autorização precedem cada efeito operacional. A Phase 09A revisou o plano sem autorizar 10/10A. As datas de integração devem ser recalculadas após o inventário runtime e contract freeze, evitando precisão fictícia.

Marcos de controle: baseline pronta; UX aprovada; shell autenticado; fluxos integrados; infraestrutura/privacidade verificadas; QA/UAT aceitos; autorização do piloto; launch readiness. Qualquer gate pendente mantém NO_GO no escopo correspondente e desloca o marco. Se não houver homologação Domínio, o escopo comercial não pode prometer exportação oficial.
