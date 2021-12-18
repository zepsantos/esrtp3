# envia ping
import pickle

from common import create_tracker
from pingMessage import pingMessage


def pingTeste(info):
        ott = info['ott']
        tracker = create_tracker(info, ['10.0.0.1', '10.0.1.2'])
        message = pingMessage(ott.get_ott_id(),tracker=tracker)
        return message