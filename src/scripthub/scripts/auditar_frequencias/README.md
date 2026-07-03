# auditar_frequencias

Extrai dados de frequência do Moodle e exporta um arquivo `.xlsx` por turma.

Pipeline:

```
Passo 1 — exportar: Exportação de frequências (Moodle)
    ↓
Passo 2 — integrar: Integração (Google Sheets)
```

## Execução parcial

Use `--passo` (ou `-p`) para executar apenas um passo do pipeline:

| Slug | Alias | Descrição |
|---|---|---|
| `exportar` | `e` | Baixa as frequências do Moodle e exporta `.xlsx` |
| `integrar` | `i` | Envia os dados ao Google Sheets |

```bash
uv run scripthub frequencias --passo exportar   # só baixa do Moodle
uv run scripthub frequencias -p e               # idem, forma curta
uv run scripthub frequencias --passo integrar   # só integra com Sheets
```

## Como rodar

```bash
uv run scripthub frequencias
```

## Configuração

> Alternativa a editar `.env`/`settings.json` manualmente: `uv run scripthub config -s auditar_frequencias` configura essas mesmas opções interativamente.

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
| `moodle.urlsFrequencias` | Dicionário `{ "Nome da Turma": "URL do módulo de presença" }` |
| `moodle.caminhoExportacao` | Pasta onde os `.xlsx` serão salvos |
| `gsheets.idPlanilha` | ID da planilha do Google Sheets |

Exemplo de `urlsFrequencias`:

```json
{
  "Turma 01": "https://moodle.aponti.org.br/mod/attendance/view.php?id=1234",
  "Turma 02": "https://moodle.aponti.org.br/mod/attendance/view.php?id=5678"
}
```

### 3. credentials.json

Necessário para a integração com Google Sheets. O caminho é fixo em `src/scripthub/scripts/auditar_frequencias/credentials.json` (dentro da pasta deste módulo) — hoje não é configurável via `settings.json` nem `scripthub config`.

> A planilha deve ser compartilhada com o e-mail da conta de serviço.

## Estrutura de saída

```
caminho_exportacao/
├── Turma 01.xlsx
├── Turma 02.xlsx
└── ...
```

## Dependências

| Pacote | Uso |
|---|---|
| `requests` + `beautifulsoup4` | Login e download das frequências via HTTP (sem navegador) |
| `gspread` + `pandas` | Leitura dos `.xlsx` e escrita no Google Sheets |
| `python-dotenv` | Leitura do `.env` |
