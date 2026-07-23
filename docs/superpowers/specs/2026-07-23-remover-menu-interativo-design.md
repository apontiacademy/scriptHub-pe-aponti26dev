# Remoção do menu interativo depreciado

## Objetivo

Remover por completo o menu interativo depreciado da CLI, preservando os comandos
diretos que já oferecem as mesmas automações.

## Alterações

- Remover de `scripthub.cli` o import do serviço de menu, o comando `menu` e o
  alias `m`, incluindo a indicação deles na ajuda contextual da CLI.
- Excluir o pacote `scripthub.services.menu` e seus testes dedicados.
- Remover do README a seção e a tabela que documentam o menu interativo.

## Compatibilidade

`scripthub menu` e `scripthub m` deixam de ser comandos válidos. Os comandos
diretos existentes não terão mudanças de interface ou comportamento.

## Validação

Os testes de CLI devem confirmar que a ajuda não anuncia o menu e que o comando
não está mais registrado. A suíte completa deve manter a cobertura mínima de 80%,
além das verificações de lint e formatação.
