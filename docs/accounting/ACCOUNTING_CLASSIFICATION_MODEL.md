# Modelo de classificação contábil

`ItemEvidence` preserva empresa, documento/item, fornecedor, código do fornecedor, GTIN, descrição original, NCM, CFOP, CST e valor. `ItemClassification` registra intenção, categoria, confiança, estado, regra e evidências.

Estados: `AUTO_CLASSIFIED`, `PRE_CLASSIFIED`, `REVIEW_REQUIRED`, `CONFLICTING_EVIDENCE` e `ACCOUNT_MAPPING_REQUIRED`. `AUTO_CLASSIFIED` autoriza somente preparar proposta; aprovação profissional continua obrigatória.
