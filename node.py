import logging
import socket
import nodeprotocol
import common


class Node():

    def __init__(self, ott, addr, port, sock=None, id=None, callback=None):
        self.addr = addr
        self.callback = callback
        self.port = port

        self.ott = ott
        if sock is None:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.connect()
        else:
            self.status = nodeprotocol.NodeStatus.ACKRECEIVING
            self.sock = sock
        if id is None:
            self.id = common.generate_id(addr, port)
        else:
            self.id = id
        self.sock.setblocking(False)

    def get_addr(self):
        return self.addr

    def get_socket(self):
        return self.sock

    def connect(self):
        try:
            logging.debug("Connecting to node: " + str(self.addr) + ":" + str(self.port))
            self.sock.connect((self.addr, self.port))
            self.set_status(nodeprotocol.NodeStatus.ACKSENDING)
        except socket.error:
            logging.debug("Could not connect to node %s:%d" % (self.addr, self.port))
            self.set_status(nodeprotocol.NodeStatus.OFFLINE)

    def disconnect(self):
        self.sock.close()

    def reconnect(self):
        if self.get_status() == nodeprotocol.NodeStatus.OFFLINE:
            self.connect()

    def get_id(self):
        return self.id

    def get_status(self):
        return self.status

    def get_port(self):
        return self.port

    def set_status(self, status):
        self.status = status
        logging.debug("Node %s:%d status changed to %s" % (self.addr, self.port, status))

    def set_id(self, newid):
        tmp = self.id
        self.id = newid
        self.ott.node_changed_id(tmp, newid)

    def received_connection(self, connnode):
        self.addr = connnode.get_addr()
        self.port = connnode.get_port()
        self.sock = connnode.get_socket()
        self.set_status(nodeprotocol.NodeStatus.ACKRECEIVING)
