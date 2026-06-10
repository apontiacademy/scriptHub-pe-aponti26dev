# Auditoria de Relatórios — Residentes Aponti

## Autores

- Leandro Carvalho [Linkedin](https://www.linkedin.com/in/leandro-c-s/)
- Caio Tenório [Linkedin](https://www.linkedin.com/in/caiomatenorio/)

Script para auditar quais residentes/alunos responderam (ou não) seus relatórios semanais.

## Requisitos

- Python 3.10+
- pandas

```bash
pip install pandas
```

## Como usar

1. Coloque todos os arquivos `.csv` na mesma pasta:
   - A **planilha geral** de alunos
   - As **planilhas de relatório** (uma por relatório)

2. Execute o script apontando a pasta de origem ou navegue interativamente até ela:

```bash
python pente_fino.py --pasta-origem ./relatorios
```

Ou, se preferir, rode apenas `python pente_fino.py` e informe a pasta quando o script perguntar.

3. O script lista os CSVs encontrados nessa pasta e pergunta qual é a planilha geral:

```
Arquivos CSV encontrados:
  [1] alunos.csv
  [2] relatorio_semana_01.csv
  [3] relatorio_semana_02.csv

Digite o número da planilha GERAL de alunos: 1
```

4. O script pergunta qual modo de visualização você deseja:

```
Escolha o modo de visualização:
  [1] Não feitos (mostra quem não fez relatórios)
  [2] Feitos (mostra quem fez relatórios)

Digite o número do modo: 
```

5. O resultado é exibido no terminal e salvo em arquivo CSV (nome varia conforme o modo).

### Argumentos de CLI

- `--pasta-origem` ou `-d`: define a pasta onde estão os CSVs.
- `--planilha` ou `-p`: define o arquivo da planilha geral dentro da pasta de origem.
- `--modo` ou `-m`: escolhe entre `feitos` e `nao_feitos`.
- `--output` ou `-o`: define o caminho do CSV de saída.

## Formato esperado das planilhas

### Planilha geral de alunos

| Nome   | Sobrenome       | Endereço de e-mail | Grupos                                     |
| ------ | --------------- | ------------------ | ------------------------------------------ |
| ADRIEL | FULANO DA SILVA | fulano@email.com   | Pernambuco: Aponti PE - 00.501.070/0001-23 |

O campo **Grupos** deve seguir o formato `Estado: Empresa - CNPJ`. Estado e empresa são extraídos automaticamente.

### Planilhas de relatório

Devem conter uma coluna chamada **`Nome completo`** com o nome de quem respondeu.

| Nome completo          | Grupos | Endereço de e-mail | Data | ... |
| ---------------------- | ------ | ------------------ | ---- | --- |
| ADRIEL FULANO DA SILVA | ...    | ...                | ...  | ... |

## Resultado

### Modo 1: Não feitos

Mostra alunos que **não responderam** relatórios.

#### Terminal

```
Relatórios processados: relatorio_semana_01, relatorio_semana_02

Nome Completo              Estado       Empresa      Relatórios Ausentes    Total
-------------------------- ------------ ------------ ---------------------- -----
ADRIEL FULANO DA SILVA     Pernambuco   Aponti PE    relatorio_semana_02    1
MARIA FULANA               São Paulo    Aponti SP    relatorio_semana_01    1

Total: 2 aluno(s) | 2 aluno(s) com pelo menos 1 ausência.
Resultado salvo em: resultado_auditoria.csv
```

#### Arquivo `resultado_auditoria.csv`

| nome_completo | estado | empresa | relatorios_ausentes | total_ausencias |
|---|---|---|---|---|
| ADRIEL FULANO DA SILVA | Pernambuco | Aponti PE | relatorio_semana_02 | 1 |
| MARIA FULANA | São Paulo | Aponti SP | relatorio_semana_01 | 1 |

### Modo 2: Feitos

Mostra alunos que **responderam** relatórios. Exibe todos os alunos, indicando quais relatórios cada um completou.

#### Terminal

```
Relatórios processados: relatorio_semana_01, relatorio_semana_02

Nome Completo              Estado       Empresa      Relatórios Feitos                           Total
-------------------------- ------------ ------------ ------------------------------------------- -----
ADRIEL FULANO DA SILVA     Pernambuco   Aponti PE    relatorio_semana_01                        1
MARIA FULANA               São Paulo    Aponti SP    relatorio_semana_01, relatorio_semana_02   2
JOÃO SILVA                 Pernambuco   Aponti PE    Nenhum                                      0

Total: 3 aluno(s) | 2 aluno(s) com pelo menos 1 relatório feito.
Resultado salvo em: resultado_relatorios_feitos.csv
```

#### Arquivo `resultado_relatorios_feitos.csv`

| nome_completo | estado | empresa | relatorios_feitos | total_feitos |
|---|---|---|---|---|
| ADRIEL FULANO DA SILVA | Pernambuco | Aponti PE | relatorio_semana_01 | 1 |
| MARIA FULANA | São Paulo | Aponti SP | relatorio_semana_01, relatorio_semana_02 | 2 |
| JOÃO SILVA | Pernambuco | Aponti PE | | 0 |

## Arquivos de saída

Os CSVs são salvos com encoding `UTF-8 BOM` para abrir corretamente no Excel:
- **`resultado_auditoria.csv`**: gerado no modo "Não feitos"
- **`resultado_relatorios_feitos.csv`**: gerado no modo "Feitos"

## Observações

- A comparação de nomes é **case-insensitive** e ignora espaços extras — variações de digitação não geram falsos negativos.
- Se um relatório não tiver a coluna `Nome completo`, um aviso é exibido e o arquivo é pulado.
- Alunos presentes em todos os relatórios não aparecem no resultado.
