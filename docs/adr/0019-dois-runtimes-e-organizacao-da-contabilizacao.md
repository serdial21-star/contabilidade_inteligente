# ADR 0019 — Dois runtimes, um produto, e a organização da contabilização

## Status

**Aceita pelo proprietário em 05/10/2026** (item 1 da resposta à pesquisa), com o registro abaixo.
Base: [pesquisa de 04–05/10/2026](../PESQUISA_ARQUITETURA_A_B_CONTABILIZACAO_2026-10-05.md).

### Registro das respostas do proprietário (05/10/2026)

1. ADR 0019: **aprovado**.
2. Empresas piloto: os clientes de teste do Sistema A "Fenix teste" e "Teste T-0003". Ponto em aberto: se os documentos usados serão fictícios (piloto sintético) ou reais de outra empresa.
3. Duas pessoas indicadas para o piloto (segregação). A identificação fica fora do repositório (minimização, AGENTS.md §6.9). Elas precisam ser funcionários do Sistema A, porque a ponte só aceita sessões de funcionário.
4. Responsável pelas seis condições de dados reais: o proprietário.
5. Leiaute de importação do Domínio: o proprietário não consegue obter o leiaute nem o golden file pelo suporte. Ele pediu para construir a exportação "de acordo com os manuais". O alcance está em aberto: exportação pelo manual público do Domínio, validada por importação real no Domínio, ou escrituração própria (R2).
6. Data contábil da NF-e de entrada: **data de entrada**. Como o XML não traz a data de entrada no estabelecimento, a forma de informá-la ainda precisa ser definida.

## Contexto

Em 04/10/2026 o proprietário definiu que o Sistema B vai consumir as informações do Sistema A para contabilizar. A contabilização se organiza em seis áreas: caixa de entrada, documentos, fiscal, financeiro, contábil e relatórios. Ele perguntou se o B deve continuar separado ou ser agrupado ao A, e pediu um protótipo funcional o mais breve possível.

A pesquisa constatou cinco pontos:

1. O B tem a fundação de governança pronta. O livro contábil, porém, não existe em tabelas: o pré-lançamento só vive no JSON das jornadas de NF-e.
2. Relatórios estão fora do escopo aprovado do MVP (`docs/engenharia-produto/14-backlog-tecnico-mvp.md:27`).
3. Só pode existir uma escrituração principal por empresa e período (Manual da ECD, leiaute 9, itens 1.7 e 1.9). A emissão de relatórios e demonstrativos é responsabilidade exclusiva de contador habilitado (ITG 2000 (R1), item 12).
4. O baseline marca `REAL DATA = NO_GO`, com seis condições formais.
5. A mesma NF-e pode gerar duas propostas: um defeito pré-existente.

## Decisão

1. **Dois runtimes, um produto.**
   - A e B continuam separados em código, banco, credenciais e publicação.
   - A união é de experiência: entrada pelo login do A (ponte do ADR 0014), menu, links diretos validados e identidade visual. Sem iframe.
   - Ficam mantidos os ADRs 0014 e 0015: sem banco compartilhado, sem FK ou consulta entre bancos, e sincronização só por contrato.

2. **Divisão de responsabilidade.**
   - O A é dono do relacionamento com o cliente: portal, chamados, envio de arquivos, operação, honorários e publicações.
   - O B é dono de toda inteligência fiscal e contábil **nova**.
   - As ferramentas fiscais já existentes no A (Extrator XML, Apuração ICMS) recebem só correção de defeito e segurança.
   - O item 23 da fila (apuração por IA) passa a ser futuro do B.

3. **Seis áreas no B:** Caixa de entrada, Documentos, Fiscal, Financeiro, Contábil e Relatórios, com os papéis da seção 6 da pesquisa.

