# automacao_de_frequencias

Extrai dados de frequência do Moodle e exporta um arquivo `.xlsx` por turma.

## Como rodar

```bash
python3 -m automacao_de_frequencias
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
| `moodle.urlLogin` | URL de login do Moodle |
| `moodle.urlsFrequencias` | Dicionário `{ "Nome da Turma": "URL do módulo de presença" }` |
| `moodle.caminhoExportacao` | Pasta onde os `.xlsx` serão salvos |

Exemplo de `urlsFrequencias`:

```json
{
  "Turma 01": "https://moodle.aponti.org.br/mod/attendance/view.php?id=1234",
  "Turma 02": "https://moodle.aponti.org.br/mod/attendance/view.php?id=5678"
}
```

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
| `playwright` | Automação do navegador para login e download das frequências |
| `python-dotenv` | Leitura do `.env` |
