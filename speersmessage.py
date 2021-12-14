from message import Message, MessageType


class SPeersMessage(Message):
    def __init__(self, sender_id, neighbours, clients):
        super().__init__(sender_id)
        self.type = MessageType.SPEERS
        self.neighbours = neighbours
        self.clients = clients


    def get_neighbours(self):
        return self.neighbours

    def get_clients(self):
        return self.clients

