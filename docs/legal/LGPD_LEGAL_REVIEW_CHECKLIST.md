# Checklist de revisão jurídica LGPD

Todas as caixas requerem evidência e responsável humano; não são declarações de conformidade.

- [ ] qualificar controlador(es), operador(es), suboperadores e encarregado;
- [ ] validar categorias de titulares/dados, finalidades e minimização;
- [ ] escolher e documentar base legal por finalidade;
- [ ] definir retenção, gatilho, exceções, hold, backup e descarte;
- [ ] aprovar canal DSR, prova de identidade, alçadas, respostas e prazos;
- [ ] avaliar necessidade e aprovar RIPD/ROPA;
- [ ] aprovar aviso de privacidade, termos, contrato SaaS, DPA e anexo de segurança;
- [ ] confirmar fornecedores, países/regiões, transferências e subcontratação;
- [ ] validar cookies/Web Storage, marketing e mecanismo de consentimento se aplicável;
- [ ] definir processo para menores e categorias sensíveis, mesmo não sendo público-alvo;
- [ ] aprovar critérios, contatos, registro e comunicações de incidente;
- [ ] alinhar encerramento, exportação, devolução, eliminação e restauração;
- [ ] verificar coerência entre contratos, produto, operação e evidências técnicas;
- [ ] registrar versão, aprovadores, vigência, exceções e próxima revisão.

**Resultado obrigatório:** `PENDING_HUMAN_APPROVAL` até assinatura/registro formal. Revisão jurídica não substitui validação técnica de produção.

## Separação dos gates

| Categoria | Itens |
|---|---|
| TECHNICALLY_VERIFIED | isolamento, minimização, dry-run, Legal Hold, DSR parcial, auditoria, logs/métricas e documentação de restore |
| BUSINESS_DECISION_REQUIRED | finalidades aprovadas, owners, canal DSR, alçadas, corpus e critérios do piloto |
| LEGAL_REVIEW_REQUIRED | papéis, bases, prazos, direitos, incidentes, RIPD/ROPA e transferências |
| CONTRACT_REQUIRED | SaaS, DPA, anexo de segurança, subcontratação, SLA e saída |
| PROVIDER_CONFIRMATION_REQUIRED | regiões, criptografia em repouso, chaves, backup, IdP, monitoramento e exclusão |

`TECHNICAL_PRIVACY_GATE = PASS`; `LEGAL_REVIEW_GATE = PENDING`;
`CONTRACTUAL_GATE = PENDING`. Esses estados são independentes e não autorizam
dados reais ou exposição externa.
