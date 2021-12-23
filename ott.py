import logging
import select
import selectors
import socket
import pickle
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
        self.main_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.main_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.main_socket.bind((HOST, PORT))
        self.main_socket.listen(5)
        self.poll = select.poll()
        self.poll.register(self.main_socket.fileno(), select.POLLIN)
        self.bootstrapper = False
        self.addr = self.main_socket.getsockname()[0]
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

    def accept_connection(self, key):
        conn, addr = self.main_socket.accept()
        logging.info(f'Accepted connection from {addr}')
        self.add_node(Node(addr[0], addr[1], conn))

    def add_node(self, nodeconn):
        status, ournode = self.check_node_address(nodeconn.get_addr())
        if status:
            ournode.received_connection(nodeconn)
            #self.selector.unregister(nodeconn.get_socket())
        else:
            ournode = nodeconn
            self.nodes[nodeconn.get_id()] = nodeconn
        nodeconn.set_change_idcallback(self.node_changed_id)
        nodeconn.set_nodeofflinecallback(self.nodeIsOffline)
        self.node_id[nodeconn.get_socket().fileno()] = ournode.get_id()
        self.poll.register(nodeconn.get_socket().fileno(), select.POLLIN | select.POLLOUT)

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
        return list(map(lambda node: node.get_addr(), self.nodes.values()))

    def handle_node_event(self, key, event):
        # if node is not self.neighbours
        id = self.node_id.get(key, None)
        node = self.nodes.get(id, None)
        if node is None:
            self.poll.unregister(key)
            return

        if event & select.POLLIN:
            message = node.receive()
            self.executor.submit(self.handleRead,(node, message))
        if event & select.POLLOUT:
            self.executor.submit(self.handleWrite, node)

        if event & select.EPOLLHUP:
            node = self.getNodeByfileno(key)
            self.poll.unregister(key)
            node.get_socket().close()
            del self.node_id[key]

    def getNodeByfileno(self, fileno):
        return self.nodes[self.node_id[fileno]]

    def nodeIsOffline(self,node):
        self.poll.unregister(node.get_socket().fileno())
        self.node_id.pop(node.get_socket().fileno())


    def handleRead(self,info):
        node,message = info
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
                    self.handler(key,event)
        finally:
            pass #close all sockets

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

    def add_neighbour(self, neighbour):
        self.neighbours.append(neighbour)
        for node in neighbour:
            self.connect_to_node(node, 7000)

    def node_changed_id(self, id, newid):
        node = self.nodes.pop(id)
        dispatcher_oldid = self.toDispatch.pop(id, [])
        dispatcher_newid = self.toDispatch.pop(newid, [])
        dispatcher_newid.extend(dispatcher_oldid)
        self.toDispatch[newid] = dispatcher_newid
        self.node_id[node.get_socket().fileno()] = newid
        self.nodes[newid] = node
        # data = {'handler': self.handle_node_event, 'node': node}

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
        return addrToId

    # Adiciona uma stream a transmitir pelo nosso path
    def send_data(self, packet, addr, path):
        addr_dic = self.get_addr_to_id()
        path_id = list(map(lambda a: addr_dic.get(a, None), path))
        if None not in path_id:
            id = addr_dic.get(addr, None)
            if id is not None:
                tracker = Tracker(path_id)
                datapacket = DataMessage(id, tracker, packet)
                self.add_toDispatch(tracker.get_next_channel(), datapacket)
        else:
            logging.debug('Client not found')

    def send_ping(self, addr, path):
        logging.debug('Sending ping')
        addr_dic = self.get_addr_to_id()
        path_id = list(map(lambda a: addr_dic.get(a, None), path))
        if None not in path_id:
            id = addr_dic.get(addr, None)
            if id is not None:
                tracker = Tracker(path_id)
                datapacket = pingMessage(id, tracker)
                self.add_toDispatch(tracker.get_next_channel(), datapacket)
        else:
            logging.debug('Client not found')

    def setDataCallback(self, callback):
        self.dataCallback = callback


    def checkIfNodeIsNeighbour(self,node):
        for neighbour in self.neighbours:
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
