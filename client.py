import logging
import sys
import threading

from tkinter import Tk
from ClienteGUI import ClienteGUI
from ott import Ott


def initClient():
    """
    Initializes the client.
    """

    try:
        addr = sys.argv[1]
        port = 7000
    except:
        print("[Usage: Cliente.py serveraddr]\n")
    logging.basicConfig(level=logging.NOTSET,
                        format='%(asctime)s - %(levelname)s - %(filename)s:%(funcName)s - %(message)s')

    bootstrapper_info = {'addr': addr, 'port': port}
    ott_manager = Ott(bootstrapper_info)
    # Create a new client
    root = Tk()
    app = ClienteGUI(root, ott_manager)
    threading.Thread(target= ott_manager.serve_forever()).start()
    app.master.title("Cliente")
    root.mainloop()

    return

if __name__ == '__main__':
    initClient()



