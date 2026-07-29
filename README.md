# ScriptHub — Aponti PE

Hub de automações para operações do bootcamp Aponti PE. Cada módulo resolve um problema específico do dia a dia com o Moodle e o Google Workspace.

## Instalação

Requer Python 3.12+ e [uv](https://docs.astral.sh/uv/). O projeto depende de um pacote privado da organização resolvido via `[tool.uv.sources]`, por isso `pip` não é suportado diretamente.

```bash
git clone git@github.com:apontiacademy/scriptHub-pe-aponti26dev.git
cd scriptHub-pe-aponti26dev
uv sync

# Configure as opções de cada script (veja a seção Configuração abaixo)
uv run scripthub config

# Para ver todos os comandos disponíveis:
uv run scripthub --help
```

Após o `uv sync`, também é possível ativar o ambiente virtual e invocar os comandos sem o prefixo `uv run`:

```bash
source .venv/bin/activate   # Linux/Mac
.venv\Scripts\activate      # Windows
scripthub config
```

## Uso

```bash
# Invocar um script diretamente
uv run scripthub frequencias auditar
uv run scripthub frequencias compilar
uv run scripthub relatorios compilar
uv run scripthub softskills
uv run scripthub torpedo
```

Para ver a ajuda e os aliases disponíveis:

```bash
uv run scripthub --help      # ou: scripthub -h
uv run scripthub --aliases   # ou: scripthub -a
uv run scripthub --version   # ou: scripthub -V
```

## Comandos

| Comando | Alias | Descrição |
|---|---|---|
| `scripthub frequencias auditar [-p slug]` | `f auditar` | Pipeline completo: extração de frequências do Moodle → integração ao Google Sheets |
| `scripthub frequencias compilar [-p slug]` | `f compilar` | Pipeline completo: extração de frequências do Moodle → geração de atas em PDF |
| `scripthub frequencias extrair` | `f extrair` | Executa somente a extração de frequências do Moodle (atalho) |
| `scripthub relatorios extrair` | `r extrair` | Executa somente a extração de relatórios do Moodle |
| `scripthub relatorios compilar` | `r compilar` | Compila relatórios em PDF |
| `scripthub softskills` | `s` | Baixa notas de soft skills do Moodle e envia ao Google Drive |
| `scripthub torpedo` | `t` | Posta tópicos em fóruns do Moodle a partir de arquivos Markdown |
| `scripthub config` | `c` | Configura interativamente as opções de um script |

A opção `--passo <slug>` (ou `-p`) executa apenas um passo do pipeline. Disponível nos comandos `frequencias auditar` e `frequencias compilar`. Os passos mais usados isoladamente (extração) também têm um subcomando próprio (`extrair`), que não exige saber o slug:

| Comando | Passos disponíveis |
|---|---|
| `scripthub frequencias auditar` | `extrair` (`e`), `integrar` (`i`) |
| `scripthub frequencias compilar` | `extrair` (`e`), `gerar` (`g`) |

```bash
scripthub frequencias auditar --passo extrair      # só baixa do Moodle
scripthub frequencias auditar -p e                 # idem, forma curta
scripthub frequencias compilar --passo gerar       # só gera os PDFs
scripthub frequencias extrair                      # atalho direto pro passo de extração
scripthub relatorios extrair                       # atalho direto pro passo de extração
```

## Configuração

Cada script tem suas próprias opções configuráveis (URLs do Moodle, credenciais, IDs de planilhas, etc.). Use o comando `config` para inspecionar e editar essas opções interativamente:

```bash
# Selecionar script interativamente e editar opções
uv run scripthub config

# Ir direto para as opções de um script específico
uv run scripthub config frequencias

# Apenas visualizar o estado atual das opções (sem editar)
uv run scripthub config --opcoes
uv run scripthub config torpedo --opcoes
```

O comando exibe cada opção com um ícone de status:

- ✅ Preenchida e válida — valor atual é exibido em resumo
- ❌ Ausente ou inválida — motivo do erro é exibido
- ⚪ Opcional e não preenchida

No modo de edição, selecione quais opções modificar (estilo `gh` CLI) e preencha os valores. Inputs são adaptados ao tipo do campo: texto, senha (oculta), URL, caminho, booleano, inteiro, listas de URLs e dicionários (com sub-menus de adicionar/editar/remover).

As configurações são persistidas nos diretórios padrão do sistema operacional (via `platformdirs`), divididas por **profile** — permitindo múltiplos contextos isolados na mesma máquina (ex.: duas pessoas usando a mesma instalação, ou alternar entre configs de dev/produção):

- `settings.toml` — todos os parâmetros de cada domínio, exceto a senha do Moodle
- Senha do Moodle — armazenada no keyring do sistema operacional (Keychain no macOS, Credential Locker no Windows, Secret Service/KWallet no Linux), com uma entrada própria por domínio

Por padrão, tudo roda sob o profile `default`. Para trocar de profile:

```bash
uv run scripthub set-profile equipe-noturna     # define o profile ativo (persiste)
uv run scripthub frequencias auditar            # usa o profile equipe-noturna
uv run scripthub --profile equipe-diurna frequencias auditar   # override pontual, não persiste
uv run scripthub unset-profile                  # volta para default (no-op se já for default)
```

Quem já usava uma versão anterior do scriptHub (`.env`/`settings.json` dentro do próprio pacote instalado) roda uma vez o comando de migração depreciado, que move essa configuração para o novo layout sem apagar os arquivos originais:

```bash
uv run scripthub migrate-legacy-config
```

Se um script for executado sem as opções obrigatórias preenchidas, a CLI indica o comando exato para corrigi-las.

## Changelog

Histórico de versões em [CHANGELOG.md](CHANGELOG.md). Fluxo de contribuição e versionamento (branches, commits, PRs) documentado em [CONTRIBUTING.md](CONTRIBUTING.md).

## Colaboradores

- **Leandro Carvalho** — [LinkedIn](https://www.linkedin.com/in/leandro-c-s/)
- **Caio Tenório** — [LinkedIn](https://www.linkedin.com/in/caiomatenorio/)
- **Ruan Rickelme Ramos** — [LinkedIn](https://www.linkedin.com/in/ruanrickelmeramos/?locale=pt)
