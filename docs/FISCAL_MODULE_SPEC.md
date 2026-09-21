# Módulo Fiscal — Phase 07

## Escopo suportado

O módulo operacional suporta exclusivamente **NF-e modelo 55 em XML**, nas versões aceitas pelo `SafeNFe55XmlParser`. CT-e, NFS-e, NFC-e, ZIP, PDF e imagem não fazem parte do contrato. O Serdial21 estrutura evidência e prepara o fluxo; o sistema contábil externo continua sendo a autoridade oficial.

## Importação e processamento

O frontend reutiliza `POST /api/v1/operations/companies/{company_id}/imports/nfe`. O corpo contém os bytes do XML e os cabeçalhos informam tipo, nome seguro e `Idempotency-Key`. Os únicos campos adicionais são os já exigidos pelo caso de uso: data contábil, início/fim do período e expiração da etapa posterior. Eles não são preenchidos por inferência.

O backend revalida principal autenticado, tenant, `CompanyAccess`, permissão `journal.propose`, escopo da empresa, tamanho e tipo do arquivo. Em seguida reutiliza intake, parser NF-e, normalização, deduplicação, quarentena, workflow e auditoria existentes. A interface não aprova proposta nem efetiva escrituração.

## Validação, duplicidade e quarentena

- o XML tem limite configurável (`NFE_MAX_XML_BYTES`, padrão de 5 MiB);
- DOCTYPE, entidades e referências externas são rejeitados pelo parser seguro;
- uma reentrega com mesma chave idempotente e mesmo conteúdo vincula o resultado anterior;
- a mesma chave de acesso NF-e com hash divergente entra no fluxo real de quarentena, sem sobrescrever evidência;
- erros retornam classificação segura, sem XML bruto, caminho ou stack trace.

Antes do envio, a interface mantém uma lista revisável dos XML selecionados e
permite remover individualmente um arquivo escolhido por engano. A expiração da
revisão é informada somente como data; a borda converte o fim do dia escolhido
para o timestamp exigido pelo contrato. A expiração continua obrigatória para
que uma aprovação não permaneça válida indefinidamente.

O contexto de trabalho preenche início e fim pela competência escolhida e
calcula a revisão por uma política explícita: `data da importação + dias` ou
`fim do período + dias`, entre 1 e 90. A primeira é o padrão para não gerar uma
validade vencida ao trabalhar em competência histórica. Os três valores
permanecem visíveis e ajustáveis no formulário. Sem data contábil manual, a
interface lê somente a data de emissão do XML e bloqueia o envio se ela estiver
fora do período; o arquivo permanece selecionado para correção. Uma data
contábil manual dentro do período representa um ajuste consciente, nunca uma
inferência. Essa pré-validação melhora o feedback, mas não substitui o parser
seguro nem a invariante equivalente do backend.

O feedback de importação distingue por nome de arquivo sucesso,
reentrega/duplicidade, divergência de empresa e atenção ou quarentena. No modo
sintético, o resultado declara que é uma simulação sem persistência; não cria
uma NF-e fictícia na consulta. Uma evidência real em quarentena pode não gerar
`FiscalDocument`; por isso continua visível na Central de Documentos e em suas
issues, sem registro fiscal fictício.

## Consulta operacional

`GET .../fiscal-documents` oferece paginação no servidor e filtros por texto (chave, número ou emitente), status observado e intervalo de emissão. O detalhe `GET .../fiscal-documents/{id}` projeta apenas campos canônicos suportados: cabeçalho, emitente/destinatário, valores `Decimal`, status observado, itens e totais tributários já persistidos. Itens são limitados a 200 no detalhe; não há novo cálculo de tributos.

O `observed_status` descreve o protocolo encontrado no XML e não constitui consulta à SEFAZ nem confirmação oficial. O vínculo `document_receipt_id` leva à Central de Documentos sem expor `artifact_id`, chave de storage ou XML bruto.

## Autorização e fronteiras

Leitura exige `company.read`; importação preserva a permissão existente `journal.propose`. Toda consulta contém simultaneamente `tenant_id` e `company_id`, e a aplicação verifica `CompanyAccess` antes do repositório. IDs de outro contexto recebem erro uniforme.

## Exceções e gaps conhecidos

A Central de Documentos e W004 expõem a projeção real de issues existentes. O detalhe fiscal ainda não agrega essa projeção diretamente, então exceções fiscais são **parciais**. Upload em lote, raw XML, verificação online de protocolo, malware scanning, cálculo fiscal completo, obrigações e workflow contábil são adiados ou gaps explícitos.

Na Fase 09, o detalhe de NF-e agrega a Linha da Decisão usando a correlação da evidência real. A linha pode alcançar regra, proposta e decisão somente quando essas transições existem; o status de protocolo continua sendo apenas o observado no XML.
