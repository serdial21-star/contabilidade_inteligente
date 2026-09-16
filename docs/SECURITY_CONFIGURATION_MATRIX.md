# Matriz de configuração de segurança

Valores abaixo são contratos, nunca credenciais. LOCAL corresponde ao literal técnico `development`.

| NAME | PURPOSE | LOCAL | TEST | HOMOLOGATION | PRODUCTION | SECRET? | REQUIRED? | FAIL-CLOSED? |
|---|---|---|---|---|---|---|---|---|
| `SERDIAL21_ENVIRONMENT` | perfil de validação | development | test | homologation | production | não | sim | sim |
| `SERDIAL21_DEBUG` | páginas de debug | false | false | false | false | não | sim | sim fora de local/test |
| `DATABASE_URL` | conexão MySQL | opcional | SQLite permitido | isolada | exclusiva | sim | hom/prod | sim |
| `OIDC_ISSUER` | issuer exato | opcional completo | opcional completo | HTTPS | HTTPS | não | hom/prod | sim |
| `OIDC_AUDIENCE` | audience exclusiva | opcional completo | opcional completo | explícita | explícita | não | hom/prod | sim |
| `OIDC_JWKS_URL` | chaves públicas | opcional completo | opcional completo | HTTPS | HTTPS | não | hom/prod | sim |
| `PUBLIC_FRONTEND_URL` | origem pública | opcional | opcional | HTTPS | HTTPS | não | hom/prod | sim |
| `CORS_ALLOWED_ORIGINS` | origins CSV exatas | vazio/same-origin | explícitas em teste | HTTPS | HTTPS | não | hom/prod | sim |
| `TRUSTED_HOSTS` | hosts CSV exatos | vazio | testserver opcional | obrigatório | obrigatório | não | hom/prod | sim |
| `EXTERNAL_HTTPS` | confirmação da borda TLS | false | false | true | true | não | hom/prod | sim |
| `HSTS_MAX_AGE_SECONDS` | duração HSTS | sem emissão | sem emissão | sem emissão pelo app | 31536000 | não | production | sim |
| `GENERAL_REQUEST_MAX_BYTES` | corpo não-upload | 1048576 | 1048576 | explícito | explícito | não | não | sim |
| `NFE_MAX_XML_BYTES` | upload/parser NF-e | 5242880 | 5242880 | explícito | explícito | não | não | sim |
| `OFX_MAX_UPLOAD_BYTES` | upload/parser OFX | 10485760 | 10485760 | explícito | explícito | não | não | sim |
| `RATE_LIMIT_BACKEND` | coordenação de limites | memory | memory | distributed | distributed | não | sim | sim |
| `RATE_LIMIT_BACKEND_URL` | endpoint/credencial backend | vazio | vazio | provedor | provedor | sim | hom/prod | sim |
| `RATE_LIMIT_*_PER_MINUTE` | políticas por classe | defaults seguros | determinístico | revisado | revisado | não | não | sim |
| `API_DOCS_ENABLED` | Swagger/ReDoc/OpenAPI | true default | true default | false default | false default | não | não | sim |
| `METRICS_ENDPOINT_ENABLED` | exposição operacional opt-in | false | false | conforme infraestrutura | conforme infraestrutura | não | não | sim |
| `METRICS_ACCESS_TOKEN` | autenticação do scrape interno | vazio | sintético se ativado | secret provider | secret provider | sim | se endpoint ativo | sim |
| `OBJECT_STORAGE_PATH` | evidência local | ignorado | temporário | storage isolado | storage privado | potencialmente | sim no deploy | operacional |

O adapter distribuído implementa a porta `RateLimiter` e deve ser injetado na fábrica. Selecionar `distributed` sem adapter interrompe a composição; nunca cai silenciosamente para memória.

Mesmo autenticado, `/internal/metrics` deve ser privado no proxy e inacessível
pelo portal do cliente. O token possui no mínimo 32 caracteres, não aparece em
logs e deve ser rotacionado pelo provedor de segredos.
