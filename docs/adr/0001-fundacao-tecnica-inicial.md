# ADR 0001 — Fundação técnica inicial

- Status: aceito
- Data: 2026-09-03
- Escopo: primeira fatia executável do backlog S0

## Contexto

O repositório continha a engenharia aprovada e o baseline técnico, mas ainda
não possuía aplicação, dependências, testes ou infraestrutura de migrations.
A stack foi determinada nas instruções permanentes: Python 3.12+, FastAPI,
SQLAlchemy 2.x, Alembic, MySQL/PyMySQL, Pydantic 2, Pydantic Settings e Pytest.

Os documentos anteriores ainda registram como pendentes algumas decisões que
foram parcialmente resolvidas por essa determinação de stack. Também há duas
nomenclaturas de domínios que precisam de um mapa explícito antes de se criarem
pacotes de negócio.

## Decisão

Implementar somente a fundação horizontal nesta primeira fatia:

1. layout Python src;
2. fábrica da aplicação FastAPI;
3. configurações tipadas e carregadas do ambiente;
4. endpoint de vivacidade sem dependência do banco;
5. identificador de correlação HTTP validado como UUID;
6. metadados SQLAlchemy e ambiente Alembic sem tabelas;
7. testes unitários e de API.

A URL de banco é tratada como segredo. Ambientes staging e production exigem
sua configuração; production não permite modo debug.

O endpoint de vivacidade prova somente que o processo HTTP responde. Um futuro
endpoint de prontidão poderá verificar dependências sem mudar essa semântica.

## Consequências

- a aplicação pode iniciar e ser testada antes da modelagem empresarial;
- nenhuma estrutura contábil é inferida ou antecipada;
- migrations futuras usarão convenção determinística de nomes;
- toda resposta HTTP recebe X-Correlation-ID;
- a definição de compatibilidade do MySQL e o modelo físico de tenancy seguem
  pendentes.

## Decisões deliberadamente adiadas

- mapa entre os domínios lógicos e os módulos aprovados;
- versão mínima e política de suporte do MySQL;
- estratégia física de isolamento por tenant;
- autenticação e autorização;
- estratégia de IDs empresariais;
- storage de documentos, filas/jobs e observabilidade;
- provedor de IA e conectores externos.

