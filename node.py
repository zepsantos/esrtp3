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
            self.node_connect()
            self.status = nodeprotocol.NodeStatus.ACKSENDING
        else:
            self.status = nodeprotocol.NodeStatus.ACKRECEIVING
            self.sock = sock
        if id is None:
            self.id = common.generate_id(addr,port)
        else:
            self.id = id

    def get_addr(self):
        return self.addr

    def get_socket(self):
        return self.sock



    def node_connect(self):
        try:
            self.sock.connect((self.addr, self.port))
        except socket.error:
            self.set_status(nodeprotocol.NodeStatus.OFFLINE)

    def node_disconnect(self):
        self.sock.close()

    def node_reconnect(self):
        connbool = self.node_connect()



    def get_id(self):
        return self.id

    def get_status(self):
        return self.status

    def set_status(self, status):
        self.status = status

    def set_id(self, id):
        self.id = id


