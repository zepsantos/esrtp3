import datetime

from message import Message, MessageType


class pingMessage(Message):
    def __init__(self, sender_id,tracker = None):
        super().__init__(sender_id,tracker = tracker)
        self.message = "PING"
        self.type = MessageType.PING

    def ping(self):
        currentTime = datetime.datetime.now()
        ping = currentTime - Message.convert_timestamp(self.get_timestamp())
        return ping.total_seconds()
