# Anexo de segurança da informação — insumo técnico

**DRAFT — CONTRACTUAL_COMMITMENT_NOT_APPROVED**

Controles existentes: autenticação OIDC suportada; autorização tenant/company e menor privilégio; validação de entrada; documentos com hash e chave protegida; trilha append-oriented; segredos por ambiente; logs sanitizados; métricas sem labels empresariais; testes automatizados; backup/restore tooling; resposta a incidente e change control.

Controles condicionais à infraestrutura: TLS, criptografia em repouso, gestão de chaves, segregação de rede, hardening, patches, varredura, agregação/alertas, backup externo, regiões e disponibilidade. Marcar como obrigação somente após fornecedor e operação comprovarem o controle.

Exclusões atuais: sem produção, dados reais, IdP produtivo, SIEM, object-storage backup homologado, IA externa, System A ou Domínio. Prazos, RPO/RTO, retenção, auditorias, pentest e notificações exigem aprovação contratual e capacidade operacional verificável.
