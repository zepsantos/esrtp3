import socket
import sys

import logging
import ott
from netifaces import interfaces, ifaddresses, AF_INET

def init():
    logging.basicConfig(level=logging.NOTSET, format= '%(asctime)s - %(levelname)s - %(filename)s:%(funcName)s - %(message)s')
    bootstrapper_info = {}
    if len(sys.argv) == 1:
        logging.info("INITIATING BOOTSTRAPER")
    # bootstrapper.start(o)
    else:
        #print(sys.argv[1])
        hostip = sys.argv[1]
        bootstrapper_info = {'addr': hostip, 'port': 7000}
    #  client_thread = threading.Thread(target=client.start_client, args=(bootstraper_info,))
    #  client_thread.start()
    #  client_thread.join()

    for ifaceName in interfaces():
        addresses = [i['addr'] for i in ifaddresses(ifaceName).setdefault(AF_INET, [{'addr': 'No IP addr'}])]
       # print(' '.join(addresses))
    ott_manager = ott.Ott(bootstrapper_info)
    ott_manager.serve_forever()



if __name__ == '__main__':
    init()
