# Serdial21 Contabilidade Inteligente

## Fase 1 — Visão e Escopo do Produto

| Controle | Valor |
|---|---|
| Status | **APROVADA COM REFINAMENTOS — baseline vigente** |
| Versão | 1.0 |
| Data | 02/09/2026 |
| Aprovação | DAT-01 a DAT-10 aprovadas pelo responsável do produto em 02/09/2026 |
| Fonte | Prompt-Mestre de Engenharia do Produto Serdial21 |
| Limite | Exclusivamente Fase 1; sem código, seleção tecnológica, modelo físico de dados ou contratos de API |

### Convenções de governança

- **REQUISITO APROVADO (RA):** explícito no Prompt-Mestre; não pode ser alterado silenciosamente.
- **HIPÓTESE (H):** inferência que precisa de evidência de usuários, operação, mercado ou especialistas.
- **RECOMENDAÇÃO (REC):** proposta desta fase; só se torna decisão após aprovação.
- **PENDÊNCIA (P):** informação ausente ou descoberta necessária.
- **DECISÃO A TOMAR (DAT):** escolha com alternativas e impactos que requer aprovação.
- **PROPOSTA DE ALTERAÇÃO DE REQUISITO (PAR):** inclusão ou mudança explicitamente identificada.

---

## 1. Resumo executivo

O Serdial21 é uma plataforma contábil inteligente, multi-tenant e comercializável para escritórios contábeis. Sua visão combina três modos de operação: sistema contábil principal, solução integrada e camada inteligente de processamento, análise, conferência e automação.

O diferencial não é “uma IA que faz contabilidade”. É a união de um núcleo determinístico, regras versionadas, dados e documentos rastreáveis, interoperabilidade, IA assistiva, validações, aprovações humanas, segurança e auditoria. A plataforma deve automatizar o que for determinável, assistir o que for incerto e interromper o que não for seguro.

**Conclusão de produto desta fase:** a visão é coerente, mas abrange três profundidades de produto muito diferentes. Para reduzir risco e validar valor mais cedo, recomenda-se que o MVP entre no mercado como **camada inteligente integrada**, com um fluxo contábil estreito e completo, mantendo o sistema contábil existente como fonte oficial da escrituração. A capacidade de se tornar sistema principal permanece na visão de destino, não no primeiro lançamento.

Essa conclusão é **RECOMENDAÇÃO**, não requisito aprovado.

### Declaração de visão proposta

> Ser a camada confiável de operação contábil dos escritórios brasileiros, transformando documentos e dados heterogêneos em trabalho contábil padronizado, validado, explicável e auditável, convivendo com os sistemas já utilizados e evoluindo, quando houver maturidade e valor comprovado, para assumir a escrituração principal.

### Proposta operacional curta

> Automatizar o que é determinístico, assistir o que é incerto e interromper o que não é seguro.

### Resultados pretendidos

- Reduzir esforço manual repetitivo e retrabalho.
- Aumentar consistência entre pessoas, empresas e competências.
- Direcionar atenção humana às exceções e decisões materiais.
- Tornar cada resultado explicável e reconstruível a partir da origem.
- Permitir adoção progressiva, sem exigir migração total imediata.
- Proteger integridade contábil, confidencialidade e responsabilidade profissional.

### O que o produto não promete

- Não substitui automaticamente o julgamento e a responsabilidade do profissional contábil.
- Não transforma ausência de dados em autorização para inferir.
- Não trata saída de IA como verdade contábil definitiva.
- Não garante conformidade de escopo regulatório ainda não formalmente suportado e validado.
- Não cria conta contábil automaticamente para concluir uma contabilização.

---

## 2. Decisões já consolidadas pelo Prompt-Mestre

| ID | Requisito aprovado | Consequência para o produto |
|---|---|---|
| RA-01 | Plataforma comercializável para múltiplos escritórios | Multi-tenancy e administração da plataforma são estruturais. |
| RA-02 | Pode operar como sistema principal, integrado ou camada inteligente | A visão comporta os três modos, ainda que o roadmap os separe. |
| RA-03 | Interoperabilidade é estratégica | O núcleo não pode depender de layout ou fornecedor específico. |
| RA-04 | Motor contábil e controles críticos são determinísticos | Mesmos dados, contexto e versões produzem resultado reprodutível. |
| RA-05 | IA interpreta, classifica, recomenda, explica e detecta inconsistências | Saídas da IA são assistivas, identificáveis e governadas. |
| RA-06 | Dado necessário ausente gera PENDÊNCIA | Nenhum canal preenche ou autoriza silenciosamente o que falta. |
| RA-07 | IA não eleva sozinha PENDÊNCIA, CONFLITO ou BLOQUEADO a VALIDADO | Transições críticas dependem de controle externo à própria IA. |
| RA-08 | IA não cria conta contábil para concluir o processo | Conta inexistente produz sugestão, pendência ou bloqueio controlado. |
| RA-09 | Escritório, empresa, estabelecimento, usuário, perfil e permissão compõem a hierarquia | Nenhum dado ou contexto pode contaminar outro tenant. |
| RA-10 | Plano, regras, DE/PARA e normativa possuem governança e histórico | Versão, vigência, autoria, aprovação e rastreabilidade integram o domínio. |
| RA-11 | Bloqueios valem para humano, IA, API, importação, integração e automação | Não pode existir canal alternativo que contorne a política. |
| RA-12 | Alteração após desbloqueio exige nova conferência | Artefatos afetados não podem permanecer falsamente conciliados. |
| RA-13 | Auditoria é estrutural e correções geram novos eventos | Histórico anterior não é apagado ou reescrito silenciosamente. |
| RA-14 | Segurança, segregação de funções, proteção de dados e LGPD integram o desenho | Não são itens postergáveis para depois do MVP. |
| RA-15 | Sugestão, pendência, bloqueio, conflito e validação são visualmente distintos | A UX não pode induzir aceitação automática da IA. |
| RA-16 | Desenvolvimento incremental por fases | Esta entrega para antes da arquitetura macro. |

---

## 3. Atores e necessidades

As categorias do Prompt-Mestre são requisitos aprovados. As necessidades e prioridades abaixo são hipóteses até pesquisa de campo.

