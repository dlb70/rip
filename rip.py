import sys
from time import time,sleep
from random import random
import socket
from select import select


### GLOBALS ###
LOCALHOST = "127.0.0.1"
CONFIGFILE = sys.argv[1]
BUFSIZE = 1023      # Maximum bytes read by socket.recvfrom()
TIMER = 6           # Time between periodic updates
TIMEOUT = TIMER/6.0 # Timout length for select()



class Output(object):
    def __init__(self, string):
        """ Takes a string input of the form "port-metric-dest" """
        elements = string.split('-')
        self.port   = int(elements[0])
        self.metric = int(elements[1])
        self.dest   = int(elements[2])

    def __repr__(self):
        rstr = "("
        rstr += "port:" + str(self.port) + ','
        rstr += "metric:" + str(self.metric) + ','
        rstr += "dest:" + str(self.dest) + ')'
        return rstr

class Router(object):
    def __init__(self, id, inputPorts, outputs):
        """
            id          - is the int ID of the router
            inputPorts  - is a list of ints which are ports on which to listen
            outputs     - is a list of dict(s) of the form specified 
                            in parseOutput()
        """
        self.id = id
        self.entryTable = []
        self.inputPorts = inputPorts
        self.inputSockets = []
        self.outputs = outputs
        self.outputSocket = None
    
    def show(self):
        print("ID: " + str(self.id))
        print("Inputs: " + str(self.inputPorts))
        print("Outputs: ")
        for output in sorted(self.outputs.keys()):
            print(" - " + str(self.outputs.get(output)))
    
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
                self.recieveUpdate(sock)
            return 1
        else:
            return 0
    
    def sendUpdate(self, output):
        """ Send a update message to the defined output. This involves sending
            a packet identifying the sender, and the sender's entry table.
            The entry table sent will include an entry for the sender with a
            metric set to zero.

            Split horizon - Avoid creating a loop that would be 
                created by including routes that run through the output.
            Poizoned reverse - Instead of just removing those routes, set their
                metric to infinity (A constant INFINITY in reality)
        """
        self.outputSocket.sendto(bytes("MESSAGE",'utf-8'),(LOCALHOST,output.port))
    
    def recieveUpdate(self, sock):
        """ Reads a packet from the socket 'sock'
            Returns a tuple containing the str message and tuple address
        """
        packet = sock.recvfrom(BUFSIZE)
        address = packet[1]
        message = packet[0].decode(encoding='utf-8')
        print("Packet recieved from " + address[0] + ':' + str(address[1]))
        return (message, address)
     
    def broadcast(self):
        """ Send a request message to all outputs """
        for output in self.outputs.keys():
            self.sendUpdate(self.outputs.get(output))
    
    def close(self):
        """ close all sockets """
        try:
            for sock in self.inputSockets:
                sock.close()
        except:
            print("WARNING!!! Could not exit cleanly! " + 
                "Sockets may still be open!")
            return 1
        return 0



def createRouter(cfg):
    """ Wrapper function for creating a Router object from a 
        configuration file
    """
    l = cfg.readline().strip('\n')
    while (l != ""):
        if l.startswith("router-id"):
            rtrid = int(l.split(' ')[1])
        
        if l.startswith("input-ports"):
            inputs = l.strip("input-ports ").split(' ')
            inputs = list(map(int, inputs))
        
        if l.startswith("outputs"):
            outputList = l.strip("outputs ").split(' ')
            outputs = {}
            for string in outputList:
                newOutput = Output(string)
                outputs.update({newOutput.dest:newOutput})
        
        l = cfg.readline().strip('\n')
    return Router(rtrid,inputs,outputs)



def main(router):
    router.openInputSockets()
    router.openOutputSocket()
    router.broadcast()
    t = time()
    while True: 
        if ((time() - t) >= TIMER):
            t = time()
            t += (random() - 0.5) * (TIMER * 0.4) # adds randomness to timer 
            router.broadcast()
        
        if (router.wait() == 1): # router recieved a packet
            pass
            # print("MAIN: router recieved a packet")
        

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
    

