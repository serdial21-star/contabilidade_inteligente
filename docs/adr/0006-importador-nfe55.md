# ADR 0006 — Importador NF-e modelo 55

## Status

Aceita na Execução 06, em 04/09/2026.

## Contexto

O primeiro insumo real do piloto é a NF-e modelo 55. O XML precisa permanecer
como evidência imutável enquanto a extração produz dados fiscais tipados e
rastreáveis, sem inferir tratamento contábil.

## Decisão

- Nesta primeira materialização, o módulo fiscal_documents é proprietário de
  CanonicalRecord, FiscalDocument, FiscalDocumentItem e TaxDetail. Isso não
  autoriza um futuro canônico bancário a depender de adaptadores fiscais; o
  ownership do envelope genérico deverá ser extraído por decisão aprovada antes
  da entrada de outro tipo canônico.
- A cadeia preservada é EvidenceArtifact, ArtifactReceipt,
  TransformationRun, CanonicalRecord e entidades fiscais tipadas. LineageEdge
  liga cada recebimento à execução que processou ou reutilizou.
- O parser aceita somente as raízes NFe e nfeProc no namespace NF-e, exatamente
  um infNFe e o modelo 55. CT-e, NFS-e, eventos fiscais e interpretação
  contábil permanecem fora desta execução.
- A validação desta etapa é estrutural e explícita; não substitui validação
  integral contra o pacote oficial de XSD nem validação XMLDSIG.
- DTD, entidades internas/externas e notações são recusadas por um pré-parse
  Expat encoding-aware antes da construção da árvore. UTF-32 é recusado
  explicitamente. O tamanho máximo é configurável por NFE_MAX_XML_BYTES,
  ligado pela composição interna, e começa em 5 MiB.
- Chave, dígito verificador, modelo embutido, versões do envelope e vínculo da
  chave com o protocolo são validados sem consultar fonte externa.
- Valores numéricos são Decimal finitos e precisam caber exatamente na
  precisão/escala persistida. Não há quantização, arredondamento ou truncamento.
  indTot aceita somente 0/1. Ausências permanecem nulas e produzem
  ValidationIssue quando o campo é acompanhado.
- O subconjunto tributário tipado desta versão cobre ICMS, ICMSUFDest, IPI, II,
  PIS, PISST, COFINS, COFINSST e ISSQN. Grupo presente fora desse subconjunto
  gera warning explícito, sem inferência nem descarte silencioso.
- O parser registra sua versão, a versão indicada por infNFe, o hash de
  origem e o fingerprint SHA-256 da representação canônica.
- Mesma chave no mesmo tenant/company e mesmo hash é reentrega idempotente:
  preserva novo ArtifactReceipt e reutiliza o documento canônico existente.
- Mesma chave e hash diferente gera TransformationRun com falha,
  ValidationIssue NFE_ACCESS_KEY_HASH_CONFLICT e estado de quarentena. O
  documento anterior não é alterado e a linhagem registra CONFLICTS_WITH.
- Documentos, itens, tributos, envelope canônico e TransformationRun terminal
  são imutáveis na aplicação.
- Consultas e chaves estrangeiras carregam tenant e company; cada importação
  revalida a autorização documental após o parse e antes de revelar ou criar
  um resultado fiscal.

## Precisão adotada

- Totais, bases e valores tributários: NUMERIC(20,2).
- Quantidades: NUMERIC(20,6).
- Valores unitários: NUMERIC(20,10).
- Alíquotas: NUMERIC(12,6).

Essas escalas preservam os valores capturados e não autorizam arredondamento
ou decisão contábil. Divergências aritméticas e regras fiscais adicionais
exigirão políticas explícitas em evolução posterior.

## Consequências

XML inválido, hostil, excessivo ou conflitante permanece como evidência e
recebe transformação falha e issue estruturada, sem gerar FiscalDocument ou
CanonicalRecord. Uma NF-e estruturalmente válida pode conter warnings por
campos ausentes; os campos ficam nulos e rastreáveis.

O status REPORTED_AUTHORIZED significa apenas que o XML recebido informou
cStat 100 em protocolo ligado à mesma chave. Ele não declara validade
criptográfica, confirmação online nem autoridade sobre escrituração.

O repositório ainda não contém o bundle oficial de XSD, corpus homologado ou
infraestrutura MySQL de testes. Validação XSD/XMLDSIG, idempotência concorrente
com duas transações e atualização conciliável dos estados de ImportItem/Batch
permanecem pendências explícitas; a restrição única no banco impede dois
FiscalDocument para a mesma chave no mesmo tenant/company.

O fluxo é um caso de uso interno. API autenticada, upload HTTP e processamento
assíncrono não fazem parte desta execução.
