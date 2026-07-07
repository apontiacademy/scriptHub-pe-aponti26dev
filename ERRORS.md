# Códigos de saída

Todo comando do scriptHub termina com um código de saída que indica a causa
raiz da falha (ou `0` em caso de sucesso). Automações que chamam `scripthub`
podem decidir o que fazer a partir desse código, sem precisar parsear a
mensagem de log.

| Código | Categoria | Quando ocorre | Mecanismo |
|---|---|---|---|
| 0 | Sucesso | Pipeline (ou comando informativo, ex.: `--version`) terminou sem erros | — |
| 1 | Erro genérico / inesperado | Qualquer exceção não classificada nas categorias abaixo — normalmente indica um bug | fallback do `except Exception` em `cli.py` |
| 2 | Configuração inválida ou ausente | `.env`, `settings.json`, credenciais do Google, ou um arquivo/diretório local que um passo anterior do pipeline deveria ter gerado | `scripthub.services.erros.ErroConfiguracao` |
| 3 | Uso inválido da CLI | `--passo` desconhecido, flags conflitantes (`--opcoes` + `--limpar`), `modo` inválido em `relatorios`, script desconhecido em `config` | validação direta em `cli.py`/`services/config/main.py` — não passa pela hierarquia de exceções abaixo |
| 4 | Falha parcial | Parte de um lote de itens falhou (N de M PDFs, fóruns, arquivos), mas o restante foi processado | `scripthub.services.erros.FalhaParcial` |
| 5 | Falha de integração externa | Moodle, Google Sheets/Drive ou o `pentefino` retornaram algo inesperado (HTML mudou, planilha/aba não encontrada, API falhou) | `scripthub.services.erros.ErroIntegracao` |

**Nota sobre o código 2 do Click/Typer**: por convenção, a biblioteca Click
(usada pelo Typer) sai com código `2` quando falha em fazer o parsing de uma
opção (tipo inválido, `Choice` fora da lista, etc.), antes mesmo do código do
scriptHub rodar. Esse esquema reserva `2` para "configuração inválida" — uma
categoria diferente. Hoje nenhuma opção do CLI usa um tipo que aciona esse
caminho automático do Click (todas são `str`/`bool` simples), então a
colisão não ocorre na prática — mas vale ter em mente ao adicionar uma opção
com tipo restrito (`int`, `Enum`, `Choice`) no futuro.

## Como uma função de biblioteca escolhe o código

Pergunta prática: qual é a causa raiz mais próxima de algo que o usuário
consiga corrigir?

- Falta algo no `.env`/`settings.json`/credenciais, ou um arquivo/diretório
  que um passo anterior do pipeline deveria ter gerado → `ErroConfiguracao` (2)
- Parte de um lote falhou, mas não é um erro fatal do processo inteiro →
  `FalhaParcial` (4)
- Um sistema externo (Moodle, Google, `pentefino`) devolveu algo inesperado
  (página sem o elemento esperado, planilha/aba não encontrada, API falhou) →
  `ErroIntegracao` (5)
- Nenhuma das anteriores, ou a causa é ambígua/inesperada (provável bug) →
  deixe propagar como exceção genérica do Python (`RuntimeError`, etc.) →
  vira código 1

Erros de uso da CLI (3) não seguem esse mecanismo — são validados e
finalizados diretamente em `cli.py`/`services/config/main.py`, antes de
qualquer lógica de script rodar (o script nem chega a começar).

As três classes vivem em `src/scripthub/services/erros.py` e herdam de
`ErroScriptHub` (código 1, não deve ser levantada diretamente — é só a base
que carrega o atributo `codigo_saida`).

## Referência: classificação de cada `raise` nos pacotes de script

Tabela de auditoria de quando o esquema foi introduzido — útil como exemplo
ao classificar um novo `raise`.

**`ErroConfiguracao` (2)**
- `.env`/`settings.json` ausentes ou incompletos: `config.py` de todos os 5 pacotes
- Precondição de um passo anterior não satisfeita: `auditar_frequencias/integracao_google_sheets.py` (diretório de exportação, XLSX ausentes), `auditar_relatorios/integracao_google_sheets.py` (CSV de auditoria ausente), `compilacao_de_relatorios/compilar_pdfs.py` (nenhum dado de aluno nos CSVs)
- Credenciais/IDs do Google ausentes: `auditar_frequencias/integracao_google_sheets.py`, `auditar_relatorios/integracao_google_sheets.py`, `auditar_relatorios/backup.py`
- Arquivo/URL de entrada do próprio script ausente: `auditar_frequencias/exportar_frequencias.py` (URLs de frequência), `auditar_relatorios/download_de_relatorios.py` (URLs de relatório), `compilacao_de_relatorios/download_de_relatorios.py` (meses), `torpedo_de_forum/main.py` (post `.md`, URLs de fórum, título do `.md`)

**`FalhaParcial` (4)**
- `auditar_frequencias/integracao_google_sheets.py` (N arquivos XLSX falharam)
- `compilacao_de_relatorios/compilar_pdfs.py` (N PDFs falharam)
- `torpedo_de_forum/main.py` (N fóruns falharam ao publicar)

**`ErroIntegracao` (5)**
- Estrutura de página do Moodle inesperada: `auditar_frequencias/exportar_frequencias.py` (formulário não encontrado)
- Dados vindos de fora malformados: `auditar_relatorios/integracao_google_sheets.py` (CSV ilegível ou com menos de 4 colunas, aba não encontrada na planilha)
- `pentefino` (biblioteca externa) falhou: `auditar_relatorios/middleware_analise_de_relatorios.py`
- Google Drive falhou ao gerar o backup: `auditar_relatorios/backup.py`