| Ator/persona | Necessidade principal | Autoridade ou cuidado esperado | Classificação |
|---|---|---|---|
| Escritório contábil | Operar várias empresas com padronização, produtividade e controle | Cliente organizacional e limite padrão recomendado de tenant | RA/REC |
| Sócio ou gestor | Aumentar capacidade, previsibilidade e margem sem elevar risco | Visualiza carteira, gargalos, qualidade e exceções | H |
| Contador responsável | Aprovar decisões materiais com evidência | Compreende origem, regra, versão, impacto e justificativa | RA/H |
| Analista contábil | Processar em lote, configurar e revisar exceções | Usuário diário recomendado do MVP | RA/REC |
| Auxiliar contábil | Receber, classificar, sanear e resolver pendências | Não recebe alçada crítica por executar trabalho inicial | RA/REC |
| Administrador do escritório | Manter usuários, empresas, configurações e integrações | Administração não implica aprovação contábil automática | RA/REC |
| Auditor/controlador interno | Reconstruir decisões e consultar evidências | Acesso preferencialmente somente leitura e segregado | H/REC |
| Operador de integração | Configurar conectores e tratar reprocessamentos | Identidade e permissão distintas das contábeis | H/REC |
| Operador da plataforma | Operar tenants, suporte e saúde do serviço | Sem acesso rotineiro a conteúdo; exceção exige controle | H/REC |
| Usuário da empresa atendida | Enviar documento, responder pendência ou acompanhar status | Portal e escopo ainda não definidos | P |
| Sistema externo/conta de serviço | Importar e exportar dados | Respeita os mesmos bloqueios, escopos e trilhas | RA/P |

### Personas recomendadas para o MVP

- **Usuário diário:** analista contábil.
- **Revisor/aprovador:** contador responsável ou gestor com alçada contábil.
- **Operador de saneamento:** auxiliar contábil.
- **Comprador econômico:** sócio ou gestor do escritório.
- **Administrador:** papel administrativo separado das alçadas contábeis.

Essa composição precisa ser validada por entrevistas e observação do trabalho real.

---

## 4. Problemas que o produto resolve

| Problema | Trabalho do usuário | Resultado esperado |
|---|---|---|
| Entradas chegam em canais, formatos e sistemas diferentes | Convertê-las para linguagem contábil comum sem redigitação | Menos esforço, erros e dependência de layout |
| Códigos, contas e cadastros variam por sistema/empresa | Manter correspondências reutilizáveis e rastreáveis | Onboarding e manutenção previsíveis |
| Fatos equivalentes recebem tratamentos diferentes | Aplicar a mesma regra aprovada ao mesmo contexto | Consistência e reprodutibilidade |
| Volume força revisão item a item | Trabalhar em lote e focar exceções | Produtividade sem revisão cega |
| Entradas são incompletas ou contraditórias | Saber por que parou e o que falta | Pendência/conflito explícito |
| Sugestão automática parece decisão | Ver fundamento, evidência, confiança e impacto | Confiança calibrada e responsabilidade clara |
| Mudanças vêm de pessoas, regras, IA ou integrações | Reconstruir quem/o quê/quando/por quê/versão | Auditoria ponta a ponta |
| Retries e reimportações duplicam efeitos | Repetir com segurança | Idempotência e reprocessamento explícito |
| Período protegido recebe alteração por canal paralelo | Aplicar bloqueio no momento do efeito | Integridade da conciliação e fechamento |
| Escritórios dependem de sistemas existentes | Obter valor sem migração total | Adoção progressiva |
| Gestão não enxerga filas e gargalos | Acompanhar volume, idade, risco e responsável | Gestão baseada em fatos |

### Job-to-be-Done nuclear recomendado

> Quando eu receber documentos ou dados de um fluxo contábil selecionado, quero que o sistema os normalize, valide, processe por regras, destaque incertezas e entregue uma proposta aprovada ao sistema de destino, para reduzir esforço sem perder controle, evidência ou rastreabilidade.

---

## 5. Proposta de valor

> Para escritórios contábeis que operam múltiplas empresas em ambientes heterogêneos, o Serdial21 é uma plataforma de processamento contábil confiável que padroniza dados, executa regras determinísticas, usa IA como assistência explicável, conduz exceções à pessoa certa e preserva evidências de ponta a ponta. Diferentemente de automações opacas ou soluções que exigem substituição imediata do legado, ele nasce para coexistir, integrar e controlar.

### Pilares de valor

1. Confiança antes da automação.
2. Interoperabilidade nativa.
3. Controle profissional sobre efeitos críticos.
4. Rastreabilidade entre origem, transformação, regra, versão e aprovação.
5. Produtividade orientada a exceções.
6. Adoção progressiva.

### Provas de valor ainda necessárias

- Tempo poupado por item, lote, empresa e competência.
- Redução de retrabalho, duplicidades e correções.
- Tempo e custo de onboarding e parametrização.
- Aceitação e correção das sugestões por tarefa.
- Impacto sobre o fechamento.
- Disposição a pagar e custo sustentável de conectores, armazenamento e IA.

---

## 6. Modos de operação e fronteira do produto

| Modo | Responsabilidade do Serdial21 | Fonte oficial recomendada | Horizonte recomendado |
|---|---|---|---|
| Camada inteligente | Recebe, normaliza, analisa, propõe, aprova e devolve resultados | Sistema contábil externo para livros e saldos | **MVP** |
| Operação integrada | Divide domínios com outro sistema; cada domínio tem autoridade explícita | Definida por domínio e direção | **Pós-MVP** |
| Sistema contábil principal | Mantém razão oficial, fechamento, demonstrações e livros suportados | Serdial21 | **Evolução** |

Os três modos permanecem na visão aprovada. O sequenciamento é recomendação.

### Dentro do MVP recomendado

- Administração mínima de tenant, empresas, estabelecimentos, usuários, papéis e configurações.
- Cadastros e plano de contas estritamente necessários ao fluxo-piloto.
- Recepção de um conjunto limitado de documentos/dados e preservação do original.
- Validação de origem, formato, completude e duplicidade.
- Modelo canônico mínimo, identidades externas e DE/PARA versionado.
- Motor de regras versionado e aprovável no recorte.
- IA limitada às tarefas aprovadas, com sugestão sempre distinguível.
- Fila de sugestão, pendência, conflito, bloqueio, revisão e aprovação.
- Proposta de contabilização balanceada e exportação controlada.
- Confirmação/reconciliação técnica do resultado no sistema de destino.
- Auditoria, segurança, reprocessamento seguro e monitoramento essenciais.

