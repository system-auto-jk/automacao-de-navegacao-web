# System Auto JK - Web-IA

Aplicacao desktop em Python para automacao de navegacao web, extracao de conteudo e comandos assistidos por IA. O sistema combina uma interface grafica em CustomTkinter, controle de navegador com Selenium/ChromeDriver e integracao com Google Gemini para resumo e interpretacao de conteudos de paginas.

## Recursos principais

- Navegacao automatizada com comandos em linguagem natural.
- Abertura de URLs, voltar, avancar, recarregar, nova aba e fechamento de aba.
- Clique e preenchimento de campos por XPath, CSS, id, name, classe, type, placeholder, aria-label ou texto visivel.
- Extracao de noticias, links, imagens e contagem de tabelas da pagina atual.
- Resumo de paginas usando Gemini.
- Memoria local de noticias, favoritos, historico e macros.
- Exportacao de noticias em `json`, `csv`, `txt`, `xlsx` e `html`.
- Captura de tela e salvamento do HTML da pagina.
- Gravacao e execucao de macros de comandos.
- Interface desktop com painel lateral, barra de comandos e area de log.

## Tecnologias

- Python
- CustomTkinter
- Selenium
- webdriver-manager
- Google Generative AI SDK
- lxml
- pandas

## Requisitos

- Python 3.10 ou superior
- Google Chrome instalado
- Chave de API do Google Gemini

## Instalacao

Clone o projeto e instale as dependencias:

```bash
pip install -r requirements.txt
```

Ou, no Windows, execute:

```bat
iniciar.bat
```

O arquivo `iniciar.bat` atualiza o `pip`, instala as dependencias e inicia a aplicacao.

## Configuracao da API

Crie um arquivo `config.json` na raiz do projeto com a sua chave do Gemini:

```json
{
  "GEMINI_API_KEY": "SUA_CHAVE_AQUI"
}
```

Importante: nao publique sua chave real no GitHub. Antes de subir o projeto, remova a chave do arquivo ou adicione `config.json` ao `.gitignore`.

## Como executar

Pelo terminal:

```bash
python main_ui.py
```

No Windows, tambem e possivel executar:

```bat
iniciar.bat
```

Ao iniciar, a aplicacao abre uma janela desktop. O Chrome sera iniciado automaticamente quando voce abrir o primeiro site.

## Exemplos de comandos

Navegacao:

```text
abrir https://www.exemplo.com
recarregar
voltar
avancar
nova aba
fechar aba
```

Interacao com elementos:

```text
clicar no xpath //button[@type="submit"]
clicar "Entrar"
digite "meu texto" no id campo_busca
digite "senha123" no type password
enter
fechar popup
```

Extracao e arquivos:

```text
pegue as noticias
extrair links
extrair imagens
extrair tabelas
salvar html
screenshot
```

Memoria e exportacao:

```text
listar noticias
exportar json
exportar csv
exportar xlsx favoritos
exportar html "filtro"
```

IA:

```text
resuma a pagina atual
explique esta pagina
traduza o conteudo da pagina
```

Macros:

```text
criar macro "login"
parar macro
rodar macro "login"
listar macros
```

## Atalhos de teclado

- `Ctrl + E`: extrair noticias
- `Ctrl + L`: limpar log
- `Ctrl + P`: tirar screenshot
- `Ctrl + S`: exportar noticias em JSON
- `Ctrl + Left`: voltar
- `Ctrl + Right`: avancar
- `Ctrl + R`: recarregar

## Estrutura do projeto

```text
.
|-- main_ui.py           # Interface grafica e controlador principal
|-- ia_core.py           # Integracao Gemini e interpretador de comandos
|-- navegador.py         # Inicializacao do Selenium/ChromeDriver
|-- memory_manager.py    # Memoria local, favoritos, macros e exportacoes
|-- requirements.txt     # Dependencias Python
|-- iniciar.bat          # Script de instalacao/execucao no Windows
|-- config.json          # Configuracao local da API Gemini
|-- session_data.json    # Dados locais da sessao
`-- exports/             # Arquivos gerados: screenshots, HTML e exportacoes
```

## Arquivos gerados

Durante o uso, o sistema cria e atualiza arquivos locais:

- `session_data.json`: historico, noticias, favoritos e macros.
- `exports/`: screenshots, paginas HTML salvas e exportacoes.
- `__pycache__/`: cache gerado pelo Python.

Esses arquivos normalmente nao devem ser versionados.

## Sugestao de `.gitignore`

Antes de publicar no GitHub, considere criar um `.gitignore` com:

```gitignore
__pycache__/
*.pyc
exports/
session_data.json
config.json
.env
```

## Observacoes de seguranca

- Nao publique chaves de API.
- Se uma chave ja foi exposta em algum commit ou arquivo compartilhado, revogue a chave antiga e gere uma nova no provedor.
- O Selenium controla um navegador real; revise macros antes de executa-las em sites com dados sensiveis.
- Alguns sites podem bloquear automacoes ou exigir autenticacao manual.

## Licenca

Defina a licenca antes de publicar o projeto. Para projetos abertos, uma opcao comum e a MIT License.
