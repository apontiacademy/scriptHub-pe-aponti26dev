# frequencias

Domínio de automação de frequências do Moodle, com dois scripts internos: `auditar` (pipeline completo de auditoria) e `compilar` (geração de atas de frequência em PDF, por turma).

## `auditar`

Extrai as frequências de todas as turmas do Moodle e sincroniza com o Google Sheets.

### Pipeline

```
Passo 1 — extrair:  Extração de frequências (Moodle)
    ↓
Passo 2 — integrar: Integração (Google Sheets)
```

O passo `extrair` também tem um subcomando de nível superior próprio, por
ser o mais comumente rodado isolado (mesmo padrão de `relatorios extrair`):

```bash
uv run scripthub frequencias extrair   # equivalente a `auditar --passo extrair`
uv run scripthub frequencias e         # idem, forma curta
```

### Execução parcial

Use `--passo` (ou `-p`) para executar apenas um passo do pipeline:

| Slug | Alias | Descrição |
|---|---|---|
| `extrair` | `e` | Baixa as frequências do Moodle e exporta `.xlsx` |
| `integrar` | `i` | Envia os dados ao Google Sheets |

```bash
uv run scripthub frequencias auditar --passo extrair    # só baixa do Moodle
uv run scripthub frequencias auditar -p e                # idem, forma curta
uv run scripthub frequencias auditar --passo integrar    # só integra com Sheets
```

### Como rodar

```bash
uv run scripthub frequencias auditar
```

### Estrutura de saída

```
<caminhoExportacao>/
├── Turma 01.xlsx
├── Turma 02.xlsx
└── ...
```

## `compilar`

Extrai as frequências de todas as turmas do Moodle (independente de `auditar` já ter rodado) e compila uma ata de frequência em PDF por turma: uma capa, um resumo geral da turma por mês, uma página por mês (com a presença de cada aluno marcada por uma bolinha colorida), um resumo geral por aluno do período inteiro e, por fim, a lista de justificativas agrupada por data.

### Pipeline

```
Passo 1 — extrair: Extração de frequências (Moodle)
    ↓
Passo 2 — gerar:   Geração de atas em PDF
```

### Execução parcial

| Slug | Alias | Descrição |
|---|---|---|
| `extrair` | `e` | Baixa as frequências do Moodle (cópia própria, independente de `auditar`) |
| `gerar` | `g` | Gera as atas em PDF a partir dos XLSX já extraídos |

```bash
uv run scripthub frequencias compilar --passo extrair   # só baixa do Moodle
uv run scripthub frequencias compilar -p g               # só gera os PDFs
```

### Como rodar

```bash
uv run scripthub frequencias compilar
```

### Regras da ata

- Status do Moodle → cor da bolinha: `PR` presente (verde), `AU` falta (vermelho), `AT` atraso (amarelo), `JU` justificada (ciano).
- Só `AU` conta como falta para o cálculo de % de faltas.
- Aluno com `"Inscrições suspensas"` em qualquer sessão é excluído inteiramente da ata.
- Aluno com matrícula tardia (`"Inscrição de usuários inicia..."`) tem as sessões anteriores à matrícula justificadas automaticamente (`"Não matriculado no momento."`), mas continua na ata.
- Sessão sem chamada feita (`"?"`) conta como falta.
- Aluno com mais de 3 faltas no mês tem a linha inteira destacada em vermelho naquela página mensal — limite fixo no código, não configurável.
- A capa mostra o logo do programa (opcional) fixo no topo, o título "Registro de Frequências" e o nome da turma centralizados logo abaixo; a assinatura de logos da Aponti (opcional) fica fixa na parte de baixo. Ambas as imagens são configuráveis (`atas.caminhoLogo`/`atas.caminhoAssinatura`) — se ausentes ou apontando para um arquivo inexistente, simplesmente não são exibidas.
- Logo após a capa, o "Resumo geral da turma" agrega, por mês, o percentual de `PR`/`AT`/`JU`/`AU` de todos os alunos (sem detalhar por aluno) — distinto do "Resumo geral por aluno", que vem depois das páginas mensais com os totais do período inteiro por aluno.
- Todas as justificativas do período ficam concentradas numa única página ao final do documento, agrupadas por data — cada página mensal com justificativas só exibe a nota "* Justificativas ao final do documento.".

### Estrutura de saída

```
frequencias/compilar/
└── dados/
    └── frequencias/
        ├── Turma 01.xlsx
        └── ...

<atas.caminhoSaida>/
├── Turma 01.pdf
├── Turma 02.pdf
└── ...
```

## Configuração

Compartilhada entre `auditar` e `compilar` — `.env` e `settings.json` vivem na raiz de `frequencias/`, não em cada subpasta.

> Alternativa a editar `.env`/`settings.json` manualmente: `uv run scripthub config frequencias` configura essas opções interativamente. Use `--script auditar` ou `--script compilar` para priorizar os campos daquele script na tela de edição.

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
| `moodle.urlsFrequencias` | ambos | Dicionário `{ "Nome da Turma": "URL do módulo de presença" }` |
| `moodle.caminhoExportacao` | `auditar` | Pasta onde os `.xlsx` de `auditar` serão salvos |
| `gsheets.idPlanilha` | `auditar` | ID da planilha do Google Sheets |
| `gsheets.caminhoJsonCredenciais` | `auditar` | Caminho absoluto para o `credentials.json` da conta de serviço Google |
| `atas.caminhoSaida` | `compilar` | Pasta onde as atas em PDF serão salvas |
| `atas.caminhoLogo` | `compilar` | Imagem do logo do programa exibida na capa (opcional) |
| `atas.caminhoAssinatura` | `compilar` | Imagem da assinatura de logos da Aponti exibida no rodapé da capa (opcional) |

Exemplo de `urlsFrequencias`:

```json
{
  "Turma 01": "https://moodle.aponti.org.br/mod/attendance/view.php?id=1234",
  "Turma 02": "https://moodle.aponti.org.br/mod/attendance/view.php?id=5678"
}
```

Um script individual roda mesmo que campos usados só pelo outro estejam vazios — `compilar` não precisa de `gsheets.*`/`moodle.caminhoExportacao`, `auditar` não precisa de `atas.caminhoSaida`.

### 3. credentials.json

Necessário só para `auditar` (integração com Google Sheets). O caminho é definido pela chave `gsheets.caminhoJsonCredenciais` em `settings.json` (ou via `scripthub config frequencias --script auditar`) e deve ser um **caminho absoluto** — caminhos relativos são rejeitados.

> A planilha deve ser compartilhada com o e-mail da conta de serviço.

## Dependências

| Pacote | Uso |
|---|---|
| `requests` + `beautifulsoup4` | Login e download das frequências via HTTP (sem navegador) |
| `gspread` + `pandas` | Leitura dos `.xlsx` e escrita no Google Sheets (`auditar`) |
| `pandas` + `openpyxl` | Leitura dos `.xlsx` de frequência (`compilar`) |
| `fpdf2` | Geração das atas em PDF (`compilar`) |
| `python-dotenv` | Leitura do `.env` |