### Fora do MVP recomendado

- Substituição geral do sistema contábil do escritório.
- Cobertura simultânea de todos os documentos, eventos, regimes, setores e fornecedores.
- Razão oficial completo, fechamento integral, demonstrações e livros oficiais.
- Conciliação bancária e contábil universal.
- Interpretação normativa autônoma ou sem curadoria profissional.
- Portal completo da empresa atendida, salvo evidência de que seja indispensável ao piloto.
- Marketplace, internacionalização e expansão para ERP, CRM, folha ou fiscal completo.

As exclusões são de sequenciamento, não eliminação definitiva da visão, salvo as proibições explícitas sobre inferência e autonomia da IA.

---

## 7. Fluxo conceitual revisado

### PAR-01 — Controles de entrada, exceção e confirmação

**PROPOSTA DE ALTERAÇÃO DE REQUISITO:** complementar o fluxo com segurança de entrada, preservação de origem, idempotência, normalização, tratamento de exceções e confirmação do destino.

**Documento/dado**
→ recepção autenticada
→ identificação de tenant, empresa e origem
→ preservação do original e sua integridade
→ inspeção de segurança e formato
→ idempotência/deduplicação
→ extração
→ normalização no modelo canônico
→ validação de qualidade e completude
→ identificação do fato contábil
→ resolução de cadastros e DE/PARA
→ seleção da regra/máscara vigente
→ aplicação ao plano de contas vigente
→ proposta de contabilização
→ validações contábeis, de permissão e de bloqueio
→ pendência/conflito ou aprovação
→ escrituração ou exportação
→ confirmação e reconciliação
→ bloqueio/fechamento
→ demonstrações/livros, conforme o modo
→ retenção e evidência.

Em qualquer etapa, falha ou ambiguidade segue para tratamento explícito, sem converter o item em sucesso.

### PAR-02 — Auditoria como capacidade transversal

**PROPOSTA DE ALTERAÇÃO DE REQUISITO:** interpretar auditoria como trilha contínua e não apenas a última etapa linear. A visão “→ AUDITORIA” permanece como resultado consultável, mas os eventos nascem junto com cada operação relevante.

### PAR-03 — Novo módulo transversal

**PROPOSTA DE ALTERAÇÃO DE REQUISITO:** adicionar **M19 — Workflow, Pendências e Aprovações**.

O módulo responde por filas, atribuição, motivo, evidências, comentários, aprovação/rejeição, alçadas, SLA, escalonamento e histórico. A justificativa funcional é que pendências e aprovações atravessam documentos, cadastros, regras, DE/PARA, IA, escrituração, conciliação, desbloqueio e normativa. Replicar isso em cada módulo aumentaria inconsistência e risco.

Governança de dados, onboarding e observabilidade permanecem inicialmente como capacidades transversais, não como novos módulos autônomos nesta fase.

---

## 8. Mapa de capacidades e horizonte

A classificação é uma recomendação. O corte deve ocorrer por capacidade, não pela entrega indiscriminada de um módulo inteiro.

| Capacidade | Origem | MVP recomendado | Pós-MVP | Evolução |
|---|---|---|---|---|
| Organização e tenancy | M01 | Tenant, empresas, estabelecimentos e configuração essencial | Políticas avançadas | Grupos/ecossistema complexo |
| Identidade e acesso | M01 | Usuários, papéis, menor privilégio e SoD essencial | SSO, alçadas e escala | Federação avançada |
| Cadastros | M02 | Entidades do fluxo-piloto | Cobertura ampla | Enriquecimento controlado |
| Plano de contas | M03 | Importação, hierarquia, natureza, vigência e histórico | Modelos de escritório/segmento | Biblioteca abrangente |
| DE/PARA | M04 | Escopo, versão, vigência, aprovação e rastreio | Manutenção em massa | Recomendação adaptativa governada |
| Documentos/importação | M05/M06 | Tipos escolhidos, original, validação, duplicidade e linhagem | Mais canais/layouts | Catálogo extensível |
| Regras | M07 | Condições, ações, prioridade, escopo, vigência, versão e aprovação | Simulação e biblioteca | Otimização assistida |
| IA contábil | M08 | Classificação, extração, sugestão, inconsistência e explicação do recorte | Regras/DE-PARA, conciliação e pesquisa normativa | IA multimodal/preditiva controlada |
| Pendências/aprovação | M19 proposto | Fila, causa, evidência, responsável, decisão e justificativa | SLA e workflow configurável | Orquestração adaptativa controlada |
| Escrituração | M09 | Proposta, partidas, validação, aprovação e exportação | Razão interno | Sistema principal |
| Conciliação | M10 | Confirmação entrada–proposta–exportação | Bancária e contábil ampla | Contínua e assistida |
| Bloqueios | M11 | Todos os canais do MVP respeitam bloqueios aplicáveis | Granularidade e reabertura completas | Políticas adicionais de risco |
| Fechamento | M12 | Fora, salvo mudança da fonte oficial | Competência, gates e reabertura | Fechamento contínuo |
| Demonstrações/livros | M13/M14 | Apenas relatórios operacionais | Saídas coerentes com razão interno | Saídas oficiais suportadas |
| Integrações | M15 | Canônico mínimo, import/export genérico e conector-piloto | Catálogo e layouts configuráveis | SDK/marketplace |
| Auditoria | M16 | Cobertura integral das operações relevantes | Busca, relatórios e retenção avançados | Analytics em escala |
| Normativa | M17 | Referências curadas indispensáveis | Fontes, versões, vigências e aprovação | Atualização/impacto assistidos |
| Administração técnica | M18 | Filas, erros, saúde e reprocessamento seguro | Observabilidade em escala | Operação assistida avançada |

- **MVP:** sem a capacidade não existe fluxo fechado ou permanece risco inaceitável.
- **Pós-MVP:** amplia cobertura, eficiência ou robustez.
- **Evolução:** habilita novo modo estratégico, ecossistema ou mercado.

---

## 9. Integrações necessárias

