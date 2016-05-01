import sys
from time import time,sleep
from random import random
from hashlib import md5
import socket
from select import select


### GLOBALS ###
LOCALHOST = "127.0.0.1"
CONFIGFILE = sys.argv[1]
BUFSIZE = 1023      # Maximum bytes read by socket.recvfrom()
TIMER = 6           # Time between periodic updates
TIMEOUT = TIMER/6.0 # Timout length for select()
ENTRY_TIMEOUT = TIMER * 6 # Timeout length for entry invalidation
GARBAGE = TIMER * 6 # Timer for garbage collection
INFINITY = 30       # Metric representing infinity. 



class Entry(object):
    def __init__(self, dest, first, metric, t=None):
        self.dest = dest # Destination dest (Router.id)
        self.first = first # First first along route (Router.id)
        self.metric = metric # The metric of this route
        if (t == None):
            t = time()
        self.time = t # The time value of when this entry was last udated
    
    def __repr__(self):
        rstr = ""
        rstr += "dest:" + str(self.dest) + ' '
        rstr += "first:" + str(self.first) + ' '
        rstr += "metric:" + str(self.metric) + ' '
        rstr += "time:" + str(self.timer())[:4] + ''
        return rstr
    
    def timer(self):
        """ Returns the time since last updated in seconds. """
        return time() - self.time
    

class EntryTable(object):
    def __init__(self):
        self.entries = {}

    def __repr__(self):
        rstr = str(self.entries)
        return rstr

    def __str__(self):
        return repr(self)

    def tostr(self):
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
        """ Iterator function to return all entries in order. """
        for dest in self.destinations():
            yield self.entries.get(dest)

    def update(self, entry): ##############################################
        """ Tests to see wether the new entry should be added.
            Adds the entry to the table (replacing older entry if there).
            Returns the new entry if added, or None if not added.
        """
        current = self.getEntry(entry.dest)
        
        if (current == None): # If no record of destination
            if (entry.metric < INFINITY):
                self.entries.update({entry.dest:entry})
            return entry
        
        elif (current.first == entry.first): # If it came from the first hop
            if (entry.metric > INFINITY):
                entry.metric = INFINITY
            self.entries.update({entry.dest:entry})
            return entry
        
        elif (entry.metric < current.metric): 
            self.entries.update({entry.dest:entry})
            return entry
    
        return None
            
    
    def removeEntry(self, dest):
        """ Removes an entry from the table by destination """
        if (self.entries.get(dest) == None):
            return None
        else:
            return self.entries.pop(dest)


