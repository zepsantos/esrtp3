# envia ping
import pickle

import nodeprotocol
from common import create_tracker
from pingMessage import pingMessage


def pingTeste(info):
    ott = info['ott']
    tracker = create_tracker(info, ['10.0.0.1', '10.0.1.2'])
    message = pingMessage(ott.get_ott_id(), tracker=tracker)
    return message


def checkPathNodeConnected(path, nodedic):
    for p in path:
        tmp = nodedic.get(p, None)
        if tmp is None:
            return False
        else:
            if tmp.get_status() != nodeprotocol.NodeStatus.CONNECTED:
                return False
    return True
