# Commands messages flow in the ott
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

    def reach_destination(self):
        return self.channels_jump_count == len(self.channels)

    def extend_channels(self, channels):
        self.channels.extend(channels)

    def get_path(self):
        return self.channels


    def set_path(self, path):
        self.channels = path
        self.channels_jump_count = 0


    def get_channels(self):
        return self.channels