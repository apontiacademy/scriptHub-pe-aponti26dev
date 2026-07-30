# relatorios

Domínio de automação de relatórios do Moodle, com dois scripts internos: `extrair` (baixa os relatórios brutos) e `compilar` (geração de PDFs individuais por aluno).

## `extrair`

Baixa todos os relatórios do Moodle listados em `moodle.urlsRelatorios`.

### Como rodar

```bash
uv run scripthub relatorios extrair
uv run scripthub relatorios e         # idem, forma curta
```

### Estrutura de saída

```
<caminhoDownloadRelatorio>/
└── relatorio1.csv, relatorio2.csv, ...   # CSVs baixados do Moodle
```

## `compilar`

Baixa os relatórios mensais de residência do Moodle e compila um PDF individual por aluno, agrupando as respostas semana a semana.

### Pipeline

```
Etapa 1 — Download dos relatórios por mês (Moodle, via HTTP)
    ↓
Etapa 2 — Compilação de um PDF por aluno
```

> Se os CSVs já foram baixados anteriormente (pasta `dados/relatorios/`), a etapa 1 pergunta antes de baixar novamente.

### Como rodar

```bash
uv run scripthub relatorios compilar
```

### Estrutura de saída

```
relatorios/compilar/
└── dados/
    └── relatorios/
        ├── abril_2026_1.csv
        ├── abril_2026_2.csv
        └── ...

<caminhoSaida>/
└── <Estado>/
    └── <Empresa>/
        └── <Nome do Aluno>.pdf
```

## Configuração

Compartilhada entre `compilar` e `extrair` — o `settings.toml` vive no diretório de config do profile ativo para o domínio `relatorios` (`uv run scripthub set-profile`/`--profile` para trocar de profile), não em cada subpasta.

> `uv run scripthub config relatorios` configura essas opções interativamente (usuário do Moodle e demais parâmetros em `settings.toml`; a senha do Moodle é pedida e salva no keyring do sistema operacional — nunca fica em texto plano). Use `--script compilar` ou `--script extrair` para priorizar os campos daquele script na tela de edição.

### settings.toml

| Chave | Usado por | Descrição |
|---|---|---|
| `moodle.usuario` | `compilar`, `extrair` | Login de acesso ao Moodle |
| `moodle.urlLogin` | `compilar`, `extrair` | URL de login do Moodle |
| `moodle.urlsRelatorios` | `extrair` | Lista de URLs dos formulários de relatório |
| `moodle.caminhoDownloadRelatorio` | `extrair` | Diretório onde os CSVs baixados do Moodle serão salvos — caminho absoluto (relativos são rejeitados) |
| `moodle.meses` | `compilar` | Tabela `{ "Nome do Mês" = ["URL semana 1", "URL semana 2", ...] }` |
| `pdf.caminhoSaida` | `compilar` | Pasta onde os PDFs serão salvos — caminho absoluto (relativos são rejeitados) |

A senha do Moodle (`moodle.senha`) não fica em `settings.toml` — é armazenada no keyring do sistema operacional.

Um script individual roda mesmo que campos usados só pelo outro estejam vazios — `compilar` não precisa de `moodle.urlsRelatorios`/`caminhoDownloadRelatorio`, `extrair` não precisa de `moodle.meses`/`pdf.caminhoSaida`.

## Dependências

| Pacote | Uso |
|---|---|
| `requests` + `beautifulsoup4` | Login e download dos relatórios via HTTP (sem navegador) |
| `fpdf2` | Geração dos PDFs (`compilar`) |
| `questionary` | Confirmação interativa para rebaixar relatórios já existentes (`compilar`) |
| `keyring` | Senha do Moodle no keyring do sistema operacional |
