from message import Message, MessageType


class RequestStreamMessage(Message):
    def __init__(self, sender_id,tracker = None):
        super().__init__(sender_id,tracker = tracker)
        self.message = "PING"
        self.type = MessageType.RSTREAM


