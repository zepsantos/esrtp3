# Commands messages flow in the ott
import logging


class Tracker:
    def __init__(self, channels):
        self.channels = channels
        self.channels_jump_count = 0

    def get_next_channel(self):
        if self.channels_jump_count >= len(self.channels):
            return None
        else:
            self.channels_jump_count += 1
            tmp = self.channels[self.channels_jump_count - 1]

            return tmp

    def get_channels_visited(self):
        return self.channels[:self.channels_jump_count]

    def get_channels_jump_count(self):
        return self.channels_jump_count

    def reach_destination(self, current_node_id):
        return self.channels[-1] == current_node_id

    def extend_channels(self, channels):
        self.channels.extend(channels)

    def get_path(self):
        return self.channels


    def set_path(self, path):
        self.channels = path
        self.channels_jump_count = 0


    def get_channels(self):
        return self.channels


    def get_destination(self):
        return self.destination


    def send_back(self,sender_id):
        path = list(self.get_path())
        path.reverse()
        path.pop(0)
        path.append(sender_id)
        self.extend_channels(path)