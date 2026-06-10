# Pente Fino Relatórios - Aponti PE

> Ferramenta de auditoria e análise de relatórios semanais de residentes e alunos da Aponti Academy.

## 📋 Visão Geral

Este projeto automatiza a auditoria de relatórios semanais respondidos por residentes e alunos, permitindo identificar rapidamente quem completou ou não as tarefas solicitadas. Inclui pipelines de extração de dados do Moodle, análise de preenchimento e geração de relatórios consolidados.

### Funcionalidades Principais

- ✅ **Extração automática** de dados do Moodle via Playwright
- ✅ **Análise de conformidade** com cruzamento de dados
- ✅ **Relatórios visuais** de tarefas feitas vs. não feitas
- ✅ **Exportação em CSV** com encoding UTF-8 BOM (compatível com Excel)
- ✅ **Suporte a múltiplas regiões/empresas** (Pernambuco, São Paulo, etc.)

---

## 👥 Autores

- **Leandro Carvalho** — [LinkedIn](https://www.linkedin.com/in/leandro-c-s/)
- **Caio Tenório** — [LinkedIn](https://www.linkedin.com/in/caiomatenorio/)

---

## 🔧 Requisitos e Instalação

### Pré-requisitos

- **Python 3.10+**
- **pip** (gerenciador de pacotes Python)

### Instalação

1. Clone o repositório:

```bash
git clone https://github.com/apontiacademy/penteFinoRelatorios-pe-aponti26dev.git
cd penteFinoRelatorios-pe-aponti26dev
```

2. Crie um ambiente virtual:

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# ou
.venv\Scripts\activate  # Windows
```

3. Instale as dependências:

```bash
pip install -r requirements.txt
```

4. Configure as variáveis de ambiente:

```bash
cp .env.example .env
# Edite .env com suas credenciais do Moodle
```

---

## 📁 Estrutura do Projeto

```
penteFinoRelatorios-pe-aponti26dev/
├── analise/
│   ├── pente_fino.py              # Análise de conformidade de relatórios
│   └── analise_negatividade.py    # Análise de sentimentos/negatividade
├── automacao/
│   ├── escopo1.py                 # Extração de dados do Moodle
│   ├── escopo2.py                 # Processamento e consolidação
│   └── executar.py                # Orquestrador do pipeline
├── dados/
│   ├── residentes.csv             # Planilha master de alunos
│   ├── relatorios/                # Relatórios brutos extraídos
│   └── resultado.csv              # Saída da análise
├── .env.example                   # Template de variáveis de ambiente
├── LICENSE                        # Licença MIT
└── README.md                      # Este arquivo
```

---

## 🚀 Como Usar

### Escopo 1: Extração de Dados (Moodle → CSV)

Automatiza o login no Moodle e download dos relatórios via **Playwright**:

```bash
python -m automacao.escopo1
```

> **Alternativa (direto):** `python automacao/escopo1.py`

**Configuração em `.env`:**

```env
MOODLE_USERNAME=seu_usuario
MOODLE_PASSWORD=sua_senha
MOODLE_LOGIN_URL=https://moodle.suainstituicao.edu/login/index.php
MOODLE_REPORT_URLS=url1,url2,url3
MOODLE_DOWNLOAD_DIR=./dados/relatorios
MOODLE_HEADLESS=true  # true = oculto, false = visível (útil para debug)
```

**Tecnologia:** Usa [Playwright](https://playwright.dev/) para automação cross-browser robusta

---

### Escopo 2: Análise de Conformidade (Pente Fino)

Cruza dados de alunos com relatórios respondidos.

#### Modo Interativo

Sem argumentos, o script pergunta interativamente:

```bash
python -m analise.pente_fino
```

O script fará 4 perguntas:

1. **Pasta de input** — Onde estão os CSVs de relatórios (Enter = pasta atual)
2. **Planilha principal** — Qual CSV contém dados dos alunos (ex: `residentes.csv`)
3. **Modo de visualização** — `1` = Não feitos | `2` = Feitos
4. **Caminho de saída** — Onde salvar resultado (Enter = `./resultado.csv`)

#### Modo CLI (Linha de Comando)

Passe argumentos para evitar perguntas:

```bash
python -m analise.pente_fino \
  --pasta-origem ./dados/relatorios \
  --planilha ./dados/residentes.csv \
  --modo nao_feitos \
  --output ./resultados/auditoria.csv
```

> **Alternativa (direto):** `python analise/pente_fino.py [argumentos]`

**Argumentos:**

- `--pasta-origem` / `-d` → Pasta com relatórios CSV
- `--planilha` / `-p` → Arquivo da planilha geral de alunos
- `--modo` / `-m` → `feitos` ou `nao_feitos`
- `--output` / `-o` → Arquivo de saída (padrão: `./resultado.csv`)

#### Exemplos Práticos

```bash
# Modo interativo completo
python -m analise.pente_fino

# Com pasta pré-definida (ainda faz perguntas)
python -m analise.pente_fino --pasta-origem ./dados/relatorios

# Modo totalmente automático
python -m analise.pente_fino \
  -d ./dados/relatorios \
  -p ./dados/residentes.csv \
  -m nao_feitos \
  -o ./resultado_final.csv

# Planilha em caminho absoluto (ignora pasta de input)
python -m analise.pente_fino \
  -p /home/user/documentos/alunos.csv \
  -m feitos \
  -o ./resultado.csv
```

---

### Escopo 3: Pipeline Automatizado

Execute todo o fluxo (extração + análise):

```bash
python -m automacao
```

> **Alternativa (direto):** `python automacao/executar.py`

Lê configurações de `.env` e executa na sequência correta.

---

## 📊 Formato de Dados Esperado

### Planilha Master (Alunos)

Arquivo com informações dos residentes. **Colunas obrigatórias:**

| Nome   | Sobrenome       | Endereço de e-mail | Grupos                                     |
| ------ | --------------- | ------------------ | ------------------------------------------ |
| ADRIEL | FULANO DA SILVA | fulano@email.com   | Pernambuco: Aponti PE - 00.501.070/0001-23 |
| MARIA  | SILVA           | maria@email.com    | São Paulo: Aponti SP - 00.501.070/0001-24  |

**Campo `Grupos`:** Deve seguir o formato `Estado: Empresa - CNPJ`  
(Estado e empresa são parseados automaticamente)

### Relatórios Individuais

CSVs exportados do Moodle ou preenchidos manualmente. **Coluna obrigatória:**

- `Nome completo` — Nome de quem respondeu (será comparado com a planilha master)

Outras colunas (data, grupo, email, etc.) são opcionais.

| Nome completo          | Grupos                | Endereço de e-mail | Data       | Respostas |
| ---------------------- | --------------------- | ------------------ | ---------- | --------- |
| ADRIEL FULANO DA SILVA | Pernambuco: Aponti PE | fulano@email.com   | 2026-06-10 | ...       |
| MARIA SILVA            | São Paulo: Aponti SP  | maria@email.com    | 2026-06-10 | ...       |

---

## 📈 Resultados da Análise

### Modo 1: Não Feitos

Mostra alunos que **faltam completar** relatórios.

**Saída no terminal:**

```
Relatórios processados: relatorio_semana_01, relatorio_semana_02

Nome Completo              Estado       Empresa      Relatórios Ausentes    Total
--------------------------- ------------ ------------ ---------------------- -----
ADRIEL FULANO DA SILVA      Pernambuco   Aponti PE    relatorio_semana_02    1
MARIA FULANA                São Paulo    Aponti SP    relatorio_semana_01    1

Total: 2 aluno(s) | 2 aluno(s) com pelo menos 1 ausência.
Resultado salvo em: resultado_auditoria.csv
```

**Arquivo `resultado_auditoria.csv`:**

| nome_completo          | estado     | empresa   | relatorios_ausentes | total_ausencias |
| ---------------------- | ---------- | --------- | ------------------- | --------------- |
| ADRIEL FULANO DA SILVA | Pernambuco | Aponti PE | relatorio_semana_02 | 1               |
| MARIA FULANA           | São Paulo  | Aponti SP | relatorio_semana_01 | 1               |

### Modo 2: Feitos

Mostra **todos** os alunos e quais relatórios completaram.

**Saída no terminal:**

```
Relatórios processados: relatorio_semana_01, relatorio_semana_02

Nome Completo              Estado       Empresa      Relatórios Feitos                           Total
--------------------------- ------------ ------------ ------------------------------------------- -----
ADRIEL FULANO DA SILVA      Pernambuco   Aponti PE    relatorio_semana_01                        1
MARIA FULANA                São Paulo    Aponti SP    relatorio_semana_01, relatorio_semana_02   2
JOÃO SILVA                  Pernambuco   Aponti PE    (nenhum)                                   0

Total: 3 aluno(s) | 2 aluno(s) com pelo menos 1 relatório feito.
Resultado salvo em: resultado_relatorios_feitos.csv
```

**Arquivo `resultado_relatorios_feitos.csv`:**

| nome_completo          | estado     | empresa   | relatorios_feitos                        | total_feitos |
| ---------------------- | ---------- | --------- | ---------------------------------------- | ------------ |
| ADRIEL FULANO DA SILVA | Pernambuco | Aponti PE | relatorio_semana_01                      | 1            |
| MARIA FULANA           | São Paulo  | Aponti SP | relatorio_semana_01, relatorio_semana_02 | 2            |
| JOÃO SILVA             | Pernambuco | Aponti PE |                                          | 0            |

---

## 💾 Saída de Dados

Os CSVs gerados usam **encoding UTF-8 com BOM** para abrir corretamente no Excel:

- **`resultado_auditoria.csv`** — Gerado no modo "Não feitos"
- **`resultado_relatorios_feitos.csv`** — Gerado no modo "Feitos"

---

## ⚙️ Detalhes Técnicos

### Tratamento de Dados

- **Nomes:** Comparação case-insensitive, ignora espaços extras
  - ✅ "ADRIEL FULANO DA SILVA" = "adriel fulano da silva"
  - ✅ Reduz falsos negativos por variações de digitação

- **Relatórios:** Arquivo sem coluna `Nome completo` gera aviso e é pulado
- **Alunos:** Presentes em **todos** os relatórios não aparecem no resultado (modo "Não feitos")

### Variáveis de Ambiente

Consulte `.env.example` para documentação completa das variáveis:

- `ENVIRONMENT` → `development` | `production`
- `LOG_LEVEL` → `DEBUG` | `INFO` | `WARNING` | `ERROR`
- `MOODLE_*` → Configurações de extração
- `MOODLE_ANALYSIS_*` → Configurações de análise

---

## 📝 Licença

MIT License © 2026 Aponti Academy

Veja arquivo [LICENSE](./LICENSE) para detalhes.

---

## 🤝 Contribuindo

Encontrou um bug ou tem sugestões? Abra uma issue ou entre em contato com os autores.

---

## 📚 Próximas Fases

- **Escopo 3:** Dashboard web com resultados em tempo real
- **Escopo 4:** Integração com sistema de notificações
- Análise de tendências por período
- Exportação em múltiplos formatos (Excel, PDF, JSON)