| Prioridade | Integração/capacidade | Objetivo |
|---|---|---|
| P0 transversal | Canônico, identidade externa, DE/PARA, idempotência e reconciliação | Tornar conectores confiáveis e desacoplados |
| P0 piloto | Sistema contábil fonte oficial do piloto | Importar contexto e devolver lote com confirmação |
| P0 piloto | Recepção manual e um canal automatizável | Iniciar o fluxo preservando origem e duplicidade |
| P0 piloto | Import/export genérico nos formatos escolhidos | Evitar dependência total do primeiro conector |
| P1 | Dados bancários/financeiros | Apoiar conciliação; vira P0 se esse for o caso inicial |
| P1 | Documentos eletrônicos/fontes fiscais do recorte | Reduzir digitação após definição do escopo |
| P1 | ERP/financeiro da empresa atendida | Completar fatos quando a fonte for distinta |
| P1 condicional | Provedor corporativo de identidade | SSO quando exigido por clientes |
| P2 | Repositórios documentais/canais colaborativos | Ampliar formas de recepção |
| P2 | Fontes normativas externas | Alimentar base curada sem ativação automática |
| P2 | BI/consumidores analíticos | Distribuir dados sem criar fonte oculta de verdade |

### Contrato de responsabilidade de cada integração

O catálogo deve registrar: finalidade, proprietário, sistema de registro por domínio, tenant/empresa autorizados, direção, frequência, ordenação, identidade técnica, revogação, identificadores externos, correlação, versão do layout, idempotência, retry, reprocessamento, estados, falha parcial, conflito, retenção do original, evidências, dados sensíveis e responsável por cada erro.

Falha de conector não pode produzir sucesso aparente ou perda silenciosa.

---

## 10. Segurança, privacidade e auditoria críticas

### Guardrails mínimos do produto

1. **Isolamento completo:** tenant e empresa limitam registros principais e derivados, inclusive documentos, busca, relatórios, caches, filas, notificações, temporários, exportações, auditoria, backups e contexto da IA.
2. **Negação por padrão:** toda ação é autorizada por identidade, papel, ação, tenant, empresa, objeto, estado e sensibilidade.
3. **Contexto confiável:** tenant e empresa efetivos vêm da identidade e autorização, não apenas de parâmetros da requisição.
4. **Paridade entre canais:** interface, API, importação, integração, IA, regra, job e automação passam pelos mesmos bloqueios e decisões.
5. **Menor privilégio e segregação:** criar/aprovar, alterar regra/aprovar versão, conciliar/desbloquear, administrar/auditar e operar suporte/acessar conteúdo devem poder ser separados.
6. **Identidades distintas:** pessoas, serviços e integrações têm credenciais individualizadas, escopo mínimo e revogação.
7. **Acesso excepcional controlado:** eventual suporte cross-tenant é temporário, justificado, aprovado, visível e auditado.
8. **Proteção de segredo:** credenciais, tokens e chaves não aparecem em tela, exportação, erro ou antes/depois da auditoria.
9. **Conteúdo não confiável:** documentos, planilhas, XML, texto externo e normativa são dados; não alteram instruções de segurança ou permissões da IA.
10. **Revalidação no efeito:** autorização, bloqueio e versão vigente são verificados novamente ao efetivar operação crítica, inclusive após fila ou retry.
11. **Falha segura:** se autorização, auditoria ou validação indispensável não puder ser garantida, o efeito contábil não é confirmado.
12. **Recuperabilidade comprovada:** backup só é válido depois de restauração testada com integridade e isolamento.

### Conteúdo mínimo da auditoria

Para cada operação relevante, registrar conforme aplicável:

- tenant, empresa e estabelecimento;
- identidade humana ou técnica e perfil efetivo;
- instante da ocorrência e do registro;
- operação, módulo, entidade e identificador;
- estado anterior e posterior, minimizando dados sensíveis;
- origem: HUMANO, IA, MOTOR DE REGRAS, API, IMPORTAÇÃO, INTEGRAÇÃO ou ROTINA AUTOMÁTICA;
- justificativa, aprovação e alçada;
- regra, plano, DE/PARA, configuração, modelo e versões utilizadas;
- documento, fonte normativa, conector e identificadores externos;
- resultado, falha ou negativa;
- correlação/causalidade entre recepção, processamento, IA, aprovação, exportação e confirmação;
- referência ao evento anterior em correção, reversão ou reprocessamento.

Também devem ser auditados: tentativas negadas relevantes, acessos privilegiados, exportações/downloads sensíveis e mudanças de permissões, regras, DE/PARA, normativa, conectores e política da própria auditoria.

Observabilidade operacional não substitui trilha de auditoria.

### LGPD e governança de dados

Antes do piloto, são necessários:

- inventário dos dados e fluxos por documento, integração, IA, auditoria, backup e exportação;
- finalidade, categorias de dados/titulares, base legal e papéis de controlador/operador por fluxo, validados pelo jurídico/encarregado;
- política de minimização, classificação, acesso, retenção, descarte e bloqueio legal;
- procedimentos para direitos dos titulares quando aplicáveis e encerramento do tenant;
- política de incidentes, preservação de evidências e comunicações;
- governança de fornecedores/suboperadores, localização, retenção, transferência e treinamento;
- proibição de usar dados de um tenant em resposta, memória, recuperação ou treinamento de outro;
- telemetria e logs sem cópia irrestrita de documentos e dados pessoais.

Não se presume consentimento como base legal padrão nem se fixa prazo de retenção nesta fase. Isso depende da finalidade e de validação especializada.

---

## 11. Requisitos não funcionais por prioridade

As prioridades são recomendações; metas numéricas dependem de volumetria, contratos e risco do piloto.

| Prioridade | Requisito | Critério inicial |
|---|---|---|
| P0 | Integridade contábil/transacional | Nenhum efeito parcial, desbalanceado, duplicado ou incompatível com bloqueio |
| P0 | Isolamento/confidencialidade | Zero acesso cruzado, inclusive em dados derivados |
| P0 | Autorização/segregação | Política única em todos os canais e alçadas aprovadas |
| P0 | Auditoria/linhagem | Todo efeito crítico reconstruível da origem à saída |
| P0 | Idempotência/reprocessamento | Repetição não duplica; reprocessamento é explícito e versionado |
| P0 | Segurança da IA | Nenhuma promoção proibida, mistura de contexto ou comando de conteúdo externo |
| P0 | Recuperação | Dados, documentos, auditoria, regras, permissões e integrações restauráveis |
| P0 | Versionamento/reprodutibilidade | Resultado histórico aponta para as versões usadas |
| P0 | Retenção/proteção de dados | Política aprovada antes de dados reais |
| P1 | Disponibilidade/observabilidade | Metas, alertas, responsáveis e degradação definidos para o piloto |
| P1 | Performance/grandes volumes | Metas baseadas em volume e sazonalidade reais |
| P1 | Escalabilidade/assíncrono | Filas não relaxam ordem, autorização, bloqueio ou auditoria |
| P1 | Manutenibilidade/testabilidade | Regras, conectores e IA testáveis e substituíveis |
| P1 | Portabilidade | Plano de saída para dependências críticas |
| P2 | Internacionalização | Preparar conceitos sem prometer suporte externo |

