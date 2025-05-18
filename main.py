import core.view as v
import core.controller as controller
import signal
import sys

def handle_sigint(signum, frame):
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, handle_sigint)
    
    v.main_menu(isFromMain=True)
    # controller.scan_new_token()