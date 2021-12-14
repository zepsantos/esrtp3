import hashlib
import logging
import random


def generate_id(addr, port):
    """Generates a unique ID for each node."""
    id = hashlib.sha512()
    t = addr + str(port) + str(random.randint(1, 99999999))
    id.update(t.encode('ascii'))
    tmp_id = id.hexdigest()
    logging.info(f'Generating ID for {addr}:{port} : {tmp_id}')
    return tmp_id