---

## 12. Critérios de sucesso

### Para concluir a Fase 1

- Visão, posicionamento e modo do MVP aprovados.
- Personas primárias e participantes do piloto definidos.
- Caso de uso, documentos/eventos, regimes e sistemas do piloto delimitados.
- Fronteira entre Serdial21 e sistema de registro aprovada.
- Semântica inicial de estados, validação e aprovação sem ambiguidade material.
- Matriz preliminar de alçadas e segregação aprovada.
- Hipóteses, riscos e pendências com responsáveis.
- Métricas do piloto e linha de base planejadas.

### Invariantes obrigatórios do futuro MVP

- 100% dos efeitos contábeis rastreáveis à origem, versões, regras e decisões.
- 100% dos dados obrigatórios ausentes geram pendência ou bloqueio explícito.
- Zero promoção autônoma de sugestão de IA a validação, aprovação ou escrituração.
- Zero criação autônoma de conta contábil pela IA.
- Zero acesso cruzado entre tenants nos testes de isolamento.
- Mesmos dados, contexto e versões produzem o mesmo resultado determinístico.
- Reimportação ou retry não duplica documento, fato, proposta ou lançamento.
- Bloqueio vigente impede efeito por qualquer canal.
- Falha de conector é visível, recuperável e reconciliável.
- Histórico continua explicável depois de mudança de regra, plano ou DE/PARA.
- Conteúdo normativo não aprovado não influencia decisão operacional.

### Métricas recomendadas para o piloto

Metas numéricas são pendências.

- Tempo entre onboarding e primeiro lote aprovado/exportado.
- Tempo de ciclo e idade das pendências.
- Toques humanos por item e percentual direcionado a exceção.
- Cobertura determinística por tipo de evento.
- Aceitação, rejeição e correção da IA por tarefa, classe e versão.
- Duplicidades, desbalanceamentos, reversões e correções.
- Sucesso e latência de importação, exportação e confirmação.
- Cobertura de auditoria das operações críticas.
- Incidentes/tentativas de isolamento e autorização.
- Adoção recorrente por escritório, empresa, usuário e competência.
- Economia líquida do custo de implantação, parametrização, conectores e IA.

---

## 13. Lacunas de requisitos

### Produto e mercado

- Perfil e porte do escritório-alvo; número típico de empresas e usuários.
- Comprador, usuário diário, aprovador e administrador reais.
- Dor prioritária e linha de base mensurável.
- Modelo comercial, implantação, suporte e custo admissível.
- Participação ou não da empresa atendida.

### Escopo contábil

- Regimes, segmentos, jurisdições, eventos e documentos iniciais.
- Invariantes de proposta/lançamento: moeda, arredondamento, dimensões, competência, reversão e ajustes.
- Significado operacional de “máscara contábil”.
- Precedência entre norma, regra global, escritório, empresa e exceção.
- Retroatividade/reprocessamento após mudança de regra.
- Conciliação, fechamento, reabertura e invalidação de derivados.
- Matriz explícita do que cada versão suporta.

### Estados, workflow e autoridade

- Diferença entre VALIDADO, APROVADO, ESCRITURADO e FECHADO.
- Atores e pré-condições de cada transição.
- Operações que exigem quatro olhos, justificativa ou exceção.
- Responsável e SLA por pendência/conflito.
- Alcance de REQUER NOVA CONFERÊNCIA.

### Multi-tenancy e acesso

- Escritório sempre como tenant e empresa como subescopo.
- Usuário em um ou vários tenants e troca explícita de contexto.
- Grupos de escritórios e compartilhamento autorizado.
- Suporte cross-tenant e acesso emergencial.
- Catálogo de perfis, alçadas e segregações.

### Integrações e dados

- Sistemas externos/versões do piloto.
- Fonte oficial de cadastro, plano, documento, proposta, lançamento, saldo e status.
- Direção, frequência, ordenação e conflito por fluxo.
- Identidade/deduplicação e reprocessamento intencional.
- Carga histórica, reconciliação inicial e qualidade da origem.
- Governança do canônico e layouts.

### IA e normativa

- Tarefas liberadas e custo aceitável do erro.
- Evidência, explicação e limiar por tarefa.
- Conjuntos de avaliação e aprovação de versão.
- Fornecedores, localização, retenção, treinamento e suboperadores.
- Fontes normativas, direitos, curadoria, jurisdição, vigência e conflitos.

### Segurança, LGPD e continuidade

- Inventário/classificação, controlador/operador e base legal.
- Retenção, descarte, legal hold, exportação e encerramento.
- Autenticação reforçada, sessão, recuperação e revogação.
- RPO, RTO, SLA, volume, sazonalidade e testes de restauração.
- Incidentes, responsáveis, atendimento e comunicação.
- Comportamento quando a auditoria não puder ser garantida.

---

## 14. Decisões submetidas à aprovação — aprovadas em 02/09/2026

### DAT-01 — Estratégia de entrada do MVP

**DECISÃO**  
Definir se o primeiro lançamento será camada inteligente, operação híbrida ampla ou sistema contábil principal.

**MOTIVO**  
A escolha altera escopo, responsabilidade, prazo, integrações, relatórios e risco regulatório.

**ALTERNATIVAS**  
A) camada inteligente; B) operação híbrida por vários domínios; C) sistema principal desde o MVP.

**IMPACTOS**  
A reduz barreira e valida o núcleo com menor superfície; B exige sincronização complexa; C exige razão, fechamento, demonstrações e livros maduros no primeiro lançamento.

**RECOMENDAÇÃO**  
**A — camada inteligente integrada**, preservando os três modos na visão futura.

### DAT-02 — Caso de uso vertical do MVP

**DECISÃO**  
Selecionar uma família concreta de documentos/eventos e um fluxo ponta a ponta para o piloto.

**MOTIVO**  
Sem esse corte, não há escopo estimável, testes, métrica de qualidade ou prova econômica.

