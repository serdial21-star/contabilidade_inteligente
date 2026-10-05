-- Diagnóstico somente leitura para decisão humana após a migration 0017.
-- Lista jornadas não rejeitadas que não são a dona da reserva ativa.
WITH latest AS (
  SELECT c.*,
         ROW_NUMBER() OVER (
           PARTITION BY tenant_id, company_id, journey_id ORDER BY version DESC
         ) AS journey_rank
  FROM nfe_journey_checkpoints c
  WHERE fiscal_document_id IS NOT NULL
)
SELECT l.tenant_id, l.company_id, l.fiscal_document_id,
       r.journey_id AS reserved_journey_id, l.journey_id AS duplicate_journey_id,
       l.status, l.version
FROM latest l
JOIN nfe_journey_document_reservations r
  ON r.tenant_id = l.tenant_id
 AND r.company_id = l.company_id
 AND r.fiscal_document_id = l.fiscal_document_id
 AND r.active_marker = 'ACTIVE'
WHERE l.journey_rank = 1
  AND l.status NOT IN ('REJECTED', 'SUPERSEDED')
  AND l.journey_id <> r.journey_id
ORDER BY l.tenant_id, l.company_id, l.fiscal_document_id, l.journey_id;
