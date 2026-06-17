# automacao_de_forum

Posta tópicos em fóruns do Moodle a partir de um arquivo Markdown. Suporta múltiplos fóruns e upload de imagem opcional.

## Como rodar

```bash
python3 -m automacao_de_forum
```

Ou com argumentos:

```bash
python3 -m automacao_de_forum --content post.md --image imagem.png
```

## Configuração

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
| `playwright` | Automação do navegador (login, preenchimento de formulário, upload) |
| `beautifulsoup4` | Conversão de Markdown para HTML |
| `python-dotenv` | Leitura do `.env` |