**ALTERNATIVAS**  
A) documento/dado até proposta e exportação; B) conciliação como entrada; C) outro fluxo escolhido por evidência.

**IMPACTOS**  
Escolha ampla explode escopo; escolha estreita demais pode não provar valor.

**RECOMENDAÇÃO**  
**A**, com uma ou poucas famílias de alto volume, repetibilidade e dados disponíveis; a família exata vem dos pilotos.

### DAT-03 — Fonte oficial no MVP

**DECISÃO**  
Definir onde residem os registros oficiais de cadastros, plano, lançamentos, saldos e fechamento.

**MOTIVO**  
Sincronização sem autoridade explícita cria conflitos e perda de confiança.

**ALTERNATIVAS**  
A) sistema externo; B) Serdial21; C) autoridade híbrida por domínio.

**IMPACTOS**  
A limita o MVP à proposta/controle/exportação; B exige sistema principal; C introduz conflitos bidirecionais desde o início.

**RECOMENDAÇÃO**  
**A no MVP**, com autoridade registrada por domínio e confirmação do destino.

### DAT-04 — Persona e governança operacional

**DECISÃO**  
Definir usuário primário, aprovador, comprador e participação da empresa atendida.

**MOTIVO**  
Fila, UX, permissões, implantação e proposta comercial dependem dos papéis.

**ALTERNATIVAS**  
Operação centrada em analista, contador, gestor ou empresa atendida.

**IMPACTOS**  
Cada escolha muda densidade das telas, linguagem, alçadas e canais.

**RECOMENDAÇÃO**  
**Analista como usuário diário, contador como aprovador, gestor como comprador e auxiliar como saneador**; portal da empresa fica fora do MVP salvo evidência contrária.

### DAT-05 — Pacote inicial de integração

**DECISÃO**  
Escolher os sistemas e formatos do piloto.

**MOTIVO**  
Interoperabilidade é estratégica, mas cada conector tem custo e risco contínuo.

**ALTERNATIVAS**  
A) apenas arquivos genéricos; B) vários conectores proprietários; C) contrato genérico mais um conector estratégico.

**IMPACTOS**  
A reduz o valor da automação; B dispersa a equipe; C equilibra aprendizado e adoção.

**RECOMENDAÇÃO**  
**C — importação/exportação genérica mais um conector do escritório-piloto.**

### DAT-06 — Limite de automação e aprovação

**DECISÃO**  
Definir quais passos determinísticos podem concluir automaticamente e quais efeitos exigem pessoa autorizada.

**MOTIVO**  
O Prompt-Mestre limita a IA, mas não define todas as alçadas do motor determinístico.

**ALTERNATIVAS**  
A) aprovação humana de toda proposta; B) automação governada com revisão por amostra; C) automação ampla por confiança.

**IMPACTOS**  
A maximiza aprendizado/controle com menor ganho inicial; B exige histórico e critérios confiáveis; C aumenta o risco de automação indevida.

**RECOMENDAÇÃO**  
**A no piloto para toda proposta com efeito contábil**, automatizando apenas etapas preparatórias determinísticas. Avaliar B depois de métricas segmentadas, regras aprovadas e reversão segura.

### DAT-07 — Hierarquia de tenancy

**DECISÃO**  
Confirmar o escritório como tenant padrão e a empresa atendida como subescopo.

**MOTIVO**  
O limite afeta contrato, administração, acesso, integração, auditoria e IA.

**ALTERNATIVAS**  
A) tenant por escritório; B) por empresa; C) por grupo/franquia.

**IMPACTOS**  
A acompanha o comprador e a operação descritos; B multiplica administração; C exige compartilhamento complexo.

**RECOMENDAÇÃO**  
**A como padrão**, com empresas subordinadas e associação explícita da identidade a cada tenant. Grupos ficam pendentes de caso real.

### DAT-08 — Módulo transversal de pendências e decisões

**DECISÃO**  
Aprovar M19 — Workflow, Pendências e Aprovações — e auditoria transversal.

**MOTIVO**  
Pendência, revisão e aprovação atravessam vários módulos e precisam de semântica uniforme.

**ALTERNATIVAS**  
A) lógica duplicada por módulo; B) capacidade transversal compartilhada.

**IMPACTOS**  
A aumenta divergência e risco; B centraliza governança e exige contratos claros com cada domínio.

**RECOMENDAÇÃO**  
**B**, aprovando PAR-02 e PAR-03.

### DAT-09 — Política inicial de IA e dados

**DECISÃO**  
Definir retenção e uso de dados dos tenants por fornecedores, inclusive treinamento e localização.

**MOTIVO**  
Documentos contábeis podem conter dados pessoais, financeiros e sigilosos.

**ALTERNATIVAS**  
A) proibir treinamento e minimizar retenção externa; B) uso agregado/anonimizado aprovado; C) uso amplo autorizado.

**IMPACTOS**  
A reduz risco e opções de aprendizado; B exige garantias robustas; C amplia exposição e barreira comercial.

**RECOMENDAÇÃO**  
**A como padrão**, com exceção específica, opt-in, juridicamente validada e auditada.

### DAT-10 — Corte de capacidades por horizonte

**DECISÃO**  
Aprovar a classificação da seção 8 como base de planejamento.

**MOTIVO**  
Os módulos M01–M18 são visão, não obrigação de entrega simultânea.

**ALTERNATIVAS**  
A) fatia vertical segura; B) módulos horizontais completos; C) todos os módulos no primeiro lançamento.

**IMPACTOS**  
A entrega resultado validável; B pode produzir componentes sem jornada; C torna prazo, qualidade e conformidade imprevisíveis.

**RECOMENDAÇÃO**  
**A — fatia vertical segura e completa**, conforme MVP/Pós-MVP/Evolução.

---

## 15. Glossário inicial

