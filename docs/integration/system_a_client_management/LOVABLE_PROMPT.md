# Prompt para o Lovable

```text
Atualize somente a administracao e recuperacao de clientes do Sistema A.
Preserve o layout, a identidade visual, as rotas existentes e as telas de
login administrativo. Nao altere o Sistema B.

1. Em src/pages/admin/AdminClientes.tsx:
- aceite status Ativo, Inativo e Lead na criacao e edicao;
- o status deve vir da API, nunca ficar fixo como Ativo;
- mostre nome, CPF/CNPJ, e-mail, WhatsApp e status retornados por
  /admin/clientes-v2;
- envie para /admin/novo-cliente-v2 os campos nome_cliente, email, cnpj_cpf,
  whatsapp e status;
- normalize somente para validacao local: remova ponto, barra, hifen e espaco
  e converta letras para maiusculas;
- CPF deve ter 11 digitos e DVs validos;
- CNPJ deve ter 14 posicoes, aceitar [0-9A-Z] nas 12 primeiras, exigir dois
  digitos ao final e validar os DVs pelo modulo 11 oficial, usando o valor
  ASCII do caractere menos 48;
- nao remova letras do CNPJ durante a digitacao;
- aplique mascara somente na exibicao. CPF: 000.000.000-00. CNPJ numerico:
  00.000.000/0000-00. Para CNPJ alfanumerico, preserve letras maiusculas e use
  a mesma separacao visual;
- Lead pode ficar sem CPF/CNPJ. Ativo e Inativo exigem documento valido;
- erros do frontend sao apenas conveniencia. Exiba as mensagens devolvidas
  pela API sem considerar o frontend autoridade da validacao.

2. Em src/pages/RedefinirSenha.tsx:
- leia o token exclusivamente do fragmento #token=;
- remova o fragmento da barra com history.replaceState sem recarregar;
- nunca mostre nem registre o token;
- mantenha o POST existente para /portal/redefinir-senha com
  { token, nova_senha };
- exija 12 a 128 caracteres, ao menos uma letra e um numero, e confirmacao;
- sem token, mostre link invalido e permita solicitar outro;
- nao volte a aceitar token em query string.

3. Em src/pages/EsqueciSenha.tsx:
- preserve o POST para /portal/solicitar-senha;
- sempre apresente a mesma confirmacao neutra, exista ou nao o e-mail;
- nao registre o e-mail em console ou telemetria.

4. Contratos e seguranca:
- continue usando o proxy-webhook existente;
- nao inclua senha provisoria, token, segredo ou credencial no codigo;
- nao use Math.random para token;
- nao crie validacao que dependa somente da interface;
- nao mude os paths dos webhooks;
- nao publique nem faça deploy automaticamente.

5. Testes obrigatorios:
- CPF valido e invalido;
- CNPJ numerico valido e invalido;
- CNPJ alfanumerico valido e invalido;
- Lead sem documento;
- Ativo/Inativo sem documento rejeitado;
- exibicao dos tres status;
- token lido do fragmento e removido da URL;
- build completo sem erros.

Ao concluir, apresente os arquivos alterados, o diff resumido e os testes.
Pare antes de publicar.
```
