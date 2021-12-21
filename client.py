import logging
import socket
import sys
import threading

from tkinter import Tk
from ClienteGui import ClienteGUI
from ott import Ott

bootstrapper_info = {'addr': sys.argv[1], 'port': 7000}

def initOtt():
    """
    Initializes the client.
    """

    global ott_manager
    ott_manager = Ott(bootstrapper_info)
    threading.Thread(target=ott_manager.serve_forever).start()
    return

def initClient():
    askForStream()
    # Create a new client
    root = Tk()
    app = ClienteGUI(root, ott_manager)
    app.master.title("Cliente")
    root.mainloop()


def askForStream():
    clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    clientsocket.connect((bootstrapper_info['addr'], 20000))
    clientsocket.send("movie.Mjpeg".encode())
    clientsocket.close()

if __name__ == '__main__':
    logging.basicConfig(level=logging.NOTSET,
                        format='%(asctime)s - %(levelname)s - %(filename)s:%(funcName)s - %(message)s')
    initOtt()
    initClient()



