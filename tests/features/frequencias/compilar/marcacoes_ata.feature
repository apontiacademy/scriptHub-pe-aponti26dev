# language: pt
Funcionalidade: Marcações visuais e regras de faltas na ata de frequência
  Como responsável pela emissão das atas de frequência mensal
  Quero que a ata em PDF distinga visualmente matrícula tardia, aula
  realocada e níveis de falta
  Para que a leitura da ata não seja ambígua nem penalize erroneamente os alunos

  Cenário: Matrícula tardia é distinta de justificativa comum na mesma linha
    Dado um aluno com matrícula tardia numa sessão anterior à data de início da matrícula
    E uma justificativa comum numa sessão posterior à matrícula
    Quando a ata mensal é gerada
    Então a célula da sessão de matrícula tardia é marcada como "não matriculado"
    E a célula da sessão com justificativa comum não é marcada como "não matriculado"

  Cenário: Matrícula tardia não aparece na lista de justificativas da página
    Dado um aluno com matrícula tardia numa sessão anterior à data de início da matrícula
    E uma justificativa comum numa sessão posterior à matrícula
    Quando a ata mensal é gerada
    Então a lista de justificativas da página contém apenas a justificativa comum

  Cenário: Sessão com status AR é marcada como realocada sem alterar os demais status
    Dado uma sessão em que um aluno tem status "AR"
    E outro aluno tem status "AT" na mesma sessão
    Quando a ata mensal é gerada
    Então a sessão é marcada como realocada
    E o aluno com status "AT" mantém esse status na mesma sessão

  Cenário: Status AR conta como presença no cálculo de faltas
    Dado um aluno com status "AR" numa sessão e status "AU" em outra
    Quando o percentual e a contagem de faltas do aluno são calculados
    Então apenas a sessão com status "AU" conta como falta
    E a sessão com status "AR" conta como presença no resumo geral

  Cenário: Três faltas no mês destacam a linha em vermelho
    Dado um aluno com 3 falta(s) no mês
    Quando a ata mensal é gerada
    Então a linha desse aluno é destacada com o nível "risco"

  Cenário: Exatamente duas faltas no mês destacam a linha em amarelo, nunca em vermelho
    Dado um aluno com 2 falta(s) no mês
    Quando a ata mensal é gerada
    Então a linha desse aluno é destacada com o nível "atencao"
    E a linha desse aluno não é destacada com o nível "risco"

  Esquema do Cenário: Zero ou uma falta no mês não geram destaque
    Dado um aluno com <faltas> falta(s) no mês
    Quando a ata mensal é gerada
    Então a linha desse aluno não recebe nenhum nível de destaque

    Exemplos:
      | faltas |
      | 0      |
      | 1      |