| Termo | Definição inicial |
|---|---|
| Plataforma Serdial21 | Serviço e capacidades que atendem múltiplos escritórios de forma isolada. |
| Tenant | Unidade máxima de isolamento contratual e operacional; recomendação: um escritório. |
| Escritório contábil | Organização cliente que atende uma carteira de empresas. |
| Empresa atendida | Entidade cuja contabilidade é processada; evita confusão com “cliente” cadastral da empresa. |
| Estabelecimento | Unidade, filial ou inscrição vinculada à empresa; sentido jurídico depende do escopo. |
| Usuário | Identidade humana autenticada, associada explicitamente a tenant, empresa, papel e alçada. |
| Identidade técnica | Conta não humana de API, integração, job ou automação, autorizável e revogável. |
| Perfil/papel | Conjunto administrável de permissões; não substitui o escopo contextual. |
| Permissão | Autorização granular para ação sobre recurso, estado e escopo determinados. |
| Segregação de funções | Separação de ações incompatíveis, como criar e aprovar a mesma regra. |
| Competência | Período ao qual o fato ou lançamento pertence, distinto da data de recepção. |
| Exercício | Intervalo contábil mais amplo que agrega competências. |
| Documento | Evidência recebida com original, metadados, origem, integridade e histórico. |
| Registro de origem | Representação imutável do recebido antes de normalização ou enriquecimento. |
| Extração | Conversão de conteúdo em campos estruturados; não equivale a validação. |
| Fato contábil | Ocorrência econômica normalizada e sustentada por evidência, candidata a regras. |
| Modelo canônico | Vocabulário interno estável que desacopla o núcleo dos formatos externos. |
| Conector | Fronteira que traduz dados entre sistema específico e modelo canônico. |
| Sistema de registro | Fonte autoritativa de um domínio ou campo. |
| DE/PARA | Correspondência governada entre códigos/identidades de origem, canônico e destino. |
| Plano de contas | Hierarquia de contas permitidas para uma empresa/período, com natureza e restrições. |
| Conta sintética | Conta agregadora, normalmente sem partidas diretas. |
| Conta analítica | Conta apta a receber partidas conforme plano e vigência. |
| Conta referencial | Conta externa ou normativa relacionada à conta da empresa. |
| Máscara contábil | Template parametrizado que transforma contexto/fato em proposta; sentido exato precisa ser validado. |
| Regra determinística | Produz o mesmo resultado para os mesmos dados, contexto e versões. |
| Vigência | Intervalo em que cadastro, regra, plano, DE/PARA ou norma pode ser aplicado. |
| Versão | Identidade imutável de um artefato em determinado estado histórico. |
| Sugestão de IA | Recomendação provisória com contexto, evidência, confiança e versão; sem efeito definitivo autônomo. |
| Proposta contábil | Candidato a lançamento com contas, valores, dimensões, histórico, evidências e versões. |
| Validação | Confirmação de critérios; não implica automaticamente aprovação ou escrituração. |
| Aprovação | Ato de responsabilidade que autoriza o próximo efeito e registra alçada/justificativa. |
| Lote | Agrupamento controlado de propostas ou lançamentos. |
| Lançamento | Registro composto por partidas, sujeito a equilíbrio, competência, permissão e bloqueio. |
| Escrituração | Efetivação do lançamento no sistema de registro contábil. |
| Conciliação | Comparação entre fontes para confirmar correspondência e evidenciar diferenças. |
| Bloqueio | Impedimento explícito de mutação ou progressão em determinado escopo. |
| Fechamento | Estado controlado de uma competência; impede mutações ordinárias. |
| Reabertura | Exceção autorizada ao fechamento, com justificativa e tratamento de derivados. |
| VALIDADO | Passou pelo gate definido; não significa automaticamente APROVADO ou ESCRITURADO. |
| SUGESTÃO | Resultado provisório sem autoridade para produzir efeito definitivo. |
| PENDÊNCIA | Ausência de dado, evidência ou ação obrigatória que impede progressão segura. |
| CONFLITO | Fontes, valores, regras ou versões incompatíveis sem resolução automática segura. |
| BLOQUEADO | Impedimento por controle, segurança, período, regra ou dependência. |
| REQUER NOVA CONFERÊNCIA | Alteração relevante invalidou a confiança da conferência anterior. |
| Linhagem | Relação navegável entre origem, transformações, versões, decisões e saída. |
| Evento de auditoria | Registro imutável de ação, tentativa, mudança ou decisão relevante. |
| Idempotência | Repetir a mesma operação não cria efeito adicional indevido. |
| Deduplicação | Identificação de entradas semanticamente repetidas antes de novo efeito. |
| Reprocessamento | Nova execução controlada, preservando resultados e versões anteriores. |
| Base normativa autorizada | Fontes cuja procedência, versão, vigência e uso foram aprovados. |

---

## 16. Encerramento da Fase 1

### DECISÕES CONSOLIDADAS

- Plataforma contábil inteligente multi-tenant para escritórios.
- Modos de destino: sistema principal, integrado e camada inteligente.
- Interoperabilidade, canônico, conectores e DE/PARA governado são estratégicos.
- Núcleo determinístico, regras, validações, permissões e aprovação governam efeitos críticos.
- IA é assistiva, identificável e explicável; não é fonte absoluta da verdade.
- Dado ausente gera PENDÊNCIA; IA não cria conta nem promove sozinha estados proibidos.
- Isolamento, segurança, auditoria, bloqueios e rastreabilidade são estruturais e transversais.
- Correções preservam o histórico e geram novos eventos.
- M01–M18 compõem a visão, mas não são todos automaticamente MVP.

### HIPÓTESES A VALIDAR

- Escritórios aceitarão começar com camada integrada antes de substituir o sistema principal.
- Documento/dado → proposta → aprovação → exportação é o melhor ponto de entrada.
- Analista é usuário diário, contador aprovador e gestor comprador.
- Um recorte estreito tem volume e dor suficientes para provar valor.
- Sistemas do piloto têm dados e integração com qualidade aceitável.
- Regras e DE/PARA podem ser reutilizados com custo de configuração sustentável.
- Filas de exceção reduzem tempo sem estimular aprovação automática.
- Explicação e evidência aumentam confiança na IA.
- Especialistas estarão disponíveis para aprovar regras, normas e avaliações.
- Ganho operacional supera onboarding, conectores, armazenamento e IA.

### PENDÊNCIAS

- Escritórios-piloto, porte, carteira, volumes e sazonalidade.
- Caso de uso, documentos/eventos, regimes, setores e jurisdições iniciais.
- Sistema contábil e formatos do primeiro conector.
- Fonte oficial por domínio e política de conflito.
- Personas, alçadas, permissões e segregação.
- Semântica de VALIDADO, APROVADO, ESCRITURADO e FECHADO.
- Invariantes contábeis e precedência das regras.
- Reprocessamento, correção, reabertura e invalidação de derivados.
- IA, avaliação, fornecedores, retenção, treinamento e localização.
- Inventário LGPD, bases legais, papéis, retenção e descarte.
- Volumetria, SLA, RPO, RTO e continuidade.
- Métricas e metas objetivas do MVP.
- Modelo comercial, onboarding, suporte e custo admissível.

