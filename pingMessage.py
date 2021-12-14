import datetime

from message import Message, MessageType


class pingMessage(Message):
    def __init__(self, message):
        super().__init__()
        self.message = "PING"
        self.type = MessageType.PING

    def ping(self):
        currentTime = datetime.datetime.now()
        ping = currentTime - Message.convert_timestamp(self.get_timestamp())
        return ping.total_seconds()
