# Máscara de código contábil

A máscara é estrutural: larguras ordenadas e separador único não alfanumérico. Exemplo `(1,2,2,4)` com `.` aceita `1.02.03.0001`. Ela valida formato, mas não infere hierarquia.

Mudança que invalide contas existentes deve ser rejeitada e tratada em nova versão governada do catálogo.
