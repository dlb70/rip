import sys
from time import time,sleep
import socket
from select import select


### GLOBALS ###
LOCALHOST = "127.0.0.1"
CONFIGFILE = sys.argv[1]
BUFSIZE = 1023      # Maximum bytes read by socket.recvfrom()
TIMER = 6           # Time between periodic updates
TIMEOUT = TIMER/6.0 # Timout length for select()


class Router(object):
    def __init__(self, rtrid, inputPorts, outputs):
        """
            rtrid       - is the int ID of the router
            inputPorts  - is a list of ints which are ports on which to listen
            outputs     - is a list of dict(s) of the form specified 
                            in parseOutput()
        """
        self.rtrid = rtrid
        self.entryTable = []
        self.inputPorts = inputPorts
        self.inputSockets = []
        self.outputs = outputs
        self.outputSocket = None
    
    def show(self):
        print(self.rtrid)
        print(self.inputPorts)
        print("Outputs: ")
        for output in self.outputs:
            print(output)
    
    def openSocket(self, port):
        """ Open the socket for the router """
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.bind((LOCALHOST, port))
            print("Opened socket on port " + str(port))
            return s
        except:
            print("Could not open socket on port " + str(port))
            self.close()
        
    def openInputSockets(self):
        """ Creates a list of opened sockets using the asigned ports """
        for port in self.inputPorts:
            sock = self.openSocket(port)
            self.inputSockets.append(sock)
        return self.inputSockets
    
    def openOutputSocket(self):
        """ Allocates the first input socket as the output socket
            Does not actually open a socket
        """
        self.outputSocket = self.inputSockets[0]
        return self.outputSocket
    
    def wait(self):
        """ Waits for an incoming packet """
        read, written, errors = select(self.inputSockets,[],[],TIMEOUT)
        if (len(read) > 0):
            for sock in read:
                self.readPacket(sock)
        
    
    def readPacket(self, sock):
        """ Reads a packet from the socket 'sock'
            Decides wether to process the packet as a request or a response
        """
        packet = sock.recvfrom(BUFSIZE)
        address = packet[1]
        message = packet[0].decode(encoding='utf-8')
        print("Packet recieved from " + address[0] + ':' + str(address[1]))
        print(message)
    
    def sendRequest(self, output):
        """ Send a request message to the defined output """
        raise Exception("NotImplementedError")
    
    def parseRequest(self):
        """ Do something with a request message """
        raise Exception("NotImplementedError")
    
    def sendResponse(self, output):
        """" Send a response message to the defined output """
        raise Exception("NotImplementedError")
    
    def parseResponse(self):
        """ Do something with a response message """
        raise Exception("NotImplementedError")
    
    def broadcast(self):
        """ Send a request message to all outputs """
        for output in self.outputs:
            self.sendRequest(output)
    
    def close(self):
        """ close all sockets and exit cleanly """
        try:
            for sock in self.inputSockets:
                sock.close()
        except:
            print("WARNING!!! Could not exit cleanly! " + 
                "Sockets may still be open!")
            return 1
        return 0


def parseOutput(string):
    """ Takes a string input of the form port-dest-metric
        Returns a dict with the values mapped to their names
    """
    elements = string.split('-')
    return {'dest':elements[2], 
            'port':elements[0], 
            'metric':elements[1]}

def createRouter(cfg):
    """ Reads the provided config file and returns a newly created 
        Router object
    """
    l = cfg.readline().strip('\n')
    while (l != ""):
        if l.startswith("router-id"):
            rtrid = int(l.split(' ')[1])
        if l.startswith("input-ports"):
            inputs = l.strip("input-ports ").split(' ')
            inputs = list(map(int, inputs))
        if l.startswith("outputs"):
            outputs = l.strip("outputs ").split(' ')
            outputs = list(map(parseOutput, outputs))
        l = cfg.readline().strip('\n')
    return Router(rtrid,inputs,outputs)



def main(router):
    router.openInputSockets()
    router.openOutputSocket()
        
    while True: 
        router.wait()

if (__name__ =="__main__"):
    configFile = open(CONFIGFILE,'r')
    router = createRouter(configFile)
    configFile.close()
    router.show()
    try:
        main(router)
    except(KeyboardInterrupt, SystemExit):
        print("\nRecieved interrupt, closing...  ")
        router.close()
        print("done")
        input("Press [ENTER] to exit")
        exit()
    

