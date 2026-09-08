# Revisão humana UAT contábil

`ACCOUNTANT_SIGNOFF = PENDING`. Esta folha não representa aprovação automática.

| Scenario | Expected debit | Expected credit | Amount | Rule | Status | Reviewer | Approved/Rejected | Notes |
|---|---|---|---:|---|---|---|---|---|
| UAT-NFE-01 | 1.1 | 3.1 | 100.00 | nfe55 | PENDING |  |  |  |
| UAT-NFE-02 | 1.1 | 3.1 | 100.00 | nfe55 retry | PENDING |  |  |  |
| UAT-NFE-03 | N/A | N/A | N/A | quarantine | PENDING |  |  |  |
| UAT-OFX-01 | N/A | N/A | -10.00 | import only | PENDING |  |  |  |
