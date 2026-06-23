import sys

from scripthub.services import log

from .main import ESCOPOS, get_config

if __name__ == "__main__":
    try:
        config = get_config()
        for escopo in ESCOPOS:
            escopo(config)
    except Exception as e:
        log.erro(str(e))
        sys.exit(1)
