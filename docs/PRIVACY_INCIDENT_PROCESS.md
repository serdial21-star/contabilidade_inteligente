# Processo de incidente de privacidade — piloto

## Status

Runbook técnico inicial; não substitui plano jurídico, contratual ou regulatório.
Prazos, obrigação de notificar, destinatários e conteúdo de comunicação devem
ser determinados pelo responsável jurídico/encarregado conforme o incidente.

Referências jurídicas a validar pela organização: LGPD arts. 16, 18 e 19
(incluindo declaração completa em até 15 dias), e RCIS/Resolução CD/ANPD
15/2024 (incidente comunicável em 3 dias úteis e registro pelo controlador por
5 anos). A qualificação de controlador/operador e a aplicação concreta dessas
regras continuam `PENDING_HUMAN_LEGAL_APPROVAL`.

## Acionamento

Abrir incidente imediatamente para suspeita ou confirmação de acesso indevido,
perda, alteração, vazamento, envio a destinatário errado, exposição de backup,
comprometimento de credencial, falha de isolamento tenant/company ou exclusão
fora da política. Registrar somente identificador do incidente, timestamps,
operador, sistemas afetados, correlação e evidências técnicas minimizadas.
Nunca copiar XML, OFX, token, senha, dump ou lista completa de titulares ao ticket.

## Fluxo

1. **Detectar e classificar.** Preservar alerta/log sanitizado, origem, escopo
   conhecido e estado da investigação; não concluir impacto sem evidência.
2. **Conter.** Revogar/suspender acesso, token, integração ou rota afetada;
   restringir leitura de storage/backup; bloquear job de descarte. Registrar a
   decisão e evitar destruição de evidência.
3. **Preservar.** Criar legal hold operacional provisório quando o mecanismo
   existir; até lá, suspender remoções manuais e backups expirantes sob ordem do
   responsável. Preservar hashes, `AuditEvent`, correlação e configuração
   relevante em local de acesso restrito.
4. **Investigar.** Equipe técnica avalia categorias, tenants/empresas, período,
   vetores, destinatários, cópias e controles; jurídico/privacidade avalia
   titulares, riscos e deveres de comunicação. Não fazer busca cross-tenant
   ampla sem autorização documentada.
5. **Decidir comunicação.** Encarregado/jurídico decide se, quando e a quem
   notificar; engenharia fornece fatos e linha do tempo, não parecer jurídico.
6. **Erradicar e recuperar.** Corrigir causa, rotacionar segredo se aplicável,
   validar isolamento, restaurar somente por runbook aprovado e confirmar que
   legal hold/retencão não foram violados.
7. **Encerrar e aprender.** Aprovação conjunta de segurança e privacidade,
   relatório minimizado, `AuditEvent` quando aplicável, ações corretivas, teste
   de regressão e revisão da matriz/política.

## Papéis mínimos

- operador de plantão: contenção técnica inicial e escalonamento;
- segurança/engenharia: investigação, correção e evidência técnica;
- responsável do escritório: contexto operacional e autorização de negócio;
- encarregado/jurídico: classificação, comunicação e decisão de privacidade;
- infraestrutura: storage, backup, restore e credenciais.

Uma pessoa não deve aprovar sozinha a destruição de evidência, liberação de
legal hold ou comunicação externa quando a estrutura do piloto permitir
segregação.

## Preparação bloqueante

Antes do piloto, definir contatos 24x7 ou janela de resposta, canal seguro,
matriz de escalonamento, inventário de fornecedores, procedimento de rotação de
segredos, retenção do ticket de incidente e exercício simulado. O coletor de
logs, backup de object storage e legal hold executável ainda são pendências.
