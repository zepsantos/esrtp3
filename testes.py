# envia ping
import pickle

import nodeprotocol
import paths
from common import create_tracker
from pingMessage import pingMessage
from tracker import Tracker


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

def trackerteste():
    pathlist = paths.multicast_path_list("10.0.0.10", ["10.0.3.20","10.0.4.20"])
    path = paths.multicast_path2(pathlist)
    tracker = Tracker(path)
    trackers = []
    tracker.get_next_channel("sad")
    tracker.get_next_channel("asdasd")
    tmp = tracker.get_next_channel("asd")
    multicastsd = dropMulticastPath(path,tmp)
    if isinstance(tmp,list):
        for l in tmp:

            pathToTracker = path + l
            nt = Tracker(pathToTracker)
            trackers.append(nt)
    else:
        print(path)
    for t in trackers:
        print(t.get_path())

def dropMulticastPath(path, drop_list):
    lsts = list(path)
    lsts.remove(drop_list)
    return lsts


if __name__ == '__main__':
    trackerteste()

