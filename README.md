# Auditoria de Relatórios — Residentes Aponti

Script para identificar quais residentes/alunos não responderam seus relatórios semanais.

## Requisitos

- Python 3.10+
- pandas

```bash
pip install pandas
```

## Como usar

1. Coloque todos os arquivos `.csv` no mesmo diretório:
   - A **planilha geral** de alunos
   - As **planilhas de relatório** (uma por relatório)

2. Execute o script na pasta onde estão os arquivos:

```bash
python pente_fino.py
```

3. O script lista os CSVs encontrados e pergunta qual é a planilha geral:

```
Arquivos CSV encontrados:
  [1] alunos.csv
  [2] relatorio_semana_01.csv
  [3] relatorio_semana_02.csv

Digite o número da planilha GERAL de alunos: 1
```

4. O resultado é exibido no terminal e salvo em `resultado_auditoria.csv`.

## Formato esperado das planilhas

### Planilha geral de alunos

| Nome | Sobrenome | Endereço de e-mail | Grupos |
|---|---|---|---|
| ADRIEL | FULANO SILVA | fulano@email.com | Pernambuco: Aponti PE - 00.501.070/0001-23 |

O campo **Grupos** deve seguir o formato `Estado: Empresa - CNPJ`. Estado e empresa são extraídos automaticamente.

### Planilhas de relatório

Devem conter uma coluna chamada **`Nome completo`** com o nome de quem respondeu.

| Nome completo | Grupos | Endereço de e-mail | Data | ... |
|---|---|---|---|---|
| ADRIEL GOMES SILVA | ... | ... | ... | ... |

## Resultado

### Terminal

```
Relatórios processados: relatorio_semana_01, relatorio_semana_02

Alunos com ausências:
Nome Completo          Estado      Empresa    Relatórios Ausentes
---------------------- ----------- ---------- -------------------
ADRIEL GOMES SILVA     Pernambuco  Aponti PE  relatorio_semana_02
MARIA SOUZA            São Paulo   Aponti SP  relatorio_semana_01

Total: 2 aluno(s) com pelo menos 1 ausência.
Resultado salvo em: resultado_auditoria.csv
```

### Arquivo `resultado_auditoria.csv`

| nome_completo | estado | empresa | relatorios_ausentes | total_ausencias |
|---|---|---|---|---|
| ADRIEL GOMES SILVA | Pernambuco | Aponti PE | relatorio_semana_02 | 1 |
| MARIA SOUZA | São Paulo | Aponti SP | relatorio_semana_01 | 1 |

O CSV é salvo com encoding `UTF-8 BOM` para abrir corretamente no Excel.

## Observações

- A comparação de nomes é **case-insensitive** e ignora espaços extras — variações de digitação não geram falsos negativos.
- Se um relatório não tiver a coluna `Nome completo`, um aviso é exibido e o arquivo é pulado.
- Alunos presentes em todos os relatórios não aparecem no resultado.
