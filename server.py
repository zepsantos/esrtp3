import logging
from ott import Ott
def initServer():
    """
    Initializes the server.
    """
    logging.basicConfig(level=logging.NOTSET,
                        format='%(asctime)s - %(levelname)s - %(filename)s:%(funcName)s - %(message)s')
    bootstrapper_info = {}
    ott_manager = Ott(bootstrapper_info)
    ott_manager.serve_forever()
    return



if __name__ == '__main__':
    initServer()