class Output(object):
    """ Class defining the attributes of an output.
        Attributes refer to the destination router and its edge cost.
    """

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
    def __init__(self, rtrid, inputPorts, outputs):
        """ A Router.
            id          - is the int ID of the router.
            inputPorts  - is a list of ints which are ports on which to listen.
            outputs     - is a dict of the form {dest:Output},
                where 'dest' is the destination id.
            outputSocket    - is the socket on which updates are sent from.
        """
        self.id = rtrid
        self.entryTable = EntryTable()
        self.inputPorts = inputPorts
        self.inputSockets = []
        self.outputs = outputs
        self.outputSocket = None
        self.garbageTimer = 0
    
    def show(self):
        print("ID: " + str(self.id))
        print("Table: ")
        for entry in self.entryTable.getEntries():
            print(" - " + str(entry))
    
    def showIO(self):
        print("Inputs: " + str(self.inputPorts))
        print("Outputs: ")
        for output in sorted(self.outputs.keys()):
            print(" - " + str(self.outputs.get(output)))
    
    def checksum(self, payload):
        """ Returns a checksum of the payload """
        return md5(bytes(payload, 'utf-8')).hexdigest()[:10]

    def verifies(self, message):
        """ Returns True if a packet is valid, False if invalid """
        return (message[:10] == self.checksum(message[10:]))
    
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
    
    def createUpdate(self, output): #######################################
        """ Create an update message (as a string) from the router's
            information and the routing table. 
            
            Message format:
            '''
            HEADER self.id output.dest\n
            ENTRY self.id 0\n
            ENTRY dest metric\n
            ENTRY dest metric\n
            '''
        """
        # The first newline is to split the checksum from the message
        # Header = src dest
        message  = "\nHEADER " + str(self.id) + ' ' + str(output.dest) + '\n'
        message += "ENTRY " + str(self.id) + " 0\n"
        for entry in self.entryTable.getEntries():
            dest, metric, first = (entry.dest, entry.metric, entry.first)
            if (first == output.dest): # Split Horizon with Poisoned Reverse
                metric = INFINITY
            message += "ENTRY " + str(dest) + ' ' + str(metric) + '\n'

        checksum = self.checksum(message)
        return (checksum + message)
        
    
    def sendUpdate(self, output):
        """ Send a update message to the defined output. This involves sending
            a packet identifying the sender, and the sender's entry table.
            The entry table sent will include an entry for the sender with a
            metric set to zero.

            Split horizon - Avoid loop creation by not sending routes that have
                their first hop set to the defined output.
            Poizoned reverse - Instead of just removing those routes, set their
                metric to infinity (A constant INFINITY in reality)
        """
        message = self.createUpdate(output)
        self.outputSocket.sendto(bytes(message,'utf-8'),
                                    (LOCALHOST,output.port))

    def process(self, message): ###########################################
        """ Takes an update message as a string and processes it.
            If the checksum does not match the payload, drop the packet.
            Returns True on success
        """
        if not (self.verifies(message)):
            print("Invalid Checksum. Packed dropped!")
            return None # Drop the packet
        
        lines = message.split('\n')
        for line in lines[1:]: # Skip checksum
            line = line.split(' ')
            
            if (line[0] == ''): # End of message
                return None
            
            elif (line[0] == "HEADER"):
                source = int(line[1])
                routerid = int(line[2])
                if (routerid != self.id):
                    print("Message not destined for me. Dropping packet!")
                output = self.outputs.get(source)
            
            elif (line[0] == "ENTRY"):
                dest = int(line[1])
                if (dest != self.id): # Do not add ourselves
                    metric = int(line[2]) + output.metric 
                    newEntry = Entry(dest, source, metric)
                    self.entryTable.update(newEntry)
            
        return None
    
    def recieveUpdate(self, sock):
        """ Reads a packet from the socket 'sock'
            Returns a tuple containing the str message and tuple address
        """
        packet = sock.recvfrom(BUFSIZE)
        address = packet[1]
        message = packet[0].decode(encoding='utf-8')
        #print("Packet recieved from " + address[0] + ':' + str(address[1]))#DBG
        return message
     
    def broadcast(self):
        """ Send a request message to all outputs """
        for output in self.outputs.keys():
            self.sendUpdate(self.outputs.get(output))
    
    def wait(self, timeout):
        """ Waits for an incoming packet. Returns a list of update messages 
            to be processed, or None if there were no queued packets.
        """
        read, written, errors = select(self.inputSockets,[],[],timeout)
        if (len(read) > 0):
            messages = []
            for sock in read:
                message = self.recieveUpdate(sock)
                messages.append(message)
            return messages
        else:
            return None
    
    def garbageCollect(self): #############################################
        """ Removes expired entries from the entry table. 
            Before removing the entries, set their metric to INFINITY
                and broadcast an update.
            Returns a list of removed entries.
        """
        self.garbageTimer += GARBAGE
        expired = []
        for entry in self.entryTable.getEntries():
            if (entry.timer() > ENTRY_TIMEOUT):
                expired.append(entry.dest)
                entry.metric = INFINITY
        if (len(expired) != 0):
            self.broadcast()     # Broadcast Update
            self.show()
            print()
            for dest in expired: # Remove Entries
                self.entryTable.removeEntry(dest)
        return expired
            
    
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
    print("INITIALIZED.\n\n")
    router.broadcast()
    t = time()
    router.garbageTimer = time() + GARBAGE
    while True: 
        # Do main router update message
        if ((time() - t) >= TIMER):
            # router.show()
            t += TIMER + (random() - 0.5) * (TIMER * 0.4) # Randomises timer
            router.broadcast()
            router.show()
            print()

        # Wait for incoming packets
        packets = router.wait(TIMEOUT) 
        if (packets != None):
            for packet in packets:
                router.process(packet)
        
        # Do garbage collection
        if (time() - router.garbageTimer >= GARBAGE):
            # timer reset is called from garbageCollect()
            print("GARBAGE COLLECTION")
            n = len(router.garbageCollect())
            print("GARBAGE COLLECTION: Removed " + str(n) + "entries.")

        #if (router.garbageCollect() != None):
        #    print("GARBAGE COLLECTION")

if (__name__ =="__main__"):
    print("\nReading from config file: " + CONFIGFILE)
    configFile = open(CONFIGFILE,'r')
    print("INITIALIZING...")
    router = createRouter(configFile)
    configFile.close()
    router.show()
    router.showIO()
    try:
        main(router)
    except(KeyboardInterrupt, SystemExit):
        print("\nrecieved interrupt, closing...  ")
        router.close()
        print("done.")
        exit(0)



