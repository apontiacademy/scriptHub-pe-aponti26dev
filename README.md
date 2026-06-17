# ScriptHub — Aponti PE

Hub de automações para operações do bootcamp Aponti PE. Cada módulo resolve um problema específico do dia a dia com o Moodle e o Google Workspace.

## Módulos

- [automacao_de_relatorios](./automacao_de_relatorios/README.md) — Pipeline completo: download → análise → Google Sheets → backup.
- [automacao_de_forum](./automacao_de_forum/README.md) — Posta tópicos em fóruns do Moodle a partir de arquivos Markdown.
- [automacao_de_frequencias](./automacao_de_frequencias/README.md) — Extrai dados de frequência do Moodle e exporta para `.xlsx`.
- [automacao_de_softskills](./automacao_de_softskills/README.md) — Baixa notas de soft skills do bootcamp e envia para o Google Drive.
- [auditoria_de_relatorios](./auditoria_de_relatorios/README.md) — Pente fino de conformidade: identifica quem enviou ou não os relatórios.

## Como usar

```bash
pip3 install -r requirements.txt
python3 menu.py
```

## Colaboradores

- **Leandro Carvalho** — [LinkedIn](https://www.linkedin.com/in/leandro-c-s/)
- **Caio Tenório** — [LinkedIn](https://www.linkedin.com/in/caiomatenorio/)
- **Ruan Rickelme Ramos** — [LinkedIn](https://www.linkedin.com/in/ruanrickelmeramos/?locale=pt)
