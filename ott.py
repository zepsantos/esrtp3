import logging
import selectors
import socket
import pickle
from node import Node
import nodeprotocol
import json
import common

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
                               data={'handler': self.accept_connection, 'id': 'main'})
        self.clients = []
        self.bootstrapper = False
        self.addr = self.main_socket.getsockname()[0]
        self.id = common.generate_id(HOST, PORT)
        if bootstrapper_info == {}:
            self.bootstrapper = True
        else:
            self.connect_to_bootstrapper(bootstrapper_info)
        self.network_config = {}
        self.load_network_config()

    def accept_connection(self, key, mask, id):
        conn, addr = self.main_socket.accept()
        logging.info(f'Accepted connection from {addr}')
        self.add_node(Node(self, addr[0], addr[1], conn))

    def add_node(self, node):
        self.nodes[node.get_id()] = node
        data = {'handler': self.handle_node_event, 'id': node.get_id()}
        self.selector.register(node.get_socket(), selectors.EVENT_READ | selectors.EVENT_WRITE, data=data)

    def remove_node(self, node):
        self.nodes.pop(node)

    def get_nodes(self):
        return list(map(lambda node: node.get_addr(), self.nodes))

    def handle_node_event(self, key, mask, id):

        node = self.nodes[id]
        try:
            if mask & selectors.EVENT_READ:
                message = key.recv(1024)
                self.handleRead(node, message)

            if mask & selectors.EVENT_WRITE:
                tosend = self.handleWrite(node)
                if tosend:
                    key.send(tosend)
        except Exception as e:
            return

    def handleRead(self, node, message):
        if message:
            message = pickle.loads(message)
            status = node.get_status()
            handler = nodeprotocol.get_handler(status, True)
            if handler is None: return
            info = {'node': node, 'message': message, 'id': self.id, 'ott': self}
            logging.info(f'{node.get_addr()} : {message}')
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
        info = {'node': node, 'id': self.id, 'ott': self}
        tosend = handler(info)
        return tosend

    def serve_forever(self):

        while True:
            # Wait until some registered socket becomes ready. This will block
            # for 200 ms.
            events = self.selector.select(timeout=0.2)

            # For each new event, dispatch to its handler
            for key, mask in events:
                handler = key.data['handler']
                handler(key.fileobj, mask, key.data['id'])

    def connect_to_bootstrapper(self, bootstrapper_info):
        addr = bootstrapper_info['addr']
        port = bootstrapper_info['port']
        self.connect_to_node(addr, port)

    def connect_to_node(self, addr, port):
        print(f'{addr} : {port}')
        node = Node(self, addr, port)
        self.add_node(node)

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
