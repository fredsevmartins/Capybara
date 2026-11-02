# Guia do Capybara em português

O **Capybara 1.0.0** organiza experimentos científicos em pacotes `.orepro`: dados,
protocolos, scripts, resultados e histórico ficam juntos, com inventário e hashes.
O nome do repositório é Capybara; o programa e o módulo Python continuam chamados
**openrepro**. Você não precisa de conta no PyPI nem de ChatGPT para usar o produto.

## 1. Instalar

Use Python 3.11, 3.12 ou 3.13. Abra o terminal numa pasta de trabalho e crie um
ambiente separado:

```bash
python -m venv .venv
```

Ative com `source .venv/bin/activate` no Linux/macOS ou
`.venv\Scripts\Activate.ps1` no PowerShell do Windows. Em seguida:

```bash
python -m pip install 'https://github.com/fredsevmartins/Capybara/releases/download/v1.0.0/openrepro-1.0.0-py3-none-any.whl'
openrepro version --json
```

O resultado deve indicar `1.0.0`. A instalação baixa dependências; depois disso,
a criação e validação de pacotes funcionam localmente sem conexão. A
[instalação detalhada](installation.md) explica outras opções e a conferência de hashes.

## 2. Criar um primeiro experimento

Em uma pasta nova, crie um arquivo `protocolo.txt` descrevendo os procedimentos.
Os comandos abaixo não executam análise nem enviam dados para a Internet:

```bash
openrepro init experimentos/estudo --title 'Meu estudo' --description 'Exemplo de treinamento' --author 'Seu nome' --reproduction 'Leia protocol/protocolo.txt' --json
openrepro add experimentos/estudo protocolo.txt --role protocol --json
openrepro inspect experimentos/estudo --json
openrepro validate experimentos/estudo --json
```

Substitua título, descrição e autor pelos dados reais. A licença padrão dos dados
é CC-BY-4.0; escolha outra com `--license` se necessário e se tiver direito de
aplicá-la. A licença MIT do programa é independente da licença dos seus dados.

A validação informa:

| Resultado | Interpretação |
| --- | --- |
| PASS | As verificações implementadas de estrutura e integridade passaram |
| WARN | A operação terminou, mas existem observações para revisar |
| FAIL | Existem problemas que precisam ser corrigidos antes de compartilhar |
| NOT_EVALUATED | A validade científica não foi avaliada pelo programa |

PASS não prova que a hipótese, os dados ou o método científico estão corretos.
Confira os itens de `issues` quando houver WARN ou FAIL.

## 3. Gerar um pacote e abrir uma cópia

```bash
openrepro export experimentos/estudo estudo.orepro --json
openrepro import estudo.orepro experimentos/copia --json
openrepro validate experimentos/copia --json
```

O arquivo `estudo.orepro` pode ser preservado ou compartilhado. A importação não
executa scripts. Use destinos novos: o programa evita substituir arquivos existentes.
Não edite os hashes manualmente para esconder alterações; use os comandos de
[edição](editing.md), valide e gere um novo pacote.

## 4. Compartilhar e obter DOI

`openrepro publish estudo.orepro --catalog catalogo --json` guarda uma revisão
imutável no catálogo **local**. Isso não publica na Internet e não cria um DOI.

Para um depósito público, escolha uma das opções:

- **Software do GitHub:** vincule a conta GitHub ao Zenodo, habilite o repositório
  e publique uma nova release estável. Confira depois se o Zenodo criou o registro.
- **Pacote de pesquisa:** prepare `openrepro deposit-bundle estudo.orepro --output deposito`
  e revise os metadados. Você pode usar a interface do Zenodo ou a integração por API.

Um DOI reservado num rascunho não é um registro publicado. Para citar uma versão
específica, use o DOI daquela versão; o DOI de conceito representa o conjunto de
versões. O registro antigo rc1 do projeto não identifica automaticamente a versão
1.0.0. Veja o [guia de Zenodo](zenodo.md). Não envie tokens por conversa ou Git.

## 5. Executar uma análise

A reprodução automática requer **Linux e Docker local**. Primeiro revise scripts,
imagem, entradas e tolerâncias; use `plan` para conferir a receita. Somente
`reproduce --allow-execution` autoriza a execução explícita. A execução não é
oferecida pelas ferramentas MCP. Para um roteiro completo, veja
[execução](execution.md) e o [exemplo Iris](../examples/iris/README.md).

## Onde encontrar ajuda

- [Tutorial completo sem Docker](quickstart.md).
- [Comandos](cli-reference.md) e [todas as opções](cli-options.md).
- [Cópias de segurança e restauração](operations.md).
- [Solução de problemas](troubleshooting.md), [API Python](python-api.md) e [MCP](mcp-integration.md).
- [Índice de toda a documentação](introduction.md).

Ao abrir uma issue, informe versão, sistema, comando e erro com informações
sensíveis removidas. Não anexe credenciais nem dados privados de participantes.
