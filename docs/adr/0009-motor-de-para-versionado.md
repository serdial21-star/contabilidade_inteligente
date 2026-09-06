# ADR 0009 — Motor de DE/PARA versionado

MappingVersion usa os estados `DRAFT`, `IN_REVIEW`, `PUBLISHED`, `SUSPENDED`
e `RETIRED`. Conteúdo publicado é imutável; mudança cria nova versão.

A simulação considera vigência e todos os seletores declarados (código externo,
histórico, dimensão e entidade canônica). Uma única regra de maior prioridade
produz resultado; empate devolve `CONFLICT`, sem escolha arbitrária. O alvo só
é aceito se a `AccountVersion` estiver publicada, vigente e lançável.
