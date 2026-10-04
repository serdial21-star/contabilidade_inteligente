# Google Colab — autenticação da integração CND

Crie no painel **Secrets** do Colab um secret chamado `SERDIAL21_CND_INTEGRATION_SECRET`, conceda acesso ao notebook e não escreva seu valor em nenhuma célula.

Use o cabeçalho abaixo na chamada já existente. O payload é ilustrativo: mantenha os campos reais que o extrator já produz.

```python
from google.colab import userdata
import requests


def enviar_cnd(payload: dict[str, object]) -> dict[str, object]:
    integration_secret = userdata.get("SERDIAL21_CND_INTEGRATION_SECRET")
    if not integration_secret:
        raise RuntimeError("Secret da integração CND não configurado no Colab")

    response = requests.post(
        "https://n8n.serdial21.com/webhook/admin/integracao-cnd-v1",
        json=payload,
        headers={"X-Serdial21-Integration-Secret": integration_secret},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()
```

O mesmo valor deve existir somente na credencial **Header Auth** associada ao nó Webhook do n8n. Para rotacionar, crie um valor aleatório novo, atualize a credencial e o Secret em uma janela coordenada e teste o reenvio. Não coloque o valor no workflow, notebook, chat, tarefa ou log.
