import logging
import sys
from enum import Enum
import pickle
from message import Message, MessageType
from speersmessage import SPeersMessage
from ACKMessage import ACKMessage


# NODE que se liga ao bootstrap manda pedido ACK com id , boootstrap manda lista de vizinhos ( NODE(BOOTSTRAP)  = status(CONNECTING) , NODE(NODE) = status(ACK)
# status(CONNECTING) -> RECEIVING ACK -> SEND ACK -> status(CONNECTED) -> status(IDLE) -> status(DISCONNECTED) (BOOTSTRAP)
# SEND ACK(com id) -> RECEIVE ACK ->recebe id e lista vizinhos -> status(CONNECTED) -> status(IDLE) -> status(DISCONNECTED) (NODE)
# NODE connect to lista vizinhos (NODE)
class NodeStatus(Enum):
    ACKSENDING = 1 #Sending ACK
    ACKRECEIVING = 2 #Receiving ACK
    SPEERS = 3  # Sending Peers
    WPEERS = 4  # waiting Peers
    CONNECTED = 5 # Connected
    OFFLINE = 6 # Offline


## VERIFICAR SE AINDA NAO EXISTE LIGACAO QUANDO O NODE ESTA A LIGAR SE AOS PEERS
def handle_RPeers(info):
    message = info['message']
    node = info['node']
    ott = info['ott']
    if message.get_type() != MessageType.SPEERS: return
    node.set_status(NodeStatus.CONNECTED)

    for peer in message.get_neighbours():
        logging.debug(f'peer: {peer}')
        ott.connect_to_node(peer,7000)
    ott.add_clients(message.get_clients())


def handle_SPeers(info):
    node = info['node']
    ott = info['ott']
    noderepr = ott.get_network_config()[node.get_addr()]
    neighbors = noderepr['neighbors']
    clients = noderepr['clients']
    speersmessage = SPeersMessage(ott.get_ott_id(), neighbors, clients)
    node.set_status(NodeStatus.CONNECTED)
    tmp = pickle.dumps(speersmessage)
    logging.debug(f'size of speersmessage: {sys.getsizeof(tmp)}')
    return tmp


# RECEBE O ACK E METE O NODO EM NodeStatus.SPEERS e da set do id do node
def handle_AckReceive(info):
    message = info['message']
    node = info['node']
    if message.get_type() != MessageType.ACK: return
    node.set_status(NodeStatus.SPEERS)
    node.set_id(message.get_sender_id())
    logging.debug(f'id received and updated: {node.get_id()}')


def handle_AckSend(info):
    id = info['id']
    node = info['node']
    message = ACKMessage(id)
    pickled = pickle.dumps(message)
    node.set_status(NodeStatus.WPEERS)
    return pickled


def get_handler(status, read):
    if read:
        dic = {
            NodeStatus.ACKRECEIVING: handle_AckReceive,
            NodeStatus.WPEERS: handle_RPeers
        }
    else:
        dic = {
            NodeStatus.ACKSENDING: handle_AckSend,
            NodeStatus.SPEERS: handle_SPeers
        }

    tmp = dic.get(status, None)
    #logging.debug(f'handler: {tmp}')
    return tmp


def nofunc(info):
    pass
