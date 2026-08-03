# language: pt
Funcionalidade: Perfis, diretórios padrão do SO e keyring (issue #78)
  Como usuário do scriptHub
  Quero que configuração, dados e log sejam isolados por profile e usem os
  diretórios padrão do sistema operacional, com a senha do Moodle no keyring
  em vez de arquivos .env

  Cenário: set-profile persiste e é usado nas execuções seguintes
    Dado que nenhum profile está persistido
    Quando o usuário roda "scripthub set-profile equipe-noturna"
    Então o profile ativo passa a ser "equipe-noturna"
    E o profile "equipe-noturna" permanece ativo nas execuções seguintes

  Cenário: unset-profile volta para default quando o profile ativo não é default
    Dado que o profile "equipe-noturna" está persistido
    Quando o usuário roda "scripthub unset-profile"
    Então o profile ativo passa a ser "default"

  Cenário: unset-profile é no-op quando o profile ativo já é default
    Dado que o profile ativo já é "default"
    Quando o usuário roda "scripthub unset-profile"
    Então nada muda no profile persistido

  Cenário: --profile é um override pontual que não altera o profile persistido
    Dado que o profile "equipe-diurna" está persistido
    Quando o usuário roda um comando com a flag "--profile equipe-noturna"
    Então a execução usa o profile "equipe-noturna"
    Mas o profile persistido continua sendo "equipe-diurna"
    E a próxima execução sem a flag usa o profile "equipe-diurna"

  Cenário: dois profiles não vazam config/dados entre si
    Dado dois profiles diferentes com config própria para o mesmo script
    Quando o usuário alterna entre os dois profiles
    Então cada execução só enxerga a config do profile ativo

  Cenário: log é compartilhado só por profile, entre scripts diferentes
    Dado múltiplos scripts rodando sob o mesmo profile
    Quando eles geram log
    Então todos escrevem no mesmo arquivo de log daquele profile

  Cenário: configuração não lê mais .env
    Dado a versão nova instalada
    Quando qualquer script carrega configuração
    Então o usuário do Moodle vem de "settings.toml"
    E a senha do Moodle vem do keyring do sistema operacional
    E cada script tem sua própria entrada de keyring, sem colisão entre scripts

  Cenário: senha do Moodle no keyring também é isolada por profile
    Dado dois profiles diferentes usando o mesmo script
    Quando cada profile define sua própria senha do Moodle para esse script
    Então cada profile lê de volta só a própria senha, sem vazamento entre profiles

  Cenário: migrate-legacy-config migra sem perda de dados
    Dado uma instalação existente no layout antigo, com settings.json, dados/ e .env
    Quando o usuário roda "scripthub migrate-legacy-config"
    Então "settings.json" vira "settings.toml" válido no novo layout por profile e script
    E a pasta "dados/" migra junto
    E "MOODLE_USUARIO" vai para "settings.toml"
    E "MOODLE_SENHA" vai para "keyring"
    E "credentials.json" permanece no caminho já configurado, sem ser movido

  Cenário: migrate-legacy-config é no-op amigável sem arquivos legados
    Dado uma instalação já no layout novo, sem arquivos legados
    Quando o usuário roda "scripthub migrate-legacy-config"
    Então o comando não faz nada destrutivo
