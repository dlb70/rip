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



class Entry(object):
    def __init__(self, dest, first, metric, time):
        self.dest = dest # Destination dest (Router.id)
        self.first = first # First first along route (Router.id)
        self.metric = metric # The metric of this route
        self.time = time # The time value of when this entry was last udated
    
    def __repr__(self):
        rstr = ""
        rstr += "dest:" + str(self.dest) + ' '
        rstr += "first:" + str(self.first) + ' '
        rstr += "metric:" + str(self.metric) + ' '
        rstr += "time:" + str(self.timer()) + ''
        return rstr
    
    def timer(self):
        return time() - self.time
    

class EntryTable(object):
    def __init__(self):
        self.entries = {}

    def __repr__(self):
        rstr = str(self.entries)
        return rstr

    def __str__(self):
        return repr(self)

    def toStr(self):
        rstr = ""
        for entry in self.getEntries():
            rstr += str(entry) + '\n'
        return rstr

    def destinations(self):
        """ Returns a sorted list of destinations in the table. """
        return sorted(self.entries.keys())

    def getEntry(self, dest):
        """ Returns an entry from the table specified by destination. """
        return self.entries.get(dest)

    def getEntries(self):
        """ iterator function to return all entries in order. """
        for dest in self.destinations():
            yield self.get(dest)

    def addEntry(self, entry):
        """ Adds an entry to the table. Doesn't add if there is a conflict. """
        if (self.getEntry(entry.dest) == None):
            self.entries.update({entry.dest:entry})
        else:
            raise Exception("entry already in table: " + str(entry))
    
    def removeEntry(self, dest):
        """ Removes an entry from the table by destination """
        if (self.get(dest) == None):
            return None
        else:
            return self.entries.pop(dest)


class Output(object):
    def __init__(self, string):
        """ Takes a string input of the form "port-metric-dest" """
        elements = string.split('-')
        self.port   = int(elements[0])
        self.metric = int(elements[1])
        self.dest   = int(elements[2]) # the Router.id of the router

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
        self.entryTable = EntryTable()
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
        print("Table: ")
        for entry in self.entryTable.getEntries():
            print(" - " + str(entry))
    
    def openSocket(self, port):
        """ Open a socket for the router on the integer port. """
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.bind((LOCALHOST, port))
            print("Opened socket on port " + str(port))
            return s
        except:
            print("Could not open socket on port " + str(port))
            self.close()
    
    def openInputSockets(self):
        """ Creates a list of opened sockets using the asigned ports. """
        for port in self.inputPorts:
            sock = self.openSocket(port)
            self.inputSockets.append(sock)
        return self.inputSockets
    
    def openOutputSocket(self):
        """ Allocates the first input socket as the output socket.
            Does not actually open a socket.
        """
        self.outputSocket = self.inputSockets[0]
        return self.outputSocket
    
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
        self.outputSocket.sendto(bytes("MESSAGE",'utf-8'),
                                    (LOCALHOST,output.port))
    
    def recieveUpdate(self, sock):
        """ Reads a packet from the socket 'sock'
            Returns a tuple containing the str message and tuple address
        """
        packet = sock.recvfrom(BUFSIZE)
        address = packet[1]
        message = packet[0].decode(encoding='utf-8')
        print("Packet recieved from " + address[0] + ':' + str(address[1])) #DEBUG
        return message
     
    def broadcast(self):
        """ Send a request message to all outputs """
        for output in self.outputs.keys():
            self.sendUpdate(self.outputs.get(output))
    
    def wait(self):
        """ Waits for an incoming packet. Returns a list of packets to be 
            processed, or None if there were no queued packets.
        """
        read, written, errors = select(self.inputSockets,[],[],TIMEOUT)
        if (len(read) > 0):
            packets = []
            for sock in read:
                message = self.recieveUpdate(sock)
                packets.append(message)
            return packets
        else:
            return None
    
    def process(self, message):
        """ Takes an update message and processes it.
        """
        raise Exception("NotImplementedError")
    
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
            # router.show()
            t = time()
            t += (random() - 0.5) * (TIMER * 0.4) # adds randomness to timer 
            router.broadcast()
        
        packets = router.wait()
        if (packets != None):
            for packet in packets:
                router.process(packet)

if (__name__ =="__main__"):
    configFile = open(CONFIGFILE,'r')
    router = createRouter(configFile)
    configFile.close()
    router.show()
    try:
        main(router)
    except(KeyboardInterrupt, SystemExit):
        print("\nrecieved interrupt, closing...  ")
        router.close()
        print("done")
        input("Press [ENTER] to exit")
        exit()
