# Mapping de intenção para conta

O mapping versionado aceita `accounting_intent` e categoria opcional e aponta para `AccountVersion.id`, nunca para texto de conta. A precedência é categoria específica → intenção da empresa → template → ausência.

O alvo deve pertencer ao escopo, estar publicado, vigente, ativo e ser analítico/lançável. Sem alvo válido, o resultado é `ACCOUNT_MAPPING_REQUIRED`.
