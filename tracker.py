# Commands messages flow in the ott
import logging


class Tracker:
    def __init__(self, channels, destination=None):
        self.channels = channels
        self.channels_jump_count = 0
        self.channels_visited = set()
        self.destination = destination

    def get_next_channel(self, current_node_id):
        if self.channels[self.channels_jump_count] == -1:
            self.channels[self.channels_jump_count] = current_node_id
            self.channels_jump_count += 1
            self.channels.append(-1)
            return -1
        else:
            self.channels_visited.add(current_node_id)
            self.channels_jump_count += 1
            tmp = self.channels[self.channels_jump_count]
            return tmp

    def add_channel_visit(self, node_id):
        self.channels_visited.add(node_id)

    def add_channels_visits(self, node_ids):
        self.channels_visited.update(node_ids)

    def get_channels_visited(self):
        return self.channels[:self.channels_jump_count]

    def get_channels_jump_count(self):
        return self.channels_jump_count

    def reach_destination(self, current_node_id):
        return self.destination[0] == current_node_id

    def extend_channels(self, channels):
        self.channels.extend(channels)

    def get_path(self):
        return self.channels

    def set_path(self, path):
        self.channels = path

    def get_channels(self):
        return self.channels

    def get_destination(self):
        return self.destination

    def send_back(self, sender_id):
        path = list(self.get_path())
        path.reverse()
        path.pop(0)
        path.append(sender_id)
        self.extend_channels(path)

    def alreadyPassed(self, node_id):
        return node_id in self.channels_visited

    def checkMulticast(self, channel):
        return isinstance(channel, list)

    def separateMulticast(self):
        trackers = []
        channel = self.channels[self.channels_jump_count]
        if isinstance(channel, list):
            alreadyvisited = dropMulticastPath(self.get_path(), channel)
            dst = 0
            for ls in channel:
                pathToTracker = alreadyvisited + ls
                nt = self.__clone__()
                nt.set_destination([self.destination[dst]])
                nt.set_path(pathToTracker)
                trackers.append(nt)
                dst += 1
        return trackers

    def __clone__(self):
        t = Tracker(self.channels, destination=self.destination)
        t.channels_jump_count = self.channels_jump_count
        t.channels_visited = set(self.channels_visited)
        return t

    def set_destination(self, destination):
        self.destination = destination


def dropMulticastPath(entirepath, multicastpath):
    singlepath = list(entirepath)
    singlepath.remove(multicastpath)
    return singlepath
