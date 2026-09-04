# ADR 0005 — Evidência documental imutável

## Status

Aceita na Execução 05, em 04/09/2026.

## Contexto

O Serdial21 precisa preservar o conteúdo bruto recebido como evidência,
distinguir cada recebimento e rastrear transformações sem implementar ainda
um parser fiscal. Arquivos grandes no MySQL aumentariam custo, contenção e
dificultariam a futura adoção de armazenamento de objetos.

## Decisão

- O módulo intake_documents possui domínio puro, casos de uso, portas e
  adaptadores privados.
- EvidenceArtifact é tenant-scoped, imutável e deduplicado pela combinação
  tenant, algoritmo e hash SHA-256.
- O conteúdo binário fica no ObjectStorage. O banco armazena somente hash,
  tamanho, tipo de mídia, classificação, chave e timestamps.
- A chave de armazenamento é derivada do tenant e do hash. O adaptador local
  usa criação exclusiva, verifica colisões e impede escape do diretório raiz.
- Cada chegada gera novo ArtifactReceipt e ImportItem, mesmo quando o
  EvidenceArtifact já existe.
- ImportBatch é idempotente por tenant, company, origem e chave fornecida.
- Uma empresa somente transforma artefato para o qual tenha recebimento no
  mesmo tenant e company.
- Todo caso de uso exige AuthorizationService, membership e CompanyAccess
  ativos e a permissão atômica company.manage antes de qualquer efeito.
- TransformationRun concluída é imutável. Nova tentativa cria outro run e
  pode referenciar o anterior.
- ValidationIssue é estruturada e append-oriented.
- LineageEdge registra origem e destino no mesmo tenant/company e recusa
  auto-referência e ciclos conhecidos.
- Metadados documentais e seus eventos de auditoria usam a mesma Session e a
  mesma transação.
- Não há API pública nem conhecimento de NF-e nesta execução.

## Consequências

Repetir um upload preserva a evidência existente e cria uma nova prova de
recebimento. O arquivo é gravado antes da transação relacional, pois uma
chamada a object storage não deve ocorrer dentro da transação de negócio.
Se o banco falhar depois da gravação, pode restar um objeto endereçado por
conteúdo sem metadado; reconciliação e coleta segura desses órfãos ficam para
uma evolução específica.

O adaptador local atende desenvolvimento e testes. Produção deverá fornecer
outro adaptador para a mesma porta, com criptografia, retenção, versionamento,
controle de acesso e observabilidade definidos na infraestrutura escolhida.
