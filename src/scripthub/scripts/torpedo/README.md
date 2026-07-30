# torpedo

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

O arquivo de conteúdo e a imagem (opcional) são lidos do `settings.toml` (`moodle.caminhoPostFile` e `moodle.caminhoImagem`), não de argumentos de linha de comando.

## Configuração

> `uv run scripthub config torpedo` configura essas opções interativamente (usuário do Moodle e demais parâmetros em `settings.toml`; a senha do Moodle é pedida e salva no keyring do sistema operacional — nunca fica em texto plano). O `settings.toml` vive no diretório de config do profile ativo para o domínio `torpedo` (`uv run scripthub set-profile`/`--profile` para trocar de profile).

### settings.toml

| Chave | Descrição |
|---|---|
| `moodle.usuario` | Login de acesso ao Moodle |
| `moodle.urlLogin` | URL de login do Moodle |
| `moodle.urlsForuns` | Lista de URLs dos fóruns onde o tópico será postado |
| `moodle.headless` | `true` para rodar o navegador sem interface gráfica |
| `moodle.postDelay` | Intervalo em segundos entre postagens |
| `moodle.caminhoPostFile` | Caminho do arquivo Markdown com o conteúdo — deve ser um **caminho absoluto**; caminhos relativos são rejeitados |
| `moodle.caminhoImagem` | Caminho da imagem (opcional, omita a chave para ignorar) — deve ser um **caminho absoluto**; caminhos relativos são rejeitados |

A senha do Moodle (`moodle.senha`) não fica em `settings.toml` — é armazenada no keyring do sistema operacional.

### Arquivo de conteúdo (post.md)

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
| `keyring` | Senha do Moodle no keyring do sistema operacional |
