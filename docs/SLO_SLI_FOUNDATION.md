# Fundação de SLI/SLO do piloto

Esta fundação define medição, não SLA contratual nem compromisso percentual.
Metas numéricas só serão propostas após volume sintético representativo e
capacidade de monitoramento contínuo.

| SLI | Medição | Fonte | Observação inicial |
|---|---|---|---|
| Disponibilidade | requests atendidos / requests elegíveis | status HTTP por template | separar 5xx de 4xx |
| Taxa de 5xx | respostas 5xx / requests | `http_errors_total`, `http_requests_total` | 409/422/429 não são falha do serviço |
| Latência HTTP | duração por método/template/status class | `http_request_duration_seconds` | percentis no backend futuro |
| Sucesso documental | sucessos / tentativas por `nfe|ofx` | `document_import_total` | sem dimensão de cliente |
| Processamento | duração por fonte/resultado | `document_processing_duration_seconds` | NF-e instrumentada; OFX ao ganhar caso de uso equivalente |
| Backup | último backup verificado dentro do RPO | metadado/hash/job | exit code sozinho não basta |
| Recuperação | drills aprovados / drills executados | relatório de drill | local e MariaDB são evidências distintas |

O piloto começa coletando distribuição e volume por ambiente. O review semanal
define baseline, qualidade dos sinais, janelas e orçamento de erro experimental.
LOCAL/TEST nunca alimentam painel de produção sem identificação explícita.
