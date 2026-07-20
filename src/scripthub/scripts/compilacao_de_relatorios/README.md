# compilacao_de_relatorios

Baixa os relatórios mensais de residência do Moodle e compila um PDF individual por aluno, agrupando as respostas semana a semana.

## Pipeline

```
Etapa 1 — Download dos relatórios por mês (Moodle, via HTTP)
    ↓
Etapa 2 — Compilação de um PDF por aluno
```

> Se os CSVs já foram baixados anteriormente (pasta `dados/relatorios/`), a etapa 1 pergunta antes de baixar novamente.

## Como rodar

```bash
uv run scripthub relatorios compilar
```

## Configuração

> Alternativa a editar `.env`/`settings.json` manualmente: `uv run scripthub config -s compilacao_de_relatorios` configura essas mesmas opções interativamente.

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
| `moodle.meses` | Dicionário `{ "Nome do Mês": ["URL do relatório semana 1", "URL semana 2", ...] }` |
| `pdf.caminhoSaida` | Pasta onde os PDFs serão salvos |
| `pdf.csvResidentes` | CSV com CPF dos residentes (colunas `residente`, `cpf_residente`), usado para preencher o PDF |

Exemplo de `meses`:

```json
{
  "Abril 2026": [
    "https://moodle.aponti.org.br/mod/feedback/show_entries.php?id=10000",
    "https://moodle.aponti.org.br/mod/feedback/show_entries.php?id=10001"
  ],
  "Maio 2026": [
    "https://moodle.aponti.org.br/mod/feedback/show_entries.php?id=10363"
  ]
}
```

## Estrutura de saída

```
compilacao_de_relatorios/
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

## Dependências

| Pacote | Uso |
|---|---|
| `requests` + `beautifulsoup4` | Login e download dos relatórios via HTTP (sem navegador) |
| `pandas` | Leitura dos CSVs semanais e do CSV de residentes |
| `fpdf2` | Geração dos PDFs |
| `questionary` | Confirmação interativa para rebaixar relatórios já existentes |
| `python-dotenv` | Leitura do `.env` |