### RISCOS

| Risco | Criticidade | Resposta recomendada |
|---|---|---|
| Entregar três modos e M01–M18 simultaneamente | Crítica | Fatia vertical segura e exclusões explícitas |
| Caso de uso sem foco/volume | Crítica | Selecionar com dados de pilotos |
| Ambiguidade entre validar, aprovar, escriturar e fechar | Crítica | Formalizar estados e autoridades |
| Escrita concorrente com sistema externo | Crítica | Sistema de registro por domínio/campo |
| Vazamento entre tenants em derivados, backup ou IA | Crítica | Isolamento ponta a ponta e testes negativos |
| Alucinação, prompt injection ou automação indevida | Crítica | Efeitos restritos, contexto separado, evidência e gates |
| Duplicidade por retry/reimportação/falha parcial | Crítica | Identidade, idempotência, checkpoints e reconciliação |
| Bloqueio contornado por API/job/concorrência | Crítica | Revalidar no efeito e aplicar política única |
| Regra ou DE/PARA incorreto em escala | Alta | Versão, vigência, simulação, aprovação e reversão |
| Histórico perder explicabilidade | Alta | Preservar versões e reprocessar explicitamente |
| Normativa desatualizada/não aprovada | Alta | Curadoria, vigência, impacto e aprovação profissional |
| Retenção excessiva ou eliminação indevida | Alta | Inventário, finalidade, política e validação jurídica |
| Parametrização/conectores custarem mais que o valor | Alta | Medir economia líquida desde o piloto |
| UX induzir confiança excessiva | Alta | Estados inequívocos, evidência e métricas de correção |
| Recuperação incompleta ou mistura de tenants | Alta | Backup completo e restaurações testadas |

### DECISÕES APROVADAS EM 02/09/2026

1. **DAT-01:** MVP como camada inteligente integrada.
2. **DAT-02:** fluxo documento/dado → proposta → aprovação → exportação; família exata escolhida com os pilotos.
3. **DAT-03:** sistema contábil externo como fonte oficial no MVP.
4. **DAT-04:** analista como usuário diário, contador aprovador, gestor comprador e auxiliar no saneamento.
5. **DAT-05:** import/export genérico mais um conector estratégico.
6. **DAT-06:** aprovação humana de toda proposta com efeito contábil no piloto.
7. **DAT-07:** escritório como tenant padrão e empresas como subescopos.
8. **DAT-08:** M19 — Workflow, Pendências e Aprovações — e auditoria transversal.
9. **DAT-09:** proibir por padrão treinamento com dados dos tenants e minimizar retenção externa.
10. **DAT-10:** classificação da seção 8 como base de MVP, Pós-MVP e Evolução.

### Gate para iniciar a Fase 2

**SUPERADO EM 02/09/2026.** DAT-01 a DAT-10 foram aprovadas, com os refinamentos registrados abaixo. A autorização subsequente abrange arquitetura macro, domínios, modelo de dados, organização modular Python e backlog técnico do MVP; não autoriza implementação de código de produção.

---

## 17. Registro formal de aprovação e refinamentos

| Decisão | Estado aprovado | Refinamento vinculante |
|---|---|---|
| DAT-01 | Aprovada | MVP como camada inteligente integrada, com domínio contábil próprio preparado para evolução a sistema principal. |
| DAT-02 | Aprovada | Duas verticais iniciais: XML/documentos fiscais estruturados e movimentação bancária/extrato. |
| DAT-03 | Aprovada com refinamento | Autoridade por domínio: sistema externo para escrituração, saldos e fechamento oficiais; Serdial21 para documentos processados, propostas, workflow, aprovações, regras, DE/PARA, auditoria, IA e integrações. |
| DAT-04 | Aprovada | Analista opera; contador aprova; gestor administra/compra; auxiliar prepara e saneia; portal da empresa atendida fora do MVP. |
| DAT-05 | Aprovada | Integração em três partes: modelo canônico, layout configurável e conector específico; primeiro MVP inclui formatos genéricos e um conector estratégico. |
| DAT-06 | Aprovada | Todo efeito contábil exige aprovação humana no piloto; automação apenas preparatória; métricas de sugestão, aprovação, correção e rejeição desde o primeiro dia. |
| DAT-07 | Aprovada | Tenant é o escritório; empresa e estabelecimento são subescopos; o modelo deve permitir associação explícita User → TenantMembership → CompanyAccess. |
| DAT-08 | Aprovada fortemente | Nome oficial: M19 — Workflow, Pendências e Aprovações; capacidade transversal obrigatória. |
| DAT-09 | Aprovada | Sem treinamento externo por padrão, retenção mínima e opt-in formal; separar finalidades operacional, inferência, log, melhoria interna e treinamento. |
| DAT-10 | Aprovada | Desenvolvimento por fatias verticais completas, começando por XML e movimentação bancária. |

### Autoridade por domínio aprovada para o MVP

| Domínio | Sistema de registro no MVP |
|---|---|
| Escrituração contábil oficial | Sistema contábil externo |
| Saldos oficiais | Sistema contábil externo |
| Fechamento oficial | Sistema contábil externo |
| Documentos processados e evidências | Serdial21 |
| Propostas e lotes de contabilização | Serdial21 |
| Pendências, tarefas e aprovações | Serdial21 |
| Regras, máscaras e suas versões | Serdial21 |
| Plano operacional importado e DE/PARA | Serdial21, preservando origem e autoridade externa quando aplicável |
| Auditoria do processo Serdial21 | Serdial21 |
| Execuções, sugestões e explicações de IA | Serdial21 |
| Configuração, execução e reconciliação das integrações | Serdial21 |

### Verticais aprovadas

1. **Vertical XML:** empresa → plano/DE-PARA mínimo → recepção de XML estruturado → fato contábil → regra/IA → proposta → aprovação → exportação → confirmação → auditoria.
2. **Vertical bancária:** empresa/conta → importação de extrato → normalização de movimentações → correspondência/conciliação → proposta/pendência → aprovação → bloqueio aplicável → exportação/retorno → auditoria.

Esses refinamentos passam a ser requisitos aprovados da baseline 1.0.
