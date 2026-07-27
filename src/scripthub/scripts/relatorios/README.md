# relatorios

Domínio de automação de relatórios do Moodle, com três scripts internos: `auditar` (pipeline completo de auditoria), `compilar` (geração de PDFs individuais por aluno) e `extrair` (só a extração de relatórios, isolada).

## `auditar`

Baixa as respostas dos alunos, analisa quem enviou ou não, sincroniza com o Google Sheets e gera um backup local.

### Pipeline

```
Passo 1 — extrair:  Extração de relatórios (Moodle/Playwright)
    ↓
Passo 2 — analisar: Análise pente-fino (middleware)
    ↓
Passo 3 — integrar: Sincronização com Google Sheets
    ↓
Passo 4 — salvar:   Backup local em .xlsx
```

### Execução parcial

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
uv run scripthub relatorios auditar -p s               # só faz backup
```

O passo `extrair` também existe como script próprio de nível superior — ver
seção [`extrair`](#extrair) abaixo — por ser o mais comumente rodado isolado:

```bash
uv run scripthub relatorios extrair   # mesmo resultado de `auditar --passo extrair`
uv run scripthub relatorios e         # idem, forma curta
```

### Como rodar

```bash
uv run scripthub relatorios auditar
```

### Estrutura de saída

```
relatorios/auditar/
└── dados/
    ├── relatorios/          # CSVs baixados do Moodle
    ├── residentes.csv       # Lista de alunos
    └── resultado_analise.csv

<caminhoBackupLocal>/
└── [BACKUP AAAA-MM-DD HH-MM] <nome da aba>.xlsx
```

## `extrair`

Baixa todos os relatórios do Moodle listados em `moodle.urlsRelatorios` — sem análise pente-fino, sem sincronizar com o Google Sheets e sem backup (isso é feito por `auditar`). Implementação própria, independente de `auditar`, embora hoje produza o mesmo resultado que o passo `extrair` de lá.

### Como rodar

```bash
uv run scripthub relatorios extrair
```

### Estrutura de saída

```
relatorios/extrair/
└── dados/
    └── relatorios/          # CSVs baixados do Moodle
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

Compartilhada entre `auditar`, `compilar` e `extrair` — `.env` e `settings.json` vivem na raiz de `relatorios/`, não em cada subpasta.

> Alternativa a editar `.env`/`settings.json` manualmente: `uv run scripthub config relatorios` configura essas opções interativamente. Use `--script auditar`, `--script compilar` ou `--script extrair` para priorizar os campos daquele script na tela de edição.

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

| Chave | Usado por | Descrição |
|---|---|---|
| `moodle.urlLogin` | ambos | URL de login do Moodle |
| `moodle.urlsRelatorios` | `auditar`, `extrair` | Lista de URLs dos formulários de relatório |
| `moodle.exportarAnaliseRelatorio` | `auditar` | `true` para exportar análise em CSV |
| `moodle.caminhoExportacaoAnalise` | `auditar` | Caminho de saída da análise (obrigatório quando `exportarAnaliseRelatorio=true`) |
| `moodle.csvResidentes` | `auditar` | Caminho do CSV de residentes usado na análise |
| `moodle.meses` | `compilar` | Dicionário `{ "Nome do Mês": ["URL semana 1", "URL semana 2", ...] }` |
| `gsheets.idPlanilha` | `auditar` | ID da planilha do Google Sheets |
| `gsheets.nomeAba` | `auditar` | Nome da aba a ser atualizada |
| `gsheets.caminhoBackupLocal` | `auditar` | Pasta onde o backup `.xlsx` será salvo |
| `gsheets.caminhoJsonCredenciais` | `auditar` | Caminho absoluto para o `credentials.json` da conta de serviço Google |
| `pdf.caminhoSaida` | `compilar` | Pasta onde os PDFs serão salvos |

Um script individual roda mesmo que campos usados só pelo outro estejam vazios — `auditar` não precisa de `pdf.caminhoSaida`, `compilar` não precisa de `gsheets.*`.

### 3. credentials.json

Necessário para integração com Google Sheets e backup no Drive (usado só por `auditar`). O caminho é definido pela chave `gsheets.caminhoJsonCredenciais` em `settings.json` (ou via `scripthub config relatorios --script auditar`) e deve ser um **caminho absoluto** — caminhos relativos são rejeitados.

> A planilha deve ser compartilhada com o e-mail da conta de serviço.

## Dependências

| Pacote | Uso |
|---|---|
| `requests` + `beautifulsoup4` | Login e download dos relatórios via HTTP (sem navegador) |
| `pentefinocli-pe-aponti26dev` (pacote privado) | Análise pente-fino de quem enviou ou não os relatórios (`auditar`) |
| `gspread` + `pandas` | Escrita no Google Sheets (`auditar`) |
| `google-api-python-client` | Export e backup via Google Drive API (`auditar`) |
| `google-auth` | Autenticação com conta de serviço (`auditar`) |
| `fpdf2` | Geração dos PDFs (`compilar`) |
| `questionary` | Confirmação interativa para rebaixar relatórios já existentes (`compilar`) |
| `python-dotenv` | Leitura do `.env` |
