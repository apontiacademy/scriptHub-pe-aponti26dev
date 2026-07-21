# automacao_de_relatorios

Pipeline completo de automação de relatórios do Moodle: baixa as respostas dos alunos, analisa quem enviou ou não, sincroniza com o Google Sheets e gera um backup local.

## Pipeline

```
Passo 1 — extrair:  Extração de relatórios (Moodle/Playwright)
    ↓
Passo 2 — analisar: Análise pente-fino (middleware)
    ↓
Passo 3 — integrar: Sincronização com Google Sheets
    ↓
Passo 4 — salvar:   Backup local em .xlsx
```

## Execução parcial

Use `--passo` (ou `-p`) para executar apenas um passo do pipeline:

| Slug | Alias | Descrição |
|---|---|---|
| `extrair` | `e` | Baixa os relatórios do Moodle via Playwright |
| `analisar` | `a` | Analisa quem enviou ou não (middleware) |
| `integrar` | `i` | Envia os dados ao Google Sheets |
| `salvar` | `s` | Gera backup local em `.xlsx` |

```bash
uv run scripthub relatorios auditar --passo extrair   # só baixa relatórios
uv run scripthub relatorios auditar -p e              # idem, forma curta
uv run scripthub relatorios auditar --passo analisar  # só analisa
uv run scripthub relatorios auditar -p s              # só faz backup
```

## Como rodar

> Na primeira vez, instale o navegador do Playwright:
>
> ```bash
> playwright install chromium
> ```

```bash
uv run scripthub relatorios auditar
```

## Configuração

### 1. Variáveis de ambiente

Copie o arquivo de exemplo e preencha com suas credenciais do Moodle:

```bash
cp .env.example .env
```

```env
MOODLE_USUARIO=seu_usuario@aponti.org.br
MOODLE_SENHA=sua_senha
```

### 2. settings.json

Copie e preencha:

```bash
cp settings.example.json settings.json
```

| Chave | Descrição |
|---|---|
| `moodle.urlLogin` | URL de login do Moodle |
| `moodle.urlsRelatorios` | Lista de URLs dos formulários de relatório |
| `moodle.headless` | `true` para rodar o navegador sem interface gráfica (use `false` para debug) |
| `moodle.exportarAnaliseRelatorio` | `true` para exportar análise em CSV |
| `moodle.caminhoExportacaoAnalise` | Caminho de saída da análise |
| `gsheets.idPlanilha` | ID da planilha do Google Sheets |
| `gsheets.nomeAba` | Nome da aba a ser atualizada |
| `gsheets.caminhoBackupLocal` | Pasta onde o backup `.xlsx` será salvo |

### 3. credentials.json

Necessário para integração com Google Sheets e backup no Drive. Coloque o arquivo de credenciais da conta de serviço na raiz do projeto.

> A planilha deve ser compartilhada com o e-mail da conta de serviço.

## Estrutura de saída

```
automacao_de_relatorios/
└── dados/
    ├── relatorios/          # CSVs baixados do Moodle
    ├── residentes.csv       # Lista de alunos
    └── resultado_analise.csv
```

## Dependências

| Pacote | Uso |
|---|---|
| `playwright` | Automação do navegador para login e download |
| `beautifulsoup4` | Parsing de HTML |
| `gspread` | Escrita no Google Sheets |
| `google-api-python-client` | Export e backup via Google Drive API |
| `google-auth` | Autenticação com conta de serviço |
| `python-dotenv` | Leitura do `.env` |
