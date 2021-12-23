import logging
import select
import selectors
import socket
import pickle
import string
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
import testes
from dataMessage import DataMessage
from node import Node
import nodeprotocol
import json
import common
from time import sleep
from netifaces import interfaces, ifaddresses, AF_INET
from pingMessage import pingMessage
from requestStream import RequestStreamMessage
from tracker import Tracker

HOST = '0.0.0.0'
PORT = 7000
num_of_threads = 2


# https://github.com/eliben/python3-samples/blob/master/async/selectors-async-tcp-server.py

class Ott:

    def __init__(self, bootstrapper_info):
        self.nodes = {}
        self.node_id = {}
        self.addr = self.get_node_ip()
        self.main_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.main_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.main_socket.bind((self.addr, PORT))
        self.main_socket.listen(5)
        self.poll = select.poll()
        self.poll.register(self.main_socket.fileno(), select.POLLIN)
        self.bootstrapper = False

        self.id = common.generate_id(HOST, PORT)
        self.executor = ThreadPoolExecutor(num_of_threads)
        logging.info(f'Ott id: {self.id}')
        if bootstrapper_info == {}:
            self.bootstrapper = True
            self.network_config = {}
            self.load_network_config()
        else:
            self.connect_to_bootstrapper(bootstrapper_info)
        self.neighbours = []
        self.toDispatch = {}

    def get_node_ip(self):
        interf = interfaces()
        tmp = ifaddresses(interf[1]).setdefault(AF_INET, [{'addr': '0.0.0.0'}])
        return tmp[0]['addr']

    def accept_connection(self, key):
        conn, addr = self.main_socket.accept()
        logging.info(f'Accepted connection from {addr}')
        self.add_node(Node(addr[0], addr[1], conn))

    def add_node(self, nodeconn):
        """status, ournode = self.check_node_address(nodeconn.get_addr())
        if status:
            self.poll.unregister(nodeconn.get_socket())
            ournode.received_connection(nodeconn)
        else:
            ournode = nodeconn
            self.nodes[ournode.get_id()] = ournode"""
        self.nodes[nodeconn.get_id()] = nodeconn
        nodeconn.set_change_idcallback(self.node_changed_id)
        nodeconn.set_nodeofflinecallback(self.nodeIsOffline)
        self.node_id[nodeconn.get_socket().fileno()] = nodeconn.get_id()
        self.poll.register(nodeconn.get_socket().fileno(), select.POLLIN | select.POLLOUT)

    def node_changed_id(self, id, newid):
        node = None
        if newid in self.nodes.keys(): #No caso de um node que se conecta e ja esta na rede ja o conhecemos
            node = self.nodes[newid] # O que nós já temos
            newconnnode = self.nodes.pop(id) # O que o node que está a tentar se conectar
            node.set_socket(newconnnode.get_socket()) # Atualizamos o socket do node que já temos
            node.set_addr(newconnnode.get_addr())
            node.set_id(newconnnode.get_id())
            self.nodes[newid] = node # Atualizamos o node que já temos , talvez nao precisemos de dar update ao nodo
            self.node_id[node.get_socket().fileno()] = newid
           # self.poll.unregister(newconnnode.get_socket().fileno())
            self.poll.unregister(node.get_socket().fileno())
            self.remove_node(newconnnode)
        else:
            node = self.nodes.pop(id)
        dispatcher_oldid = self.toDispatch.pop(id, [])
        dispatcher_newid = self.toDispatch.pop(newid, [])
        dispatcher_newid.extend(dispatcher_oldid)
        self.toDispatch[newid] = dispatcher_newid
        self.node_id[node.get_socket().fileno()] = newid
        self.nodes[newid] = node



    def connect_to_node(self, addr, port):
        logging.debug(f'Connecting to {addr}:{port}')
        inNetwork, node = self.check_node_address(addr)
        if not inNetwork:
            node = Node(addr, port)
            self.add_node(node)
        else:  ## TODO: check if node is connected if not reconnect (open the discriptor and read(provavelmente))
            node.reconnect()
            return

    def remove_node(self, node):
        self.nodes.pop(node)

    def get_nodes(self):
        return self.nodes.values()

    def handle_node_event(self, key, event):
        # if node is not self.neighbours
        id = self.node_id.get(key, None)
        node = self.nodes.get(id, None)
        if node is None:
            self.poll.unregister(key)
            return

        if event & select.POLLIN:
            message = node.receive()
            self.executor.submit(self.handleRead, (node, message))
        if event & select.POLLOUT:
            self.executor.submit(self.handleWrite, node)

        if event & select.EPOLLHUP:
            node = self.getNodeByfileno(key)
            self.poll.unregister(key)
            node.get_socket().close()
            del self.node_id[key]

    def getNodeByfileno(self, fileno):
        return self.nodes[self.node_id[fileno]]

    def nodeIsOffline(self, node):
        self.poll.unregister(node.get_socket().fileno())
        self.node_id.pop(node.get_socket().fileno())

    def handleRead(self, info):
        node, message = info
        if node is None:
            return
        if message:
            # logging.debug(f'Received from {node.get_id()} : {message}')
            message = pickle.loads(message)
            status = node.get_status()
            handler = nodeprotocol.get_handler(status, True)
            if handler is None: return
            info = {'node': node, 'message': message, 'ott': self}
            handler(info)

    def get_ott_id(self):
        return self.id

    def handleWrite(self, node):
        if node is None: return
        status = node.get_status()
        tosend = None
        handler = nodeprotocol.get_handler(status, False)
        if handler is None: return None
        info = {'node': node, 'ott': self}
        tosend = handler(info)
        if tosend:
            # logging.debug(f'Sending to {node.get_id()} : {tosend}')
            node.send(tosend)
        # return tosend

    def serve_forever(self):
        try:
            while True:
                time.sleep(0.01)
                events = self.poll.poll(1)
                # For each new event, dispatch to its handler
                for key, event in events:
                    self.handler(key, event)
        finally:
            pass  # close all sockets

    def handler(self, key, event):
        if key == self.main_socket.fileno():
            self.accept_connection(key)
        else:
            self.handle_node_event(key, event)

    def connect_to_bootstrapper(self, bootstrapper_info):
        addr = bootstrapper_info['addr']
        port = bootstrapper_info['port']
        self.connect_to_node(addr, port)

    # Checks if we already have a connection with the node by his address
    def check_node_address(self, node_addr):
        for node in self.nodes.values():
            if node.get_addr() == node_addr:
                return True, node
        return False, None

    def load_network_config(self):
        with open('networkconfigotim.json', 'r') as f:
            self.network_config = json.load(f)  # load networkconfig.json

    # Verifica se o id existe
    def check_id(self, id):
        return self.nodes.get(id) is None

    def get_network_config(self):
        return self.network_config

    def get_selector(self):
        return self.poll

    def is_bootstrapper(self):
        return self.bootstrapper

    def add_neighbours(self, neighbours):
        self.neighbours.extend(neighbours)
        for node in neighbours:
            self.connect_to_node(node, 7000)

    def get_neighbours(self):
        if len(self.neighbours) == 0 and self.bootstrapper:
            noderepr = self.network_config[self.addr]
            neighbors = noderepr['neighbors']
            self.neighbours.extend(neighbors)
        return self.neighbours

    def get_neighbours_nodesids(self):
        res = []
        tmp = self.get_addr_to_id()
        for neig in self.get_neighbours():
            res.append(tmp[neig])
        return res

    """def node_changed_id(self, id, newid):
        node = self.nodes.pop(id)
        dispatcher_oldid = self.toDispatch.pop(id, [])
        dispatcher_newid = self.toDispatch.pop(newid, [])
        dispatcher_newid.extend(dispatcher_oldid)
        self.toDispatch[newid] = dispatcher_newid
        self.node_id[node.get_socket().fileno()] = newid
        self.nodes[newid] = node
        # data = {'handler': self.handle_node_event, 'node': node}"""

    def add_toDispatch(self, id, message):
        node = self.nodes.get(id, None)
        if node is None: return
        dispatcher = self.toDispatch.get(id, [])
        #  if dispatcher:
        #    self.poll.modify(node.get_socket().fileno(), select.POLLOUT)
        dispatcher.append(message)
        self.toDispatch[id] = dispatcher

    def add_toDispatchByAddr(self, addr, message):
        id = self.get_addr_to_id().get(addr, None)
        if id is not None:
            self.add_toDispatch(id, message)
        else:
            logging.debug('Node not found')  ## Envia para todos?

    def get_toDispatch(self, id):
        tmp = self.toDispatch.get(id, [])
        ret = None
        if len(tmp) > 0:
            ret = tmp.pop(0)
        # if len(tmp) == 0:
        # self.poll.modify(self.nodes.get(id).get_socket().fileno(),select.POLLIN)
        return ret

    def get_addr_to_id(self):
        addrToId = {}
        for node in self.nodes.values():
            addrToId[node.get_addr()] = node.get_id()
        if self.bootstrapper:
            addrToId[self.addr] = self.id
        return addrToId

    # Adiciona uma stream a transmitir pelo nosso path
    def send_data(self, packet, addrs, path):
        addr_dic = self.get_addr_to_id()
        path_id = self.convertPathToId(path)
        logging.debug(f'path_id: {path_id}')
        #time.sleep(5)
        if None not in path_id:
            ids = list(map(lambda a: addr_dic[a], addrs))
            if id is not None:
                tracker = Tracker(path_id, destination=ids)
                datapacket = DataMessage(id, tracker, packet)
                self.add_toDispatch(tracker.get_next_channel(self.get_ott_id()), datapacket)
        else:
            logging.debug('Client not found')



    def convertPathToId(self, l):
        tmp = []
        addr_dic = self.get_addr_to_id()
        for p in l:
            if isinstance(p,list):
                tmp.append(self.convertPathToId(p))
            else:
                tmp.append(addr_dic[p])
        return tmp


    def send_ping(self, addr, path):
        logging.debug('Sending ping')
        addr_dic = self.get_addr_to_id()
        path_id = list(map(lambda a: addr_dic.get(a, None), path))
        if None not in path_id:
            id = addr_dic.get(addr, None)
            if id is not None:
                tracker = Tracker(path_id, destination=id)
                datapacket = pingMessage(id, tracker)

                self.add_toDispatch(tracker.get_next_channel(self.get_ott_id()), datapacket)
        else:
            logging.debug('Client not found')

    def broadcast_message(self, addr):
        info = {'ott': self}
        status, node = self.check_node_address(addr)
        if status:
            id = node.get_id()
            if id is not None:
                tracker = Tracker([-1], destination=id)
                datapacket = pingMessage(id, tracker)
                info['message'] = datapacket
                nodeprotocol.sendToAllNodes(info)

    def setDataCallback(self, callback):
        self.dataCallback = callback

    def checkIfNodeIsNeighbour(self, node):
        for neighbour in self.get_neighbours():
            if node.get_addr() == neighbour:
                return True
        return False


def initOtt():
    logging.basicConfig(level=logging.NOTSET,
                        format='%(asctime)s - %(levelname)s - %(filename)s:%(funcName)s - %(message)s')
    asd = {}
    if len(sys.argv) > 1:
        hostip = sys.argv[1]
        asd = {'addr': hostip, 'port': 7000}

    ott_manager = Ott(asd)
    ott_manager.serve_forever()


if __name__ == '__main__':
    initOtt()
