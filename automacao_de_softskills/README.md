# automacao_de_softskills

Baixa as notas de soft skills do bootcamp no Moodle, cruza com a lista de aprovados e envia a planilha consolidada para o Google Drive.

## Pipeline

```
Etapa 1 — Download das atividades do bootcamp (com cache)
    ↓
Etapa 2 — Consolida softskills_resultado.csv
    ↓
Etapa 3 — Download dos aprovados por trilha (com cache)
    ↓
Etapa 4 — Gera aprovados_bootcamp_fap2026.csv → envia ao Google Drive
```

> Se os dados já foram baixados anteriormente, as etapas 1 e 3 são puladas automaticamente.
> O cache é baseado na presença de arquivos nas pastas `bootcamps/` e `aprovados/` — delete essas pastas para forçar um novo download.

## Como rodar

```bash
python3 -m automacao_de_softskills
```

Ou pelo menu interativo:

```bash
python3 menu.py
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
| `moodle.url` | URL base do Moodle |
| `moodle.bootcampCatId` | ID da categoria das turmas do bootcamp |
| `moodle.aprovadosCatId` | ID da categoria dos cursos de aprovados por trilha |
| `drive.folderId` | ID da pasta no Google Drive onde a planilha será enviada |
| `drive.credentialsPath` | Caminho do `credentials.json` (relativo à raiz do projeto) |
| `outputDir` | Pasta local para salvar os dados do bootcamp (padrão: `bootcamps`) |
| `aprovadosDir` | Pasta local para salvar os dados dos aprovados (padrão: `aprovados`) |

### 3. credentials.json

Credenciais de conta de serviço do Google. Coloque o arquivo na raiz do projeto e compartilhe a pasta do Drive com o e-mail da conta de serviço.

> A pasta de destino pode ser um Shared Drive (Drive compartilhado do Google Workspace) — o módulo suporta isso via `supportsAllDrives`.

## Atividades avaliadas

| Soft Skill | Arquivo CSV |
|---|---|
| Gestão de Tempo | `gestao_de_tempo.csv` |
| Inteligência Emocional | `inteligencia_emocional.csv` |
| Trabalho em Equipe | `trabalho_em_equipe.csv` |
| Resolução de Problemas | `resolucao_de_problemas.csv` |
| Comunicação | `comunicacao.csv` |
| Liderança Pessoal | `lideranca_pessoal.csv` |
| Atividade Avaliativa | `atividade_avaliativa.csv` |

## Estrutura de saída

```
automacao_de_softskills/
├── bootcamps/
│   ├── turma_01/
│   │   ├── gestao_de_tempo.csv
│   │   └── ...
│   └── softskills_resultado.csv
├── aprovados/
│   └── *.csv
└── aprovados_bootcamp_fap2026.csv   ← enviado ao Google Drive (nome fixo, específico do ciclo FAP 2026)
```

## Planilha no Google Drive

A aba **Dados** é criada (ou atualizada) automaticamente. Outras abas existentes na planilha não são tocadas — você pode criar abas adicionais para gráficos sem risco de perda.

Colunas geradas:

| Coluna | Tipo |
|---|---|
| Nome Completo | Texto |
| E-mail | Texto |
| Trilha | Texto |
| Turma Trilha | Número (0.00) |
| Nota {Soft Skill} | Número (0.00) |
| Nota Geral Soft Skills | Número (0.00) |

## Dependências

| Pacote | Uso |
|---|---|
| `requests` + `beautifulsoup4` | Download de dados do Moodle via HTTP (sem navegador) |
| `pandas` | Consolidação e cruzamento dos CSVs |
| `gspread` | Escrita na planilha do Google Sheets |
| `google-api-python-client` | Busca e criação de arquivos no Google Drive |
| `google-auth` | Autenticação com conta de serviço |
| `python-dotenv` | Leitura do `.env` |
