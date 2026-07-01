# torpedo_de_forum

Posta tópicos em fóruns do Moodle a partir de um arquivo Markdown. Suporta múltiplos fóruns e upload de imagem opcional.

## Como rodar

> Na primeira vez, instale o navegador do Playwright:
>
> ```bash
> playwright install chromium
> ```

```bash
uv run scripthub torpedo
```

O arquivo de conteúdo e a imagem (opcional) são lidos do `settings.json` (`moodle.caminhoPostFile` e `moodle.caminhoImagem`), não de argumentos de linha de comando.

## Configuração

> Alternativa a editar `.env`/`settings.json` manualmente: `uv run scripthub config -s torpedo_de_forum` configura essas mesmas opções interativamente.

### 1. Variáveis de ambiente

```bash
cp .env.example .env
```

```env
MOODLE_USUARIO=seu_usuario@aponti.org.br
MOODLE_SENHA=sua_senha
```

### 2. settings.json

```bash
cp settings.example.json settings.json
```

| Chave | Descrição |
|---|---|
| `moodle.urlLogin` | URL de login do Moodle |
| `moodle.urlsForuns` | Lista de URLs dos fóruns onde o tópico será postado |
| `moodle.headless` | `true` para rodar o navegador sem interface gráfica |
| `moodle.postDelay` | Intervalo em segundos entre postagens |
| `moodle.caminhoPostFile` | Caminho do arquivo Markdown com o conteúdo |
| `moodle.caminhoImagem` | Caminho da imagem (opcional, `null` para ignorar) |

### 3. Arquivo de conteúdo (post.md)

A primeira linha com `#` vira o título do tópico. O restante vira o corpo em HTML:

```markdown
# Título do tópico

Texto do post com **negrito**, *itálico* e [links](https://exemplo.com).

- Item 1
- Item 2
```

## Dependências

| Pacote | Uso |
|---|---|
| `requests` + `beautifulsoup4` | Login via HTTP, cujo cookie de sessão é injetado no navegador |
| `playwright` | Automação do navegador (preenchimento de formulário, upload) |
| `python-dotenv` | Leitura do `.env` |
