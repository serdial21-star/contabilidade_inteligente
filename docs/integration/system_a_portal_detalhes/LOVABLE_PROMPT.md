# Prompt para o Lovable — T-0008

Cole somente o texto depois da linha horizontal. Revise o diff antes de
publicar. Não inclua dados reais no chat do Lovable.

---

Implemente a interface de detalhe e complemento de chamados e documentos sem
alterar autenticação, rotas ou outras páginas.

## Contrato do portal

- Continue usando `portalFetch` → `proxy-webhook`, sempre com o token já
  gerenciado pela sessão. Não aceite `cliente_id` na tela e não envie token no
  corpo.
- `POST /portal/detalhe-chamado`: `{ ticket_id: number }`.
- `POST /portal/detalhe-documento`: `{ documento_id: number }`.
- Resposta de detalhe: `{ success: true, data }`. Em `data`, renderize
  `complementos` em ordem recebida. Cada item possui `id`, `mensagem`,
  `arquivo_url?`, `arquivo_nome?`, `criado_em`, `autor?` e
  `tipo?: "cliente" | "equipe"`.
- No chamado, exiba também `anexos_abertura` quando houver. Cada item possui
  `nome`, `tipo` e `arquivo_url`.
- `POST /portal/complementar-chamado`: `{ ticket_id, mensagem,
  arquivo_base64?, arquivo_nome? }`.
- `POST /portal/complementar-documento`: `{ documento_id, mensagem,
  arquivo_base64?, arquivo_nome? }`.

## Validação antes do envio

- Aceite no máximo um arquivo e no máximo 10 MiB (10 × 1024 × 1024 bytes).
- Chamados: PDF, JPG/JPEG e PNG. Documentos: os mesmos tipos e XML.
- Exija mensagem não vazia ou arquivo; mensagem com no máximo 5000 caracteres.
- Não confie só em `accept`: confira `File.type`, extensão e tamanho antes de
  chamar `FileReader.readAsDataURL`. O servidor fará nova validação pelo
  conteúdo.
- Mostre erro local claro e não faça a chamada quando a validação falhar.

## Estados e erros

- Preserve as regras atuais que desabilitam complemento em chamado concluído e
  documento processado, concluído ou rejeitado.
- Durante detalhe e envio, desabilite ações duplicadas e mostre carregamento.
- `401`: encerre a sessão pelo fluxo já existente. `404`: mensagem neutra de
  recurso indisponível. `409`: item encerrado. `422`: entrada/arquivo inválido.
  `500`: falha temporária sem afirmar que o complemento foi salvo.
- Após sucesso, recarregue o detalhe e a lista correspondente; não altere o
  status localmente.

## Painel administrativo

Em `AdminDocumentos`, preserve a chamada e os campos atuais de
`/admin/documentos-v2`. Quando um documento tiver `complementos`, mostre uma
linha do tempo cronológica com mensagem, autor/tipo, data e link/nome do anexo.
Não permita resposta da equipe nesta tarefa e não altere status. Estados vazios
devem dizer que ainda não há complementos.

## Restrições

- Não crie rota, fallback, armazenamento local ou chamada direta ao n8n.
- Não registre token, base64, conteúdo de mensagem ou URL de anexo em console,
  analytics ou logs.
- Não mude Certidões, Livros, Obrigações, Inteligência Fiscal nem telas fora do
  detalhe/painel descrito.

Ao concluir, liste arquivos alterados e descreva como testou: mensagem somente,
arquivo válido, arquivo acima de 10 MiB, tipo inválido, item fechado, 401, 404,
409 e 422.
