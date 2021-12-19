import logging
import selectors
import socket
import pickle

import testes
from node import Node
import nodeprotocol
import json
import common
from time import sleep

HOST = '0.0.0.0'
PORT = 7000


# https://github.com/eliben/python3-samples/blob/master/async/selectors-async-tcp-server.py

class Ott:

    def __init__(self, bootstrapper_info):
        self.nodes = {}
        # self.init_server()
        self.main_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.main_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.main_socket.bind((HOST, PORT))
        self.main_socket.listen(5)
        self.selector = selectors.DefaultSelector()
        self.selector.register(self.main_socket, selectors.EVENT_READ,
                               data={'handler': self.accept_connection, 'node': None})
        self.clients = []
        self.bootstrapper = False
        self.addr = self.main_socket.getsockname()[0]
        self.id = common.generate_id(HOST, PORT)
        logging.info(f'Ott id: {self.id}')
        if bootstrapper_info == {}:
            self.bootstrapper = True
            self.network_config = {}
            self.load_network_config()
        else:
            self.connect_to_bootstrapper(bootstrapper_info)
        self.neighbours = []
        self.toDispatch = {}

    def accept_connection(self, key, mask, node):
        conn, addr = self.main_socket.accept()
        logging.info(f'Accepted connection from {addr}')
        self.add_node(Node(self, addr[0], addr[1], conn))

    def add_node(self, conn):
        status, ournode = self.check_node_address(conn.get_addr())
        if status:
            ournode.received_connection(conn)
        else:
            ournode = conn
            self.nodes[conn.get_id()] = conn
        data = {'handler': self.handle_node_event, 'node': ournode}  # CUIDADO COM ISTO
        self.selector.register(conn.get_socket(), selectors.EVENT_READ | selectors.EVENT_WRITE, data=data)

    def remove_node(self, node):
        self.nodes.pop(node)

    def get_nodes(self):
        return list(map(lambda node: node.get_addr(), self.nodes))

    def handle_node_event(self, key, mask, node):
        if node is None:
            logging.error('Node is none in handle_node_Event')
            return
        try:
            if mask & selectors.EVENT_READ:
                message = key.recv(1024)
                self.handleRead(node, message)

            if mask & selectors.EVENT_WRITE:
                #print(f' sending to {node.get_id()} dispatcher: {self.get_toDispatch(node.get_id())}')
                tosend = self.handleWrite(node)
                if tosend:
                   # logging.debug(f'Sending to {node.get_id()} : {tosend}')
                    key.send(tosend)
        except Exception as e:
            return

    def handleRead(self, node, message):
        if message:
            message = pickle.loads(message)
            logging.info(f'{node.get_addr()} : {message}')
            status = node.get_status()
            handler = nodeprotocol.get_handler(status, True)
            if handler is None: return
            info = {'node': node, 'message': message, 'ott': self}
            handler(info)

    def get_ott_id(self):
        return self.id

    def add_clients(self, clients):
        self.clients.append(clients)

    def handleWrite(self, node):
        status = node.get_status()
        tosend = None
        handler = nodeprotocol.get_handler(status, False)
        if handler is None: return None
        info = {'node': node, 'ott': self}
        tosend = handler(info)
        return tosend

    def serve_forever(self):
        info = {'ott': self}
        count = 0
        teste = 0
        while True:
            # Wait until some registered socket becomes ready. This will block
            # for 200 ms.
            # teste += 7
            # if teste%10 == 0:
            #     testelista = list(map(lambda node: (node.get_addr(),node.get_status()), self.nodes.values()))
            #    print(f'node status {testelista}')
            if self.bootstrapper and count == 0:
                msg = testes.pingTeste(info)
                addr_to_id = self.get_addr_to_id()
                channels = msg.get_tracker().get_channels()
                path = list(map(lambda x: addr_to_id.get(x, None), channels))
                if None not in path:
                    if testes.checkPathNodeConnected(path, self.nodes):
                        msg.get_tracker().set_path(path)
                        nxt = msg.get_tracker().get_next_channel()
                        #logging.debug('Dispatching ping to ' + str(nxt))
                        self.add_toDispatch(nxt, msg)
                        count += 1

            events = self.selector.select(timeout=0.2)

            # For each new event, dispatch to its handler
            for key, mask in events:
                handler = key.data['handler']
                handler(key.fileobj, mask, key.data['node'])

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

    def connect_to_node(self, addr, port):
        logging.debug(f'Connecting to {addr}:{port}')
        inNetwork, node = self.check_node_address(addr)
        if not inNetwork:
            node = Node(self, addr, port)
            self.add_node(node)
        else:  ## TODO: check if node is connected if not reconnect (open the discriptor and read(provavelmente))
            logging.debug(f'Selectors list {self.selector.get_map().values()}')
            node.reconnect()
            logging.debug(f'Selectors list {self.selector.get_map().values()} after reconnect')
            return

    def load_network_config(self):
        with open('networkconfigotim.json', 'r') as f:
            self.network_config = json.load(f)  # load networkconfig.json

    # Verifica se o id existe
    def check_id(self, id):
        return self.nodes.get(id) is None

    def get_network_config(self):
        return self.network_config

    def get_selector(self):
        return self.selector

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
        self.nodes[newid] = node
        data = {'handler': self.handle_node_event, 'node': node}
        self.selector.modify(node.get_socket(), selectors.EVENT_READ | selectors.EVENT_WRITE, data=data)
        tmp = list(map( lambda a : a.get_status() , self.nodes.values()))

    def add_toDispatch(self, id, message):
        #logging.debug(f'add toDispatch {id} , {message}')
        dispatcher = self.toDispatch.get(id, [])
        dispatcher.append(message)
        self.toDispatch[id] = dispatcher

    def get_toDispatch(self, id):
        tmp = self.toDispatch.get(id, [])
        if len(tmp) > 0:
            return tmp.pop(0)
        return None

    def get_addr_to_id(self):
        addrToId = {}
        for node in self.nodes.values():
            addrToId[node.get_addr()] = node.get_id()
        return addrToId

    # Adiciona uma stream a transmitir pelo nosso path
    def add_stream(self, stream,id):
        pass

