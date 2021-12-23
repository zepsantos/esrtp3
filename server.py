import logging
import sys
import threading
import time
import socket

import paths
from RtpPacket import RtpPacket
from VideoStream import VideoStream
from ott import Ott

class Server:
    clientInfo = {}

    def __init__(self):
        """
        Initializes the server.
        """
        self.filename = "movie.Mjpeg"
        # videoStram

        return


    def main(self):
        print(self.getPathToGo('10.0.3.20'))
        self.initOtt()
        self.initServer()


    def initOtt(self):
        """
        Initializes the server.
        """
        global ott_manager
        bootstrapper_info = {}
        ott_manager = Ott(bootstrapper_info)
        threading.Thread(target=ott_manager.serve_forever).start()
        return

    def initServer(self):
        """
        Initializes the server.
        """
        socketServer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socketServer.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        socketServer.bind(('10.0.0.10', 20000))
        socketServer.listen(5)
        while True:
            clientSocket, address = socketServer.accept()
            logging.info("Client connected from: %s", address)
            message = clientSocket.recv(1024).decode()
            threading.Thread(target=self.acceptStreamRequest, args=(address,message)).start()
            clientSocket.close()
        return


    def acceptStreamRequest(self,address,message):
        """
        Accepts a stream request.
        """
        try:
            self.clientInfo[address[0]] = VideoStream(message)
            self.sendThroughOtt(address[0])
        except IOError:
            self.clientInfo[address[0]] = VideoStream(self.filename)
            self.sendThroughOtt(address[0])
        return

    def sendThroughOtt(self,address):
        path = self.getPathToGo(address)
        while True:
            #ott_manager.send_ping(address, path)
            data = self.clientInfo[address].nextFrame()
            if data:
                frameNumber = self.clientInfo[address].frameNbr()
                packet = self.makeRtp(data, frameNumber)
                ott_manager.send_data(packet, address, path)
            time.sleep(0.05)


    def sendPingToClient(self,address):
        path = self.getPathToGo(address)
        ott_manager.send_ping(address, path)


    def getPathToGo(self,addr):
        graph = paths.initGraph()
        path = paths.shortest_path('10.0.0.10',addr,graph)
        return path[1:]

    def makeRtp(self, payload, frameNbr):
        """RTP-packetize the video data."""
        version = 2
        padding = 0
        extension = 0
        cc = 0
        marker = 0
        pt = 26  # MJPEG type
        seqnum = frameNbr
        ssrc = 0

        rtpPacket = RtpPacket()

        rtpPacket.encode(version, padding, extension, cc, seqnum, marker, pt, ssrc, payload)
        #print("Encoding RTP Packet: " + str(seqnum))

        return rtpPacket.getPacket()

if __name__ == '__main__':
    logging.basicConfig(level=logging.NOTSET,
                        format='%(asctime)s - %(levelname)s - %(filename)s:%(funcName)s - %(message)s')
    server = Server()
    server.main()