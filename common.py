import hashlib
import logging
import random
from tracker import Tracker


def generate_id(addr, port):
    """Generates a unique ID for each node."""
    id = hashlib.sha512()
    t = addr + str(port) + str(random.randint(1, 99999999))
    id.update(t.encode('ascii'))
    tmp_id = id.hexdigest()
    # logging.info(f'Generating ID for {addr}:{port} : {tmp_id}')
    return tmp_id


def create_tracker(info, channels):
    ott = info['ott']
    #addr_to_id = ott.get_addr_to_id()
    #path = list(map(lambda x: addr_to_id.get(x,None), channels))
    tracker = Tracker(channels)
    return tracker