4. **Autoridade da escrituração (R3).**
   - O sistema contábil externo (Domínio) continua sendo o livro oficial.
   - O B emite **prévias internas** de Diário, Razão, Balancete, BP e DRE, calculadas a partir de saldo de abertura importado e de lançamentos aprovados internamente.
   - **No piloto, as prévias não podem ser entregues a clientes ou terceiros.** Cada prévia é emitida por contador identificado.
   - Cada prévia leva o título "Prévia gerencial — não constitui escrituração contábil oficial", a data de corte, a base de cálculo, a fonte do saldo de abertura e as pendências que ficaram de fora.
   - A prévia não tem termos de abertura ou encerramento, assinatura nem arquivo em formato SPED.
   - Esta decisão amplia de forma explícita o limite do backlog ("O MVP não promete razão, saldo ou fechamento oficial"). O B continua sem prometer oficialidade.

5. **Livro do B nos requisitos da ITG 2000.**
   - Lançamentos em tabelas, com:
     - número sequencial atribuído na aprovação, por empresa e exercício;
     - histórico obrigatório, em texto ou padrão versionado;
     - data do fato, distinta da data de registro;
     - vínculo à evidência;
     - período contábil.
   - Edição livre só antes da aprovação. Depois da aprovação, a correção é feita por estorno, transferência ou complemento, como lançamento novo vinculado ao original (DL 486/1969, art. 2º, §2º; ITG 2000, itens 31–36).
   - A correção por nova revisão de lançamento já aprovado deixa de ser permitida no domínio.

6. **Exportação ao Domínio.**
   - A exportação prevista no MVP (S6, INT-909) continua sendo o caminho para eliminar o trabalho em dobro.
   - Ela segue bloqueada até o leiaute oficial e o golden file, que o proprietário solicita ao suporte do Domínio.

7. **Ordem do protótipo** (detalhes na seção 8 da pesquisa):
   - primeiro, o B funciona sozinho, com upload manual de documentos de empresas piloto autorizadas;
   - depois, o primeiro fluxo automático A→B: o B busca no A o XML da NF-e, com filtro imposto pelo A e token assimétrico verificado numa Edge Function.
   - Esse fluxo exigirá **ADR próprio**, como segunda exceção nomeada ao gate do Connect Hub. O ADR deve trazer critérios concretos de homologação e declarar o desvio do transporte previsto em `CONNECT_HUB_ARCHITECTURE.md`.
   - O gate continua `NO_GO` para todo o resto.

8. **Pré-requisitos antes de dados reais:**
   - as seis condições do baseline, com responsável e registro: corpus autorizado, aceite do contador, aprovação jurídica e de privacidade, migration 0012 verificada, backup prévio e aprovação operacional de privacidade;
   - backup do armazenamento de evidências;
   - retenção provisória: nada é eliminado durante o piloto;
   - unicidade de proposta por documento, com reprocessamento explícito;
   - cabeçalhos anti-iframe no servidor;
   - duas pessoas no piloto, para manter a segregação (quem importa não aprova).

## Fora desta decisão

Cada item abaixo exige decisão própria:
- livro oficial e ECD (R2);
- EFD;
- guarda de certificado digital de cliente;
- IA de extração;
- multi-tenant do A;
- sincronização de clientes;
- retorno de status ao portal;
- entrega de prévias a clientes;
- tratamento contábil de IBS/CBS;
- data contábil da entrada (emissão ou entrada), que é decisão do contador.

## Consequências

- O backlog ganha, em ondas:
  - reserva por documento e reprocessamento;
  - livro em tabelas;
  - edição antes da aprovação;
  - caixa de entrada genérica;
  - financeiro com proposta;
  - saldos de abertura;
  - prévias internas;
  - exportação ao Domínio, quando houver leiaute.
- As fatias S0–S8 continuam válidas. Esta decisão antecipa parte do EP6 (pré-ledger) e acrescenta a prévia de relatórios.
- O B continua vendável sem o A. A venda do A a outros escritórios segue como iniciativa separada.
- Toda nova fronteira exige testes negativos entre tenants e entre empresas (AGENTS.md §6.4).
- Os relatórios internos ficam sob responsabilidade de contador. A IA nunca aprova nem emite.
