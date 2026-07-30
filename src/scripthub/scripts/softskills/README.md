# softskills

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
uv run scripthub softskills
```

Ou pelo menu interativo (depreciado — prefira o comando acima):

```bash
uv run scripthub menu
```

## Configuração

> `uv run scripthub config softskills` configura essas opções interativamente (usuário do Moodle e demais parâmetros em `settings.toml`; a senha do Moodle é pedida e salva no keyring do sistema operacional — nunca fica em texto plano). O `settings.toml` vive no diretório de config do profile ativo para o domínio `softskills` (`uv run scripthub set-profile`/`--profile` para trocar de profile).

### settings.toml

| Chave | Descrição |
|---|---|
| `moodle.usuario` | Login de acesso ao Moodle |
| `moodle.url` | URL base do Moodle |
| `moodle.bootcampCatId` | ID da categoria das turmas do bootcamp |
| `moodle.aprovadosCatId` | ID da categoria dos cursos de aprovados por trilha |
| `drive.folderId` | ID da pasta no Google Drive onde a planilha será enviada |
| `drive.credentialsPath` | Caminho do `credentials.json` — deve ser um **caminho absoluto**; caminhos relativos são rejeitados |
| `outputDir` | Pasta para salvar os dados do bootcamp, relativa ao diretório de dados do domínio (padrão: `bootcamps`) |
| `aprovadosDir` | Pasta para salvar os dados dos aprovados, relativa ao diretório de dados do domínio (padrão: `aprovados`) |

A senha do Moodle (`moodle.senha`) não fica em `settings.toml` — é armazenada no keyring do sistema operacional.

### credentials.json

Credenciais de conta de serviço do Google. O caminho é definido por `drive.credentialsPath` em `settings.toml` (ou via `scripthub config -s softskills`) e deve ser um **caminho absoluto** — caminhos relativos são rejeitados. Compartilhe a pasta do Drive com o e-mail da conta de serviço.

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
| Atividade Avaliativa | `atividade_avaliativa_softskills.csv` |

## Estrutura de saída

```
softskills/
├── bootcamps/
│   ├── turma_01/
│   │   ├── gestao_de_tempo.csv
│   │   ├── atividade_avaliativa_softskills.csv
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
| `keyring` | Senha do Moodle no keyring do sistema operacional |
