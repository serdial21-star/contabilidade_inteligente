# Inicialização local padronizada

## Caminho recomendado para testes de interface

Na raiz do projeto, abra com dois cliques:

```text
INICIAR_SERDIAL21.cmd
```

O inicializador abre automaticamente o endereço único:

```text
http://127.0.0.1:8080/app/
```

Na tela inicial, selecione **Abrir demonstração sintética**. Esse modo usa
somente dados fictícios versionados, não exige banco, `.env`, API, login ou
conexão externa e é o caminho padrão para validar a interface nesta etapa.
O servidor aceita conexões somente do próprio computador e expõe apenas os
ativos públicos de `app/` e `ui/`; `.env`, código-fonte e demais arquivos do
repositório não são disponibilizados.

Mantenha a janela `Serdial21 - Ambiente local` aberta enquanto estiver usando o
sistema. Para encerrar, pressione `Ctrl+C` ou feche essa janela. Na próxima vez,
use novamente o mesmo arquivo e o mesmo endereço.

## Diagnóstico rápido

- Se a janela informar que a porta 8080 está em uso, feche uma inicialização
  anterior do Serdial21 e tente novamente.
- Se o navegador não abrir sozinho, mantenha a janela aberta e acesse
  `http://127.0.0.1:8080/app/` manualmente.
- Se aparecer uma mensagem sobre Python, instale o Python 3.12 ou superior ou
  restaure o ambiente virtual `.venv` do projeto.
- Não abra `app/index.html` diretamente. O navegador exige um servidor local
  para aplicar corretamente os recursos e as políticas de segurança da página.

## Uso pelo terminal

O mesmo inicializador pode ser executado no PowerShell:

```powershell
.\INICIAR_SERDIAL21.cmd
```

Para validar os pré-requisitos sem iniciar o servidor:

```powershell
.\INICIAR_SERDIAL21.cmd --check
```

Este inicializador é exclusivo para desenvolvimento e demonstração sintética.
Ele não substitui o runtime da API, migrations, MySQL, OIDC ou o processo de
homologação/produção.
