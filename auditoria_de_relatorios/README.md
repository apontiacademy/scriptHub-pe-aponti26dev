# auditoria_de_relatorios

Motor de análise de conformidade: compara a lista de alunos com os relatórios entregues e identifica quem enviou ou não.

Pode ser usado de forma independente via CLI ou como biblioteca interna pelo módulo `automacao_de_relatorios`.

## Como rodar

### Modo interativo

```bash
python3 -m auditoria_de_relatorios
```

O script vai pedir a pasta com os relatórios, a planilha de alunos, o modo de análise e o caminho de saída.

### Modo CLI

```bash
python3 -m auditoria_de_relatorios \
  -d dados/relatorios/ \
  -p dados/residentes.csv \
  -m feitos \
  -o dados/resultado_analise.csv
```

| Argumento | Descrição |
|---|---|
| `-d` / `--pasta-origem` | Pasta com os CSVs de relatórios baixados do Moodle |
| `-p` / `--planilha` | CSV com a lista de alunos |
| `-m` / `--modo` | `feitos` (quem enviou) ou `nao_feitos` (quem não enviou) |
| `-o` / `--output` | Caminho de saída do CSV de resultado |

## Formatos de entrada

### Lista de alunos (`-p`)

Suporta dois formatos:

**Formato A** — coluna `residente`:
```
residente
João Silva
Maria Souza
```

**Formato B** — colunas `Nome` + `Sobrenome` com campo `Grupos`:
```
Nome,Sobrenome,Grupos
João,Silva,PE | Empresa X
```

### Relatórios (`-d`)

CSVs exportados do Moodle com a coluna `Nome completo`.

## Saída

CSV com as colunas: `nome_completo`, `estado`, `empresa`, `relatorios_feitos` / `relatorios_ausentes`, `total`.

Exibe também uma tabela formatada no terminal com resumo estatístico.

## Dependências

| Pacote | Uso |
|---|---|
| `pandas` | Leitura, cruzamento e exportação dos dados |
