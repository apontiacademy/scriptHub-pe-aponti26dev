import sys

from scripthub.services import log

from .main import main

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log.erro(str(e))
        sys.exit(1)
