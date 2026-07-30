# Códigos de saída

Todo comando do scriptHub termina com um código de saída que indica a causa
raiz da falha (ou `0` em caso de sucesso). Automações que chamam `scripthub`
podem decidir o que fazer a partir desse código, sem precisar parsear a
mensagem de log.

| Código | Categoria | Quando ocorre | Mecanismo |
| --- | --- | --- | --- |
| 0 | Sucesso | Pipeline (ou comando informativo, ex.: `--version`) terminou sem erros | — |
| 1 | Erro genérico / inesperado | Qualquer exceção não classificada nas categorias abaixo — normalmente indica um bug. Rode com `--debug` para ver o traceback completo no terminal | fallback `except Exception` do handler global |
| 2 | Configuração inválida ou ausente | `settings.toml`, senha do Moodle no keyring, credenciais do Google, ou um arquivo/diretório local que um passo anterior do pipeline deveria ter gerado | `scripthub.services.erros.ErroConfiguracao` |
| 3 | Uso inválido da CLI | `--passo` desconhecido, flags conflitantes (`--opcoes` + `--limpar`), `modo` inválido em `relatorios`, script desconhecido em `config` | `scripthub.services.erros.ErroUsoCLI` |
| 4 | Falha parcial | Parte de um lote de itens falhou (N de M PDFs, fóruns, arquivos), mas o restante foi processado | `scripthub.services.erros.FalhaParcial` |
| 5 | Falha de integração externa | Moodle ou Google Sheets/Drive retornaram algo inesperado (HTML mudou, planilha/aba não encontrada, API falhou) | `scripthub.services.erros.ErroIntegracao` |

**Nota sobre o código 2 do Click/Typer**: por convenção, a biblioteca Click
(usada pelo Typer) sai com código `2` quando falha em fazer o parsing de uma
opção (tipo inválido, `Choice` fora da lista, etc.), antes mesmo do código do
scriptHub rodar. Esse esquema reserva `2` para "configuração inválida" — uma
categoria diferente. Hoje nenhuma opção do CLI usa um tipo que aciona esse
caminho automático do Click (todas são `str`/`bool` simples), então a
colisão não ocorre na prática — mas vale ter em mente ao adicionar uma opção
com tipo restrito (`int`, `Enum`, `Choice`) no futuro. Esse erro é renderizado
inteiramente pelo próprio Click/Typer (patchado em `_i18n.py` para incluir o
código de saída na mensagem) e não passa pelo handler global do scriptHub.

## Handler global de erros

`cli.py` tem um único ponto de tratamento de erros,
`_executar_com_tratamento_global`, que envolve a execução do app inteiro
(chamado a partir de `run()`, o entry point do pacote). Todo o resto do
código — comandos, `executar_script`, `_carregar_config`, validações de uso
da CLI — **apenas levanta a exceção correta**; nunca chama `log.erro`
diretamente para finalizar o processo, nunca decide o código de saída, nunca
chama `typer.Exit`/`sys.exit`. O handler:

1. Captura qualquer `ErroScriptHub` (e subclasses), loga
   `"{mensagem}. Código de saída: {código}"` como um único painel e finaliza
   com `SystemExit(exc.codigo_saida)`.
2. Se a exceção tiver uma `dica` (ver abaixo), loga essa dica logo em seguida
   como uma sugestão de próximo passo.
3. Captura qualquer outra exceção (bug/erro inesperado), loga
   `"Erro inesperado: {mensagem}. Código de saída: 1"` e finaliza com
   `SystemExit(1)`. Se a flag `--debug` estiver ativa, também imprime o
   traceback completo (via `log.traceback()`) — **só** nesse caso; erros
   classificados (2, 3, 4, 5) nunca mostram traceback, mesmo com `--debug`.

Isso facilita adicionar um novo tipo de erro no futuro: basta uma nova
subclasse de `ErroScriptHub` com seu `codigo_saida`, sem tocar em nenhum
ponto de tratamento espalhado pelo código.

### Atributo `dica`

`ErroScriptHub.__init__` aceita um `dica: str | None` opcional — uma linha de
sugestão de próximo passo (ex.: `"Execute: scripthub config -s x"`), exibida
pelo handler global logo após o painel de erro. `_carregar_config` usa isso
para toda `ErroConfiguracao`/`KeyError` levantada ao carregar a config de um
script, preenchendo a `dica` com o comando de configuração correto — sem
sobrescrever uma `dica` que a exceção já tenha recebido na origem.

## Como uma função de biblioteca escolhe o código

