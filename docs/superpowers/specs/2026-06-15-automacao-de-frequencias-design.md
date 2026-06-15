# Design: automacao_de_frequencias

**Data:** 2026-06-15

## Objetivo

Módulo Python independente que faz login no Moodle e exporta relatórios de frequência em formato XLSX para cada turma configurada, salvando os arquivos em uma pasta local.

## Estrutura de arquivos

```
automacao_de_frequencias/
├── __init__.py
├── __main__.py
├── config.py
├── exportar_frequencias.py
├── executar.py
├── .env.example
└── settings.example.json
```

## Configuração

### `.env` (credenciais — não versionado)
```
MOODLE_USUARIO=seu_usuario_aqui
MOODLE_SENHA=sua_senha_aqui
```

### `settings.json` (configurações — não versionado)
```json
{
  "moodle": {
    "urlLogin": "https://moodle.yourinstitution.edu/login/index.php",
    "urlsFrequencias": {
      "Turma A": "https://moodle.yourinstitution.edu/mod/.../view.php?id=1111",
      "Turma B": "https://moodle.yourinstitution.edu/mod/.../view.php?id=2222"
    },
    "caminhoExportacao": "/home/you/Downloads/frequencias"
  }
}
```

`urlsFrequencias` é um objeto onde a chave é o nome da turma (usado como nome do arquivo XLSX) e o valor é a URL direta do formulário de exportação de frequências no Moodle.

## Componentes

### `config.py`

Define duas dataclasses e o método `Config.load()`:

```python
@dataclass
class MoodleConfig:
    usuario: str
    senha: str
    url_login: str
    urls_frequencias: dict[str, str]  # {nome_turma: url}
    caminho_exportacao: Path

@dataclass
class Config:
    moodle: MoodleConfig

    @staticmethod
    def load() -> "Config": ...
```

`load()` carrega credenciais do `.env` via `python-dotenv` e configurações do `settings.json`, com validação de campos obrigatórios. Mesmos padrões de `automacao_de_relatorios/config.py`.

### `exportar_frequencias.py`

Três funções:

**`realizar_login(page, url_login, usuario, senha)`**
- Mesma lógica de `automacao_de_relatorios/download_de_relatorios.py`
- Trata sessão fantasma ativa antes de preencher credenciais
- Fallback no seletor do botão de submit

**`exportar_frequencia(page, url, nome_turma, caminho_saida, url_login, usuario, senha)`**
- Navega para a URL do formulário de exportação
- Detecta redirecionamento para login e refaz autenticação se necessário
- Marca o checkbox de "incluir observações" (localizado pelo texto/label)
- Clica no botão "OK" que dispara o download XLSX
- Salva o arquivo como `{nome_turma}.xlsx` em `caminho_saida`
- Loga sucesso ou erro por turma

**`main(config: Config)`**
- Cria `caminho_exportacao` se não existir
- Abre único contexto Playwright com headless e user-agent do Chrome
- Faz login uma vez antes do loop
- Itera `urls_frequencias.items()` chamando `exportar_frequencia` para cada turma
- `time.sleep(1.5)` entre cada exportação
- Imprime banner de início e resultado final

### `executar.py`

Ponto de entrada do pipeline:

```python
def main():
    config = Config.load()
    # banner de abertura
    exportar_frequencias.main(config)
    # banner de encerramento
```

### `__main__.py`

```python
from .executar import main
if __name__ == "__main__":
    main()
```

Permite execução com `python -m automacao_de_frequencias`.

## Fluxo de execução

```
Config.load()
  └── .env → credenciais
  └── settings.json → urls_frequencias, caminho_exportacao, url_login

Playwright (único contexto, headless)
  └── realizar_login()
  └── para cada (nome_turma, url) em urls_frequencias:
        exportar_frequencia()
          └── goto(url)
          └── verificar sessão ativa
          └── marcar checkbox "incluir observações"
          └── clicar "OK" → download XLSX
          └── salvar como {nome_turma}.xlsx
        sleep(1.5s)
```

## Tratamento de erros

- Sessão expirada mid-loop: detectada por redirecionamento para URL de login → refaz login → renaviega para URL original
- Checkbox não encontrado: erro logado no stderr, turma pulada
- Download não iniciado: erro logado no stderr, turma pulada
- `settings.json` ausente ou campos obrigatórios faltando: exceção levantada em `Config.load()` com mensagem clara

## Execução

```bash
python -m automacao_de_frequencias
```

Requer `settings.json` e `.env` na pasta `automacao_de_frequencias/`.
