import logging
import sys
import time
from enum import Enum
import pickle
from message import Message, MessageType
from pingMessage import pingMessage
from speersmessage import SPeersMessage
from ACKMessage import ACKMessage
from tracker import Tracker


# NODE que se liga ao bootstrap manda pedido ACK com id , boootstrap manda lista de vizinhos ( NODE(BOOTSTRAP)  = status(CONNECTING) , NODE(NODE) = status(ACK)
# status(CONNECTING) -> RECEIVING ACK -> SEND ACK -> status(CONNECTED) -> status(IDLE) -> status(DISCONNECTED) (BOOTSTRAP)
# SEND ACK(com id) -> RECEIVE ACK ->recebe id e lista vizinhos -> status(CONNECTED) -> status(IDLE) -> status(DISCONNECTED) (NODE)
# NODE connect to lista vizinhos (NODE)

class NodeStatus(Enum):
    ACKSENDING = 1  # Sending ACK
    ACKRECEIVING = 2  # Receiving ACK
    SPEERS = 3  # Sending Peers
    WPEERS = 4  # waiting Peers
    CONNECTED = 5  # Connected
    OFFLINE = 6  # Offline
    FACK = 7  # Final ACK
    WACK = 8  # Waiting final ACK


def handle_RPeers(info):
    message = info['message']
    node = info['node']
    ott = info['ott']
    if message.get_type() != MessageType.SPEERS: return
    node.set_id(message.get_sender_id())
    ott.add_neighbours(message.get_neighbours())
    node.set_status(NodeStatus.FACK)


def handle_SPeers(info):
    node = info['node']
    ott = info['ott']
    if ott.bootstrapper:
        noderepr = ott.get_network_config()[node.get_addr()]
        neighbors = noderepr['neighbors']
        speersmessage = SPeersMessage(ott.get_ott_id(), neighbors)
    else:
        speersmessage = SPeersMessage(ott.get_ott_id(), [])
    node.set_status(NodeStatus.WACK)
    tmp = pickle.dumps(speersmessage)
    return tmp


# RECEBE O ACK E METE O NODO EM NodeStatus.SPEERS e da set do id do node
def handle_AckReceive(info):
    message = info['message']
    node = info['node']
    if message.get_type() != MessageType.ACK: return
    node.set_id(message.get_sender_id())
    node.set_status(NodeStatus.SPEERS)


def handle_AckSend(info):
    ott = info['ott']
    node = info['node']
    id = ott.get_ott_id()
    message = ACKMessage(id)
    pickled = pickle.dumps(message)
    node.set_status(NodeStatus.WPEERS)
    return pickled


def sendToAllNodes(info):
    ott = info['ott']
    message = info['message']
    tracker = message.get_tracker()

    maintracker = tracker.__clone__()
    node_ids = ott.get_neighbours_nodesids()

    maintracker.add_channels_visits(node_ids)
    for node_id in node_ids:
        print(f'Sending message to {node_id}')
        if tracker.alreadyPassed(node_id):
            continue
        else:
            message.set_tracker(maintracker)
            ott.add_toDispatch(node_id, message)


def handle_connectedR(info):
    node = info['node']
    ott = info['ott']
    message: Message = info['message']
    tracker = message.get_tracker()
    reached_destination = tracker.reach_destination(ott.get_ott_id())

    #logging.debug(f' reach_destination: {reached_destination} destination: {tracker.get_destination()}')
    if not reached_destination:
        tracker_nxt_channel = tracker.get_next_channel(ott.get_ott_id())
        if tracker_nxt_channel == -1:
            sendToAllNodes(info)
        elif isinstance(tracker_nxt_channel,list):
            trackers = tracker.separateMulticast()
            for t in trackers:
               # logging.debug(f'Sending message to {t.get_path()}')
                tmp_nxt_channel = t.get_next_channel(ott.get_ott_id())
                message.set_tracker(t)
                ott.add_toDispatch(tmp_nxt_channel, message)
        else:
            ott.add_toDispatch(tracker_nxt_channel, message)
        # logging.info(f' Transmiting to next peer with id: {nextdestination_id}')

    else:
        if message.get_type() == MessageType.DATA:
            ott.dataCallback(message.get_rtppacket())
        elif message.get_type() == MessageType.PING:
            if (ott.bootstrapper):
                delay = message.ping()
                logging.info(f'Received ping with delay: {delay}')
            else:
                logging.info("Received ping from server with delay: " + str(message.ping()))
                tracker.send_back(message.get_sender_id())
                # logging.debug(f'Path after receiving ping from bootstrap: {tracker.get_path()}')
                nextdestination_id = tracker.get_next_channel()
                ott.add_toDispatch(nextdestination_id, message)


def handle_connectedW(info):
    node = info['node']
    ott = info['ott']
    toTransmit = ott.get_toDispatch(node.get_id())
    if toTransmit:
        logging.debug(f'Received message to transmit {toTransmit}  to {node.get_id()}')
        pickled = pickle.dumps(toTransmit)
        return pickled
    else:
        return None


def handle_AckConfirmation(info):
    node = info['node']
    ott = info['ott']
    message = info['message']
    if message.get_type() != MessageType.ACK: return
    if message.get_sender_id() == node.get_id():
        node.set_status(NodeStatus.CONNECTED)
        if ott.is_bootstrapper() and not ott.checkIfNodeIsNeighbour(node):
           node.disconnect()


def handle_AckConfirmationSend(info):
    node = info['node']
    ott = info['ott']
    id = ott.get_ott_id()
    message = ACKMessage(id)
    pickled = pickle.dumps(message)
    node.set_status(NodeStatus.CONNECTED)
    return pickled


def get_handler(status, read):
    if read:
        dic = {
            NodeStatus.WACK: handle_AckConfirmation,
            NodeStatus.ACKRECEIVING: handle_AckReceive,
            NodeStatus.WPEERS: handle_RPeers,
            NodeStatus.CONNECTED: handle_connectedR
        }
    else:
        dic = {
            NodeStatus.FACK: handle_AckConfirmationSend,
            NodeStatus.ACKSENDING: handle_AckSend,
            NodeStatus.SPEERS: handle_SPeers,
            NodeStatus.CONNECTED: handle_connectedW
        }

    tmp = dic.get(status, None)
    # logging.debug(f'handler: {tmp}')
    return tmp


def nofunc(info):
    pass
