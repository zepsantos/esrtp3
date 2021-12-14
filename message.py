from datetime import time

import datetime
from enum import Enum


class MessageType(Enum):
    ACK = 0
    NACK = 1
    DATA = 2
    REQUEST = 3
    RESPONSE = 4
    ERROR = 5
    UNKNOWN = 6
    MESSAGE = 7
    PING = 8
    SPEERS = 9


def generate_timestamp():
    ct = datetime.datetime.now()
    ts = ct.timestamp()
    return ts

def convert_timestamp(ts):
    ct = datetime.datetime.fromtimestamp(ts)
    return ct

class Message:
    def __init__(self , sender_id, timestamp=None):
        self.type = MessageType.MESSAGE
        self.sender_id = sender_id
        if timestamp is None:
            self.timestamp = generate_timestamp()
        # getter method

    def get_message(self):
        return self.message

    def get_timestamp(self):
        return self.timestamp

    def get_sender_id(self):
        return self.sender_id

    def get_type(self):
        return self.type