Pergunta prática: qual é a causa raiz mais próxima de algo que o usuário
consiga corrigir?

- Falta algo no `settings.toml`/keyring/credenciais, ou um arquivo/diretório
  que um passo anterior do pipeline deveria ter gerado → `ErroConfiguracao` (2)
- Uso inválido da própria CLI (opção/passo/flag/argumento inválidos,
  validados antes do script rodar) → `ErroUsoCLI` (3)
- Parte de um lote falhou, mas não é um erro fatal do processo inteiro →
  `FalhaParcial` (4)
- Um sistema externo (Moodle ou Google) devolveu algo inesperado
  (página sem o elemento esperado, planilha/aba não encontrada, API falhou) →
  `ErroIntegracao` (5)
- Nenhuma das anteriores, ou a causa é ambígua/inesperada (provável bug) →
  deixe propagar como exceção genérica do Python (`RuntimeError`, etc.) →
  vira código 1

Todas as classes vivem em `src/scripthub/services/erros.py` e herdam de
`ErroScriptHub` (código 1, não deve ser levantada diretamente — é só a base
que carrega o atributo `codigo_saida` e o `dica` opcional).

## Referência: classificação de cada `raise` nos pacotes de script

Tabela de auditoria de quando o esquema foi introduzido — útil como exemplo
ao classificar um novo `raise`.

### `ErroConfiguracao` (2)

- `settings.toml` ausente/incompleto ou senha do Moodle ausente no keyring: `config.py` de todos os 5 pacotes
- Precondição de um passo anterior não satisfeita: `frequencias/auditar/integracao_google_sheets.py` (diretório de exportação, XLSX ausentes), `frequencias/compilar/gerar_atas.py` (nenhum XLSX de frequência encontrado), `relatorios/compilar/compilar_pdfs.py` (nenhum dado de aluno nos CSVs)
- Credenciais/IDs do Google ausentes: `frequencias/auditar/integracao_google_sheets.py`
- Arquivo/URL de entrada do próprio script ausente: `frequencias/auditar/extrair_frequencias.py`, `frequencias/compilar/extrair_frequencias.py` (URLs de frequência), `relatorios/extrair/download_de_relatorios.py` (URLs de relatório), `relatorios/compilar/download_de_relatorios.py` (meses), `torpedo/main.py` (post `.md`, URLs de fórum, título do `.md`, imagem de override)
- Falha de autenticação no Moodle (usuário/senha errados): `services/moodle/sessao.py` (`MoodleSessao.login`, usado por todos os scripts que baixam do Moodle via HTTP)
- Campo de caminho de arquivo/diretório externo não é um caminho absoluto: `gsheets.caminhoJsonCredenciais` (`frequencias/auditar/config.py`), `atas.caminhoSaida`/`caminhoLogo`/`caminhoAssinatura` (`frequencias/compilar/config.py`), `moodle.caminhoExportacao` (`frequencias/extrair/config.py`), `moodle.caminhoDownloadRelatorio` (`relatorios/extrair/config.py`), `pdf.caminhoSaida` (`relatorios/compilar/config.py`), `drive.credentialsPath` (`softskills/config.py`), `moodle.caminhoPostFile`/`caminhoImagem` (`torpedo/config.py`)

### `FalhaParcial` (4)

- `frequencias/auditar/integracao_google_sheets.py` (N arquivos XLSX falharam)
- `frequencias/compilar/gerar_atas.py` (N atas falharam)
- `relatorios/compilar/compilar_pdfs.py` (N PDFs falharam)
- `torpedo/main.py` (N fóruns falharam ao publicar)

### `ErroIntegracao` (5)

- Estrutura de página do Moodle inesperada: `services/moodle/attendance.py` (`extrair_frequencia`, formulário de exportação não encontrado, resposta que não é um XLSX válido — usado por `frequencias/auditar` e `frequencias/compilar`)
- Sessão do Moodle caiu no meio da execução (já autenticada, sem ser problema de credencial): `services/moodle/sessao.py` (`MoodleSessao.get`/`baixar`, sessão expirada)
- Planilha do Google Sheets não encontrada pelo ID configurado: `services/google/sheets.py` (`GoogleSheetsClient.planilha`)
- Relatório do Moodle baixado via HTTP não é um CSV válido, ou nenhum link/formulário de download foi encontrado na página: `services/moodle/download.py` (`baixar_relatorio`, usado por `relatorios/extrair` e `relatorios/compilar`)
- Elemento esperado da página do fórum não encontrado (botão de novo tópico, editor de conteúdo, botão de submissão): `torpedo/main.py`
